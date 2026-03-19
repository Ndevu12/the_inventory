#!/bin/sh
set -xe

# Ensure environment variables are set with fallbacks
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-the_inventory.settings.production}"
export DATABASE_URL="${DATABASE_URL}"
export PORT="${PORT:-8000}"

# Debug: Print environment variables
echo "=== Environment Variables ==="
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "DATABASE_URL=$DATABASE_URL"
echo "PORT=$PORT"
echo "================================"

# Run database migrations
python manage.py migrate --noinput

# Start Gunicorn
gunicorn the_inventory.wsgi:application --bind 0.0.0.0:$PORT --workers 4
