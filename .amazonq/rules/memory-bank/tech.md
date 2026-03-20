# Technology Stack & Development Guide

## Programming Languages & Versions

| Component | Language | Version |
|---|---|---|
| Backend | Python | 3.12+ |
| Frontend | TypeScript/JavaScript | ES2020+ |
| Database | SQL | PostgreSQL 12+ (prod) / SQLite 3 (dev) |
| Markup | HTML5 | - |
| Styling | CSS3 / Tailwind | - |

## Core Dependencies

### Backend Framework
- **Django**: 6.0 - Web framework
- **Wagtail**: 7.3rc1 - CMS and admin interface
- **Django REST Framework**: API framework
- **djangorestframework-simplejwt**: JWT authentication
- **drf-spectacular**: OpenAPI/Swagger documentation

### Database & ORM
- **psycopg2-binary**: PostgreSQL adapter
- **django-filter**: Query filtering
- **modelcluster**: Clustering for Wagtail

### Caching & Task Queue
- **django-redis**: Redis cache backend
- **Celery**: Distributed task queue
- **django-celery-results**: Celery results backend

### API & Integration
- **django-cors-headers**: CORS support
- **dj-database-url**: Database URL parsing

### Data Processing
- **openpyxl**: Excel file handling
- **reportlab**: PDF generation

### Frontend
- **Next.js**: React framework
- **React**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS
- **shadcn/ui**: Component library

## Build Systems & Tools

### Backend
- **pip**: Python package manager
- **Django**: Built-in management commands
- **Celery**: Task execution
- **Gunicorn**: WSGI application server (production)

### Frontend
- **npm/yarn**: Node package manager
- **Next.js**: Build and dev server
- **TypeScript**: Type checking
- **ESLint**: Code linting
- **Tailwind CSS**: CSS compilation

### Development Tools
- **ruff**: Python linter and formatter
- **pytest**: Testing framework (via Django test runner)
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## Development Commands

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Build search index
python manage.py update_index

# Seed database
python manage.py seed_database --clear --create-default
```

### Backend Development
```bash
# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run linter
ruff check .

# Format code
ruff format .

# Check migrations
python manage.py makemigrations --check --dry-run

# Create migrations
python manage.py makemigrations

# Run Celery worker (separate terminal)
celery -A the_inventory worker -l info

# Run Celery beat scheduler (separate terminal)
celery -A the_inventory beat -l info
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
```

### Frontend Development
```bash
# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run linter
npm run lint

# Type checking
npm run type-check
```

### Docker Development
```bash
# Build image
docker build -t the_inventory .

# Run container
docker run -p 8000:8000 the_inventory

# Using Docker Compose
docker-compose up -d
docker-compose down
```

### Database Management
```bash
# Create backup
python manage.py dumpdata > backup.json

# Restore from backup
python manage.py loaddata backup.json

# Clear database
python manage.py flush

# Database shell
python manage.py dbshell
```

### API Documentation
```bash
# Generate OpenAPI schema
python manage.py spectacular --file schema.yml

# Access Swagger UI
# http://localhost:8000/api/schema/swagger-ui/

# Access ReDoc
# http://localhost:8000/api/schema/redoc/
```

## Environment Configuration

### Development (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=True
FRONTEND_URL=http://localhost:3000
ENABLE_PUBLIC_TENANT_REGISTRATION=False
```

### Production (.env)
```
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
FRONTEND_URL=https://yourdomain.com
ENABLE_PUBLIC_TENANT_REGISTRATION=True
WAGT AIL_ADMIN_BASE_URL=https://yourdomain.com
```

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test inventory

# Run specific test class
python manage.py test inventory.tests.test_models.ProductModelTests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Structure
- `inventory/tests/` - Inventory app tests
- `api/tests/` - API endpoint tests
- `tenants/tests/` - Multi-tenancy tests
- `procurement/tests/` - Procurement tests
- `sales/tests/` - Sales tests
- `reports/tests/` - Reporting tests

## CI/CD Pipeline

### GitHub Actions (.github/workflows/ci.yml)
Runs on push and pull requests to `main`:
- `python manage.py check` - Django system checks
- `python manage.py test` - Run test suite
- `python manage.py makemigrations --check --dry-run` - Check migrations
- `ruff check .` - Lint code

## Performance Optimization

### Caching
- Stock levels: 10 minutes TTL
- Dashboard data: 5 minutes TTL
- Redis backend in production
- Local memory cache in development

### Database
- Connection pooling via psycopg2
- Query optimization with select_related/prefetch_related
- Indexes on frequently queried fields
- Pagination with 25 items per page

### API
- Pagination for list endpoints
- Filtering and search capabilities
- Async task processing with Celery
- Response compression

## Deployment

### Local Development
```bash
python manage.py runserver
```

### Production with Gunicorn
```bash
gunicorn the_inventory.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Docker Deployment
```bash
docker build -t the_inventory:latest .
docker run -p 8000:8000 \
  -e DEBUG=False \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  the_inventory:latest
```

### Kubernetes (Optional)
- Containerized with Docker
- Stateless design for horizontal scaling
- Separate Celery workers
- Shared PostgreSQL and Redis

## Monitoring & Logging

### Application Logs
- Django logging to console/file
- Celery task logging
- Request/response logging

### Metrics
- Wagtail admin dashboard
- Custom dashboard panels
- API usage statistics

### Health Checks
- `/api/health/` endpoint (if implemented)
- Database connectivity
- Redis connectivity
- Celery worker status
