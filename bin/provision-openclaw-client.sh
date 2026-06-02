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

write_agent_bootstrap_files() {
  local workspace_dir="$1"
  local package_dir
  local assets_dir=""
  local candidate

  package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

  for candidate in \
    "${CLIENT_AGENT_ASSETS_DIR:-}" \
    "$package_dir/assets/client-agent-workspace" \
    "/usr/local/share/openclaw-run-once-client-wizard/assets/client-agent-workspace"; do
    if [[ -n "$candidate" && -d "$candidate" ]]; then
      assets_dir="$candidate"
      break
    fi
  done

  [[ -n "$assets_dir" ]] || die "missing client agent bootstrap assets"

  mkdir -p "$workspace_dir/memory" "$workspace_dir/scripts"
  cp -a "$assets_dir"/. "$workspace_dir"/

  cat > "$workspace_dir/AGENTS.md" <<'EOF'
# AGENTS.md - Client Agent Workspace

## Startup

If `BOOTSTRAP.md` exists, follow it first. It is the only place that performs the first-run client onboarding and skill-reading flow.

Do not reread the bootstrap skills on every session by default. Use them when the current task needs Meta ads strategy, creative production, Drive access, or image model setup.

## Memory

- Daily notes live in `memory/YYYY-MM-DD.md`.
- Capture important client decisions, preferences, credentials locations, and operating lessons.
- Do not write secrets into memory files or chat.

## Safety

- Do not expose private client data.
- Ask before sending public messages, emails, campaigns, or destructive commands.
- Prefer recoverable moves/backups over permanent deletion.
EOF

  cat > "$workspace_dir/BOOTSTRAP.md" <<'EOF'
# BOOTSTRAP.md - First Client Onboarding Run

This workspace has been pre-seeded for a client OpenClaw agent.

This file is the one-time first-run prompt. Do this only while `BOOTSTRAP.md` exists:

1. Open and read `skills/meta-andromeda-ads-strategy/SKILL.md`.
2. Open and read `skills/ad-creative-agent/SKILL.md`.
3. Learn both files and load them as active skills for this client.
4. Review the bundled `ad-creative-agent` references as needed, especially `docs/ad-creative-agent-reference-guide.md`.
5. Keep the helper skills available for relevant tasks:
   - `skills/google-drive-service-account/SKILL.md`
   - `skills/image-model-api-keys/SKILL.md`
6. If important client context is missing, ask only the minimum useful questions.
7. Save important answers into the relevant workspace files.

If the user asks: "תקרא את ה-meta token שלך ותגיד לי לאיזה חשבונות יש לך גישה", run:

```bash
bash scripts/meta-token-accounts.sh
```

Never print the `META_API_TOKEN` value. Report only accessible account IDs, names, status, currency, and timezone.

After the first onboarding conversation is complete and the skills are understood, delete this `BOOTSTRAP.md` file. Future sessions should not repeat this onboarding read unless the user asks or the task needs those files.
EOF

  cat > "$workspace_dir/SOUL.md" <<'EOF'
# SOUL.md - Client Agent

You are a practical client assistant inside OpenClaw.

Be direct, useful, and context-aware. Learn the client's business from the local workspace files, then help them execute work without unnecessary ceremony.
EOF

  cat > "$workspace_dir/USER.md" <<'EOF'
# USER.md - Client

Client details are not filled yet.

Update this file during onboarding with:

- Client name
- What to call them
- Timezone
- Communication preferences
- Important boundaries
EOF

  cat > "$workspace_dir/TOOLS.md" <<'EOF'
# TOOLS.md - Client Tools

Record local operational notes here:

- API/key locations, without exposing secret values
- Account names
- Project paths
- Common commands
- Gotchas learned during setup

## Commands

Check which Meta ad accounts the configured token can access:

```bash
bash scripts/meta-token-accounts.sh
```

This reads `META_API_TOKEN` from the environment and never prints the token.
EOF

  cat > "$workspace_dir/scripts/meta-token-accounts.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${META_API_TOKEN:-}" ]]; then
  echo "META_API_TOKEN is not set in this OpenClaw container."
  exit 1
fi

command -v curl >/dev/null 2>&1 || {
  echo "curl is required but is not installed."
  exit 1
}

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

http_code="$(
  curl -sS -G \
    --data-urlencode "fields=id,account_id,name,account_status,currency,timezone_name,business_name" \
    --data-urlencode "limit=200" \
    --data-urlencode "access_token=${META_API_TOKEN}" \
    -o "$tmp" \
    -w "%{http_code}" \
    "https://graph.facebook.com/v20.0/me/adaccounts" || true
)"

python3 - "$http_code" "$tmp" <<'PY'
import json
import sys

http_code = sys.argv[1]
path = sys.argv[2]
raw = open(path, "r", encoding="utf-8", errors="replace").read()
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    print(f"Meta API returned HTTP {http_code}, but the response was not JSON.")
    print(raw[:1000])
    sys.exit(1)

if int(http_code or 0) >= 400 or "error" in payload:
    error = payload.get("error") if isinstance(payload, dict) else {}
    message = error.get("message") if isinstance(error, dict) else ""
    code = error.get("code") if isinstance(error, dict) else ""
    print(f"Meta API request failed. HTTP {http_code}. Code: {code}. Message: {message}")
    sys.exit(1)

accounts = payload.get("data") if isinstance(payload, dict) else None
if not accounts:
    print("No ad accounts were returned for this META_API_TOKEN.")
    sys.exit(0)

print("Accessible Meta ad accounts:")
for account in accounts:
    account_id = account.get("account_id") or str(account.get("id", "")).removeprefix("act_")
    full_id = account.get("id") or (f"act_{account_id}" if account_id else "")
    name = account.get("name") or ""
    status = account.get("account_status")
    currency = account.get("currency") or ""
    timezone = account.get("timezone_name") or ""
    business = account.get("business_name") or ""
    parts = [
        f"id={full_id}",
        f"account_id={account_id}",
        f"name={name}",
        f"status={status}",
        f"currency={currency}",
        f"timezone={timezone}",
    ]
    if business:
        parts.append(f"business={business}")
    print("- " + " | ".join(parts))
PY
EOF
  chmod +x "$workspace_dir/scripts/meta-token-accounts.sh"
}

write_project_files() {
  local dir="$1"
  local project="$2"
  local port="$3"
  local host="$4"
  local token="$5"

  mkdir -p "$dir/data/.openclaw" "$dir/data/linuxbrew" "$BACKUP_ROOT"
  write_agent_bootstrap_files "$dir/data/.openclaw/workspace"

  cat > "$dir/.env" <<EOF
COMPOSE_PROJECT_NAME=${project}
PORT=${port}
TZ=${TZ_VALUE}
TRAEFIK_HOST=${host}
OPENCLAW_GATEWAY_TOKEN=${token}
OPENCLAW_STATE_DIR=/data/.openclaw
OPENCLAW_CONFIG_PATH=/data/.openclaw/openclaw.json
OPENCLAW_WORKSPACE_DIR=/data/.openclaw/workspace

# Fill per client before production use:
# OPENAI_API_KEY=
# TELEGRAM_BOT_TOKEN=
EOF

  cat > "$dir/data/.openclaw/openclaw.json" <<'EOF'
{
  "session": {
    "dmScope": "per-channel-peer",
    "resetByType": {
      "direct": {
        "mode": "idle"
      }
    }
  }
}
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
