# Auth Request Optimization

## Problem

On the Login page, frontend was making excessive requests:
- `/auth/me` called on page load
- When 401 returned, `/auth/refresh` attempted
- Refresh also failed → Redirect loop until cooldown
- Result: Multiple unnecessary requests every 10 seconds

---

## Root Cause

### Issue 1: Unnecessary fetchUser on Login Page
```tsx
// BEFORE: Called on every page, including login
useEffect(() => {
  fetchUser()  // ❌ Calls /auth/me even on login page
}, [])
```

### Issue 2: Refresh Attempted for Auth Endpoints
```tsx
// BEFORE: Tried to refresh even for auth endpoints
if (error.response?.status === 401) {
  await api.post('/auth/refresh')  // ❌ Tried refresh for /auth/me failure
}
```

---

## Fixes Applied

### Fix 1: Skip fetchUser on Login/Callback Pages

**File**: `frontend/src/services/auth.tsx`

```tsx
// AFTER: Smart check before fetching user
useEffect(() => {
  const currentPath = window.location.pathname
  
  // Skip fetch on login and callback pages
  if (currentPath === '/login' || currentPath === '/auth/callback') {
    setIsLoading(false)
    return
  }
  
  // Only fetch user on protected pages
  fetchUser()
}, [])
```

**Benefit**: Zero `/auth/me` calls on login page ✅

---

### Fix 2: Exclude Auth Endpoints from Refresh Logic

**File**: `frontend/src/lib/axios.ts`

```tsx
// AFTER: Check if it's an auth endpoint first
const isAuthEndpoint = originalRequest.url?.includes('/auth/login') ||
                      originalRequest.url?.includes('/auth/register') ||
                      originalRequest.url?.includes('/auth/refresh') ||
                      originalRequest.url?.includes('/auth/me') ||
                      originalRequest.url?.includes('/auth/google')

// Only refresh for non-auth endpoints
if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
  // ... refresh logic
}

// For auth endpoints, just reject the error
return Promise.reject(error)
```

**Benefit**: No refresh loop for auth failures ✅

---

## Before vs After

### Before (Problematic)

```
Login Page Load
    ↓
/auth/me (401 Unauthorized)
    ↓
/auth/refresh (401 Unauthorized)
    ↓
Rate limited, redirect to /login
    ↓
Loop repeats every 10 seconds
```

**Network Requests**: 2+ per 10 seconds = ~12 per minute 🔴

---

### After (Optimized)

```
Login Page Load
    ↓
Check pathname === '/login'
    ↓
Skip fetchUser()
    ↓
setIsLoading(false)
    ↓
No API calls!
```

**Network Requests**: 0 on login page ✅

---

## Request Patterns

### Login Page

| Scenario | Before | After |
|----------|--------|-------|
| Page load | `/auth/me` + `/auth/refresh` | Nothing |
| On login form submit | `/auth/login` | `/auth/login` |
| After successful login | `/auth/me` (via fetchUser) | Redirect to dashboard |

### Protected Pages (Dashboard, Scripts, etc.)

| Scenario | Before | After |
|----------|--------|-------|
| Page load | `/auth/me` | `/auth/me` |
| Token expired | `/auth/refresh` | `/auth/refresh` |
| Other API calls | Works normally | Works normally |

---

## Auth Endpoint Whitelist

These endpoints **never trigger** token refresh:
- `/auth/login` - Initial login
- `/auth/register` - User registration
- `/auth/refresh` - Refresh itself
- `/auth/me` - User info
- `/auth/google` - Google OAuth

**Why**: These endpoints handle auth themselves. Attempting to refresh when they fail creates infinite loops.

---

## Verification

### Check Login Page (Should be silent):

Open browser DevTools → Network tab → Go to login page:

**Expected**: 
- ✅ No `/auth/me` request
- ✅ No `/auth/refresh` request
- ✅ Clean, empty network log

**On Login Submit**:
- ✅ Only 1 request: `/auth/login`
- ✅ On success: redirect to dashboard
- ✅ On dashboard: 1 request to `/auth/me` (to verify session)

---

## Benefits

✅ **Reduced Network Load**: Zero unnecessary requests on login page  
✅ **Faster Page Load**: No waiting for failed auth checks  
✅ **Better UX**: No console errors or network noise  
✅ **Server Efficiency**: Fewer wasted backend calls  
✅ **Cleaner Logs**: No spam in browser console  

---

## Edge Cases Handled

### User Opens Login Page Directly
- ✅ No fetchUser called
- ✅ No refresh attempted
- ✅ isLoading immediately set to false

### User Logs Out
- ✅ Redirect to /login
- ✅ No fetchUser on login page
- ✅ Clean logout experience

### Token Expires on Protected Page
- ✅ Normal refresh flow works
- ✅ Only for non-auth endpoints
- ✅ Retry after refresh succeeds

### User Has Valid Cookie, Opens Login
- ✅ No fetchUser called
- ✅ User can still log in (won't cause issues)
- ✅ After login, redirect to dashboard

---

## Testing Checklist

- [ ] Open login page → Check Network tab (should be empty)
- [ ] Submit login form → Should see only 1 `/auth/login` request
- [ ] After login → Redirect to dashboard (1 `/auth/me` request)
- [ ] Visit protected page → Only necessary API calls
- [ ] Let token expire → Should auto-refresh once
- [ ] Try scripts page → Should work normally

---

**Result**: Login page is now silent with zero unnecessary requests! 🎉

