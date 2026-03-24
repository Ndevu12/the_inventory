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

4. **Run Django commands from `src/`** (where `manage.py` lives). The repo root holds `seeders/` and `tests/`; loading `the_inventory` adjusts `sys.path` so `INSTALLED_APPS` and the test suite resolve. From the repository root:

   ```bash
   cd src
   ```

5. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (for accessing the Wagtail admin):

   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

   The project uses a split settings pattern. `manage.py` defaults to `the_inventory.settings.dev`, which enables `DEBUG=True` and uses SQLite. You do not need to configure anything extra for local development.

### Environment Configuration

The project supports flexible environment configuration for different setups:

| Context | Configuration | Details |
|---------|---------------|---------|
| **Local Development** | Default (dev settings) | No `.env` needed; SQLite, DEBUG=True, localhost CORS |
| **Local with `.env`** | `.env` at **repository root** (optional) | Backend loads it via settings; copy from `.env.example` as needed |
| **Docker/Containers** | Platform environment variables | Set via Render, Docker Compose, K8s, etc. |
| **Frontend (Next.js)** | `.env.local` in `frontend/` | Must have `NEXT_PUBLIC_API_URL` pointing to backend |

**Key differences:**
- Backend loads environment variables from: OS env → `.env` file → code defaults
- Frontend `NEXT_PUBLIC_*` variables must be set at build time (or via hosting platform)
- `.env` and `.env.local` files are in `.gitignore` — never committed to git

For complete setup instructions, environment variables reference, and troubleshooting, see [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).

## Project Layout

```
src/
├── manage.py
├── the_inventory/      # Project config (settings, URLs, WSGI)
│   └── settings/       # base, dev, production
├── api/, home/, inventory/, procurement/, reports/, sales/, search/, tenants/
└── locale/

seeders/                # Django app + seeding commands (repo root)
tests/                  # Django / pytest-style tests (repo root)
frontend/               # Next.js app
docs/                   # Documentation (Roadmap, Architecture)
```

New Django apps live under **`src/`** next to the other apps. The **`seeders`** package stays at the repository root by design.

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

From **`src/`** (after `cd src`):

```bash
python manage.py test tests
python manage.py check
python manage.py makemigrations --check --dry-run
```

The test suite lives in the top-level **`tests`** package (repo root), not inside an installed app, so pass the **`tests`** label (or a dotted path such as `tests.api`) so Django discovers `TestCase` modules.

**Ruff** is run from the **repository root** so paths match CI:

```bash
cd ..   # if you are still inside src/
ruff check src tests seeders
```

CI sets `PYTHONPATH=<workspace>/src:<workspace>` and uses `working-directory: src` for Django steps. Locally, `cd src && python manage.py …` is enough because importing `the_inventory` adds the repo root and `src` to `sys.path`.

When adding new features, **include tests** under the top-level **`tests/`** package (mirroring the app or domain you are changing).

### Docker

From the repository root, build the image to confirm the Dockerfile and entrypoint (migrate + Gunicorn from `src/`) still work:

```bash
docker build -t the_inventory .
```

See [README — Docker](README.md#docker) for `docker run` examples and environment variables.

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

- [ ] Tests pass (`cd src && python manage.py test tests`)
- [ ] No missing migrations (`cd src && python manage.py makemigrations --check --dry-run`)
- [ ] `cd src && python manage.py check` reports no issues
- [ ] Ruff clean from repo root (`ruff check src tests seeders`)
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
