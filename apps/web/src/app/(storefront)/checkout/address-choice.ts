import type { AddressInput } from "@/lib/api/orders";
import type { AddressSelection } from "./address-step";

export function addressChoiceFromSelection(
  selection: AddressSelection,
):
  | { address_id: string; address?: undefined }
  | { address: AddressInput; address_id?: undefined } {
  if (selection.kind === "saved") {
    return { address_id: selection.addressId };
  }
  return { address: selection.address };
}
