"""Write ``frontend/src/i18n/locales-config.json`` from Wagtail Locale rows."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import get_language_info
from wagtail.models import Locale

from home.i18n_sync import wagtail_locale_display_name


class Command(BaseCommand):
    help = (
        "Export Wagtail locales to the Next.js config file. "
        "Run after changing locales in Wagtail admin, then rebuild the frontend."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=None,
            help=(
                "Output path (default: <REPO_ROOT>/frontend/src/i18n/locales-config.json)"
            ),
        )

    def handle(self, *args, **options):
        repo_root = Path(settings.REPO_ROOT)
        out = (
            Path(options["output"])
            if options["output"]
            else repo_root / "frontend" / "src" / "i18n" / "locales-config.json"
        )

        try:
            default = Locale.get_default().language_code
        except Exception:
            default = settings.LANGUAGE_CODE or "en"

        locales = []
        for loc in Locale.objects.order_by("language_code"):
            try:
                info = get_language_info(loc.language_code)
                is_rtl = bool(info.get("bidi"))
            except Exception:
                is_rtl = False
            locales.append(
                {
                    "code": loc.language_code,
                    "displayName": wagtail_locale_display_name(loc),
                    "isRtl": is_rtl,
                    "isDefault": bool(loc.is_default),
                }
            )

        payload = {"defaultLocale": default, "locales": locales}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"Wrote {out} ({len(locales)} locales)"))
