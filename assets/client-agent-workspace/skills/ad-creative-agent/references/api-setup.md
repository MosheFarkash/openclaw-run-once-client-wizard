# API Setup

The agent can generate images through two supported image providers:

1. OpenAI image model, preferably GPT Image 2.0.
2. Google Gemini image model, referred to in the workshop as Nano Banana.

## Required API Keys

The user must provide at least one of these:

- `OPENAI_API_KEY` for OpenAI / GPT Image.
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` for Google Gemini / Nano Banana.

If both are available, prefer this routing:

- Use GPT Image 2.0 as the preferred final production model for polished ad images, typography-sensitive outputs, and clean commercial design.
- Use Nano Banana 2 / fast Gemini for cheap, fast draft concepts and broad exploration.
- Use Nano Banana Pro / stronger Gemini for final production when Google image generation is preferred or GPT Image is unavailable.

## Before Generating Images

Check whether image generation is available in the current OpenClaw environment.

If using OpenClaw's native image tool, list available providers/models when possible and choose the matching provider.

If no provider is configured, ask the user for the missing API key and explain exactly which key is needed.

Do not ask for both keys if one provider is enough for the current task.

## Safe Key Handling

- Never paste API keys into public prompts, final outputs, generated creative files, or manifests.
- Prefer environment variables or OpenClaw provider configuration.
- If the user sends a key in chat, use it only for setup/configuration and do not repeat it back.
- Do not store keys inside the skill package.
- Do not commit keys into reference files, scripts, manifests, or generated outputs.

## Setup Guidance for Workshop Participants

Tell participants to add keys to their OpenClaw configuration or environment according to their installation method.

Recommended environment variable names:

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
# or
export GEMINI_API_KEY="..."
```

After adding keys, restart the OpenClaw gateway/app if their setup requires it.

## Provider Selection Checklist

Before image generation, determine:

1. Which providers are available: OpenAI, Gemini, or both.
2. Which model the user wants: GPT Image 2.0 or Nano Banana.
3. Desired image count.
4. Aspect ratio/format.
5. Whether this is new generation or edit/variation from a reference image.

## Fallback Behavior

- If OpenAI is unavailable but Gemini is available, use Gemini/Nano Banana.
- If Gemini is unavailable but OpenAI is available, use GPT Image.
- If neither is available, stop and ask for one API key before continuing. If only the cheaper draft model is available, explain that outputs should be treated as draft concepts unless a final-quality model is configured.

## API Key Setup Handoff

If the user needs help finding, creating, billing, storing, or verifying OpenAI/Gemini image API keys, refer to the dedicated skill:

```text
skills/image-model-api-keys/
```

Use that skill for:

- OpenAI Platform API key creation.
- OpenAI billing/credits setup.
- Gemini / Google AI Studio API key creation.
- Gemini billing/quota issues.
- Safe storage instructions.
- Verification checklist and troubleshooting.

Do not duplicate the full API-key walkthrough here; this skill should only decide whether keys are available and which provider/model to use.
