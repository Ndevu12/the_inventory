# Cookie-Based Authentication Migration Tasks

> Tasks are designed for **maximum parallel execution** unless noted in **Depends On**. The goal is to migrate JWT token storage from localStorage (XSS-vulnerable) to HttpOnly cookies (XSS-protected, browser-managed).

---

## Overview

**Current State:** Tokens stored in localStorage via Zustand; frontend reads and manually sets `Authorization: Bearer` header.

**Target State:** Tokens stored in HttpOnly cookies; browser automatically sends cookies; frontend stores only non-sensitive data (user, tenant, memberships) in Zustand.

**Security Gain:** XSS attack cannot exfiltrate tokens; tokens are inaccessible from JavaScript.

---

## Pre-Implementation Decision Checklist (Reuse First)

Use this checklist before touching auth code for any `COOKIE-*` task. If an item is already implemented, **reuse and tighten** it instead of creating parallel logic.

### 1) UI channel and auth mechanism mapping

- **`/frontend` (tenant UI):** Cookie-based JWT flow (`access_token` + `refresh_token`) for API access.
- **Wagtail admin (`/admin/`):** Django session + CSRF flow (`sessionid`/`csrftoken`) for staff/admin operations.
- Confirm the task targets one channel or both. Do not conflate SPA JWT cookies with Wagtail session cookies.

### 2) Existing implementation inventory

Before implementing, verify current behavior in:

- `src/api/views/auth.py` for login/refresh/logout cookie handling
- `src/api/authentication.py` for header-vs-cookie precedence
- `src/api/middleware.py` for early request authentication
- `src/the_inventory/settings/base.py`, `src/the_inventory/settings/dev.py`, `src/the_inventory/settings/production.py` for cookie flags and max-age
- `tests/api/test_auth_api.py` and `tests/api/test_cookie_auth.py` for existing expectations

If behavior already exists, prefer focused fixes (consistency, tests, edge cases) over refactors.

### 3) Decision questions (must answer in task notes/PR)

1. **Cookie source of truth:** Should JWT cookies continue to use `JWT_COOKIE_*` settings, or intentionally inherit from session cookie flags?
2. **Lifetime alignment:** Are JWT cookie max-age values intentionally different from `SIMPLE_JWT` lifetimes?
3. **Logout symmetry:** Are cookie deletion parameters (`path`, `domain`, `secure`, `samesite`) aligned with creation for reliable clearing?
4. **CSRF model:** For browser cookie JWT requests, what CSRF protections are expected for unsafe methods?
5. **Compatibility boundary:** Which clients must continue to rely on token JSON body responses (mobile/API tools)?
6. **Test ownership:** Which existing tests will be updated, and can overlap be reduced instead of adding duplicates?

### 4) Non-duplication guardrails

- Do not add a second cookie-writing path if `LoginView`/`RefreshView` already sets cookies.
- Do not introduce another authenticator if `CookieJWTAuthentication` already satisfies fallback order.
- Do not replace session auth used by Wagtail admin unless the task explicitly asks for admin auth changes.
- Extend existing tests first; only add new files when coverage cannot fit current suites cleanly.

---

## Tasks — Auth Cookie Migration (COOKIE-01–COOKIE-07)

### COOKIE-01 — Backend: Configure cookie-based JWT response

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes (must be first; others depend structurally)

**Problem:**
Backend `/api/v1/auth/login/` and `/api/v1/auth/refresh/` currently return tokens in JSON response body. Frontend must set them in localStorage manually. Need to switch to HttpOnly cookie response.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Login endpoint | Set `access_token` and `refresh_token` in HttpOnly cookies on successful login |
| Refresh endpoint | Accept refresh token from cookie; return new access token in cookie |
| Cookie security | HttpOnly, Secure, SameSite=Lax (or custom per environment) |
| Backward compatibility | Keep JSON response body with tokens for non-browser clients (mobile, API). Cookie takes precedence for browser. |
| Logout endpoint | Clear cookies on logout (set max-age=0) |

**Acceptance Criteria:**

- [x] `/api/v1/auth/login/` sets `access_token` and `refresh_token` cookies on 200 response
- [x] `/api/v1/auth/refresh/` accepts `refresh_token` from cookie; returns new `access_token` in cookie
- [x] Cookies are `HttpOnly=True`, `Secure=True` (except dev), `SameSite=Lax`
- [x] JSON response body still includes tokens (for backward compatibility with mobile/API clients)
- [x] `/api/v1/auth/logout/` clears both cookies
- [x] Django test suite passes; new tests verify cookie presence in responses

**Files to Modify:**
- `src/api/views/auth.py` — login, refresh, logout views OR serializers
- `src/api/serializers/auth.py` — if moving token response logic here
- `src/the_inventory/settings.py` — cookie security configuration (if not already set)
- `tests/api/test_auth.py` — add response cookie assertions

**Implementation Notes:**
- Use `response.set_cookie()` with parameters: `key`, `value`, `max_age`, `httponly=True`, `secure=True`, `samesite='Lax'`.
- Access token max-age: ~300 seconds (5 min). Refresh token max-age: ~604800 seconds (7 days).
- Test both header-based JWT (mobile) and cookie-based JWT (browser) paths concurrently.
- See [ENVIRONMENT.md](ENVIRONMENT.md) for JWT cookie variables (`JWT_COOKIE_SAMESITE`, `JWT_COOKIE_SECURE`, `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`, `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE`).

**Example:**
```python
# In auth view or serializer
response.set_cookie(
    'access_token',
    value=str(access_token),
    max_age=300,
    httponly=True,
    secure=True,  # Set to False only in dev (check DEBUG)
    samesite='Lax',
)
response.set_cookie(
    'refresh_token',
    value=str(refresh_token),
    max_age=604800,
    httponly=True,
    secure=True,
    samesite='Lax',
)
```

---

### COOKIE-02 — Backend: Ensure API authentication reads cookies

**Priority:** HIGH | **Depends On:** COOKIE-01 | **Parallel:** Yes (after COOKIE-01)

**Problem:**
Backend middleware and views must recognize tokens in cookies, not just headers. The `JWTAuthMiddleware` currently only reads `Authorization: Bearer` header.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| JWT middleware | Check for `access_token` cookie if no header JWT provided |
| DRF authenticators | Ensure `JWTAuthentication` class can validate cookie tokens |
| Fallback order | Header > Cookie (header takes precedence for explicit auth, cookie for implicit browser auth) |
| Tests | Verify requests with token in cookie are authenticated correctly |

**Acceptance Criteria:**

- [x] `src/api/middleware.py` (JWTAuthMiddleware) checks cookie if header is absent
- [x] DRF view-level JWT auth also supports cookie (may use custom `TokenAuthentication` class)
- [x] Request with token in `access_token` cookie is authenticated without header
- [x] Request with header JWT takes precedence over cookie
- [x] Tests confirm both paths work

**Files to Modify:**
- `src/api/middleware.py` — add cookie fallback
- `src/api/authentication.py` (if exists) or import from `rest_framework_simplejwt`
- `tests/api/test_auth.py` — add cookie authentication tests

**Implementation Notes:**
- Extract cookie: `request.COOKIES.get('access_token')`
- Add to request headers if present: `request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'`
- Or create a custom DRF authenticator that checks cookies first.

---

### COOKIE-03 — Frontend: Auth store refactoring (remove token persistence)

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes (independent of backend, but COOKIE-01 must be deployed first)

**Problem:**
Zustand store persists `accessToken` and `refreshToken` to localStorage. Must remove token persistence and only store non-sensitive user data.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Remove token persistence | `accessToken` and `refreshToken` not persisted to localStorage (stay in-memory only) |
| Keep user data persistence | User, tenant, memberships still persist (rehydrate on page load) |
| Store initialization | Tokens default to `null`; hydration does not restore them from storage |
| Logout cleanup | Still clears store, but token clearing is already memory-only |

**Acceptance Criteria:**

- [x] `useAuthStore` still has `accessToken` and `refreshToken` (in-memory), but NOT in persistence config
- [x] User, tenant, memberships ARE persisted
- [x] Page reload: user data hydrates, tokens are null (forces bootstrap to `/auth/me/`)
- [x] LocalStorage no longer contains `inventory-auth` with tokens
- [x] Frontend tests pass (mock no stored tokens on mount)

**Files to Modify:**
- `frontend/src/lib/auth-store.ts` — remove `accessToken` and `refreshToken` from `partialize()` callback

**Implementation Notes:**
```typescript
// In Zustand persist config:
partialize: (state) => ({
  // accessToken: DO NOT include
  // refreshToken: DO NOT include
  user: state.user,
  tenantSlug: state.tenantSlug,
  memberships: state.memberships,
  impersonation: state.impersonation,
}),
```

---

### COOKIE-04 — Frontend: API client refactoring (remove manual token handling)

**Priority:** HIGH | **Depends On:** COOKIE-01, COOKIE-03 | **Parallel:** Yes (after COOKIE-03 completed)

**Problem:**
Currently, `api-client.ts` reads `accessToken` from Zustand and manually sets `Authorization: Bearer` header. With cookies, browser sends token automatically; header approach conflicts.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Remove header token injection | Don't read `useAuthStore.accessToken` and set header |
| Keep CORS credentials | Ensure `fetch` calls include `credentials: 'include'` so cookies are sent |
| Refresh logic | When 401 is received, call `/auth/refresh/` to refresh token in cookie; no manual token update |
| Simplify token check logic | Remove token expiry checks from JS (rely on server 401 for token validity) |

**Acceptance Criteria:**

- [x] `buildHeaders()` no longer reads `accessToken` from store
- [x] `fetch()` calls use `credentials: 'include'` or `credentials: 'same-origin'` (browser sends cookies)
- [x] Refresh endpoint call still works (cookie auto-sent, new cookie auto-set by server)
- [x] 401 response triggers refresh (server has new cookie after response)
- [x] Redirect to `/login` after failed refresh with no valid cookie
- [x] API tests pass; no 401 loops; successful token refresh on 401

**Files to Modify:**
- `frontend/src/lib/api-client.ts`:
  - Remove `accessToken` reference from `buildHeaders()`
  - Ensure `credentials` in fetch options
  - Simplify refresh logic if needed (no Zustand token update)

**Implementation Notes:**
```typescript
// Old:
const { accessToken } = useAuthStore.getState();
if (accessToken) {
  headers.set('Authorization', `Bearer ${accessToken}`);
}

// New: Browser sends cookie automatically with credentials: 'include'
// No manual header needed
```

---

### COOKIE-05 — Frontend: Next.js middleware for auth context initialization

**Priority:** HIGH | **Depends On:** COOKIE-01 | **Parallel:** Yes (after COOKIE-01)

**Problem:**
On first page load, HttpOnly cookies aren't readable from client JS. Need server-side mechanism to detect auth state and pass it to client for hydration, avoiding redirect loops or hydration mismatches.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Middleware auth check | Detect if `access_token` cookie exists on incoming request |
| Redirect to login | If accessing protected route without cookie, redirect to `/login` before rendering |
| Bootstrap data | Call `/auth/me/` on server during render (or in layout) to fetch user/tenant/memberships once |
| Pass to client | Use React context or query cache to provide pre-fetched auth data to client |

**Acceptance Criteria:**

- [x] `middleware.ts` checks for `access_token` cookie on protected routes
- [x] Routes without auth are redirected to `/login` (no 401 on client)
- [x] Bootstrap call (`GET /auth/me/`) runs server-side or early client-side to populate AuthProvider
- [x] AuthProvider receives user/tenant/memberships pre-hydrated (no null flash)
- [x] No hydration mismatch between server (auth) and client (initially no auth)
- [x] Page load tests pass (logged in: user visible immediately; logged out: login page shown)

**Files to Modify:**
- `frontend/middleware.ts` — add auth route checking
- `frontend/src/features/auth/context/auth-context.tsx` — accept pre-fetched data as prop or from query cache
- `frontend/src/app/[locale]/layout.tsx` (or wrapper) — fetch `/auth/me/` before rendering protected routes

**Implementation Notes:**
- Use `next/headers` → `cookies()` in middleware to read `access_token`
- Protected routes: check middleware; if no cookie, `NextResponse.redirect('/login')`
- For hydration: either pre-fetch in a wrapper component or use server component to call API, then pass context value as initial state

---

### COOKIE-06 — Frontend: AuthProvider and AuthGuard auth state sync updates

**Priority:** HIGH | **Depends On:** COOKIE-03, COOKIE-04, COOKIE-05 | **Parallel:** Yes (after dependencies)

**Problem:**
AuthProvider currently waits for localStorage hydration (`_hasHydrated`). Tokens are in localStorage. With cookies, no localStorage tokens to hydrate; instead rely on middleware pre-check and bootstrap endpoint.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Remove localStorage polling | AuthProvider no longer polls for `_hasHydrated` token state |
| Bootstrap on mount | If Zustand has no user data but cookies exist (from middleware or manual check), call `GET /auth/me/` |
| AuthGuard simplification | No need to check for token expiry; rely on server 401 response to indicate stale session |
| Logout state | Clearing store also triggers redirect to `/login` (user data was cleared) |

**Acceptance Criteria:**

- [x] AuthProvider no longer depends on localStorage token persistence
- [x] AuthProvider immediately renders if middleware confirmed auth (data pre-populated) OR starts bootstrap if not
- [x] AuthGuard no longer checks `isTokenExpired(accessToken)` in JS
- [x] On logout, user data cleared from store → AuthGuard sees no user → redirects to `/login`
- [x] No `_hasHydrated` polling delay visible to user (instant render if pre-authenticated)
- [x] Tests pass for logged-in boot, logged-out boot, and logout redirect

**Files to Modify:**
- `frontend/src/features/auth/context/auth-context.tsx`:
  - Remove `_hasHydrated` polling
  - Simplify `isReady` logic
  - Accept pre-fetched auth data if available
- `frontend/src/features/auth/components/auth-guard.tsx`:
  - Remove token expiry check
  - Rely on AuthProvider `isReady` and user presence

**Implementation Notes:**
- `AuthProvider` sets `isReady = true` immediately on mount if user data exists (pre-hydrated by middleware)
- Or call bootstrap endpoint once if not pre-hydrated, then set `isReady = true`
- `AuthGuard` simplifies to: `if (!isReady) return; if (!isAuthenticated) redirect;` where `isAuthenticated` = `!!user || !!accessToken`

---

### COOKIE-07 — Testing and security audit

**Priority:** HIGH | **Depends On:** COOKIE-01 through COOKIE-06 | **Parallel:** No (final verification)

**Problem:**
New authentication flow needs comprehensive testing (happy path, refresh, logout, token expiry, XSS mitigation) and security review.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Backend tests | Login sets cookies; refresh accepts and returns cookies; logout clears cookies; tokens in body still present (backward compat) |
| Frontend tests | API client sends credentials; 401 refresh flow; auth sync on mount; logout redirect |
| Integration tests | Full login → bootstrap → authenticated request → token refresh → logout flow |
| Security checklist | Cookies are HttpOnly, Secure, SameSite; no tokens in localStorage; browser can't exfiltrate via JS; CSRF tokens if needed |
| Manual smoke test | Login as test user, browse protected pages, refresh page, logout; verify no localStorage auth tokens |

**Acceptance Criteria:**

- [x] Backend auth tests pass (COOKIE-01 tests in `tests/api/test_auth.py`)
- [x] Frontend auth tests pass (`frontend/__tests__/features/auth/*` and `auth-store.test.ts`)
- [x] Integration test: login → dashboard → page reload → still authenticated → logout → redirect
- [x] Security audit: run OWASP ZAP or similar on `/login`, `/auth/refresh/`, verify no token leaks
- [x] Manual test: localStorage.getItem('inventory-auth') returns null or only `{user, memberships, tenantSlug, impersonation}`
- [x] Cross-browser test: Chrome, Firefox, Safari (HttpOnly support varies slightly)
- [x] Documentation updated: [ARCHITECTURE.md](ARCHITECTURE.md) notes cookie-based auth; [docs/SECURITY.md](../SECURITY.md) updated with new auth method

**Files to Modify:**
- `tests/api/test_auth.py` — add/update cookie response assertions
- `frontend/__tests__/features/auth/auth-store.test.ts` — verify no token persistence
- `frontend/__tests__/app/root-entry.test.tsx` — update hydration tests
- `docs/ARCHITECTURE.md` — update auth table to note cookie-based JWT
- `docs/SECURITY.md` — add cookie security notes

**Implementation Notes:**
- Use Django test client to inspect `response.cookies` (e.g. `assert 'access_token' in response.cookies`)
- Mock fetch in frontend tests to verify `credentials: 'include'`
- Manual: browse DevTools → Application → Cookies; confirm tokens present; localStorage should not have auth tokens
- XSS vulnerability: create a test that tries `localStorage.getItem('inventory-auth')` after app boots; should return no tokens

---

## Dependency Graph

```
COOKIE-01 (Backend: cookie response setup — MUST BE FIRST)
├─ COOKIE-02 (Backend: auth reads cookies)
├─ COOKIE-03 (Frontend: remove token persistence — independent)
├─ COOKIE-05 (Frontend: Next.js middleware for auth check)
├─ COOKIE-04 (Frontend: API client refactoring — after COOKIE-03)
├─ COOKIE-06 (Frontend: AuthProvider sync updates — after COOKIE-03, 04, 05)
└─ COOKIE-07 (Testing & security audit — after all others)
```

---

## Recommended Execution Order

### Phase 1: Backend Setup (can overlap with Phase 2 prep)
1. **COOKIE-01:** Implement cookie response in login/refresh/logout endpoints
2. **COOKIE-02:** Ensure middleware/views read cookies

### Phase 2: Frontend Refactoring (max 3 contributors in parallel)
- **COOKIE-03:** Remove token persistence (1 person, ~1 hour)
- **COOKIE-05:** Next.js middleware auth check (1 person, ~2 hours)
- **COOKIE-04:** API client refactoring (1 person, ~1.5 hours) — must wait for COOKIE-03
- **COOKIE-06:** AuthProvider/AuthGuard updates (1 person, ~2 hours) — must wait for COOKIE-03, 04, 05

### Phase 3: Testing & Hardening
1. **COOKIE-07:** Testing, security audit, documentation

---

## Parallelization Summary

| Phase | # Contributors | Duration | Notes |
|-------|---|---|---|
| 1 (Backend) | 1–2 | ~4 hours | COOKIE-01 blocks COOKIE-02; both needed before Phase 2 |
| 2 (Frontend) | Up to 3 | ~6 hours | COOKIE-03, COOKIE-05 can run first; COOKIE-04, 06 follow |
| 3 (Testing) | 1 | ~4 hours | Run after Phase 2 complete on a test branch |

**Total:** ~14 hours effort (linear), ~8 hours calendar (with parallel execution)

---

## Testing Strategy

### Per-task (COOKIE-01–COOKIE-06)

- **COOKIE-01–02:** Django `TestCase` assertions on response cookies + status codes
- **COOKIE-03–04:** Vitest for Zustand store + fetch mocking
- **COOKIE-05–06:** Vitest for middleware stubs + context hydration

### Final audit (COOKIE-07)

- Full integration test: login API → set cookies → fetch protected endpoint → receive 401 → refresh → retry with new cookie → succeed
- Manual browser test: DevTools verify token in cookie, not in localStorage
- OWASP ZAP scan on `/login` and `/auth/*` routes

### Manual Testing Checklist

- [ ] Log in; DevTools shows `access_token` cookie (HttpOnly)
- [ ] localStorage does NOT contain tokens (only user/memberships/tenantSlug)
- [ ] Refresh page while logged in; still authenticated immediately (no flash of login)
- [ ] Expired token (modify max-age or wait): next API call gets 401 → refresh called → 200 on retry
- [ ] Log out; cookies cleared; redirected to `/login`
- [ ] Try XSS attack in console: `localStorage.getItem('inventory-auth')` returns object with NO tokens
- [ ] Mobile client still works: send JWT in header (deprecated but supported for backward compat)

---

## Implementation Checklist

- [ ] **COOKIE-01** — Backend: Configure cookie-based JWT response
- [ ] **COOKIE-02** — Backend: Ensure API authentication reads cookies
- [ ] **COOKIE-03** — Frontend: Auth store refactoring (remove token persistence)
- [ ] **COOKIE-04** — Frontend: API client refactoring (remove manual token handling)
- [ ] **COOKIE-05** — Frontend: Next.js middleware for auth context initialization
- [ ] **COOKIE-06** — Frontend: AuthProvider and AuthGuard auth state sync updates
- [ ] **COOKIE-07** — Testing and security audit

---

## Reference — Key Files

### Backend

- `src/api/views/auth.py` — Login, refresh, logout endpoints
- `src/api/serializers/auth.py` — Token serialization logic
- `src/api/middleware.py` — JWT auth middleware
- `src/the_inventory/settings.py` — Cookie security settings
- `tests/api/test_auth.py` — Auth endpoint tests

### Frontend

- `frontend/src/lib/auth-store.ts` — Zustand auth state store
- `frontend/src/lib/api-client.ts` — HTTP client with token/cookie handling
- `frontend/middleware.ts` — Next.js request middleware
- `frontend/src/features/auth/context/auth-context.tsx` — Auth provider
- `frontend/src/features/auth/components/auth-guard.tsx` — Protected route wrapper

---

## Notes for Developers

### New auth cookie flow

1. User logs in → backend sets `access_token` and `refresh_token` cookies (HttpOnly, Secure, SameSite)
2. Frontend stores user/tenant/memberships in Zustand (persisted to localStorage — non-sensitive)
3. Next.js middleware checks for `access_token` cookie on each request
4. API client sends requests with `credentials: 'include'` (browser auto-sends cookies)
5. If token expires (401), refresh endpoint called (server sets new cookie in response)
6. User logs out → server clears cookies; frontend clears Zustand; redirected to `/login`

### XSS Protection

- Tokens are **not** in JavaScript-accessible storage (localStorage, sessionStorage, window object)
- Even with successful XSS injection, attacker cannot exfiltrate tokens
- CSRF protection via SameSite and CSRF token (if using stateful cookies alongside stateless JWT)

### Backward Compatibility

- Mobile and service-to-service clients still use `Authorization: Bearer <token>` header
- Backend returns tokens in JSON response body (in addition to cookies)
- Header-based auth takes precedence over cookie auth in middleware

### Local Quick Check

```bash
# Backend
python manage.py test tests.api.test_auth

# Frontend
cd frontend && yarn test --run

# Manual
cd frontend && yarn dev
# Visit http://localhost:3000/login, log in, open DevTools → Application → Cookies
# Verify 'access_token' cookie present, HttpOnly checked
# localStorage should NOT contain 'inventory-auth' with tokens
```

---

## Future Enhancements

- [ ] CSRF token in header for POSTs (SameSite=None for cross-domain)
- [ ] Single sign-on (SSO) via cookie domain sharing (if multi-tenant domains)
- [ ] Refresh token rotation (issue new refresh on each access)
- [ ] Token binding (tie token to IP/user agent to block stolen token replay)
