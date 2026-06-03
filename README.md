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

## Agency Pack Quick Start

Use this variant when the created OpenClaw should become an AI Ad Agency
workspace automatically after OAuth and Telegram pairing.

```bash
rm -rf /tmp/openclaw-run-once-client-wizard
git clone https://github.com/MosheFarkash/openclaw-run-once-client-wizard.git /tmp/openclaw-run-once-client-wizard
cd /tmp/openclaw-run-once-client-wizard
bash bin/run-agency-client-wizard.sh --self-destruct
```

The agency wizard uses this release by default:

```text
https://github.com/MosheFarkash/ai-ad-agency-pack/releases/download/v0.1.0/ai-ad-agency-pack-0.1.0.tgz
```

Override it with `AGENCY_PACK_URL` when releasing a new pack version.

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

For public self-serve/payment-gated onboarding, use a separate Cardcom/session gate before exposing any wizard URL.
