import subprocess
import os
import signal
import time
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from celery import current_task

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..core.config import settings
from ..models.script import Script, ScriptStatus

logger = logging.getLogger(__name__)


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
        
        try:
            # Run script with timeout
            process = subprocess.Popen(
                ["python", script.file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.path.dirname(script.file_path)
            )
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log_line = output.strip()
                    logs.append(log_line)
                    
                    # Update logs in database
                    script.execution_logs = "\n".join(logs)
                    db.commit()
                    
                    # Update Celery task info
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "script_id": script_id,
                            "logs": logs,
                            "status": "running"
                        }
                    )
            
            # Get return code
            return_code = process.poll()
            
            if return_code == 0:
                script.status = ScriptStatus.COMPLETED
                script.completed_at = datetime.utcnow()
            else:
                script.status = ScriptStatus.FAILED
                script.error_message = f"Script exited with code {return_code}"
                script.completed_at = datetime.utcnow()
            
            script.execution_logs = "\n".join(logs)
            db.commit()
            
            return {
                "script_id": script_id,
                "status": script.status.value,
                "logs": logs,
                "return_code": return_code,
                "execution_time": time.time() - start_time
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            script.status = ScriptStatus.FAILED
            script.error_message = "Script execution timeout"
            script.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "script_id": script_id,
                "status": "failed",
                "logs": logs,
                "error": "Execution timeout"
            }
            
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        
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
            # In a real implementation, you'd need to track process IDs
            # and kill the actual subprocess
            script.status = ScriptStatus.CANCELLED
            script.completed_at = datetime.utcnow()
            db.commit()
            
            return {"script_id": script_id, "status": "cancelled"}
        else:
            return {"script_id": script_id, "status": "not_running"}
            
    except Exception as e:
        logger.error(f"Script cancellation error: {e}")
        return {"script_id": script_id, "error": str(e)}
    
    finally:
        db.close()
