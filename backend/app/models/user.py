from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import enum
import re
from datetime import datetime
from ..core.database import Base


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Null for OAuth users
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    google_id = Column(String(100), unique=True, index=True, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # IBKR Integration (optional, after main auth)
    ibkr_user_id = Column(String(100), unique=True, index=True, nullable=True)
    ibkr_access_token = Column(Text, nullable=True)
    ibkr_refresh_token = Column(Text, nullable=True)
    ibkr_token_expires_at = Column(DateTime, nullable=True)
    ibkr_connected_at = Column(DateTime, nullable=True)

    # Relationships
    scripts = relationship(
        "Script", 
        back_populates="owner", 
        cascade="all, delete-orphan",
        lazy="select"  # Lazy loading for better performance
    )

    # Indexes for better query performance
    __table_args__ = (
        Index('ix_users_email_provider', 'email', 'auth_provider'),
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_last_login', 'last_login_at'),
        CheckConstraint(
            "CASE WHEN auth_provider = 'EMAIL' THEN hashed_password IS NOT NULL ELSE TRUE END",
            name='ck_email_password_required'
        ),
        CheckConstraint(
            "CASE WHEN auth_provider = 'GOOGLE' THEN google_id IS NOT NULL ELSE TRUE END",
            name='ck_google_id_required'
        ),
    )

    # Validation methods
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()

    @validates('username')
    def validate_username(self, key, username):
        """Validate username format"""
        if len(username) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return username

    # Hybrid properties
    @hybrid_property
    def is_ibkr_connected(self):
        """Check if IBKR account is connected"""
        return self.ibkr_user_id is not None

    @hybrid_property
    def account_age_days(self):
        """Calculate account age in days"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at.replace(tzinfo=None)).days
        return 0

    @hybrid_property
    def script_count(self):
        """Get total number of scripts"""
        return len(self.scripts) if self.scripts else 0

    # Class methods for common queries
    @classmethod
    def get_by_email(cls, session, email):
        """Get user by email"""
        return session.query(cls).filter(cls.email == email.lower()).first()

    @classmethod
    def get_by_google_id(cls, session, google_id):
        """Get user by Google ID"""
        return session.query(cls).filter(cls.google_id == google_id).first()

    @classmethod
    def get_active_users(cls, session):
        """Get all active users"""
        return session.query(cls).filter(cls.is_active == True).all()

    @classmethod
    def get_users_with_ibkr(cls, session):
        """Get users with connected IBKR accounts"""
        return session.query(cls).filter(cls.ibkr_user_id.isnot(None)).all()

    # Instance methods
    def update_last_login(self, session):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
        session.commit()

    def connect_ibkr(self, session, ibkr_user_id, access_token, refresh_token=None, expires_at=None):
        """Connect IBKR account"""
        self.ibkr_user_id = ibkr_user_id
        self.ibkr_access_token = access_token
        self.ibkr_refresh_token = refresh_token
        self.ibkr_token_expires_at = expires_at
        self.ibkr_connected_at = datetime.utcnow()
        session.commit()

    def disconnect_ibkr(self, session):
        """Disconnect IBKR account"""
        self.ibkr_user_id = None
        self.ibkr_access_token = None
        self.ibkr_refresh_token = None
        self.ibkr_token_expires_at = None
        self.ibkr_connected_at = None
        session.commit()

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'auth_provider': self.auth_provider.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_ibkr_connected': self.is_ibkr_connected,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'script_count': self.script_count,
            'account_age_days': self.account_age_days
        }

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
