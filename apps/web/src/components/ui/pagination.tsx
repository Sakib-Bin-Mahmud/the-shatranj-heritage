import { Button } from "./button";
import styles from "./pagination.module.css";

const DEFAULT_ARIA_LABEL = "Pagination";
const DEFAULT_PREVIOUS_LABEL = "Previous";
const DEFAULT_NEXT_LABEL = "Next";
const DEFAULT_PAGE_OF_LABEL = "Page {page} of {totalPages}";

export type PaginationProps = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  // Shared with the (deliberately English-only) Admin Portal, so labels
  // are optional overrides rather than baked-in useDictionary() calls —
  // storefront callers pass their own localized strings, admin callers
  // pass nothing and get the English defaults below.
  ariaLabel?: string;
  previousLabel?: string;
  nextLabel?: string;
  // Template string with {page} and {totalPages} placeholders.
  pageOfLabel?: string;
};

export function Pagination({
  page,
  totalPages,
  onPageChange,
  ariaLabel = DEFAULT_ARIA_LABEL,
  previousLabel = DEFAULT_PREVIOUS_LABEL,
  nextLabel = DEFAULT_NEXT_LABEL,
  pageOfLabel = DEFAULT_PAGE_OF_LABEL,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const atFirstPage = page <= 1;
  const atLastPage = page >= totalPages;
  const statusText = pageOfLabel
    .replace("{page}", String(page))
    .replace("{totalPages}", String(totalPages));

  return (
    <nav className={styles.pagination} aria-label={ariaLabel}>
      <span role="status" aria-live="polite">
        {statusText}
      </span>
      <div className={styles.controls}>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          aria-disabled={atFirstPage}
          onClick={() => {
            if (!atFirstPage) onPageChange(page - 1);
          }}
        >
          {previousLabel}
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          aria-disabled={atLastPage}
          onClick={() => {
            if (!atLastPage) onPageChange(page + 1);
          }}
        >
          {nextLabel}
        </Button>
      </div>
    </nav>
  );
}
