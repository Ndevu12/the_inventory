# Contributing to The Inventory

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Project Layout](#project-layout)
- [Branching Strategy](#branching-strategy)
- [Coding Standards](#coding-standards)
- [Running Tests & Checks](#running-tests--checks)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

## Prerequisites

- **Python 3.12+**
- **Git**
- A GitHub account

## Local Development Setup

1. **Fork & clone** the repository:

   ```bash
   git clone https://github.com/<your-username>/the_inventory.git
   cd the_inventory
   ```

2. **Create a virtual environment** and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Ruff and other dev tools
   ```

4. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for accessing the Wagtail admin):

   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

   The project uses a split settings pattern. `manage.py` defaults to `the_inventory.settings.dev`, which enables `DEBUG=True` and uses SQLite. You do not need to configure anything extra for local development.

## Project Layout

```
the_inventory/          # Project config (settings, URLs, WSGI)
├── settings/
│   ├── base.py         # Shared settings (all environments)
│   ├── dev.py          # Development (DEBUG=True, SQLite)
│   └── production.py   # Production (ManifestStaticFilesStorage)
home/                   # Home page app
search/                 # Site-wide search
docs/                   # Documentation (Roadmap, Architecture)
```

New feature apps (e.g. `inventory/`, `procurement/`) are created at the project root alongside `home/` and `search/`.

## Branching Strategy

- **`main`** is the stable default branch.
- Create a **feature branch** from `main` for your work:
  ```bash
  git checkout -b feature/your-feature-name
  ```
- Use descriptive branch names: `feature/stock-movements`, `fix/low-stock-alert`, `docs/update-readme`.
- All changes reach `main` through a **Pull Request** — direct pushes to `main` are not allowed.

## Coding Standards

- Follow **[PEP 8](https://peps.python.org/pep-0008/)** for Python code.
- Use **double quotes** for strings (consistent with the existing codebase and Wagtail conventions).
- Model names: singular `PascalCase` (e.g. `StockMovement`, not `StockMovements`).
- App names: lowercase, short, descriptive (e.g. `inventory`, `procurement`).
- Keep imports organized: stdlib → third-party → Django → Wagtail → local apps.
- Write **docstrings** for models, views, and non-trivial functions.

## Running Tests & Checks

```bash
python manage.py test
```

Before submitting a PR, also verify:

```bash
# Django system checks
python manage.py check

# Ensure no missing migrations
python manage.py makemigrations --check --dry-run

# Ruff linting (matches CI)
ruff check .
```

When adding new features, **include tests**. Place them in `<app>/tests.py` or `<app>/tests/` for larger test suites.

## Submitting a Pull Request

1. Ensure your branch is up to date with `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. Verify all checks pass (tests, migrations, `manage.py check`).

3. Push your branch and open a PR against `main`.

4. Fill out the **PR template** — it will guide you through describing your changes.

### PR Checklist

- [ ] Tests pass (`python manage.py test`)
- [ ] No missing migrations (`python manage.py makemigrations --check --dry-run`)
- [ ] `python manage.py check` reports no issues
- [ ] New features include tests
- [ ] New models include migrations
- [ ] Documentation updated if needed

## Reporting Issues

- Use the [Bug Report](https://github.com/Ndevu12/the_inventory/issues/new?template=bug_report.md) template for bugs.
- Use the [Feature Request](https://github.com/Ndevu12/the_inventory/issues/new?template=feature_request.md) template for ideas.
- Search existing issues before opening a new one to avoid duplicates.

## Related Documentation

- High-level technical overview: see [Architecture](docs/ARCHITECTURE.md).
- Roadmap and planned phases: see [Roadmap](docs/ROADMAP.md).
- Release history and notable changes: see [Changelog](CHANGELOG.md).

## Questions?

Open a [Discussion](https://github.com/Ndevu12/the_inventory/discussions) or an issue — we're happy to help.
