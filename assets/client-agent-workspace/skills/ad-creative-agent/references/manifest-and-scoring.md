# Manifest and Creative Scoring

## Manifest

For every creative batch, save a manifest next to the generated images.

Recommended path:

```text
/ad-creatives/[client-or-product]/[YYYY-MM-DD-batch]/manifest.json
```

If `/ad-creatives` is not writable, use `./ad-creatives` in the current workspace.

Manifest schema:

```json
{
  "batch_id": "",
  "created_at": "",
  "client_name": "",
  "product_name": "",
  "landing_page_url": "",
  "audience": "",
  "offer": "",
  "provider_requested": "",
  "model_requested": "",
  "provider_used": "",
  "model_used": "",
  "generation_tier": "draft | final",
  "format": "1:1 square by default; 9:16 for vertical/story/reel; 4:3 for landscape/horizontal",
  "brand_brief_summary": "",
  "source": "user request / campaign manager / refresh",
  "creatives": [
    {
      "file": "",
      "variation_name": "",
      "angle": "",
      "hook": "",
      "proof": "",
      "framework": "",
      "image_text": "",
      "prompt": "",
      "score": {
        "clarity": 0,
        "scroll_stopping": 0,
        "audience_fit": 0,
        "offer_strength": 0,
        "visual_simplicity": 0,
        "total": 0
      },
      "qa_status": "draft_concept | needs_edit | failed_text | approved_concept | final_candidate | ad_ready | rejected",
      "is_ad_ready": false,
      "notes": ""
    }
  ]
}
```

## Creative Scoring

Score concepts before image generation.

Use a 1-5 score for:

- Clarity: Is the message instantly understandable?
- Scroll-stopping: Is there a strong visual/hook reason to notice it?
- Audience fit: Does it match the target market’s actual motivation?
- Offer strength: Does it make the offer feel valuable or urgent?
- Visual simplicity: Can it work on mobile without clutter?

Generate images from the highest-scoring concepts first.

If the user asks for N images, create at least 2N concepts, score them, then generate the best N.
