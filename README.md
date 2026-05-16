# The Inventory — Backend API

[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/Django-6.0-092E20.svg)](https://djangoproject.com/)
[![Wagtail 7.3](https://img.shields.io/badge/Wagtail-7.3-43B1B0.svg)](https://wagtail.org/)

A comprehensive **REST API** for inventory management built with [Django](https://djangoproject.com/) and [Wagtail CMS](https://wagtail.org/). Manage products, stock levels, warehouses, purchases, sales, and reporting through a powerful headless API.

**This is the backend API only.** For the frontend UI, see [the-inventory-ui](https://github.com/Ndevu12/the-inventory-ui).

---

## Features

- 📦 **Inventory Management** — Products, categories, stock locations, and movements
- 🛒 **Procurement** — Suppliers, purchase orders, goods received notes
- 💳 **Sales** — Customers, sales orders, dispatch tracking
- 📊 **Reporting** — Stock valuation, movement history, analytics
- 🌍 **Multi-Tenancy** — Support multiple organizations on one deployment
- 🔐 **Security** — JWT authentication, RBAC, audit logging
- 🔌 **REST API** — Comprehensive API with OpenAPI documentation
- 🌐 **Internationalization** — Support for multiple languages

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Web Framework | Django 6.0 |
| API | Django REST Framework |
| Admin UI | Wagtail 7.3 |
| Database | SQLite (dev) / PostgreSQL (production) |
| Search | Wagtail search backend |
| Containerization | Docker |

---

## Quick Start

**For detailed setup instructions, see the [Getting Started Guide](docs/getting-started.md).**

### Prerequisites

- Python 3.12 or later
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Ndevu12/the_inventory.git
cd the_inventory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Navigate to backend
cd src

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Access the API

- **API Root:** http://localhost:8000/api/v1/
- **API Documentation:** http://localhost:8000/api/schema/swagger/
- **Wagtail Admin:** http://localhost:8000/admin/

---

## Documentation

| Guide | Purpose |
|-------|---------|
| [Getting Started](docs/getting-started.md) | Installation and first steps |
| [Features](docs/features.md) | What this API provides |
| [API Reference](docs/api.md) | REST API endpoints and examples |
| [Deployment](docs/deployment.md) | Production deployment (Docker, Render, K8s) |
| [Integration](docs/integration.md) | How to integrate with frontend |
| [Development](docs/development.md) | For contributors |
| [Operations](docs/operations.md) | For platform operators |
| [Security](docs/security.md) | Security best practices |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [FAQ](docs/faq.md) | Frequently asked questions |
| [Architecture](docs/architecture.md) | Technical design |
| [Environment Variables](docs/environment.md) | Configuration reference |
| [Roadmap](docs/roadmap.md) | Development roadmap |

---

## Project Structure

```
src/
├── manage.py                    # Django entry point
├── the_inventory/               # Project configuration
│   ├── settings/                # base, dev, production
│   ├── urls.py                  # URL routing
│   └── wsgi.py                  # WSGI application
├── api/                         # REST API
├── inventory/                   # Core inventory app
├── procurement/                 # Procurement app
├── sales/                        # Sales app
├── reports/                     # Reporting app
├── tenants/                     # Multi-tenancy
└── locale/                      # Translations

seeders/                         # Database seeding
tests/                           # Test suite
docs/                            # Documentation
```

See [Architecture](docs/architecture.md) for the full technical design.

---

## Docker

Build and run with Docker:

```bash
# Build image
docker build -t the_inventory .

# Run container
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql://user:pass@db:5432/inventory" \
  the_inventory
```

For complete deployment instructions, see [Deployment Guide](docs/deployment.md).

---

## Testing

```bash
cd src

# Run all tests (seeders excluded)
python manage.py test

# Run specific test module
python manage.py test tests.api

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

See [Development Guide](docs/development.md) for more testing details.

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

---

## Frontend

The official frontend is a separate repository:

**[the-inventory-ui](https://github.com/Ndevu12/the-inventory-ui)** — Next.js UI for The Inventory

You can also build your own frontend using any framework (React, Vue, Angular, etc.) by consuming this REST API.

---

## License

This project is licensed under the **BSD 3-Clause License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026, Jean Paul Elisa NIYOKWIZERWA.

---

## Support

- 📖 **Documentation:** See [docs/](docs/)
- 🐛 **Issues:** [GitHub Issues](https://github.com/Ndevu12/the_inventory/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Ndevu12/the_inventory/discussions)
- 📧 **Email:** support@example.com

---

## Roadmap

See [Roadmap](docs/roadmap.md) for planned features and development phases.

---

## Changelog

See [Changelog](CHANGELOG.md) for release notes and version history.
