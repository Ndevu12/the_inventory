"""Celery application factory for the_inventory.

Loads Django settings and auto-discovers ``tasks.py`` modules in every
installed app.  Celery Beat is configured with a default periodic task
that expires stale reservations every hour.

Start a worker::

    celery -A the_inventory worker --loglevel=info

Start the beat scheduler::

    celery -A the_inventory beat --loglevel=info
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "the_inventory.settings.dev")

app = Celery("the_inventory")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-stale-reservations": {
        "task": "inventory.tasks.expire_reservations",
        "schedule": crontab(minute=0),  # every hour
    },
}
