"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminCreateStaff, type Role } from "@/lib/api/staff";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Button,
  CheckboxField,
  Modal,
  TextField,
} from "@/components/ui";
import styles from "./page.module.css";

export function CreateStaffModal({
  open,
  onClose,
  roles,
}: {
  open: boolean;
  onClose: () => void;
  roles: Role[];
}) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [roleNames, setRoleNames] = useState<string[]>([]);

  const mutation = useMutation({
    mutationFn: () =>
      adminCreateStaff(
        { email, password, full_name: fullName, role_names: roleNames },
        accessToken,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-staff"] });
      reset();
      onClose();
    },
  });

  function reset() {
    setEmail("");
    setPassword("");
    setFullName("");
    setRoleNames([]);
  }

  function toggleRole(name: string) {
    setRoleNames((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name],
    );
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        reset();
        onClose();
      }}
      title="New staff member"
    >
      <form
        className={styles.modalForm}
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <TextField
          label="Full name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <TextField
          label="Email"
          type="email"
          required
          autoComplete="off"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="Temporary password"
          type="password"
          required
          autoComplete="new-password"
          hint="At least 8 characters, with a letter and a digit."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className={styles.checkboxGrid}>
          <span>Roles</span>
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
              : "Could not create this staff member."}
          </Alert>
        )}
        <div className={styles.modalActions}>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              reset();
              onClose();
            }}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={mutation.isPending || roleNames.length === 0}
          >
            Create staff member
          </Button>
        </div>
      </form>
    </Modal>
  );
}
