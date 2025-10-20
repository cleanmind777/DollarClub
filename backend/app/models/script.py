from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, Index, CheckConstraint, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import enum
import os
import re
from datetime import datetime
from ..core.database import Base


class ScriptStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Script(Base):
    __tablename__ = "scripts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key relationship
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_extension = Column(String(10), nullable=True)
    
    # Execution information
    status = Column(Enum(ScriptStatus), default=ScriptStatus.UPLOADED, nullable=False)
    execution_logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Execution metrics
    execution_time_seconds = Column(Numeric(10, 3), nullable=True)
    memory_usage_mb = Column(Numeric(10, 2), nullable=True)
    exit_code = Column(Integer, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    owner = relationship(
        "User", 
        back_populates="scripts",
        lazy="select"  # Lazy loading for better performance
    )

    # Indexes and constraints
    __table_args__ = (
        Index('ix_scripts_user_status', 'user_id', 'status'),
        Index('ix_scripts_created_at', 'created_at'),
        Index('ix_scripts_filename', 'filename'),
        Index('ix_scripts_status', 'status'),
        CheckConstraint(
            "file_size > 0",
            name='ck_positive_file_size'
        ),
        CheckConstraint(
            "execution_time_seconds >= 0",
            name='ck_non_negative_execution_time'
        ),
        CheckConstraint(
            "memory_usage_mb >= 0",
            name='ck_non_negative_memory'
        ),
        CheckConstraint(
            "CASE WHEN status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN completed_at IS NOT NULL ELSE TRUE END",
            name='ck_completed_has_completion_time'
        ),
        CheckConstraint(
            "CASE WHEN status = 'RUNNING' THEN started_at IS NOT NULL ELSE TRUE END",
            name='ck_running_has_start_time'
        ),
    )

    # Validation methods
    @validates('filename')
    def validate_filename(self, key, filename):
        """Validate filename"""
        if not filename or len(filename.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        # Remove any path components for security
        filename = os.path.basename(filename)
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            raise ValueError('Filename contains invalid characters')
        return filename

    @validates('file_size')
    def validate_file_size(self, key, file_size):
        """Validate file size"""
        if file_size is not None and file_size <= 0:
            raise ValueError('File size must be positive')
        return file_size

    @validates('file_path')
    def validate_file_path(self, key, file_path):
        """Validate file path"""
        if not file_path or len(file_path.strip()) == 0:
            raise ValueError('File path cannot be empty')
        return file_path

    # Hybrid properties
    @hybrid_property
    def is_running(self):
        """Check if script is currently running"""
        return self.status == ScriptStatus.RUNNING

    @hybrid_property
    def is_completed(self):
        """Check if script has completed successfully"""
        return self.status == ScriptStatus.COMPLETED

    @hybrid_property
    def is_failed(self):
        """Check if script failed"""
        return self.status == ScriptStatus.FAILED

    @hybrid_property
    def execution_duration(self):
        """Calculate execution duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @hybrid_property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    @hybrid_property
    def log_line_count(self):
        """Get number of log lines"""
        if self.execution_logs:
            return len(self.execution_logs.split('\n'))
        return 0

    # Class methods for common queries
    @classmethod
    def get_by_user(cls, session, user_id, limit=None, offset=None):
        """Get scripts by user with pagination"""
        query = session.query(cls).filter(cls.user_id == user_id).order_by(cls.created_at.desc())
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all()

    @classmethod
    def get_by_status(cls, session, status, limit=None):
        """Get scripts by status"""
        query = session.query(cls).filter(cls.status == status)
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_running_scripts(cls, session):
        """Get all currently running scripts"""
        return session.query(cls).filter(cls.status == ScriptStatus.RUNNING).all()

    @classmethod
    def get_user_running_scripts(cls, session, user_id):
        """Get user's currently running scripts"""
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.status == ScriptStatus.RUNNING
        ).all()

    @classmethod
    def get_recent_scripts(cls, session, days=7, limit=100):
        """Get recent scripts from the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return session.query(cls).filter(
            cls.created_at >= cutoff_date
        ).order_by(cls.created_at.desc()).limit(limit).all()

    # Instance methods
    def start_execution(self, session):
        """Mark script as started"""
        self.status = ScriptStatus.RUNNING
        self.started_at = datetime.utcnow()
        session.commit()

    def complete_execution(self, session, exit_code=0, execution_time=None, memory_usage=None):
        """Mark script as completed"""
        self.status = ScriptStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.exit_code = exit_code
        if execution_time is not None:
            self.execution_time_seconds = execution_time
        if memory_usage is not None:
            self.memory_usage_mb = memory_usage
        session.commit()

    def fail_execution(self, session, error_message, exit_code=1):
        """Mark script as failed"""
        self.status = ScriptStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.exit_code = exit_code
        session.commit()

    def cancel_execution(self, session):
        """Cancel script execution"""
        self.status = ScriptStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        session.commit()

    def add_log_line(self, session, log_line):
        """Add a line to execution logs"""
        if self.execution_logs:
            self.execution_logs += f"\n{log_line}"
        else:
            self.execution_logs = log_line
        session.commit()

    def get_logs_tail(self, lines=50):
        """Get last N lines of logs"""
        if not self.execution_logs:
            return []
        log_lines = self.execution_logs.split('\n')
        return log_lines[-lines:] if len(log_lines) > lines else log_lines

    def to_dict(self):
        """Convert script to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'file_extension': self.file_extension,
            'status': self.status.value,
            'is_running': self.is_running,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'execution_time_seconds': float(self.execution_time_seconds) if self.execution_time_seconds else None,
            'memory_usage_mb': float(self.memory_usage_mb) if self.memory_usage_mb else None,
            'exit_code': self.exit_code,
            'log_line_count': self.log_line_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'error_message': self.error_message
        }

    def __repr__(self):
        return f"<Script(id={self.id}, filename='{self.filename}', status='{self.status.value}')>"
