"""Regression checks for Django .po and Next.js locale JSON (I18N-12)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from django.test import SimpleTestCase


class LocaleCatalogTests(SimpleTestCase):
    def test_django_po_files_compile(self) -> None:
        if shutil.which("msgfmt") is None:
            self.skipTest("msgfmt is not installed in this environment")
        repo_root = Path(__file__).resolve().parent.parent
        for lang in ("fr", "sw", "rw", "es", "ar"):
            po = repo_root / "src" / "locale" / lang / "LC_MESSAGES" / "django.po"
            self.assertTrue(
                po.is_file(),
                f"Missing {po}",
            )
            proc = subprocess.run(
                ["msgfmt", "-c", "-o", os.devnull, str(po)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"msgfmt failed for {po}: {proc.stderr}",
            )

    def test_frontend_locale_json_structure_matches(self) -> None:
        root = Path(__file__).resolve().parent.parent / "frontend" / "public" / "locales"
        codes = ("en", "fr", "sw", "rw", "es", "ar")
        loaded: dict[str, object] = {}
        for code in codes:
            path = root / f"{code}.json"
            self.assertTrue(path.is_file(), f"Missing {path}")
            loaded[code] = json.loads(path.read_text(encoding="utf-8"))

        def keys(obj: object, prefix: str = "") -> set[str]:
            if not isinstance(obj, dict):
                return {prefix} if prefix else set()
            out: set[str] = set()
            for k, v in obj.items():
                p = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    out |= keys(v, p)
                else:
                    out.add(p)
            return out

        base = keys(loaded["en"])
        for code in codes[1:]:
            self.assertEqual(
                keys(loaded[code]),
                base,
                f"Locale {code}.json keys must match en.json",
            )
