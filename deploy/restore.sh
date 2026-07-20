#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ "${RESTORE_CONFIRM:-}" != "restore-vk-tutors" ]; then
  echo "Usage: RESTORE_CONFIRM=restore-vk-tutors $0 /path/to/backup" >&2
  exit 2
fi

PROJECT_DIR=${PROJECT_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}
ENV_FILE=${ENV_FILE:-"$PROJECT_DIR/.env.production"}
export ENV_FILE
set -a
. "$ENV_FILE"
set +a
BACKUP_DIR=$(CDPATH= cd -- "$1" && pwd)
test -f "$BACKUP_DIR/postgres.dump"
test -f "$BACKUP_DIR/media.tar.gz"
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)

compose() {
  docker compose --env-file "$ENV_FILE" -f "$PROJECT_DIR/compose.yaml" -f "$PROJECT_DIR/compose.prod.yaml" "$@"
}

compose stop api vk-listener worker frontend caddy
compose up -d postgres
compose exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$BACKUP_DIR/postgres.dump"
compose run --rm --no-deps -T api python -c "import pathlib,shutil,sys,tarfile; root=pathlib.Path('/data/media'); [shutil.rmtree(p) if p.is_dir() else p.unlink() for p in root.iterdir()]; tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz').extractall('/data',filter='data')" < "$BACKUP_DIR/media.tar.gz"
compose up -d

i=0
until curl --fail --silent --show-error "${HEALTHCHECK_URL:?HEALTHCHECK_URL is required}" > /dev/null; do
  i=$((i + 1))
  [ "$i" -lt 30 ] || exit 1
  sleep 2
done
echo "Restore completed"
