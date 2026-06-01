#!/usr/bin/env bash
set -euo pipefail

DOCKER_ROOT="${DOCKER_ROOT:-/docker}"
BACKUP_ROOT="${BACKUP_ROOT:-/docker/openclaw-client-backups}"
IMAGE="${IMAGE:-ghcr.io/hostinger/hvps-openclaw:latest}"
PORT_START="${PORT_START:-54410}"
PORT_END="${PORT_END:-54599}"
TZ_VALUE="${TZ_VALUE:-Europe/Berlin}"
CPU_LIMIT="${CPU_LIMIT:-1.0}"
MEM_LIMIT="${MEM_LIMIT:-1024M}"

SLUG=""
BASE_HOST=""
PORT=""
APPLY=0
START=0
FORCE=0
BACKUP_NOW=0
CLIENT_ENV_FILE=""
SMOKE=0

usage() {
  cat <<'EOF'
Provision a separate OpenClaw Docker Compose project on a Hostinger Docker VPS.

Usage:
  provision_hostinger_openclaw_client.sh --slug client-a [--dry-run]
  provision_hostinger_openclaw_client.sh --slug client-a --apply
  provision_hostinger_openclaw_client.sh --slug client-a --apply --start

Options:
  --slug NAME        Client slug, lowercase letters/numbers/dashes only.
  --base-host HOST   Override detected Traefik base host, e.g. srv123.hstgr.cloud.
  --port PORT        Override auto-selected app port.
  --image IMAGE      Override OpenClaw image.
  --docker-root DIR  Docker project root. Default: /docker
  --backup-root DIR  Backup root. Default: /docker/openclaw-client-backups
  --apply            Write files into /docker/openclaw-NAME.
  --start            Start the project after writing files. Implies --apply.
  --backup-now       Run the generated per-client backup after writing files.
  --client-env FILE  Append client secrets/settings from a key=value env file.
  --smoke            After start, verify container, local/public HTTP, and model auth if present.
  --force            Allow overwriting an existing project folder.
  --dry-run          Validate and show what would be created without writing.
  -h, --help         Show this help.

Environment overrides:
  PORT_START, PORT_END, TZ_VALUE, CPU_LIMIT, MEM_LIMIT
EOF
}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug)
      SLUG="${2:-}"
      shift 2
      ;;
    --base-host)
      BASE_HOST="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --image)
      IMAGE="${2:-}"
      shift 2
      ;;
    --docker-root)
      DOCKER_ROOT="${2:-}"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    --start)
      APPLY=1
      START=1
      shift
      ;;
    --backup-now)
      BACKUP_NOW=1
      shift
      ;;
    --client-env)
      CLIENT_ENV_FILE="${2:-}"
      shift 2
      ;;
    --smoke)
      SMOKE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      APPLY=0
      START=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$SLUG" ]] || die "--slug is required"
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{0,50}[a-z0-9]$ ]] || die "slug must use lowercase letters, numbers, and dashes, and cannot start/end with dash"
[[ "$PORT_START" =~ ^[0-9]+$ && "$PORT_END" =~ ^[0-9]+$ ]] || die "PORT_START and PORT_END must be numbers"

need_cmd docker
need_cmd sed
need_cmd grep
need_cmd tar

if [[ -n "$CLIENT_ENV_FILE" && ! -f "$CLIENT_ENV_FILE" ]]; then
  die "client env file not found: $CLIENT_ENV_FILE"
fi

PROJECT_NAME="openclaw-${SLUG}"
PROJECT_DIR="${DOCKER_ROOT}/${PROJECT_NAME}"
TARGET_DIR="$PROJECT_DIR"

if [[ ${#PROJECT_NAME} -gt 63 ]]; then
  die "project name is too long for Docker Compose: ${PROJECT_NAME}"
fi

detect_base_host() {
  if [[ -n "$BASE_HOST" ]]; then
    printf '%s\n' "$BASE_HOST"
    return
  fi

  local from_env=""
  from_env="$(find "$DOCKER_ROOT" -maxdepth 2 -type f -name .env -print 2>/dev/null \
    | xargs -r grep -h '^TRAEFIK_HOST=' 2>/dev/null \
    | sed -n 's/^TRAEFIK_HOST=//p' \
    | grep -m1 '.')"
  if [[ -n "$from_env" ]]; then
    printf '%s\n' "$from_env"
    return
  fi

  local from_label=""
  from_label="$(docker ps -q \
    | xargs -r docker inspect --format '{{range $k,$v := .Config.Labels}}{{println $v}}{{end}}' 2>/dev/null \
    | sed -n 's/.*Host(`\([^`]*\)`).*/\1/p' \
    | awk -F. 'NF>2 {sub(/^[^.]*\./, "", $0); print; exit}')"
  if [[ -n "$from_label" ]]; then
    printf '%s\n' "$from_label"
    return
  fi

  die "could not detect Traefik base host. Pass --base-host srvXXXX.hstgr.cloud"
}

port_in_use() {
  local candidate="$1"

  if command -v ss >/dev/null 2>&1 && ss -H -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]${candidate}$"; then
    return 0
  fi

  if docker ps --format '{{.Ports}}' | grep -Eq "(:|0\\.0\\.0\\.0:|:::)$candidate->|:$candidate/tcp"; then
    return 0
  fi

  if find "$DOCKER_ROOT" -maxdepth 3 -type f \( -name .env -o -name '.env.example' -o -name 'docker-compose.yml' -o -name 'compose.yml' \) -print 2>/dev/null \
    | xargs -r grep -hE "(^PORT=${candidate}$|[\"']?${candidate}:${candidate}[\"']?|loadbalancer.server.port=${candidate})" >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

choose_port() {
  if [[ -n "$PORT" ]]; then
    [[ "$PORT" =~ ^[0-9]+$ ]] || die "--port must be a number"
    if port_in_use "$PORT"; then
      die "port $PORT already appears to be in use"
    fi
    printf '%s\n' "$PORT"
    return
  fi

  local candidate
  for candidate in $(seq "$PORT_START" "$PORT_END"); do
    if ! port_in_use "$candidate"; then
      printf '%s\n' "$candidate"
      return
    fi
  done

  die "no free port found in range ${PORT_START}-${PORT_END}"
}

new_token() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 36 | tr -dc 'A-Za-z0-9' | head -c 40
    printf '\n'
  else
    date +%s%N | sha256sum | awk '{print substr($1,1,40)}'
  fi
}

write_project_files() {
  local dir="$1"
  local project="$2"
  local port="$3"
  local host="$4"
  local token="$5"

  mkdir -p "$dir/data/linuxbrew" "$BACKUP_ROOT"

  cat > "$dir/.env" <<EOF
COMPOSE_PROJECT_NAME=${project}
PORT=${port}
TZ=${TZ_VALUE}
TRAEFIK_HOST=${host}
OPENCLAW_GATEWAY_TOKEN=${token}

# Fill per client before production use:
# OPENAI_API_KEY=
# TELEGRAM_BOT_TOKEN=
EOF

  if [[ -n "$CLIENT_ENV_FILE" ]]; then
    {
      printf '\n# Client-specific settings from %s\n' "$CLIENT_ENV_FILE"
      grep -Ev '^[[:space:]]*(#|$)' "$CLIENT_ENV_FILE" \
        | grep -Ev '^(COMPOSE_PROJECT_NAME|PORT|TZ|TRAEFIK_HOST|OPENCLAW_GATEWAY_TOKEN)=' || true
    } >> "$dir/.env"
  fi

  cat > "$dir/docker-compose.yml" <<'EOF'
services:
  openclaw:
    image: ${IMAGE:-ghcr.io/hostinger/hvps-openclaw:latest}
    init: true
    ports:
      - "${PORT}:${PORT}"
    labels:
      - traefik.enable=true
      - traefik.http.routers.${COMPOSE_PROJECT_NAME}.rule=Host(`${COMPOSE_PROJECT_NAME}.${TRAEFIK_HOST}`)
      - traefik.http.routers.${COMPOSE_PROJECT_NAME}.entrypoints=websecure
      - traefik.http.routers.${COMPOSE_PROJECT_NAME}.tls.certresolver=letsencrypt
      - traefik.http.services.${COMPOSE_PROJECT_NAME}.loadbalancer.server.port=${PORT}
    env_file:
      - .env
    restart: unless-stopped
    cpus: "${CPU_LIMIT:-1.0}"
    mem_limit: "${MEM_LIMIT:-1024M}"
    volumes:
      - ./data:/data
      - ./data/linuxbrew:/home/linuxbrew
EOF

  cat > "$dir/backup.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/docker/openclaw-client-backups}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${BACKUP_ROOT}/${PROJECT_NAME}-${STAMP}.tgz"

mkdir -p "$BACKUP_ROOT"
tar -C "$PROJECT_DIR" -czf "$ARCHIVE" data .env docker-compose.yml
find "$BACKUP_ROOT" -type f -name "${PROJECT_NAME}-*.tgz" -mtime +14 -delete
printf '%s\n' "$ARCHIVE"
EOF
  chmod +x "$dir/backup.sh"
}

validate_compose() {
  local dir="$1"
  (
    cd "$dir"
    IMAGE="$IMAGE" CPU_LIMIT="$CPU_LIMIT" MEM_LIMIT="$MEM_LIMIT" docker compose --env-file .env config --quiet
  )
}

has_model_auth() {
  local dir="$1"
  if grep -Eq '^OPENAI_API_KEY=.+|^ANTHROPIC_API_KEY=.+|^OPENROUTER_API_KEY=.+' "$dir/.env"; then
    return 0
  fi

  return 1
}

smoke_project() {
  local dir="$1"
  local project="$2"
  local port="$3"
  local host="$4"
  local url="https://${project}.${host}"
  local container=""
  local code=""
  local path=""

  container="$(docker ps --filter "name=${project}-openclaw-1" --format '{{.Names}}' | head -n 1)"
  if [[ -z "$container" ]]; then
    container="$(docker ps --filter "name=${project}" --format '{{.Names}}' | head -n 1)"
  fi
  [[ -n "$container" ]] || die "smoke failed: no running container for $project"

  log "Smoke container: $container"
  docker exec "$container" sh -lc 'command -v openclaw; openclaw --version'

  for path in / /health /api/health; do
    code="$(curl -k -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}${path}" || true)"
    log "Smoke local ${path}: ${code}"
  done

  for path in / /health /api/health; do
    code="$(curl -k -s -o /dev/null -w '%{http_code}' "${url}${path}" || true)"
    log "Smoke public ${path}: ${code}"
  done

  if has_model_auth "$dir"; then
    log "Smoke agent: running because model auth env exists"
    docker exec "$container" openclaw agent --agent main --session-id "smoke-${project}" -m "Reply exactly OK_OPENCLAW_CLIENT" --json
  else
    log "Smoke agent: skipped; no model API key/auth file was provided for this client"
  fi
}

BASE_HOST="$(detect_base_host)"
PORT="$(choose_port)"
GATEWAY_TOKEN="$(new_token)"
URL="https://${PROJECT_NAME}.${BASE_HOST}"

if [[ "$APPLY" -eq 1 ]]; then
  if [[ -e "$PROJECT_DIR" && "$FORCE" -ne 1 ]]; then
    die "project directory already exists: $PROJECT_DIR (use --force only if you really want to overwrite generated files)"
  fi
else
  TARGET_DIR="$(mktemp -d "/tmp/${PROJECT_NAME}.XXXXXX")"
  trap 'rm -rf "$TARGET_DIR"' EXIT
fi

write_project_files "$TARGET_DIR" "$PROJECT_NAME" "$PORT" "$BASE_HOST" "$GATEWAY_TOKEN"
validate_compose "$TARGET_DIR"

if [[ "$APPLY" -eq 1 ]]; then
  log "Created project: $PROJECT_NAME"
  log "Directory: $PROJECT_DIR"
  log "URL: $URL"
  log "Port: $PORT"
  log "Backup: $PROJECT_DIR/backup.sh"

  if [[ "$BACKUP_NOW" -eq 1 ]]; then
    log "Backup archive: $("$PROJECT_DIR/backup.sh")"
  fi

  if [[ "$START" -eq 1 ]]; then
    (
      cd "$PROJECT_DIR"
      IMAGE="$IMAGE" CPU_LIMIT="$CPU_LIMIT" MEM_LIMIT="$MEM_LIMIT" docker compose --env-file .env pull openclaw || true
      IMAGE="$IMAGE" CPU_LIMIT="$CPU_LIMIT" MEM_LIMIT="$MEM_LIMIT" docker compose --env-file .env up -d
    )
    log "Started container for $PROJECT_NAME"
    if [[ "$SMOKE" -eq 1 ]]; then
      smoke_project "$PROJECT_DIR" "$PROJECT_NAME" "$PORT" "$BASE_HOST"
    fi
  else
    log "Not started. To start later:"
    log "  cd $PROJECT_DIR && docker compose --env-file .env up -d"
  fi
else
  log "DRY RUN OK"
  log "Would create: $PROJECT_DIR"
  log "Would use URL: $URL"
  log "Would use port: $PORT"
  log "Would create per-client backup script"
fi
