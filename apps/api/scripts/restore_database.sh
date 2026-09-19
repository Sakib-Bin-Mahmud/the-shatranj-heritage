#!/usr/bin/env bash
set -euo pipefail

# Restores a backup produced by backup_database.sh (NFR-DR-002/003).
#
# DESTRUCTIVE: drops and recreates the public schema before restoring,
# so anything in the target database that isn't in the backup is lost.
# Always restore into a fresh/throwaway database first to verify a
# backup is actually usable before ever pointing this at a database
# you can't afford to lose — see apps/api/README.md's "Backup &
# Restore" section for the full drill.
#
# Usage: ./scripts/restore_database.sh <backup_file> [--yes]
#   --yes   skip the interactive confirmation prompt (for scripted/CI use)

BACKUP_FILE="${1:?Usage: restore_database.sh <backup_file> [--yes]}"
CONFIRM="${2:-}"
DATABASE_URL="${DATABASE_URL:-postgresql://shatranj:shatranj@localhost:5432/shatranj_heritage}"
PG_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"

if [[ "$CONFIRM" != "--yes" ]]; then
    read -r -p "This will DROP the public schema at ${PG_URL} and restore from ${BACKUP_FILE}. Continue? [y/N] " reply
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

psql "$PG_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
pg_restore --format=custom --dbname="$PG_URL" --no-owner --no-privileges "$BACKUP_FILE"

echo "Restore complete from $BACKUP_FILE"
