# Photometrics AI Website

Hugo static site for photometrics.ai marketing website.

## Site Purpose & Strategy

This site uses **gap selling** — a sales methodology that drives action by making the visitor feel the distance between their current state and a better future state. Every page and section should reinforce this framework:

### Gap Selling Structure (Homepage)

1. **Current State (The Injustice)** — Establish that street lighting hasn't changed in 100 years. Specific, emotional pain points: birds dying, children in darkness, dangerous crosswalks, rain-blind intersections. The visitor should feel that the status quo is unacceptable.

2. **Future State (The Vignettes)** — Cinematic video scenarios showing what *should* happen. Each vignette pairs a human moment with an intelligent lighting response. The visitor should feel the gap between what exists and what's possible.

3. **The Bridge (The How)** — Photometrics AI closes the gap. Software-only, no hardware, works with existing infrastructure. This must feel simple and inevitable — the gap is big, and the fix is small.

4. **Call to Action** — Drive toward a demo or conversation. The visitor should feel urgency from the gap, not from pressure tactics.

### Content Guidelines

- **Lead with emotion, follow with logic.** Vignettes come before technical details.
- **Specificity over abstraction.** "Birds die colliding with over-lit buildings during migration" not "lighting causes environmental harm."
- **The product is the bridge, not the hero.** The gap (current vs. future) is the story. Photometrics AI is just how you get there.
- **No jargon in storytelling sections.** Technical depth lives on How It Works and Benefits pages, not in the emotional narrative.
- **Every page should connect back to the gap.** Even technical pages should remind the visitor why this matters.

## Tech Stack

- **Static Site Generator:** Hugo
- **Hosting:** AWS Amplify
- **Repository:** GitHub (Photometrics-ai/photometricsai-website)

## Development

```bash
# Run local dev server
hugo server -D

# Build for production
hugo --minify
```

## Deployment

Deployment is a **two-step process**:

### Step 1: Push to GitHub

**IMPORTANT: Always commit ALL changed files.** Don't cherry-pick specific files. Git tracks what changed since last commit - just add everything:

```bash
git add -A
git commit -m "Your commit message"
git push origin master
```

This is how normal git workflows work - you sync all changes, not just some. Selecting specific files leads to missing dependencies (e.g., pushing a partial but not the layout that includes it).

### Step 2: Trigger AWS Amplify Build

Amplify sometimes auto-detects pushes, but often needs manual trigger:

```bash
# Trigger deployment via AWS CLI
aws amplify start-job --app-id d22p16j9j2s18f --branch-name master --job-type RELEASE

# Check build status
aws amplify list-jobs --app-id d22p16j9j2s18f --branch-name master --max-results 1

# Get detailed job info
aws amplify get-job --app-id d22p16j9j2s18f --branch-name master --job-id <JOB_ID>
```

### Amplify App Details

- **App ID:** `d22p16j9j2s18f`
- **App Name:** `photometricsai-website`
- **Region:** `us-east-2`
- **Branch:** `master`
- **Console:** https://us-east-2.console.aws.amazon.com/amplify/home?region=us-east-2#/d22p16j9j2s18f

### Build Time

Typical build + deploy takes ~90 seconds.

### Troubleshooting

If site doesn't update after deploy:
1. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Check in incognito/private window
3. Verify build succeeded: `aws amplify list-jobs --app-id d22p16j9j2s18f --branch-name master --max-results 1`
