"""seed phase7 permissions

Revision ID: 20d514a833a6
Revises: 667594ab073a
Create Date: 2026-09-18 08:00:42.822930

Adds the permissions Phase 7 enforces: cms.write (policy pages),
audit.read (audit log viewer), settings.manage (shipping-rate
settings), and reports.read (admin reporting). Per docs/Entity
Relationship Diagram and Database Schema.md §5.3, content_manager
"manages categories, CMS pages, blog posts, and reviews" so it gets
cms.write; the other three are super_admin-only, matching how
staff.manage/audit-adjacent capabilities were scoped in Phase 1.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20d514a833a6"
down_revision: Union[str, Sequence[str], None] = "667594ab073a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = [
    ("cms.write", "Create and update CMS pages."),
    ("audit.read", "View the admin/system action audit trail."),
    ("settings.manage", "View and update system settings (e.g. shipping rates)."),
    ("reports.read", "View sales, inventory, customer, and refund reports."),
]

ROLE_PERMISSIONS = {
    "content_manager": ["cms.write"],
    "super_admin": ["cms.write", "audit.read", "settings.manage", "reports.read"],
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
        "(SELECT id FROM permissions WHERE code IN "
        "('cms.write', 'audit.read', 'settings.manage', 'reports.read'))"
    )
    op.execute(
        "DELETE FROM permissions WHERE code IN "
        "('cms.write', 'audit.read', 'settings.manage', 'reports.read')"
    )
