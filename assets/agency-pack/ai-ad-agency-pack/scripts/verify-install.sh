#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
WORKSPACE="${WORKSPACE:-$OPENCLAW_HOME/workspace}"
PACK_DIR="$WORKSPACE/packs/ai-ad-agency-pack"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

[ -d "$WORKSPACE" ] || fail "workspace missing: $WORKSPACE"
[ -d "$OPENCLAW_HOME" ] || fail "openclaw home missing: $OPENCLAW_HOME"

# Main agent files
for f in AGENTS.md SOUL.md IDENTITY.md USER.md MEMORY.md TOOLS.md HEARTBEAT.md; do
  [ -f "$WORKSPACE/$f" ] || fail "missing main workspace file: $WORKSPACE/$f"
done
ok "main workspace files exist"

grep -q "AI Ad Agency" "$WORKSPACE/AGENTS.md" || fail "AGENTS.md does not look like Agency Pack AGENTS.md"
grep -q "agency" "$WORKSPACE/SOUL.md" || fail "SOUL.md does not look like Agency Pack SOUL.md"
ok "main identity files look correct"

# Pack files
[ -d "$PACK_DIR" ] || fail "pack dir missing: $PACK_DIR"
[ -x "$PACK_DIR/scripts/create-client-agent.sh" ] || fail "create-client-agent.sh missing or not executable"
[ -f "$PACK_DIR/docs/AGENCY_PACK_SOP.md" ] || fail "AGENCY_PACK_SOP.md missing"
[ -f "$PACK_DIR/docs/CLIENT_ONBOARDING_FLOW.md" ] || fail "CLIENT_ONBOARDING_FLOW.md missing"
[ -d "$PACK_DIR/templates/client-agent" ] || fail "client-agent template missing"
ok "agency pack structure exists"

# Template completeness
for f in AGENTS.md SOUL.md USER.md MEMORY.md config.yaml IDENTITY.md HEARTBEAT.md TOOLS.md; do
  [ -f "$PACK_DIR/templates/client-agent/$f" ] || fail "missing client template file: $f"
done
ok "client-agent template complete"

# Global skill install
[ -d "$OPENCLAW_HOME/skills/client-ads-manager" ] || fail "global skill missing: $OPENCLAW_HOME/skills/client-ads-manager"
[ -f "$OPENCLAW_HOME/skills/client-ads-manager/SKILL.md" ] || fail "global skill SKILL.md missing"
[ -f "$OPENCLAW_HOME/skills/client-ads-manager/COLLECTIVE.md" ] || fail "global skill COLLECTIVE.md missing"
ok "global client-ads-manager skill installed"

# Script syntax
bash -n "$PACK_DIR/scripts/create-client-agent.sh" || fail "create-client-agent.sh syntax failed"
ok "create-client-agent.sh syntax valid"

# OpenClaw CLI visibility, if available
if command -v openclaw >/dev/null 2>&1; then
  openclaw --version >/dev/null 2>&1 || fail "openclaw CLI exists but does not run"
  ok "openclaw CLI runs"

  if openclaw status >/tmp/openclaw-agency-pack-status.txt 2>&1; then
    ok "openclaw status runs"
  else
    echo "WARN: openclaw status failed; gateway may still be restarting"
    tail -40 /tmp/openclaw-agency-pack-status.txt || true
  fi
else
  echo "WARN: openclaw CLI not found in PATH; file-level install verified only"
fi

echo ""
echo "AI Ad Agency Pack verification passed."
echo "Workspace: $WORKSPACE"
echo "OpenClaw home: $OPENCLAW_HOME"
echo "Next: open the bot and ask: 'מה התפקיד שלך ומה הפאק שמותקן כאן?'"
