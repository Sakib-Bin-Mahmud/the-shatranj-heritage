import type { ReactNode } from "react";
import { Pagination } from "./pagination";
import { Skeleton } from "./skeleton";
import { EmptyState } from "./empty-state";
import styles from "./table.module.css";

export type SortDirection = "asc" | "desc";

export type TableColumn<T> = {
  key: string;
  header: string;
  // For a column whose header is purely visual noise for sighted users
  // (an actions column with no text label) — keeps the header text for
  // screen readers without printing it in the row.
  srOnlyHeader?: boolean;
  sortable?: boolean;
  render: (row: T) => ReactNode;
};

export type TableProps<T> = {
  columns: TableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  isLoading?: boolean;
  loadingLabel?: string;
  caption?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  sort?: { key: string; direction: SortDirection };
  onSortChange?: (key: string, direction: SortDirection) => void;
  pagination?: {
    page: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
};

export function Table<T>({
  columns,
  rows,
  rowKey,
  isLoading,
  loadingLabel = "Loading…",
  caption,
  emptyTitle = "Nothing here yet",
  emptyDescription,
  sort,
  onSortChange,
  pagination,
}: TableProps<T>) {
  function toggleSort(column: TableColumn<T>) {
    if (!column.sortable || !onSortChange) return;
    const nextDirection: SortDirection =
      sort?.key === column.key && sort.direction === "asc" ? "desc" : "asc";
    onSortChange(column.key, nextDirection);
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.tableScroll}>
        <table className={styles.table} aria-busy={isLoading || undefined}>
          {caption && <caption className="visually-hidden">{caption}</caption>}
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  aria-sort={
                    sort?.key === column.key
                      ? sort.direction === "asc"
                        ? "ascending"
                        : "descending"
                      : undefined
                  }
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      className={styles.sortButton}
                      onClick={() => toggleSort(column)}
                    >
                      {column.header}
                      <span aria-hidden="true">
                        {sort?.key === column.key
                          ? sort.direction === "asc"
                            ? "▲"
                            : "▼"
                          : ""}
                      </span>
                    </button>
                  ) : column.srOnlyHeader ? (
                    <span className="visually-hidden">{column.header}</span>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {columns.map((column) => (
                      <td key={column.key}>
                        <Skeleton />
                      </td>
                    ))}
                  </tr>
                ))
              : rows.map((row) => (
                  <tr key={rowKey(row)}>
                    {columns.map((column) => (
                      <td key={column.key}>{column.render(row)}</td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {isLoading && (
        <span role="status" className="visually-hidden">
          {loadingLabel}
        </span>
      )}

      {!isLoading && rows.length === 0 && (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      )}

      {pagination && !isLoading && rows.length > 0 && (
        <Pagination
          page={pagination.page}
          totalPages={pagination.totalPages}
          onPageChange={pagination.onPageChange}
        />
      )}
    </div>
  );
}
