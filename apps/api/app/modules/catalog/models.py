import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Self-referencing product category tree, per ERD §5.4."""

    __tablename__ = "categories"

    parent_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    parent: Mapped["Category | None"] = relationship(
        back_populates="children", remote_side="Category.id"
    )


class Artisan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Artisan storytelling profile, per ERD §5.5 and BRD recommendation."""

    __tablename__ = "artisans"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Sellable item, per ERD §5.6. `status='active'` is required for
    public visibility (BR-PRO rule: archived/draft products excluded
    from search and listings).
    """

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'archived')", name="ck_products_status"),
        Index("ix_products_search_vector", "search_vector", postgresql_using="gin"),
    )

    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    artisan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artisans.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    base_price: Mapped[Any] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default="BDT"
    )
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Phase 3 (FR-SCH-001): kept in sync by Postgres itself (GENERATED
    # ALWAYS ... STORED), not the application, so it can never drift from
    # name/description. Matches the indexing strategy in
    # docs/Entity Relationship Diagram and Database Schema.md §6.
    # `name` is weighted 'A' and `description` 'B' so ts_rank favors a
    # name match over a description match, not just insertion order.
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
            persisted=True,
        ),
        nullable=False,
    )

    category: Mapped[Category] = relationship()
    artisan: Mapped[Artisan | None] = relationship()
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductVariant.created_at"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )


class ProductVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Purchasable variation of a product (size, material, finish, ...),
    per ERD §5.7. Every variant gets exactly one `Inventory` row,
    created alongside it (see catalog/service.py) — the system has no
    concept of a variant without a stock record.
    """

    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name="ck_product_variants_status"),
        # Per ERD §6 ("GIN on attributes" for attribute-based
        # filtering). Note this doesn't accelerate the current
        # `attributes["material"].astext.ilike(...)` substring filter
        # in catalog/service.py (GIN's jsonb_ops supports containment/
        # existence operators, not arbitrary substring match) — that
        # would need a separate trigram index if it becomes a real
        # workload. This index is what makes a future `attributes @>
        # {...}` containment filter usable without a sequential scan.
        Index("ix_product_variants_attributes", "attributes", postgresql_using="gin"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    variant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    price_override: Mapped[Any | None] = mapped_column(Numeric(12, 2), nullable=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )

    product: Mapped[Product] = relationship(back_populates="variants")


class ProductImage(UUIDPrimaryKeyMixin, Base):
    """Product (or variant-specific) image, per ERD §5.8."""

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    product: Mapped[Product] = relationship(back_populates="images")
