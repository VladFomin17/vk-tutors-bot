#!/bin/sh
set -eu

test "$#" -eq 1
PROJECT_DIR=${PROJECT_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}
ENV_FILE=${ENV_FILE:-"$PROJECT_DIR/.env.production"}
export ENV_FILE
set -a
. "$ENV_FILE"
set +a
BACKUP_DIR=$(CDPATH= cd -- "$1" && pwd)
CHECK_DB="vk_tutors_restore_check_$$"

compose() {
  docker compose --env-file "$ENV_FILE" -f "$PROJECT_DIR/compose.yaml" -f "$PROJECT_DIR/compose.prod.yaml" "$@"
}

(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)
compose exec -T postgres sh -c "createdb -U \"\$POSTGRES_USER\" '$CHECK_DB'"
trap 'compose exec -T postgres sh -c "dropdb -U \"\$POSTGRES_USER\" --if-exists --force \"$CHECK_DB\"" > /dev/null 2>&1 || true' EXIT INT TERM
compose exec -T postgres sh -c "pg_restore -U \"\$POSTGRES_USER\" -d '$CHECK_DB' --no-owner --no-privileges" < "$BACKUP_DIR/postgres.dump"
compose exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d '$CHECK_DB' -v ON_ERROR_STOP=1 -c 'SELECT version_num FROM alembic_version LIMIT 1'" > /dev/null
compose exec -T api python -c "import sys,tarfile; list(tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz'))" < "$BACKUP_DIR/media.tar.gz"
echo "Backup verified"
