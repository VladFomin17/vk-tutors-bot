#!/bin/sh
set -eu

PROJECT_DIR=${PROJECT_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}
ENV_FILE=${ENV_FILE:-"$PROJECT_DIR/.env.production"}
export ENV_FILE
set -a
. "$ENV_FILE"
set +a
LIMIT=${DISK_USAGE_LIMIT:-85}
FAILED=0

compose() {
  docker compose --env-file "$ENV_FILE" -f "$PROJECT_DIR/compose.yaml" -f "$PROJECT_DIR/compose.prod.yaml" "$@"
}

usage=$(df -P "$PROJECT_DIR" | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')
if [ "$usage" -ge "$LIMIT" ]; then
  echo "Disk usage is ${usage}% (limit ${LIMIT}%)" >&2
  FAILED=1
fi

running=$(compose ps --services --filter status=running)
for service in postgres api vk-listener worker frontend caddy; do
  if ! printf '%s\n' "$running" | grep -qx "$service"; then
    echo "Service is not running: $service" >&2
    FAILED=1
  fi
done

if ! curl --fail --silent --show-error "${HEALTHCHECK_URL:?HEALTHCHECK_URL is required}" > /dev/null; then
  echo "Readiness check failed: $HEALTHCHECK_URL" >&2
  FAILED=1
fi

exit "$FAILED"
