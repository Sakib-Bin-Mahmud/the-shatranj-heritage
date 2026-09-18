"""seed order permissions

Revision ID: 365af278d782
Revises: 22852a8b4a98
Create Date: 2026-09-17 23:49:42.127550

Adds the permissions Phase 5 enforces (orders.read, orders.write) and
grants them to order_manager, per docs/Entity Relationship Diagram and
Database Schema.md §5.3 ("Manages orders, shipments, and refunds").
super_admin gets everything, per the Phase 1 seed's own precedent.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "365af278d782"
down_revision: Union[str, Sequence[str], None] = "22852a8b4a98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = [
    ("orders.read", "View orders, order details, and payment history."),
    ("orders.write", "Update order status, and record refund requests."),
]

ROLE_PERMISSIONS = {
    "order_manager": ["orders.read", "orders.write"],
    "super_admin": ["orders.read", "orders.write"],
}


def upgrade() -> None:
    bind = op.get_bind()

    permissions_table = sa.table(
        "permissions",
        sa.column("id", UUID),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
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
        for row in bind.execute(
            sa.select(roles_table.c.id).where(roles_table.c.name == name)
        ).fetchall()
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
        "(SELECT id FROM permissions WHERE code IN ('orders.read', 'orders.write'))"
    )
    op.execute("DELETE FROM permissions WHERE code IN ('orders.read', 'orders.write')")
