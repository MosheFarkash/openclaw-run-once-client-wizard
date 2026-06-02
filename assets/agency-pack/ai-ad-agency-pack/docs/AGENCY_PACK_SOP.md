# AI Ad Agency Pack SOP

## Purpose
This pack turns a fresh OpenClaw install into a lightweight agency operating system:

- one main/agency agent
- one isolated client agent per client
- one workspace per client
- WhatsApp/Telegram group routing per client
- shared campaign-management skill

## What this pack includes

```text
workspace-root/                 # main agent AGENTS/SOUL/IDENTITY/MEMORY files
templates/client-agent/        # files copied into each client workspace
skills/client-ads-manager/     # shared campaign/reporting methodology
scripts/create-client-agent.sh # creates client workspace + optional group binding
docs/                          # operating instructions
```

## What this pack intentionally excludes

- Meta Ads Client Connect
- Meta Ads Builder Portable
- meta-atomic-test-campaign
- meta-ads-tags

This pack is for agency/client workspace structure and campaign-management support, not full Meta campaign upload automation. It also includes main-agent identity/memory files for the agency operator workspace.

## Standard client creation flow

From the OpenClaw workspace where this pack is installed:

```bash
./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Client Name" whatsapp "120363...@g.us"
```

If the group ID is not known yet:

```bash
./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Client Name" whatsapp
```

Then add/bind the group later.

## What the script does

1. Creates a slug from the client name.
2. Creates a workspace:

```text
~/.openclaw/agents/<client-slug>/
```

3. Creates:

```text
AGENTS.md
SOUL.md
USER.md
MEMORY.md
IDENTITY.md
HEARTBEAT.md
TOOLS.md
config.yaml
memory/
secrets/keys.md
skills/client-ads-manager/
sessions/
tmp/
```

4. Registers the agent with OpenClaw if the CLI is available.
5. Patches `openclaw.json` with:
   - agent workspace
   - model
   - group mention patterns
   - optional group binding
6. For WhatsApp, ensures the `channels.whatsapp.groups["*"]` wildcard exists so other groups are not silently blocked.

## What the script does not do

- It does not restart the gateway automatically.
- It does not send messages to the client.
- It does not add API keys.
- It does not activate campaigns.

Restart manually only when safe:

```bash
openclaw gateway restart
```

## Client workspace rule
Each client agent must keep all client-specific context inside its own workspace:

```text
~/.openclaw/agents/<client-slug>/
```

Client-specific memory goes in:

```text
MEMORY.md
memory/YYYY-MM-DD.md
config.yaml
secrets/keys.md
```

Universal campaign-management lessons go in:

```text
skills/client-ads-manager/COLLECTIVE.md
```

## Recommended operating model

- Main agency agent: creates clients, audits processes, coordinates work.
- Client agent: lives in the client group and handles only that client.
- Client data never crosses between client workspaces.
