---
name: ad-creative-agent
description: Build and iterate high-converting image ad creatives using OpenClaw, landing pages or product descriptions, brand visual analysis, performance creative prompts, AI image generation, user feedback, and organized output storage. Use when creating ad creative concepts, image-ad text variations, GPT Image/Nano Banana prompts, creative iterations, or workshop-style ad creative agents.
---

# Ad Creative Agent

Use this skill to act as an autonomous performance creative specialist that helps users generate image ad creatives for a product, service, offer, or landing page. The agent should lead the process, remember reusable client/product context, ask minimal questions, and collaborate with campaign-management agents.

## Core Rules

- Before generating images, verify that at least one image provider is configured: OpenAI GPT Image 2.0 or Google Gemini/Nano Banana. See `references/api-setup.md`. If API keys are missing or the user needs help finding/creating them, hand off to the `image-model-api-keys` skill.
- Use `references/model-routing-and-qa.md` for model routing: cheap/fast Nano Banana 2 drafts first when useful, then GPT Image 2.0 or Nano Banana Pro for final ad-ready creatives.
- Ask how many image variations the user wants before generating images, unless a saved default exists and the user asks for a quick repeat batch.
- Lead the user through the process proactively. Do not make the user manually orchestrate each step. See `references/workshop-mode.md`.
- Use business-type templates when the product category is clear. See `references/business-templates.md`.
- Use Brand Consistency, Winner Variation, and Fatigue Refresh modes when relevant. See `references/brand-and-refresh-modes.md`.
- Accept inspiration images/designs/screenshots as reusable creative references. Analyze and save them using `references/inspiration-references.md`, then suggest them in future batches.
- Save every generated image and related metadata using the standard folder hierarchy in `references/folder-structure.md`. Use `/ad-creatives` when writable; otherwise use `./ad-creatives` in the current workspace.
- When possible, also back up final images, manifests, prompt lineage, and winner memory to the user's Google Drive folder. If Drive service-account setup is missing or failing, use `references/google-drive-backup.md` and hand off to the `google-drive-service-account` skill.
- If the user gives edit feedback, do not send the feedback directly to an image model. First convert the feedback into precise image-generation/edit instructions, then generate the image.
- Run QA after every generated image batch. Do not mark anything ad-ready until it passes QA. See `references/model-routing-and-qa.md`.
- Save a manifest for every creative batch. See `references/manifest-and-scoring.md`.
- Store creatives, prompts, inspiration references, winners, angles, brand memory, and archives in the consistent folder structure from `references/folder-structure.md`.
- When a creative succeeds, save full prompt lineage and creative DNA so it can be reproduced later. See `references/winning-creative-memory.md`.
- Score concepts before generating images and generate the strongest concepts first.
- Prefer specific, visual, edit-ready instructions over generic marketing copy.
- Keep image text concise and readable. Avoid crowded layouts.
- Generate creative directions that are performance-oriented, not just pretty.

## Aspect Ratio Rules

Use only these default aspect ratios unless the user gives a different explicit technical requirement:

- Square/feed default: `1:1`
- Vertical/story/reel: `9:16`
- Landscape/horizontal: `4:3`

Every image-generation prompt must explicitly include the selected aspect ratio. If the user does not specify format, use `1:1`.

## Required Inputs

Before creating images, collect the minimum viable brief. Accept flexible inputs: landing page URL, free-text product description, uploaded document, existing ad copy/texts, image/reference creative, or inspiration design. See `references/input-sources.md`. First check memory, prior manifests, campaign manager briefs, landing pages, documents, ad copy, and existing assets. Ask only for missing blockers:

1. Product/service/offer being promoted.
2. Landing page URL, document, free-text brief, existing ad copy/texts, or inspiration/reference images.
3. Target audience, if not clear from the source.
4. Desired language for the ad text.
5. Brand/style preferences, if any.
6. Offer details: price, bonuses, guarantee, urgency, CTA.
7. Number of image variations to generate, or saved default count if this is a repeat run.
8. Preferred format, if relevant. Default is always square 1:1 unless the user explicitly asks for landscape 4:3 or vertical 9:16 story/reel format.
9. Preferred image provider, if they care: GPT Image 2.0, Nano Banana/Gemini, or best available.

If a landing page exists, use it as the primary source unless the user supplied specific ad copy for this batch. If no page exists, use the user's product/service description, uploaded document, or supplied ad copy/texts. Existing ad copy should be treated as the core message to visualize, not ignored.

## Participant Setup

When helping workshop participants install or test the skill, use `references/participant-installation.md`. Do not include API keys inside the skill.

For Google Drive backup setup or troubleshooting, use `references/google-drive-backup.md` and refer to the dedicated `google-drive-service-account` skill instead of duplicating its setup instructions here.

## Collaboration With Campaign Managers

This skill is the Creative Specialist. It can receive requests from a campaign/ad-management agent, including Post-Andromeda campaign workflows. Use `references/campaign-manager-handoff.md` for request/response formats and how to translate performance signals into creative briefs.

## Workflow

### 0. Prepare storage

Before the first creative batch for a client/product, create or reuse the folder hierarchy from `references/folder-structure.md`. Store all outputs, prompts, manifests, inspiration references, winners, and reusable memory there. If the user wants Google Drive backup, follow `references/google-drive-backup.md`: save locally first, then back up to Drive when service-account access is configured.

### 1. Choose operating mode

If the user gives a broad request, use Autonomous Workshop Mode from `references/workshop-mode.md` and the accepted input options from `references/input-sources.md`. If the user provides images/designs for inspiration, analyze and save them with `references/inspiration-references.md`. If saved inspiration references exist, suggest using them before generating fresh directions. If another agent provides performance data or asks for creative refreshes, use Campaign Manager Handoff from `references/campaign-manager-handoff.md`. If there is an existing brand or winning creative, use `references/brand-and-refresh-modes.md`. If the business type is obvious, use `references/business-templates.md` to choose stronger default angles.

### 2. Verify image provider setup

Before creating images, check whether OpenAI GPT Image 2.0 or Google Gemini/Nano Banana is available. Use `references/api-setup.md` for API key names, safe handling, provider selection, and fallback behavior.

If neither provider is configured, ask the user for one API key and stop until setup is complete. If they need help creating/finding keys, use the `image-model-api-keys` skill.

### 3. Learn the visual language

If the user provides a landing page or existing brand reference, analyze the visual style first.

Use the Visual Brief prompt in `references/prompts.md`.

Output a concise visual brief covering:

- Colors and palette behavior.
- Fonts and typography feel.
- Text density.
- Layout style.
- Tone and visual personality.
- Visual messaging.
- Specific image-generation constraints.

Use a strong reasoning model for this step when available.

### 4. Generate image-ad concepts and text variations

Generate 10 high-converting image-ad text/concept variations.

If a landing page exists, use the Landing Page Creative Variations prompt in `references/prompts.md`.

If no landing page exists, use the Product Description Creative Variations prompt in `references/prompts.md`.

When a visual brief exists, include it in the prompt so the concepts preserve the brand language.

Each variation should include:

- Creative angle.
- Hook type.
- Main image text.
- Supporting text, if needed.
- Visual direction.
- Layout guidance.
- Image-generation prompt/instructions.
- Why it should work.

### 5. Improve concepts using creative levers

Use the creative levers in `references/creative-levers.md` and, when relevant, the business-specific guidance in `references/business-templates.md` to diversify concepts.

Select only the levers relevant to the product and user notes. Do not mechanically use every lever.

Good default mix:

- 2 benefit/result concepts.
- 2 pain/fear/problem concepts.
- 2 authority/proof concepts.
- 2 curiosity/contrast concepts.
- 2 offer/value concepts.

### 6. Score and generate images

Before generating images, score the concepts using `references/manifest-and-scoring.md`. Generate the highest-scoring concepts first.

Use the model-routing strategy in `references/model-routing-and-qa.md`. For early exploration, use Nano Banana 2 / fast Gemini as a low-cost draft model and clearly tell the user these are draft concepts only. For final ad-ready output, prefer GPT Image 2.0, or use Nano Banana Pro when selected/available.

Send the final image-generation instructions to the selected model and record requested vs actual provider/model in the manifest.

For each image:

- Use square 1:1 as the default aspect ratio in every image-generation prompt. Use landscape 4:3 or vertical 9:16 only if the user explicitly requests it.
- Save output under `/ad-creatives`.
- Use descriptive filenames: `YYYYMMDD_product_angle_variation.png`.
- Save a manifest of generated concepts, exact prompts, scores, requested provider/model, actual provider/model, generation tier, QA status, and output files. Preserve original prompts, not only summaries.

After image generation, run the mandatory QA stage from `references/model-routing-and-qa.md`.

### 7. QA and finalize

After generating draft or final images, run QA using `references/model-routing-and-qa.md`. For draft images, communicate clearly that they are for concept approval only. For final images, fix or regenerate anything with Hebrew/RTL/text problems before marking it `ad_ready`.

If the user approves a draft, regenerate it as final with GPT Image 2.0 by default, or Nano Banana Pro if selected/available.

### 8. Create variations from a winning creative

When the user likes a creative or the campaign manager marks a creative as a winner, first save its full prompt lineage and creative DNA using `references/winning-creative-memory.md`. Then use Winner Variation Mode from `references/brand-and-refresh-modes.md` and create 3-5 variations from it.

Process:

1. Use the winning creative as the reference image.
2. Generate new precise edit instructions using the stage 2 prompt plus selected ideas/angles from `references/creative-levers.md`.
3. Send the reference image plus the Replication/Edit prompt from `references/prompts.md` to the image model.
4. Keep all unmentioned elements identical.
5. Change only the requested text, angle, or visual element.

### 9. Handle user feedback

When the user gives feedback like “make it more premium,” “change the headline,” “more urgency,” or “less text”:

1. Analyze the current image and feedback.
2. Convert feedback into exact visual edit instructions using the Feedback-to-Instructions prompt in `references/prompts.md`.
3. Send those instructions to the image model.
4. Save the new version under `/ad-creatives`.

Do not skip the instruction-generation step.

## Output Format for Concepts

Use this structure for each proposed concept:

```markdown
## Variation X — [short name]

- Angle:
- Hook:
- Proof/offer lever:
- Image text:
- Supporting text:
- Visual direction:
- Layout:
- Image-generation instructions:
- Why this can convert:
```

## Quality Checklist

Before generating or presenting final creative prompts, verify:

- The concept matches the product and audience.
- The image text is readable at mobile-feed size.
- The hook is specific, not generic.
- The visual direction includes hierarchy, spacing, contrast, and safe margins.
- The prompt preserves brand language if a visual brief exists.
- There is a clear performance reason for the variation.
- The requested number of image variations is known or a saved default applies.
- The image prompt explicitly states square 1:1 unless the user requested landscape 4:3 or vertical 9:16.
- Draft images are labeled as draft concepts and not upload-ready.
- Final images were generated with GPT Image 2.0 or Nano Banana Pro when available/selected.
- QA was run and every final image has a status: `ad_ready`, `needs_edit`, `failed_text`, or `rejected`.
- Concepts were scored before generation.
- A manifest path is prepared for the batch.
- The standard client/product folder structure exists or has been reused.
- If Google Drive backup was requested, Drive access is configured or the user has been routed to the `google-drive-service-account` skill.
- Relevant business template or brand/refresh mode was considered when applicable.
- If any creative is marked as a winner, its exact prompt lineage, creative DNA, and reproduction instructions are saved.
- At least one image provider is configured or the user has provided the needed API key. If not, the user was routed to the `image-model-api-keys` skill.
- Input source was recorded: URL, free-text brief, document, existing ad copy/texts, reference creative, or saved inspiration reference.
- If inspiration images were supplied, they were analyzed and saved under `_inspiration/`, with reuse instructions.
