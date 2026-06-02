# Install AI Ad Agency Pack in Hostinger Docker OpenClaw

This installs two layers:

1. Main workspace files:
   - AGENTS.md
   - SOUL.md
   - IDENTITY.md
   - USER.md
   - MEMORY.md
   - TOOLS.md
   - HEARTBEAT.md
2. Agency pack files:
   - packs/ai-ad-agency-pack/
   - global skill: skills/client-ads-manager/

## Hostinger default paths

```bash
OPENCLAW_HOME="/data/.openclaw"
WORKSPACE="/data/.openclaw/workspace"
```

## Install + verify command

```bash
PACK_URL="https://your-domain.com/ai-ad-agency-pack.tgz"
CONTAINER="openclaw-XXXX-openclaw-1"
OPENCLAW_HOME="/data/.openclaw"
WORKSPACE="/data/.openclaw/workspace"

curl -fsSL "$PACK_URL" -o /tmp/ai-ad-agency-pack.tgz \
&& docker cp /tmp/ai-ad-agency-pack.tgz "$CONTAINER":/tmp/ai-ad-agency-pack.tgz \
&& docker exec "$CONTAINER" sh -lc "set -e; OPENCLAW_HOME='$OPENCLAW_HOME'; WORKSPACE='$WORKSPACE'; TS=\$(date +%Y%m%d-%H%M%S); mkdir -p \"\$OPENCLAW_HOME/backups\" \"\$WORKSPACE\" \"\$OPENCLAW_HOME/skills\"; tar -czf \"\$OPENCLAW_HOME/backups/pre-agency-pack-\$TS.tgz\" -C \"\$WORKSPACE\" AGENTS.md SOUL.md USER.md IDENTITY.md MEMORY.md TOOLS.md HEARTBEAT.md packs 2>/dev/null || true; tar -xzf /tmp/ai-ad-agency-pack.tgz -C \"\$WORKSPACE\"; cp -a \"\$WORKSPACE/packs/ai-ad-agency-pack/workspace-root/.\" \"\$WORKSPACE/\"; cp -a \"\$WORKSPACE/packs/ai-ad-agency-pack/skills/client-ads-manager\" \"\$OPENCLAW_HOME/skills/\"; chmod +x \"\$WORKSPACE/packs/ai-ad-agency-pack/scripts/\"*.sh; OPENCLAW_HOME=\"\$OPENCLAW_HOME\" WORKSPACE=\"\$WORKSPACE\" \"\$WORKSPACE/packs/ai-ad-agency-pack/scripts/verify-install.sh\"" \
&& docker restart "$CONTAINER"
```

## Post-restart smoke test

After restart, message the bot:

```text
מה התפקיד שלך ומה הפאק שמותקן כאן?
```

Expected answer: it should identify itself as an agency/main operating agent and mention client agent workspaces / AI Ad Agency Pack.

Then test client creation without a real group:

```bash
docker exec -it "$CONTAINER" sh -lc 'cd /data/.openclaw/workspace && ./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Test Client" whatsapp'
```

If it creates `/data/.openclaw/agents/test-client/`, the pack is operational.
