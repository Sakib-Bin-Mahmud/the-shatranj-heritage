"""Seed a local database with demo catalog, customer, and order data.

For local development and demos only — every person, artisan, and
order here is fictional. Refuses to run when ENVIRONMENT=production.
Safe to re-run: catalog/customer/order data is skipped once present, and
product images are only attached to demo products that have none. Run
from apps/api (so `app` resolves as a package), after `alembic upgrade
head`:

    python -m scripts.seed_demo_data

Inside the docker-compose stack:

    docker compose exec api python -m scripts.seed_demo_data

Product images are illustrations from scripts/demo_images/ (see
generate.py there), uploaded to object storage the same way the admin
portal's image upload does — so MinIO must be running.

Every demo customer signs in with the password in DEMO_CUSTOMER_PASSWORD.
"""

import asyncio
import io
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.datastructures import Headers, UploadFile

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.storage import upload_image_file

# Registers `admin_users`, which inventory/payments models reference by
# foreign key, so the mapper can resolve it at flush time.
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.auth.security import hash_password
from app.modules.catalog.models import Artisan, Category, Product, ProductVariant
from app.modules.catalog.service import add_image, effective_price, effective_weight
from app.modules.customers.models import Customer, CustomerAddress
from app.modules.inventory.models import Inventory, InventoryTransaction
from app.modules.newsletter.models import NewsletterSubscriber
from app.modules.orders.models import Order, OrderItem
from app.modules.payments.models import Payment, Refund
from app.modules.shipping.models import Shipment
from app.modules.shipping.service import calculate_shipping

DEMO_CUSTOMER_PASSWORD = "DemoPass123!"
# Presence of this category means the script already ran.
MARKER_CATEGORY_SLUG = "chess-sets"
# How far back the oldest seeded record goes, so the admin reports'
# default date ranges have something to chart.
HISTORY_DAYS = 90

NOW = datetime.now(UTC)


def days_ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


# --- Catalog ---------------------------------------------------------------

# (slug, name, parent slug, description)
CATEGORIES: list[tuple[str, str, str | None, str]] = [
    (
        "chess-sets",
        "Chess Sets",
        None,
        "Complete sets — board and pieces — carved, cast, and woven by hand.",
    ),
    (
        "wooden-chess-sets",
        "Wooden Chess Sets",
        "chess-sets",
        "Rosewood, mango wood, and boxwood sets turned on village lathes.",
    ),
    (
        "brass-and-metal-sets",
        "Brass & Metal Sets",
        "chess-sets",
        "Lost-wax cast brass and copper pieces from Dhamrai's metal workshops.",
    ),
    (
        "travel-chess-sets",
        "Travel Sets",
        "chess-sets",
        "Roll-up and pocket sets for games on trains, launches, and verandas.",
    ),
    ("chess-boards", "Chess Boards", None, "Inlaid boards and embroidered board cloths."),
    ("chess-pieces", "Chess Pieces", None, "Piece sets sold on their own, to pair with any board."),
    ("accessories", "Accessories", None, "Everything a set needs around it."),
    ("storage-boxes", "Storage & Cases", "accessories", "Woven and carved homes for your pieces."),
    ("chess-clocks", "Chess Clocks", "accessories", "Analogue and digital clocks for timed play."),
]

# key -> (name, region, bio)
ARTISANS: dict[str, tuple[str, str, str]] = {
    "karim": (
        "Abdul Karim Mridha",
        "Khulna",
        "A third-generation woodcarver who learned on his grandfather's foot lathe. "
        "Known for Staunton knights with unusually expressive manes.",
    ),
    "rina": (
        "Rina Pal",
        "Dhamrai, Dhaka",
        "Casts every piece by the lost-wax method her family has practised in "
        "Dhamrai for five generations — no two kings come out alike.",
    ),
    "selim": (
        "Mohammad Selim",
        "Sylhet",
        "A sheetal pati weaver who began making cases for chess pieces after a "
        "customer asked for a mat that could hold a whole army.",
    ),
    "shahana": (
        "Shahana Begum",
        "Rajshahi",
        "Weaves and embroiders Rajshahi silk into roll-up boards light enough to carry anywhere.",
    ),
}


@dataclass
class VariantSeed:
    sku: str
    name: str
    attributes: dict[str, Any]
    # Units on the shelf once every seeded order has been applied.
    on_hand: int
    price_override: Decimal | None = None
    weight_grams: int | None = None
    reorder_threshold: int = 5


@dataclass
class ProductSeed:
    sku: str
    name: str
    category: str
    description: str
    base_price: Decimal
    weight_grams: int
    variants: list[VariantSeed]
    artisan: str | None = None
    brand: str | None = None
    is_featured: bool = False
    status: str = "active"


PRODUCTS: list[ProductSeed] = [
    ProductSeed(
        sku="SH-WCS-001",
        name="Royal Bengal Rosewood Chess Set",
        category="wooden-chess-sets",
        artisan="karim",
        description=(
            "Weighted rosewood and boxwood Staunton pieces on a hand-inlaid board. "
            "Each knight is carved freehand, so its mane is unique to your set."
        ),
        base_price=Decimal("18500.00"),
        weight_grams=3200,
        is_featured=True,
        variants=[
            VariantSeed(
                "SH-WCS-001-16",
                "16-inch board",
                {"material": "Rosewood", "size": "16 inch"},
                on_hand=12,
            ),
            VariantSeed(
                "SH-WCS-001-20",
                "20-inch board",
                {"material": "Rosewood", "size": "20 inch"},
                on_hand=4,
                price_override=Decimal("24500.00"),
                weight_grams=4600,
            ),
        ],
    ),
    ProductSeed(
        sku="SH-WCS-002",
        name="Sundarbans Tiger Staunton Set",
        category="wooden-chess-sets",
        artisan="karim",
        description=(
            "A Staunton set whose knights are Royal Bengal tigers mid-leap. "
            "Mango wood board with a mangrove-root border."
        ),
        base_price=Decimal("12900.00"),
        weight_grams=2600,
        is_featured=True,
        variants=[
            VariantSeed(
                "SH-WCS-002-NAT",
                "Natural finish",
                {"material": "Mango wood", "finish": "Natural"},
                on_hand=9,
            ),
            VariantSeed(
                "SH-WCS-002-EBN",
                "Ebonised finish",
                {"material": "Mango wood", "finish": "Ebonised"},
                on_hand=2,
            ),
        ],
    ),
    ProductSeed(
        sku="SH-WCS-003",
        name="Mango Wood Village Set",
        category="wooden-chess-sets",
        artisan="karim",
        description="An everyday set for the tea-stall game: sturdy, light, and easy to replace.",
        base_price=Decimal("6500.00"),
        weight_grams=1800,
        variants=[
            VariantSeed("SH-WCS-003-STD", "Standard", {"material": "Mango wood"}, on_hand=25),
        ],
    ),
    ProductSeed(
        sku="SH-BMS-001",
        name="Dhamrai Lost-Wax Brass Chess Set",
        category="brass-and-metal-sets",
        artisan="rina",
        description=(
            "Thirty-two pieces cast one at a time in Dhamrai by the lost-wax "
            "method, on a brass-edged walnut board."
        ),
        base_price=Decimal("32000.00"),
        weight_grams=5400,
        is_featured=True,
        variants=[
            VariantSeed(
                "SH-BMS-001-ANT",
                "Antique brass",
                {"material": "Brass", "finish": "Antique"},
                on_hand=3,
                reorder_threshold=3,
            ),
            VariantSeed(
                "SH-BMS-001-POL",
                "Polished brass",
                {"material": "Brass", "finish": "Polished"},
                on_hand=6,
                reorder_threshold=3,
            ),
        ],
    ),
    ProductSeed(
        sku="SH-BMS-002",
        name="Mughal Court Brass & Copper Set",
        category="brass-and-metal-sets",
        artisan="rina",
        description=(
            "Shahs, viziers, and war elephants in brass and copper, after the "
            "court sets of the Mughal era. Made to order in small batches."
        ),
        base_price=Decimal("45000.00"),
        weight_grams=6200,
        variants=[
            VariantSeed(
                "SH-BMS-002-STD",
                "Standard",
                {"material": "Brass and copper"},
                on_hand=0,
                reorder_threshold=2,
            ),
        ],
    ),
    ProductSeed(
        sku="SH-TCS-001",
        name="Rajshahi Silk Roll-Up Travel Set",
        category="travel-chess-sets",
        artisan="shahana",
        description=(
            "A silk board that rolls around its own pouch of wooden pieces. "
            "Weighs less than a paperback."
        ),
        base_price=Decimal("3800.00"),
        weight_grams=450,
        is_featured=True,
        variants=[
            VariantSeed(
                "SH-TCS-001-MAR", "Maroon", {"material": "Silk", "colour": "Maroon"}, on_hand=18
            ),
            VariantSeed(
                "SH-TCS-001-IND", "Indigo", {"material": "Silk", "colour": "Indigo"}, on_hand=11
            ),
            VariantSeed(
                "SH-TCS-001-SAF", "Saffron", {"material": "Silk", "colour": "Saffron"}, on_hand=0
            ),
        ],
    ),
    ProductSeed(
        sku="SH-TCS-002",
        name="Magnetic Pocket Chess",
        category="travel-chess-sets",
        artisan="karim",
        description="A folding mango wood case with magnetic pieces that stay put on a moving bus.",
        base_price=Decimal("1900.00"),
        weight_grams=300,
        variants=[
            VariantSeed("SH-TCS-002-STD", "Standard", {"material": "Mango wood"}, on_hand=40),
        ],
    ),
    ProductSeed(
        sku="SH-CB-001",
        name="Inlaid Rosewood & Maple Chessboard",
        category="chess-boards",
        artisan="karim",
        description="Sixty-four hand-cut squares of rosewood and maple, sealed with shellac.",
        base_price=Decimal("9800.00"),
        weight_grams=2400,
        variants=[
            VariantSeed(
                "SH-CB-001-16", "16-inch", {"material": "Rosewood", "size": "16 inch"}, on_hand=7
            ),
            VariantSeed(
                "SH-CB-001-20",
                "20-inch",
                {"material": "Rosewood", "size": "20 inch"},
                on_hand=5,
                price_override=Decimal("13200.00"),
                weight_grams=3400,
            ),
        ],
    ),
    ProductSeed(
        sku="SH-CB-002",
        name="Nakshi Kantha Embroidered Board Cloth",
        category="chess-boards",
        artisan="shahana",
        description=(
            "A cotton board cloth with a nakshi kantha border stitching the story "
            "of a game played across a monsoon."
        ),
        base_price=Decimal("2600.00"),
        weight_grams=250,
        variants=[
            VariantSeed("SH-CB-002-STD", "Standard", {"material": "Cotton"}, on_hand=14),
        ],
    ),
    ProductSeed(
        sku="SH-CP-001",
        name="Weighted Boxwood Staunton Pieces",
        category="chess-pieces",
        artisan="karim",
        description="Tournament-weight Staunton pieces in boxwood and ebonised boxwood.",
        base_price=Decimal("7400.00"),
        weight_grams=1100,
        variants=[
            VariantSeed(
                "SH-CP-001-325",
                "King height 3.25 in",
                {"material": "Boxwood", "size": "3.25 inch"},
                on_hand=10,
            ),
            VariantSeed(
                "SH-CP-001-375",
                "King height 3.75 in",
                {"material": "Boxwood", "size": "3.75 inch"},
                on_hand=6,
                price_override=Decimal("8900.00"),
            ),
        ],
    ),
    ProductSeed(
        sku="SH-CP-002",
        name="Brass Elephant & Camel Shatranj Pieces",
        category="chess-pieces",
        artisan="rina",
        description=(
            "The pieces of shatranj, chess's Persian ancestor: the fil (elephant) "
            "and the camel where bishops and knights stand today."
        ),
        base_price=Decimal("15500.00"),
        weight_grams=2800,
        is_featured=True,
        variants=[
            VariantSeed("SH-CP-002-STD", "Standard", {"material": "Brass"}, on_hand=4),
        ],
    ),
    ProductSeed(
        sku="SH-SB-001",
        name="Sheetal Pati Woven Storage Case",
        category="storage-boxes",
        artisan="selim",
        description="A cool-to-the-touch murta-cane case with a compartment for every piece.",
        base_price=Decimal("2200.00"),
        weight_grams=400,
        variants=[
            VariantSeed("SH-SB-001-S", "Small", {"material": "Murta cane", "size": "Small"}, 20),
            VariantSeed(
                "SH-SB-001-L",
                "Large",
                {"material": "Murta cane", "size": "Large"},
                on_hand=8,
                price_override=Decimal("2900.00"),
            ),
        ],
    ),
    ProductSeed(
        sku="SH-SB-002",
        name="Carved Mango Wood Piece Box",
        category="storage-boxes",
        artisan="karim",
        description="A sliding-lid box with a carved lotus on top and felt-lined slots inside.",
        base_price=Decimal("3400.00"),
        weight_grams=900,
        variants=[
            VariantSeed("SH-SB-002-STD", "Standard", {"material": "Mango wood"}, on_hand=15),
        ],
    ),
    ProductSeed(
        sku="SH-CC-001",
        name="Analogue Tournament Chess Clock",
        category="chess-clocks",
        brand="Heritage Timekeepers",
        description="A wind-up clock in a walnut case, with a flag that falls on the minute.",
        base_price=Decimal("4200.00"),
        weight_grams=700,
        variants=[
            VariantSeed("SH-CC-001-STD", "Walnut case", {"material": "Walnut"}, on_hand=9),
        ],
    ),
    ProductSeed(
        sku="SH-CC-002",
        name="Digital Chess Clock with Delay",
        category="chess-clocks",
        brand="Heritage Timekeepers",
        description="Fischer increment, Bronstein delay, and 30 preset time controls.",
        base_price=Decimal("5600.00"),
        weight_grams=350,
        variants=[
            VariantSeed("SH-CC-002-STD", "Standard", {"material": "ABS plastic"}, on_hand=22),
        ],
    ),
    ProductSeed(
        sku="SH-WCS-099",
        name="Heirloom Ebony Grandmaster Set",
        category="wooden-chess-sets",
        artisan="karim",
        description="Draft listing — not visible on the storefront until published.",
        base_price=Decimal("58000.00"),
        weight_grams=4800,
        status="draft",
        variants=[
            VariantSeed("SH-WCS-099-STD", "Standard", {"material": "Ebony"}, on_hand=0),
        ],
    ),
    ProductSeed(
        sku="SH-TCS-090",
        name="Plastic Folding Travel Set",
        category="travel-chess-sets",
        brand="Generic",
        description="Discontinued — archived listings are hidden from the storefront.",
        base_price=Decimal("650.00"),
        weight_grams=350,
        status="archived",
        variants=[
            VariantSeed("SH-TCS-090-STD", "Standard", {"material": "Plastic"}, on_hand=0),
        ],
    ),
]


DEMO_IMAGES_DIR = Path(__file__).resolve().parent / "demo_images"

# Product SKU -> image file stems (in DEMO_IMAGES_DIR) in gallery order;
# the first is the primary image. A stem that is also a variant SKU
# becomes that variant's image.
PRODUCT_IMAGES: dict[str, list[str]] = {
    "SH-WCS-001": ["SH-WCS-001-1", "SH-WCS-001-2"],
    "SH-WCS-002": ["SH-WCS-002-NAT", "SH-WCS-002-EBN", "SH-WCS-002-2"],
    "SH-WCS-003": ["SH-WCS-003-1"],
    "SH-BMS-001": ["SH-BMS-001-ANT", "SH-BMS-001-POL", "SH-BMS-001-2"],
    "SH-BMS-002": ["SH-BMS-002-1", "SH-BMS-002-2"],
    "SH-TCS-001": ["SH-TCS-001-MAR", "SH-TCS-001-IND", "SH-TCS-001-SAF"],
    "SH-TCS-002": ["SH-TCS-002-1"],
    "SH-CB-001": ["SH-CB-001-1"],
    "SH-CB-002": ["SH-CB-002-1"],
    "SH-CP-001": ["SH-CP-001-1", "SH-CP-001-2"],
    "SH-CP-002": ["SH-CP-002-1"],
    "SH-SB-001": ["SH-SB-001-1"],
    "SH-SB-002": ["SH-SB-002-1"],
    "SH-CC-001": ["SH-CC-001-1"],
    "SH-CC-002": ["SH-CC-002-1"],
    "SH-WCS-099": ["SH-WCS-099-1"],
    "SH-TCS-090": ["SH-TCS-090-1"],
}


# --- Customers -------------------------------------------------------------


@dataclass
class CustomerSeed:
    full_name: str
    email: str | None
    mobile_number: str | None
    joined_days_ago: int
    address: dict[str, Any]
    preferred_language: str = "en"


def _address(
    label: str, name: str, phone: str, line1: str, city: str, district: str, postal: str
) -> dict[str, Any]:
    return {
        "label": label,
        "recipient_name": name,
        "phone": phone,
        "address_line1": line1,
        "address_line2": None,
        "city": city,
        "district": district,
        "postal_code": postal,
        "country": "BD",
    }


CUSTOMERS: list[CustomerSeed] = [
    CustomerSeed(
        "Tanvir Ahmed",
        "tanvir@example.com",
        "01711000001",
        88,
        _address(
            "Home",
            "Tanvir Ahmed",
            "01711000001",
            "House 12, Road 5, Dhanmondi",
            "Dhaka",
            "Dhaka",
            "1205",
        ),
    ),
    CustomerSeed(
        "Nusrat Jahan",
        "nusrat@example.com",
        None,
        70,
        _address(
            "Home",
            "Nusrat Jahan",
            "01811000002",
            "Flat 4B, 22 Agrabad C/A",
            "Chattogram",
            "Chattogram",
            "4100",
        ),
        preferred_language="bn",
    ),
    CustomerSeed(
        "Farhan Rahman",
        "farhan@example.com",
        "01911000003",
        52,
        _address(
            "Office",
            "Farhan Rahman",
            "01911000003",
            "Level 7, 45 Gulshan Avenue",
            "Dhaka",
            "Dhaka",
            "1212",
        ),
    ),
    CustomerSeed(
        "Sadia Islam",
        "sadia@example.com",
        None,
        34,
        _address(
            "Home",
            "Sadia Islam",
            "01611000004",
            "17 Zindabazar Road",
            "Sylhet",
            "Sylhet",
            "3100",
        ),
    ),
    CustomerSeed(
        "Arif Hossain",
        None,
        "01511000005",
        9,
        _address(
            "Home",
            "Arif Hossain",
            "01511000005",
            "8 Shaheb Bazar",
            "Rajshahi",
            "Rajshahi",
            "6100",
        ),
        preferred_language="bn",
    ),
]

GUEST_ADDRESS = _address(
    "Guest", "Mitu Chowdhury", "01311000006", "33 KDA Avenue", "Khulna", "Khulna", "9100"
)


# --- Orders ----------------------------------------------------------------

COURIERS = ("Pathao", "Steadfast", "RedX")


@dataclass
class OrderSeed:
    placed_days_ago: float
    status: str
    payment_method: str
    # (variant SKU, quantity)
    items: list[tuple[str, int]]
    # Index into CUSTOMERS; None for a guest checkout.
    customer: int | None = None
    shipping_method: str = "standard"
    # Overrides the payment status implied by `status` (e.g. a failed
    # online payment that led to cancellation).
    payment_status: str | None = None
    refund_reason: str | None = None


ORDERS: list[OrderSeed] = [
    OrderSeed(80, "delivered", "rocket", [("SH-TCS-002-STD", 2)], customer=None),
    OrderSeed(
        75,
        "delivered",
        "bkash",
        [("SH-WCS-001-16", 1), ("SH-SB-002-STD", 1)],
        customer=0,
    ),
    OrderSeed(61, "delivered", "cod", [("SH-TCS-001-MAR", 2), ("SH-CB-002-STD", 1)], customer=1),
    OrderSeed(
        47,
        "delivered",
        "card",
        [("SH-BMS-001-POL", 1)],
        customer=2,
        shipping_method="express",
    ),
    OrderSeed(40, "delivered", "nagad", [("SH-BMS-002-STD", 1)], customer=0),
    OrderSeed(33, "delivered", "bkash", [("SH-TCS-001-SAF", 3), ("SH-CC-002-STD", 1)], customer=3),
    OrderSeed(
        26,
        "cancelled",
        "bkash",
        [("SH-CP-001-375", 1)],
        customer=2,
        refund_reason="Order cancelled by customer.",
    ),
    OrderSeed(19, "delivered", "card", [("SH-WCS-002-NAT", 1), ("SH-CC-001-STD", 1)], customer=1),
    OrderSeed(
        14,
        "cancelled",
        "card",
        [("SH-CB-001-20", 1)],
        customer=3,
        payment_status="failed",
    ),
    OrderSeed(
        6,
        "shipped",
        "nagad",
        [("SH-WCS-002-EBN", 1), ("SH-SB-001-S", 2)],
        customer=0,
        shipping_method="express",
    ),
    OrderSeed(4, "packed", "card", [("SH-CP-002-STD", 1)], customer=2),
    OrderSeed(2, "confirmed", "cod", [("SH-WCS-003-STD", 1), ("SH-SB-001-L", 1)], customer=4),
    OrderSeed(1, "awaiting_payment", "bkash", [("SH-TCS-001-IND", 1)], customer=1),
    OrderSeed(0.2, "awaiting_payment", "cod", [("SH-CB-001-16", 1)], customer=None),
]

# Statuses whose stock has moved from reserved to sold (see
# orders/service.py:confirm_order).
COMMITTED_STATUSES = {"confirmed", "packed", "shipped", "delivered"}

NEWSLETTER_EMAILS = [
    "tanvir@example.com",
    "nusrat@example.com",
    "chessclub.dhaka@example.com",
    "rahim.k@example.com",
    "lamia.s@example.com",
    "bishop.of.bogura@example.com",
]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", "and")).strip("-")


def _payment_status(order: OrderSeed) -> str:
    if order.payment_status:
        return order.payment_status
    if order.status == "awaiting_payment":
        return "pending"
    if order.payment_method == "cod":
        # Cash is only collected on delivery.
        return "successful" if order.status == "delivered" else "pending"
    return "successful"


def _sold_quantities() -> dict[str, int]:
    """Units each variant left the shelf for, across every committed
    order — added back onto the initial restock so `on_hand` in PRODUCTS
    is what's left afterwards."""
    sold: dict[str, int] = {}
    for order in ORDERS:
        if order.status in COMMITTED_STATUSES or order.refund_reason:
            for sku, quantity in order.items:
                sold[sku] = sold.get(sku, 0) + quantity
    return sold


def _cancelled_after_sale_quantities() -> dict[str, int]:
    returned: dict[str, int] = {}
    for order in ORDERS:
        if order.refund_reason:
            for sku, quantity in order.items:
                returned[sku] = returned.get(sku, 0) + quantity
    return returned


async def _seed_catalog(
    session: AsyncSession,
) -> dict[str, tuple[ProductVariant, Product, Inventory]]:
    categories: dict[str, Category] = {}
    for sort_order, (slug, name, parent_slug, description) in enumerate(CATEGORIES):
        category = Category(
            slug=slug,
            name=name,
            description=description,
            parent_category_id=categories[parent_slug].id if parent_slug else None,
            sort_order=sort_order,
        )
        session.add(category)
        await session.flush()
        categories[slug] = category

    artisans: dict[str, Artisan] = {}
    for key, (name, region, bio) in ARTISANS.items():
        artisans[key] = Artisan(name=name, region=region, bio=bio)
        session.add(artisans[key])
    await session.flush()

    sold = _sold_quantities()
    returned = _cancelled_after_sale_quantities()
    restocked_at = days_ago(HISTORY_DAYS)
    variants: dict[str, tuple[ProductVariant, Product, Inventory]] = {}
    for seed in PRODUCTS:
        product = Product(
            sku=seed.sku,
            name=seed.name,
            slug=_slugify(seed.name),
            description=seed.description,
            category_id=categories[seed.category].id,
            artisan_id=artisans[seed.artisan].id if seed.artisan else None,
            brand=seed.brand,
            base_price=seed.base_price,
            weight_grams=seed.weight_grams,
            status=seed.status,
            is_featured=seed.is_featured,
            meta_title=f"{seed.name} | The Shatranj Heritage",
            meta_description=seed.description,
        )
        session.add(product)
        await session.flush()

        for index, variant_seed in enumerate(seed.variants):
            variant = ProductVariant(
                product_id=product.id,
                sku=variant_seed.sku,
                variant_name=variant_seed.name,
                price_override=variant_seed.price_override,
                weight_grams=variant_seed.weight_grams,
                attributes=variant_seed.attributes,
                is_default=index == 0,
                status="archived" if seed.status == "archived" else "active",
            )
            session.add(variant)
            await session.flush()

            # Net units that left for good: sold minus whatever came back
            # from a cancellation after confirmation.
            net_sold = sold.get(variant_seed.sku, 0) - returned.get(variant_seed.sku, 0)
            restock_quantity = variant_seed.on_hand + net_sold
            inventory = Inventory(
                product_variant_id=variant.id,
                quantity_on_hand=variant_seed.on_hand,
                quantity_reserved=0,
                reorder_threshold=variant_seed.reorder_threshold,
            )
            session.add(inventory)
            if restock_quantity > 0:
                session.add(
                    InventoryTransaction(
                        product_variant_id=variant.id,
                        change_type="restock",
                        quantity_delta=restock_quantity,
                        reference_type="seed",
                        note="Opening stock (demo data).",
                        created_at=restocked_at,
                    )
                )
            variants[variant_seed.sku] = (variant, product, inventory)

    await session.flush()
    return variants


async def _seed_customers(session: AsyncSession) -> list[Customer]:
    password_hash = hash_password(DEMO_CUSTOMER_PASSWORD)
    customers = []
    for seed in CUSTOMERS:
        joined_at = days_ago(seed.joined_days_ago)
        customer = Customer(
            email=seed.email,
            mobile_number=seed.mobile_number,
            password_hash=password_hash,
            full_name=seed.full_name,
            preferred_language=seed.preferred_language,
            created_at=joined_at,
            updated_at=joined_at,
        )
        customer.addresses.append(
            CustomerAddress(
                **seed.address,
                address_type="both",
                is_default=True,
                created_at=joined_at,
                updated_at=joined_at,
            )
        )
        session.add(customer)
        customers.append(customer)
    await session.flush()
    return customers


async def _order_number(session: AsyncSession, placed_at: datetime) -> str:
    # Same format as orders/service.py:_generate_order_number, but dated
    # by when the demo order was "placed" rather than today.
    seq_value = await session.scalar(select(func.nextval("order_number_seq")))
    return f"SH-{placed_at:%Y%m%d}-{seq_value:05d}"


async def _seed_orders(
    session: AsyncSession,
    customers: list[Customer],
    variants: dict[str, tuple[ProductVariant, Product, Inventory]],
) -> None:
    for index, seed in enumerate(ORDERS):
        placed_at = days_ago(seed.placed_days_ago)
        customer = customers[seed.customer] if seed.customer is not None else None
        address = CUSTOMERS[seed.customer].address if seed.customer is not None else GUEST_ADDRESS

        subtotal = Decimal("0.00")
        total_weight = 0
        lines = []
        for sku, quantity in seed.items:
            variant, product, _ = variants[sku]
            unit_price = effective_price(variant, product)
            subtotal += unit_price * quantity
            total_weight += effective_weight(variant, product) * quantity
            lines.append((variant, product, unit_price, quantity))

        shipping_amount = await calculate_shipping(
            session,
            district=address["district"],
            method=seed.shipping_method,
            total_weight_grams=total_weight,
        )
        order = Order(
            order_number=await _order_number(session, placed_at),
            customer_id=customer.id if customer else None,
            guest_email=None if customer else "mitu.guest@example.com",
            guest_phone=None if customer else address["phone"],
            status=seed.status,
            subtotal_amount=subtotal,
            shipping_amount=shipping_amount,
            total_amount=subtotal + shipping_amount,
            shipping_address_snapshot=address,
            placed_at=placed_at,
            created_at=placed_at,
            updated_at=placed_at,
        )
        session.add(order)
        await session.flush()

        for variant, product, unit_price, quantity in lines:
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_variant_id=variant.id,
                    product_name_snapshot=product.name,
                    sku_snapshot=variant.sku,
                    unit_price=unit_price,
                    quantity=quantity,
                    line_total=unit_price * quantity,
                    created_at=placed_at,
                )
            )
            inventory = variants[variant.sku][2]
            if seed.status == "awaiting_payment":
                inventory.quantity_reserved += quantity
            elif seed.status in COMMITTED_STATUSES or seed.refund_reason:
                session.add(
                    InventoryTransaction(
                        product_variant_id=variant.id,
                        change_type="sale",
                        quantity_delta=-quantity,
                        reference_type="order",
                        reference_id=order.id,
                        note=f"Order {order.order_number} confirmed.",
                        created_at=placed_at + timedelta(minutes=5),
                    )
                )
            if seed.refund_reason:
                session.add(
                    InventoryTransaction(
                        product_variant_id=variant.id,
                        change_type="return",
                        quantity_delta=quantity,
                        reference_type="order",
                        reference_id=order.id,
                        note=f"Order {order.order_number} cancelled.",
                        created_at=placed_at + timedelta(days=1),
                    )
                )

        payment_status = _payment_status(seed)
        paid_at = None
        if payment_status == "successful":
            paid_at = placed_at + (
                timedelta(days=3) if seed.payment_method == "cod" else timedelta(minutes=5)
            )
        payment = Payment(
            order_id=order.id,
            method=seed.payment_method,
            provider=None if seed.payment_method == "cod" else "sslcommerz",
            transaction_id=(
                None if seed.payment_method == "cod" else f"DEMO-TXN-{order.order_number}"
            ),
            status=payment_status,
            amount=order.total_amount,
            paid_at=paid_at,
            created_at=placed_at,
            updated_at=paid_at or placed_at,
        )
        session.add(payment)
        await session.flush()

        if seed.refund_reason:
            session.add(
                Refund(
                    order_id=order.id,
                    payment_id=payment.id,
                    amount=payment.amount,
                    reason=seed.refund_reason,
                    status="requested",
                    requested_at=placed_at + timedelta(days=1),
                )
            )

        if seed.status in {"packed", "shipped", "delivered"}:
            shipped_at = placed_at + timedelta(days=1)
            transit_days = 1 if seed.shipping_method == "express" else 3
            shipment_status = {
                "packed": "pending",
                "shipped": "in_transit",
                "delivered": "delivered",
            }[seed.status]
            session.add(
                Shipment(
                    order_id=order.id,
                    courier_name=COURIERS[index % len(COURIERS)],
                    tracking_number=(
                        None if seed.status == "packed" else f"DEMO{order.order_number[-5:]}BD"
                    ),
                    status=shipment_status,
                    estimated_delivery_date=(shipped_at + timedelta(days=transit_days)).date(),
                    shipped_at=None if seed.status == "packed" else shipped_at,
                    delivered_at=(
                        shipped_at + timedelta(days=transit_days)
                        if seed.status == "delivered"
                        else None
                    ),
                    created_at=placed_at,
                    updated_at=placed_at,
                )
            )

    await session.flush()


async def _seed_images(session: AsyncSession) -> int:
    """Attaches each demo product's illustrations, primary first. A
    product that already has any image is left alone, so this never
    duplicates images or overrides ones uploaded through the admin
    portal."""
    products = await session.scalars(
        select(Product)
        .where(Product.sku.in_(PRODUCT_IMAGES))
        .options(selectinload(Product.images), selectinload(Product.variants))
    )
    uploaded = 0
    for product in products:
        if product.images:
            continue
        variants_by_sku = {variant.sku: variant for variant in product.variants}
        images = []
        for sort_order, stem in enumerate(PRODUCT_IMAGES[product.sku]):
            variant = variants_by_sku.get(stem)
            file = UploadFile(
                io.BytesIO((DEMO_IMAGES_DIR / f"{stem}.webp").read_bytes()),
                filename=f"{stem}.webp",
                headers=Headers({"content-type": "image/webp"}),
            )
            url = await upload_image_file(file, key_prefix=f"products/{product.id}")
            image = await add_image(
                session,
                product.id,
                url=url,
                alt_text=f"{product.name} — {variant.variant_name}" if variant else product.name,
                is_primary=sort_order == 0,
                product_variant_id=variant.id if variant else None,
            )
            image.sort_order = sort_order
            images.append(image)
            uploaded += 1
        # add_image decides "first image -> primary" from the product's
        # loaded `images`, which doesn't see images added earlier in this
        # same session — so every one claims primary and the last wins.
        # Set the flags explicitly instead.
        for image in images:
            image.is_primary = image is images[0]
    await session.flush()
    return uploaded


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as session:
        if await session.scalar(select(Category).where(Category.slug == MARKER_CATEGORY_SLUG)):
            print(
                f"Demo data already present (category {MARKER_CATEGORY_SLUG!r} exists) — "
                "skipping catalog, customers, and orders."
            )
        else:
            variants = await _seed_catalog(session)
            customers = await _seed_customers(session)
            await _seed_orders(session, customers, variants)
            session.add_all(NewsletterSubscriber(email=email) for email in NEWSLETTER_EMAILS)
            await session.commit()
            print(
                f"Seeded {len(CATEGORIES)} categories, {len(ARTISANS)} artisans, "
                f"{len(PRODUCTS)} products, {len(CUSTOMERS)} customers, {len(ORDERS)} orders, "
                f"and {len(NEWSLETTER_EMAILS)} newsletter subscribers."
            )
            print(f"Demo customers sign in with password {DEMO_CUSTOMER_PASSWORD!r}.")

        uploaded = await _seed_images(session)
        await session.commit()
        print(f"Uploaded {uploaded} product images.")


def main() -> None:
    if get_settings().environment == "production":
        print("Refusing to seed demo data into a production environment.", file=sys.stderr)
        raise SystemExit(1)

    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
