from prometheus_client import Counter, Gauge

# Request-level metrics (latency, request/response counts by path/
# method/status) come for free from prometheus-fastapi-instrumentator,
# wired in main.py. These are the business-level counters/gauges NFR-
# MON-001/002 ask for on top of that: order/payment health and low
# stock, so an alert can fire on "orders stopped succeeding" or
# "payments are failing" rather than only on raw HTTP error rates.

orders_placed_total = Counter(
    "orders_placed_total", "Orders successfully placed", ["payment_method"]
)

payment_webhook_results_total = Counter(
    "payment_webhook_results_total",
    "Payment webhook deliveries processed, by outcome",
    ["result"],
)

notifications_failed_total = Counter(
    "notifications_failed_total",
    "Notification sends that failed (NFR-AVL-003: never blocks the triggering operation)",
    ["channel", "template_code"],
)

low_stock_variants = Gauge(
    "low_stock_variants",
    "Product variants currently at or below their reorder threshold",
)
