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

Build and run using Docker:

```bash
docker build -t the_inventory .
docker run -p 8000:8000 the_inventory
```

Optional **database seeding** on container start uses **environment variables** (not extra CLI arguments to gunicorn). Example:

```bash
docker run -p 8000:8000 -e AUTO_SEED_DATABASE=true -e DATABASE_URL=… the_inventory
```

On **Render**, add the same keys under the service **Environment** tab. Details: `.env.example` (section **AUTO-SEED**), [Architecture — Docker](docs/ARCHITECTURE.md#docker), [seeders/README.md](seeders/README.md).

## Project Structure

```
the_inventory/          # Project configuration (settings, URLs, WSGI)
├── settings/
│   ├── base.py         # Shared settings
│   ├── dev.py          # Development overrides (DEBUG=True)
│   └── production.py   # Production overrides
├── templates/          # Project-level templates (base, 404, 500)
└── static/             # Project-level static files

home/                   # Landing / home page app
search/                 # Site-wide search app
inventory/              # [Phase 1] Core inventory (products, stock, movements)
docs/                   # Project documentation (Architecture, Roadmap)
```

See [Architecture](docs/ARCHITECTURE.md) for the full technical design, including the Phase 1 schema and future apps (`procurement/`, `sales/`, `reports/`, `api/`).

## Project Docs & Meta

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

Our CI workflow runs on pushes and pull requests to `main`, and will:

- Run `python manage.py check`
- Run `python manage.py test`
- Run `python manage.py makemigrations --check --dry-run`
- Run `ruff check .`

You can run the same commands locally using the instructions in `CONTRIBUTING.md` (including installing dev dependencies from `requirements-dev.txt`).

## License

This project is licensed under the **BSD 3-Clause License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026, Jean Paul Elisa NIYOKWIZERWA.
