from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..core.database import get_db_session
from ..models.user import User, AuthProvider
from ..models.script import Script, ScriptStatus

logger = logging.getLogger(__name__)


class UserService:
    """Service class for User database operations"""
    
    @staticmethod
    def create_user(session: Session, email: str, username: str, 
                   hashed_password: str = None, auth_provider: AuthProvider = AuthProvider.EMAIL,
                   google_id: str = None) -> User:
        """Create a new user"""
        user = User(
            email=email.lower(),
            username=username,
            hashed_password=hashed_password,
            auth_provider=auth_provider,
            google_id=google_id
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Created user: {user.email}")
        return user
    
    @staticmethod
    def get_by_id(session: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(session: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return User.get_by_email(session, email)
    
    @staticmethod
    def get_by_google_id(session: Session, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        return User.get_by_google_id(session, google_id)
    
    @staticmethod
    def update_user(session: Session, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields"""
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        session.commit()
        session.refresh(user)
        logger.info(f"Updated user: {user.email}")
        return user
    
    @staticmethod
    def deactivate_user(session: Session, user_id: int) -> bool:
        """Deactivate user account"""
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        session.commit()
        logger.info(f"Deactivated user: {user.email}")
        return True
    
    @staticmethod
    def get_users_with_pagination(session: Session, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get users with pagination"""
        offset = (page - 1) * per_page
        
        # Get total count
        total = session.query(User).count()
        
        # Get users for current page
        users = session.query(User).offset(offset).limit(per_page).all()
        
        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def search_users(session: Session, query: str, limit: int = 20) -> List[User]:
        """Search users by email or username"""
        search_term = f"%{query.lower()}%"
        return session.query(User).filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        ).limit(limit).all()
    
    @staticmethod
    def get_user_stats(session: Session) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = session.query(User).count()
        active_users = session.query(User).filter(User.is_active == True).count()
        verified_users = session.query(User).filter(User.is_verified == True).count()
        ibkr_connected = session.query(User).filter(User.ibkr_user_id.isnot(None)).count()
        
        # Users by auth provider
        email_users = session.query(User).filter(User.auth_provider == AuthProvider.EMAIL).count()
        google_users = session.query(User).filter(User.auth_provider == AuthProvider.GOOGLE).count()
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = session.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'ibkr_connected': ibkr_connected,
            'email_users': email_users,
            'google_users': google_users,
            'recent_registrations': recent_registrations
        }


class ScriptService:
    """Service class for Script database operations"""
    
    @staticmethod
    def create_script(session: Session, user_id: int, filename: str, 
                     original_filename: str, file_path: str, file_size: int) -> Script:
        """Create a new script"""
        script = Script(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_extension=filename.split('.')[-1] if '.' in filename else None
        )
        session.add(script)
        session.commit()
        session.refresh(script)
        logger.info(f"Created script: {script.filename} for user {user_id}")
        return script
    
    @staticmethod
    def get_by_id(session: Session, script_id: int) -> Optional[Script]:
        """Get script by ID"""
        return session.query(Script).filter(Script.id == script_id).first()
    
    @staticmethod
    def get_by_user(session: Session, user_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get user's scripts with pagination"""
        offset = (page - 1) * per_page
        
        # Get total count
        total = session.query(Script).filter(Script.user_id == user_id).count()
        
        # Get scripts for current page
        scripts = Script.get_by_user(session, user_id, limit=per_page, offset=offset)
        
        return {
            'scripts': scripts,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def get_running_scripts(session: Session) -> List[Script]:
        """Get all currently running scripts"""
        return Script.get_running_scripts(session)
    
    @staticmethod
    def get_user_running_scripts(session: Session, user_id: int) -> List[Script]:
        """Get user's currently running scripts"""
        return Script.get_user_running_scripts(session, user_id)
    
    @staticmethod
    def update_script_status(session: Session, script_id: int, status: ScriptStatus, 
                           **kwargs) -> Optional[Script]:
        """Update script status and related fields"""
        script = session.query(Script).filter(Script.id == script_id).first()
        if not script:
            return None
        
        script.status = status
        
        # Update related fields based on status
        if status == ScriptStatus.RUNNING:
            script.started_at = datetime.utcnow()
        elif status in [ScriptStatus.COMPLETED, ScriptStatus.FAILED, ScriptStatus.CANCELLED]:
            script.completed_at = datetime.utcnow()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(script, key):
                setattr(script, key, value)
        
        session.commit()
        session.refresh(script)
        logger.info(f"Updated script {script_id} status to {status.value}")
        return script
    
    @staticmethod
    def add_execution_log(session: Session, script_id: int, log_line: str) -> bool:
        """Add a line to script execution logs"""
        script = session.query(Script).filter(Script.id == script_id).first()
        if not script:
            return False
        
        script.add_log_line(session, log_line)
        return True
    
    @staticmethod
    def delete_script(session: Session, script_id: int, user_id: int) -> bool:
        """Delete a script (only if it belongs to the user)"""
        script = session.query(Script).filter(
            and_(Script.id == script_id, Script.user_id == user_id)
        ).first()
        
        if not script:
            return False
        
        session.delete(script)
        session.commit()
        logger.info(f"Deleted script: {script.filename}")
        return True
    
    @staticmethod
    def get_script_stats(session: Session) -> Dict[str, Any]:
        """Get script statistics"""
        total_scripts = session.query(Script).count()
        running_scripts = session.query(Script).filter(Script.status == ScriptStatus.RUNNING).count()
        completed_scripts = session.query(Script).filter(Script.status == ScriptStatus.COMPLETED).count()
        failed_scripts = session.query(Script).filter(Script.status == ScriptStatus.FAILED).count()
        
        # Total file size
        total_size = session.query(func.sum(Script.file_size)).scalar() or 0
        
        # Average execution time
        avg_execution_time = session.query(func.avg(Script.execution_time_seconds)).filter(
            Script.execution_time_seconds.isnot(None)
        ).scalar() or 0
        
        # Recent uploads (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = session.query(Script).filter(
            Script.created_at >= seven_days_ago
        ).count()
        
        return {
            'total_scripts': total_scripts,
            'running_scripts': running_scripts,
            'completed_scripts': completed_scripts,
            'failed_scripts': failed_scripts,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'avg_execution_time': float(avg_execution_time) if avg_execution_time else 0,
            'recent_uploads': recent_uploads
        }
    
    @staticmethod
    def get_scripts_by_status(session: Session, status: ScriptStatus, limit: int = 100) -> List[Script]:
        """Get scripts by status"""
        return Script.get_by_status(session, status, limit)
    
    @staticmethod
    def get_recent_scripts(session: Session, days: int = 7, limit: int = 100) -> List[Script]:
        """Get recent scripts"""
        return Script.get_recent_scripts(session, days, limit)


class DatabaseService:
    """Main database service class"""
    
    @staticmethod
    def get_health_check(session: Session) -> Dict[str, Any]:
        """Get database health check information"""
        try:
            # Test basic connectivity
            session.execute(text("SELECT 1"))
            
            # Get basic stats
            user_stats = UserService.get_user_stats(session)
            script_stats = ScriptService.get_script_stats(session)
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'user_stats': user_stats,
                'script_stats': script_stats
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def cleanup_old_logs(session: Session, days: int = 30) -> int:
        """Clean up old execution logs to save space"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get old completed/failed scripts
        old_scripts = session.query(Script).filter(
            and_(
                Script.completed_at <= cutoff_date,
                or_(
                    Script.status == ScriptStatus.COMPLETED,
                    Script.status == ScriptStatus.FAILED
                )
            )
        ).all()
        
        cleaned_count = 0
        for script in old_scripts:
            if script.execution_logs and len(script.execution_logs) > 1000:  # Keep only last 1000 chars
                script.execution_logs = script.execution_logs[-1000:]
                cleaned_count += 1
        
        session.commit()
        logger.info(f"Cleaned up logs for {cleaned_count} scripts")
        return cleaned_count
