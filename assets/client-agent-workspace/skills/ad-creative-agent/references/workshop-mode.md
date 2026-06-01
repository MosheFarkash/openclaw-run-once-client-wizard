# Autonomous Workshop Mode

Use this mode when the user says something broad like:

- “I want to create ad creatives.”
- “Make me new creatives.”
- “I need ads for this offer.”
- “Generate more variations.”

The agent should lead the process proactively. Do not wait for the user to design the workflow.

## Operating Principle

Ask the fewest questions possible. Use memory, prior briefs, existing campaign data, landing pages, and previous outputs before asking the user.

If required information is missing, ask only the minimum blocking question. A landing page is optional; document, free-text brief, existing ad copy, or inspiration/reference image are valid inputs.

## First Run Flow

On the first run for a client/product:

1. Identify or ask for the product/offer.
2. Ask for one usable input source: landing page URL, free-text product/audience description, uploaded document, existing ad copy/texts, reference creative, or inspiration image/design.
3. Identify or ask for target audience if not obvious from the source.
4. Ask how many image variations to generate.
5. Ask provider preference only if more than one provider is configured and the choice matters.
6. Build a brand/visual brief if a page or reference exists.
7. Generate concepts.
8. Score concepts.
9. Generate the requested number of images.
10. Save images and manifest.
11. Save reusable client/product memory.

## Repeat Run Flow

On later runs:

1. Load the saved client/product memory if available.
2. Reuse prior brand brief, audience, offer, visual rules, and provider preference.
3. Ask only for what changed:
   - New offer?
   - New angle?
   - More like a previous winner?
   - How many variations?
4. Generate new concepts and images.

Default behavior if the user simply says “make more creatives”:

- Use the last known product/offer.
- Check saved inspiration references and suggest the most relevant ones.
- If the user supplies new ad copy, use it as the primary source for this batch.
- Use the last known brand brief.
- Use the last known audience.
- Generate 5 variations unless a previous default count is saved.
- Favor new angles not already used recently.

## Minimal Question Policy

Ask a question only when the answer materially changes output quality or prevents execution.

Do not ask for:

- Brand colors if a website exists.
- Audience if campaign or landing page data makes it clear.
- Image format if the platform default is known; default to square 1:1 for feed ads.
- Provider if only one provider is available.

## Default Assumptions

If the user gives no preference:

- Image count: 5.
- Format: square 1:1 feed image. This is mandatory by default unless the user explicitly asks for landscape 4:3 or vertical 9:16 story/reel.
- Language: same language as the landing page or user request.
- Objective: lead/sale conversion.
- Style: direct-response, high-clarity, mobile-first.
- Text density: low to medium.

## Client/Product Memory

Maintain reusable memory per client/product when possible.

Suggested memory fields:

```json
{
  "client_name": "",
  "product_name": "",
  "landing_page_url": "",
  "audience": "",
  "offer": "",
  "language": "",
  "brand_brief": "",
  "preferred_provider": "",
  "default_image_count": 5,
  "default_format": "1:1 square feed image",
  "winning_creatives": [],
  "losing_patterns": [],
  "used_angles": [],
  "notes": []
}
```

Store this in the user's normal project memory system when available, or in a local per-project manifest folder if memory tools are unavailable.
