# MEMORY.md - AI Ad Agency Pack Memory

## Operating Model
- Main agent is the agency brain.
- Each client gets an isolated client agent workspace.
- Client workspaces live under `~/.openclaw/agents/<client-slug>/`.
- Client-specific data must stay in that client workspace.
- Universal agency/campaign lessons can go into shared docs or shared skills.

## Client Agent Creation
Use:

```bash
./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Client Name" whatsapp "GROUP_ID"
```

The script creates the workspace, templates, local client skill copy, and optional group binding.
It does not restart the gateway automatically.

## WhatsApp Routing Gotcha
If explicit WhatsApp groups are configured, keep the wildcard:

```json
"groups": {
  "*": { "requireMention": true }
}
```

Without this wildcard, other groups can be silently dropped.

## Safety Rules
- Do not restart OpenClaw gateway without explicit operator approval.
- Do not print tokens or secrets.
- Do not mix data between clients.
