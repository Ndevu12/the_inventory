import sys
from pathlib import Path

# Repo root holds ``seeders`` and ``tests``; ``src/`` holds Django apps. When
# ``manage.py`` or Gunicorn run with cwd ``src/``, only ``src`` is on ``sys.path``
# by default — add both roots so ``seeders`` and ``tests`` import correctly.
_src_dir = Path(__file__).resolve().parent.parent
_repo_root = _src_dir.parent
for _path in (_repo_root, _src_dir):
    _s = str(_path)
    try:
        sys.path.remove(_s)
    except ValueError:
        pass
    sys.path.insert(0, _s)

from .celery import app as celery_app

__all__ = ("celery_app",)
