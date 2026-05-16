# Security Guide

## Overview

The Inventory is built with security as a core principle. This guide covers security features, best practices, and how to report vulnerabilities.

---

## Security Features

### Authentication

**JWT (JSON Web Tokens)**
- Stateless authentication
- Tokens expire after 24 hours
- Refresh tokens for extended sessions
- Secure token storage (httpOnly cookies recommended)

**Password Security**
- PBKDF2 hashing with SHA256
- Minimum 8 characters
- Complexity requirements enforced
- Password reset via email

**Multi-Factor Authentication (MFA)**
- Optional MFA support
- TOTP (Time-based One-Time Password)
- Backup codes for account recovery

See [API Reference - Authentication](api.md#authentication) for implementation details.

### Authorization

**Role-Based Access Control (RBAC)**
- Admin — Full system access
- Manager — Tenant management and user management
- Staff — Inventory operations
- Viewer — Read-only access

**Tenant Isolation**
- Complete data separation between tenants
- Users can only access their tenant's data
- Cross-tenant access is impossible
- Audit trails per tenant

**Permission Levels**
- Object-level permissions
- Field-level permissions
- Custom permission rules

### Data Protection

**Encryption in Transit**
- HTTPS/TLS 1.2+ required in production
- All API communication encrypted
- Secure cookie transmission

**Encryption at Rest**
- Database-level encryption (optional)
- Sensitive fields encrypted in database
- Secure key management

**Data Isolation**
- Tenant data completely isolated
- No cross-tenant data leakage
- Separate database schemas (optional)

### Input Validation

**Request Validation**
- All inputs validated on server-side
- Type checking and format validation
- Length and range validation
- Whitelist-based validation

**SQL Injection Prevention**
- Parameterized queries (ORM)
- No raw SQL queries
- Input sanitization

**XSS Prevention**
- Output encoding
- Content Security Policy (CSP) headers
- No inline scripts

### CSRF Protection

**Cross-Site Request Forgery**
- CSRF tokens for state-changing requests
- SameSite cookie attribute
- Origin validation

### Rate Limiting

**API Rate Limiting**
- Per-user rate limits
- Per-IP rate limits
- Configurable limits per endpoint
- Graceful degradation under load

**Brute Force Protection**
- Account lockout after failed attempts
- Progressive delays
- IP-based blocking

### Audit Trails

**Complete Audit Logging**
- All data changes logged
- User and timestamp recorded
- Change details captured
- Immutable audit records

**Access Logging**
- All API requests logged
- Authentication attempts logged
- Failed access attempts logged
- Suspicious activity flagged

---

## Best Practices

### For Administrators

#### 1. Environment Configuration

**Production Environment:**
```bash
# .env
DEBUG=False
ALLOWED_HOSTS=api.example.com
SECRET_KEY=<strong-random-key>
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

**Never:**
- Use DEBUG=True in production
- Commit secrets to version control
- Use default SECRET_KEY
- Allow all hosts

#### 2. User Management

**Strong Passwords**
- Enforce minimum 12 characters
- Require complexity (uppercase, lowercase, numbers, symbols)
- Regular password rotation (90 days)
- Prevent password reuse

**Account Security**
- Disable inactive accounts after 90 days
- Require MFA for admin accounts
- Regular access reviews
- Remove access immediately when users leave

**Principle of Least Privilege**
- Grant minimum necessary permissions
- Use specific roles, not admin
- Regular permission audits
- Document permission changes

#### 3. API Security

**CORS Configuration**
```python
# Only allow trusted origins
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]
```

**API Keys**
- Rotate API keys regularly
- Use separate keys per application
- Monitor key usage
- Revoke unused keys

**Rate Limiting**
- Configure appropriate limits
- Monitor for abuse
- Adjust based on usage patterns
- Alert on suspicious activity

#### 4. Database Security

**Access Control**
- Use strong database passwords
- Limit database user permissions
- Use separate users for different applications
- Disable default accounts

**Backups**
- Encrypt backups
- Store backups securely
- Test restore procedures
- Maintain backup retention policy

**Monitoring**
- Monitor database access
- Alert on unusual queries
- Monitor performance
- Track schema changes

#### 5. Infrastructure Security

**Server Hardening**
- Keep OS and packages updated
- Disable unnecessary services
- Configure firewall rules
- Use SSH keys (not passwords)

**Network Security**
- Use VPN for admin access
- Restrict API access by IP (if possible)
- Use WAF (Web Application Firewall)
- Monitor network traffic

**Monitoring & Logging**
- Centralized logging
- Real-time alerting
- Regular log review
- Long-term log retention

### For Developers

#### 1. Secure Coding

**Input Validation**
```python
# ✅ Good: Validate all inputs
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'price']
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value

# ❌ Bad: No validation
def create_product(request):
    name = request.GET.get('name')  # No validation!
    Product.objects.create(name=name)
```

**Parameterized Queries**
```python
# ✅ Good: Use ORM
products = Product.objects.filter(name=search_term)

# ❌ Bad: Raw SQL
products = Product.objects.raw(f"SELECT * FROM products WHERE name = '{search_term}'")
```

**Error Handling**
```python
# ✅ Good: Generic error messages
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    raise serializers.ValidationError("Invalid credentials")

# ❌ Bad: Revealing error messages
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    raise serializers.ValidationError(f"User {email} not found")
```

#### 2. Authentication & Authorization

**Protect Endpoints**
```python
# ✅ Good: Require authentication
from rest_framework.permissions import IsAuthenticated

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only return user's tenant data
        return Product.objects.filter(tenant=self.request.user.tenant)

# ❌ Bad: No authentication
class ProductViewSet(viewsets.ModelViewSet):
    # Anyone can access!
    pass
```

**Tenant Isolation**
```python
# ✅ Good: Filter by tenant
def get_queryset(self):
    return Product.objects.filter(tenant=self.request.user.tenant)

# ❌ Bad: No tenant filtering
def get_queryset(self):
    return Product.objects.all()  # All tenants!
```

#### 3. Dependency Management

**Keep Dependencies Updated**
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade -r requirements.txt
```

**Use Pinned Versions**
```
# ✅ Good: Pinned versions
Django==4.2.0
djangorestframework==3.14.0

# ❌ Bad: Open ranges
Django>=4.0
djangorestframework>=3.0
```

#### 4. Secrets Management

**Never Commit Secrets**
```bash
# ✅ Good: Use environment variables
SECRET_KEY = os.environ.get('SECRET_KEY')

# ❌ Bad: Hardcoded secrets
SECRET_KEY = 'my-secret-key-12345'
```

**Use .env Files**
```bash
# .env (never commit)
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgres://user:pass@localhost/db
API_KEY=<api-key>

# .env.example (commit this)
SECRET_KEY=<change-me>
DATABASE_URL=postgres://user:pass@localhost/db
API_KEY=<change-me>
```

#### 5. Testing Security

**Test Authentication**
```python
def test_unauthenticated_access_denied():
    response = client.get('/api/products/')
    assert response.status_code == 401

def test_authenticated_access_allowed():
    client.force_authenticate(user=user)
    response = client.get('/api/products/')
    assert response.status_code == 200
```

**Test Authorization**
```python
def test_user_cannot_access_other_tenant():
    user1 = create_user(tenant=tenant1)
    user2 = create_user(tenant=tenant2)
    
    client.force_authenticate(user=user1)
    response = client.get(f'/api/products/{user2_product.id}/')
    assert response.status_code == 403
```

**Test Input Validation**
```python
def test_invalid_price_rejected():
    response = client.post('/api/products/', {
        'name': 'Product',
        'price': -10  # Invalid!
    })
    assert response.status_code == 400
```

---

## Vulnerability Management

### Reporting Vulnerabilities

**Responsible Disclosure**

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. **Do NOT** post on social media
3. **Do NOT** share details publicly

**Report To:**
- Email: security@example.com
- Or use GitHub's [Security Advisory](https://github.com/Ndevu12/the_inventory/security/advisories)

**Include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

**Response Timeline:**
- Acknowledgment within 24 hours
- Initial assessment within 48 hours
- Fix and patch within 7 days (or timeline agreed upon)
- Public disclosure after patch is released

### Security Updates

**Staying Updated**
- Watch the [GitHub repository](https://github.com/Ndevu12/the_inventory)
- Subscribe to [security advisories](https://github.com/Ndevu12/the_inventory/security/advisories)
- Check [Changelog](../CHANGELOG.md) for security fixes
- Follow [releases](https://github.com/Ndevu12/the_inventory/releases)

**Applying Updates**
```bash
# Check for security updates
pip install --upgrade pip
pip list --outdated

# Update dependencies
pip install --upgrade -r requirements.txt

# Run tests
pytest

# Deploy to production
# (See Deployment Guide)
```

---

## Data Protection

### Personal Data

**Data Collection**
- Only collect necessary data
- Inform users what data is collected
- Get explicit consent for data processing
- Provide data access and deletion options

**Data Retention**
- Define retention periods
- Delete data when no longer needed
- Archive old data securely
- Comply with regulations (GDPR, CCPA, etc.)

**Data Sharing**
- Never share data with third parties without consent
- Use data processing agreements
- Limit data access to necessary personnel
- Audit data sharing

### Compliance

**GDPR (General Data Protection Regulation)**
- Right to access personal data
- Right to be forgotten (deletion)
- Right to data portability
- Privacy by design

**CCPA (California Consumer Privacy Act)**
- Right to know what data is collected
- Right to delete personal data
- Right to opt-out of data sales
- Non-discrimination for exercising rights

**HIPAA (Health Insurance Portability and Accountability Act)**
- If handling health data, implement HIPAA controls
- Encryption and access controls
- Audit trails and monitoring
- Business associate agreements

---

## Security Checklist

### Before Deployment

- [ ] DEBUG=False in production
- [ ] SECRET_KEY is strong and random
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS/TLS enabled
- [ ] Database password is strong
- [ ] Database backups configured
- [ ] Logging and monitoring configured
- [ ] Rate limiting configured
- [ ] CORS configured for trusted origins only
- [ ] Admin interface protected
- [ ] All dependencies updated
- [ ] Security tests passing
- [ ] Code review completed
- [ ] Security audit completed

### Regular Maintenance

- [ ] Weekly: Check for security updates
- [ ] Monthly: Review access logs
- [ ] Monthly: Audit user permissions
- [ ] Quarterly: Security assessment
- [ ] Quarterly: Penetration testing
- [ ] Annually: Full security audit

### Incident Response

**If a Security Incident Occurs:**

1. **Assess the Situation**
   - What was compromised?
   - How did it happen?
   - Who has access?

2. **Contain the Incident**
   - Disable affected accounts
   - Revoke compromised tokens
   - Block suspicious IPs
   - Isolate affected systems

3. **Investigate**
   - Review logs
   - Identify root cause
   - Determine scope
   - Document findings

4. **Remediate**
   - Fix the vulnerability
   - Apply patches
   - Update security controls
   - Test fixes

5. **Communicate**
   - Notify affected users
   - Provide guidance
   - Offer support
   - Be transparent

6. **Learn**
   - Post-incident review
   - Update procedures
   - Improve monitoring
   - Share lessons learned

---

## Security Resources

### Internal Documentation
- [API Reference - Authentication](api.md#authentication)
- [Deployment Guide - Security](deployment.md#security)
- [Operations Guide - Monitoring](operations.md#monitoring)
- [Development Guide - Secure Coding](development.md#secure-coding)

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Django REST Framework Security](https://www.django-rest-framework.org/topics/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### Tools
- [OWASP ZAP](https://www.zaproxy.org/) — Web application security scanner
- [Bandit](https://bandit.readthedocs.io/) — Python security issue scanner
- [Safety](https://safety.readthedocs.io/) — Dependency vulnerability checker
- [Snyk](https://snyk.io/) — Vulnerability management

---

## Questions?

For security questions or concerns:

1. Check this guide
2. Review [API Reference - Authentication](api.md#authentication)
3. Check [Troubleshooting Guide](troubleshooting.md)
4. Create a [GitHub Discussion](https://github.com/Ndevu12/the_inventory/discussions)
5. Contact security team (security@example.com)

**Security is everyone's responsibility. Thank you for helping keep The Inventory secure!** 🔒
