# COLLECTIVE.md - Cross-Client Learnings

## Meta Platform Behavior
- CRM typically has more leads than Meta pixel -- filtered/unqualified leads are tracked in CRM but not fired as conversions (intentional for pixel quality)
- Custom conversion events need BOTH `custom_event_type: "OTHER"` + `custom_event_str: "EventName"`
- ABO campaigns: bid_strategy goes on adsets, NOT campaign level
- When creating creatives via API, always include media (image_hash or video_id) -- copy-only creatives show as "no media"
- Strip image_url/thumbnail_url/picture from object_story_spec before POSTing new creatives (Meta rejects redundant fields)

## Optimization Methodology (Andromeda / Jeremy Haynes)
- Blended adset CPQ is the decision metric, not individual ad performance
- Don't turn off adsets that have winners -- use Duplication Protocol instead
- No "graduating" ads between adsets -- each adset runs independently
- Budget vampires: >30% of adset spend + below-average CPQ
- Hidden stars: good CPQ but <5% distribution -- need more budget allocation
- Hybrid approach works: Duplicate for clean reset + snipe worst offenders

## Reporting Best Practices
- Always show CPQ (cost per qualified lead) as primary metric, not just CPL
- Quality % = post-meeting stages (after initial contact)
- 2-day minimum data window before making optimization decisions
- 48h evaluation period after duplications before next changes

## API Gotchas
- POST body: use `data=` not `params=` in requests.post() for large payloads
- ABO adset budgets must be in cents (multiply by 100)
- Always check _results.json for errors before declaring upload success
- Delete failed campaign shells immediately -- they show as DELETED in Ads Manager
