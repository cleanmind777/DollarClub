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
from ..services.package_validator import validator as package_validator

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
        
        # Validate packages before execution
        logger.info(f"Script {script_id}: Validating package dependencies...")
        all_installed, missing_pkgs, available_pkgs = package_validator.validate_packages(script.file_path)
        
        if not all_installed:
            error_msg = package_validator.create_error_message(missing_pkgs)
            logger.error(f"Script {script_id}: Missing packages: {missing_pkgs}")
            
            # Save error to database
            script.status = ScriptStatus.FAILED
            script.error_message = error_msg
            script.execution_logs = f"Package validation failed.\n\n{error_msg}"
            script.completed_at = datetime.utcnow()
            script.celery_task_id = None
            db.commit()
            
            return {
                "script_id": script_id,
                "status": "failed",
                "error": error_msg,
                "missing_packages": missing_pkgs
            }
        
        logger.info(f"Script {script_id}: All packages available: {available_pkgs}")
        
        # Execute script
        logs = []
        start_time = time.time()
        process = None
        
        try:
            # Determine Python executable (use current Python interpreter)
            python_executable = sys.executable
            
            # Set environment to force unbuffered output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
            env['PYTHONIOENCODING'] = 'utf-8'  # Ensure UTF-8 encoding
            
            # Decide whether to use wrapper or run directly
            if settings.USE_SCRIPT_WRAPPER:
                # Use wrapper script for better output handling (recommended)
                wrapper_path = os.path.join(os.path.dirname(__file__), 'script_wrapper.py')
                cmd = [python_executable, "-u", wrapper_path, script.file_path]
                logger.info(f"Script {script_id}: Using wrapper for execution")
            else:
                # Run script directly (for debugging)
                cmd = [python_executable, "-u", script.file_path]
                logger.info(f"Script {script_id}: Running directly without wrapper")
            
            # Run script with forced unbuffering
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0,  # Completely unbuffered
                cwd=os.path.dirname(script.file_path),
                env=env,  # Pass environment with PYTHONUNBUFFERED
                # Security: Run with limited privileges (Unix-only)
                # preexec_fn=os.setpgrp if os.name != 'nt' else None
            )
            
            # Store process for cancellation
            running_processes[script_id] = process
            
            # Stream output with timeout
            timeout = settings.MAX_EXECUTION_TIME
            last_db_update = time.time()
            heartbeat_interval = 2.0  # Update DB every 2 seconds even without output
            
            iteration = 0
            while True:
                iteration += 1
                
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
                    # Just try to read a line - simple and reliable
                    output = process.stdout.readline()
                    
                    # If we got output, great - process it below
                    # If readline() returns empty, check why
                    if not output or output == '':
                        # No output - check if process finished
                        if process.poll() is not None:
                            # Process finished AND no more output from readline
                            # This means we've read everything line-by-line
                            logger.info(f"Script {script_id}: Process finished, readline empty")
                            break
                        
                        # Process still running, just no output yet
                        # Check for cancellation
                        if script_id in cancelled_scripts:
                            logger.warning(f"Script {script_id}: Cancelled")
                            break
                        
                        # Small sleep to avoid busy loop
                        time.sleep(0.01)
                        continue
                        
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
                    last_db_update = time.time()
                    db.commit()
                    logger.debug(f"Script {script_id}: Saved {len(logs)} lines to database")
                
                # Heartbeat: Update database periodically even without output
                # This is critical for infinite loops that don't produce output
                current_time = time.time()
                if current_time - last_db_update >= heartbeat_interval:
                    # Add status info to logs if no output recently
                    elapsed = int(current_time - start_time)
                    if not logs or current_time - start_time > 3:  # Add status after 3 seconds
                        status_msg = f"[Status: Script running... {elapsed}s elapsed, {len(logs)} lines captured]"
                        # Don't add duplicate status messages
                        if not logs or not logs[-1].startswith("[Status:"):
                            logs.append(status_msg)
                            script.execution_logs = "\n".join(logs)
                    else:
                        # Just update timestamp without adding to logs
                        script.execution_logs = "\n".join(logs) if logs else "[Script started, waiting for output...]"
                    
                    last_db_update = current_time
                    db.commit()
                    logger.debug(f"Script {script_id}: Heartbeat update ({elapsed}s elapsed, {len(logs)} lines)")
                
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
                
                # If no output, just continue
                if not output or output == '':
                    continue
            
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
