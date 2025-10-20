# Quick Google OAuth Setup

## Problem
You can't register using Google OAuth because credentials are not configured.

---

## Solution: Add Google OAuth Credentials

### Step 1: Get Credentials from Google

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/

2. **Create/Select Project**:
   - Click "Select a project" → "New Project"
   - Name: "DollarClub"
   - Click "Create"

3. **Enable Required APIs**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" → Click "Enable"
   - (Optional) Also enable "People API"

4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - User type: **External** (for development/testing)
   - Click "Create"
   
   **App Information**:
   - App name: `DollarClub Trading Platform`
   - User support email: `your-email@gmail.com`
   - Developer contact: `your-email@gmail.com`
   - Click "Save and Continue"
   
   **Scopes**: Click "Save and Continue" (use default)
   
   **Test Users**:
   - Click "+ Add Users"
   - Add your Gmail address
   - Click "Save and Continue"

5. **Create OAuth Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: `DollarClub Web Client`
   
   **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://localhost:8001
   ```
   
   **Authorized redirect URIs**:
   ```
   http://localhost:8001/auth/google/callback
   ```
   
   - Click "Create"

6. **Copy Your Credentials**:
   - You'll see a popup with:
     - **Client ID**: `123456789-abcdefg.apps.googleusercontent.com`
     - **Client Secret**: `GOCSPX-xxxxxxxxxxxxx`
   - **IMPORTANT**: Copy these somewhere safe!

---

### Step 2: Update backend/.env File

**Open**: `backend/.env`

**Find these lines**:
```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

**Replace with your credentials**:
```env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-secret-here
```

**Example**:
```env
GOOGLE_CLIENT_ID=987654321-abc123xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-1234567890abcdefghij
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback
```

---

### Step 3: Restart Backend

After updating `.env`, restart your backend:

```bash
# Stop the current backend (Ctrl+C)

# Start again
cd backend
uvicorn main:app --reload --port 8001
```

The backend will now load your Google OAuth credentials.

---

### Step 4: Test Google Login

1. **Open login page**: http://localhost:3000/login

2. **Click "Continue with Google"** button

3. **Expected Flow**:
   - Redirects to Google login
   - Select your Google account
   - (First time) Shows consent screen
   - Click "Continue" or "Allow"
   - **Redirects to dashboard** ✅
   - **You're logged in!** ✅

4. **Verify**:
   - Open DevTools → Application → Cookies
   - Should see: `access_token` and `refresh_token`

---

## Troubleshooting

### Error: "Error 400: redirect_uri_mismatch"

**Cause**: The redirect URI in Google Cloud Console doesn't match

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Click your OAuth client ID
3. Under "Authorized redirect URIs", ensure you have:
   ```
   http://localhost:8001/auth/google/callback
   ```
4. **Important**: Must be exact match (port 8001, not 8000!)
5. Save and try again

---

### Error: "Invalid client"

**Cause**: Wrong Client ID or Client Secret

**Solution**:
1. Double-check credentials in `backend/.env`
2. No extra spaces or quotes
3. Copy-paste directly from Google Cloud Console
4. Restart backend after changing .env

---

### Error: "Access denied"

**Cause**: Your Google account is not in test users list

**Solution**:
1. Go to OAuth consent screen in Google Cloud Console
2. Under "Test users", add your Gmail address
3. Click "Save"
4. Try again

---

### Google Login Button Does Nothing

**Cause**: Backend not running or wrong credentials

**Solution**:
1. Check backend is running on port 8001
2. Check browser console for errors
3. Check backend logs for errors
4. Verify `GOOGLE_CLIENT_ID` is not empty

---

## Quick Check Command

Verify your Google OAuth configuration:

```bash
cd backend
python -c "from app.core.config import settings; print('Client ID:', settings.GOOGLE_CLIENT_ID[:20] + '...' if settings.GOOGLE_CLIENT_ID else 'NOT SET ❌'); print('Secret:', 'SET ✅' if settings.GOOGLE_CLIENT_SECRET else 'NOT SET ❌'); print('Redirect:', settings.GOOGLE_REDIRECT_URI)"
```

Expected output:
```
Client ID: 123456789-abcdefghi...  ✅
Secret: SET ✅
Redirect: http://localhost:8001/auth/google/callback
```

If you see "NOT SET ❌", update your `.env` file!

---

## Manual .env Creation (If Needed)

If `.env` doesn't exist, create it manually:

```bash
cd backend
notepad .env
```

Paste this content and update the values:

```env
APP_NAME=DollarClub Trading Platform
DEBUG=true
SECRET_KEY=change-this-to-random-string

DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/dollarclub

REDIS_URL=redis://localhost:6379/0

GOOGLE_CLIENT_ID=YOUR-GOOGLE-CLIENT-ID-HERE
GOOGLE_CLIENT_SECRET=YOUR-GOOGLE-SECRET-HERE
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

MAX_SCRIPT_SIZE=10485760
MAX_EXECUTION_TIME=3600
MAX_CONCURRENT_SCRIPTS=5

SCRIPTS_DIR=scripts
UPLOAD_DIR=uploads

CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

Save and restart backend.

---

## Summary

**Why Google OAuth isn't working**: Missing credentials in `.env`

**To fix**:
1. ✅ Get Client ID & Secret from Google Cloud Console
2. ✅ Add to `backend/.env`
3. ✅ Restart backend
4. ✅ Test login

**See detailed instructions above!** 🎯

