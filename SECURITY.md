# Security Policy

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

Security patches for critical vulnerabilities are released for the current stable version only.

---

## Core Security Features

### Authentication & Authorization
- **Multi-Tenant Architecture** with tenant-level data isolation
- **RBAC**: Owner, Admin, Manager, Viewer roles
- **JWT, Token & Session Authentication** supported

### Data Protection
- **Password Validation**: Django enforced validators
- **Secure Cookies**: HttpOnly, SameSite=Lax (production)
- **CSRF & CORS Protection**: Configurable and enforced
- **SQL Injection Prevention**: Django ORM parameterized queries
- **Tenant Query Filtering**: Users access only their tenant data

### Transport Security
- **TLS/SSL**: X-Forwarded-Proto support for load balancers
- **Security Middleware**: X-Frame-Options, anti-MIME-type sniffing

---

## Production Deployment Checklist

- [ ] Set unique, random `SECRET_KEY` via environment variable
- [ ] Disable `DEBUG` mode (enforced in production settings)
- [ ] List allowed domains in `ALLOWED_HOSTS`
- [ ] Use PostgreSQL (not SQLite) with SSL enabled
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Configure `CORS_ALLOWED_ORIGINS` explicitly (list allowed domains)
- [ ] Set up Redis for caching if multi-process
- [ ] Use strong database credentials from secrets manager
- [ ] Enable logging to centralized system
- [ ] Configure SMTP for email with TLS/SSL

**Key Environment Variables:**
```
SECRET_KEY=<unique-random-string>
DATABASE_URL=postgres://user:pass@host:5432/db
ALLOWED_HOSTS=example.com,www.example.com
CORS_ALLOWED_ORIGINS=https://frontend.example.com
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.example.com
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=<strong-password>
```

---

## Reporting Security Vulnerabilities

**Do not** open public GitHub issues for security vulnerabilities.

**Email:** Send details to [security@ndevu.com](mailto:security@ndevu.com) with:
- Vulnerability description
- Steps to reproduce
- Affected versions
- Potential impact

**Response Timeline:**
- **Critical**: Fixed and released within 7 days
- **High**: Fixed within 14 days
- **Medium/Low**: Included in next scheduled release

We ask for a 90-day embargo before public disclosure.

---

## Known Limitations & Roadmap

**Currently Not Implemented:**
- Rate limiting (use reverse proxy)
- Two-Factor Authentication (2FA)
- Data encryption at rest
- Detailed audit logging

**Planned:**
- 2FA (TOTP, email-based)
- Granular operation-level audit logs
- Data encryption at rest option
- Advanced rate limiting

---

## References

- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [Wagtail Deployment](https://docs.wagtail.org/en/stable/advanced_topics/deploying.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
