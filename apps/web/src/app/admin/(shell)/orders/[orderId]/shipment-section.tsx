"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminAssignShipment,
  adminGetShipment,
  adminUpdateShipmentStatus,
  type OrderDetail,
} from "@/lib/api/orders";
import { nextShipmentStatuses, shipmentStatusTone } from "@/lib/order-status";
import { titleCase } from "@/lib/text-format";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Badge, Button, Modal, TextField } from "@/components/ui";
import styles from "../page.module.css";

export function ShipmentSection({ order }: { order: OrderDetail }) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();

  const {
    data: shipment,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin-order-shipment", order.id],
    queryFn: () => adminGetShipment(order.id, accessToken),
    retry: false,
  });

  function invalidate() {
    queryClient.invalidateQueries({
      queryKey: ["admin-order-shipment", order.id],
    });
    queryClient.invalidateQueries({ queryKey: ["admin-order", order.id] });
  }

  const [assigning, setAssigning] = useState(false);
  const [courierName, setCourierName] = useState("");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [eta, setEta] = useState("");

  const assignMutation = useMutation({
    mutationFn: () =>
      adminAssignShipment(
        order.id,
        {
          courier_name: courierName,
          tracking_number: trackingNumber || null,
          estimated_delivery_date: eta || null,
        },
        accessToken,
      ),
    onSuccess: () => {
      setAssigning(false);
      invalidate();
    },
  });

  const [confirmingStatus, setConfirmingStatus] = useState<string | null>(null);
  const statusMutation = useMutation({
    mutationFn: (status: string) =>
      adminUpdateShipmentStatus(
        shipment!.id,
        status as "dispatched" | "in_transit" | "delivered" | "failed",
        accessToken,
      ),
    onSuccess: () => {
      setConfirmingStatus(null);
      invalidate();
    },
  });

  const shipmentMissing =
    isError && error instanceof ApiClientError && error.code === "NOT_FOUND";

  if (isLoading) return null;

  return (
    <div className={styles.section}>
      <span className={styles.sectionHeading}>Shipping</span>

      {shipmentMissing && order.status === "packed" && !assigning && (
        <Button onClick={() => setAssigning(true)}>Assign courier</Button>
      )}

      {shipmentMissing && order.status !== "packed" && (
        <p>Assign a courier once this order has been packed.</p>
      )}

      {shipmentMissing && assigning && (
        <form
          className={styles.modalForm}
          onSubmit={(e) => {
            e.preventDefault();
            assignMutation.mutate();
          }}
        >
          <div className={styles.formGrid}>
            <TextField
              label="Courier name"
              required
              value={courierName}
              onChange={(e) => setCourierName(e.target.value)}
            />
            <TextField
              label="Tracking number (optional)"
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
              hint="Leave blank to let the courier provider book one."
            />
            <TextField
              label="Estimated delivery date (optional)"
              type="date"
              value={eta}
              onChange={(e) => setEta(e.target.value)}
            />
          </div>
          {assignMutation.isError && (
            <Alert tone="danger">
              {assignMutation.error instanceof ApiClientError
                ? assignMutation.error.message
                : "Could not assign a courier to this order."}
            </Alert>
          )}
          <div className={styles.modalActions}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setAssigning(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={assignMutation.isPending}>
              Assign courier
            </Button>
          </div>
        </form>
      )}

      {shipment && (
        <>
          <div className={styles.itemRow}>
            <span>Courier</span>
            <span>{shipment.courier_name ?? "—"}</span>
          </div>
          <div className={styles.itemRow}>
            <span>Tracking number</span>
            <span>{shipment.tracking_number ?? "—"}</span>
          </div>
          <div className={styles.itemRow}>
            <span>Status</span>
            <Badge tone={shipmentStatusTone(shipment.status)}>
              {titleCase(shipment.status)}
            </Badge>
          </div>
          {shipment.estimated_delivery_date && (
            <div className={styles.itemRow}>
              <span>Estimated delivery</span>
              <span>
                {new Date(
                  shipment.estimated_delivery_date,
                ).toLocaleDateString()}
              </span>
            </div>
          )}

          {nextShipmentStatuses(shipment.status).length > 0 && (
            <div className={styles.actionsRow}>
              {nextShipmentStatuses(shipment.status).map((status) => (
                <Button
                  key={status}
                  variant="secondary"
                  onClick={() => setConfirmingStatus(status)}
                >
                  Mark as {titleCase(status)}
                </Button>
              ))}
            </div>
          )}
        </>
      )}

      <Modal
        open={Boolean(confirmingStatus)}
        onClose={() => setConfirmingStatus(null)}
        title={`Mark shipment as ${confirmingStatus ? titleCase(confirmingStatus) : ""}?`}
      >
        <p>
          {confirmingStatus === "delivered"
            ? "This also marks the order as delivered and sends the customer a delivery confirmation."
            : "This updates the shipment's tracking status."}
        </p>
        {statusMutation.isError && (
          <Alert tone="danger">
            {statusMutation.error instanceof ApiClientError
              ? statusMutation.error.message
              : "Could not update this shipment's status."}
          </Alert>
        )}
        <div className={styles.modalActions}>
          <Button variant="ghost" onClick={() => setConfirmingStatus(null)}>
            Cancel
          </Button>
          <Button
            disabled={statusMutation.isPending}
            onClick={() =>
              confirmingStatus && statusMutation.mutate(confirmingStatus)
            }
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}
