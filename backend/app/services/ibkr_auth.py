import httpx
from typing import Optional, Dict, Any
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class IBKRAuthService:
    def __init__(self):
        self.client_id = settings.IBKR_CLIENT_ID
        self.client_secret = settings.IBKR_CLIENT_SECRET
        self.redirect_uri = settings.IBKR_REDIRECT_URI
        self.auth_url = settings.IBKR_AUTH_URL
        self.token_url = settings.IBKR_TOKEN_URL
        self.api_base = settings.IBKR_API_BASE

    def get_authorization_url(self, state: str) -> str:
        """Generate IBKR OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read write",
            "state": state
        }
        
        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_params}"

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Token exchange failed: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Token refresh failed: {e}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from IBKR API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/user", headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def validate_token(self, access_token: str) -> bool:
        """Validate if access token is still valid"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/validate", headers=headers)
                return response.status_code == 200
        except httpx.HTTPError:
            return False


# Global instance
ibkr_auth_service = IBKRAuthService()
