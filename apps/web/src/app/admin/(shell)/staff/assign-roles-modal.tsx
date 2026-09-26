"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminAssignStaffRoles,
  type Role,
  type StaffSummary,
} from "@/lib/api/staff";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Button, CheckboxField, Modal } from "@/components/ui";
import styles from "./page.module.css";

function AssignRolesForm({
  staff,
  onClose,
  roles,
}: {
  staff: StaffSummary;
  onClose: () => void;
  roles: Role[];
}) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [roleNames, setRoleNames] = useState<string[]>(staff.roles);

  const mutation = useMutation({
    mutationFn: () => adminAssignStaffRoles(staff.id, roleNames, accessToken),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-staff"] });
      onClose();
    },
  });

  function toggleRole(name: string) {
    setRoleNames((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name],
    );
  }

  return (
    <div className={styles.modalForm}>
      <div className={styles.checkboxGrid}>
        {roles.map((role) => (
          <CheckboxField
            key={role.id}
            label={role.name}
            checked={roleNames.includes(role.name)}
            onChange={() => toggleRole(role.name)}
          />
        ))}
      </div>
      {mutation.isError && (
        <Alert tone="danger">
          {mutation.error instanceof ApiClientError
            ? mutation.error.message
            : "Could not update this staff member's roles."}
        </Alert>
      )}
      <div className={styles.modalActions}>
        <Button type="button" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button
          disabled={mutation.isPending || roleNames.length === 0}
          onClick={() => mutation.mutate()}
        >
          Save roles
        </Button>
      </div>
    </div>
  );
}

export function AssignRolesModal({
  staff,
  onClose,
  roles,
}: {
  staff: StaffSummary | null;
  onClose: () => void;
  roles: Role[];
}) {
  return (
    <Modal
      open={Boolean(staff)}
      onClose={onClose}
      title={staff ? `Edit roles — ${staff.full_name}` : "Edit roles"}
    >
      {staff && (
        <AssignRolesForm
          key={staff.id}
          staff={staff}
          onClose={onClose}
          roles={roles}
        />
      )}
    </Modal>
  );
}
