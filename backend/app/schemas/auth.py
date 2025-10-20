from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthResponse(BaseModel):
    authorization_url: str
    state: str
