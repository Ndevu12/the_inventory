# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.12-slim-bookworm

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000 10000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install the project requirements (includes gunicorn).
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user. This Wagtail project
# uses SQLite, the folder needs to be owned by the user that
# will be writing to the database file.
RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container (includes entrypoint.sh).
COPY --chown=wagtail:wagtail . .
RUN chmod +x /app/entrypoint.sh && test -x /app/entrypoint.sh

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files using the same STORAGES["staticfiles"] as production
# (ManifestStaticFilesStorage). Default manage.py uses dev settings, which
# skips the manifest; runtime then raises "Missing staticfiles manifest entry".
RUN DJANGO_SETTINGS_MODULE=the_inventory.settings.production \
    SECRET_KEY=collectstatic-build-only-not-used-at-runtime \
    python manage.py collectstatic --noinput --clear

# Runtime command that executes when "docker run" is called.
# entrypoint.sh: migrate → optional seed (env AUTO_SEED_DATABASE / SEED_*) → gunicorn.
# Seed vars are OS env vars (Render Environment, docker -e, compose env_file), not CLI flags.
# See .env.example section "AUTO-SEED".
ENTRYPOINT ["/app/entrypoint.sh"]
