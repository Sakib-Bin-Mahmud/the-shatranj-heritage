// Order shipping/billing addresses come back from the API as a loosely
// typed JSON snapshot (Record<string, unknown>), not a fixed schema —
// see OrderDetail.shipping_address in lib/api/orders.ts.
export function addressLine(address: Record<string, unknown>): string {
  const get = (key: string) =>
    typeof address[key] === "string" ? (address[key] as string) : "";
  return [
    get("address_line1"),
    get("address_line2"),
    get("city"),
    get("district"),
  ]
    .filter(Boolean)
    .join(", ");
}
