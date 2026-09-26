"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminGetCustomer } from "@/lib/api/customers";
import { titleCase } from "@/lib/text-format";
import { Badge, type BadgeTone, Skeleton } from "@/components/ui";
import { CustomerStatusSection } from "./status-section";
import styles from "../page.module.css";

function customerStatusTone(status: string): BadgeTone {
  if (status === "active") return "success";
  if (status === "suspended") return "danger";
  return "neutral";
}

export default function AdminCustomerDetailPage() {
  const { customerId } = useParams<{ customerId: string }>();
  const { accessToken } = useAdminAuth();

  const {
    data: customer,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["admin-customer", customerId],
    queryFn: () => adminGetCustomer(customerId, accessToken),
  });

  if (isLoading) {
    return (
      <div className={styles.page}>
        <Skeleton height="16rem" />
      </div>
    );
  }

  if (isError || !customer) {
    return (
      <div className={styles.page}>
        <h1>Customer not found</h1>
        <Link href="/admin/customers">Back to customers</Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link href="/admin/customers" className={styles.backLink}>
        Back to customers
      </Link>

      <div className={styles.headingRow}>
        <h1>{customer.full_name}</h1>
        <Badge tone={customerStatusTone(customer.status)}>
          {titleCase(customer.status)}
        </Badge>
      </div>

      <div className={styles.section}>
        <span className={styles.sectionHeading}>Contact</span>
        <div className={styles.itemRow}>
          <span>Email</span>
          <span>{customer.email ?? "—"}</span>
        </div>
        <div className={styles.itemRow}>
          <span>Mobile number</span>
          <span>{customer.mobile_number ?? "—"}</span>
        </div>
        <div className={styles.itemRow}>
          <span>Preferred language</span>
          <span>
            {customer.preferred_language === "bn" ? "Bangla" : "English"}
          </span>
        </div>
      </div>

      <CustomerStatusSection customer={customer} />
    </div>
  );
}
