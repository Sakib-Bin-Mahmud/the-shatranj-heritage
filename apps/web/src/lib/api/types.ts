/**
 * Shared response envelope shapes used across the typed API client
 * helpers in this directory (src/lib/api). Field names and types
 * mirror the backend's Pydantic schemas (apps/api/app/modules, each
 * module's schemas.py) as of Phase 8 — see
 * docs/Frontend Implementation Plan.md Phase F0.
 *
 * Money fields are typed `string`: Decimal fields serialize as JSON
 * strings via Pydantic's `mode="json"` dump, not numbers.
 */

export type PaginationMeta = {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
};

export type Paginated<T> = {
  items: T[];
  meta: PaginationMeta;
};
