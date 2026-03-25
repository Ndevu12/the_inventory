# The Inventory

[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/Django-6.0-092E20.svg)](https://djangoproject.com/)
[![Wagtail 7.3](https://img.shields.io/badge/Wagtail-7.3-43B1B0.svg)](https://wagtail.org/)

An open-source inventory management system built with [Wagtail CMS](https://wagtail.org/) and [Django](https://djangoproject.com/). Manage products, stock levels, warehouses, purchases, and sales — all through Wagtail's powerful admin interface.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Web framework | Django 6.0 |
| CMS / Admin UI | Wagtail 7.3 |
| Database | SQLite (dev) / PostgreSQL (production) |
| Search | Wagtail search backend (database or Elasticsearch) |
| Containerization | Docker |

## Quick Start

**For detailed environment configuration (local, Docker, production), see the [Environment Configuration Guide](docs/ENVIRONMENT.md).**

### Prerequisites

- Python 3.12 or later
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Ndevu12/the_inventory.git
cd the_inventory
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Django’s `manage.py` and the project package live under **`src/`**. The repository root also holds `seeders/` and `tests/`; run Django from `src` so imports resolve correctly (this matches CI and Docker).

```bash
cd src
```

### 4. Run database migrations

```bash
python manage.py migrate
```

### 5. Build the search index

Enable full-text search functionality by indexing all searchable models (Products, Categories, Stock Locations):

```bash
python manage.py update_index
```

### 6. Seed the database

Seed the database with sample data for testing and development. By default, this creates a "Default" tenant and seeds all data to it:

```bash
python manage.py seed_database --clear --create-default
```

For multi-tenant setups or to seed a specific tenant, see the [Seeding Guide](docs/SEEDING_GUIDE.md).

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Start the development server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000) for the site, or [http://localhost:8000/admin/](http://localhost:8000/admin/) for the Wagtail admin.

## Docker

The image copies the full repository to `/app`, sets `PYTHONPATH=/app/src:/app`, and the entrypoint runs migrations and Gunicorn from **`/app/src`** (same layout as local `cd src`).

Build and run using Docker:

```bash
docker build -t the_inventory .
docker run -p 8000:8000 the_inventory
```

Optional **database seeding** on container start uses **environment variables** (not extra CLI arguments to gunicorn). Example:

```bash
docker run -p 8000:8000 -e AUTO_SEED_DATABASE=true -e DATABASE_URL=… the_inventory
```

For complete environment variable documentation and deployment guides (Docker, Render, K8s), see the [Environment Configuration Guide](docs/ENVIRONMENT.md). Quick reference also in `.env.example` (section **AUTO-SEED**), [seeders/README.md](seeders/README.md).

## Project Structure

```
src/
├── manage.py           # Django entry point (run commands from this directory)
├── the_inventory/      # Project configuration (settings, URLs, WSGI)
│   ├── settings/
│   ├── templates/
│   └── static/
├── api/, home/, inventory/, procurement/, reports/, sales/, search/, tenants/  # Django apps
└── locale/             # Backend translation catalogs

seeders/                # Seeding app (management commands) — repo root
tests/                  # Test suite — repo root
frontend/               # Next.js tenant UI
docs/                   # Project documentation (Architecture, Roadmap)
```

See [Architecture](docs/ARCHITECTURE.md) for the full technical design, including the Phase 1 schema and app boundaries.

## Project Docs & Meta

- [Environment Configuration Guide](docs/ENVIRONMENT.md) — Complete environment variables and setup for all deployment contexts
- [Architecture](docs/ARCHITECTURE.md) — Technical design and system overview
- [Seeding Guide](docs/SEEDING_GUIDE.md) — Quick reference for tenant-scoped database seeding
- [Seeder Documentation](seeders/README.md) — Comprehensive seeding system documentation
- [Roadmap](docs/ROADMAP.md) — Development roadmap and phases
- [Contributing Guide](CONTRIBUTING.md) — How to contribute
- [Code of Conduct](CODE_OF_CONDUCT.md) — Community guidelines
- [Changelog](CHANGELOG.md) — Release history

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

Our CI workflow runs on pushes and pull requests to `main` and `develop`, and will:

- Set `PYTHONPATH` to `<repo>/src:<repo>` (so `seeders` and `tests` import correctly)
- From **`src/`** (i.e. `working-directory: src` in the workflow):
    - Run `python manage.py check`
    - Run `python manage.py test tests`
    - Run `python manage.py makemigrations --check --dry-run`
- From the repo root: `ruff check src tests`

You can mirror that locally from the repository root: `cd src` for Django commands, then `ruff check src tests` after `cd ..` (or open a second shell). If you change code under `seeders/`, also run `ruff check seeders`. Install dev tools from `requirements-dev.txt`. See [Contributing](CONTRIBUTING.md) for a full copy-paste checklist, including `docker build`.

## License

This project is licensed under the **BSD 3-Clause License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026, Jean Paul Elisa NIYOKWIZERWA.
