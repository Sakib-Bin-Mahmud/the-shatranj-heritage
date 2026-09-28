// Admin-only identifiers (RBAC role names, order statuses) come back
// from the API as snake_case; this is purely their display form.
export function titleCase(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function titleCaseList(values: string[]): string {
  return values.map(titleCase).join(", ");
}
