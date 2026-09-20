"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import {
  getCart,
  removeCartItem,
  updateCartItem,
  type Cart,
} from "@/lib/api/cart";
import { Alert, Button, EmptyState, Skeleton } from "@/components/ui";
import styles from "./page.module.css";

export default function CartPage() {
  const { dict } = useDictionary();
  const t = dict.cart;
  const { status, accessToken } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  const cartQueryKey = ["cart", accessToken ?? "guest"];

  const { data: cart, isLoading } = useQuery({
    queryKey: cartQueryKey,
    queryFn: () => getCart(accessToken),
    enabled: status !== "loading",
  });

  const updateQuantity = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
      updateCartItem(itemId, quantity, accessToken),
    onSuccess: (data) => queryClient.setQueryData<Cart>(cartQueryKey, data),
  });

  const removeItem = useMutation({
    mutationFn: (itemId: string) => removeCartItem(itemId, accessToken),
    onSuccess: (data) => queryClient.setQueryData<Cart>(cartQueryKey, data),
  });

  if (isLoading || status === "loading") {
    return (
      <div className={styles.page}>
        <h1>{t.heading}</h1>
        <Skeleton height="20rem" />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className={styles.page}>
        <h1>{t.heading}</h1>
        <EmptyState
          title={t.emptyHeading}
          action={
            <Button onClick={() => router.push("/products")}>
              {t.emptyAction}
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1>{t.heading}</h1>

      {cart.warnings.length > 0 && (
        <Alert tone="warning">{cart.warnings.join(" ")}</Alert>
      )}

      <div className={styles.layout}>
        <div className={styles.items}>
          {cart.items.map((item) => (
            <div key={item.id} className={styles.item}>
              <div className={styles.imageWrap}>
                {item.primary_image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.primary_image_url}
                    alt={item.product_name ?? ""}
                    className={styles.image}
                  />
                ) : (
                  <span className={styles.imagePlaceholder} aria-hidden="true">
                    ♞
                  </span>
                )}
              </div>

              <div className={styles.itemInfo}>
                {item.product_slug ? (
                  <Link
                    href={`/products/${item.product_slug}`}
                    className={styles.itemName}
                  >
                    {item.product_name}
                  </Link>
                ) : (
                  <span className={styles.itemName}>{item.product_name}</span>
                )}
                {item.variant_name && (
                  <span className={styles.itemMeta}>{item.variant_name}</span>
                )}
                <span className={styles.itemMeta}>
                  ৳{item.unit_price_snapshot} {t.priceEach}
                </span>
                {!item.is_available && (
                  <Alert tone="danger">{t.unavailableLabel}</Alert>
                )}
              </div>

              <div className={styles.itemActions}>
                <span className={styles.lineTotal}>৳{item.line_total}</span>
                <label>
                  <span className={styles.visuallyHidden}>
                    {t.quantityLabel}
                  </span>
                  <input
                    type="number"
                    min={1}
                    max={item.max_available}
                    value={item.quantity}
                    className={styles.quantityInput}
                    onChange={(e) => {
                      const quantity = Number(e.target.value);
                      if (quantity >= 1) {
                        updateQuantity.mutate({ itemId: item.id, quantity });
                      }
                    }}
                  />
                </label>
                <button
                  type="button"
                  className={styles.removeButton}
                  onClick={() => removeItem.mutate(item.id)}
                >
                  {t.removeButton}
                </button>
              </div>
            </div>
          ))}

          {(updateQuantity.isError || removeItem.isError) && (
            <Alert tone="danger">
              {updateQuantity.isError ? t.updateError : t.removeError}
            </Alert>
          )}
        </div>

        <div className={styles.summary}>
          <div className={styles.summaryRow}>
            <span>{t.subtotalLabel}</span>
            <span>৳{cart.subtotal}</span>
          </div>
          <div className={styles.summaryRow}>
            <span>{t.shippingLabel}</span>
            <span>৳{cart.estimated_shipping}</span>
          </div>
          <div className={styles.summaryRow}>
            <span>{t.taxLabel}</span>
            <span>৳{cart.estimated_tax}</span>
          </div>
          {Number(cart.discount_amount) > 0 && (
            <div className={styles.summaryRow}>
              <span>{t.discountLabel}</span>
              <span>-৳{cart.discount_amount}</span>
            </div>
          )}
          <div className={styles.summaryTotal}>
            <span>{t.totalLabel}</span>
            <span>৳{cart.total}</span>
          </div>
          <Button onClick={() => router.push("/checkout")}>
            {t.checkoutButton}
          </Button>
        </div>
      </div>
    </div>
  );
}
