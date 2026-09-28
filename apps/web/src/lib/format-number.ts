// Presentational only — inserts thousands separators without parsing
// through a float, so a Decimal amount returned by the API as an exact
// string (e.g. "12345.50") is never at risk of floating-point drift.
// The digits shown are exactly the API's own digits, just grouped.
export function formatAmount(value: string): string {
  const negative = value.startsWith("-");
  const unsigned = negative ? value.slice(1) : value;
  const [integerPart, fractionPart] = unsigned.split(".");
  const withCommas = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const sign = negative ? "-" : "";
  return fractionPart !== undefined
    ? `${sign}${withCommas}.${fractionPart}`
    : `${sign}${withCommas}`;
}

export function formatInt(value: number): string {
  return value.toLocaleString("en-US");
}
