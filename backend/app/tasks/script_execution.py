import subprocess
import os
import signal
import time
import logging
import psutil
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


def _kill_process(process: subprocess.Popen) -> None:
    """Kill a process and all its children"""
    try:
        if process.poll() is None:  # Process is still running
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            
            # Wait for process to die
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if still alive
                process.kill()
    except Exception as e:
        logger.error(f"Error killing process: {e}")


@celery_app.task(bind=True, name="execute_script")
def execute_script(self, script_id: int) -> Dict[str, Any]:
    """Execute a user script in a subprocess"""
    db = SessionLocal()
    
    try:
        # Get script from database
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise Exception(f"Script {script_id} not found")
        
        # Update status to running
        script.status = ScriptStatus.RUNNING
        script.started_at = datetime.utcnow()
        script.execution_logs = ""
        db.commit()
        
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
            
            # Run script with timeout
            process = subprocess.Popen(
                [python_executable, script.file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.path.dirname(script.file_path),
                # Security: Run with limited privileges (Unix-only)
                # preexec_fn=os.setpgrp if os.name != 'nt' else None
            )
            
            # Store process for cancellation
            running_processes[script_id] = process
            
            # Stream output with timeout
            timeout = settings.MAX_EXECUTION_TIME
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"Script {script_id} exceeded timeout ({timeout}s)")
                    _kill_process(process)
                    raise TimeoutError(f"Script execution exceeded {timeout} seconds")
                
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log_line = output.strip()
                    logs.append(log_line)
                    logger.info(f"Script {script_id}: {log_line}")
                    
                    # Update logs in database (every 10 lines to reduce DB load)
                    if len(logs) % 10 == 0:
                        script.execution_logs = "\n".join(logs)
                        db.commit()
                    
                    # Update Celery task info
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "script_id": script_id,
                            "logs": logs[-10:],  # Last 10 lines only
                            "status": "running",
                            "progress": int((time.time() - start_time) / timeout * 100)
                        }
                    )
            
            # Get return code
            return_code = process.poll()
            
            # Final log update
            script.execution_logs = "\n".join(logs)
            
            if return_code == 0:
                script.status = ScriptStatus.COMPLETED
                script.completed_at = datetime.utcnow()
                logger.info(f"Script {script_id} completed successfully")
            else:
                script.status = ScriptStatus.FAILED
                script.error_message = f"Script exited with code {return_code}"
                script.completed_at = datetime.utcnow()
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
                _kill_process(process)
            script.status = ScriptStatus.FAILED
            script.error_message = str(e)
            script.execution_logs = "\n".join(logs)
            script.completed_at = datetime.utcnow()
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
        
        # Kill process if still running
        if process and process.poll() is None:
            _kill_process(process)
        
        # Update script status
        if 'script' in locals():
            script.status = ScriptStatus.FAILED
            script.error_message = str(e)
            script.completed_at = datetime.utcnow()
            script.execution_logs = "\n".join(logs) if 'logs' in locals() else ""
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
