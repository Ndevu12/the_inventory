#!/bin/sh
set -xe

# Django lives in src/ (repo root is parent of this script in Docker: /app).
APP_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$APP_ROOT/src" || exit 1

# Ensure environment variables are set with fallbacks
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-the_inventory.settings.production}"
export DATABASE_URL="${DATABASE_URL}"
export PORT="${PORT:-8000}"

# Debug: Print environment variables
echo "=== Environment Variables ==="
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "DATABASE_URL=$DATABASE_URL"
echo "PORT=$PORT"
echo "AUTO_SEED_DATABASE=${AUTO_SEED_DATABASE:-}"
echo "================================"

# Run database migrations
python manage.py migrate --noinput

# Optional: seed sample data when AUTO_SEED_DATABASE is truthy (1, true, yes, on)
_auto_seed=$(printf '%s' "${AUTO_SEED_DATABASE:-}" | tr '[:upper:]' '[:lower:]')
case "$_auto_seed" in
  1|true|yes|on)
    echo "=== AUTO_SEED_DATABASE enabled: running seed_database ==="
    if [ -n "${SEED_TENANT:-}" ]; then
      SEED_ARGS="--tenant=${SEED_TENANT}"
    else
      SEED_ARGS="--create-default"
    fi
    if [ -n "${SEED_MODELS:-}" ]; then
      SEED_ARGS="$SEED_ARGS --models=${SEED_MODELS}"
    fi
    _seed_clear=$(printf '%s' "${SEED_CLEAR:-}" | tr '[:upper:]' '[:lower:]')
    case "$_seed_clear" in
      1|true|yes|on) SEED_ARGS="$SEED_ARGS --clear" ;;
    esac
    _seed_quiet=$(printf '%s' "${SEED_QUIET:-}" | tr '[:upper:]' '[:lower:]')
    case "$_seed_quiet" in
      1|true|yes|on) SEED_ARGS="$SEED_ARGS --quiet" ;;
    esac
    python manage.py seed_database $SEED_ARGS
    echo "=== seed_database finished ==="
    ;;
esac

# Start Gunicorn (access + error logs to stdout/stderr for platform log drains)
exec gunicorn the_inventory.wsgi:application \
  --bind "0.0.0.0:$PORT" \
  --workers 4 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output
