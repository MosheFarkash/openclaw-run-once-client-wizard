# OpenClaw Run-Once Client Wizard

Temporary provisioning wizard for a client VPS managed by GetScale.

The goal is to log into a fresh VPS, run one command, get a wizard link in the terminal, complete the client OpenClaw setup, and then remove the temporary wizard layer automatically.

The created client OpenClaw project is preserved.

## Quick Start

On the client VPS:

```bash
git clone https://github.com/MosheFarkash/openclaw-run-once-client-wizard.git /tmp/openclaw-run-once-client-wizard
cd /tmp/openclaw-run-once-client-wizard
bash bin/run-managed-client-wizard.sh --self-destruct
```

The command prints:

- a local VPS URL,
- a recommended SSH tunnel command,
- the browser URL to open from your computer.

Because the wizard binds to `127.0.0.1` by default, the secure flow is:

```bash
ssh -L 8099:127.0.0.1:8099 root@CLIENT_VPS_IP
```

Then open the URL printed by the script.

## What It Installs Temporarily

- `/root/openclaw-run-once-wizard.py`
- `/root/openclaw-run-once-oauth-chat.sh`
- `/usr/local/bin/openclaw-run-once-provision-client`
- `/usr/local/bin/openclaw-run-once-cleanup-request`
- `/usr/local/bin/openclaw-run-once-cleanup-worker`
- `openclaw-run-once-wizard.service`

With `--self-destruct`, these are removed after the final wizard step completes.

## What It Keeps

The cleanup never deletes the provisioned client stack:

- `/docker/openclaw-<slug>`
- the client `.env`,
- the client OpenClaw config at `/docker/openclaw-<slug>/data/.openclaw/openclaw.json`,
- the client agent workspace at `/docker/openclaw-<slug>/data/.openclaw/workspace`,
- the OpenClaw data volume,
- `docker-compose.yml`,
- `backup.sh`,
- the running OpenClaw container.

## VPS Requirements

- root shell access,
- Docker,
- Docker Compose plugin (`docker compose`),
- systemd,
- Python 3,
- Traefik/reverse proxy if public subdomain routing is desired.

## Notes

Remote servers cannot reliably open a browser window on your local machine. This product prints a ready link and SSH tunnel command instead.

Provisioned clients are created with `session.resetByType.direct.mode = "idle"` so direct-message sessions are not reset by the default nightly cleanup.

Provisioned clients also get a persistent agent workspace under `/data/.openclaw/workspace` with:

- `AGENTS.md` and `BOOTSTRAP.md`,
- `scripts/meta-token-accounts.sh`,
- `skills/meta-andromeda-ads-strategy/SKILL.md`,
- `skills/ad-creative-agent/SKILL.md` plus references,
- helper skills from the creative workshop bundle, including Google Drive and image model setup.

Only `BOOTSTRAP.md` tells the agent to read, learn, and load the bootstrap skills. After first onboarding, the agent deletes `BOOTSTRAP.md`; `AGENTS.md` keeps only general workspace safety/memory guidance and does not force the skill-read on every session.

The Meta account helper reads `META_API_TOKEN` from the container environment and reports accessible ad accounts without printing the token:

```bash
bash scripts/meta-token-accounts.sh
```

For public self-serve/payment-gated onboarding, use a separate Cardcom/session gate before exposing any wizard URL.
