# Internationalization — scope and limitations

The product uses **several mechanisms** together. They are **not** interchangeable: each covers a different kind of “string” or content.

## Where translation happens (stack overview)

| Layer | Technology | What it translates | Typical source of truth |
| ----- | ---------- | ------------------ | ------------------------- |
| **Next.js tenant UI** (labels, buttons, errors, nav) | **next-intl** | Static **UI copy** bundled with the SPA | [`frontend/public/locales/`](../frontend/public/locales/) at runtime; many trees are produced from [`frontend/scripts/`](../frontend/scripts/) via **`yarn locale:merge`** — see [**I18N_FRONTEND.md**](I18N_FRONTEND.md) |
| **Catalog / domain content** (product name, category description, supplier name, …) | **Wagtail i18n + [wagtail-localize](https://www.wagtail-localize.org/)** (`TranslatableMixin`, linked rows per `Locale`) | **Database-backed** translatable fields | **Primary:** REST API (`/api/v1/`) for tenant operators. **Optional:** Wagtail admin — **Catalog (translations)** menu registers Product, Category, Supplier, and Customer snippets so staff with `wagtail_localize.submit_translation` see **Translate** / sync actions. Listings follow `request.tenant`; platform users without a default tenant can scope with `?tenant=<slug>`. |
| **API read/write of localized rows** | **Django REST Framework** + serializers/mixins (`?language=`, `translation_of`, canonical vs overlay locale) | Exposes the right language variant to the SPA | Backend rules in [`api/`](../api/), e.g. translatable serializers and [`inventory/services/localization.py`](../inventory/services/localization.py) |
| **Wagtail / Django staff UI** | Django **gettext** / Wagtail where applicable | Admin strings, some templates | Python `.po` / core translations (orthogonal to the Next.js JSON pipeline) |

**Important:** **wagtail-localize** does **not** replace **next-intl**. The SPA does not read Wagtail locale tables for sidebar labels or form placeholders; those stay in **next-intl** JSON. Conversely, **next-intl** JSON does **not** store per-tenant product titles—those come from the **API** as localized model fields.

For API behaviour (`GET ?language=`, writes, `translation_of`), see [**Architecture** (Tech stack → Internationalization)](ARCHITECTURE.md#tech-stack) and tests under `tests/api/` / `tests/inventory/` (e.g. translatable panels and API authoring).

---

## Wagtail admin vs API-only catalog authoring

- **Default product path:** tenant apps use the **REST API** and Next.js UI; you do **not** need Wagtail snippet screens for day-to-day catalog CRUD.
- **When to use admin snippets:** staff translation workflows, audits, or support edits. Implementation: [`tenants/catalog_snippets.py`](../src/tenants/catalog_snippets.py) (registered from [`tenants/wagtail_hooks.py`](../src/tenants/wagtail_hooks.py)). The **Translate** button on snippet listings comes from **wagtail-localize** and requires the **Submit translation** permission (`wagtail_localize.submit_translation`).
- **Tenant scope:** the same **TenantMiddleware** rules as the rest of the site apply; creating rows in admin without tenant context is blocked (use `?tenant=` or the API).

---

## Scope of the rest of this document

**How** the Next.js catalog pipeline works (scripts → merge → `public/locales`, `en.json` rebuild, where to edit) is documented in [**I18N_FRONTEND.md**](I18N_FRONTEND.md).

The sections below focus on **limitations, boundaries, and caveats** (tenant URL vs default language, parity test coverage, operational constraints). They do **not** describe wagtail-localize workflow limits (e.g. translation coverage in admin, machine translation hooks, or Locale configuration in Wagtail)—those belong in Wagtail/wagtail-localize docs and project tasks ([`TASKS.MD`](TASKS.MD) I18N entries).

## Tenant default language vs URL (operator preference)

The SPA keeps three related ideas separate:

| Mechanism | What it controls | Stored where |
| -------- | ---------------- | ------------ |
| **Path segment** (`/fr/...`) | next-intl UI messages for static copy | URL (and next-intl middleware) |
| **Language switcher** | Operator explicitly chose a locale | `localStorage` key `the-inventory.locale.explicit` (plus `django_language` cookie); legacy sessions may still only have `the-inventory.locale` |
| **Tenant “preferred language”** | Default for operators who never used the switcher | Backend on the tenant record; read from `GET /auth/me/` |

[`TenantLocaleSync`](../frontend/src/components/tenant-locale-sync.tsx) runs after `/auth/me/` succeeds: if **no** explicit choice exists in `localStorage`, it navigates to `tenant.preferred_language` when that differs from the current URL locale. It updates the **`django_language` cookie** and the API UI locale helper so `?language=` stays aligned — it **does not** set the explicit switcher key, so changing the tenant default later can still update the URL on a full reload for users who never used the switcher.

**Expectation:** If an operator has already used the language switcher (or has a pre-upgrade `the-inventory.locale` value), the URL **will not** follow subsequent edits to `tenant.preferred_language` until they clear site data for this origin or pick a language again. That is intentional: explicit UI choice wins over tenant defaults.

Static catalog copy does **not** come from the API `?language=` parameter; that parameter affects Wagtail-backed catalog fields only.

### Limitation: overwritten namespaces (Next.js catalogs only)

Merged subtrees in `public/locales/*.json` are **replaced** when you run **`yarn locale:merge`**. Persist changes in the appropriate files under [`frontend/scripts/`](../frontend/scripts/) (see [**I18N_FRONTEND.md**](I18N_FRONTEND.md)). **`en.json`** is rebuilt from English artifacts; **`fr.json`** is used for key-tree parity, not as the English string source.

## Parity testing (partial coverage, Next.js only)

[`frontend/__tests__/i18n/locale-json-parity.test.ts`](../frontend/__tests__/i18n/locale-json-parity.test.ts) checks **leaf message paths** against `en.json` for:

`Nav`, `Breadcrumbs`, `Reservations`, `Reports`, `CycleCounts`, `BulkOperations`, `Procurement`, `Sales`, `Auth`, `Audit`, `SettingsTenant`, `SettingsPlatform`.

### Limitation: other JSON namespaces are unchecked

Keys under **`Common`**, **`Inventory`**, **`Dashboard`**, **`Errors`**, **`Shell`**, etc. are **not** in that test. **Wagtail-localize / DB content is not covered** by this test at all.

## Locale quality and “mixed” catalogs (Next.js JSON)

- **`Reports` for `rw` and `sw`** may **fall back to English** (`payload[code] ?? payload.en`).
- **`Auth` / `Audit` for `rw` and `sw`** may be **partially** localized.
- The parity test does **not** validate natural language—only **key sets** for the listed namespaces.

## Operational constraints (Next.js pipeline)

- Run merges from **`frontend/`**.
- New **UI** namespaces in the SPA need script/payload updates and often parity test updates.
- **ICU placeholders** must stay consistent across locale files; mistakes often surface only at **runtime**.

## What the Next.js catalog pipeline is not

- **Not a TMS** (no translator workflow or external sync).
- **Not** responsible for **Wagtail** or **API** content translation—that is **wagtail-localize + DRF**, not next-intl JSON.
- **Not** a single “one tool” story: **content** vs **chrome/strings** are intentionally split.

For the **scripts → merge → `public/locales`** workflow and **`en.json` rebuild**, see [**I18N_FRONTEND.md**](I18N_FRONTEND.md). For task-level notes, see [`TASKS.MD`](TASKS.MD) (I18N-*). For product direction, see [`ROADMAP.md`](ROADMAP.md).
