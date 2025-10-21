import subprocess
import os
import signal
import time
import logging
import psutil
import select
import sys
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from celery import current_task

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..core.config import settings
from ..models.script import Script, ScriptStatus

logger = logging.getLogger(__name__)

# Store running processes for cancellation
running_processes: Dict[int, subprocess.Popen] = {}
# Track which scripts are being cancelled
cancelled_scripts: set = set()


def _kill_process(process: subprocess.Popen) -> None:
    """Kill a process and all its children forcefully"""
    try:
        if process.poll() is not None:
            # Process already finished
            logger.info(f"Process {process.pid} already terminated")
            return
        
        logger.warning(f"Force killing process {process.pid} and all children...")
        
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        
        # First: Terminate all children gracefully
        for child in children:
            try:
                logger.info(f"Terminating child process {child.pid}")
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # Terminate parent gracefully
        try:
            logger.info(f"Terminating parent process {parent.pid}")
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        
        # Wait for graceful shutdown
        try:
            parent.wait(timeout=1)
            logger.info(f"Process {process.pid} terminated gracefully")
            return
        except psutil.TimeoutExpired:
            logger.warning(f"Process {parent.pid} did not terminate gracefully, force killing...")
        
        # Force kill all children
        for child in children:
            try:
                if child.is_running():
                    logger.warning(f"Force killing child process {child.pid}")
                    child.kill()
            except psutil.NoSuchProcess:
                pass
        
        # Force kill parent
        try:
            if parent.is_running():
                logger.warning(f"Force killing parent process {parent.pid}")
                parent.kill()
        except psutil.NoSuchProcess:
            pass
        
        # Final wait for process to die
        try:
            process.wait(timeout=2)
            logger.info(f"Process {process.pid} killed successfully")
        except subprocess.TimeoutExpired:
            # Last resort: force kill via subprocess
            logger.error(f"Process {process.pid} STILL RUNNING after kill attempts!")
            process.kill()
            process.wait(timeout=1)
            logger.info(f"Process {process.pid} finally killed with process.kill()")
            
    except psutil.NoSuchProcess:
        logger.info("Process already terminated")
    except Exception as e:
        logger.error(f"Error killing process: {e}")
        # Absolute last resort
        try:
            process.kill()
            process.wait(timeout=1)
        except:
            logger.error(f"Failed all attempts to kill process!")


@celery_app.task(bind=True, name="execute_script")
def execute_script(self, script_id: int) -> Dict[str, Any]:
    """Execute a user script in a subprocess"""
    db = SessionLocal()
    
    try:
        # Get script from database
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise Exception(f"Script {script_id} not found")
        
        # Reset script status and clear previous execution data
        script.status = ScriptStatus.RUNNING
        script.started_at = datetime.utcnow()
        script.completed_at = None  # Clear previous completion time
        script.execution_logs = ""  # Clear previous logs
        script.error_message = None  # Clear previous errors
        script.exit_code = None  # Clear previous exit code
        script.execution_time_seconds = None  # Clear previous execution time
        db.commit()
        logger.info(f"Script {script_id} status changed to RUNNING (previous state cleared)")
        
        # Check file exists
        if not os.path.exists(script.file_path):
            raise Exception(f"Script file not found: {script.file_path}")
        
        # Execute script
        logs = []
        start_time = time.time()
        process = None
        
        try:
            # Determine Python executable (use system python or virtual env)
            python_executable = "python3" if os.path.exists("/usr/bin/python3") else "python"
            
            # Run script with timeout and proper buffering
            process = subprocess.Popen(
                [python_executable, "-u", script.file_path],  # -u for unbuffered output
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,  # Line buffered
                cwd=os.path.dirname(script.file_path),
                # Security: Run with limited privileges (Unix-only)
                # preexec_fn=os.setpgrp if os.name != 'nt' else None
            )
            
            # Store process for cancellation
            running_processes[script_id] = process
            
            # Stream output with timeout
            timeout = settings.MAX_EXECUTION_TIME
            
            while True:
                # Check if script was cancelled externally by checking DATABASE
                # (Don't use in-memory set - FastAPI and Celery are separate processes!)
                db.refresh(script)  # Reload from database to get latest status
                if script.status == ScriptStatus.CANCELLED:
                    logger.warning(f"Script {script_id}: Cancellation detected from database - exiting cleanly")
                    
                    # Kill the subprocess if it's still running
                    if 'process' in locals() and process and process.poll() is None:
                        logger.warning(f"Script {script_id}: Killing subprocess PID {process.pid}")
                        try:
                            process.kill()
                            process.wait(timeout=1)
                            logger.info(f"Script {script_id}: Subprocess killed successfully")
                        except Exception as e:
                            logger.error(f"Script {script_id}: Error killing subprocess: {e}")
                    
                    # Save all logs collected so far
                    script.execution_logs = "\n".join(logs) + f"\n\n[Cancelled by user at {datetime.utcnow().isoformat()}]"
                    script.completed_at = datetime.utcnow()
                    script.celery_task_id = None  # Clear task ID
                    db.commit()
                    logger.info(f"Script {script_id}: Saved {len(logs)} lines, marked CANCELLED, cleared task ID")
                    
                    # Return immediately - task exits cleanly
                    logger.info(f"Script {script_id}: Task exiting cleanly - worker will be ready for next task")
                    return {
                        "script_id": script_id,
                        "status": "cancelled",
                        "logs": logs,
                        "message": "Cancelled by user - task exited cleanly"
                    }
                
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"Script {script_id} exceeded timeout ({timeout}s)")
                    _kill_process(process)
                    raise TimeoutError(f"Script execution exceeded {timeout} seconds")
                
                try:
                    # Use non-blocking read with short timeout
                    if sys.platform == 'win32':
                        # Windows: Use a timeout approach
                        output = None
                        
                        def read_output():
                            nonlocal output
                            try:
                                output = process.stdout.readline()
                            except:
                                pass
                        
                        thread = threading.Thread(target=read_output)
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout=0.1)  # 100ms timeout
                        
                        if thread.is_alive():
                            # Thread still reading - check cancellation and process death
                            # This is critical for infinite loops!
                            if script_id in cancelled_scripts or process.poll() is not None:
                                logger.warning(f"Script {script_id}: Cancelled or process dead while reading")
                                break
                            # No output available yet, continue to check cancellation
                            continue
                            
                    else:
                        # Unix/Linux: Use select for non-blocking read
                        ready, _, _ = select.select([process.stdout], [], [], 0.1)
                        if not ready:
                            # No data available - check cancellation before continuing
                            if script_id in cancelled_scripts or process.poll() is not None:
                                logger.warning(f"Script {script_id}: Cancelled or process dead (Unix)")
                                break
                            # No data available, continue to check cancellation
                            continue
                        output = process.stdout.readline()
                        
                except (IOError, OSError) as e:
                    # Process was killed externally
                    logger.warning(f"Script {script_id}: Process output stream closed (likely cancelled)")
                    break
                except Exception as e:
                    logger.warning(f"Script {script_id}: Error reading from process: {e}")
                    continue
                
                # Check if we got output
                if output:
                    log_line = output.strip()
                    logs.append(log_line)
                    logger.info(f"Script {script_id}: {log_line}")
                    
                    # CRITICAL: Check cancellation BEFORE saving (for infinite loops)
                    if script_id in cancelled_scripts:
                        logger.warning(f"Script {script_id}: Cancellation detected while processing output")
                        cancelled_scripts.discard(script_id)
                        script.execution_logs = "\n".join(logs) + f"\n\n[Cancelled by user at {datetime.utcnow().isoformat()}]"
                        script.status = ScriptStatus.CANCELLED
                        script.completed_at = datetime.utcnow()
                        script.celery_task_id = None
                        db.commit()
                        return {
                            "script_id": script_id,
                            "status": "cancelled",
                            "logs": logs,
                            "message": "Cancelled while processing output"
                        }
                    
                    # Save EVERY line to database immediately for accurate logging
                    # This ensures no logs are lost and user sees real-time updates
                    script.execution_logs = "\n".join(logs)
                    db.commit()
                    logger.debug(f"Script {script_id}: Saved {len(logs)} lines to database")
                
                # Update Celery task info
                if output:
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "script_id": script_id,
                            "logs": logs[-20:],  # Last 20 lines for context
                            "status": "running",
                            "progress": int((time.time() - start_time) / timeout * 100),
                            "lines_captured": len(logs)
                        }
                    )
                
                # Check if process finished AFTER trying to read
                # This ensures we capture all buffered output before exiting
                elif output == '' and process.poll() is not None:
                    logger.info(f"Script {script_id}: Process finished, no more output")
                    break
            
            # Get return code
            return_code = process.poll()
            
            # Check if cancelled (should already be handled above, but double-check)
            if script.status == ScriptStatus.CANCELLED:
                logger.info(f"Script {script_id}: Already marked as CANCELLED, exiting")
                return {
                    "script_id": script_id,
                    "status": "cancelled",
                    "logs": logs,
                    "message": "Script was cancelled"
                }
            
            # Final log update
            script.execution_logs = "\n".join(logs)
            
            if return_code == 0:
                script.status = ScriptStatus.COMPLETED
                script.completed_at = datetime.utcnow()
                script.celery_task_id = None  # Clear task ID on completion
                logger.info(f"Script {script_id} completed successfully")
            else:
                script.status = ScriptStatus.FAILED
                script.error_message = f"Script exited with code {return_code}"
                script.completed_at = datetime.utcnow()
                script.celery_task_id = None  # Clear task ID on failure
                logger.error(f"Script {script_id} failed with code {return_code}")
            
            db.commit()
            
            return {
                "script_id": script_id,
                "status": script.status.value,
                "logs": logs,
                "return_code": return_code,
                "execution_time": time.time() - start_time
            }
            
        except TimeoutError as e:
            if process:
                logger.warning(f"Script {script_id} timed out, force killing process...")
                _kill_process(process)
                # Ensure process is dead
                time.sleep(0.5)
                if process.poll() is None:
                    logger.error(f"Process {process.pid} STILL RUNNING after timeout kill!")
                    try:
                        process.kill()
                        process.wait(timeout=2)
                    except:
                        pass
                logger.info(f"Process for timed out script {script_id} killed successfully")
            script.status = ScriptStatus.FAILED
            script.error_message = str(e)
            script.execution_logs = "\n".join(logs)
            script.completed_at = datetime.utcnow()
            script.celery_task_id = None  # Clear task ID on timeout
            db.commit()
            logger.error(f"Script {script_id} timeout: {e}")
            
            return {
                "script_id": script_id,
                "status": "failed",
                "logs": logs,
                "error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        
        # Kill process if it was created and still running
        if 'process' in locals() and process:
            if process.poll() is None:  # Process still running
                logger.warning(f"Process still running for failed script {script_id}, force killing...")
                _kill_process(process)
                # Wait to ensure it's dead
                time.sleep(0.5)
                if process.poll() is None:
                    logger.error(f"Process {process.pid} STILL RUNNING after kill attempt!")
                    try:
                        process.kill()
                        process.wait(timeout=2)
                    except:
                        pass
                logger.info(f"Process for failed script {script_id} killed successfully")
        
        # Update script status
        if 'script' in locals() and script:
            script.status = ScriptStatus.FAILED
            script.error_message = str(e)
            script.completed_at = datetime.utcnow()
            script.execution_logs = "\n".join(logs) if 'logs' in locals() else ""
            script.celery_task_id = None  # Clear task ID on exception
            db.commit()
        
        return {
            "script_id": script_id,
            "status": "failed",
            "error": str(e)
        }
    
    finally:
        # Cleanup: Remove from running processes
        if script_id in running_processes:
            del running_processes[script_id]
            logger.info(f"Removed script {script_id} from running_processes")
        
        # Cleanup: Remove from cancelled scripts (in case it wasn't removed)
        if script_id in cancelled_scripts:
            cancelled_scripts.discard(script_id)
            logger.info(f"Removed script {script_id} from cancelled_scripts")
        
        db.close()


@celery_app.task(name="cancel_script")
def cancel_script(script_id: int) -> Dict[str, Any]:
    """Cancel a running script"""
    db = SessionLocal()
    
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise Exception(f"Script {script_id} not found")
        
        if script.status == ScriptStatus.RUNNING:
            # Kill the actual process if it exists
            if script_id in running_processes:
                process = running_processes[script_id]
                _kill_process(process)
                logger.info(f"Killed process for script {script_id}")
            
            script.status = ScriptStatus.CANCELLED
            script.completed_at = datetime.utcnow()
            script.execution_logs = (script.execution_logs or "") + "\n[Script cancelled by user]"
            db.commit()
            
            return {"script_id": script_id, "status": "cancelled"}
        else:
            return {"script_id": script_id, "status": "not_running", "current_status": script.status.value}
            
    except Exception as e:
        logger.error(f"Script cancellation error: {e}")
        return {"script_id": script_id, "error": str(e)}
    
    finally:
        db.close()
