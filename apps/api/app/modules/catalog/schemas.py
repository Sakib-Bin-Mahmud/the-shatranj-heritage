import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

# --- Categories ----------------------------------------------------------


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    description: str | None = None
    image_url: str | None = None
    sort_order: int = 0
    parent_category_id: uuid.UUID | None = None


class CreateCategoryRequest(CategoryBase):
    pass


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    image_url: str | None = None
    sort_order: int | None = None
    parent_category_id: uuid.UUID | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    is_active: bool

    model_config = {"from_attributes": True}


class CategoryTreeResponse(CategoryResponse):
    children: list["CategoryTreeResponse"] = []


# --- Artisans --------------------------------------------------------------


class ArtisanBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    region: str | None = None
    bio: str | None = None
    photo_url: str | None = None


class CreateArtisanRequest(ArtisanBase):
    pass


class UpdateArtisanRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    region: str | None = None
    bio: str | None = None
    photo_url: str | None = None


class ArtisanResponse(ArtisanBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


# --- Product variants --------------------------------------------------


class CreateVariantRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    variant_name: str = Field(min_length=1, max_length=150)
    price_override: Decimal | None = None
    weight_grams: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False


class UpdateVariantRequest(BaseModel):
    variant_name: str | None = Field(default=None, min_length=1, max_length=150)
    price_override: Decimal | None = None
    weight_grams: int | None = None
    attributes: dict[str, Any] | None = None
    is_default: bool | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class VariantResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    variant_name: str
    price_override: Decimal | None
    weight_grams: int | None
    attributes: dict[str, Any]
    is_default: bool
    status: str
    effective_price: Decimal
    quantity_available: int

    model_config = {"from_attributes": True}


# --- Product images ------------------------------------------------------


class ImageResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_variant_id: uuid.UUID | None
    url: str
    alt_text: str | None
    sort_order: int
    is_primary: bool

    model_config = {"from_attributes": True}


# --- Products --------------------------------------------------------------


class CreateProductRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=220)
    description: str | None = None
    category_id: uuid.UUID
    artisan_id: uuid.UUID | None = None
    brand: str | None = None
    base_price: Decimal
    weight_grams: int | None = None
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")
    meta_title: str | None = None
    meta_description: str | None = None


class UpdateProductRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=220)
    description: str | None = None
    category_id: uuid.UUID | None = None
    artisan_id: uuid.UUID | None = None
    brand: str | None = None
    base_price: Decimal | None = None
    weight_grams: int | None = None
    status: str | None = Field(default=None, pattern="^(draft|active|archived)$")
    meta_title: str | None = None
    meta_description: str | None = None


class ProductSummary(BaseModel):
    """Shape returned by GET /products (list), per API Specification §4."""

    id: uuid.UUID
    slug: str
    name: str
    primary_image_url: str | None
    price: Decimal
    stock_status: str


class ProductDetail(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    slug: str
    description: str | None
    category: CategoryResponse
    artisan: ArtisanResponse | None
    brand: str | None
    base_price: Decimal
    currency: str
    weight_grams: int | None
    status: str
    variants: list[VariantResponse]
    images: list[ImageResponse]


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ProductListResponse(BaseModel):
    items: list[ProductSummary]
    meta: PaginationMeta


class AdminProductListResponse(BaseModel):
    items: list[ProductDetail]
    meta: PaginationMeta
