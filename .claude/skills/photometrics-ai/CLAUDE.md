# Claude Instructions: Photometrics AI

## When to Invoke This Skill

Use this skill when the user needs help with:
- Sales materials, proposals, presentations, pitch decks
- Technical discussions about the product
- Understanding how Photometrics AI works
- Competitive positioning questions
- Go-to-market strategy
- Content creation about street lighting optimization

**Trigger phrases:**
- "Help me write a proposal for..."
- "How does Photometrics AI work?"
- "What's our competitive advantage?"
- "Create a pitch deck for..."
- "Explain Target Lighting Layers"

## Core Principle

**Photometrics AI is software-only. No hardware. No retrofits. No field activity.**

It determines optimal operating parameters for each luminaire based on real-world geography and sends those parameters to existing lighting control systems via API.

## How to Use This Skill

### Before Writing Content

1. Read SKILL.md for complete product knowledge
2. Check reference files for specific topics:
   - `references/value-proposition.md` - Benefits by stakeholder
   - `references/technical.md` - Architecture, TLL, optimization engine
   - `references/competitive.md` - Market positioning, GRADIS comparison
   - `references/gtm.md` - ICP, pricing, pilots, sales channels

### For Financial Questions

**Use the photometrics-ai-financials skill instead** for:
- ROI calculations
- Value per light figures
- Energy savings math
- Source verification for numbers

## Key Facts

| Fact | Value |
|------|-------|
| Deployed lights | 0 (as of Jan 2025) |
| Pipeline | 8,500 (TN) + 2,000 (MS) |
| NLC integrations | 2 major systems |
| Patents | 1 granted, 1 issuing, 1 continuation |
| Operating hours | ~4,100 hrs/year (dusk-to-dawn) |

## The 4 Components

1. **Target Lighting Layer (TLL)** - GIS maps specifying illumination by zone (Patent: US9894736B2)
2. **Optimization Engine** - AI-accelerated testing of configurations (Patent pending: 18/660,680)
3. **Dynamic Scheduling** - Priority-based calendar for lighting instructions
4. **NLC Integration** - API to lighting control platforms

## Current Photometric Approach

Currently calculates **horizontal illuminance** only. Vertical illuminance and luminance are planned but not yet implemented. If a project requires these, it becomes a top development priority.

**Practical note:** Horizontal illuminance is a reasonable proxy for most applications. 20 lux horizontal ≈ 20 lux vertical at the same location (not exact, but close enough for optimization work).

See **outdoor-lighting-standards** skill for detailed photometric principles.

## Priority Hierarchy (Never Compromised)

1. Dispatch (CAD integration)
2. Demand Side Management (grid emergencies)
3. Transportation Safety (crosswalks, bike lanes)
4. Crime Prevention (high-risk areas)
5. Special Events (MLB games, Halloween)
6. Migratory Birds (BirdCast integration)
7. Default (on at dusk, midnight dimming, off at dawn)

## What NOT to Claim

- "X streetlights in active deployment"
- "Running in Memphis right now"
- Any deployed/operational claims until projects go live
- Specific savings percentages without checking financials skill

## Relationship to Other Skills

| Question Type | Use This Skill? |
|---------------|-----------------|
| How does TLL work? | ✅ Yes |
| What's the ROI? | ❌ Use photometrics-ai-financials |
| Write a grant application | ✅ Yes + proposal-grantwriter |
| Source for $51.09? | ❌ Use photometrics-ai-financials |
