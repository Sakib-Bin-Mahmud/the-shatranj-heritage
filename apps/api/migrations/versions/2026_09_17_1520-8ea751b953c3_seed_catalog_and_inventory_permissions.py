"""seed catalog and inventory permissions

Revision ID: 8ea751b953c3
Revises: 02449269a248
Create Date: 2026-09-17 15:20:24.993543

Adds the permissions Phase 2 enforces (categories.write, products.write,
inventory.read, inventory.write) and grants them to the roles named in
docs/Entity Relationship Diagram and Database Schema.md §5.3:
content_manager (categories) and inventory_manager (products,
inventory). super_admin gets everything, per the Phase 1 seed's own
precedent.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8ea751b953c3"
down_revision: Union[str, Sequence[str], None] = "02449269a248"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = [
    ("categories.write", "Create, update, and deactivate product categories."),
    ("products.write", "Create, update, and archive products, variants, images, and artisans."),
    ("inventory.read", "View stock levels and inventory transaction history."),
    ("inventory.write", "Adjust stock levels (restock, damage, correction)."),
]

ROLE_PERMISSIONS = {
    "content_manager": ["categories.write"],
    "inventory_manager": ["products.write", "inventory.read", "inventory.write"],
    "super_admin": ["categories.write", "products.write", "inventory.read", "inventory.write"],
}


def upgrade() -> None:
    bind = op.get_bind()

    permissions_table = sa.table(
        "permissions", sa.column("id", UUID), sa.column("code", sa.String), sa.column("description", sa.String)
    )
    role_permissions_table = sa.table(
        "role_permissions", sa.column("role_id", UUID), sa.column("permission_id", UUID)
    )
    roles_table = sa.table("roles", sa.column("id", UUID), sa.column("name", sa.String))

    permission_ids = {code: uuid.uuid4() for code, _ in PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in PERMISSIONS
        ],
    )

    role_ids = {
        name: row[0]
        for name in ROLE_PERMISSIONS
        for row in bind.execute(sa.select(roles_table.c.id).where(roles_table.c.name == name)).fetchall()
    }

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[code]}
            for role_name, codes in ROLE_PERMISSIONS.items()
            for code in codes
            if role_name in role_ids
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE code IN "
        "('categories.write', 'products.write', 'inventory.read', 'inventory.write'))"
    )
    op.execute(
        "DELETE FROM permissions WHERE code IN "
        "('categories.write', 'products.write', 'inventory.read', 'inventory.write')"
    )
