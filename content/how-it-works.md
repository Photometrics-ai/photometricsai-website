---
title: "How It Works"
subtitle: "Every light has a story. We read it."
description: "Discover how to reduce streetlight energy by 35% without hardware changes. Photometrics AI uses GIS-based Target Lighting Layers and AI optimization to deliver precision dimming through your existing networked lighting controls."
---

## The Core Idea

Today, most street lights run on simple timers — full brightness from dusk to dawn, regardless of what's actually happening on the ground. A light over a busy crosswalk runs at the same level as one illuminating an empty field. A residential cul-de-sac blazes at the same intensity as a six-lane highway interchange.

Photometrics AI changes that. We analyze the **unique context of every single light** — its height, optic type, the road geometry it serves, nearby land use, adjacent fixtures whose beams overlap — and calculate the precise dimming level that delivers the right amount of light, in the right place, at the right time.

This isn't blanket dimming. It's not "reduce everything by 30% after midnight." It's **per-luminaire optimization** — a custom instruction for each fixture, grounded in physics and real-world GIS data, verified against IES lighting standards.

The result: energy savings of 25-50% while *maintaining or improving* lighting quality where it matters most.

<div style="border-top: 1px solid var(--border-dark); margin: var(--space-xl) 0 var(--space-lg);"></div>

<div style="margin: 0 0 var(--space-xl); text-align: center;">
  <img src="/images/how-it-works-system.png" alt="Photometrics AI system diagram showing four integrated components: Target Lighting Layer mapping, AI-accelerated Optimization Engine, Dynamic Scheduling, and Lighting Controls System Integration" style="max-width: 100%;">
  <p style="font-size: 0.85rem; color: var(--text-subtle); margin-top: var(--space-sm);">Four integrated components — from GIS mapping to your existing lighting controls</p>
</div>

<h2 style="margin-top: 0; padding-top: 0; border-top: none;">The Four Components</h2>

<div class="features-grid" style="margin-bottom: var(--space-xl);">
  <div class="feature-card glass-card">
    <div class="feature-icon">1</div>
    <h3>Target Lighting Layer</h3>
    <p>GIS-based maps specifying desired illumination levels for every zone in your coverage area.</p>
    <ul>
      <li>Crosswalks: 20 lux</li>
      <li>Major roads: 11-18 lux</li>
      <li>Local streets: 7 lux</li>
      <li>Sidewalks: 2 lux</li>
      <li>Building footprints: 0 lux</li>
    </ul>
    <p>Dynamic variations for Halloween, late night, migratory bird protection, demand response, and special events.</p>
  </div>

  <div class="feature-card glass-card">
    <div class="feature-icon">2</div>
    <h3>Optimization Engine</h3>
    <p>AI-accelerated system that finds the optimal dimming level (0-100%) for each luminaire.</p>
    <ul>
      <li>Tests thousands of configurations in minutes</li>
      <li>Accounts for overlapping beam spreads</li>
      <li>Uses real-world geometry (slopes, intersections, mast arm positions)</li>
      <li>Generates in-house labeled training data</li>
    </ul>
    <p>Human eyes cannot perceive brightness changes under 20%—significant optimization headroom exists.</p>
  </div>

  <div class="feature-card glass-card">
    <div class="feature-icon">3</div>
    <h3>Dynamic Scheduling</h3>
    <p>Priority-based calendar resolving which lighting instruction runs at any given time.</p>
    <p><strong>Priority hierarchy (highest to lowest):</strong></p>
    <ol>
      <li>Emergency dispatch (CAD integration)</li>
      <li>Grid emergency (demand response)</li>
      <li>Transportation safety</li>
      <li>Crime prevention</li>
      <li>Special events</li>
      <li>Environmental protection (BirdCast)</li>
      <li>Default operating profile</li>
    </ol>
    <p>Higher priorities are never degraded for lower ones.</p>
  </div>

  <div class="feature-card glass-card">
    <div class="feature-icon">4</div>
    <h3>NLC Integration</h3>
    <p>API communication with your existing lighting control platforms.</p>
    <p><strong>We receive:</strong></p>
    <ul>
      <li>Asset inventory</li>
      <li>Luminaire locations</li>
      <li>IES file assignments</li>
      <li>Current schedules</li>
    </ul>
    <p><strong>We send:</strong></p>
    <ul>
      <li>Optimized per-luminaire dimming</li>
      <li>Schedule assignments</li>
    </ul>
    <p>Currently integrated with 2 major lighting control systems.</p>
  </div>
</div>

## Processing Speed

For a 2,000-light project:
- **Traditional method:** Days to weeks
- **Photometrics AI:** 3-5 minutes

## Standards Compliance

Photometrics AI optimizes to meet:
- **ANSI/IES RP-8** (US roadway lighting)
- **CIE 115** (International)
- **AS/NZS 1158** (Australia/New Zealand)

Typical compliance rate: **91-97%** of calculation points meet or exceed standards.

## What Photometrics AI Adds (vs. NLCs alone)

Your networked lighting controls provide the infrastructure—communications, metering, health monitoring, on/off control.

Photometrics AI adds the **intelligence**:
- Photometric optimization based on actual physics
- Per-luminaire dimming (not one-size-fits-all)
- Standards compliance verification
- Dynamic context-aware scheduling
- Multi-priority resolution
