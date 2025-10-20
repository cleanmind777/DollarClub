# Refresh Token Optimization

## Problem
Frontend was making excessive refresh requests, causing performance issues and potential server overload.

## Root Causes

1. **Frequent Polling**: ScriptsPage was refetching every 5 seconds
2. **Refresh Loops**: Multiple simultaneous 401 errors could trigger multiple refresh attempts
3. **No Rate Limiting**: No protection against rapid refresh attempts
4. **Aggressive Caching**: No proper cache configuration

## Fixes Applied

### 1. Reduced Polling Frequency
**File**: `frontend/src/components/ScriptsPage.tsx`

```typescript
// Before: Refetch every 5 seconds
refetchInterval: 5000

// After: Refetch every 30 seconds + better caching
refetchInterval: 30000, // 30 seconds
refetchOnWindowFocus: false, // Don't refetch on window focus
staleTime: 10000, // Consider data fresh for 10 seconds
```

### 2. Improved Refresh Interceptor
**File**: `frontend/src/services/api.ts`

**Added**:
- **Queue System**: Prevents multiple simultaneous refresh attempts
- **Rate Limiting**: 10-second cooldown between refresh attempts
- **Better Error Handling**: Proper queue processing

```typescript
// Global state management
let isRefreshing = false
let failedQueue: Array<{ resolve: Function; reject: Function }> = []
let lastRefreshTime = 0
const REFRESH_COOLDOWN = 10000 // 10 seconds

// Rate limiting check
if (now - lastRefreshTime < REFRESH_COOLDOWN) {
  console.log('Refresh rate limited, redirecting to login')
  window.location.href = '/login'
  return Promise.reject(error)
}
```

### 3. Global Query Configuration
**File**: `frontend/src/main.tsx`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
})
```

## Benefits

✅ **Reduced Server Load**: 6x fewer requests (30s vs 5s polling)  
✅ **No Refresh Loops**: Queue system prevents simultaneous refresh attempts  
✅ **Rate Limited**: Maximum 1 refresh per 10 seconds  
✅ **Better Caching**: Data stays fresh for 5 minutes  
✅ **Improved UX**: Less network activity, smoother experience  

## Request Patterns

### Before (Problematic)
```
00:00 - Scripts list request
00:05 - Scripts list request (401) → Refresh attempt
00:05 - Scripts list request (401) → Refresh attempt (duplicate!)
00:05 - Scripts list request (401) → Refresh attempt (duplicate!)
00:10 - Scripts list request
00:15 - Scripts list request (401) → Refresh attempt
... (continues every 5 seconds)
```

### After (Optimized)
```
00:00 - Scripts list request
00:30 - Scripts list request
01:00 - Scripts list request
01:30 - Scripts list request (401) → Refresh attempt (rate limited)
01:30 - Redirect to login (if refresh fails)
```

## Monitoring

Watch for these console messages:
- `"Refresh rate limited, redirecting to login"` - Normal behavior when rate limited
- Network tab should show much fewer requests
- Scripts page should update every 30 seconds instead of 5

## Configuration

### Adjust Polling Frequency
```typescript
// In ScriptsPage.tsx
refetchInterval: 30000, // Change this value (milliseconds)
```

### Adjust Refresh Cooldown
```typescript
// In api.ts
const REFRESH_COOLDOWN = 10000 // Change this value (milliseconds)
```

### Adjust Cache Times
```typescript
// In main.tsx
staleTime: 5 * 60 * 1000, // Change this value (milliseconds)
cacheTime: 10 * 60 * 1000, // Change this value (milliseconds)
```

---

**Result**: Dramatically reduced refresh requests while maintaining functionality! 🎉
