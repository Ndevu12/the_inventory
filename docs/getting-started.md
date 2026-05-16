# Getting Started

Welcome to **The Inventory** — an open-source REST API for inventory management built with Django and Wagtail.

This guide will help you install and run the backend API locally in about 10 minutes.

## Prerequisites

Before you start, make sure you have:

- **Python 3.12 or later** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Download Git](https://git-scm.com/)
- **pip** — Usually comes with Python
- **A terminal/command prompt**

### Verify Prerequisites

```bash
python --version      # Should show Python 3.12+
git --version         # Should show git version
pip --version         # Should show pip version
```

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Ndevu12/the_inventory.git
cd the_inventory
```

### 2. Create a Virtual Environment

A virtual environment isolates project dependencies from your system Python.

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Django, Wagtail, Django REST Framework, and all other required packages.

### 4. Navigate to Backend Directory

```bash
cd src
```

All Django commands must be run from this directory.

### 5. Run Database Migrations

```bash
python manage.py migrate
```

This creates the SQLite database and sets up all tables.

### 6. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account:
- **Username:** (choose a username)
- **Email:** (your email)
- **Password:** (choose a strong password)

### 7. (Optional) Seed Sample Data

To populate the database with sample data for testing:

```bash
python manage.py seed_database --clear --create-default
```

This creates:
- A default tenant organization
- Sample products, categories, and stock locations
- Sample users and test data

### 8. Start the Development Server

```bash
python manage.py runserver
```

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## Verify Installation

### Access the Admin Interface

Open your browser and visit:
- **Wagtail Admin:** http://localhost:8000/admin/
- **API Root:** http://localhost:8000/api/v1/
- **API Documentation:** http://localhost:8000/api/schema/swagger/

### Login to Admin

Use the superuser credentials you created in step 6.

### Test the API

Try this in your terminal:

```bash
curl http://localhost:8000/api/v1/
```

You should see a JSON response with available API endpoints.

---

## Next Steps

### For API Users
- Read the [API Documentation](api.md) for comprehensive endpoint reference
- Check [Integration Guide](integration.md) if you're building a frontend

### For Deployers
- See [Deployment Guide](deployment.md) for production setup
- Check [Environment Variables](environment.md) for configuration options

### For Contributors
- Read [Development Guide](development.md) to set up for contributing
- See [Contributing Guide](../CONTRIBUTING.md) for workflow

### For Operators
- See [Operations Guide](operations.md) for platform management
- Check [Troubleshooting Guide](troubleshooting.md) for common issues

---

## Troubleshooting

### Python Version Error
```
Error: Python 3.12+ required
```
**Solution:** Install Python 3.12 or later from [python.org](https://www.python.org/downloads/)

### Port Already in Use
```
Error: Address already in use
```
**Solution:** The default port 8000 is in use. Run on a different port:
```bash
python manage.py runserver 8001
```

### Database Migration Error
```
Error: No such table
```
**Solution:** Run migrations again:
```bash
python manage.py migrate
```

### Permission Denied (macOS/Linux)
```
Error: Permission denied
```
**Solution:** Make sure your virtual environment is activated:
```bash
source venv/bin/activate
```

### More Issues?
See the [Troubleshooting Guide](troubleshooting.md) for more help.

---

## What's Next?

- **Explore the API:** Visit http://localhost:8000/api/schema/swagger/ to browse all endpoints
- **Read the Docs:** Check out the [API Documentation](api.md)
- **Integrate a Frontend:** See [Integration Guide](integration.md)
- **Deploy to Production:** Follow [Deployment Guide](deployment.md)

---

## Need Help?

- 📖 Check the [FAQ](faq.md)
- 🐛 See [Troubleshooting Guide](troubleshooting.md)
- 💬 Open an [Issue on GitHub](https://github.com/Ndevu12/the_inventory/issues)
- 📚 Read the [Architecture Guide](architecture.md) for technical details

Happy coding! 🚀
