from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import logging
from datetime import datetime

from ..core.database import get_db
from ..core.security import create_access_token, verify_password, get_password_hash, get_current_user_id
from ..models.user import User, AuthProvider
from ..services.ibkr_auth import ibkr_auth_service
from ..services.google_auth import google_auth_service
from ..schemas.auth import TokenResponse, GoogleAuthResponse
from ..schemas.user import UserCreate, UserLogin, GoogleAuthRequest, IBKRConnectRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


# Helper function to get current user
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


@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user with email and password"""
    print("11111111111111111111111111111111111111111")
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        auth_provider=AuthProvider.EMAIL,
        is_verified=False  # Email verification can be added later
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    jwt_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user with email and password"""
    
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token
    jwt_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse.from_orm(user)
    )


@router.get("/google/login", response_model=GoogleAuthResponse)
async def initiate_google_login():
    """Initiate Google OAuth flow"""
    state = secrets.token_urlsafe(32)
    auth_url = google_auth_service.get_authorization_url(state)
    
    return GoogleAuthResponse(
        authorization_url=auth_url,
        state=state
    )


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for token
        token_data = await google_auth_service.exchange_code_for_token(code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )

        # Get user info
        user_info = await google_auth_service.get_user_info(token_data["access_token"])
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )

        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info["id"]).first()
        
        if not user:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = user_info["id"]
                existing_user.auth_provider = AuthProvider.GOOGLE
                existing_user.is_verified = True
                db.commit()
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=user_info["email"],
                    username=user_info.get("name", user_info["email"].split("@")[0]),
                    google_id=user_info["id"],
                    auth_provider=AuthProvider.GOOGLE,
                    is_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        else:
            # Update existing user info
            user.username = user_info.get("name", user.username)
            user.is_verified = True
            db.commit()

        # Create JWT token for our application
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/auth/callback?token={jwt_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/google/verify", response_model=TokenResponse)
async def verify_google_token(
    token_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """Verify Google ID token and login/register user"""
    try:
        # Verify ID token
        user_info = await google_auth_service.verify_id_token(token_data.id_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )

        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info["sub"]).first()
        
        if not user:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = user_info["sub"]
                existing_user.auth_provider = AuthProvider.GOOGLE
                existing_user.is_verified = True
                db.commit()
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=user_info["email"],
                    username=user_info.get("name", user_info["email"].split("@")[0]),
                    google_id=user_info["sub"],
                    auth_provider=AuthProvider.GOOGLE,
                    is_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        else:
            # Update existing user info
            user.username = user_info.get("name", user.username)
            user.is_verified = True
            db.commit()

        # Create JWT token for our application
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=jwt_token,
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        logger.error(f"Google token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout():
    """Logout user"""
    return {"message": "Successfully logged out"}


# IBKR Integration Endpoints (Secondary Authentication)
@router.get("/ibkr/connect")
async def initiate_ibkr_connect(
    current_user: User = Depends(get_current_user)
):
    """Initiate IBKR OAuth flow for account connection"""
    if current_user.ibkr_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IBKR account already connected"
        )
    
    state = secrets.token_urlsafe(32)
    auth_url = ibkr_auth_service.get_authorization_url(state)
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/ibkr/callback")
async def ibkr_callback(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle IBKR OAuth callback for account connection"""
    try:
        # Exchange code for token
        token_data = await ibkr_auth_service.exchange_code_for_token(code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )

        # Get user info
        user_info = await ibkr_auth_service.get_user_info(token_data["access_token"])
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get IBKR user information"
            )

        # Update user with IBKR credentials
        current_user.ibkr_user_id = user_info["id"]
        current_user.ibkr_access_token = token_data["access_token"]
        current_user.ibkr_refresh_token = token_data.get("refresh_token")
        current_user.ibkr_token_expires_at = token_data.get("expires_at")
        current_user.ibkr_connected_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "IBKR account connected successfully",
            "ibkr_user_id": user_info["id"]
        }
        
    except Exception as e:
        logger.error(f"IBKR OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect IBKR account"
        )


@router.delete("/ibkr/disconnect")
async def disconnect_ibkr(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect IBKR account"""
    if not current_user.ibkr_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No IBKR account connected"
        )
    
    # Clear IBKR credentials
    current_user.ibkr_user_id = None
    current_user.ibkr_access_token = None
    current_user.ibkr_refresh_token = None
    current_user.ibkr_token_expires_at = None
    current_user.ibkr_connected_at = None
    
    db.commit()
    
    return {"message": "IBKR account disconnected successfully"}