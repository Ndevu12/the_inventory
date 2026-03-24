# Project Tasks

> Tasks are designed for parallel execution unless noted in **Depends On**. **This file only lists remaining work** for **Next.js static UI copy** ([next-intl](https://next-intl.dev/), [`frontend/public/locales/`](../frontend/public/locales/)). **Already shipped:** locale routing, language switcher, shell copy (`Nav`, `Shell`, `Breadcrumbs`), API `?language=` from the active UI locale ([`frontend/src/lib/api-client.ts`](../frontend/src/lib/api-client.ts)), and backend catalog localization (Wagtail locales, `TranslatableMixin`, DRF serializers)—extend those by following existing code, not this checklist.

---

## Next.js page UI — Internationalization (I18N-01–I18N-10)

**Goal:** Replace hardcoded English in feature pages with message keys in **all six** JSON files (`en`, `fr`, `sw`, `rw`, `es`, `ar`) and `useTranslations` / `getTranslations`. **CI:** [`tests/test_locale_catalogs.py`](../tests/test_locale_catalogs.py) enforces identical key trees across locales.

---

### Shared rules — Next.js page UI (next-intl)

**Applies to I18N-01 through I18N-10.** Follow these for every task so CI and translators stay consistent.

| Rule | Detail |
| ---- | ------ |
| Key parity | Add strings to [`frontend/public/locales/en.json`](../frontend/public/locales/en.json) first, then mirror the **exact same key tree** in **fr, sw, rw, es, ar** (see [`tests/test_locale_catalogs.py`](../tests/test_locale_catalogs.py)). |
| Namespaces | Use one top-level JSON object per task area (e.g. `Dashboard`, `Products`) with nested keys (`title`, `description`, `actions.save`). Avoid flat collisions across features. |
| Client vs server | Prefer **`useTranslations('Namespace')`** in client components. For rare RSC-only pages, use **`getTranslations({ locale, namespace: '…' })`** from `next-intl/server`. |
| Data tables | Column headers live in `*-columns.tsx`; refactor to **`createXColumns(t)`** or pass **`t`** into factories so headers translate. |
| Reuse | If copy matches an existing key (e.g. `Nav.items.products`), either import the same namespace key or duplicate only when wording must differ—note the choice in the PR. |
| API copy | Choice labels and model-backed strings come from the **API** when `?language=` is set; these tasks cover **static UI only** (buttons, headings, empty states, zod messages in forms). |
| Verify | After JSON edits: `python manage.py test tests.test_locale_catalogs` and `cd frontend && yarn test`. |

---

### I18N-01 — Shared UI strings & cross-cutting patterns

**Priority:** HIGH | **Depends On:** None (assumes next-intl + locale JSON pipeline exists) | **Parallel:** Yes (recommended first; not blocking other tasks)

**Problem:**
Buttons, errors, empty states, and table patterns repeat across features. Without a shared namespace, parallel contributors duplicate keys or English literals.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| `Common` (or `Ui`) keys | Save, Cancel, Delete, Edit, Create, New, Back, Close, Submit, Search, Filter, Export, Import, Loading…, Error, Retry, No results, Required field, etc. |
| Optional `Errors` / `Validation` | Generic load failed, network error, permission denied (where not API-driven). |
| Column pattern doc | One short example in a README comment or this file: `const columns = useMemo(() => createColumns(t), [t])`. |
| Layout chrome | Command palette / search dialog ([`search-command.tsx`](../frontend/src/components/layout/search-command.tsx)), theme toggle labels if any user-visible string remains English. |

**Acceptance Criteria:**

- [x] New keys added under an agreed namespace (extend `Common` or add `Ui`) in **all six** locale JSON files
- [x] At least one refactored consumer (e.g. a shared button label or search palette string) uses `useTranslations` + shared keys
- [x] `python manage.py test tests.test_locale_catalogs` passes
- [x] `cd frontend && yarn test` passes

**Files to Modify (typical):**
- `frontend/public/locales/*.json`
- `frontend/src/components/layout/search-command.tsx` — optional
- `frontend/src/components/ui/*` — only where strings are user-visible and shared

**Implementation Notes:**
- Keep keys stable; prefer `actions.save` over `saveButton`.
- **Table columns:** pass `t` from `useTranslations('Common')` (or a feature namespace) into a column factory, e.g. `const columns = useMemo(() => createColumns(t), [t])`, so headers and cell labels resolve from JSON.
- ICU / plurals: use next-intl rich text only when needed (see **Future enhancements** below).

---

### I18N-02 — Dashboard feature UI strings

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01 for shared labels)

**Problem:**
[`dashboard-page.tsx`](../frontend/src/features/dashboard/pages/dashboard-page.tsx) and dashboard widgets use hardcoded English titles, descriptions, chart labels, and empty states.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Page chrome | H1, subtitle, section headings |
| KPI / charts | Card titles, axis labels, legends, “no data” states |
| Hooks/components | All TSX under [`frontend/src/features/dashboard/`](../frontend/src/features/dashboard/) that render user-visible English |

**Acceptance Criteria:**

- [x] Namespace (e.g. `Dashboard`) in all six `*.json` files with full key parity
- [x] Dashboard page and child components use `useTranslations` (or pass `t` into pure helpers)
- [x] Locale catalog test + frontend tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/dashboard/**/*.tsx`

---

### I18N-03 — Inventory feature UI strings

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Products, categories, stock locations, records, movements, and lots pages, dialogs, and tables contain hardcoded English.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| List & detail pages | Titles, filters, empty states, pagination hints |
| Forms & dialogs | Labels, placeholders, zod `message` strings where local to this feature |
| Tables | Column headers via column factories + `t` |
| Mutations | Toast / success copy if hardcoded |

**Acceptance Criteria:**

- [x] One or more namespaces (e.g. `InventoryProducts`, `InventoryCategories`, `StockRecords`) — structure is up to implementer but must be documented in PR
- [x] All six locale files updated with identical key trees
- [x] Locale catalog test + `yarn test` pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/inventory/**/*.tsx`

---

### I18N-04 — Reservations, cycle counts & bulk operations UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
[`reservations/`](../frontend/src/features/reservations/), [`cycle-counts/`](../frontend/src/features/cycle-counts/), and [`bulk-operations/`](../frontend/src/features/bulk-operations/) still use English literals in pages and forms.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| All pages & components | Titles, descriptions, wizard steps, confirmations |
| Tables & forms | Headers, validation messages, tooltips |

**Acceptance Criteria:**

- [x] Namespaced JSON keys in all six locales; parity enforced by test
- [x] Feature folders use `useTranslations` consistently
- [x] Tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/reservations/**/*.tsx`
- `frontend/src/features/cycle-counts/**/*.tsx`
- `frontend/src/features/bulk-operations/**/*.tsx`

---

### I18N-05 — Procurement feature UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Suppliers, purchase orders, and goods-received flows under [`frontend/src/features/procurement/`](../frontend/src/features/procurement/) are English-only in the UI.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| List/detail/new/edit flows | All visible copy |
| Line items & PO/GRN specifics | Status labels shown in UI (distinct from API enum **values**) |

**Acceptance Criteria:**

- [x] JSON namespaces + six-locale parity
- [x] Column definitions and forms translated
- [x] Tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/procurement/**/*.tsx`

---

### I18N-06 — Sales feature UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Customers, sales orders, and dispatches under [`frontend/src/features/sales/`](../frontend/src/features/sales/) need next-intl coverage.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| CRUD pages & dialogs | Titles, buttons, empty states |
| Tables | Sort/filter labels, column headers |
| Wizards / multi-step | Step titles and descriptions |

**Acceptance Criteria:**

- [x] JSON namespaces + six-locale parity
- [x] Sales feature TSX uses translations; tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/sales/**/*.tsx`

---

### I18N-07 — Reports feature UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Report routes under [`frontend/src/features/reports/`](../frontend/src/features/reports/) (valuation, movement history, low stock, etc.) expose English-only headings and filter labels.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Each report page | Title, description, chart/table chrome |
| Shared report UI | Date range, export, filter components |

**Acceptance Criteria:**

- [x] Namespaced messages per report or a single `Reports` tree with sub-keys per route
- [x] Six-locale parity; tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/reports/**/*.tsx`

---

### I18N-08 — Settings & platform admin UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Tenant settings, profile, members, invitations, billing, users, and platform audit UI under [`frontend/src/features/settings/`](../frontend/src/features/settings/) remain English.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Tenant vs platform | Separate sub-namespaces if helpful (`SettingsTenant`, `SettingsPlatform`) |
| Destructive actions | Confirm dialogs, irreversible warnings |

**Acceptance Criteria:**

- [ ] JSON + components updated; superuser-only screens included
- [ ] Six-locale parity; tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/settings/**/*.tsx`

---

### I18N-09 — Auth & tenant audit UI strings

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes (recommended after I18N-01)

**Problem:**
Login, register, accept-invitation, and tenant [`audit/`](../frontend/src/features/audit/) pages still hardcode English.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Auth flows | Headings, hints, error banners, link text |
| Audit log | Column headers, filters, empty states |

**Acceptance Criteria:**

- [x] `Auth` / `Audit` (or similar) namespaces in all six locales
- [x] Tests pass

**Files to Modify:**
- `frontend/public/locales/*.json`
- `frontend/src/features/auth/**/*.tsx`
- `frontend/src/features/audit/**/*.tsx`

---

### I18N-10 — Page i18n QA sweep

**Priority:** MEDIUM | **Depends On:** I18N-01–I18N-09 (all merged or nearly complete) | **Parallel:** No (final pass)

**Problem:**
Parallel PRs can miss strings, drift key naming, or skip `ar.json`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Grep pass | Search `frontend/src/features` for obvious English literals in JSX (iterate until acceptable) |
| Manual smoke | Two locales (e.g. en + fr + ar) on one page per feature area |
| Docs | Update this file’s checklists to checked state when done |

**Acceptance Criteria:**

- [x] `python manage.py test tests.test_locale_catalogs` passes on `main`
- [x] `cd frontend && yarn test` passes
- [ ] Spot-check: language switch updates **page** copy (not only nav) for sampled routes *(manual — recommended on `/reports`, `/reports/stock-valuation`, and one other feature route in **en / fr / ar**)*
- [x] Any remaining intentional English (e.g. brand names) documented in PR or code comment *(see **Sweep notes** below)*

**Files to Modify:**
- As found during sweep
- `docs/TASKS.MD` — check off Implementation Checklist when complete

**Implementation Notes:**
- Do not block feature PRs on I18N-10; run when most of I18N-02–I18N-09 have landed.

**Sweep notes (close-out):**
- **Reports:** The UI already called `useTranslations('Reports.…')` but locale files were missing the `Reports` tree. Added **`Reports`** to all six catalogs via [`frontend/scripts/reports-locale-payload.json`](../frontend/scripts/reports-locale-payload.json) and [`frontend/scripts/merge-reports-locale.mjs`](../frontend/scripts/merge-reports-locale.mjs) (re-run after editing the payload). **Kinyarwanda** and **Swahili** currently reuse the English `Reports` strings until dedicated translations are added (`payload[code] ?? payload.en`).
- **Residual English:** A grep pass still finds literals on some **platform-only settings** screens (e.g. billing, platform users); keep **I18N-08** open until those components read from `SettingsPlatform` / `SettingsTenant` only. **SKU** and similar abbreviations remain as neutral catalog labels across locales.

---

## Dependency Graph

```
I18N-01 (Shared UI strings — recommended first)
├─ I18N-02 (Dashboard)
├─ I18N-03 (Inventory)
├─ I18N-04 (Reservations / cycle counts / bulk)
├─ I18N-05 (Procurement)
├─ I18N-06 (Sales)
├─ I18N-07 (Reports)
├─ I18N-08 (Settings & platform)
└─ I18N-09 (Auth & tenant audit)
   (all of I18N-02–I18N-09 are parallel to each other after optional I18N-01 patterns land)
        └─ I18N-10 (Page i18n QA sweep — after most page tasks merge)
```

---

## Recommended Execution Order

**Phase A (optional but recommended):**
- **I18N-01:** Shared labels + patterns so feature PRs reuse keys.

**Phase B (maximum parallelization — assign one area per contributor):**
- **I18N-02** through **I18N-09** in any order or all at once.

**Phase C (close-out):**
- **I18N-10:** Grep/manual QA and checklist sign-off.

---

## Parallelization Summary

| Phase | Who can work in parallel | Notes |
|-------|-------------------------|--------|
| A | 1 contributor (or pair with B) | Establishes `Common` / `Ui` keys others import |
| B | Up to **8** contributors | One task ID per feature area (I18N-02 … I18N-09) |
| C | 1 owner | Run when most of Phase B is on `main` |

---

## Testing Strategy

### Per-task (I18N-01–I18N-09)

- **`tests.test_locale_catalogs`:** After every JSON change, all six locale files must share the same key tree as `en.json`.
- **`cd frontend && yarn test`:** Avoid breaking Vitest; add tests for new shared helpers if introduced.
- **Manual:** Switch locale on a page touched by the task; confirm **page** copy updates (not only nav), and RTL for **ar** if layout-sensitive.

### Final sweep (I18N-10)

- Grep for remaining English literals under `frontend/src/features`.
- Spot-check **en / fr / ar** on representative routes per area.

### Manual Testing Checklist

- [ ] **I18N-01:** Shared action labels appear translated on at least one consumer screen
- [ ] **I18N-02–I18N-09:** Each merged area: open two locales on a list + a form page; strings match JSON
- [ ] **I18N-10:** No orphaned English in primary flows; intentional exceptions documented *(reports area cleared; platform settings still partial — see I18N-10 **Sweep notes**)*

---

## Implementation Checklist

- [x] **I18N-01** — Shared UI strings & cross-cutting patterns
- [x] **I18N-02** — Dashboard feature UI strings
- [x] **I18N-03** — Inventory feature UI strings
- [x] **I18N-04** — Reservations, cycle counts & bulk operations UI strings
- [x] **I18N-05** — Procurement feature UI strings
- [x] **I18N-06** — Sales feature UI strings
- [x] **I18N-07** — Reports feature UI strings
- [ ] **I18N-08** — Settings & platform admin UI strings
- [x] **I18N-09** — Auth & tenant audit UI strings
- [x] **I18N-10** — Page i18n QA sweep *(automated checks + documented residuals; manual spot-check item still open in task criteria)*
- [x] `python manage.py test tests.test_locale_catalogs` passes
- [x] `cd frontend && yarn test` passes

---

## Reference — Message files (this initiative)

Tenant UI strings for **pages and features** live here (not in Django `.po`):

```
frontend/public/locales/
├── en.json
├── fr.json
├── sw.json
├── rw.json
├── es.json
└── ar.json
```

Request config loads them via [`frontend/src/i18n/load-messages.ts`](../frontend/src/i18n/load-messages.ts) and [`frontend/src/i18n.ts`](../frontend/src/i18n.ts). Locale list is synced from Wagtail with `sync_frontend_locales` when admin locales change.

---

## Future enhancements (frontend UI)

- [ ] **Machine-aided translation** for JSON values (optional tooling; keep key parity)
- [ ] **RTL polish** for **ar** where individual components still assume LTR
- [ ] **Number/currency / date formatting** per active locale in tables and forms
- [ ] **ICU / plural rules** in next-intl messages where copy needs plurals

---

## Notes for developers

### New Next.js UI copy

1. Add keys to **`en.json`**, then mirror the **same tree** in **fr, sw, rw, es, ar**.
2. Use **`useTranslations('YourNamespace')`** in client components (or **`getTranslations`** in server components).
3. Run **`python manage.py test tests.test_locale_catalogs`** and **`cd frontend && yarn test`** before merging.

### Backend or catalog behavior

Do **not** use this task list for Django/Wagtail work—it is already implemented. For new API fields or translatable models, follow existing patterns under `api/`, `inventory/services/localization.py`, and Wagtail `TranslatableMixin` docs in the codebase.

### Local quick check

```bash
cd frontend && yarn dev
# Visit http://localhost:3000/fr/… (or /ar/…) and confirm strings update after editing JSON.

python manage.py test tests.test_locale_catalogs
cd frontend && yarn test
```
