import httpx
from typing import Optional, Dict, Any
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class GoogleAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_params}"

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Google token exchange failed: {e}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Google API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get Google user info: {e}")
            return None

    async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Google ID token"""
        try:
            # In production, you should verify the JWT signature
            # For now, we'll decode the payload (not recommended for production)
            import base64
            import json
            
            # Split the token and get the payload
            parts = id_token.split('.')
            if len(parts) != 3:
                return None
                
            # Decode the payload
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            user_info = json.loads(decoded)
            
            # Verify the token is for our app
            if user_info.get('aud') != self.client_id:
                return None
                
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to verify Google ID token: {e}")
            return None


# Global instance
google_auth_service = GoogleAuthService()
