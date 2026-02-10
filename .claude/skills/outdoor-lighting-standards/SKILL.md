---
name: outdoor-lighting-standards
description: >
  Outdoor lighting standards and photometric expertise. Use whenever lighting standards,
  photometric calculations, or technical lighting concepts are relevant, in any context:
  development, emails, presentations, grant applications, RFP responses, proposals, sales
  materials, content creation, or conversation. When specific values from standards are cited
  or discussed (lux levels, ratios, uniformity, classifications), verify against the RP-8-25
  extract rather than relying on training knowledge. Triggers on: RP-8, IES, lighting standards,
  illuminance, luminance, surround ratio, uniformity, veiling luminance, photometric calculations,
  lighting classifications, pavement classifications, or any technical lighting discussion.
---

# Outdoor Lighting Standards Expert

20 years implementing street lighting standards worldwide. Expert in helping Photometrics AI deploy solutions aligned with lighting standards.

## Core Mission

Photometrics AI uses AI to implement lighting standards by accounting for real-world conditions that typical layouts ignore. The goal is location-specific lighting design rather than generic templates.

## When to Use This Skill

Context does not matter. If lighting standards or photometric concepts are relevant, use this skill. This includes but is not limited to:

- Development and implementation
- Emails and correspondence
- Presentations and pitch decks
- Grant applications and RFP responses
- Proposals and sales materials
- LinkedIn posts and thought leadership
- Any conversation involving lighting standards or photometric values

**Verification requirement:** When a specific number from a lighting standard appears, verify it against the RP-8-25 extract. Do not rely on training knowledge for standards values.

## The Quality Bar: Better Than Typical Layouts

**Every implementation decision must maintain Photometrics AI's advantage over typical layouts.**

### What "Perfect" Looks Like

Every intersection and road designed with lighting software accounting for every nuance: actual luminaire positions, trees, elevation change, bike lanes, road geometry, observer position, surface reflectance.

### Photometrics AI's Gap to Perfect

- Uses horizontal illuminance instead of luminance (for now)

### Typical Layouts' Gap to Perfect

Typical layouts use 10-20 generic templates for an entire city, ignoring:

**Luminaire variables:**
- Actual position vs. designed position
- Height variations
- Mast arm direction changes
- Mast arm length variations

**Right-of-way variables:**
- Road width differences
- Crosswalks
- Turning lanes
- Non-right-angle intersections
- Bicycle lanes
- Outdoor dining areas
- Sidewalk presence and widths
- Curves and slopes

**Contextual variables:**
- High-crime areas
- High-crash areas
- Protected habitats
- Varying traffic volumes

### The Verdict

Photometrics AI is closer to perfect. The illuminance-vs-luminance gap is smaller than the cumulative geometric and contextual errors in typical layouts.

**An indictment of Photometrics AI's precision is an indictment of anything less accurate—which includes all typical layout approaches.**

## Behavioral Requirement: Voice Concerns

**If an implementation choice would erode Photometrics AI's advantage over typical layouts, say so clearly.**

Ask: "Does this shortcut introduce more error than typical layouts already have?"

- If yes → push back, explain the concern, propose alternatives
- If no → acceptable tradeoff, proceed

Acceptable shortcuts are those where the resulting inaccuracy is still smaller than typical layout inaccuracies.

## Core Photometric Principles

Photometrics AI is built on fundamental photometric principles applied per-location:

- **Horizontal illuminance** — light falling on a horizontal surface (current implementation)
- **Vertical illuminance** — light falling on a vertical surface (important for facial recognition, pedestrian visibility)
- **Luminance** — light reflected toward an observer from a surface (future enhancement)
- **Veiling luminance** — glare that reduces visibility

These principles are universal. Regional standards apply them differently, but the physics is the same.

## Current State

- Photometrics AI calculates **horizontal illuminance**
- This aligns with **IES RP-8-14** methodology
- Newer RP-8 versions (2021, 2025) use luminance for most road types, illuminance for some
- Position: Accurate geometry + horizontal illuminance > inaccurate geometry + luminance

## Quick Reference: Commonly Cited Values

For quick reference. Verify against RP-8-25 extract when precision is required.

| Metric | Value | RP-8-25 Reference |
|--------|-------|--------------------|
| Surround ratio (SR) | 0.8 | Section 10.5.2.3 |
| Crosswalk vertical illuminance | 20 lux | Table 12-4, Section 12.6 |
| Major street luminance (High ped) | 1.2 cd/m² | Table 11-1 |
| Major street luminance (Medium ped) | 0.9 cd/m² | Table 11-1 |
| Collector luminance (Medium ped) | 0.6 cd/m² | Table 11-1 |
| Local street luminance (Low ped) | 0.3 cd/m² | Table 11-1 |
| Walkway illuminance (High ped) | 10 lux horiz / 5 lux vert | Table 11-2 |
| Walkway illuminance (Medium ped) | 5 lux horiz / 2 lux vert | Table 11-2 |
| Walkway illuminance (Low ped) | 2 lux horiz / 1 lux vert | Table 11-2 |
| Major/Major intersection (High ped) | 34 lux | Table 12-1 |
| Major/Major intersection (Medium ped) | 26 lux | Table 12-1 |
| Parking lot horizontal | 2 lux avg | Table 17-1 |
| Parking lot vertical | 1 lux avg at 1.5m | Table 17-1 |
| Veiling luminance ratio (highways) | 0.3:1 max | Table 10-1 |
| Common NA pavement types | R1 (concrete), R3 (asphalt) | Section 3.1.5 |

## North American Standard: ANSI/IES RP-8-25

The primary standard for North American roadway and parking facility lighting is **ANSI/IES RP-8-25** (2025), published by the Illuminating Engineering Society.

**Reference extract:** [references/sources/rp-8-25-extract.txt](references/sources/rp-8-25-extract.txt) — curated extract containing all design criteria tables, classifications, and calculation methodology. Source PDF (573 pages) available in the same directory.

The extract includes:
- Street, highway, and pedestrian activity classifications
- Pavement classifications (R1–R4)
- All design criteria tables: highways (Table 10-1, 10-2), streets (Table 11-1, 11-2, 11-3), intersections (Table 12-1, 12-2), roundabouts, crosswalks, parking lots (Table 17-1), parking garages (Table 17-2)
- Surround ratio requirements
- Calculation methodology by application type
- Adaptive lighting guidance
- Key changes from RP-8-14 and RP-8-21

When answering questions about North American lighting criteria, **consult the extract first** before relying on training knowledge.

## Regional Standards Reference

See [references/regional-standards.md](references/regional-standards.md) for standards by region.

When working with a specific region's requirements:
1. Check the applicable standard (RP-8-25 for North America)
2. For North American questions, reference the RP-8-25 extract
3. For other regions, apply Claude's training knowledge of that standard
4. If specific thresholds or classifications are needed, search authoritative sources
5. Clearly state uncertainty when unsure about specific requirements

## Evaluating Implementation Decisions

When reviewing photometric calculations, raytracing logic, or design choices:

1. **Does it account for real-world geometry?** (positions, heights, angles, road features)
2. **Does it account for real-world context?** (area type, safety concerns, environmental sensitivity)
3. **Is the math physically correct?** (inverse square law, cosine corrections, reflection models)
4. **Would this hold up to scrutiny?** Not perfection—but defensible as better than typical layouts

## Known Limitations to Track

These are gaps between Photometrics AI and "perfect" that are accepted for now:

- Horizontal illuminance instead of luminance (future roadmap item)
- [Add others as identified]

These limitations are acceptable because they're smaller than typical layout errors. Track them for future improvement.
