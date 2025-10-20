# Google OAuth Setup Guide

## Overview

DollarClub now supports Google OAuth login with cookie-based authentication. This guide shows you how to configure and use it.

---

## What Was Fixed

### ✅ **Issues Resolved**:

1. **Cookie-based Authentication** - Updated callback to set HttpOnly cookies instead of URL tokens
2. **Correct Port** - Changed redirect URI from port 8000 → 8001
3. **Direct Redirect** - Backend now redirects directly to `/dashboard` with cookies
4. **Removed Token Callback** - No longer need frontend callback handler

---

## Google OAuth Flow

```
User clicks "Continue with Google"
    ↓
Frontend: GET /auth/google/login
    ↓
Backend: Returns Google authorization URL
    ↓
User redirected to Google login
    ↓
User authenticates with Google
    ↓
Google redirects to: http://localhost:8001/auth/google/callback?code=xxx
    ↓
Backend: Exchanges code for user info
    ↓
Backend: Creates/updates user in database
    ↓
Backend: Sets access_token + refresh_token cookies
    ↓
Backend: Redirects to http://localhost:3000/dashboard
    ↓
User lands on dashboard (authenticated via cookies) ✅
```

---

## Setup Instructions

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. **Create a Project** (or select existing):
   - Click "Select a project" → "New Project"
   - Name: "DollarClub" (or any name)
   - Click "Create"

3. **Enable Google+ API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google+ API"
   - Click "Enable"

4. **Create OAuth Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "DollarClub Web Client"

5. **Configure OAuth Consent Screen** (if prompted):
   - User type: "External" (for testing)
   - App name: "DollarClub Trading Platform"
   - User support email: your-email@gmail.com
   - Developer contact: your-email@gmail.com
   - Click "Save and Continue"
   - Scopes: Click "Save and Continue" (default scopes)
   - Test users: Add your Google account email
   - Click "Save and Continue"

6. **Add Authorized Redirect URIs**:
   ```
   http://localhost:8001/auth/google/callback
   ```
   - Click "Create"

7. **Copy Credentials**:
   - You'll see your Client ID and Client Secret
   - **Save these securely!**

---

### Step 2: Configure Backend

Create `backend/.env` (if not exists):

```env
# Application
APP_NAME=DollarClub Trading Platform
DEBUG=true
SECRET_KEY=your-super-secret-key-change-this

# Database
DATABASE_URL=postgresql://user:password@localhost/dollarclub

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth - REPLACE WITH YOUR CREDENTIALS
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# Script Execution
MAX_SCRIPT_SIZE=10485760
MAX_EXECUTION_TIME=3600
MAX_CONCURRENT_SCRIPTS=5

# File Storage
SCRIPTS_DIR=scripts
UPLOAD_DIR=uploads

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**Important**: Replace `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` with your actual values from Google Cloud Console.

---

### Step 3: Verify Backend Configuration

Check your settings are loaded:

```bash
cd backend
python -c "from app.core.config import settings; print(f'Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...')"
```

Expected output:
```
Client ID: 123456789-abcdefgh...
```

If you see empty string, your `.env` file is not being loaded properly.

---

## How to Use

### Frontend Login Page

1. User clicks **"Continue with Google"** button
2. Browser redirects to Google login
3. User logs in with Google account
4. Google redirects back to backend
5. Backend sets cookies and redirects to dashboard
6. **User is authenticated!** ✅

---

## Testing Flow

### 1. Test Authorization URL Generation

```bash
curl http://localhost:8001/auth/google/login
```

Expected response:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "random-state-token"
}
```

### 2. Test Full Flow

1. Start backend:
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open browser: `http://localhost:3000/login`

4. Click **"Continue with Google"**

5. Login with your Google account

6. **Expected**: Redirected to dashboard, authenticated

7. Verify cookies:
   - Open DevTools → Application → Cookies → `http://localhost:3000`
   - You should see: `access_token` and `refresh_token`

---

## Troubleshooting

### Issue: "Error 400: redirect_uri_mismatch"

**Cause**: Redirect URI in Google Cloud Console doesn't match backend configuration

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth client
3. Add exact URI: `http://localhost:8001/auth/google/callback`
4. Save and try again

---

### Issue: "Failed to exchange code for token"

**Cause**: Invalid client secret or client ID

**Solution**:
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Check for typos or extra spaces
3. Regenerate credentials if needed

---

### Issue: "Authentication failed"

**Cause**: Backend can't get user info from Google

**Solution**:
1. Check backend logs for detailed error
2. Verify Google+ API is enabled
3. Check scopes include "email" and "profile"

---

### Issue: "Redirects to login page immediately"

**Cause**: Cookies not being set

**Solution**:
1. Check backend sets cookies in callback (line 247-262)
2. Verify `withCredentials: true` in frontend axios (lib/axios.ts)
3. Check CORS settings allow credentials

---

## Security Notes

### Development vs Production

**Development** (localhost):
- `secure: false` - Cookies work over HTTP
- `redirect_uri: http://localhost:8001/...`
- `frontend_url: http://localhost:3000/...`

**Production** (deployed):
- `secure: true` - Cookies require HTTPS
- `redirect_uri: https://yourdomain.com/auth/google/callback`
- `frontend_url: https://yourdomain.com/dashboard`
- Update authorized redirect URIs in Google Cloud Console

---

## Configuration Variables

### Backend (.env)

```env
# Required
GOOGLE_CLIENT_ID=<from-google-cloud>
GOOGLE_CLIENT_SECRET=<from-google-cloud>
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# Development
DEBUG=true

# Production
DEBUG=false
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/auth/google/callback
```

### Google Cloud Console

**Authorized JavaScript origins**:
```
http://localhost:3000
https://yourdomain.com
```

**Authorized redirect URIs**:
```
http://localhost:8001/auth/google/callback
https://api.yourdomain.com/auth/google/callback
```

---

## Code Changes Made

### Backend (`backend/app/api/auth.py`)

**Before**:
```python
# Old: Token in URL
jwt_token = create_access_token(data={"sub": str(user.id)})
frontend_url = f"http://localhost:3000/auth/callback?token={jwt_token}"
return RedirectResponse(url=frontend_url)
```

**After**:
```python
# New: Cookies + direct redirect
access_token = create_access_token(data={"sub": str(user.id)})
refresh_token = create_refresh_token(data={"sub": str(user.id)})

redirect_response = RedirectResponse(url="http://localhost:3000/dashboard")
redirect_response.set_cookie(key="access_token", value=access_token, httponly=True, ...)
redirect_response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, ...)
return redirect_response
```

### Frontend (`frontend/src/services/auth.tsx`)

**Removed**:
- ❌ `handleAuthCallback` function
- ❌ `/auth/callback` route handling
- ❌ Token extraction from URL

**Why**: Backend now sets cookies and redirects directly to dashboard

---

## Verification Checklist

- [ ] Google Cloud Console project created
- [ ] OAuth credentials created
- [ ] Authorized redirect URI added: `http://localhost:8001/auth/google/callback`
- [ ] Client ID and Secret copied
- [ ] `backend/.env` updated with credentials
- [ ] Backend restarted to load new .env
- [ ] Frontend running on port 3000
- [ ] Backend running on port 8001
- [ ] Test Google login button
- [ ] Verify redirect to dashboard
- [ ] Check cookies are set

---

## Expected Behavior

### ✅ Success Flow:

1. Click "Continue with Google"
2. Redirected to Google login
3. Enter Google credentials
4. Consent screen (first time only)
5. **Redirected to dashboard**
6. **Authenticated with cookies**
7. Can access all pages

### ❌ Common Errors:

| Error | Cause | Solution |
|-------|-------|----------|
| redirect_uri_mismatch | URI not in Google Console | Add exact URI |
| invalid_client | Wrong client ID/secret | Check .env values |
| access_denied | User cancelled | Normal behavior |
| Authentication failed | Backend error | Check logs |

---

## Quick Setup (TL;DR)

```bash
# 1. Get Google OAuth credentials from console.cloud.google.com
# 2. Add to backend/.env:
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# 3. In Google Console, add authorized redirect URI:
http://localhost:8001/auth/google/callback

# 4. Restart backend
cd backend
uvicorn main:app --reload --port 8001

# 5. Test
Open http://localhost:3000/login → Click "Continue with Google"
```

---

**Google OAuth is now fixed and uses cookie-based authentication! 🎉**

