# Winning Creative Memory

Use this whenever a creative is marked as successful by the user, campaign manager, or performance data.

Goal: preserve not just the image, but the full creative DNA that made it work so it can be reproduced, varied, and scaled later.

## When to Save a Winning Creative

Mark a creative as a winner when any of these happen:

- User says it is good, approved, or wants more like it.
- Campaign manager reports strong performance.
- Metrics show strong CTR, CPA, CPQ, ROAS, lead quality, purchase rate, or thumbstop/hook rate.
- It becomes the base image for more variations.

## Save Full Prompt Lineage

For every winning creative, save:

```json
{
  "winner_id": "",
  "creative_file": "",
  "thumbnail_file": "",
  "created_at": "",
  "marked_winner_at": "",
  "client_name": "",
  "product_name": "",
  "campaign_id": "",
  "ad_id": "",
  "landing_page_url": "",
  "performance_snapshot": {
    "spend": "",
    "impressions": "",
    "ctr": "",
    "cpa": "",
    "cpq": "",
    "roas": "",
    "lead_quality_notes": ""
  },
  "creative_dna": {
    "angle": "",
    "hook_type": "",
    "proof_type": "",
    "offer_frame": "",
    "copy_framework": "",
    "visual_pattern": "",
    "audience_insight": "",
    "core_promise": "",
    "why_it_worked_hypothesis": ""
  },
  "prompt_lineage": {
    "visual_brief_prompt": "",
    "visual_brief_output": "",
    "concept_generation_prompt": "",
    "concept_generation_output": "",
    "selected_concept": "",
    "image_generation_prompt": "",
    "image_model": "",
    "image_provider": "",
    "reference_images": [],
    "edit_feedback_history": [
      {
        "feedback": "",
        "feedback_to_instruction_prompt": "",
        "generated_edit_instructions": "",
        "result_file": ""
      }
    ]
  },
  "reproduction_instructions": {
    "what_to_keep": [],
    "what_can_change": [],
    "what_not_to_change": [],
    "recommended_variation_axes": []
  },
  "notes": ""
}
```

## Explain Why It Worked

When a creative is marked as a winner, write a short hypothesis:

- What audience belief/desire/fear did it hit?
- What visual pattern made it noticeable?
- What copy element made it clear or persuasive?
- What proof/offer element reduced friction?
- What should be preserved in future variations?

This is a hypothesis, not a fact. Update it when performance data changes.

## Reproduction Rules

When asked to make more creatives like a winner:

1. Load the winning creative memory.
2. Preserve the core promise, visual pattern, hook type, and audience insight unless instructed otherwise.
3. Change only one or two variables per variation.
4. Reuse the original image-generation prompt structure.
5. Explicitly state what was preserved and what changed.
6. Save new prompt lineage for each variation.

## Prompt Preservation Rules

Always preserve the exact prompts that contributed to a winner:

- Visual analysis prompt and output.
- Concept generation prompt and output.
- Final image generation prompt.
- Any edit prompt or feedback transformation prompt.
- Reference image filenames/IDs.
- Model/provider used.

Do not summarize prompts in place of storing the original. Summaries can be added, but originals must remain recoverable.

## Storage Location

Store winning creative memories inside the batch manifest and, when possible, in a reusable winners file:

```text
/ad-creatives/[client-or-product]/winning-creatives.json
```

If `/ad-creatives` is not writable, use:

```text
./ad-creatives/[client-or-product]/winning-creatives.json
```
