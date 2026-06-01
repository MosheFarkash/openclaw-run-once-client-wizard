---
name: image-model-api-keys
description: Guide users step-by-step through getting OpenAI and Google Gemini API keys for image generation models, including GPT Image / GPT Image 2 and Gemini image models such as Nano Banana; use for API key onboarding, billing setup, console navigation, safe storage, and verification.
---

# Image Model API Keys Setup

Use this skill when a user needs help getting API keys for image generation providers:

- OpenAI API key for GPT Image / GPT Image 2 image generation.
- Google Gemini API key for Gemini image models, including Nano Banana / Gemini image generation models.

The goal is to guide a non-technical user calmly through account setup, billing, key creation, safe storage, and a simple verification step.

## Core principles

- Do **not** ask the user to paste API keys into normal chat unless they explicitly accept the risk and the channel is trusted.
- Prefer: save the key into the app/settings/secrets manager directly.
- Explain that API keys are like passwords.
- Guide one provider at a time unless the user explicitly asks for both together.
- If the user gets stuck, ask for a screenshot and tell them exactly what to click next.
- Mention billing clearly: image generation usually requires paid API billing/credits, even if the user has a ChatGPT/Gemini subscription.

## Client-facing explanation

Use this framing:

> To let OpenClaw generate images, you need to give it API access to the image model provider. This is separate from your ChatGPT or Gemini chat subscription. We’ll create an API key, store it securely, and use it only for the image-generation feature.

## OpenAI API key setup — GPT Image / GPT Image 2

### What the user needs

- An OpenAI account.
- API billing enabled or credits available.
- Access to the desired image model in the OpenAI API.

### Step-by-step

1. Go to the OpenAI Platform:

   ```text
   https://platform.openai.com/
   ```

2. Sign in with the Google/email account you want to use for API billing.

3. Open the API keys page:

   ```text
   https://platform.openai.com/api-keys
   ```

   Or click:

   - Dashboard / Platform
   - API keys
   - Create new secret key

4. Create a new key:

   - Click **Create new secret key**.
   - Name it something clear, e.g. `OpenClaw Image Generation`.
   - If OpenAI asks for project selection, choose the relevant project or create a new one.
   - Copy the key immediately. OpenAI may show it only once.

5. Confirm billing is active:

   ```text
   https://platform.openai.com/settings/organization/billing/overview
   ```

   Or click:

   - Settings
   - Billing
   - Add payment method / Buy credits / Set budget

6. Optional but recommended: set a spend limit/budget.

   - Settings → Limits / Billing limits
   - Set a monthly budget that matches the user's comfort level.

7. Store the key in OpenClaw/app settings.

   Recommended secret name:

   ```text
   OPENAI_API_KEY
   ```

8. Verify the model name expected by the app.

   Common image model names may include:

   ```text
   gpt-image-1
   gpt-image-2
   ```

   Use the exact model ID supported by the app/provider configuration.

### Common OpenAI issues

- **ChatGPT Plus/Pro is not enough**: API billing is separate from ChatGPT subscription.
- **Key copied but image generation fails**: billing may not be enabled, credits may be missing, or the model ID may be unsupported.
- **Cannot see API keys**: user may be in the wrong workspace/project or lacks org permissions.
- **Rate limit / quota exceeded**: add credits, increase limits, or wait for quota reset.

## Google Gemini API key setup — Nano Banana / Gemini image models

Google may expose Gemini API keys through either Google AI Studio or Google Cloud/Vertex AI. For most non-technical users, start with Google AI Studio.

### Option A — Google AI Studio API key (recommended first path)

Use this path when the app supports a Gemini API key directly.

1. Go to Google AI Studio:

   ```text
   https://aistudio.google.com/
   ```

2. Sign in with the Google account you want to use.

3. Open API keys:

   ```text
   https://aistudio.google.com/app/apikey
   ```

   Or click:

   - Get API key
   - Create API key

4. Create/select a Google Cloud project.

   - If prompted, choose an existing project or create a new one.
   - Suggested name: `OpenClaw Gemini Images`.

5. Click **Create API key**.

6. Copy the key.

7. Store the key in OpenClaw/app settings.

   Recommended secret names, depending on app convention:

   ```text
   GOOGLE_API_KEY
   GEMINI_API_KEY
   ```

8. Confirm billing/quota if needed.

   Some usage tiers/models require billing enabled in Google Cloud:

   ```text
   https://console.cloud.google.com/billing
   ```

9. Verify the model name expected by the app.

   Nano Banana commonly refers to Gemini image generation/editing models. Depending on provider config, model IDs may look like:

   ```text
   gemini-2.5-flash-image
   gemini-2.5-flash-image-preview
   ```

   Use the exact model ID supported by the app/provider configuration.

### Option B — Google Cloud / Vertex AI path

Use this path if the app uses Vertex AI, service accounts, or Google Cloud authentication instead of a simple AI Studio API key.

1. Go to Google Cloud Console:

   ```text
   https://console.cloud.google.com/
   ```

2. Create/select a project:

   - Project name: `OpenClaw Gemini Images`.

3. Enable billing:

   - Billing → Link billing account.

4. Enable the required APIs:

   - APIs & Services → Library
   - Enable **Vertex AI API**
   - If needed, also enable **Generative Language API**

5. Create credentials:

   - For API-key based apps: APIs & Services → Credentials → Create credentials → API key.
   - For service-account based apps: IAM & Admin → Service Accounts → Create service account → create JSON key.

6. Restrict the key where possible:

   - Application restrictions: as appropriate for backend usage.
   - API restrictions: restrict to Generative Language API / Vertex AI API if supported.

7. Store credentials in OpenClaw/app settings.

### Common Google issues

- **Wrong Google account**: the user is logged into a personal account but billing/project is under Workspace, or vice versa.
- **API key created but model fails**: billing/quota may not be enabled, or the app is using Vertex when the key is for AI Studio only.
- **Model not found**: model name changed or is region/provider specific. Check the app's supported model list.
- **Permission denied**: API not enabled, billing not linked, or key is restricted too tightly.

## Safe storage guidance

Tell the user:

> API keys are like passwords. Don’t post them publicly, don’t put them in screenshots, and don’t send them in group chats. Store them only in the app’s secret settings or a secure password manager.

Recommended environment variable names:

```text
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
GEMINI_API_KEY=...
```

If editing an OpenClaw server directly, prefer a secrets file such as:

```bash
~/.secrets.env
```

with restrictive permissions:

```bash
chmod 600 ~/.secrets.env
```

## Verification checklist

After key setup, verify:

- OpenAI key exists and billing is active.
- Google/Gemini key exists and billing/quota is active if required.
- The app secret names match the app config.
- The selected image model IDs are supported.
- A tiny test image generation works.
- Spending limits/budgets are set.

## Suggested guided conversation

When guiding a client, use this flow:

1. Ask: “Which provider do you want to set up first — OpenAI or Gemini?”
2. Give the direct link for that provider.
3. Ask them to tell you when they are signed in.
4. Give the next click path.
5. When the key is created, tell them where to paste/store it securely.
6. Run or request a small test.
7. Help them set a budget limit.

## Short version for clients

### OpenAI

1. Go to `https://platform.openai.com/api-keys`.
2. Sign in.
3. Click **Create new secret key**.
4. Name it `OpenClaw Image Generation`.
5. Copy it once and save it securely.
6. Make sure billing is enabled at `https://platform.openai.com/settings/organization/billing/overview`.
7. Add it to OpenClaw as `OPENAI_API_KEY`.

### Gemini

1. Go to `https://aistudio.google.com/app/apikey`.
2. Sign in.
3. Click **Create API key**.
4. Choose/create a project.
5. Copy the key and save it securely.
6. If required, enable billing in Google Cloud.
7. Add it to OpenClaw as `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
