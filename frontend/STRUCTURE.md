# Frontend Project Structure

## Current Structure

```
src/
├── assets/                 # Static assets (TODO: organize images, fonts, icons)
├── components/             # Shared UI components
│   ├── IBKRIntegration.tsx # IBKR integration component
│   └── Layout.tsx          # App layout with sidebar
├── features/               # Feature-based modules (TODO: organize by domain)
├── hooks/                  # Shared application-wide hooks (TODO: add custom hooks)
├── lib/                    # Third-party library configurations ✅
│   ├── axios.ts            # Axios instance with refresh interceptor
│   └── queryClient.ts      # React Query client configuration
├── pages/                  # Top-level routing components ✅
│   ├── Dashboard.tsx       # Dashboard page
│   ├── Login.tsx           # Login page
│   ├── Scripts.tsx         # Scripts page
│   ├── Settings.tsx        # Settings page
│   └── index.ts            # Barrel export
├── routes/                 # Routing configuration ✅
│   ├── AppRouter.tsx       # Main router with all routes
│   └── ProtectedRoute.tsx  # Auth guard component
├── services/               # API clients and services
│   └── auth.tsx            # Auth context and hooks
├── stores/                 # Global state management (TODO: add if needed)
├── types/                  # Global TypeScript definitions ✅
│   ├── api.ts              # API-related types
│   ├── script.ts           # Script-related types
│   ├── user.ts             # User-related types
│   └── index.ts            # Barrel export
├── utils/                  # Shared utility functions (TODO: add helpers)
├── main.tsx                # App entry point
├── index.css               # Global styles
└── vite-env.d.ts           # Vite environment types

## Path Aliases

All imports use `@/` prefix:
- `@/lib/axios` - Axios instance
- `@/lib/queryClient` - React Query client
- `@/pages` - Page components
- `@/routes` - Routing components
- `@/services/auth` - Auth context
- `@/types` - TypeScript types
- `@/components` - UI components

## Key Features

### ✅ Implemented

1. **Path Aliases**: `@/*` for clean imports
2. **Centralized API Client**: `@/lib/axios` with refresh token handling
3. **React Query Config**: Optimized caching and refetching
4. **Type Safety**: Shared types in `@/types`
5. **Page-based Routing**: Clean separation of pages and components
6. **Protected Routes**: Auth guards via `ProtectedRoute`

### 📦 Clean Structure Achieved

✅ **Removed deprecated files:**
- ~~`components/*Page.tsx`~~ - Moved to `pages/`
- ~~`services/api.ts`~~ - Using `@/lib/axios` now
- ~~`App.tsx`~~ - Using `AppRouter` now

### 🔄 Next Steps

1. **Move to Features**: Organize auth and scripts into `features/`
   - `features/auth/` - Login, register, auth hooks
   - `features/scripts/` - Script upload, list, execution
   - `features/dashboard/` - Dashboard stats and widgets

2. **Create UI Components**: Build reusable primitives
   - `components/ui/Button/`
   - `components/ui/Input/`
   - `components/ui/Modal/`
   - `components/layout/Header/`
   - `components/layout/Sidebar/`

3. **Add Custom Hooks**: Extract reusable logic
   - `hooks/useDebounce.ts`
   - `hooks/useLocalStorage.ts`
   - `hooks/useToggle.ts`

4. **Add Utilities**: Helper functions
   - `utils/formatters.ts` - Date, currency, file size
   - `utils/validators.ts` - Form validation
   - `utils/constants.ts` - App constants

## Import Examples

### Before (Relative Imports)
```tsx
import { api } from '../services/api'
import { useAuth } from '../services/auth'
```

### After (Alias Imports)
```tsx
import { api } from '@/lib/axios'
import { useAuth } from '@/services/auth'
import type { User, Script } from '@/types'
```

## File Organization

### Components
- **Shared**: Reusable across features → `components/`
- **Feature-specific**: Used in one feature → `features/{feature}/components/`
- **Pages**: Top-level route containers → `pages/`

### Types
- **Global**: Used across features → `types/`
- **Feature-specific**: Used in one feature → `features/{feature}/types/`

### Services
- **API Client**: `lib/axios.ts`
- **Domain Services**: `services/` or `features/{feature}/services/`

## Best Practices

1. **Always use `@/` imports** instead of relative paths
2. **Export types from `@/types`** for reusability
3. **Keep pages thin** - delegate logic to components/hooks
4. **Use barrel exports** (`index.ts`) for clean imports
5. **Colocate feature code** in `features/` when it grows
6. **Test components** with `*.test.tsx` files alongside code

---

**Status**: ✅ Clean structure with best practices implemented  
**Next**: Organize into features and add UI component library

