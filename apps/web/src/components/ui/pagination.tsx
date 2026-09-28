import { Button } from "./button";
import styles from "./pagination.module.css";

export type PaginationProps = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

export function Pagination({
  page,
  totalPages,
  onPageChange,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const atFirstPage = page <= 1;
  const atLastPage = page >= totalPages;

  return (
    <nav className={styles.pagination} aria-label="Pagination">
      <span role="status" aria-live="polite">
        Page {page} of {totalPages}
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
          Previous
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
          Next
        </Button>
      </div>
    </nav>
  );
}
