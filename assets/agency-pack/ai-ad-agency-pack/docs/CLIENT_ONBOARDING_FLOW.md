# Client Onboarding Flow

## Goal
Create a new client agent that can sit inside the client's WhatsApp/Telegram group, remember client-specific context, and help with campaign reporting/recommendations.

## Required inputs

Minimum:

- Client name
- Channel: `whatsapp` or `telegram`
- Group ID, if already known

Later during onboarding:

- Meta Ad Account ID(s)
- Facebook Page ID
- Pixel ID, if relevant
- Instagram Account ID, if relevant
- Currency
- Report schedule
- What metrics matter to the client

## Step 1 — Create the client workspace

```bash
./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Client Name" whatsapp "GROUP_ID"
```

Example:

```bash
./packs/ai-ad-agency-pack/scripts/create-client-agent.sh "Invested" whatsapp "120363403002923620@g.us"
```

## Step 2 — Review generated files

Check:

```bash
~/.openclaw/agents/<client-slug>/config.yaml
~/.openclaw/agents/<client-slug>/MEMORY.md
```

Add any known client details before first use.

## Step 3 — Restart gateway when safe

The script writes config, but routing changes require a gateway restart.

```bash
openclaw gateway restart
```

Do this only when no important sessions are mid-task.

## Step 4 — Trigger onboarding in the group

In the client group, mention the bot, for example:

```text
@clawd היי, תתחיל אונבורדינג ללקוח הזה
```

The client agent should read `config.yaml`. If `onboarding_complete: false`, it asks for missing details.

## Step 5 — Complete config

The agent should collect details and update:

```yaml
onboarding_complete: true
meta_ads:
  accounts:
    - account_id: "act_..."
      name: "..."
  page_id: "..."
  pixel_id: "..."
  ig_account_id: "..."
```

## Step 6 — First report/test

Ask in the group:

```text
@clawd תן לי דוח קצר על הקמפיינים הפעילים
```

If data access is missing, the agent should say exactly what is missing.

## Done state

A client is fully onboarded when:

- The group routes to the correct client agent.
- The agent answers only about that client.
- `config.yaml` has the key account details.
- `MEMORY.md` includes client-specific preferences.
- A first report/test response succeeds or clearly identifies the missing access.
