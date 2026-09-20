"""Bootstrap the first super_admin account.

Deliberately a one-off CLI script rather than a public API endpoint or a
migration: staff account creation via API (`POST /admin/users`) is
Phase 7 (Admin Portal) work per docs/Implementation Plan.md, and baking
a password hash into a migration would commit a known-password account
to version control. Run once per environment, from apps/api (so `app`
resolves as a package):

    python -m scripts.create_admin_user --email admin@example.com --role super_admin

Prompts for a password interactively (or pass --password, mainly for
scripted/CI use — avoid that in shells with shared history).
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.modules.auth.models import AdminUser, Role
from app.modules.auth.security import hash_password


async def create_admin_user(email: str, password: str, full_name: str, role_name: str) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(AdminUser).where(AdminUser.email == email))
        if existing:
            print(f"Admin user with email {email!r} already exists.", file=sys.stderr)
            raise SystemExit(1)

        role = await session.scalar(select(Role).where(Role.name == role_name))
        if not role:
            print(
                f"Role {role_name!r} not found. Run `alembic upgrade head` first.", file=sys.stderr
            )
            raise SystemExit(1)

        admin = AdminUser(email=email, password_hash=hash_password(password), full_name=full_name)
        admin.roles.append(role)
        session.add(admin)
        await session.commit()
        print(f"Created admin user {email!r} with role {role_name!r}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", default="Super Admin")
    parser.add_argument("--role", default="super_admin")
    parser.add_argument("--password", help="If omitted, you will be prompted (recommended).")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters long.", file=sys.stderr)
        raise SystemExit(1)

    asyncio.run(create_admin_user(args.email, password, args.full_name, args.role))


if __name__ == "__main__":
    main()
