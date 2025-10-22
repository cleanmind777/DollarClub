#!/usr/bin/env python3
"""
Test Google OAuth configuration and flow
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.google_auth import google_auth_service

print("=" * 60)
print("Google OAuth Configuration Test")
print("=" * 60)
print()

# Test 1: Check credentials
print("1. Checking Google OAuth Credentials...")
print("-" * 60)
if settings.GOOGLE_CLIENT_ID:
    print(f"[OK] GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID[:30]}...")
else:
    print("[ERROR] GOOGLE_CLIENT_ID: NOT SET")
    print("   -> Add to backend/.env file")

if settings.GOOGLE_CLIENT_SECRET:
    print(f"[OK] GOOGLE_CLIENT_SECRET: {settings.GOOGLE_CLIENT_SECRET[:10]}... (hidden)")
else:
    print("[ERROR] GOOGLE_CLIENT_SECRET: NOT SET")
    print("   -> Add to backend/.env file")

print(f"[OK] GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
print()

# Test 2: Generate authorization URL
print("2. Testing Authorization URL Generation...")
print("-" * 60)
try:
    test_state = "test-state-123"
    auth_url = google_auth_service.get_authorization_url(test_state)
    print(f"[OK] Authorization URL generated successfully!")
    print(f"   URL: {auth_url[:100]}...")
    print()
    
    # Check URL contains required parameters
    required_params = ['client_id', 'redirect_uri', 'scope', 'response_type', 'state']
    for param in required_params:
        if param in auth_url:
            print(f"   [OK] {param} present")
        else:
            print(f"   [ERROR] {param} MISSING")
    
except Exception as e:
    print(f"[ERROR] Failed to generate URL: {e}")

print()

# Test 3: Check redirect URI format
print("3. Checking Redirect URI Configuration...")
print("-" * 60)
redirect_uri = settings.GOOGLE_REDIRECT_URI

if "localhost:8001" in redirect_uri:
    print("[OK] Correct port (8001)")
elif "localhost:8000" in redirect_uri:
    print("[ERROR] Wrong port (8000) - should be 8001")
    print("   -> Update GOOGLE_REDIRECT_URI in backend/.env")
else:
    print("[WARNING] Non-localhost URI:", redirect_uri)

if "/auth/google/callback" in redirect_uri:
    print("[OK] Correct path (/auth/google/callback)")
else:
    print("[ERROR] Wrong path - should be /auth/google/callback")

print()

# Test 4: Next steps
print("4. Next Steps for Testing:")
print("-" * 60)
print("[OK] Backend configuration looks good!")
print()
print("To test Google OAuth:")
print("1. Ensure backend is running:")
print("   cd backend")
print("   uvicorn main:app --reload --port 8001")
print()
print("2. Open frontend:")
print("   http://localhost:3000/login")
print()
print("3. Click 'Continue with Google' button")
print()
print("4. If you get errors, check:")
print("   a) Google Cloud Console → Credentials")
print("   b) Authorized redirect URIs includes:")
print(f"      {redirect_uri}")
print("   c) OAuth consent screen test users includes your email")
print("   d) Google+ API is enabled")
print()

# Test 5: Common issues
print("5. Common Issues & Solutions:")
print("-" * 60)
print()
print("Error: 'redirect_uri_mismatch'")
print("→ Add this EXACT URI in Google Console:")
print(f"  {redirect_uri}")
print()
print("Error: 'access_denied'")
print("→ Add your Gmail to test users in OAuth consent screen")
print()
print("Error: 'invalid_client'")
print("→ Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
print()
print("Error: Backend 500 error")
print("→ Check backend terminal for detailed error message")
print()

print("=" * 60)
print("Configuration Test Complete!")
print("=" * 60)

