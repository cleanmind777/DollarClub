from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import aiofiles
import uuid
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user_id
from ..core.config import settings
from ..models.user import User
from ..models.script import Script, ScriptStatus
from ..schemas.script import ScriptResponse, ScriptList, ScriptExecution
from ..tasks.script_execution import execute_script, cancel_script

router = APIRouter(prefix="/scripts", tags=["scripts"])


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(get_current_user_id)):
    """Get current authenticated user"""
    user_id = get_current_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/upload", response_model=ScriptResponse)
async def upload_script(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a trading strategy script"""
    
    # Validate file
    if not file.filename.endswith(('.py', '.js', '.ts')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Python, JavaScript, and TypeScript files are allowed"
        )
    
    if file.size > settings.MAX_SCRIPT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.MAX_SCRIPT_SIZE} bytes"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.SCRIPTS_DIR, unique_filename)
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create script record in database
    script = Script(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size,
        status=ScriptStatus.UPLOADED
    )
    
    db.add(script)
    db.commit()
    db.refresh(script)
    
    return script


@router.get("/list", response_model=ScriptList)
async def list_scripts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List user's scripts"""
    
    scripts_query = db.query(Script).filter(Script.user_id == current_user.id)
    total = scripts_query.count()
    scripts = scripts_query.offset(skip).limit(limit).all()
    
    return ScriptList(scripts=scripts, total=total)


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific script details"""
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    return script


@router.post("/{script_id}/execute")
async def execute_script_endpoint(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a script"""
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if script.status == ScriptStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Script is already running"
        )
    
    # Check concurrent execution limit
    running_scripts = db.query(Script).filter(
        Script.user_id == current_user.id,
        Script.status == ScriptStatus.RUNNING
    ).count()
    
    if running_scripts >= settings.MAX_CONCURRENT_SCRIPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum concurrent scripts limit ({settings.MAX_CONCURRENT_SCRIPTS}) reached"
        )
    
    # Start Celery task
    task = execute_script.delay(script_id)
    
    return {
        "message": "Script execution started",
        "task_id": task.id,
        "script_id": script_id
    }


@router.get("/{script_id}/status")
async def get_script_status(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get script execution status and logs"""
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    return {
        "script_id": script_id,
        "status": script.status.value,
        "logs": script.execution_logs or "",
        "error_message": script.error_message,
        "started_at": script.started_at,
        "completed_at": script.completed_at
    }


@router.post("/{script_id}/cancel")
async def cancel_script_endpoint(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running script"""
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if script.status != ScriptStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Script is not running"
        )
    
    # Cancel Celery task
    cancel_script.delay(script_id)
    
    return {"message": "Script cancellation requested"}


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a script"""
    
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if script.status == ScriptStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running script"
        )
    
    # Delete file
    if os.path.exists(script.file_path):
        os.remove(script.file_path)
    
    # Delete from database
    db.delete(script)
    db.commit()
    
    return {"message": "Script deleted successfully"}
