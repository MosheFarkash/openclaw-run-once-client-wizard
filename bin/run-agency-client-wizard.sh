#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export SERVICE_NAME="${SERVICE_NAME:-openclaw-run-once-agency-wizard.service}"
export TOKEN_FILE="${TOKEN_FILE:-/root/openclaw-run-once-agency-wizard-token}"
export ENV_FILE="${ENV_FILE:-/root/openclaw-run-once-agency-wizard.env}"
export AGENCY_PACK_URL="${AGENCY_PACK_URL:-https://github.com/MosheFarkash/ai-ad-agency-pack/releases/download/v0.1.0/ai-ad-agency-pack-0.1.0.tgz}"

exec bash "$SCRIPT_DIR/run-managed-client-wizard.sh" "$@"
