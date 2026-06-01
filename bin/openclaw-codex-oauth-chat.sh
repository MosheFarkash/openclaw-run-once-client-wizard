#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./openclaw-codex-oauth-chat.sh start
  ./openclaw-codex-oauth-chat.sh finish CALLBACK_URL
  ./openclaw-codex-oauth-chat.sh device-code

Purpose:
  Run OpenAI Codex auth for an OpenClaw instance from chat.

Chat workflow:
  1. Ask the agent to run: ./openclaw-codex-oauth-chat.sh start
  2. The script prints an OAuth URL.
  3. Open the URL locally, sign in, and copy the final browser URL.
     It usually starts with: http://localhost:<port>/auth/callback?...
  4. Send that full callback URL back to the agent.
  5. Ask the agent to run:
     ./openclaw-codex-oauth-chat.sh finish '<callback-url>'

No account email, chat id, bot name, server path, or local-user-specific value is
embedded in this script.
USAGE
}

strip_ansi() {
  sed -E $'s/\x1B\\[[0-9;?]*[ -/]*[@-~]//g' | tr -d '\r'
}

require_openclaw() {
  if ! command -v openclaw >/dev/null 2>&1; then
    echo "Missing 'openclaw' command in PATH." >&2
    exit 1
  fi
}

require_script_command() {
  if ! command -v script >/dev/null 2>&1; then
    echo "Missing 'script' command. Install util-linux, or run manually:" >&2
    echo "openclaw models auth login --provider openai-codex --method oauth --set-default" >&2
    exit 1
  fi
}

start_oauth() {
  require_openclaw
  require_script_command

  local auth_command tmpdir status_file fifo auth_pid
  auth_command="openclaw models auth login --provider openai-codex --method oauth --set-default"
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  status_file="$tmpdir/status"
  fifo="$tmpdir/output.fifo"
  mkfifo "$fifo"

  (
    set +e
    script -qefc "$auth_command" /dev/null >"$fifo" 2>&1
    echo "$?" >"$status_file"
  ) &
  auth_pid=$!

  while IFS= read -r raw_line; do
    printf '%s\n' "$raw_line"

    local clean_line
    clean_line="$(printf '%s' "$raw_line" | strip_ansi)"

    if [[ "$clean_line" =~ https://auth\.openai\.com/oauth/authorize[^[:space:]]+ ]]; then
      cat <<EOF

=== OAUTH URL - SEND THIS TO THE USER ===
${BASH_REMATCH[0]}
=== END OAUTH URL ===

After sign-in, the user should send back the full final browser URL, usually:
http://localhost:<port>/auth/callback?code=...&state=...

Then run:
./openclaw-codex-oauth-chat.sh finish '<that-full-url>'

EOF
    fi
  done <"$fifo"

  wait "$auth_pid" || true
  exit "$(cat "$status_file" 2>/dev/null || echo 1)"
}

finish_oauth() {
  local callback_url="${1:-}"
  if [[ -z "$callback_url" ]]; then
    echo "Missing CALLBACK_URL." >&2
    usage >&2
    exit 2
  fi

  if [[ ! "$callback_url" =~ ^http://localhost:[0-9]+/auth/callback\? ]]; then
    echo "Refusing unexpected callback URL. Expected http://localhost:<port>/auth/callback?..." >&2
    exit 2
  fi

  curl -fsS "$callback_url" >/dev/null
  echo "OAuth callback delivered. Wait for the original start process to finish."
}

device_code() {
  require_openclaw
  require_script_command
  script -qefc "openclaw models auth login --provider openai-codex --method device-code --set-default" /dev/null
}

cmd="${1:-}"
case "$cmd" in
  start)
    shift
    start_oauth "$@"
    ;;
  finish)
    shift
    finish_oauth "$@"
    ;;
  device-code)
    shift
    device_code "$@"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
