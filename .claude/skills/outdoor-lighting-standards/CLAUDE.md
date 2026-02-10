# Claude Instructions: Outdoor Lighting Standards

## When to Invoke This Skill

Use this skill whenever lighting standards, photometric calculations, or technical lighting concepts are relevant — **regardless of context**. This includes development, emails, presentations, grant applications, RFP responses, proposals, sales materials, LinkedIn content, or any conversation with lighting professionals.

A wrong number in an email is just as damaging as a wrong number in code.

**Trigger keywords:**
RP-8, IES, lighting standards, illuminance, luminance, surround ratio, uniformity, veiling luminance, photometric calculations, lighting classifications, pavement classifications, lux levels, cd/m², any technical lighting discussion.

**Verification requirement:** When a specific number from a lighting standard appears, verify it against the RP-8-25 extract rather than relying on training knowledge.

## Core Principle

**Every implementation decision must maintain Photometrics AI's advantage over typical layouts.**

Photometrics AI is closer to "perfect" than typical layouts. The question is never "Is this perfect?" but "Is this better than what typical layouts do?"

## The Quality Bar

### What "Perfect" Looks Like
Every intersection designed with lighting software accounting for: actual luminaire positions, trees, elevation, bike lanes, road geometry, observer position, surface reflectance.

### Photometrics AI's Gap to Perfect
- Uses horizontal illuminance instead of luminance (for now)

### Typical Layouts' Gap to Perfect
10-20 generic templates for entire cities, ignoring:
- Actual vs designed luminaire positions
- Height variations, mast arm direction/length
- Road width, crosswalks, turning lanes, intersections
- Curves, slopes, sidewalk presence
- High-crime areas, high-crash areas, traffic volumes

### The Verdict
Illuminance-vs-luminance gap < cumulative geometric errors in typical layouts.

## How to Use This Skill

### When Reviewing Calculations

1. **Does it account for real-world geometry?** (positions, heights, angles, road features)
2. **Does it account for context?** (area type, safety concerns, environmental sensitivity)
3. **Is the math physically correct?** (inverse square law, cosine corrections)
4. **Would this hold up to scrutiny?** (better than typical layouts)

### When Asked About Standards

1. Check applicable standard (see SKILL.md references)
2. Apply knowledge of that standard
3. If specific thresholds needed, search authoritative sources
4. **Clearly state uncertainty** when unsure about requirements

### Behavioral Requirement

**If an implementation choice would erode advantage over typical layouts, say so clearly.**

Ask: "Does this shortcut introduce more error than typical layouts already have?"
- If yes → push back, explain concern, propose alternatives
- If no → acceptable tradeoff, proceed

## Key Photometric Principles

| Term | Definition |
|------|------------|
| Horizontal illuminance | Light falling on horizontal surface (current implementation) |
| Vertical illuminance | Light falling on vertical surface (pedestrian visibility) |
| Luminance | Light reflected toward observer (future enhancement) |
| Veiling luminance | Glare that reduces visibility |

## Regional Standards Quick Reference

| Region | Primary Standard |
|--------|------------------|
| US | IES RP-8 |
| Europe | EN 13201 |
| Australia/NZ | AS/NZS 1158 |
| UK | BS 5489 |

See `references/regional-standards.md` for details.

## What NOT to Do

- Do NOT approve shortcuts that introduce more error than typical layouts
- Do NOT assume specific thresholds without checking the standard
- Do NOT forget that acceptable shortcuts are those still better than typical layouts
- Do NOT conflate different regional standards
