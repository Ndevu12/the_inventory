"""Django ``LocaleMiddleware`` activates language from the locale cookie (I18N-15)."""

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.middleware.locale import LocaleMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.utils import translation


def _noop_get_response(request):
    return HttpResponse("ok")


def _lang_echo_get_response(request):
    return HttpResponse(translation.get_language() or "")


@override_settings(
    LANGUAGE_CODE="en",
    LANGUAGES=[("en", "English"), ("fr", "French")],
    LOCALE_PATHS=settings.LOCALE_PATHS,
)
class LocaleMiddlewareCookieTests(TestCase):
    """``django_language`` cookie is honored once session middleware has run."""

    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        translation.deactivate()

    def test_cookie_django_language_fr(self):
        request = self.factory.get("/api/v1/products/")
        request.COOKIES["django_language"] = "fr"

        session_mw = SessionMiddleware(_noop_get_response)
        session_mw.process_request(request)
        request.session.save()

        locale_mw = LocaleMiddleware(_lang_echo_get_response)
        response = locale_mw(request)
        self.assertEqual(response.content.decode(), "fr")

    def test_no_cookie_falls_back_to_language_code(self):
        request = self.factory.get("/api/v1/products/")

        session_mw = SessionMiddleware(_noop_get_response)
        session_mw.process_request(request)
        request.session.save()

        locale_mw = LocaleMiddleware(_lang_echo_get_response)
        response = locale_mw(request)
        self.assertEqual(response.content.decode(), "en")
