"""seed rbac roles and permissions

Revision ID: 850ed220e4c9
Revises: b2ef9bd66a6e
Create Date: 2026-09-17 11:22:45.486561

Seeds the six staff roles named in docs/Entity Relationship Diagram and
Database Schema.md §5.3, plus the small set of permissions Phase 1
actually enforces. Further permissions are added by later migrations as
each owning module (catalog, inventory, orders, ...) ships enforcement
for them — see docs/Implementation Plan.md.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "850ed220e4c9"
down_revision: Union[str, Sequence[str], None] = "b2ef9bd66a6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES = [
    ("super_admin", "Full administrative access across the platform."),
    ("inventory_manager", "Manages products, variants, and stock levels."),
    ("content_manager", "Manages categories, CMS pages, blog posts, and reviews."),
    ("marketing_manager", "Manages coupons, campaigns, and promotions."),
    ("order_manager", "Manages orders, shipments, and refunds."),
    ("customer_support", "Assists customers; read access to customer accounts."),
]

PERMISSIONS = [
    ("customers.read", "View customer accounts."),
    ("customers.manage", "Suspend/reactivate customer accounts."),
    ("staff.manage", "Create staff accounts and assign roles."),
]

ROLE_PERMISSIONS = {
    "super_admin": ["customers.read", "customers.manage", "staff.manage"],
    "customer_support": ["customers.read"],
}


def upgrade() -> None:
    roles_table = sa.table(
        "roles",
        sa.column("id", UUID),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    permissions_table = sa.table(
        "permissions",
        sa.column("id", UUID),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions_table = sa.table(
        "role_permissions", sa.column("role_id", UUID), sa.column("permission_id", UUID)
    )

    role_ids = {name: uuid.uuid4() for name, _ in ROLES}
    permission_ids = {code: uuid.uuid4() for code, _ in PERMISSIONS}

    op.bulk_insert(
        roles_table,
        [
            {"id": role_ids[name], "name": name, "description": description}
            for name, description in ROLES
        ],
    )
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in PERMISSIONS
        ],
    )
    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[code]}
            for role_name, codes in ROLE_PERMISSIONS.items()
            for code in codes
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM permissions")
    op.execute("DELETE FROM roles")
