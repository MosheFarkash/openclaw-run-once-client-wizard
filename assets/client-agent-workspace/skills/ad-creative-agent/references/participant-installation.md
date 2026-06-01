# Participant Installation Guide

Use this when helping workshop participants install and run the skill.

## Install the Skill

1. Download or receive `ad-creative-agent.skill`.
2. Install it in OpenClaw using the OpenClaw skill installation method available in their setup.
3. Restart OpenClaw/gateway if their installation requires restart for new skills.

If they are unsure, tell them to run:

```bash
openclaw help
```

or check their OpenClaw docs/UI for skill import.

## Add API Keys

At least one image provider is required.

Recommended environment variables:

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
# or
export GEMINI_API_KEY="..."
```

Use:

- `OPENAI_API_KEY` for GPT Image 2.0.
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` for Google Gemini / Nano Banana.

Never put API keys inside the `.skill` file.

## First Prompt to Test

Participants can start with:

```text
I want to generate ad creatives for my product. Lead me through the process and create the first batch.
```

If they already have a landing page:

```text
I want to generate 5 ad creatives for this landing page: [URL]. Use the page style and create image ads.
```

If they do not have a landing page:

```text
I want to generate 5 ad creatives. The product is [describe product], the audience is [describe audience], and the offer is [describe offer].
```

## Expected Output

The agent should:

1. Ask only missing blocking questions.
2. Create or reuse a visual brief.
3. Generate and score concepts.
4. Generate images.
5. Save outputs under `/ad-creatives` or `./ad-creatives`.
6. Save a manifest for the batch.
