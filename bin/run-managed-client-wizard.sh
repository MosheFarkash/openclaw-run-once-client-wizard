#!/usr/bin/env bash
set -euo pipefail

BIND="${BIND:-127.0.0.1}"
PORT="${PORT:-8099}"
SERVICE_NAME="${SERVICE_NAME:-openclaw-run-once-wizard.service}"
TOKEN_FILE="${TOKEN_FILE:-/root/openclaw-run-once-wizard-token}"
FORM_PATH="${FORM_PATH:-/root/openclaw-run-once-wizard.py}"
PROVISION_CMD="${PROVISION_CMD:-/usr/local/bin/openclaw-run-once-provision-client}"
OAUTH_HELPER="${OAUTH_HELPER:-/root/openclaw-run-once-oauth-chat.sh}"
CLEANUP_REQUEST="${CLEANUP_REQUEST:-/usr/local/bin/openclaw-run-once-cleanup-request}"
CLEANUP_WORKER="${CLEANUP_WORKER:-/usr/local/bin/openclaw-run-once-cleanup-worker}"
SELF_DESTRUCT=0

usage() {
  cat <<'EOF'
Run a temporary OpenClaw client provisioning wizard on a managed VPS.

Usage:
  bash bin/run-managed-client-wizard.sh --self-destruct

Options:
  --bind IP             Bind address. Default: 127.0.0.1
  --port PORT           Wizard port. Default: 8099
  --self-destruct       Remove the temporary wizard after the setup completes.
  -h, --help            Show this help.

The created OpenClaw client project under /docker/openclaw-<slug> is never
deleted by self-destruct cleanup.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

detect_public_ip() {
  local ip=""

  if [[ -n "${SSH_CONNECTION:-}" ]]; then
    # SSH_CONNECTION fields: client_ip client_port server_ip server_port.
    ip="$(awk '{print $3}' <<<"$SSH_CONNECTION")"
  fi

  if [[ -z "$ip" ]] && command -v curl >/dev/null 2>&1; then
    ip="$(curl -4fsS --max-time 3 https://api.ipify.org 2>/dev/null || true)"
  fi

  if [[ -z "$ip" ]]; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi

  if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    printf '%s\n' "$ip"
  else
    printf 'CLIENT_VPS_IP\n'
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bind)
      BIND="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --self-destruct)
      SELF_DESTRUCT=1
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

[[ "$(id -u)" == "0" ]] || die "run as root"
[[ "$PORT" =~ ^[0-9]+$ ]] || die "--port must be numeric"

need_cmd docker
docker compose version >/dev/null 2>&1 || die "docker compose plugin is required"
need_cmd python3
need_cmd systemctl

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$PACKAGE_DIR/bin/provision-openclaw-client.sh" ]] || die "missing provisioner script"
[[ -f "$PACKAGE_DIR/bin/openclaw-codex-oauth-chat.sh" ]] || die "missing OAuth helper"
[[ -f "$PACKAGE_DIR/server/openclaw-run-once-wizard.py" ]] || die "missing run-once wizard server"

install -m 755 "$PACKAGE_DIR/bin/provision-openclaw-client.sh" "$PROVISION_CMD"
install -m 755 "$PACKAGE_DIR/bin/openclaw-codex-oauth-chat.sh" "$OAUTH_HELPER"
install -m 755 "$PACKAGE_DIR/server/openclaw-run-once-wizard.py" "$FORM_PATH"

if [[ "$SELF_DESTRUCT" == "1" ]]; then
  cat > "$CLEANUP_WORKER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
slug="\${1:-}"
echo "Cleaning temporary run-once wizard for \${slug:-unknown}..."
systemctl disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
rm -f /etc/systemd/system/"$SERVICE_NAME"
systemctl daemon-reload >/dev/null 2>&1 || true
rm -f "$FORM_PATH" "$OAUTH_HELPER" "$PROVISION_CMD" "$TOKEN_FILE"
rm -f "$CLEANUP_REQUEST" "$CLEANUP_WORKER"
case "$PACKAGE_DIR" in
  /tmp/*|/root/*)
    rm -rf "$PACKAGE_DIR"
    ;;
esac
echo "Temporary wizard removed. Client project under /docker is preserved."
EOF
  chmod 755 "$CLEANUP_WORKER"

  cat > "$CLEANUP_REQUEST" <<EOF
#!/usr/bin/env bash
set -euo pipefail
slug="\${1:-}"
systemd-run --unit=openclaw-run-once-cleanup --collect --on-active=3 "$CLEANUP_WORKER" "\$slug" >/dev/null
EOF
  chmod 755 "$CLEANUP_REQUEST"
  cleanup_args_line="--cleanup-command $CLEANUP_REQUEST"
else
  cleanup_args_line=""
fi

cat > /etc/systemd/system/"$SERVICE_NAME" <<EOF
[Unit]
Description=OpenClaw Run-Once Client Wizard
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 "$FORM_PATH" --bind "$BIND" --port "$PORT" --token-file "$TOKEN_FILE" --provision-cmd "$PROVISION_CMD" --oauth-helper "$OAUTH_HELPER" $cleanup_args_line
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

python3 -m py_compile "$FORM_PATH"
TOKEN_FILE="$TOKEN_FILE" python3 - <<'PY'
from pathlib import Path
import os
import re
import secrets

path = Path(os.environ["TOKEN_FILE"])
token_re = re.compile(r"^[A-Za-z0-9_.:-]{12,}$")
if path.exists():
    token = path.read_text(encoding="utf-8").strip()
    if token_re.match(token):
        raise SystemExit(0)

path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
path.chmod(0o600)
PY
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"
systemctl is-active --quiet "$SERVICE_NAME"

token="$(cat "$TOKEN_FILE")"
local_url="http://${BIND}:${PORT}/?token=${token}"
vps_ip="$(detect_public_ip)"

printf '\nOpenClaw run-once wizard is ready.\n\n'
printf 'Local URL on the VPS:\n%s\n\n' "$local_url"
printf 'Recommended secure access from your computer:\n'
printf 'ssh -L %s:127.0.0.1:%s root@%s\n' "$PORT" "$PORT" "$vps_ip"
printf 'Then open:\nhttp://127.0.0.1:%s/?token=%s\n\n' "$PORT" "$token"

if [[ "$SELF_DESTRUCT" == "1" ]]; then
  printf 'Self-destruct is enabled: when the final wizard step completes, temporary wizard files and service will be removed.\n'
  printf 'The created OpenClaw client project under /docker/openclaw-<slug> will remain running.\n'
else
  printf 'Self-destruct is disabled: remove temporary wizard files manually when done.\n'
fi
