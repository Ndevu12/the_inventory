"""Shared API registry plugins use to contribute routes.

Core endpoints stay hard-wired in ``api/urls.py``; this registry is the seam
that lets *plugins* add endpoints without editing that file.  A plugin populates
the registry from its ``api_register.py`` module (auto-discovered at startup),
and ``api/urls.py`` calls :meth:`APIRegistry.apply` / :meth:`get_url_patterns`
to fold those contributions into the live URLconf.

Two contribution shapes are supported:

* **ViewSets** — registered onto the DRF router under ``/api/v1/`` (tenant
  scope) or ``/api/v1/platform/`` (platform scope), mirroring the two routers
  already used by the core API.
* **Routes** — ready-made ``django.urls.path``/``re_path`` objects for plain
  ``APIView`` style endpoints, mounted directly under ``/api/v1/``.

Prefixes/names are checked for collisions so a misbehaving plugin fails loudly
at startup instead of silently shadowing another route.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import ImproperlyConfigured

TENANT_SCOPE = "tenant"
PLATFORM_SCOPE = "platform"
_SCOPES = {TENANT_SCOPE, PLATFORM_SCOPE}


@dataclass(frozen=True)
class ViewSetEntry:
    prefix: str
    viewset: Any
    basename: str
    scope: str
    source: str | None = None


@dataclass(frozen=True)
class RouteEntry:
    route: Any  # URLPattern / URLResolver
    source: str | None = None


@dataclass
class APIRegistry:
    """Collects plugin API contributions; consumed by ``api/urls.py``."""

    _viewsets: list[ViewSetEntry] = field(default_factory=list)
    _routes: list[RouteEntry] = field(default_factory=list)
    # (scope, prefix) -> source, used for collision detection.
    _taken_prefixes: dict[tuple[str, str], str | None] = field(default_factory=dict)

    # -- registration ----------------------------------------------------

    def register_viewset(
        self,
        prefix: str,
        viewset: Any,
        *,
        basename: str | None = None,
        scope: str = TENANT_SCOPE,
        source: str | None = None,
    ) -> None:
        """Register a DRF ViewSet under ``prefix`` for the given scope.

        ``basename`` defaults to a slug derived from ``prefix`` when the
        ViewSet has no ``queryset`` for DRF to infer one from.
        """
        if scope not in _SCOPES:
            raise ImproperlyConfigured(
                f"Plugin viewset {prefix!r} has unknown scope {scope!r}; "
                f"expected one of {sorted(_SCOPES)}."
            )
        prefix = prefix.strip("/")
        if not prefix:
            raise ImproperlyConfigured("Plugin viewset prefix must be non-empty.")
        key = (scope, prefix)
        if key in self._taken_prefixes:
            owner = self._taken_prefixes[key] or "another plugin"
            raise ImproperlyConfigured(
                f"Plugin route conflict: prefix {prefix!r} ({scope} scope) is "
                f"already registered by {owner}."
            )
        self._taken_prefixes[key] = source
        self._viewsets.append(
            ViewSetEntry(
                prefix=prefix,
                viewset=viewset,
                basename=basename or prefix.replace("/", "-"),
                scope=scope,
                source=source,
            )
        )

    def register_route(self, route: Any, *, source: str | None = None) -> None:
        """Register a ready-made ``path()``/``re_path()`` under ``/api/v1/``."""
        self._routes.append(RouteEntry(route=route, source=source))

    # -- consumption (called from api/urls.py) ---------------------------

    def apply(self, router: Any, platform_router: Any) -> None:
        """Register collected ViewSets onto the supplied DRF routers."""
        for entry in self._viewsets:
            target = router if entry.scope == TENANT_SCOPE else platform_router
            target.register(entry.prefix, entry.viewset, basename=entry.basename)

    def get_url_patterns(self) -> list[Any]:
        """Return the plain route patterns to splice into ``urlpatterns``."""
        return [entry.route for entry in self._routes]

    # -- introspection / testing ----------------------------------------

    def contributions(self) -> dict[str, list[dict[str, Any]]]:
        """A serialisable summary of everything registered, for diagnostics."""
        return {
            "viewsets": [
                {
                    "prefix": e.prefix,
                    "scope": e.scope,
                    "basename": e.basename,
                    "source": e.source,
                }
                for e in self._viewsets
            ],
            "routes": [
                {"pattern": str(getattr(e.route, "pattern", e.route)), "source": e.source}
                for e in self._routes
            ],
        }

    def reset(self) -> None:
        """Clear all registrations. Primarily for tests."""
        self._viewsets.clear()
        self._routes.clear()
        self._taken_prefixes.clear()


# Process-wide singleton shared by every plugin's ``api_register`` module.
registry = APIRegistry()
