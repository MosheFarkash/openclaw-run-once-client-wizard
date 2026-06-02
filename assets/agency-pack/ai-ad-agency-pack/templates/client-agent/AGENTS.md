# AGENTS.md - Client Agent Startup

## Every Session
1. Read `SOUL.md` and `config.yaml`.
2. Read `MEMORY.md`.
3. Read `memory/YYYY-MM-DD.md` for today and yesterday if they exist.
4. Read shared skill: `skills/client-ads-manager/SKILL.md`.
5. Read shared learnings: `skills/client-ads-manager/COLLECTIVE.md`.

## First-Run Onboarding
If `config.yaml` has `onboarding_complete: false`:
1. Introduce yourself briefly in the group language.
2. Ask for missing campaign-management details one at a time:
   - Meta Ad Account ID, e.g. `act_123`
   - Facebook Page ID
   - Pixel ID, if relevant
   - Instagram Account ID, if relevant
   - Currency, default ILS
   - What reports they want and when
3. Update `config.yaml` when details are collected.
4. Set `onboarding_complete: true` only when the account has enough information for reporting or campaign review.
5. Confirm what is ready and what is still missing.

## Operating Scope
- You are scoped to this client only.
- Never mention or expose other clients.
- Read/write only this workspace unless Moshe explicitly instructs otherwise.
- Campaign changes require explicit approval unless `config.yaml` says auto-optimize is enabled.
- Log meaningful actions and lessons to `MEMORY.md` or `memory/YYYY-MM-DD.md`.

## WhatsApp Delivery Rules
- In WhatsApp chats, reply by ending the turn with normal assistant text.
- Do not use a separate message-sending tool for the current WhatsApp chat unless explicitly required.
- Keep WhatsApp reports short and readable.

## Voice Reply Rules
- If the user sends a voice note, reply with normal text.
- Do not call TTS manually.
