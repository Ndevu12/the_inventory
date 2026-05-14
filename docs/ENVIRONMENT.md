# Environment Configuration Guide

This guide explains how to configure **The Inventory** for different environments using environment variables. It covers both the **Django backend** and **Next.js frontend**, with setup instructions for local development, Docker deployment, and production.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Overview](#configuration-overview)
- [Backend Environment Variables](#backend-environment-variables)
- [Frontend Environment Variables](#frontend-environment-variables)
- [Environment-Specific Defaults](#environment-specific-defaults)
- [Setup Guides](#setup-guides)
- [Translations (Django & Next.js)](#translations-django--nextjs)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Local Development (5 minutes)

```bash
# 1. Copy backend template (root directory)
cp .env.example .env.local

# 2. Copy frontend template (frontend directory)
cp frontend/.env.local.example frontend/.env.local

# 3. Start Django (uses dev defaults, SQLite)
python manage.py runserver

# 4. In another terminal, start Next.js frontend
cd frontend && yarn dev
```

**That's it!** Default values work for local development:
- Django runs on `http://localhost:8000`
- Frontend runs on `http://localhost:3000`
- SQLite database used automatically
- Redis/Celery disabled (tasks run synchronously)
- CORS configured for localhost

### Docker Deployment

```bash
# Build image
docker build -t the_inventory .

# Run with environment variables
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql://user:pass@db:5432/inventory" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e FRONTEND_URL="https://app.example.com" \
  the_inventory
```

Environment variables are read from your orchestration platform (**Render**, **Docker Compose**, **Kubernetes**, etc.) — not from `.env` files.

---

## Configuration Overview

### How Environment Variables Are Loaded

**Backend (Django):**

```
┌─────────────────────────────────────────┐
│  OS Environment Variables               │ ← From platform (Render, K8s, Docker, etc.)
│  .env file (root directory)             │ ← From .env or .env.local
│  Code defaults (settings/*.py)          │ ← Fallback defaults
└─────────────────────────────────────────┘
```

Priority: **OS environment** > **.env file** > **code defaults**

**Frontend (Next.js):**

```
┌─────────────────────────────────────────┐
│  NEXT_PUBLIC_* environment variables    │ ← Build-time and runtime
│  .env.local (frontend directory)        │ ← Development/local config
│  .env.production.local (opt.)           │ ← Production-specific override
│  Code defaults (next.config.ts)         │ ← Fallback defaults
└─────────────────────────────────────────┘
```

> **Note:** Files in `.gitignore` (`.env`, `.env.local`) are **never committed** — you must set environment variables on your platform (Render, Docker, K8s, etc.) for production.

### Settings Pattern

The project uses **split Django settings**:

| File | When Used | Debug | Database | Purpose |
|------|-----------|-------|----------|---------|
| `the_inventory/settings/dev.py` | Local development | `True` | SQLite | Fast iteration, all features enabled |
| `the_inventory/settings/production.py` | Render, Docker, K8s | `False` | PostgreSQL (required) | Security hardening, optimized defaults |
| `the_inventory/settings/base.py` | Always | — | — | Shared config (apps, middleware, templates) |

**Selection:** `DJANGO_SETTINGS_MODULE` environment variable (default: `production` in containers, `dev` locally)

---

## Backend Environment Variables

### Core Settings

Required and important variables for both development and production.

#### `SECRET_KEY`

- **Type:** string
- **Required:** Yes (production), optional (development)
- **Default:** Insecure `dev-insecure-xxx` in development
- **Purpose:** Cryptographic key for Django session, CSRF, and password reset tokens
- **Example:**
  ```bash
  SECRET_KEY="your-very-long-random-string-here"
  ```
- **Generate a new key:**
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **⚠️ Security:** Never commit real SECRET_KEY to git. Use a platform secret manager (Render Secrets, AWS Secrets Manager, etc.).

#### `ALLOWED_HOSTS`

- **Type:** comma-separated hostnames
- **Default:** `localhost,127.0.0.1` (development)
- **Purpose:** Prevent HTTP Host header attacks; whitelist all production domains
- **Format:** Hostname only — **no `https://` prefix, no paths**
- **Examples:**
  ```bash
  # Local development (default)
  ALLOWED_HOSTS=localhost,127.0.0.1
  
  # Production with custom domain
  ALLOWED_HOSTS=api.example.com,app.example.com
  
  # Render deployment
  ALLOWED_HOSTS=my-service.onrender.com
  
  # Multi-tenant SaaS (all subdomains)
  ALLOWED_HOSTS=.example.com    # (matches *.example.com and example.com)
  ```
- **❌ Wrong:** `https://api.example.com`, `https://api.example.com/api`
- **✅ Right:** `api.example.com`, `.example.com`

#### `DJANGO_LOG_LEVEL`

- **Type:** string (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- **Default:** `INFO`
- **Purpose:** Controls Django's logging output to console/stdout
- **When to use:**
  - `DEBUG` — Trace authorization, middleware, or request issues
  - `INFO` — Standard production logging
  - `WARNING`, `ERROR` — Suppress debug output in strict environments
- **Example:**
  ```bash
  DJANGO_LOG_LEVEL=DEBUG  # Use briefly to troubleshoot; revert to INFO
  ```

#### `LANGUAGE_CODE` & `TIME_ZONE` (Optional)

- **Type:** string
- **Default:** `en-us` / `UTC`
- **Purpose:** Localization for date/time display and form validation
- **Examples:**
  ```bash
  LANGUAGE_CODE=en-us
  TIME_ZONE=America/New_York
  TIME_ZONE=Europe/London
  TIME_ZONE=Asia/Tokyo
  ```

### Database & Storage

#### `DATABASE_URL`

- **Type:** string (database connection string)
- **Default:** SQLite (`db.sqlite3`) in development
- **Purpose:** PostgreSQL connection for production
- **Format:**
  ```
  postgresql://[user]:[password]@[host]:[port]/[database]
  ```
- **Examples:**
  ```bash
  # Local PostgreSQL (development)
  DATABASE_URL=postgresql://postgres:password@localhost:5432/the_inventory
  
  # Render PostgreSQL (managed)
  DATABASE_URL=postgresql://the_inventory_db_user:abc123@dpg-xyz.render-postgresql.com:5432/the_inventory_db
  
  # AWS RDS
  DATABASE_URL=postgresql://admin:SecurePass@inventory-db.xyz.rds.amazonaws.com:5432/inventory
  
  # Local Docker Compose
  DATABASE_URL=postgresql://postgres:postgres@db:5432/the_inventory
  ```
- **⚠️:** Always use PostgreSQL in production (SQLite is not suitable for concurrent users)

#### `STATIC_URL` & `MEDIA_URL` (Optional)

- **Type:** string (URL paths)
- **Default:** `/static/` / `/media/`
- **Purpose:** Configure where static files (CSS, JS) and user uploads are served
- **Examples:**
  ```bash
  # Local development (default)
  STATIC_URL=/static/
  MEDIA_URL=/media/
  
  # Cloud storage (S3, GCS)
  STATIC_URL=https://cdn.example.com/static/
  MEDIA_URL=https://storage.googleapis.com/my-bucket/media/
  ```
- **Note:** In production, static files are collected to a flat directory via `python manage.py collectstatic`

### Redis & Caching

#### `REDIS_URL`

- **Type:** string (Redis connection URL)
- **Default:** `redis://localhost:6379/0`
- **Purpose:** Configure Redis for caching and Celery task broker
- **Optional:** Yes — if not set, Django uses in-memory cache (`LocMemCache`)
- **Format:**
  ```
  redis://[host]:[port]/[db_number]
  redis://:password@[host]:[port]/[db_number]
  ```
- **Examples:**
  ```bash
  # Local Redis (default)
  REDIS_URL=redis://localhost:6379/0
  
  # Render Redis (managed)
  REDIS_URL=redis://default:your-password@redis-xyz.render.com:10456
  
  # AWS ElastiCache
  REDIS_URL=redis://:your-auth-token@my-cache.cache.amazonaws.com:6379/0
  
  # Local Docker Compose
  REDIS_URL=redis://redis:6379/0
  ```
- **Note:** Redis is optional for simple deployments; apps still work without it (just slower caching and no Celery)

#### `CELERY_BROKER_URL`

- **Type:** string
- **Default:** Uses `REDIS_URL` if not specified
- **Purpose:** Celery task queue broker (for async background jobs)
- **When to set:** Only if you want a separate message broker from cache
- **Example:**
  ```bash
  CELERY_BROKER_URL=redis://localhost:6379/1
  ```

#### `CELERY_TASK_ALWAYS_EAGER`

- **Type:** boolean (`true`, `1`, `yes`, or `false`, `0`, `no`)
- **Default:** `false`
- **Purpose:** Execute Celery tasks synchronously (not in background)
- **Use case:** Development and testing — avoids need for separate Celery worker process
- **Example:**
  ```bash
  CELERY_TASK_ALWAYS_EAGER=true   # Dev: tasks run immediately
  CELERY_TASK_ALWAYS_EAGER=false  # Prod: tasks queued asynchronously
  ```

### Frontend Integration & URLs

#### `FRONTEND_URL`

- **Type:** string (full URL)
- **Default:** `http://localhost:3000`
- **Purpose:** Frontend base URL for redirects in password reset emails, OAuth callbacks, etc.
- **Examples:**
  ```bash
  # Local development
  FRONTEND_URL=http://localhost:3000
  
  # Production
  FRONTEND_URL=https://app.example.com
  
  # Staging
  FRONTEND_URL=https://staging.example.com
  ```

#### `PUBLIC_BASE_URL` (Optional)

- **Type:** string (full URL)
- **Default:** Derived from `ALLOWED_HOSTS` or `http://127.0.0.1:8000`
- **Purpose:** Public API endpoint used in emails and API documentation
- **Example:**
  ```bash
  PUBLIC_BASE_URL=https://api.example.com
  ```

#### `WAGTAILADMIN_BASE_URL` (Optional)

- **Type:** string (URL base without `/admin/`)
- **Default:** `PUBLIC_BASE_URL` or `http://127.0.0.1:8000`
- **Purpose:** Wagtail admin URL displayed in emails (e.g., "Edit this at: `https://api.example.com/admin/`")
- **Example:**
  ```bash
  WAGTAILADMIN_BASE_URL=https://api.example.com
  ```

#### `WAGTAIL_SITE_NAME` (Optional)

- **Type:** string
- **Default:** `the_inventory`
- **Purpose:** Display name in Wagtail admin UI and emails
- **Example:**
  ```bash
  WAGTAIL_SITE_NAME="My Company Inventory"
  ```

### Tenants & Registration

#### `ENABLE_PUBLIC_TENANT_REGISTRATION`

- **Type:** boolean
- **Default:** `false`
- **Purpose:** Allow public users to create new organizations via API
- **Use case:**
  - `true` — SaaS multi-tenant model (anyone can sign up and create an organization)
  - `false` — Self-hosted or invite-only (only admins create organizations)
- **Example:**
  ```bash
  ENABLE_PUBLIC_TENANT_REGISTRATION=true   # SaaS mode
  ENABLE_PUBLIC_TENANT_REGISTRATION=false  # Self-hosted mode
  ```

#### `AUDIT_TENANT_ACCESS`

- **Type:** boolean
- **Default:** `true`
- **Purpose:** Log (audit trail) when users switch tenants or access is changed
- **Use case:**
  - `true` — Standard; enables compliance/security auditing
  - `false` — High-traffic systems where audit overhead is a concern
- **Example:**
  ```bash
  AUDIT_TENANT_ACCESS=true   # Enable audit logging
  ```

### CORS & CSRF Security

#### `CORS_ALLOWED_ORIGINS`

- **Type:** comma-separated URLs
- **Default:** `http://localhost:3000,http://localhost:5173` (dev)
- **Purpose:** Whitelist frontend origins that can make CORS requests to the API
- **Format:** Full origin = scheme + hostname + port (no path)
- **Examples:**
  ```bash
  # Local development (default)
  CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
  
  # Production
  CORS_ALLOWED_ORIGINS=https://app.example.com
  
  # Multiple frontends
  CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
  
  # Wildcard subdomains (not recommended)
  CORS_ALLOWED_ORIGINS=https://*.example.com
  ```

#### `CORS_ALLOW_ALL_ORIGINS`

- **Type:** boolean
- **Default:** `false`
- **Purpose:** Allow requests from **any** origin (insecure)
- **⚠️ WARNING:** Only for development or trusted internal networks
- **Example:**
  ```bash
  CORS_ALLOW_ALL_ORIGINS=true  # Dev only!
  ```

#### `CORS_ALLOW_CREDENTIALS`

- **Type:** boolean
- **Default:** `true`
- **Purpose:** Allow browser to send cookies/credentials in CORS requests (JWT in headers)
- **Note:** Usually `true` for stateless JWT auth
- **Example:**
  ```bash
  CORS_ALLOW_CREDENTIALS=true
  ```

#### `CORS_EXTRA_HEADERS` (Optional)

- **Type:** comma-separated header names
- **Default:** Not set
- **Purpose:** Allow extra request headers beyond the default CORS safe list
- **Example:**
  ```bash
  CORS_EXTRA_HEADERS=X-Custom-Header,X-API-Version
  ```

#### `CSRF_TRUSTED_ORIGINS`

- **Type:** comma-separated URLs
- **Default:** Defaults to `CORS_ALLOWED_ORIGINS` if not set
- **Purpose:** Trusted origins for form submissions and cookies (CSRF protection)
- **Example:**
  ```bash
  CSRF_TRUSTED_ORIGINS=https://app.example.com
  ```

#### JWT Cookie Security (`JWT_COOKIE_SAMESITE`, `JWT_COOKIE_SECURE`)

- **Type:** string / boolean
- **Default:**
  - Local dev: `SameSite=Lax`, `Secure=false`
  - Production: `SameSite=Lax`, `Secure=true`
- **Purpose:** Control JWT cookie transport/security policy for browser auth flows
- **Examples for third-party (cross-domain) cookies:**
  ```bash
  JWT_COOKIE_SAMESITE=None
  JWT_COOKIE_SECURE=true
  ```

#### `USE_X_FORWARDED_PROTO`

- **Type:** boolean
- **Default:** `true` in production, `false` in dev
- **Purpose:** Trust the `X-Forwarded-Proto` header from reverse proxies/load balancers
- **Use case:** When TLS terminates at a load balancer (Nginx, CloudFlare, etc.), not on Python app
- **Example:**
  ```bash
  USE_X_FORWARDED_PROTO=true  # Trust load balancer headers (production)
  ```

### REST API & JWT Authentication

#### `API_PAGE_SIZE`

- **Type:** integer
- **Default:** `25`
- **Purpose:** Default number of items per page in paginated API responses
- **Example:**
  ```bash
  API_PAGE_SIZE=50  # Return 50 items per page instead of 25
  ```

#### `JWT_ACCESS_TOKEN_MINUTES`

- **Type:** integer
- **Default:** `30`
- **Purpose:** JWT access token expiry time (minutes)
- **Use case:**
  - `30` — Standard security
  - `5` — High security (frequent refreshes)
  - `60+` — Less-secure, longer-lived tokens
- **Example:**
  ```bash
  JWT_ACCESS_TOKEN_MINUTES=15  # Short-lived tokens for security
  ```

#### `JWT_REFRESH_TOKEN_DAYS`

- **Type:** integer
- **Default:** `7`
- **Purpose:** JWT refresh token expiry time (days) — allows getting new access tokens
- **Example:**
  ```bash
  JWT_REFRESH_TOKEN_DAYS=30  # Refresh tokens valid for 30 days
  ```

### JWT Cookie Configuration

The system uses **HTTP-only cookies** for secure browser-based JWT authentication. These settings control how JWT tokens are transmitted via cookies and ensure cookies work correctly in both development (localhost) and production (subdomains) scenarios.

> **Important:** JWT cookies cannot be shared across mismatched hostnames (e.g., `localhost` vs `127.0.0.1`). Ensure your frontend and backend use consistent hostnames.

#### `JWT_COOKIE_DOMAIN`

- **Type:** string or `None` (empty)
- **Default:** `None` (same-domain only)
- **Purpose:** Cookie domain scope for cross-subdomain access
- **Values:**
  - `None` (unset) — Bind cookie to exact request domain (development default)
  - `".example.com"` — Share cookie across subdomains `*.example.com` (production with subdomains)
  - `"localhost"` — Explicitly set for localhost development (rarely needed)
- **Examples:**
  ```bash
  # Development (localhost only) — leave unset
  JWT_COOKIE_DOMAIN=
  
  # Production with subdomains (api.example.com, app.example.com, etc.)
  JWT_COOKIE_DOMAIN=.example.com
  ```
- **⚠️ Common Issue:** If frontend on `localhost:3000` and backend on `127.0.0.1:8000`, cookies won't be shared due to domain mismatch. **Solution:** Use consistent hostnames (both `localhost` or both actual domain).

#### `JWT_COOKIE_PATH`

- **Type:** string
- **Default:** `/`
- **Purpose:** Cookie path scope within the domain
- **Common values:**
  - `/` — Available to entire application
  - `/api/` — Available only to `/api/*` paths (rarely needed)
- **Example:**
  ```bash
  JWT_COOKIE_PATH=/
  ```

#### `JWT_COOKIE_SECURE`

- **Type:** boolean (`true` or `false`)
- **Default:** `false` (development), `true` (production)
- **Purpose:** Enforce HTTPS-only transmission of JWT cookies
- **Values:**
  - `false` — Allow cookies over HTTP (development only, insecure)
  - `true` — Require HTTPS (production security requirement)
- **⚠️ Security:** Must be `true` in production. Only set to `false` for local development.
- **Examples:**
  ```bash
  # Local development (HTTP)
  JWT_COOKIE_SECURE=false
  
  # Production (HTTPS required)
  JWT_COOKIE_SECURE=true
  ```

#### `JWT_COOKIE_SAMESITE`

- **Type:** string (`Lax`, `Strict`, or `None`)
- **Default:** `Lax`
- **Purpose:** CSRF protection for cookie transmission across sites
- **Values:**
  - `Lax` — Safe default; cookies sent on same-site requests and safe cross-site requests (like following links)
  - `Strict` — Strongest protection; cookies only sent on same-site requests (may break legitimate cross-site requests)
  - `None` — Allow cross-site cookie transmission; requires `JWT_COOKIE_SECURE=true` and HTTPS
- **Examples:**
  ```bash
  # Standard development and production
  JWT_COOKIE_SAMESITE=Lax
  
  # Cross-origin SPA (app.example.com calling api.example.com) with HTTPS
  JWT_COOKIE_SAMESITE=None
  JWT_COOKIE_SECURE=true
  ```

#### `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`

- **Type:** integer (seconds)
- **Default:** `300` (5 minutes)
- **Purpose:** HTTP-only access token cookie lifetime in seconds
- **Should match:** `JWT_ACCESS_TOKEN_MINUTES` lifetime (default 30 minutes in token claim, but 5-minute cookie)
- **Examples:**
  ```bash
  JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300    # 5 minutes (default)
  JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=600    # 10 minutes
  JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=1800   # 30 minutes
  ```

#### `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE`

- **Type:** integer (seconds)
- **Default:** `604800` (7 days)
- **Purpose:** HTTP-only refresh token cookie lifetime in seconds
- **Should match:** JWT token lifetime (default 7 days)
- **Examples:**
  ```bash
  JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800   # 7 days (default)
  JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=2592000  # 30 days
  ```

#### Cookie Configuration Examples

**Development (Single Machine with localhost):**

```bash
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
JWT_COOKIE_DOMAIN=          # (unset, same-domain only)
JWT_COOKIE_PATH=/
JWT_COOKIE_SECURE=false     # (allow HTTP)
JWT_COOKIE_SAMESITE=Lax
JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300
JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800
```

**Production (Subdomain Sharing over HTTPS):**

```bash
# Frontend: https://app.example.com
# Backend: https://api.example.com
JWT_COOKIE_DOMAIN=.example.com      # Share across subdomains
JWT_COOKIE_PATH=/
JWT_COOKIE_SECURE=true              # HTTPS required
JWT_COOKIE_SAMESITE=Lax
JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300
JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800
```

**Production (Cross-Origin SPA over HTTPS):**

```bash
# Frontend: https://widgets.example.com
# Backend: https://api.different.com
JWT_COOKIE_DOMAIN=.different.com
JWT_COOKIE_PATH=/
JWT_COOKIE_SECURE=true              # HTTPS required
JWT_COOKIE_SAMESITE=None            # Cross-site cookies
JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300
JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800
```

### Caching TTLs

#### `STOCK_CACHE_TTL_SECONDS`

- **Type:** integer (seconds)
- **Default:** `600` (10 minutes)
- **Purpose:** How long to cache product stock levels before refreshing from database
- **Example:**
  ```bash
  STOCK_CACHE_TTL_SECONDS=300   # Cache for 5 minutes
  STOCK_CACHE_TTL_SECONDS=3600  # Cache for 1 hour
  ```

#### `DASHBOARD_CACHE_TTL_SECONDS`

- **Type:** integer (seconds)
- **Default:** `300` (5 minutes)
- **Purpose:** How long to cache dashboard data aggregations
- **Example:**
  ```bash
  DASHBOARD_CACHE_TTL_SECONDS=60  # Cache for 1 minute
  ```

### OpenAPI Documentation

#### `API_DOC_TITLE`, `API_DOC_DESCRIPTION`, `API_DOC_VERSION`

- **Type:** string
- **Default:** `The Inventory API`, `RESTful API for The Inventory`, `1.0.0`
- **Purpose:** Customize OpenAPI/Swagger documentation
- **Example:**
  ```bash
  API_DOC_TITLE="My Company - Inventory API"
  API_DOC_DESCRIPTION="REST API for managing products, stock, and movements"
  API_DOC_VERSION=2.0.0
  ```

### Email Configuration

#### `EMAIL_BACKEND`

- **Type:** string (Python class path)
- **Default:** `django.core.mail.backends.console.EmailBackend` (dev), `django.core.mail.backends.smtp.EmailBackend` (prod)
- **Purpose:** Email transport backend
- **Common values:**
  ```bash
  EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend      # Print to console (dev)
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend         # SMTP server (prod)
  EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend       # In-memory (testing)
  ```

#### `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`

- **Type:** string / integer / boolean
- **Default:** `smtp.gmail.com`, `587`, `true`, `false`
- **Purpose:** SMTP server configuration
- **Examples:**
  ```bash
  # Gmail
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=true
  EMAIL_USE_SSL=false
  
  # Custom SMTP
  EMAIL_HOST=mail.example.com
  EMAIL_PORT=25
  EMAIL_USE_TLS=false
  EMAIL_USE_SSL=false
  ```

#### `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

- **Type:** string (username and password)
- **Purpose:** Authentication for SMTP server
- **Example:**
  ```bash
  EMAIL_HOST_USER=noreply@example.com
  EMAIL_HOST_PASSWORD=your-app-password  # Use app-specific password for Gmail
  ```
- **⚠️ Security:** Never commit real passwords — use platform secret managers

#### `DEFAULT_FROM_EMAIL`

- **Type:** string (email address)
- **Default:** Not set
- **Purpose:** Default sender email address for system emails
- **Example:**
  ```bash
  DEFAULT_FROM_EMAIL=noreply@example.com
  ```

---

## Frontend Environment Variables

### Required Variables

Frontend variables are prefixed with `NEXT_PUBLIC_` to make them accessible in the browser.

#### `NEXT_PUBLIC_API_URL`

- **Type:** string (full URL)
- **Required:** Yes
- **Purpose:** Base URL for Django REST API calls from the browser
- **Default:** None — must be explicitly set
- **Format:** Must include `/api/v1` path
- **Examples:**
  ```bash
  # Local development
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  
  # Production
  NEXT_PUBLIC_API_URL=https://api.example.com/api/v1
  
  # Vercel with backend on Render
  NEXT_PUBLIC_API_URL=https://my-api.onrender.com/api/v1
  ```

#### `NEXT_PUBLIC_APP_NAME`

- **Type:** string
- **Default:** `The Inventory (Local)`
- **Purpose:** Application display name in browser title and UI
- **Examples:**
  ```bash
  NEXT_PUBLIC_APP_NAME="The Inventory (Local)"
  NEXT_PUBLIC_APP_NAME="My Company Inventory"
  NEXT_PUBLIC_APP_NAME="Inventory - Production"
  ```

### Setup

**File location:** `frontend/.env.local` (development) or `frontend/.env.production.local` (production)

**Example `frontend/.env.local`:**

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME="The Inventory (Local)"
```

**For production deployment:**
- Set these variables in your hosting platform (Vercel, Netlify, etc.)
- Or create `frontend/.env.production.local` with production values
- The `.local` files are in `.gitignore` — never committed

---

## Environment-Specific Defaults

### Local Development

| Variable | Dev Default | Notes |
|----------|-------------|-------|
| `DEBUG` | `True` | Full error pages, static file serving |
| `SECRET_KEY` | `insecure-dev-key` | Insecure but fine for local |
| `ALLOWED_HOSTS` | `*` | Accept all hosts locally |
| `DATABASE_URL` | SQLite (db.sqlite3) | File-based, no setup needed |
| `REDIS_URL` | Not required | Uses in-memory cache if not set |
| `CELERY_TASK_ALWAYS_EAGER` | `true` | Tasks run synchronously |
| `EMAIL_BACKEND` | `console` | Emails printed to console |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Local frontend origins |
| `JWT_COOKIE_SECURE` | `false` | Allow JWT cookies over HTTP |

**Result:**
- ✅ Fast iteration, no external services needed
- ✅ Full debug output
- ✅ Static files served by Django
- ❌ Not suitable for production

### Production (Docker/Render/K8s)

| Variable | Production Default | Notes |
|----------|-------------------|-------|
| `DEBUG` | `False` | Error pages, no stack traces |
| `SECRET_KEY` | **Required** | Must be set via platform secrets |
| `ALLOWED_HOSTS` | **Required** | Must match your domain |
| `DATABASE_URL` | **Required** | PostgreSQL connection string |
| `REDIS_URL` | Optional | Recommended for caching/Celery |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | Queue tasks to Redis broker |
| `EMAIL_BACKEND` | `smtp` | Use real SMTP server |
| `CORS_ALLOWED_ORIGINS` | Not set — must override | Your production frontend URL(s) |
| `JWT_COOKIE_SECURE` | `true` | Only send JWT cookies over HTTPS |

**Result:**
- ✅ Security hardening (no DEBUG, secure cookies, etc.)
- ✅ Static file optimization (`ManifestStaticFilesStorage`)
- ✅ Required secrets are enforced (raises `ValueError` if missing)
- ❌ Requires careful configuration

---

## Setup Guides

### Local Development Setup

#### Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- Git

#### Django Backend

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ndevu12/the_inventory.git
   cd the_inventory
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For testing/linting tools
   ```

4. **Copy environment template:**
   ```bash
   cp .env.example .env.local
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **(Optional) Seed database:**
   ```bash
   python manage.py seed_database --clear --create-default
   ```

8. **Start server:**
   ```bash
   python manage.py runserver
   ```
   Visit: http://localhost:8000/admin/

#### Next.js Frontend

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Copy environment template:**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Install dependencies:**
   ```bash
   yarn install
   ```

4. **Start development server:**
   ```bash
   yarn dev
   ```
   Visit: http://localhost:3000

#### Verify Integration

- [ ] Backend running at `http://localhost:8000`
- [ ] Frontend running at `http://localhost:3000`
- [ ] Can access Wagtail admin at `http://localhost:8000/admin/`
- [ ] API endpoint responds: `http://localhost:8000/api/v1/`
- [ ] No CORS errors (check browser console)

#### JWT Cookie Configuration for Development

The system uses **HTTP-only cookies for JWT authentication**. For cookies to work correctly between frontend and backend, **both must use the same hostname**:

**✅ Correct (will work):**
- Frontend: `http://localhost:3000` → Backend: `http://localhost:8000`
- Frontend: `http://127.0.0.1:3000` → Backend: `http://127.0.0.1:8000` (not typically used)

**❌ Incorrect (cookies won't be shared):**
- Frontend: `http://localhost:3000` → Backend: `http://127.0.0.1:8000` (domain mismatch)
- Frontend: `http://127.0.0.1:3000` → Backend: `http://localhost:8000` (domain mismatch)

**To verify:** 
1. Login at `http://localhost:3000`
2. Open browser DevTools → Application/Storage → Cookies
3. Verify `access_token` and `refresh_token` cookies are present for `localhost`
4. If cookies show domain `127.0.0.1` but frontend URL shows `localhost`, you have a hostname mismatch

---

### Docker Deployment

#### Build and Run Locally

```bash
# Build image
docker build -t the_inventory:latest .

# Run with minimal environment (uses defaults)
docker run -p 8000:8000 \
  -e SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" \
  -e ALLOWED_HOSTS="localhost,127.0.0.1" \
  the_inventory:latest
```

#### Deploy to Render

1. **Connect your GitHub repository to Render**

2. **Create a Web Service with these Environment variables:**

   ```
   DJANGO_SETTINGS_MODULE        production
   SECRET_KEY                    <generate and paste here>
   ALLOWED_HOSTS                 your-service.onrender.com
   DATABASE_URL                  <Render PostgreSQL connection string>
   REDIS_URL                     <Render Redis connection string>
   FRONTEND_URL                  https://your-frontend.vercel.app
   AUTO_SEED_DATABASE            false  # true only for initial setup
   ```

3. **Database will auto-migrate** via `entrypoint.sh`

#### Deploy Frontend to Vercel

1. **Fork the repository**

2. **Create new Vercel project from `frontend/` directory**

3. **Set these Environment variables:**

   ```
   NEXT_PUBLIC_API_URL      https://your-service.onrender.com/api/v1
   NEXT_PUBLIC_APP_NAME     The Inventory - Production
   ```

4. **Deploy** — Vercel will build and deploy automatically

---

### Production Checklist

Before deploying to production:

- [ ] **Secrets are set** via platform secret manager (not in code)
  - `SECRET_KEY`
  - `EMAIL_HOST_PASSWORD` (if using SMTP)
  - Database password (in `DATABASE_URL`)
- [ ] **Domain configuration**
  - `ALLOWED_HOSTS` matches your domain(s)
  - `FRONTEND_URL` matches your frontend domain
  - CORS origins are restricted (not `*`)
  - **JWT Cookie configuration** — critical for authentication:
    - Frontend and backend use **matching hostnames** (both `example.com` or both `subdomain.example.com`, not mixed)
    - `JWT_COOKIE_SECURE=true` (HTTPS required)
    - `JWT_COOKIE_DOMAIN=.example.com` (for subdomain sharing) or blank (for same-domain)
    - `JWT_COOKIE_SAMESITE` set appropriately (`Lax` for same-domain, `None` for cross-origin with `Secure=true`)
- [ ] **Database**
  - PostgreSQL (not SQLite)
  - Backups configured
  - Migrations run: `python manage.py migrate`
- [ ] **Static files**
  - Collected: `python manage.py collectstatic`
  - Served from CDN or cloud storage (S3, GCS, etc.)
- [ ] **Email**
  - SMTP credentials set
  - `DEFAULT_FROM_EMAIL` configured
- [ ] **Logging**
  - `DJANGO_LOG_LEVEL=INFO` (at least)
  - Logs sent to centralized system (Papertrail, CloudWatch, etc.)
- [ ] **Monitoring**
  - Uptime monitoring configured
  - Error tracking (Sentry, etc.) – optional but recommended
- [ ] **HTTPS/TLS**
  - SSL certificate configured (Let's Encrypt, AWS ACM, etc.)
  - All non-HTTPS traffic redirected
- [ ] **Frontend environment variables**
  - `NEXT_PUBLIC_API_URL` points to correct API
  - Built with production configuration

---

## Translations (Django & Next.js)

### Django (`gettext`)

- **Catalog location:** `locale/<lang>/LC_MESSAGES/django.po` (see `LOCALE_PATHS` in settings).
- **Extract / update messages** (always exclude virtualenv and frontend dependencies so `xgettext` does not scan them):

  ```bash
  python manage.py makemessages -l fr -l sw -l rw -l es \
    --ignore=venv --ignore=.venv --ignore=frontend/node_modules --ignore=node_modules
  ```

- **Compile** `.po` → `.mo` (required for runtime translations):

  ```bash
  python manage.py compilemessages
  ```

  Project catalogs under `locale/**/LC_MESSAGES/*.mo` are tracked in git (see `.gitignore`).

- **Mark strings:** use `django.utils.translation.gettext_lazy as _` (models/forms) or `gettext` in views; use `{% raw %}{% trans %}{% endraw %}` / `{% raw %}{% blocktrans %}{% endraw %}` in templates.
- **Wagtail / Django admin:** pick a language via the user language preference or `Accept-Language` / `LocaleMiddleware` once `LANGUAGES` includes that code and the catalog is compiled.

### Next.js (`next-intl`)

- **Message files:** `frontend/public/locales/<locale>.json` (e.g. `en`, `fr`, `sw`, `rw`, `es`, `ar`), loaded in `frontend/src/i18n/load-messages.ts`.
- **Add or change UI copy:** keep the **same key structure** across locale files. For namespaces maintained by the merge pipeline (**Inventory**, **Sales**, **Reports**, **Auth**, **Audit**, **en.json** rebuild slices, etc.), edit the inputs under `frontend/scripts/` and run **`yarn locale:merge`** from `frontend/` — see **[I18N_FRONTEND.md](I18N_FRONTEND.md)**. For other namespaces you may edit `public/locales/*.json` directly (avoid editing merged subtrees by hand or the next merge will overwrite them).
- **Use in components:** `useTranslations('TopLevelNamespace')` on the client (nested keys: `t('child.grandchild')`); `getTranslations` / `getMessages` on the server (see `frontend/src/app/[locale]/layout.tsx`).

---

## Troubleshooting

### Common Issues

#### Django won't start with "DisallowedHost" error

**Error:**
```
400 Bad Request — Invalid HTTP_HOST header: 'my-service.onrender.com'. 
Expected one of: ['localhost', '127.0.0.1']
```

**Solution:**
Add your domain to `ALLOWED_HOSTS`:
```bash
ALLOWED_HOSTS=localhost,127.0.0.1,my-service.onrender.com
```

---

#### Frontend can't reach API (CORS error)

**Error (browser console):**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Solution:**
Ensure backend has frontend origin in `CORS_ALLOWED_ORIGINS`:
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

If frontend is on different machine/IP:
```bash
CORS_ALLOWED_ORIGINS=http://192.168.1.100:3000
```

---

#### "SECRET_KEY is missing" error in production

**Error:**
```
ValueError: SECRET_KEY is required for production deployments
```

**Solution:**
Set `SECRET_KEY` via platform environment:
1. Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. Store in Render Secrets, GitHub Secrets, or AWS Secrets Manager
3. Set as environment variable on service

**Never hardcode secrets in `.env` files committed to git!**

---

#### Database connection fails

**Error:**
```
django.core.exceptions.ImproperlyConfigured: 
The 'django.contrib.postgres' app is available, 
but not installed. (No installed app with label 'postgres'.)
```

**Solution:**
Ensure `DATABASE_URL` is set correctly:
```bash
# Format: postgresql://[user]:[password]@[host]:[port]/[database]
DATABASE_URL=postgresql://postgres:password@localhost:5432/the_inventory
```

Check connection:
```bash
# Test connection locally
psql postgresql://postgres:password@localhost:5432/the_inventory -c "SELECT 1"
```

---

#### Redis connection fails

**Error:**
```
ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Solution:**
Redis is optional. If you don't have Redis running:
- **Option 1:** Keep `REDIS_URL` unset — Django will use in-memory cache
- **Option 2:** Install and start Redis locally:
  ```bash
  # macOS
  brew install redis && redis-server
  
  # Ubuntu/Debian
  sudo apt-get install redis-server && redis-server
  
  # Docker
  docker run -p 6379:6379 redis:latest
  ```

---

#### Email not sending

**Error:**
```
No handlers could be found for logger "django.request"
Connection refused connecting to SMTP server
```

**Solution:**

1. **Check email backend:**
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # Dev only
   ```

2. **For production SMTP:**
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password  # Use app-specific password for Gmail!
   DEFAULT_FROM_EMAIL=noreply@example.com
   ```

3. **Test locally:**
   ```bash
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail(
   ...     'Test', 
   ...     'This is a test email', 
   ...     'noreply@example.com', 
   ...     ['recipient@example.com']
   ... )
   ```

---

#### "Unexpected keyword argument: SEED_MODELS" error

**Error:**
```
TypeError: seed_database() got unexpected keyword argument 'seed_models'
```

**Solution:**
The environment variable is `SEED_MODELS` (with underscore), not `SEED-MODELS`:
```bash
# ✅ Correct
SEED_MODELS=categories,products

# ❌ Wrong
SEED_MODELS=categories,products  # (typo in env var name)
```

---

#### Migrations pending error

**Error:**
```
You have unapplied migrations for apps: inventory, ...
```

**Solution:**
Run migrations:
```bash
python manage.py migrate
```

Or in Docker, migrations auto-run via `entrypoint.sh`.

---

### Getting Help

If you're stuck:

1. **Check logs** — look for error messages
   - Django: `python manage.py runserver` console output
   - Docker: `docker logs <container-id>`
   - Render: Dashboard → Logs tab

2. **Enable debug logging:**
   ```bash
   DJANGO_LOG_LEVEL=DEBUG
   ```

3. **Consult documentation:**
   - [Architecture Guide](ARCHITECTURE.md)
   - [Seeding Guide](SEEDING_GUIDE.md)
   - [Contributing Guide](../CONTRIBUTING.md)

4. **Open an issue** on GitHub with error messages and environment details

---

## Quick Reference

### Environment Variables by Category

| Category | Variables |
|----------|-----------|
| **Core** | `SECRET_KEY`, `ALLOWED_HOSTS`, `DJANGO_LOG_LEVEL` |
| **Database** | `DATABASE_URL`, `STATIC_URL`, `MEDIA_URL` |
| **Caching** | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_TASK_ALWAYS_EAGER` |
| **URLs** | `FRONTEND_URL`, `PUBLIC_BASE_URL`, `WAGTAILADMIN_BASE_URL` |
| **Security** | `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `JWT_COOKIE_SAMESITE`, `JWT_COOKIE_SECURE` |
| **Tenants** | `ENABLE_PUBLIC_TENANT_REGISTRATION`, `AUDIT_TENANT_ACCESS` |
| **API** | `API_PAGE_SIZE`, `JWT_ACCESS_TOKEN_MINUTES`, `JWT_REFRESH_TOKEN_DAYS` |
| **Caching TTLs** | `STOCK_CACHE_TTL_SECONDS`, `DASHBOARD_CACHE_TTL_SECONDS` |
| **Docs** | `API_DOC_TITLE`, `API_DOC_DESCRIPTION`, `API_DOC_VERSION` |
| **Email** | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `DEFAULT_FROM_EMAIL` |
| **Seeding** | `AUTO_SEED_DATABASE`, `SEED_CLEAR`, `SEED_QUIET`, `SEED_TENANT`, `SEED_MODELS` |
| **Frontend** | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_NAME` |

### All Environment Variables (Testing Checklist)

**Backend (.env or platform environment):**
- Core: `SECRET_KEY`, `ALLOWED_HOSTS`, `DJANGO_LOG_LEVEL`, `LANGUAGE_CODE`, `TIME_ZONE`
- Database: `DATABASE_URL`, `STATIC_URL`, `MEDIA_URL`
- Redis/Cache: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_TASK_ALWAYS_EAGER`
- URLs: `FRONTEND_URL`, `PUBLIC_BASE_URL`, `WAGTAILADMIN_BASE_URL`, `WAGTAIL_SITE_NAME`
- Tenants: `ENABLE_PUBLIC_TENANT_REGISTRATION`, `AUDIT_TENANT_ACCESS`
- CORS/CSRF: `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, `CORS_EXTRA_HEADERS`, `CSRF_TRUSTED_ORIGINS`, `JWT_COOKIE_SAMESITE`, `JWT_COOKIE_SECURE`, `USE_X_FORWARDED_PROTO`
- API: `API_PAGE_SIZE`, `JWT_ACCESS_TOKEN_MINUTES`, `JWT_REFRESH_TOKEN_DAYS`
- Cache TTLs: `STOCK_CACHE_TTL_SECONDS`, `DASHBOARD_CACHE_TTL_SECONDS`
- Docs: `API_DOC_TITLE`, `API_DOC_DESCRIPTION`, `API_DOC_VERSION`
- Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- Seeding: `AUTO_SEED_DATABASE`, `SEED_CLEAR`, `SEED_QUIET`, `SEED_TENANT`, `SEED_MODELS`

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL` (required)
- `NEXT_PUBLIC_APP_NAME` (optional)

---

## Additional Resources

- [Architecture Guide](ARCHITECTURE.md) — Technical design and deployment patterns
- [Seeding Guide](SEEDING_GUIDE.md) — Database seeding with environment variables
- [.env.example](../.env.example) — Complete template with all variables
- [Contributing Guide](../CONTRIBUTING.md) — Local development setup for contributors
- [Django Settings Documentation](https://docs.djangoproject.com/en/6.0/topics/settings/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
