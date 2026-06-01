# Architecture

This repo packages the existing deterministic Hostinger/OpenClaw provisioner into an ephemeral product.

## Flow

1. Operator SSHs into a client VPS.
2. Operator clones this repo into `/tmp`.
3. Operator runs `bin/run-managed-client-wizard.sh --self-destruct`.
4. Script installs temporary system files and starts `openclaw-run-once-wizard.service`.
5. Script prints an SSH tunnel command and a tokenized local wizard URL.
6. Operator completes the browser wizard.
7. Final wizard step schedules cleanup with `systemd-run`.
8. Cleanup removes the temporary wizard/service/package files.
9. Client OpenClaw project remains running under `/docker/openclaw-<slug>`.

## Why Cleanup Uses systemd-run

The wizard process is owned by `openclaw-run-once-wizard.service`. If it directly stopped its own service, systemd could kill the cleanup process before cleanup finished. Instead, the final wizard step asks systemd to start a separate cleanup unit a few seconds later.

## Non-Goals

- It is not a customer self-service public installer.
- It does not expose the wizard publicly by default.
- It does not delete created client OpenClaw projects.
- It does not install Docker or Traefik; the target VPS must already have them.
