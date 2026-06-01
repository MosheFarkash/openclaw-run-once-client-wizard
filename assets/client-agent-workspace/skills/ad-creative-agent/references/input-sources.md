# Input Sources

At the beginning of the process, accept any of these input types. Do not force the user into only a landing-page URL.

## Supported Inputs

1. **Landing page / website URL**
   - Best when available. Use it to learn the offer, audience, language, claims, CTA, and visual style.

2. **Free-text product brief**
   - Use when no website exists. Ask for product/service, audience, offer, proof, CTA, and desired language only if missing.

3. **Document containing the brief**
   - Accept PDF, DOCX, TXT, Markdown, notes, strategy doc, sales page copy, or workshop brief.
   - Extract product, audience, offer, objections, proof, tone, and CTA.

4. **Existing ad copy/texts**
   - Accept the actual copy the user wants to advertise.
   - The job becomes: create visual ad creatives that match and strengthen the provided copy.

5. **Existing creative/image reference**
   - Use for brand/style consistency, winner variations, refresh, or inspiration reference memory.
   - Analyze and save reusable inspiration references using `references/inspiration-references.md`.

## Opening Question

When starting with a new user, ask for input in this flexible format:

```text
Send me one of these:
1. A landing page / website URL
2. A short product + audience description
3. A document with the product/offer info
4. The ad copy/texts you already want to run

Also tell me how many draft creatives you want. If you don't choose, I'll start with 5 square 1:1 drafts.
```

## Existing Ad Copy Workflow

When the user provides ad copy/texts:

1. Treat the copy as the core message.
2. Extract:
   - Main promise
   - Audience
   - Pain/desire
   - Proof
   - CTA
   - Tone
3. Create visual concepts that support the copy instead of rewriting it from scratch.
4. If the copy is too long for an image, keep the full copy in the manifest and create shorter image text derived from it.
5. Ask before changing the strategic meaning of the copy.
6. Generate image prompts that explicitly say the creative is based on the supplied ad copy.

## Document Input Workflow

When the user uploads a document:

1. Read/extract the document.
2. Summarize the usable creative brief.
3. Identify missing blockers only.
4. Save the extracted brief to `_memory/product-brief.json` or `_memory/source-brief.md`.
5. Save the source document or a reference to it in the batch `references/` folder.

## Source Priority

If multiple sources conflict, use this priority:

1. User's latest explicit instruction.
2. Existing ad copy supplied for this batch.
3. Landing page / sales page.
4. Uploaded document.
5. Saved memory from previous runs.

Record the source used in the manifest.
