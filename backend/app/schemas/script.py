from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from ..models.script import ScriptStatus


class ScriptBase(BaseModel):
    filename: str
    original_filename: str


class ScriptCreate(ScriptBase):
    pass


class ScriptResponse(ScriptBase):
    id: int
    user_id: int
    file_path: str
    file_size: Optional[int]
    status: ScriptStatus
    execution_logs: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScriptList(BaseModel):
    scripts: List[ScriptResponse]
    total: int


class ScriptExecution(BaseModel):
    script_id: int


class ScriptLog(BaseModel):
    script_id: int
    logs: str
    status: ScriptStatus
