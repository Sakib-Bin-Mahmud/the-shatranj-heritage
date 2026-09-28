import { apiFetch } from "@/lib/api-client";

export type PaymentStatus = {
  id: string;
  order_id: string;
  method: string;
  status: string;
  amount: string;
  transaction_id: string | null;
  paid_at: string | null;
};

export type InitiatePaymentResult = {
  payment_id: string;
  status: string;
  redirect_url: string | null;
};

export function initiatePayment(
  input: {
    order_id: string;
    method: "bkash" | "nagad" | "rocket" | "card" | "cod";
  },
  accessToken?: string | null,
): Promise<InitiatePaymentResult> {
  return apiFetch<InitiatePaymentResult>("/payments/initiate", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function getPaymentStatus(
  paymentId: string,
  accessToken?: string | null,
): Promise<PaymentStatus> {
  return apiFetch<PaymentStatus>(
    `/payments/${encodeURIComponent(paymentId)}/status`,
    { accessToken },
  );
}
