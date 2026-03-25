# Frontend UI catalogs (next-intl)

This document describes how **static tenant UI strings** in the Next.js app are **authored**, **merged**, and **loaded** at runtime. It is the reference for the relationship between [`frontend/scripts/`](../frontend/scripts/) and [`frontend/public/locales/`](../frontend/public/locales/).

For **what the stack translates** (next-intl vs Wagtail vs API), see [I18N_LIMITATIONS.md](I18N_LIMITATIONS.md) (stack overview). For **catalog/content** localization in the database, see [ARCHITECTURE.md](ARCHITECTURE.md) (Internationalization).

---

## Inputs, output, and runtime (one model)

| Layer | Role |
| ----- | ---- |
| **`frontend/scripts/`** | **Authoring inputs:** JSON fragments and payloads per domain (inventory, sales, reports, auth/audit, settings, English rebuild sources). You change these when a merge step owns that namespace. |
| **`yarn locale:merge`** | **Generator:** runs [`merge-all-locales.mjs`](../frontend/scripts/merge-all-locales.mjs) and **writes** into `public/locales/*.json`. |
| **`frontend/public/locales/<locale>.json`** | **Runtime catalogs:** the **only** files next-intl loads in the running app ([`load-messages.ts`](../frontend/src/i18n/load-messages.ts)). |

This is **not** two competing sources of truth you maintain in parallel: for namespaces owned by the pipeline, the flow is **edit scripts → run merge → updated JSON under `public/locales/`**. The app never reads `scripts/` at runtime.

Hand-editing `public/locales/*.json` is fine for namespaces **not** overwritten by a merge step, but any **merged** subtree will be **replaced** on the next `yarn locale:merge`—so persist those changes in the appropriate `scripts/` file and re-run merge.

---

## Merge pipeline (`yarn locale:merge`)

Run from **`frontend/`:**

```bash
cd frontend && yarn locale:merge
```

[`merge-all-locales.mjs`](../frontend/scripts/merge-all-locales.mjs) runs these steps **in order**:

1. **Inventory** — [`merge-inventory-locale.mjs`](../frontend/scripts/merge-inventory-locale.mjs): copies `scripts/inventory-{code}.json` into each file’s `Inventory` key.
2. **Sales** — [`merge-sales-locale.mjs`](../frontend/scripts/merge-sales-locale.mjs): copies [`sales-locale-payload.json`](../frontend/scripts/sales-locale-payload.json) per language into `Sales`.
3. **Reports** — [`merge-reports-locale.mjs`](../frontend/scripts/merge-reports-locale.mjs): copies [`reports-locale-payload.json`](../frontend/scripts/reports-locale-payload.json) per language into `Reports` (with `payload[code] ?? payload.en` fallback where applicable).
4. **Auth + Audit** — [`merge-auth-audit-locale.mjs`](../frontend/scripts/merge-auth-audit-locale.mjs): for **`fr`, `es`, `ar`, `rw`, `sw` only**, replaces `Auth` and `Audit` from [`auth-audit-locale-payload.json`](../frontend/scripts/auth-audit-locale-payload.json). **`en.json` is not updated in this step.**
5. **Settings (English)** — [`apply-settings-locale-en.mjs`](../frontend/scripts/apply-settings-locale-en.mjs): overlays [`settings-locale-en.json`](../frontend/scripts/settings-locale-en.json) onto `en.json` for `SettingsTenant` / `SettingsPlatform` (before rebuild).
6. **Rebuild `en.json`** — [`rebuild-en-locale.mjs`](../frontend/scripts/rebuild-en-locale.mjs): **rewrites** `public/locales/en.json` from English artifacts (`locale-en-core.json`, `locale-en-features.json`, `procurement-en.json`, `inventory-en.json`, slices of sales/reports payloads, `settings-locale-en.json`, [`auth-audit-locale-en.json`](../frontend/scripts/auth-audit-locale-en.json), etc.). It uses **`fr.json` only to assert the same key tree** as other locales; it does **not** copy French strings into English.

### English (`en.json`) is special

- Non-English auth/audit strings come from **`auth-audit-locale-payload.json`** (step 4).
- English **`Audit` / `Auth`** (and other rebuilt sections) come from **`auth-audit-locale-en.json`** via **rebuild** (step 6).  
  When you add or change English keys in those namespaces, update **`auth-audit-locale-en.json`** (and payload files for other locales) and run **`yarn locale:merge`**.

### Procurement on English

`Procurement` in `en.json` is fed from [`procurement-en.json`](../frontend/scripts/procurement-en.json) during rebuild. If procurement keys or shape change in `fr.json`, update that artifact (and other procurement sources) so merges and parity stay aligned.

---

## Using messages in components (next-intl)

- Load path: [`frontend/src/i18n.ts`](../frontend/src/i18n.ts) → `loadMessages(locale)` → `public/locales/<locale>.json`.
- **`useTranslations`** takes a **top-level namespace** that matches one key in the JSON, e.g. `useTranslations("Audit")`.  
  Nested message paths use **dots** on that namespace: `t("tenantPage.includePlatformEvents")`, not `useTranslations("Audit.tenantPage")` (the latter is treated as a single literal namespace name and will not match nested JSON).

---

## Checks

- **Frontend key parity (subset of namespaces):** `cd frontend && yarn locale:parity` — [`locale-json-parity.test.ts`](../frontend/__tests__/i18n/locale-json-parity.test.ts).
- **Backend locale tree (all six JSON files):** `python manage.py test tests.test_locale_catalogs`.

---

## Related docs

- [I18N_LIMITATIONS.md](I18N_LIMITATIONS.md) — stack boundaries (next-intl vs Wagtail vs API), tenant default language vs URL, parity-test coverage gaps, operational caveats.
- [TASKS.MD](TASKS.MD) — I18N task checklist (`frontend/public/locales/` and workflow notes).
