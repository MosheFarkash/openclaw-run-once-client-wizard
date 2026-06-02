# AI Ad Agency Pack

OpenClaw pack for running an AI ad agency operating system.

It installs two layers:

- Main-agent workspace identity and operating files.
- Client-agent onboarding template, scripts, docs, and shared client ads management skill.

## Contents

```text
workspace-root/                 Main OpenClaw workspace files
templates/client-agent/         Template for isolated client agents
skills/client-ads-manager/      Shared skill copied into each client agent
scripts/create-client-agent.sh  Creates a new client agent workspace
scripts/verify-install.sh       Verifies installation inside Docker/OpenClaw
docs/                           Install, SOP, and onboarding docs
```

## Build

```bash
./scripts/build-release.sh
```

The release artifact is written to:

```text
dist/ai-ad-agency-pack-<version>.tgz
```

The archive expands into:

```text
packs/ai-ad-agency-pack/
```

That shape is intentional because the Docker installer extracts it directly into the OpenClaw workspace.

## Install

See:

```text
docs/INSTALL_IN_DOCKER.md
```

