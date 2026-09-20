import { apiFetch } from "@/lib/api-client";
import type { AddressInput } from "./orders";

export type Address = AddressInput & {
  id: string;
  customer_id: string;
  label: string | null;
  country: string;
  is_default: boolean;
};

export function listMyAddresses(
  accessToken?: string | null,
): Promise<Address[]> {
  return apiFetch<Address[]>("/customers/me/addresses", { accessToken });
}
