/**
 * App-wide shared constants.
 *
 * Import from "@/lib/utils/constants" to avoid magic numbers scattered across
 * components, stores, and API helpers.
 */

// ── Pagination ──────────────────────────────────────────────────────────────

/** Default number of rows shown in paginated tables. */
export const DEFAULT_PAGE_SIZE = 10;

/** Options exposed in the "rows per page" dropdown. */
export const PAGE_SIZE_OPTIONS = [10, 20, 30, 50] as const;

/** Page size used when fetching "all" records for dropdowns / selects. */
export const FETCH_ALL_PAGE_SIZE = 1000;

// ── App metadata ────────────────────────────────────────────────────────────

export const APP_NAME =
  process.env.NEXT_PUBLIC_APP_NAME ?? "The Inventory";
