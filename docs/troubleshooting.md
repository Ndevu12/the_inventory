# Troubleshooting Guide

Common issues and solutions for The Inventory development.

## CORS Errors

**Symptom:** Browser shows `No 'Access-Control-Allow-Origin' header is present`

**Most Common Cause:** Backend isn't running.

**Solution:**
```bash
cd src
python manage.py runserver
```

You should see a CORS warning box - this is normal in development and means all origins are allowed.

**Still not working?**
1. Check `frontend/.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
2. Verify both frontend and backend are running
3. Clear browser cache and reload

**Production:** Set `CORS_ALLOWED_ORIGINS=https://your-domain.com` in `.env`

---

## Network Access (Mobile/Other Devices)

**To test on mobile or another computer:**

1. Find your IP: `ip addr show` (Linux/Mac) or `ipconfig` (Windows)
2. Start Django: `python manage.py runserver 0.0.0.0:8000`
3. Access from device: `http://YOUR_IP:3000`

Development CORS allows this automatically - no configuration needed!

**Firewall blocking?**
- Linux: `sudo ufw allow 3000 && sudo ufw allow 8000`
- Mac/Windows: Allow Python/Node in firewall settings


---

## Database Issues

**Migration errors:**
```bash
cd src
rm db.sqlite3  # Development only!
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_database --clear --create-default
```

**PostgreSQL connection:**
```bash
# Check .env format
DATABASE_URL=postgresql://username:password@host:port/database
```

---

## Authentication Issues

**Can't login:**
1. Clear browser storage (F12 → Application → Clear site data)
2. Verify user exists: `python manage.py createsuperuser`
3. Check tenant membership: `python manage.py seed_database --create-default`

**"No tenant membership" error:**
```bash
cd src
python manage.py seed_database --create-default
```

---

## JWT Authentication 401 Errors (Production)

**Symptom:** Login works (200) but subsequent requests fail with `401 Unauthorized`. Cookies appear in DevTools but aren't being sent.

### Root Cause Analysis

The issue depends on your domain setup:

#### Scenario 1: Different Domains (No Shared Parent)
**Example:** Frontend on `vercel.app`, Backend on `onrender.com`

**Why it fails:**
- Backend cannot set cookies on a different domain
- Browsers enforce same-origin policy
- Cookies set by `onrender.com` won't be sent to `vercel.app`

**Solution:** Use token-based auth (Authorization header) instead of cookies
```python
# Backend settings.py
JWT_COOKIE_DOMAIN = None  # Disable cookie-based auth
```

#### Scenario 2: Shared Parent Domain (Recommended)
**Example:** Frontend on `theinventory.ndevuspace.com`, Backend on `api.theinventory.ndevuspace.com`

**Why it fails initially:**
- `JWT_COOKIE_DOMAIN = None` means cookies are only valid for exact domain match
- Cookies set by backend aren't sent to frontend because domain doesn't match

**Solution:** Set cookie domain to shared parent domain
```python
# Backend settings.py
JWT_COOKIE_DOMAIN = ".ndevuspace.com"  # Leading dot = all subdomains
JWT_COOKIE_SECURE = True               # Required for HTTPS
JWT_COOKIE_SAMESITE = "Lax"            # Safe for same parent domain
```

**Why this works:**
- `.ndevuspace.com` allows cookies to be shared between all subdomains
- Browser will include cookies in requests from `theinventory.ndevuspace.com` to `api.theinventory.ndevuspace.com`

### Configuration Checklist

**For shared parent domain setup:**

1. ✅ Frontend and backend share parent domain
   ```
   Frontend:  theinventory.ndevuspace.com
   Backend:   api.theinventory.ndevuspace.com
   Parent:    ndevuspace.com (shared)
   ```

2. ✅ Backend environment variables set correctly
   ```bash
   JWT_COOKIE_DOMAIN=.ndevuspace.com
   JWT_COOKIE_SECURE=True
   JWT_COOKIE_SAMESITE=Lax
   ```

3. ✅ Frontend API URL points to backend
   ```bash
   NEXT_PUBLIC_API_URL=https://api.theinventory.ndevuspace.com/api/v1
   ```

4. ✅ CORS configured correctly
   ```python
   CORS_ALLOWED_ORIGINS = [
       "https://theinventory.ndevuspace.com",
   ]
   CORS_ALLOW_CREDENTIALS = True
   ```

### Verify the Fix

1. After login, check browser DevTools → Application → Cookies
2. Find `access_token` cookie
3. Verify `Domain` column shows `.ndevuspace.com` (with leading dot)
4. Verify `Secure` is checked (for HTTPS)
5. Check Network tab → `/api/v1/auth/me/` request
6. Should see `Cookie: access_token=...` header
7. Response should be 200 (not 401)

### If Still Failing

- Verify `JWT_COOKIE_DOMAIN` matches your domain setup
- Clear browser cookies and log in again
- Check backend logs for CORS errors
- Verify `CORS_ALLOW_CREDENTIALS = True` in backend
- Ensure frontend and backend are on HTTPS in production

---

## Development Environment

**Port already in use:**
```bash
# Find process
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill it
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

**Python environment issues:**
```bash
deactivate
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Node/Yarn issues:**
```bash
cd frontend
rm -rf node_modules .next yarn.lock
yarn install
```

---

## Testing

**Tests not discovered?**

Ensure you're running from the `src/` directory:
```bash
cd src
python manage.py test
```

**Want to run only seeder tests?**
```bash
python manage.py test tests.seeders
```

**Want to run a specific test?**
```bash
python manage.py test tests.api.test_auth.AuthTestCase.test_login
```

**Understanding test output:**

The custom test runner automatically excludes seeder tests by default. You'll see:
- ~1487 tests when running `python manage.py test` (seeders excluded)
- ~34 tests when running `python manage.py test tests.seeders` (seeders only)

This is intentional — seeder tests are only included when explicitly requested.

---

```bash
# Backend
cd src
python manage.py runserver              # Start
python manage.py runserver 0.0.0.0:8000 # Network access
python manage.py migrate                # Migrations
python manage.py createsuperuser        # Admin user

# Frontend
cd frontend
yarn install    # Dependencies
yarn dev        # Start
yarn build      # Production build

# Database
python manage.py dbshell        # Database shell
python manage.py shell          # Django shell
```

---

## Still Stuck?

1. Check logs in terminal where servers are running
2. Check browser console (F12)
3. See [Environment Guide](ENVIRONMENT.md) for configuration
4. [Report an issue](https://github.com/Ndevu12/the_inventory/issues)
