# Project Tasks

> Tasks are designed for parallel execution unless explicitly noted in the **Depends On** column.
> All tasks are part of the **Internationalization & Localization Initiative** to enable multi-language support across the platform using wagtail-localize.

---

## Internationalization & Localization Tasks (I18N-*)

Implementing comprehensive multi-language support using **Wagtail’s built-in i18n** and **wagtail-localize**, with per-tenant language selection (English, French, Swahili, Kinyarwanda, Spanish). **Do not** add custom translation models or manual columns such as `name_fr` / `name_en`—use **linked instances per locale** (Wagtail’s model), which wagtail-localize manages.

### Mental model: API-first tenants, Wagtail-shaped storage

**Who uses what**

| Actor | Primary surface | Role in i18n |
| ----- | --------------- | ------------ |
| **Tenant companies** (inventory operators) | [frontend](../frontend/) (Next.js) + **DRF** at `/api/v1/` | Create, update, and read catalog data—including **localized** content—via the API and UI strings via **next-intl** |
| **Platform / staff** | Wagtail admin (`/admin/`) | Tenant management, reports, imports, dashboards; optional **read-heavy or support** access to inventory data if models are registered as snippets |

Inventory listing menus for products/categories were removed from Wagtail in the SaaS redesign ([inventory/wagtail_hooks.py](../inventory/wagtail_hooks.py)). **That is not permanent policy:** registering inventory-related models as **tenant-scoped** snippets (e.g. via `TenantScopedSnippetViewSet` in [tenants/snippets.py](../tenants/snippets.py)) is a reasonable change when you want **monitoring, support, or admin-level inspection** in Wagtail. **What stays fixed by design** is that **tenant operators** run day-to-day inventory work through the **Next.js app and DRF**, not through Wagtail as their main UI.

**What to build (storage vs authoring)**

1. **Storage — what and why:** Add `TranslatableMixin` to Product, Category, Supplier, Customer and use **wagtail-localize** so each locale is a **linked row** in Wagtail’s translation graph. **Why:** avoids hand-maintained columns such as `name_fr` / `name_en`, keeps one schema, and lets localize manage relationships between locale variants.
2. **Read path for tenants — how:** **I18N-10** / **I18N-11**—resolve `?language=`, `Accept-Language`, and tenant default in viewsets/serializers so API responses return the correct localized instance or field values.
3. **Write path for tenants — how:** **I18N-16**—DRF create/update must drive the same linked-locale data (programmatic localize APIs). **I18N-06** configures **which model fields** localize treats as translated vs synchronized; normal **`FieldPanel`** in admin is enough—there is **no** `TranslatableFieldPanel` in wagtail-localize 1.x. Staff **Translate** flows in Wagtail apply when models are exposed there; **I18N-06** does **not** replace **I18N-16** for tenant operators.

```text
Tenant UI (Next.js)  ──HTTP──►  DRF API  ──►  TranslatableMixin models + wagtail-localize
                                     │
                                     └──►  Wagtail admin (optional): snippets for staff / monitoring — not the primary operator surface
```

---

### I18N-01 — Install Dependencies & Configure Package Management

**Priority:** CRITICAL | **Depends On:** None | **Parallel:** No (blocking)

**Problem:**
wagtail-localize and next-intl are not installed. Must be added to dependencies before proceeding with implementation.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Backend dependencies | Add wagtail-localize[makemigrations] to requirements |
| Frontend dependencies | Add next-intl to frontend package.json |
| Verify installation | Test that modules import correctly |

**Acceptance Criteria:**

- [ ] `requirements.txt` updated with `wagtail-localize[polib]>=1.0.0`
- [ ] `frontend/package.json` updated with `next-intl@latest`
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `cd frontend && yarn install` completes without errors
- [ ] `python -c "import wagtail_localize"` succeeds
- [ ] Verify in Django shell: `from wagtail_localize.models import Locale` works
- [ ] Tested: Both backend and frontend packages are available

**Files to Modify:**
- `requirements.txt` — Add wagtail-localize dependency
- `frontend/package.json` — Add next-intl dependency

**Implementation Notes:**
- Use `wagtail-localize[polib]` for full translation support with .po files
- Ensure Node.js and Yarn are available for frontend installation
- Pin versions: `wagtail-localize>=1.0.0`, `next-intl@^3.0.0` (or latest compatible)

---

### I18N-02 — Configure Django & Wagtail i18n Settings

**Priority:** CRITICAL | **Depends On:** I18N-01 | **Parallel:** No (blocks I18N-03 through I18N-05)

**Problem:**
Django's i18n framework and Wagtail's localization features are not configured. Settings need to enable multi-language support for all subsequent features.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Language configuration | Define supported languages (EN, FR, SW, RW, ES) |
| Enable Wagtail i18n | Set WAGTAIL_I18N_ENABLED flag |
| Middleware setup | Add LocaleMiddleware to request processing |
| Locale paths | Configure where .po translation files are stored |

**Acceptance Criteria:**

- [ ] `the_inventory/settings/base.py` updated
- [ ] `USE_I18N = True` (already set, verify present)
- [ ] `LANGUAGES` list added: `[('en', 'English'), ('fr', 'Français'), ('sw', 'Swahili'), ('rw', 'Kinyarwanda'), ('es', 'Español')]`
- [ ] `LANGUAGE_CODE = 'en'` configured
- [ ] `WAGTAIL_I18N_ENABLED = True` set
- [ ] `LOCALE_PATHS` configured (e.g., `[os.path.join(BASE_DIR, 'locale')]`)
- [ ] `LocaleMiddleware` added to `MIDDLEWARE` (after `SessionMiddleware`, before template processing)
- [ ] `django.middleware.locale.LocaleMiddleware` in MIDDLEWARE list
- [ ] Run `python manage.py migrate` to create locale database tables
- [ ] Wagtail admin "Settings → Locales" page loads
- [ ] Tested: Django i18n framework is functional

**Files to Modify:**
- `the_inventory/settings/base.py` — Add language settings, middleware, WAGTAIL_I18N_ENABLED

**Implementation Notes:**
- LocaleMiddleware position matters: after SessionMiddleware, before cache middleware if present
- Ensure `os.path` is imported: `import os`
- LOCALE_PATHS must be an absolute list of directories for .po files
- After saving settings, run `python manage.py migrate wagtail_localize` to create Locale model tables

---

### I18N-03 — Add TranslatableMixin to Product & Category Models

**Priority:** HIGH | **Depends On:** I18N-01, I18N-02 | **Parallel:** Yes (parallel to I18N-04, I18N-05)

**Problem:**
Product and Category models contain translatable fields (name, description) but don't inherit from `TranslatableMixin`. wagtail-localize cannot manage translations without this mixin.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add mixin inheritance | Add `TranslatableMixin` to model class definitions |
| Translatable fields | Keep translatable content on normal model fields (e.g. `CharField`, `TextField`); `TranslatableMixin` + wagtail-localize discover them automatically—**I18N-06** only adds **optional** `override_translatable_fields` where defaults are wrong |
| Update migrations | Create migration to add translation tables |

**Acceptance Criteria:**

- [ ] `inventory/models/product.py` updated: Product inherits `TranslatableMixin`
- [ ] `inventory/models/category.py` updated: Category inherits `TranslatableMixin`
- [ ] TranslatableMixin added before TimeStampedModel in inheritance chain
- [ ] Import added: `from wagtail.models import TranslatableMixin` (this repo uses Wagtail 7.x)
- [ ] `python manage.py makemigrations` creates migration files
- [ ] `python manage.py migrate` applies migrations without errors
- [ ] **Do not** add `override_translatable_fields` or panel changes here—**I18N-06** owns optional field overrides for wagtail-localize
- [ ] Tested: Product and Category support **per-locale instances** (verify via API **I18N-16** and/or Wagtail when snippets exist, once **I18N-13** locales exist and **I18N-06** overrides are done if needed)
- [ ] Tested: Separate instances per locale behave as expected (admin and/or API)

**Files to Modify:**
- `inventory/models/product.py` — Add TranslatableMixin to Product
- `inventory/models/category.py` — Add TranslatableMixin to Category
- `inventory/models/__init__.py` — Ensure imports are correct (if needed)

**Implementation Notes:**
- Inheritance order: `class Product(TranslatableMixin, TimeStampedModel):`
- **Project standard:** `from wagtail.models import TranslatableMixin` (Wagtail 7.x in `requirements.txt`). If upgrading Wagtail later, re-check Wagtail release notes for any mixin import changes.
- No need to add individual translation fields—wagtail-localize handles this automatically
- Migration will create related translation tables (e.g., product_translation, category_translation)

---

### I18N-04 — Add TranslatableMixin to Supplier & Customer Models

**Priority:** HIGH | **Depends On:** I18N-01, I18N-02 | **Parallel:** Yes (parallel to I18N-03, I18N-05)

**Problem:**
Supplier and Customer models contain translatable fields (name, address, notes) but don't inherit from `TranslatableMixin`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add mixin inheritance | Add `TranslatableMixin` to Supplier and Customer model classes |
| Update migrations | Create migration to add translation tables for both models |

**Acceptance Criteria:**

- [ ] `procurement/models/supplier.py` updated: Supplier inherits `TranslatableMixin`
- [ ] `sales/models/customer.py` updated: Customer inherits `TranslatableMixin`
- [ ] TranslatableMixin added before TimeStampedModel in inheritance chain
- [ ] Import added to both models: `from wagtail.models import TranslatableMixin` (Wagtail 7.x)
- [ ] `python manage.py makemigrations` creates migration files for both models
- [ ] `python manage.py migrate` applies migrations without errors
- [ ] **Do not** add `override_translatable_fields` or panel changes here—**I18N-06** owns optional field overrides for wagtail-localize
- [ ] Tested: Supplier and Customer support **per-locale instances** (verify via API **I18N-16** and/or Wagtail when snippets exist, once **I18N-13** locales exist and **I18N-06** overrides are done if needed)
- [ ] Tested: Separate instances per locale behave as expected (admin and/or API)

**Files to Modify:**
- `procurement/models/supplier.py` — Add TranslatableMixin to Supplier
- `sales/models/customer.py` — Add TranslatableMixin to Customer

**Implementation Notes:**
- Same pattern as I18N-03
- Both models will generate migration files
- No manual translation field definition needed

---

### I18N-05 — Add preferred_language Field to Tenant Model

**Priority:** HIGH | **Depends On:** I18N-01, I18N-02 | **Parallel:** Yes (parallel to I18N-03, I18N-04)

**Problem:**
Tenants have no way to specify their preferred language. Each tenant should be able to select a default language independent of global settings (per-tenant localization).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add field | Add optional CharField for language preference |
| Set default | Default to 'en' (English) |
| Create migration | Backfill existing tenants with default language |

**Acceptance Criteria:**

- [ ] `tenants/models.py` updated: Tenant model adds `preferred_language` field
- [ ] Field definition: `preferred_language = models.CharField(max_length=5, default='en', choices=LANGUAGE_CHOICES)`
- [ ] LANGUAGE_CHOICES matches settings.LANGUAGES
- [ ] `python manage.py makemigrations tenants` creates migration
- [ ] `python manage.py migrate` applies migration
- [ ] Migration includes RunPython to set 'en' for all existing tenants
- [ ] Tested: Tenants can select preferred language
- [ ] Tested: Language preference is accessible in views/API

**Files to Modify:**
- `tenants/models.py` — Add preferred_language field to Tenant model

**Implementation Notes:**
- Field should allow empty (optional) initially, then make required after backfill
- Import LANGUAGES from django.conf in the migration
- Drives **Django/Wagtail request locale** via tenant middleware (see **I18N-09**) and **API default language** (see **I18N-10**). The **Next.js** app uses its own locale (URL/cookie); after authentication, consider setting the next-intl cookie (or equivalent) from `tenant.preferred_language` so storefront and tenant default stay aligned—document the chosen behavior in **I18N-07** / **I18N-08** notes.

---

### I18N-06 — wagtail-localize field behavior (no translation-specific panels)

**Priority:** MEDIUM | **Depends On:** I18N-03, I18N-04 | **Parallel:** Yes (parallel to others)

**Problem:**
Docs and older examples sometimes mention **`TranslatableFieldPanel`** or `wagtail_localize.admin` panels. **wagtail-localize 1.x does not provide that API.** Translation is driven by **model field types** and wagtail-localize’s extraction (`get_translatable_fields()`), not by swapping `FieldPanel` for a special panel.

**What to do instead**

- Keep **normal** Wagtail panels: `from wagtail.admin.panels import FieldPanel` (and your existing `TabbedInterface` / `MultiFieldPanel` layout). **No** translation-specific panel class is required.
- **Optional:** If auto-detection is wrong for a field, set **`override_translatable_fields`** on the model using `wagtail_localize.fields` (e.g. `TranslatableField`, `SynchronizedField`). Example: translate `name` / `description`, synchronize `slug` or `sku` if product rules require identical codes across locales.

**Staff and admin UI, not tenant primary:** Tenant operators use the **API** (**I18N-16**). This task only ensures **localize’s model-level rules** match product intent when staff use Wagtail. Registering snippets for monitoring remains an **architecture choice** ([tenants/snippets.py](../tenants/snippets.py)).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Verify defaults | Confirm `CharField` / `TextField` (and other localized types per docs) behave as translated; IDs/codes as synchronized if needed |
| Optional overrides | Add `override_translatable_fields` only where defaults are incorrect |
| Tenant language UI | Ensure `preferred_language` appears in Tenant admin/snippet panels (**I18N-05**) |

**Acceptance Criteria:**

- [ ] **No** use of `TranslatableFieldPanel` or `wagtail_localize.admin` panel imports (they are not part of wagtail-localize 1.x)
- [ ] `inventory/models/product.py`, `category.py`, `procurement/models/supplier.py`, `sales/models/customer.py`: panels remain standard `FieldPanel` (or existing panel wrappers); **only** add `override_translatable_fields` where reviewed and needed
- [ ] If overrides are added: `from wagtail_localize.fields import TranslatableField, SynchronizedField` (or current module path for your installed version—confirm against [wagtail-localize docs](https://www.wagtail-localize.org/))
- [ ] `tenants/models.py`: `preferred_language` exposed in relevant admin/snippet panels
- [ ] Tested: With **I18N-13** locales, translatable models show expected translate/sync behavior in Wagtail **when** those models are registered in admin, or verified via localize/unit tests if not yet in admin

**Files to Modify:**
- `inventory/models/product.py` — optional `override_translatable_fields`; panels unchanged except Tenant-related N/A
- `inventory/models/category.py` — same
- `procurement/models/supplier.py` — same
- `sales/models/customer.py` — same
- `tenants/models.py` — `preferred_language` on panels

**Implementation Notes:**
- **Mental model:** UI = `FieldPanel`; **what** gets translated = model + localize field rules (`TranslatableField` / `SynchronizedField` / defaults).
- Re-check **wagtail-localize** and **Wagtail** version release notes when upgrading; import paths and field classes can change.
- **I18N-16** remains required for tenant API authoring regardless of Wagtail registration.

---

### I18N-07 — Configure Frontend next-intl Setup

**Priority:** HIGH | **Depends On:** I18N-01 | **Parallel:** Yes (parallel to others)

**Problem:**
Frontend has no internationalization support. next-intl must be configured for multi-language Next.js app.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Configure next-intl middleware | Add locale detection and routing |
| Create i18n config | Set up language messages and routing |
| Locale-aware routing | Enable [locale] dynamic routes |

**Acceptance Criteria:**

- [ ] `frontend/next.config.ts` updated with next-intl plugin configuration
- [ ] `frontend/middleware.ts` created with locale detection logic
- [ ] `frontend/src/i18n.ts` created with language configuration
- [ ] `frontend/src` folder structure updated for locale routes: `app/[locale]/`
- [ ] `frontend/public/locales/` created with English messages as fallback
- [ ] `yarn dev` runs without errors
- [ ] Frontend loads with default language detected from browser/cookie

**Files to Create:**
- `frontend/src/i18n.ts` — next-intl configuration
- `frontend/public/locales/en.json` — English translation file (empty initially)

**Files to Modify:**
- `frontend/next.config.ts` — Add next-intl plugin
- `frontend/middleware.ts` — Add locale middleware

**Implementation Notes:**
- next-intl middleware checks Accept-Language header and cookies for locale preference
- Configure SUPPORTED_LOCALES = ['en', 'fr', 'sw', 'rw', 'es']
- Set DEFAULT_LOCALE = 'en'
- Routing structure: `/en/`, `/fr/`, `/sw/`, `/rw/`, `/es/` paths
- **Tenant vs browser:** Unauthenticated visitors get locale from browser/cookie/URL only. **Tenant `preferred_language` (I18N-05)** applies to Django admin, API defaults, and middleware-activated gettext—not automatically to the Next.js router. After login (or tenant context in the app), either sync the next-intl locale from the API/tenant profile or document that the two defaults may differ until sync is implemented.

---

### I18N-08 — Create Language Switcher UI Component

**Priority:** HIGH | **Depends On:** I18N-07 | **Parallel:** Yes (parallel to others)

**Problem:**
Users cannot switch languages. Must create language selector UI in header/navigation.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Create component | Build LanguageSwitcher React component |
| Add to layout | Place language switcher in main layout header |
| Handle routing | Switch locale and redirect to translated page |
| Persist preference | Save language choice to localStorage/cookie |

**Acceptance Criteria:**

- [ ] `frontend/src/components/LanguageSwitcher.tsx` created
- [ ] Component renders language options as dropdown or buttons
- [ ] Clicking language changes URL locale and redirects
- [ ] Current locale is highlighted/selected in UI
- [ ] Language preference persists via localStorage/cookie
- [ ] Integrated into `frontend/src/app/[locale]/layout.tsx`
- [ ] Tested: Can switch languages
- [ ] Tested: Switching updates page content (once translations added)

**Files to Create:**
- `frontend/src/components/LanguageSwitcher.tsx` — Language switcher component

**Files to Modify:**
- `frontend/src/app/[locale]/layout.tsx` — Add LanguageSwitcher to header

**Implementation Notes:**
- Use next-intl's `usePathname()` and `useRouter()` hooks
- Language preference should update cookie that backend can read
- Consider accessible dropdown: ARIA labels, keyboard navigation
- Optional: when the app knows the current tenant (e.g. after auth), initialize or update the locale cookie from `tenant.preferred_language` so the UI matches **I18N-05** without manual switching every session

---

### I18N-09 — Implement Locale Middleware for Per-Tenant Language

**Priority:** MEDIUM | **Depends On:** I18N-02, I18N-05 | **Parallel:** Yes (parallel to others)

**Problem:**
No mechanism to enforce tenant's preferred language across requests. Middleware should detect tenant and apply their language preference automatically.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Extend middleware | Update TenantMiddleware to set locale |
| Read preference | Get preferred_language from current tenant |
| Apply locale | Use Django's i18n to activate locale |

**Acceptance Criteria:**

- [ ] `tenants/middleware.py` updated
- [ ] After tenant is resolved, get `tenant.preferred_language`
- [ ] Call `translation.activate(tenant.preferred_language)` to set locale
- [ ] Falls back to LANGUAGE_CODE if tenant preference is None
- [ ] Tested: Admin entering tenant with French preference sees French UI
- [ ] Tested: Different tenants can have different language preferences

**Files to Modify:**
- `tenants/middleware.py` — Add locale activation logic to TenantMiddleware

**Implementation Notes:**
- Import: `from django.utils import translation`
- Pattern: `translation.activate(locale_code)` after tenant is set (validate against `settings.LANGUAGES` or `get_supported_language_variant` before activating)
- Ensure this runs after tenant resolution and before view logic that calls `gettext` / lazy choice labels
- **`LocaleMiddleware`** (I18N-02) resolves language from URL prefix, cookie, and `Accept-Language` per Django’s rules; it does **not** read `tenant.preferred_language`. This middleware sets the **active language for the request** from the tenant so Django admin strings and any code using the active locale see the tenant default. **Translated model content** for the API still requires explicit language handling in viewsets/serializers (**I18N-10**, **I18N-11**).

---

### I18N-10 — Add Language Parameter to API Responses

**Priority:** HIGH | **Depends On:** I18N-03, I18N-04 | **Parallel:** Yes (parallel to others)

**Problem:**
API endpoints (Product, Category, Supplier, Customer) don't support language parameter (`?language=fr`). **Tenants consume inventory through this API**—without language resolution, the frontend cannot show localized catalog data. This is the **primary read path** for translated model fields (with **I18N-11**).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add parameter support | Accept `?language=CODE` query parameter |
| Return translations | Translate content based on parameter |
| Default to tenant | Fall back to tenant's preferred language if not specified |

**Acceptance Criteria:**

- [ ] `api/views/inventory.py` viewsets updated
- [ ] `api/views/procurement.py` viewsets updated
- [ ] `api/views/sales.py` viewsets updated
- [ ] All viewsets accept optional `language` query parameter
- [ ] If language parameter provided, return translated content for that language
- [ ] If language parameter absent, use tenant's preferred_language
- [ ] If tenant has no preference, use request Accept-Language header
- [ ] Tested: `GET /api/v1/products/?language=fr` returns French translations (when available)
- [ ] Tested: `GET /api/v1/products/` uses tenant default language

**Files to Modify:**
- `api/views/inventory.py` — Add language parameter handling to viewsets
- `api/views/procurement.py` — Add language parameter handling
- `api/views/sales.py` — Add language parameter handling
- `api/pagination.py` or similar — Document language parameter in API docs

**Implementation Notes:**
- Extract parameter: `language = self.request.query_params.get('language')`
- Use Django's `translation.get_supported_language_variant(language)` to validate
- wagtail-localize Locale model can be queried to list available translations
- For a consistent combination of **translated model fields** and **gettext-based strings** (e.g. choice labels from **I18N-14**), call `translation.activate(resolved_language)` for that request (or pass explicit locale into serializers) before serialization when the resolved language differs from middleware defaults

---

### I18N-11 — Update Serializers for Language Awareness

**Priority:** HIGH | **Depends On:** I18N-03, I18N-04, I18N-10 | **Parallel:** Yes (parallel to others)

**Problem:**
Serializers (ProductSerializer, CategorySerializer, etc.) don't pass language context to models. Translations won't be returned correctly to **tenant-facing API clients**.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Pass context | Ensure language is passed to serializer context |
| Use translations | Access translated fields from models |
| Document fields | Clarify which fields are translatable in serializer |

**Acceptance Criteria:**

- [ ] `api/serializers/inventory.py` updated
- [ ] `api/serializers/procurement.py` updated
- [ ] `api/serializers/sales.py` updated
- [ ] All serializers with TranslatableMixin models updated
- [ ] In viewsets, pass language via serializer **instance** context, e.g. `MySerializer(obj, context={'request': request, 'language': resolved_language})` — not on `Meta` (Meta is class-level and has no per-request context)
- [ ] Serializers read `self.context.get('language')` (or equivalent) and return translated field values
- [ ] Tested: Serializer returns correct translation for requested language
- [ ] Documented: Docstrings note which fields are translatable

**Files to Modify:**
- `api/serializers/inventory.py` — Update Product/Category serializers
- `api/serializers/procurement.py` — Update Supplier serializer
- `api/serializers/sales.py` — Update Customer serializer
- `api/views/inventory.py` — Pass language context to serializers (coordinated with I18N-10)

**Implementation Notes:**
- Context is typically passed: `serializer = MySerializer(obj, context={'request': request, 'language': language})`
- wagtail-localize provides methods on translatable models to access translations
- May need custom `SerializerMethodField` for some translated fields

---

### I18N-16 — DRF authoring for localized catalog entities (primary write path for tenants)

**Priority:** HIGH | **Depends On:** I18N-03, I18N-04, I18N-10, I18N-11 | **Parallel:** Yes (parallel to I18N-06 and others)

**Problem:**
Tenant companies manage inventory through the **Next.js frontend** and **DRF**, not Wagtail snippet screens ([inventory/wagtail_hooks.py](../inventory/wagtail_hooks.py)). **Wagtail + I18N-06** (standard panels and optional `override_translatable_fields`) does not give operators API create/update from the tenant app. Without **I18N-16**, localized catalog rows cannot be maintained from the frontend; staff-only Wagtail translation remains possible only if models are registered there.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| API contract | Document how clients specify **locale** on create/update (e.g. header `Accept-Language`, query `?language=`, or explicit body field—pick one consistent approach per resource) |
| Write flows | POST/PATCH (or equivalent) create/update the correct **locale instance** and preserve **wagtail-localize** translation links—no `name_fr` columns |
| Service layer | Encapsulate wagtail-localize **programmatic** APIs (bootstrap translation, sync) where needed; keep viewsets thin |
| API docs | Expose new parameters or schema in drf-spectacular |

**Acceptance Criteria:**

- [ ] Documented contract for locale on **write** for Product, Category, Supplier, Customer (and nested routes if used)
- [ ] Authenticated tenant users can create **source** locale records and **translated** variants via API
- [ ] Updates target the correct localized row; tenant isolation unchanged
- [ ] Tests cover API translation **authoring** (not only `GET ?language=`)
- [ ] OpenAPI reflects the contract

**Files to Modify (expected):**
- `api/views/inventory.py`, `api/views/procurement.py`, `api/views/sales.py` — resolve language, call services
- `api/serializers/inventory.py`, `api/serializers/procurement.py`, `api/serializers/sales.py` — validate locale, create/update semantics
- New module optional: e.g. `inventory/services/localization.py` (or domain-specific helpers)—**programmatic** wagtail-localize usage

**Implementation Notes:**
- **Storage:** `TranslatableMixin` + wagtail-localize **linked instances**—one translation graph, no parallel `*_fr` columns on the same table.
- **Authoring for tenant operators:** **HTTP + DRF** (**I18N-16**). **Wagtail** (normal `FieldPanel` + **I18N-06** field overrides; snippet viewsets in [tenants/snippets.py](../tenants/snippets.py)) is for **staff** when you expose models there; it does not replace the API for companies’ routine inventory work.
- Follow current wagtail-localize documentation for creating/updating translations from Python (APIs evolve by version—avoid hard-coding outdated function names in this task doc).

---

### I18N-12 — Create & Populate Translation Files

**Priority:** MEDIUM | **Depends On:** I18N-02, I18N-07 | **Parallel:** Yes (parallel to others)

**Problem:**
No translation (.po/.json) files exist. Translation files needed for UI strings (both Django backend and frontend).

**Follow-up:** After **I18N-14** (gettext on choice labels), run `makemessages` again so new strings appear in `.po` files; the “50% translated” / compile checks below apply to the **updated** catalogs once I18N-14 is merged or repeat extraction mid-initiative.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Extract strings | Run makemessages to extract translatable strings |
| Create .po files | Generate translation files for each language |
| Populate translations | Add translations for UI strings (at least key strings) |
| Compile translations | Compile .po files to .mo for Django |

**Acceptance Criteria:**

- [ ] `python manage.py makemessages -l fr` creates locale/fr/LC_MESSAGES/django.po
- [ ] `python manage.py makemessages -l sw` creates locale/sw/LC_MESSAGES/django.po
- [ ] `python manage.py makemessages -l rw` creates locale/rw/LC_MESSAGES/django.po
- [ ] `python manage.py makemessages -l es` creates locale/es/LC_MESSAGES/django.po
- [ ] `.po` files contain auto-extracted strings from code (admin, templates, etc.)
- [ ] At least 50% of strings translated to validate workflow
- [ ] `python manage.py compilemessages` compiles .po to .mo
- [ ] Frontend translation files: `frontend/public/locales/{en,fr,sw,rw,es}.json` created with sample strings
- [ ] Tested: Django admin appears in French after switching language
- [ ] Tested: Frontend strings appear in selected language

**Files to Create:**
- `locale/fr/LC_MESSAGES/django.po` — French translations
- `locale/sw/LC_MESSAGES/django.po` — Swahili translations
- `locale/rw/LC_MESSAGES/django.po` — Kinyarwanda translations
- `locale/es/LC_MESSAGES/django.po` — Spanish translations
- `frontend/public/locales/en.json` — English frontend strings
- `frontend/public/locales/fr.json` — French frontend strings
- `frontend/public/locales/sw.json` — Swahili frontend strings
- `frontend/public/locales/rw.json` — Kinyarwanda frontend strings
- `frontend/public/locales/es.json` — Spanish frontend strings

**Implementation Notes:**
- Mark translatable strings in code with `_()` or `gettext()`
- Frontend: Use next-intl message files format (JSON)
- Initial translations can be placeholders; full translations can follow
- Document: How to add translations for new strings
- **Ordering:** First pass can run in parallel with early tasks; a **second `makemessages` pass after I18N-14** avoids re-doing choice-label translation work

---

### I18N-13 — Set Up Wagtail Locales in Admin

**Priority:** MEDIUM | **Depends On:** I18N-02, I18N-03, I18N-04 | **Parallel:** Yes (parallel to others)

**Problem:**
Wagtail locales table is empty. Must create locale records in Wagtail admin for each language (EN, FR, SW, RW, ES).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add locales | Create Locale objects for all 5 languages |
| Set defaults | Mark English as default locale |
| Document | Record which languages are active |

**Acceptance Criteria:**

- [ ] Exactly five locales exist: **en** (default), **fr**, **sw**, **rw**, **es**—via **committed migration/command (preferred)** or Wagtail Admin → Settings → Locales
- [ ] If using admin: visit Settings → Locales and create each locale as above; English marked default
- [ ] All 5 locales visible in dropdown when editing translatable models
- [ ] Tested: Can create or open French **Product** variant via Wagtail (if registered) and/or verify equivalent via **API** (**I18N-16**)

**Files to Create (recommended):**
- A **data migration** or small **management command** in the repo that creates or updates the five `wagtail.models.Locale` records (en default, fr, sw, rw, es) so **staging/production** match dev without manual admin steps

**Alternative (local/dev only):**
- No committed files—create locales manually via Wagtail Admin → Settings → Locales (not ideal for repeatable deploys)

**Implementation Notes:**
- Admin UI is fine for local experimentation; **for repeatable deploys**, use a migration or idempotent command that creates English (default), fr, sw, rw, es
- Locales are standard Wagtail **`Locale`** rows (**Settings → Locales**); `wagtail-localize` uses them for translation workflows
- Once created, "Translate" button will appear on translatable model admin pages

---

### I18N-14 — Localize Choice Fields (Status, Payment Terms, etc.)

**Priority:** MEDIUM | **Depends On:** I18N-02 | **Parallel:** Yes (parallel to others)

**Problem:**
Choice field labels (e.g., "Draft", "Confirmed", payment terms) are hardcoded in Python. User-facing strings should be translatable.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Mark choices translatable | Wrap choice labels with gettext() function |
| Create translation strings | Extract choice label strings for translation |
| Update serializers | Ensure API returns translated choice labels |

**Acceptance Criteria:**

- [ ] Choice fields in models updated: `('key', _('Label'))`
- [ ] Models affected: Product, Category, SalesOrder, PurchaseOrder, StockReservation, StockMovement, Subscription, Tenant (roles)
- [ ] Import added: `from django.utils.translation import gettext_lazy as _`
- [ ] `python manage.py makemessages` extracts choice labels
- [ ] Choices appear in .po files for translation
- [ ] Serializers return translated choice labels
- [ ] Tested: API returns choice label in selected language

**Files to Modify:**
- `inventory/models/product.py` — Localize choice fields
- `inventory/models/category.py` — Localize choice fields
- `procurement/models/order.py` — Localize choice fields
- `sales/models/order.py` — Localize choice fields
- `tenants/models.py` — Localize choice fields

**Implementation Notes:**
- Use `gettext_lazy()` (imported as `_`) for choice labels
- Example: `UNIT_CHOICES = [('pcs', _('Pieces')), ('kg', _('Kilograms'))]`
- Lazy evaluation ensures choices are translated at request time
- Serializers may need custom method to get translated choice labels

---

### I18N-15 — Testing & Validation

**Priority:** HIGH | **Depends On:** All other I18N tasks (including **I18N-16**) | **Parallel:** No (final validation)

**Problem:**
No comprehensive test coverage for i18n features. Must validate that language switching, **API read and write** for localized catalog data, and per-tenant locale behave correctly for **tenant-facing** clients.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Backend tests | Test model translations, API language parameter, middleware |
| Frontend tests | Test language switcher, locale routing, message loading |
| Integration tests | Test end-to-end translation workflow |
| Tenant isolation | Verify each tenant can have independent language preference |

**Acceptance Criteria:**

- [ ] `tests/integration/test_i18n_models.py` created
- [ ] `tests/api/test_language_parameter.py` created
- [ ] `tests/test_locale_middleware.py` created
- [ ] Test: Product (or Category) **French variant** creatable/updatable via **API** per **I18N-16** (primary); optional: same via Wagtail if snippets registered
- [ ] Test: API returns French translation with `?language=fr`
- [ ] Test: API defaults to tenant's preferred language
- [ ] Test: TenantA (French) and TenantB (Spanish) return correct languages
- [ ] Test: Frontend language switcher creates locale cookie
- [ ] Test: Frontend routes change locale correctly
- [ ] Frontend test: LanguageSwitcher component renders all languages
- [ ] Run full test suite: `python manage.py test` — all pass
- [ ] Run frontend tests: `cd frontend && yarn test` — all pass

**Files to Create:**
- `tests/integration/test_i18n_models.py` — Model translation tests
- `tests/api/test_language_parameter.py` — API language support tests
- `tests/test_locale_middleware.py` — Middleware locale activation tests
- `frontend/__tests__/components/LanguageSwitcher.test.tsx` — Frontend component tests (if using Jest)

**Implementation Notes:**
- Use Django TestCase and fixtures for model tests
- Use DRF's APITestCase for API tests
- Mock translations for testing (don't rely on actual .po files)
- Test both success and edge cases (invalid language codes, missing translations, etc.)

---

## Dependency Graph

```
I18N-01 (Install dependencies)
├─ I18N-02 (Django/Wagtail settings)
│  ├─ I18N-03 (Product & Category TranslatableMixin)
│  │  └─ I18N-06 (Localize field overrides — supplementary)
│  │  └─ I18N-11 (Serializers)
│  ├─ I18N-04 (Supplier & Customer TranslatableMixin)
│  │  └─ I18N-06 (Localize field overrides — supplementary)
│  │  └─ I18N-11 (Serializers)
│  ├─ I18N-05 (Tenant preferred_language field)
│  │  └─ I18N-09 (Locale middleware)
│  ├─ I18N-10 (API language parameter — read path)
│  │  └─ I18N-16 (DRF authoring — write path for tenants)
│  ├─ I18N-12 (Translation files)
│  ├─ I18N-13 (Wagtail locales setup)
│  └─ I18N-14 (Choice field translations)
├─ I18N-07 (Frontend next-intl)
│  └─ I18N-08 (Language switcher UI)
└─ I18N-15 (Testing) — depends on all others (including I18N-16)

```

---

## Recommended Execution Order

**Phase 0 (Blocking):**
- I18N-01: Install dependencies

**Phase 1 (Configuration, after Phase 0):**
- I18N-02: Configure Django/Wagtail i18n settings
- I18N-07: Configure frontend next-intl

**Phase 2 (Models & Tenant Setup, after Phase 1 — can run in parallel):**
- I18N-03: Add TranslatableMixin to Product & Category
- I18N-04: Add TranslatableMixin to Supplier & Customer
- I18N-05: Add preferred_language field to Tenant

**Phase 3 (Integration, after Phase 2 — can run in parallel):**
- I18N-06: wagtail-localize field behavior; standard `FieldPanel` only (supplementary)
- I18N-08: Create language switcher UI
- I18N-09: Implement locale middleware for per-tenant language
- I18N-10: Add language parameter to API (tenant read path)
- I18N-12: Create & populate translation files
- I18N-13: Set up Wagtail locales in admin
- I18N-14: Localize choice fields

**Phase 4 (API localization layer, after I18N-10):**
- I18N-11: Update serializers for language awareness
- I18N-16: DRF authoring for localized catalog (tenant **write** path)

**Phase 5 (Final validation):**
- I18N-15: Testing & validation

---

## Parallelization Summary

**Maximum parallelization (after dependencies met):**

| Phase | Parallel Tasks | Duration |
|-------|---|---|
| Phase 0 | I18N-01 | ~5 min |
| Phase 1 | I18N-02, I18N-07 | ~15 min |
| Phase 2 | I18N-03, I18N-04, I18N-05 | ~20 min |
| Phase 3 | I18N-06, I18N-08, I18N-09, I18N-10, I18N-12, I18N-13, I18N-14 | ~45 min |
| Phase 4 | I18N-11, I18N-16 | ~30–60 min |
| Phase 5 | I18N-15 | ~30 min |
| **Total** | | ~2-3 hours |

**All tasks in Phase 2 and Phase 3 can be worked on by different team members simultaneously.**

---

## Testing Strategy

**Each task includes its own acceptance criteria and tests.** Here's an overview of testing approach:

### Backend Tests

1. **Model translation tests** (I18N-15)
   - Via **API** (I18N-16): create/update source and French variant; verify linkage and tenant isolation
   - Query API with `?language=fr`, verify French content returned (I18N-10, I18N-11)
   - Per-tenant localization: Tenant A (French), Tenant B (Spanish)

2. **Middleware Tests** (I18N-09, I18N-15)
   - Verify tenant's preferred_language activates correct locale
   - Test Django admin UI appears in tenant's language

3. **API tests** (I18N-10, I18N-11, I18N-16, I18N-15)
   - `GET` with `?language=fr` returns French translations when present
   - `GET` without param defaults to tenant language / Accept-Language
   - `POST`/`PATCH` create or update correct locale instance (I18N-16)
   - Invalid language codes handled gracefully

4. **Serializer Tests** (I18N-11, I18N-15)
   - Translated fields return correct language variant
   - Choice fields translated in response

### Frontend Tests

1. **Language Switcher** (I18N-08, I18N-15)
   - Click language option, page locale changes
   - Browser stores language preference
   - All 5 languages render correctly

2. **Locale Routing** (I18N-07, I18N-15)
   - `/en/`, `/fr/`, `/sw/`, `/rw/`, `/es/` routes work
   - Default locale resolves correctly
   - Switching languages updates URL

3. **Message Loading** (I18N-12, I18N-15)
   - Frontend loads correct message file for selected locale
   - Fallback to English if translation missing

### Manual Testing Checklist

- [ ] Create Product (and one other entity) in **default locale** via API; add **fr** (and optionally other) locale via API (**I18N-16**)
- [ ] Visit Wagtail admin with French tenant → Django/Wagtail UI strings in French where gettext applies (**I18N-12**)
- [ ] Switch language in frontend → UI strings / routing update (**I18N-07**, **I18N-08**)
- [ ] API `GET` with different `?language=` codes returns correct catalog translations
- [ ] One tenant (French), another tenant (Spanish) → API defaults and/or responses match expectations
- [ ] If inventory snippets are registered: Wagtail "Translate" visible; **otherwise** skip and rely on API checks
- [ ] Choice field labels in API responses translated when active language matches (**I18N-14**)

---

## Implementation Checklist

- [ ] All dependencies installed (I18N-01)
- [ ] Django/Wagtail i18n configured (I18N-02)
- [ ] Models updated with TranslatableMixin (I18N-03, I18N-04)
- [ ] Tenant model has preferred_language (I18N-05)
- [ ] Translatable models use standard panels + optional `override_translatable_fields` per I18N-06 (no `TranslatableFieldPanel`)
- [ ] Frontend configured for next-intl (I18N-07)
- [ ] Language switcher UI added (I18N-08)
- [ ] Locale middleware activated (I18N-09)
- [ ] API supports language parameter (I18N-10)
- [ ] Serializers handle translations (I18N-11)
- [ ] API supports creating/updating localized catalog rows (I18N-16)
- [ ] Translation files created for all languages (I18N-12)
- [ ] Wagtail locales set up in admin (I18N-13)
- [ ] Choice fields localized (I18N-14)
- [ ] All tests passing (I18N-15)
- [ ] Documentation updated with i18n workflow

---

## Key Concepts & Architecture

### Per-Tenant Localization

Each tenant has a `preferred_language` field. When a request comes in:

1. **Middleware** resolves the current tenant
2. **Locale middleware** activates tenant's preferred language
3. **Views/API** return content in that language automatically
4. If API param `?language=fr` provided, override with requested language

### wagtail-localize workflow (two authoring surfaces)

**A. Tenant operators (primary):** Next.js + **DRF** (**I18N-16**, **I18N-10**, **I18N-11**)

1. Client sends create/update with an agreed **locale** (header, query, or body—document in OpenAPI).
2. Backend creates or updates the **linked locale instance** using wagtail-localize’s **programmatic** APIs—still **no** `name_fr` columns.
3. **GET** requests use `?language=` (and fallbacks) to return the right variant.

**B. Wagtail admin (optional / staff):** same underlying storage

1. Edit model in Wagtail (when registered or exposed in admin).
2. Use **Translate** / locale picker in Wagtail per wagtail-localize (models use normal `FieldPanel`; **I18N-06** = field overrides only if needed).
3. Linked copies behave the same for the API.

**Django / frontend UI strings** (admin labels, Next.js copy): **.po** / **JSON** catalogs (**I18N-12**)—separate from per-row catalog translations.

### Translation File Structure

```
locale/
├── fr/
│   └── LC_MESSAGES/
│       ├── django.po  (French translations)
│       └── django.mo  (compiled)
├── sw/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── django.mo
└── ... (other languages)

frontend/public/locales/
├── en.json
├── fr.json
├── sw.json
├── rw.json
└── es.json
```

---

## Future Enhancements

Beyond the core i18n implementation:

- [ ] **Machine-aided translation**: Integrate Google Translate API for initial translations
- [ ] **Translation management UI**: Admin interface for managing .po file translations
- [ ] **RTL language support**: Add right-to-left language support (if needed)
- [ ] **Timezone localization**: Combine with per-tenant timezone settings
- [ ] **Number/currency formatting**: Localize numeric displays per language
- [ ] **Date formatting**: Locale-aware date/time displays
- [ ] **Richer message formatting**: Extend **next-intl** (I18N-07) with ICU/plural rules as needed

---

## Notes for Developers

### When Adding New Content

1. **Translatable fields**: Always mark user-visible strings with `_()` function
2. **Choice fields**: Use `gettext_lazy()` for choice labels
3. **Model fields**: If adding a field to a `TranslatableMixin` model, use normal `FieldPanel` in Wagtail; add `TranslatableField` / `SynchronizedField` in `override_translatable_fields` only if localize’s defaults are wrong; extend **I18N-16** so tenants can edit that field per locale via the API
4. **API responses**: New serializers should accept `language` in `context` and resolve localized instances (**I18N-11**)

### Running Migrations

After updating models:

```bash
python manage.py makemigrations          # Create migration files
python manage.py migrate                 # Apply to database
python manage.py compilemessages         # Compile .po to .mo files
```

### Testing Translations Locally

```bash
# Create French translations
python manage.py makemessages -l fr

# Edit locale/fr/LC_MESSAGES/django.po (add translations)

# Compile
python manage.py compilemessages

# Test: switch Django language via LANGUAGE_CODE or middleware
# Frontend: test with localhost:3000/fr/
```
