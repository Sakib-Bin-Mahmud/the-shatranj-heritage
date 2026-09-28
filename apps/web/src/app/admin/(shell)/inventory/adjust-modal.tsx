"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adjustInventory,
  listInventoryTransactions,
  type AdjustInventoryResult,
  type InventoryItem,
} from "@/lib/api/inventory";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Button, Modal, SelectField, TextField } from "@/components/ui";
import styles from "./page.module.css";

type ChangeType = "restock" | "damage" | "adjustment";

export function AdjustModal({
  item,
  onClose,
}: {
  item: InventoryItem;
  onClose: () => void;
}) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [changeType, setChangeType] = useState<ChangeType>("restock");
  const [quantityDelta, setQuantityDelta] = useState("");
  const [note, setNote] = useState("");
  const [result, setResult] = useState<AdjustInventoryResult | null>(null);

  const { data: transactions } = useQuery({
    queryKey: ["inventory-transactions", item.product_variant_id, result?.id],
    queryFn: () =>
      listInventoryTransactions(
        item.product_variant_id,
        { limit: 1 },
        accessToken,
      ),
    enabled: Boolean(result),
  });

  const adjustMutation = useMutation({
    mutationFn: () =>
      adjustInventory(
        item.product_variant_id,
        {
          change_type: changeType,
          quantity_delta: Number(quantityDelta),
          note: note || undefined,
        },
        accessToken,
      ),
    onSuccess: (r) => {
      setResult(r);
      queryClient.invalidateQueries({ queryKey: ["admin-inventory"] });
    },
  });

  const latestEntry = transactions?.items[0];

  return (
    <Modal
      open
      onClose={onClose}
      title={`Adjust stock — ${item.product_name} (${item.variant_sku})`}
    >
      {!result ? (
        <form
          className={styles.modalForm}
          onSubmit={(e) => {
            e.preventDefault();
            adjustMutation.mutate();
          }}
        >
          <SelectField
            label="Change type"
            value={changeType}
            onChange={(e) => setChangeType(e.target.value as ChangeType)}
          >
            <option value="restock">Restock</option>
            <option value="damage">Damage</option>
            <option value="adjustment">Adjustment</option>
          </SelectField>
          <TextField
            label="Quantity delta"
            type="number"
            required
            value={quantityDelta}
            onChange={(e) => setQuantityDelta(e.target.value)}
            hint="Positive to add stock, negative to remove."
          />
          <TextField
            label="Note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          {adjustMutation.isError && (
            <Alert tone="danger">
              {adjustMutation.error instanceof ApiClientError
                ? adjustMutation.error.message
                : "Could not apply this adjustment."}
            </Alert>
          )}
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={adjustMutation.isPending}>
              Apply
            </Button>
          </div>
        </form>
      ) : (
        <div className={styles.resultPanel}>
          <Alert tone="success">
            Stock adjusted. New on-hand: {result.quantity_on_hand}, available:{" "}
            {result.quantity_available}.
          </Alert>
          {latestEntry && (
            <div className={styles.ledgerEntry}>
              <strong>Ledger entry</strong>
              <span>
                {latestEntry.change_type} ·{" "}
                {latestEntry.quantity_delta > 0 ? "+" : ""}
                {latestEntry.quantity_delta}
              </span>
              {latestEntry.note && <span>{latestEntry.note}</span>}
              <span>{new Date(latestEntry.created_at).toLocaleString()}</span>
            </div>
          )}
          <div className={styles.modalActions}>
            <Button onClick={onClose}>Done</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
