# Client Ads Manager - Shared Skill

## Overview
This skill provides Meta Ads campaign management capabilities for client agents. Each client agent has its own workspace with client-specific config and memory, but shares this skill for common operations.

## Capabilities

### 1. Daily Report
Pull yesterday's performance from Meta Ads API and format a summary:
- Total spend, leads, CPL
- Qualified leads (from CRM if available), CPQ
- Top/bottom performing ads
- Budget distribution issues

### 2. Weekly Report
Comprehensive weekly review including:
- Week-over-week trends
- Andromeda-style health check (if enabled in client config)
- Creative fatigue signals
- Recommendations

### 3. Campaign Management
- Create campaigns (CBO/ABO) via Meta Ads API
- Create/modify adsets and ads
- Update targeting, budgets, bids
- Pause/enable campaigns

### 4. Optimization (Andromeda Framework)
Apply the Post-Andromeda methodology:
- Identify budget vampires (>30% spend, below-average CPQ)
- Flag hidden stars (good CPQ, low distribution)
- Duplication Protocol for adsets with mixed performers
- Kill metrics: CTR <1%, CPQ >2x account average, 0 quals after significant spend

## How to Use

### Reading Client Config
```python
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
account_id = config['meta_ads']['account_id']
```

### Meta API Calls
**CRITICAL: Read the access token from your agent's `secrets/keys.md` file. NEVER use the `META_ACCESS_TOKEN` environment variable -- it's a different token and will cause permission errors.**

```bash
# Correct way:
TOKEN=$(grep 'Access Token:' /path/to/your/agent/secrets/keys.md | sed 's/.*: //')

# WRONG -- do NOT do this:
# TOKEN=$META_ACCESS_TOKEN
```

API base: `https://graph.facebook.com/{api_version}/{account_id}/insights`

### Report Format (WhatsApp-friendly)
Keep reports clean and readable in WhatsApp:
- Use bold (*text*) sparingly for headers
- Use line breaks for readability
- Numbers: use client's currency_display
- Keep under 4000 chars (WhatsApp chunk limit)

## Important Rules
1. NEVER mix client data -- each agent reads only its own config.yaml
2. Currency display comes from client config, not hardcoded
3. Reports should match the client's language preference
4. All campaign modifications need explicit approval unless auto-optimize is enabled
5. Log all actions to client's daily memory file
