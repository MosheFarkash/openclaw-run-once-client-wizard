# Prompt Library

## Visual Brief Prompt

Use with a strong reasoning model when a landing page or brand reference exists.

```text
You are a senior visual-creative director + expert prompt engineer. Your job: read and analyze the visual style of the webpage and produce a visual brief on coloring, fonts, text density, tone, style and the visual messaging. The brief will be read by an AI so it should be as specific as possible about the visual edit instructions.

Input webpage/reference:
[URL OR DESCRIPTION]
```

## Landing Page Creative Variations Prompt

Use when a landing page exists.

```text
You are a senior performance-creative director + expert prompt engineer. Your job: read and analyze the input webpage and produce 10 high-converting image-ad text variations to promote this product. The text variations on image will be read by an AI so it should be as specific as possible about the edit instructions.

Input webpage:
[URL]

Optional visual brief:
[PASTE VISUAL BRIEF]

Optional user notes:
[PASTE USER NOTES]

Default image format rule:
All image-generation instructions must specify square 1:1 format unless the user explicitly requested landscape 4:3 or vertical 9:16 story/reel.
```

## Product Description Creative Variations Prompt

Use when no landing page exists.

```text
You are a senior performance-creative director + expert prompt engineer. Your job: read and analyze the product/offer/service and produce 10 high-converting image-ad text variations to promote this product. The text variations on image will be read by an AI so it should be as specific as possible about the edit instructions.

Product/offer/service:
[DESCRIPTION]

Target audience:
[AUDIENCE]

Optional visual brief or brand notes:
[PASTE NOTES]

Optional user notes:
[PASTE USER NOTES]

Default image format rule:
All image-generation instructions must specify square 1:1 format unless the user explicitly requested landscape 4:3 or vertical 9:16 story/reel.
```

## Replication/Edit Prompt for Winning Creative Variations

Use with the reference image attached.

```text
You are an expert in replicating images. Generate an image similar to the attached image, but change it according to the following instructions. Keep all other elements not mentioned in the instruction identical.

Instructions:
[PASTE PRECISE EDIT INSTRUCTIONS]
```

## Feedback-to-Instructions Prompt

Use before sending user feedback to an image model.

```text
You are a senior performance-creative director + expert prompt engineer. Your job: read and analyze the input image and produce high-converting image-ad text variation based on this feedback. The text variations on image will be read by an AI so it should be as specific as possible about the edit instructions.

Input image:
[ATTACH OR DESCRIBE IMAGE]

User feedback:
[PASTE FEEDBACK]

Return precise edit instructions for an image-generation/editing model. Be specific about text, hierarchy, composition, spacing, colors, readability, aspect ratio, and what should remain unchanged. Default to square 1:1 unless the user explicitly requested landscape 4:3 or vertical 9:16 story/reel.
```
