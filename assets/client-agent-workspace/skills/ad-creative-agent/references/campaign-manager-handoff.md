# Campaign Manager Handoff

This skill is the Creative Specialist. It should work with a separate campaign/ad-management agent or skill, especially Post-Andromeda campaign management workflows.

## Role Split

Campaign Manager / Media Buyer:

- Reads campaign performance.
- Identifies winners, losers, fatigue, trash leads, CPA/CPQ issues, or scaling opportunities.
- Decides what kind of creative is needed.
- Requests new creative from this skill.

Creative Specialist:

- Translates performance problems into new creative angles.
- Generates concepts, prompts, images, and manifests.
- Produces variations of winners without breaking what works.
- Returns a structured creative batch to the campaign manager.

## Request Format from Campaign Manager

When another agent asks for creatives, prefer a structured brief:

```json
{
  "request_type": "new_angles | winner_variations | fatigue_refresh | quality_fix | cpa_fix | offer_test",
  "client_name": "",
  "product_name": "",
  "campaign_id": "",
  "adset_name": "",
  "winning_ads": [],
  "losing_ads": [],
  "performance_notes": "",
  "audience_notes": "",
  "offer": "",
  "landing_page_url": "",
  "requested_count": 5,
  "format": "1:1",
  "must_keep": [],
  "must_avoid": []
}
```

If a request is incomplete, infer what you can from saved memory and ask only for missing blockers.

## How to Respond to Campaign Signals

### Winner variations

When the campaign manager says an ad is working:

- Preserve the core concept, structure, and visual identity.
- Create 3-5 close variations.
- Change one major variable at a time: hook, proof, CTA, offer framing, or visual emphasis.
- Do not reinvent the whole creative.

### Fatigue refresh

When performance drops after initial success:

- Keep the winning promise and audience insight.
- Change the visual hook and opening text.
- Create more distinct visual patterns than winner variations.

### High CPA / weak conversion

Generate concepts that clarify:

- Specific outcome.
- Offer value.
- Who it is for / not for.
- Why now.
- Proof or risk reversal.

### Trash leads / low quality

Generate concepts that qualify the audience:

- Add specificity about who the offer is for.
- Use premium/value framing instead of broad curiosity.
- Avoid vague promises and cheap lead magnets.
- Mention constraints, requirements, price range, or seriousness when appropriate.

### Scattered spend / no clear winner

Generate diversified concepts across different angles:

- Pain/problem.
- Desired outcome.
- Authority/proof.
- Offer/value.
- Contrarian insight.

## Output Back to Campaign Manager

Return a structured summary:

```json
{
  "batch_id": "",
  "manifest_path": "",
  "creative_files": [],
  "recommended_upload_order": [],
  "testing_notes": "",
  "angle_distribution": {},
  "next_refresh_trigger": ""
}
```

Include enough context so the campaign manager can upload, test, and later request follow-up variations.
