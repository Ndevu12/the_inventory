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

**Symptom:** Login works (200) but subsequent requests fail with `401 Unauthorized`

**Root Cause:** `JWT_COOKIE_DOMAIN` set to frontend domain (e.g., `.vercel.app`) when backend is on different domain (e.g., `.onrender.com`)

**Why it fails:**
- Backend on `.onrender.com` cannot set cookies on `.vercel.app` domain
- Browsers enforce same-origin policy: cookies can only be set by the domain that serves them
- Result: Cookies are rejected by browser, not stored, subsequent requests have no auth

**Quick Fix:**

1. Go to Render Dashboard → Your Web Service → Environment
2. Find `JWT_COOKIE_DOMAIN` 
3. **Clear the value** (leave empty)
4. Save and redeploy

**Why this works:**
- Empty `JWT_COOKIE_DOMAIN` = same-domain only (safe default)
- Frontend must use `Authorization: Bearer <token>` headers instead of cookies
- Your backend already supports this via `CookieJWTAuthentication`

**Verify the fix:**

1. After login, check browser DevTools → Network tab
2. Look at request to `/api/v1/auth/me/`
3. Should see: `Authorization: Bearer eyJ...` header
4. Should NOT see: `Cookie:` header (that's expected for cross-domain)
5. Response should be 200 (not 401)

**If still failing:**
- Verify `CORS_ALLOWED_ORIGINS` includes your frontend URL
- Verify `CSRF_TRUSTED_ORIGINS` matches `CORS_ALLOWED_ORIGINS`
- Check frontend is sending `Authorization` header (not relying on cookies)
- Check Render logs for CORS errors

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
