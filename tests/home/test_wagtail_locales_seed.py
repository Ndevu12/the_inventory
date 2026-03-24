"""I18N-13: Wagtail Locale rows and content language settings."""

from django.test import TestCase, override_settings

from wagtail.coreutils import get_content_languages, get_supported_content_language_variant
from wagtail.models import Locale


class WagtailLocalesSeedTests(TestCase):
    def test_supported_locales_exist_after_migrations(self):
        codes = set(Locale.objects.values_list("language_code", flat=True))
        self.assertGreaterEqual(codes, {"en", "fr", "sw", "rw", "es", "ar"})

    def test_english_matches_language_code_default(self):
        en = Locale.objects.get(language_code="en")
        self.assertTrue(en.is_default)

    def test_wagtail_content_languages_order_matches_settings(self):
        langs = get_content_languages()
        self.assertEqual(
            list(langs.keys()),
            ["en", "fr", "sw", "rw", "es", "ar"],
        )

    def test_supported_variant_for_each_content_language(self):
        for code in ("en", "fr", "sw", "rw", "es", "ar"):
            with self.subTest(code=code):
                self.assertEqual(get_supported_content_language_variant(code), code)

    @override_settings(LANGUAGE_CODE="fr")
    def test_default_locale_follows_language_code(self):
        fr = Locale.objects.get(language_code="fr")
        self.assertTrue(fr.is_default)
