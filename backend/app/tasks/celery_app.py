from celery import Celery
from celery.signals import worker_ready
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "dollarclub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.script_execution"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.MAX_EXECUTION_TIME,
    worker_prefetch_multiplier=1,
    task_acks_late=False,  # Acknowledge immediately to prevent restart on worker restart
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes
)


@worker_ready.connect
def cleanup_stale_scripts(**kwargs):
    """
    Clean up any stale RUNNING scripts when worker starts.
    This handles scripts that were running when worker was stopped.
    """
    logger.info("Celery worker starting - cleaning up stale scripts...")
    
    try:
        from ..core.database import SessionLocal
        from ..models.script import Script, ScriptStatus
        from datetime import datetime
        
        db = SessionLocal()
        
        # Find all scripts stuck in RUNNING status
        stale_scripts = db.query(Script).filter(
            Script.status == ScriptStatus.RUNNING
        ).all()
        
        if stale_scripts:
            logger.warning(f"Found {len(stale_scripts)} stale RUNNING scripts")
            
            for script in stale_scripts:
                logger.info(f"Marking script {script.id} as FAILED (worker restart)")
                script.status = ScriptStatus.FAILED
                script.error_message = "Worker was restarted while script was running"
                script.completed_at = datetime.utcnow()
                script.celery_task_id = None  # Clear task ID
                script.execution_logs = (script.execution_logs or "") + "\n\n[Worker restarted - script terminated]"
            
            db.commit()
            logger.info(f"Cleaned up {len(stale_scripts)} stale scripts")
        else:
            logger.info("No stale scripts found")
        
        db.close()
        
        # Purge any pending tasks from queue (cancelled tasks shouldn't restart)
        try:
            purged_count = celery_app.control.purge()
            if purged_count:
                logger.warning(f"Purged {purged_count} pending tasks from queue")
            else:
                logger.info("No pending tasks to purge")
        except Exception as e:
            logger.warning(f"Could not purge queue: {e}")
        
        logger.info("Celery worker ready - all cleanup complete")
        
    except Exception as e:
        logger.error(f"Error cleaning up stale scripts: {e}")
