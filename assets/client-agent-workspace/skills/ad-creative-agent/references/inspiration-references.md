# Inspiration References

Use this when the user provides images, designs, screenshots, ads, landing-page sections, moodboards, or any visual reference for inspiration.

Goal: analyze the reference at both design level and marketing-structure level, save it as reusable creative memory, and suggest using it in future creative batches.

## Accepted Inspiration Inputs

Accept:

- Image ads.
- Screenshots of ads.
- Landing page sections.
- Social posts.
- Competitor creatives.
- Moodboard images.
- Brand design examples.
- Existing client designs.
- Winning creatives from past campaigns.

## What to Analyze

Use a vision-capable model such as GPT or Gemini to analyze the image.

Extract:

### Visual Design

- Aspect ratio and format.
- Layout structure.
- Composition and focal point.
- Color palette.
- Typography style.
- Text density.
- Spacing and margins.
- Contrast and hierarchy.
- Imagery style: photo, illustration, UI, abstract, UGC, etc.
- Background treatment.
- Brand/premium feel.

### Marketing Structure

- Main hook.
- Core promise.
- Audience implied by the creative.
- Pain/desire being used.
- Proof element, if any.
- Offer/CTA, if any.
- Copy framework, if identifiable.
- Why the design may stop scroll.
- Why it may convert.

### Reuse Guidance

Write clear instructions for how to use the reference later:

- What to borrow.
- What to avoid copying exactly.
- What can be adapted to the user's brand.
- Which future products/offers it fits.
- Which angles/hooks it supports.

## Save Location

Save references under the client/product folder:

```text
/ad-creatives/[client]/[product]/_inspiration/
├── index.json
├── [reference-id]/
│   ├── source-image.[png|jpg]
│   ├── analysis.md
│   ├── extraction.json
│   └── reuse-instructions.md
```

If the reference is general to the client and not one product, store it under:

```text
/ad-creatives/[client]/_inspiration/
```

If `/ad-creatives` is not writable, use `./ad-creatives`.

## Reference ID Naming

Use:

```text
ref-YYYYMMDD-[short-description]
```

Examples:

```text
ref-20260429-bold-split-screen
ref-20260429-premium-dashboard-ad
ref-20260429-ugc-before-after
```

## index.json Schema

Maintain an index:

```json
{
  "references": [
    {
      "reference_id": "",
      "created_at": "",
      "source_file": "",
      "description": "",
      "visual_tags": [],
      "marketing_tags": [],
      "best_for": [],
      "avoid_for": [],
      "analysis_path": "",
      "reuse_instructions_path": ""
    }
  ]
}
```

## Future Batch Behavior

When the user later asks to create creatives:

1. Check whether inspiration references exist for this client/product.
2. If relevant references exist, suggest them briefly:

```text
I found saved inspiration references for this product. I can use one of these directions:
1. Premium dashboard layout
2. Bold split-screen problem/solution
3. UGC-style before/after

Do you want me to use one, or should I create a fresh direction?
```

3. If the user does not choose, select the most relevant reference based on the current offer, audience, and creative goal.
4. Do not copy the reference exactly unless the user owns it and asks for close replication.
5. Adapt the structure and principles to the current brand and offer.

## Prompt Pattern for Analyzing an Inspiration Image

Use this prompt with the image attached:

```text
You are a senior visual creative director and performance marketing strategist. Analyze this image as an inspiration reference for future ad creatives.

Describe what is happening in the image at two levels:
1. Visual design: layout, composition, typography, colors, hierarchy, spacing, focal point, text density, and style.
2. Marketing structure: hook, promise, audience, pain/desire, proof, offer/CTA, copy framework, and why it may stop scroll or convert.

Then produce reuse instructions for an AI creative agent: what to borrow, what to avoid copying exactly, what can be adapted, and what types of future campaigns this reference fits.
```

## Copying Safety

Treat external competitor/reference images as inspiration, not assets to copy exactly.

- Borrow structure, principle, and pattern.
- Do not recreate logos, brand marks, people, or exact proprietary design unless the user owns the asset and explicitly asks.
- If the user wants close replication, ask whether they own or have permission to use the reference.

## When a Reference Becomes a Winner

If an inspiration reference leads to a winning creative, connect it to Winning Creative Memory:

- Add the reference ID to the winner metadata.
- Record which parts of the reference were used.
- Record whether the reference pattern should be reused in future batches.
