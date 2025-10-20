from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import logging
import re
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import create_access_token, create_refresh_token, verify_password, get_password_hash, get_current_user_id, get_token_from_cookie, verify_token
from ..core.config import settings
from ..models.user import User, AuthProvider
from ..services.ibkr_auth import ibkr_auth_service
from ..services.google_auth import google_auth_service
from ..schemas.auth import TokenResponse, GoogleAuthResponse
from ..schemas.user import UserCreate, UserLogin, GoogleAuthRequest, IBKRConnectRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# Cookie settings
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
ACCESS_COOKIE_MAX_AGE = 5 * 60  # 5 minutes
REFRESH_COOKIE_MAX_AGE = 15 * 60  # 15 minutes


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
    response: Response,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user with email and password"""
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
    
    # Create JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set HTTP-only cookies
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    response: Response,
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
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set HTTP-only cookies
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE
    )
    
    return TokenResponse(
        access_token=access_token,
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
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        logger.info(f"Google OAuth callback received with code: {code[:20]}...")
        
        # Exchange code for token
        token_data = await google_auth_service.exchange_code_for_token(code)
        if not token_data:
            logger.error("Failed to exchange code for token")
            raise Exception("Failed to exchange authorization code for token")

        logger.info("Successfully exchanged code for token")

        # Get user info
        user_info = await google_auth_service.get_user_info(token_data["access_token"])
        if not user_info:
            logger.error("Failed to get user info from Google")
            raise Exception("Failed to retrieve user information from Google")
        
        logger.info(f"Retrieved user info for: {user_info.get('email')}")

        # Sanitize username for database constraints
        # Google names may contain spaces/special chars, but our DB requires alphanumeric + _-
        google_name = user_info.get("name", user_info["email"].split("@")[0])
        sanitized_username = re.sub(r'[^a-zA-Z0-9_-]', '_', google_name)
        
        # Ensure minimum length
        if len(sanitized_username) < 3:
            sanitized_username = user_info["email"].split("@")[0]
        
        logger.info(f"Sanitized username: '{google_name}' -> '{sanitized_username}'")
        
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
                existing_user.last_login_at = datetime.utcnow()
                db.commit()
                user = existing_user
                logger.info(f"Linked Google account to existing user: {user.email}")
            else:
                # Create new user
                user = User(
                    email=user_info["email"],
                    username=sanitized_username,
                    google_id=user_info["id"],
                    auth_provider=AuthProvider.GOOGLE,
                    is_verified=True,
                    last_login_at=datetime.utcnow()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user from Google: {user.email}")
        else:
            # Update existing user info (don't change username to avoid breaking references)
            user.is_verified = True
            user.last_login_at = datetime.utcnow()
            db.commit()
            logger.info(f"Logged in existing Google user: {user.email}")

        # Create JWT tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create response with redirect
        redirect_response = RedirectResponse(url="http://localhost:3000/dashboard")
        
        # Set HTTP-only cookies
        redirect_response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=ACCESS_COOKIE_MAX_AGE
        )
        redirect_response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=REFRESH_COOKIE_MAX_AGE
        )
        
        return redirect_response
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}", exc_info=True)
        # Redirect to login with error message
        error_url = f"http://localhost:3000/login?error=google_auth_failed&message={str(e)}"
        return RedirectResponse(url=error_url)


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


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Get refresh token from cookie
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set new access token cookie
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=new_access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE
    )
    
    return {"message": "Token refreshed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user information from cookie"""
    # Get token from cookie
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify token and get user ID
    user_id = get_current_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the authentication cookies"""
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
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