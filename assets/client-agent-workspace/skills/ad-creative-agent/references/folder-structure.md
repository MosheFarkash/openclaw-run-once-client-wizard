# Folder Structure Contract

Use this folder structure for every client/product so outputs are consistent, reusable, and easy for another agent to read.

## Root Folder

Preferred root:

```text
/ad-creatives/
```

Fallback if `/ad-creatives` is not writable:

```text
./ad-creatives/
```

Never scatter creative outputs across random folders.

## Client/Product Folder

Create one folder per client/product:

```text
/ad-creatives/[client-slug]/[product-slug]/
```

Slug rules:

- Lowercase when possible.
- Use hyphens instead of spaces.
- Keep Hebrew names only if needed; otherwise transliterate.
- Avoid special characters except `-` and `_`.

Example:

```text
/ad-creatives/getscale/ai-workshop/
```

## Required Folder Tree

```text
/ad-creatives/[client]/[product]/
├── _memory/
│   ├── client-profile.json
│   ├── product-brief.json
│   ├── brand-brief.md
│   ├── winning-angles.json
│   ├── losing-patterns.json
│   └── winning-creatives.json
├── _prompts/
│   ├── visual-brief-prompts.md
│   ├── concept-generation-prompts.md
│   ├── image-generation-prompts.md
│   ├── edit-prompts.md
│   └── prompt-lineage.jsonl
├── _inspiration/
│   ├── index.json
│   └── ref-YYYYMMDD-[short-description]/
│       ├── source-image.png
│       ├── analysis.md
│       ├── extraction.json
│       └── reuse-instructions.md
├── batches/
│   └── YYYY-MM-DD_batch-[number]_[short-goal]/
│       ├── manifest.json
│       ├── concepts.md
│       ├── scores.json
│       ├── images/
│       │   ├── v01_[angle]_[hook].png
│       │   ├── v02_[angle]_[hook].png
│       │   └── ...
│       ├── references/
│       │   └── [reference images used]
│       └── exports/
│           └── [optional resized/renamed files for upload]
├── winners/
│   └── [winner-id]/
│       ├── winner.json
│       ├── original.png
│       ├── prompt-lineage.md
│       ├── why-it-worked.md
│       └── variations/
│           └── [new variation files]
└── archive/
    └── [old or rejected batches]
```

## What Goes Where

### `_memory/`

Persistent reusable knowledge for future runs.

- `client-profile.json`: client/business info and defaults.
- `product-brief.json`: product, audience, offer, landing page, CTA.
- `brand-brief.md`: visual language and brand rules.
- `winning-angles.json`: angles/hooks/proofs that have worked.
- `losing-patterns.json`: patterns to avoid.
- `winning-creatives.json`: index of all winning creatives.

### `_prompts/`

Prompt history and reusable prompt lineage.

- `visual-brief-prompts.md`: exact prompts used for brand/style analysis.
- `concept-generation-prompts.md`: exact prompts used to create concepts.
- `image-generation-prompts.md`: exact prompts sent to image models.
- `edit-prompts.md`: exact prompts used for edits/feedback.
- `prompt-lineage.jsonl`: one JSON object per generated creative with full prompt chain.

### `_inspiration/`

Reusable visual inspiration references supplied by the user. Store original/reference image, visual + marketing analysis, extracted tags, and reuse instructions. See `references/inspiration-references.md`.

### `batches/`

Every creative generation session gets its own batch folder.

Batch naming:

```text
YYYY-MM-DD_batch-01_initial-concepts
YYYY-MM-DD_batch-02_winner-variations
YYYY-MM-DD_batch-03_fatigue-refresh
YYYY-MM-DD_batch-04_quality-fix
```

Each batch must include:

- `manifest.json`
- `concepts.md`
- `scores.json`
- `images/`

### `winners/`

When a creative is marked as a winner, copy or link its core files into a dedicated winner folder.

Winner folder naming:

```text
winner-YYYYMMDD-[angle]-[short-hook]/
```

Each winner folder must include:

- `winner.json`: structured metadata and performance snapshot.
- `original.png`: the winning creative.
- `prompt-lineage.md`: all original prompts and outputs that created it.
- `why-it-worked.md`: hypothesis and learnings.
- `variations/`: future variations based on that winner.

### `archive/`

Move old, rejected, or deprecated batches here instead of deleting them.

## File Naming Rules

Image files:

```text
v[number]_[angle]_[hook]_[format].png
```

Examples:

```text
v01_authority_problem_square.png
v02_results_statistic_square.png
v03_fear_question_story.png
```

Avoid vague filenames like:

```text
image1.png
final.png
new_new_final.png
```

## Prompt Lineage JSONL

Every generated creative should append one line to:

```text
_prompts/prompt-lineage.jsonl
```

Recommended object:

```json
{
  "creative_id": "",
  "batch_id": "",
  "file": "",
  "created_at": "",
  "provider": "",
  "model": "",
  "visual_brief_prompt": "",
  "visual_brief_output_ref": "",
  "concept_prompt": "",
  "concept_output_ref": "",
  "image_prompt": "",
  "edit_prompt": "",
  "reference_images": [],
  "angle": "",
  "hook": "",
  "proof": "",
  "score_total": 0,
  "status": "draft | approved | winner | rejected",
  "notes": ""
}
```

## Consistency Rules

- Always create the folder tree before generating the first batch for a product.
- Always write batch files before or immediately after image generation.
- Never overwrite prior prompts or manifests; append or create a new batch.
- When creating winner variations, store them under the matching winner's `variations/` folder and also inside the current batch.
- Campaign manager agents should read manifests and `_memory/` files instead of asking the user for context again.
