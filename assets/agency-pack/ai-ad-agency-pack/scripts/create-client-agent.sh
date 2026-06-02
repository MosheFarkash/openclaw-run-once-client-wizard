#!/usr/bin/env bash
set -euo pipefail

# create-client-agent.sh — Create an isolated OpenClaw client agent workspace and optional group binding.
# Usage:
#   ./scripts/create-client-agent.sh "Client Name" whatsapp "120...@g.us"
#   ./scripts/create-client-agent.sh "Client Name" whatsapp
#
# Notes:
# - Does NOT restart the gateway automatically.
# - Does NOT edit secrets.
# - Creates workspace, registers agent, and optionally adds a binding.

CLIENT_NAME="${1:?Usage: create-client-agent.sh <client-name> <channel> [group-id]}"
CHANNEL="${2:?Usage: create-client-agent.sh <client-name> <channel> [group-id]}"
GROUP_ID="${3:-}"

if [[ "$CHANNEL" != "whatsapp" && "$CHANNEL" != "telegram" ]]; then
  echo "ERROR: channel must be whatsapp or telegram" >&2
  exit 1
fi

OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
AGENTS_DIR="${AGENTS_DIR:-$OPENCLAW_HOME/agents}"
PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$PACK_DIR/templates/client-agent"
SHARED_SKILL_DIR="$PACK_DIR/skills/client-ads-manager"
MODEL="${OPENCLAW_AGENT_MODEL:-codex/gpt-5.5}"
TODAY="$(date +%Y-%m-%d)"

slugify() {
  python3 - "$1" <<'PY'
import re, sys, unicodedata
s=sys.argv[1].strip().lower()
s=unicodedata.normalize('NFKD', s)
s=re.sub(r'\s+', '-', s)
s=re.sub(r'[^a-z0-9\u0590-\u05ff-]+', '', s)
s=s.strip('-')
print(s or 'client')
PY
}

CLIENT_SLUG="$(slugify "$CLIENT_NAME")"
AGENT_DIR="$AGENTS_DIR/$CLIENT_SLUG"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "ERROR: missing template dir: $TEMPLATE_DIR" >&2
  exit 1
fi

if [[ -e "$AGENT_DIR" ]]; then
  echo "ERROR: agent workspace already exists: $AGENT_DIR" >&2
  exit 1
fi

echo "Creating client agent"
echo "  Client:   $CLIENT_NAME"
echo "  Slug:     $CLIENT_SLUG"
echo "  Channel:  $CHANNEL"
echo "  Group ID: ${GROUP_ID:-<none>}"
echo "  Workspace:$AGENT_DIR"
echo ""

mkdir -p "$AGENT_DIR"/{memory,secrets,skills/client-ads-manager,sessions,tmp}

render() {
  local src="$1"
  local dst="$2"
  sed -e "s|{{CLIENT_NAME}}|$CLIENT_NAME|g" \
      -e "s|{{CLIENT_SLUG}}|$CLIENT_SLUG|g" \
      -e "s|{{DATE}}|$TODAY|g" \
      "$src" > "$dst"
}

for f in AGENTS.md SOUL.md USER.md MEMORY.md config.yaml IDENTITY.md HEARTBEAT.md TOOLS.md; do
  render "$TEMPLATE_DIR/$f" "$AGENT_DIR/$f"
done

# Copy shared skill into the client workspace so the agent can read it even if global skills are unavailable.
cp "$SHARED_SKILL_DIR/SKILL.md" "$AGENT_DIR/skills/client-ads-manager/SKILL.md"
cp "$SHARED_SKILL_DIR/COLLECTIVE.md" "$AGENT_DIR/skills/client-ads-manager/COLLECTIVE.md"

cat > "$AGENT_DIR/secrets/keys.md" <<'EOF'
# Client Secrets

# Store client-specific credentials here.
# Never paste this file into chat.

## Meta Ads
# Access Token:
EOF
chmod 700 "$AGENT_DIR/secrets"
chmod 600 "$AGENT_DIR/secrets/keys.md"

# Register agent if OpenClaw CLI is available.
if command -v openclaw >/dev/null 2>&1; then
  echo "Registering OpenClaw agent..."
  openclaw agents add "$CLIENT_SLUG" \
    --workspace "$AGENT_DIR" \
    --model "$MODEL" \
    --non-interactive || true
else
  echo "WARNING: openclaw CLI not found; workspace created but agent not registered." >&2
fi

# Safely patch openclaw.json for groupChat + optional binding.
CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-$OPENCLAW_HOME/openclaw.json}"
if [[ -f "$CONFIG_PATH" ]]; then
  python3 - "$CONFIG_PATH" "$CLIENT_SLUG" "$AGENT_DIR" "$MODEL" "$CHANNEL" "$GROUP_ID" <<'PY'
import json, sys, pathlib
path, agent_id, workspace, model, channel, group_id = sys.argv[1:]
p=pathlib.Path(path)
config=json.loads(p.read_text())
config.setdefault('agents', {}).setdefault('list', [])
agents=config['agents']['list']
agent=next((a for a in agents if a.get('id')==agent_id), None)
if not agent:
    agent={'id': agent_id}
    agents.append(agent)
agent['workspace']=workspace
agent['model']=model
agent['groupChat']={'mentionPatterns':['clawd','קלאוד','קלוד','claude'], 'historyLimit':50}

if group_id:
    config.setdefault('bindings', [])
    binding={
        'agentId': agent_id,
        'match': {'channel': channel, 'peer': {'kind':'group', 'id': group_id}}
    }
    config['bindings']=[b for b in config['bindings'] if not (b.get('agentId')==agent_id and b.get('match',{}).get('channel')==channel)]
    config['bindings'].append(binding)

    # WhatsApp group gating gotcha: preserve wildcard if groups map exists or if adding explicit group.
    if channel == 'whatsapp':
        w=config.setdefault('channels', {}).setdefault('whatsapp', {})
        groups=w.setdefault('groups', {})
        groups.setdefault('*', {'requireMention': True})
        groups.setdefault(group_id, {'requireMention': True})

p.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
PY
else
  echo "WARNING: config not found at $CONFIG_PATH; binding not written." >&2
fi

echo ""
echo "Done."
echo "Workspace: $AGENT_DIR"
if [[ -n "$GROUP_ID" ]]; then
  echo "Binding:   $CHANNEL group $GROUP_ID -> $CLIENT_SLUG"
fi
echo ""
echo "Next steps:"
echo "1. Review $AGENT_DIR/config.yaml"
echo "2. Restart OpenClaw gateway when safe."
echo "3. Mention the bot in the client group to start onboarding."
