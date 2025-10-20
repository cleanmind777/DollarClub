# Google OAuth Troubleshooting Guide

## Issue: "Authentication failed" Error

When you try to login with Google and see `{"detail":"Authentication failed"}`, this means the OAuth flow started but failed during the callback process.

---

## What I've Fixed

### ✅ **Improvements Made:**

1. **Better Error Logging** - Backend now logs detailed errors
2. **Error Display** - Frontend shows specific error messages
3. **URL Encoding** - Fixed parameter encoding in authorization URL
4. **Cookie-based Auth** - Callback now sets HttpOnly cookies correctly

---

## How to Diagnose the Issue

### Step 1: Check Backend Logs

**When you try Google login**, watch the backend terminal for detailed errors:

```bash
cd backend
uvicorn main:app --reload --port 8001
```

**Look for these log messages**:

```
INFO: Google OAuth callback received with code: ...
INFO: Successfully exchanged code for token
INFO: Retrieved user info for: user@gmail.com
INFO: User created/updated successfully
```

**Or error messages**:
```
ERROR: Failed to exchange code for token
ERROR: Response status: 400
ERROR: Response body: {"error": "invalid_grant"}
```

The error logs will tell you **exactly what's failing**.

---

## Common Errors & Solutions

### Error 1: "Failed to exchange code for token"

**Possible Causes**:

#### A) **Invalid Client Secret**

**Symptom**:
```
ERROR: Google token exchange failed
ERROR: Response status: 401
ERROR: Response body: {"error": "unauthorized_client"}
```

**Solution**:
1. Check `backend/.env`:
   ```env
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
   ```
2. Verify the secret is correct in Google Cloud Console
3. Copy-paste carefully (no extra spaces!)
4. Restart backend

---

#### B) **Redirect URI Mismatch**

**Symptom**:
```
ERROR: Response status: 400
ERROR: Response body: {"error": "redirect_uri_mismatch"}
```

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add **exactly**:
   ```
   http://localhost:8001/auth/google/callback
   ```
4. **Important**: Must be port 8001 (not 8000!)
5. Save and try again

---

#### C) **Authorization Code Already Used**

**Symptom**:
```
ERROR: Response body: {"error": "invalid_grant"}
```

**Solution**:
- This happens if you refresh the callback page
- Just try logging in again (fresh attempt)
- Code can only be used once

---

### Error 2: "Failed to get user information"

**Symptom**:
```
ERROR: Failed to get user info from Google
ERROR: Response status: 401
```

**Possible Causes**:

#### A) **Google+ API Not Enabled**

**Solution**:
1. Go to Google Cloud Console
2. APIs & Services → Library
3. Search "Google+ API"
4. Click "Enable"
5. Try login again

#### B) **Invalid Access Token**

**Solution**:
- Usually means token exchange failed
- Check previous errors in logs
- Verify client credentials

---

### Error 3: Database/User Creation Error

**Symptom**:
```
ERROR: Google OAuth callback error: ...
(followed by database error)
```

**Solution**:
1. Check database is running:
   ```bash
   psql -U postgres -d dollarclub -c "SELECT 1;"
   ```
2. Check database connection in `.env`
3. Verify `users` table exists

---

## Step-by-Step Debugging

### 1. **Verify Credentials Are Set**

```bash
cd backend
python -c "from app.core.config import settings; print('Client ID:', 'SET' if settings.GOOGLE_CLIENT_ID else 'NOT SET'); print('Secret:', 'SET' if settings.GOOGLE_CLIENT_SECRET else 'NOT SET')"
```

Expected output:
```
Client ID: SET
Secret: SET
```

If either shows "NOT SET", update `backend/.env`.

---

### 2. **Test Authorization URL**

```bash
curl http://localhost:8001/auth/google/login
```

Expected:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "random-state"
}
```

If you get an error, backend isn't running.

---

### 3. **Try Google Login**

1. Open: http://localhost:3000/login
2. Click "Continue with Google"
3. Watch backend terminal for logs
4. Note any error messages

---

### 4. **Check Google Cloud Console Configuration**

#### Required Settings:

**OAuth Consent Screen**:
- ✅ User type: External
- ✅ App name: Set
- ✅ Test users: Your Gmail added

**Credentials (OAuth 2.0 Client)**:
- ✅ Authorized JavaScript origins:
  ```
  http://localhost:3000
  http://localhost:8001
  ```
- ✅ Authorized redirect URIs:
  ```
  http://localhost:8001/auth/google/callback
  ```

**APIs Enabled**:
- ✅ Google+ API (or People API)

---

## Quick Fixes

### Fix 1: Missing Client Secret

```bash
# Edit backend/.env
notepad backend\.env

# Add your secret:
GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-secret-here

# Restart backend
cd backend
uvicorn main:app --reload --port 8001
```

---

### Fix 2: Wrong Redirect URI

**In Google Cloud Console**:
1. Credentials → Your OAuth Client
2. Authorized redirect URIs → Add:
   ```
   http://localhost:8001/auth/google/callback
   ```
3. Save
4. Try login again

---

### Fix 3: Not a Test User

**In Google Cloud Console**:
1. OAuth consent screen
2. Test users → Add users
3. Enter your Gmail address
4. Save
5. Try login again

---

## What Happens Now (After Fixes)

With improved error logging, when you try Google login:

### If Successful:
```
Backend logs:
INFO: Google OAuth callback received with code: ...
INFO: Successfully exchanged code for token  
INFO: Successfully retrieved user info for: user@gmail.com
INFO: Retrieved user info for: user@gmail.com
INFO: User created/updated successfully

Frontend:
→ Redirects to http://localhost:3000/dashboard
→ You're logged in! ✅
```

### If Failed:
```
Backend logs:
ERROR: Failed to exchange code for token
ERROR: Response status: 400
ERROR: Response body: {"error": "invalid_client", "error_description": "..."}

Frontend:
→ Redirects to http://localhost:3000/login?error=google_auth_failed&message=...
→ Shows specific error message in red box ✅
```

---

## Most Likely Issue

Based on the diagnostic output, **your Client Secret is probably not set** in `.env`.

**To fix**:

1. **Get Client Secret**:
   - Go to https://console.cloud.google.com/apis/credentials
   - Click your OAuth 2.0 Client ID
   - View/copy Client Secret

2. **Add to backend/.env**:
   ```env
   GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-secret-here
   ```

3. **Restart backend**:
   ```bash
   # Stop backend (Ctrl+C)
   cd backend
   uvicorn main:app --reload --port 8001
   ```

4. **Try Google login again**

---

## Testing Checklist

After making changes:

- [ ] Client ID set in `.env`
- [ ] Client Secret set in `.env`
- [ ] Redirect URI: `http://localhost:8001/auth/google/callback`
- [ ] Backend restarted
- [ ] Google Console has matching redirect URI
- [ ] Your Gmail is in test users
- [ ] Google+ API enabled
- [ ] Try login → Watch backend logs
- [ ] Note specific error if it fails

---

**Next**: Try Google login and share the **backend log output** to diagnose the exact issue! 🔍

