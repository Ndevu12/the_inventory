# Deployment Guide

This guide covers deploying **The Inventory** backend API to production environments.

---

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Docker Deployment](#docker-deployment)
- [Render Deployment](#render-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Restore](#backup--restore)

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] **Secret Key Generated** — Use a strong, random secret key
- [ ] **Database Configured** — PostgreSQL connection string ready
- [ ] **Domain/Hostname Set** — `ALLOWED_HOSTS` configured
- [ ] **CORS Origins Set** — Frontend URL(s) configured
- [ ] **Email Configured** — SMTP settings for notifications
- [ ] **Static Files** — Collected and ready to serve
- [ ] **SSL/TLS Certificate** — HTTPS enabled
- [ ] **Backups Configured** — Database backup strategy in place
- [ ] **Monitoring Set Up** — Logging and alerts configured
- [ ] **Tests Passing** — All tests pass locally

---

## Docker Deployment

### Build the Docker Image

```bash
docker build -t the_inventory:latest .
```

### Run Locally

```bash
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e ALLOWED_HOSTS="localhost,127.0.0.1" \
  -e DATABASE_URL="postgresql://user:pass@db:5432/inventory" \
  the_inventory:latest
```

### Push to Registry

```bash
# Tag image
docker tag the_inventory:latest your-registry/the_inventory:latest

# Push to registry
docker push your-registry/the_inventory:latest
```

### Docker Compose Example

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: inventory
      POSTGRES_USER: inventory_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn the_inventory.wsgi:application --bind 0.0.0.0:8000
    environment:
      DEBUG: "False"
      SECRET_KEY: "your-secret-key"
      ALLOWED_HOSTS: "localhost,127.0.0.1"
      DATABASE_URL: "postgresql://inventory_user:secure_password@db:5432/inventory"
      REDIS_URL: "redis://redis:6379/0"
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - ./src:/app/src

volumes:
  postgres_data:
```

Run with:

```bash
docker-compose up -d
```

---

## Render Deployment

### 1. Connect Repository

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `the_inventory` repository

### 2. Configure Service

**Basic Settings:**
- **Name:** `the-inventory-api`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt && python src/manage.py collectstatic --noinput`
- **Start Command:** `gunicorn the_inventory.wsgi:application --bind 0.0.0.0:8000 --chdir src`

### 3. Set Environment Variables

In Render dashboard, add these environment variables:

```
DEBUG=False
DJANGO_SETTINGS_MODULE=the_inventory.settings.production
SECRET_KEY=<generate-and-paste>
ALLOWED_HOSTS=your-service.onrender.com
DATABASE_URL=<PostgreSQL-connection-string>
REDIS_URL=<Redis-connection-string>
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

### 4. Create PostgreSQL Database

1. In Render dashboard, create a new PostgreSQL database
2. Copy the connection string
3. Paste into `DATABASE_URL` environment variable

### 5. Create Redis Cache

1. In Render dashboard, create a new Redis instance
2. Copy the connection string
3. Paste into `REDIS_URL` environment variable

### 6. Deploy

Click "Create Web Service" — Render will automatically deploy.

### 7. Run Migrations

After first deployment, run migrations:

```bash
# Via Render Shell
python src/manage.py migrate
python src/manage.py createsuperuser
```

---

## Kubernetes Deployment

### Create ConfigMap for Environment Variables

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: inventory-config
data:
  DEBUG: "False"
  DJANGO_SETTINGS_MODULE: "the_inventory.settings.production"
  ALLOWED_HOSTS: "api.example.com"
  FRONTEND_URL: "https://app.example.com"
  CORS_ALLOWED_ORIGINS: "https://app.example.com"
```

### Create Secret for Sensitive Data

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: inventory-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql://user:pass@db:5432/inventory"
  REDIS_URL: "redis://redis:6379/0"
```

### Create Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: inventory-api
  template:
    metadata:
      labels:
        app: inventory-api
    spec:
      containers:
      - name: api
        image: your-registry/the_inventory:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: inventory-config
        - secretRef:
            name: inventory-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Create Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: inventory-api-service
spec:
  selector:
    app: inventory-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to Kubernetes

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

---

## Environment Configuration

### Required Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Django secret key (generate new) |
| `ALLOWED_HOSTS` | `api.example.com` | Allowed hostnames |
| `DATABASE_URL` | `postgresql://user:pass@host/db` | PostgreSQL connection |
| `DEBUG` | `False` | Disable debug mode in production |

### Recommended Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://host:6379/0` | Redis cache connection |
| `FRONTEND_URL` | `https://app.example.com` | Frontend URL for redirects |
| `CORS_ALLOWED_ORIGINS` | `https://app.example.com` | Frontend CORS origin |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server |
| `EMAIL_HOST_USER` | `noreply@example.com` | SMTP username |
| `EMAIL_HOST_PASSWORD` | `app-password` | SMTP password |

See [Environment Variables](environment.md) for complete reference.

---

## Database Setup

### PostgreSQL Installation

**On Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
```

**On macOS:**
```bash
brew install postgresql
```

### Create Database and User

```bash
sudo -u postgres psql

CREATE DATABASE inventory;
CREATE USER inventory_user WITH PASSWORD 'secure_password';
ALTER ROLE inventory_user SET client_encoding TO 'utf8';
ALTER ROLE inventory_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE inventory_user SET default_transaction_deferrable TO on;
ALTER ROLE inventory_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory_user;
\q
```

### Connection String

```
postgresql://inventory_user:secure_password@localhost:5432/inventory
```

### Run Migrations

```bash
cd src
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

---

## Monitoring & Logging

### Application Logs

View logs from your deployment platform:

**Render:**
```bash
# Via Render dashboard → Logs tab
```

**Kubernetes:**
```bash
kubectl logs -f deployment/inventory-api
```

### Database Monitoring

Monitor PostgreSQL performance:

```bash
# Connect to database
psql postgresql://user:pass@host/inventory

# Check active connections
SELECT * FROM pg_stat_activity;

# Check slow queries
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC;
```

### Application Monitoring

Set up monitoring for:
- **Response times** — Track API latency
- **Error rates** — Monitor 4xx and 5xx errors
- **Database connections** — Ensure connection pool health
- **Memory usage** — Monitor memory consumption
- **CPU usage** — Monitor CPU utilization

### Alerting

Configure alerts for:
- High error rates (>5%)
- High response times (>1s)
- Database connection pool exhaustion
- Out of memory conditions
- Disk space low

---

## Backup & Restore

### Automated Backups

**PostgreSQL Backups:**

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/inventory"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump postgresql://user:pass@host/inventory > $BACKUP_DIR/inventory_$TIMESTAMP.sql
gzip $BACKUP_DIR/inventory_$TIMESTAMP.sql
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup-script.sh
```

### Manual Backup

```bash
pg_dump postgresql://user:pass@host/inventory > inventory_backup.sql
```

### Restore from Backup

```bash
psql postgresql://user:pass@host/inventory < inventory_backup.sql
```

### Cloud Backups

Use your cloud provider's backup service:
- **AWS RDS:** Automated backups included
- **Render:** Automated backups included
- **Google Cloud SQL:** Automated backups included

---

## SSL/TLS Configuration

### Render (Automatic)

Render automatically provides SSL certificates. Your service is accessible at:
```
https://your-service.onrender.com
```

### Self-Hosted (Let's Encrypt)

Use Certbot to get free SSL certificates:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d api.example.com
```

Configure Nginx to use the certificate:

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

---

## Troubleshooting

### Database Connection Error

```
Error: could not connect to server
```

**Solution:**
1. Verify `DATABASE_URL` is correct
2. Check database is running
3. Verify firewall allows connection

### Static Files Not Loading

```
404 Not Found for /static/...
```

**Solution:**
```bash
python src/manage.py collectstatic --noinput
```

### Secret Key Error

```
Error: SECRET_KEY is not set
```

**Solution:**
Generate and set SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Next Steps

- **Monitor your deployment** — Set up logging and alerts
- **Configure backups** — Ensure data is backed up regularly
- **Scale as needed** — Add more replicas/instances as traffic grows
- **Update regularly** — Keep dependencies updated for security

See [Troubleshooting Guide](troubleshooting.md) for more help.
