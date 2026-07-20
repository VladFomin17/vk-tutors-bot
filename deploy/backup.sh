#!/bin/sh
set -eu

PROJECT_DIR=${PROJECT_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}
BACKUP_DIR=${BACKUP_DIR:-/var/backups/vk-tutors}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-14}
ENV_FILE=${ENV_FILE:-"$PROJECT_DIR/.env.production"}
export ENV_FILE
set -a
. "$ENV_FILE"
set +a
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TARGET="$BACKUP_DIR/$STAMP"
TMP="$TARGET.tmp"

case "$BACKUP_DIR" in ""|/) echo "Unsafe BACKUP_DIR" >&2; exit 1;; esac
umask 077
mkdir -p "$BACKUP_DIR" "$TMP"
trap 'rm -rf -- "$TMP"' EXIT INT TERM

compose() {
  docker compose --env-file "$ENV_FILE" -f "$PROJECT_DIR/compose.yaml" -f "$PROJECT_DIR/compose.prod.yaml" "$@"
}

compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$TMP/postgres.dump"
compose exec -T api python -c "import sys,tarfile; t=tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz'); t.add('/data/media',arcname='media'); t.close()" > "$TMP/media.tar.gz"
sha256sum "$TMP/postgres.dump" "$TMP/media.tar.gz" > "$TMP/SHA256SUMS"
"$PROJECT_DIR/deploy/verify-backup.sh" "$TMP"
mv "$TMP" "$TARGET"
trap - EXIT INT TERM
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -exec rm -rf -- {} +
echo "$TARGET"
