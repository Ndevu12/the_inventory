#!/bin/bash
set -e

# Django lives in src/ (repo root is parent of this script in Docker: /app).
APP_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$APP_ROOT/src" || exit 1

# Ensure environment variables are set with fallbacks
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-the_inventory.settings.production}"
export DATABASE_URL="${DATABASE_URL}"
export PORT="${PORT:-8000}"

# Validate critical environment variables
_validate_env() {
  local var=$1
  local is_required=$2
  local value="${!var}"
  
  if [ -z "$value" ]; then
    if [ "$is_required" = "true" ]; then
      echo "ERROR: Required environment variable '$var' is not set"
      exit 1
    else
      echo "WARNING: Optional environment variable '$var' is not set"
    fi
  fi
}

# Log safe startup context without leaking credentials.
echo "=== Startup Environment Status ==="

# Validate required variables (fail if missing)
_validate_env "SECRET_KEY" "true"
_validate_env "ALLOWED_HOSTS" "true"
_validate_env "DATABASE_URL" "true"

# Validate recommended variables (warn but don't fail)
_validate_env "CORS_ALLOWED_ORIGINS" "false"
_validate_env "FRONTEND_URL" "false"
_validate_env "CSRF_TRUSTED_ORIGINS" "false"

echo "DJANGO_SETTINGS_MODULE loaded"
if [ -n "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL loaded"
else
  echo "DATABASE_URL missing"
fi
if [ -n "${PORT:-}" ]; then
  echo "PORT loaded"
else
  echo "PORT missing (will use default)"
fi
if [ -n "${AUTO_SEED_DATABASE:-}" ]; then
  echo "AUTO_SEED_DATABASE loaded"
else
  echo "AUTO_SEED_DATABASE not set"
fi
echo "=================================="

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
# Configuration tuned for production:
#   --workers ${GUNICORN_WORKERS:-4}: Configurable worker count with default 4
#   --worker-class sync: Synchronous workers (suitable for I/O-bound Django)
#   --max-requests 1000: Recycle workers every 1000 requests to prevent memory leaks
#   --max-requests-jitter 100: Stagger worker recycling to avoid simultaneous restarts
#   --timeout 60: Request timeout (increased from default 30s for longer operations)
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
exec gunicorn the_inventory.wsgi:application \
  --bind "[::]:$PORT" \
  --workers "$GUNICORN_WORKERS" \
  --worker-class sync \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output
