#!/usr/bin/env bash
set -euo pipefail

# Automated Postgres backup (NFR-DR-001). Produces a timestamped,
# compressed custom-format dump that pg_restore can apply cleanly
# regardless of table dependency order — see restore_database.sh and
# apps/api/README.md's "Backup & Restore" section for the full
# procedure.
#
# Usage: ./scripts/backup_database.sh [output_dir]
# Reads connection info from DATABASE_URL (same variable
# app/core/config.py uses), falling back to the local dev default.

OUTPUT_DIR="${1:-./backups}"
DATABASE_URL="${DATABASE_URL:-postgresql://shatranj:shatranj@localhost:5432/shatranj_heritage}"
# pg_dump doesn't understand the "+asyncpg" driver suffix SQLAlchemy's
# async engine uses in DATABASE_URL — strip it back to a plain libpq URL.
PG_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"

mkdir -p "$OUTPUT_DIR"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="$OUTPUT_DIR/shatranj_heritage_${TIMESTAMP}.dump"

pg_dump --format=custom --compress=9 --file="$OUTPUT_FILE" "$PG_URL"

echo "Backup written to $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
