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

## Civil Lighting Design Newsletter (`content/civil-lighting-design/`, `tools/civil-lighting-design/`)

A separate EvariLABS newsletter (signup page at `/civil-lighting-design/`), sent via Buttondown (account username `civillightingdesign`), styled as a civil-engineering plan sheet — a deliberate visual exception from the main brand. The sheet identity is modeled directly on real DOT plan sheets (checked against a DelDOT construction plan sheet): border frame (neatline) with grid-reference ticks, dashed matchline dividers with end ticks, and a lineweight-hierarchical title block (heavy outer border, thin internal grid). Typeface is Overpass/Overpass Mono site-wide (chosen because Overpass was originally drawn from U.S. highway signage lettering), all-caps on every piece of "sheet furniture," and an italic/roman split on story attributions that mirrors the existing-vs-proposed convention on real sheets (external/reported stories get an italic source line; original Photometrics.ai stories don't). Because email clients don't reliably load custom fonts for live text, the masthead+STA line, matchline dividers, and title block are rasterized to PNG at build time in the real typeface with exact lineweights — see `tools/civil-lighting-design/sheet_assets.py` for the rasterization and the full reasoning. Assets and generator scripts live in `tools/civil-lighting-design/`: font files (`fonts/`), `sheet_assets.py`, and `build_issue.py`, which assembles each issue's complete HTML/plain-text **locally** (and calls into `sheet_assets.py` to regenerate the per-issue masthead/title-block images) — Buttondown has no confirmed template variable for per-issue body content, so the script bakes date/issue number/content into static HTML at generation time rather than relying on Buttondown-side template substitution (see comments in `build_issue.py` for the full reasoning). The only Buttondown-side variable used is `{{ unsubscribe_url }}`, which is documented and confirmed to work directly inside email body content. Deploying an issue requires pushing the newly generated PNGs under `static/images/civil-lighting-design/` (via the normal `git add -A` / Amplify deploy flow) *before* sending, since Buttondown emails load them by URL, not inline.

### Link backlog workflow

Ari sends story links (studies, industry news, standards updates) whenever he finds one — not tied to any particular issue being in progress.

**If Ari pastes a URL and asks to save it / add it to the newsletter / queue it for a future issue:**

1. Read `tools/civil-lighting-design/link-backlog.json` (array of entries; empty array if nothing queued yet).
2. Fetch the URL, draft a `headline` and a short factual 1-2 sentence `summary` — concise and factual, not gap-selling copy; this is a roundup.
3. Guess a `section`: `"From Photometrics.ai"` (company-authored), `"Around the Industry"` (general industry news), or `"Standards and Committees"` (standards-body/regulatory) — this is a guess for Ari to correct later, not a final assignment.
4. Append `{url, date_added, headline, summary, section, status: "unused", used_in_issue: null}` and write the file back.
5. Confirm briefly what was added — don't just silently write the file.

This works from any Claude Code session on this repo (local terminal, desktop app, or claude.ai/code from mobile) since it only needs git read/write access — no dependency on the local-only Buttondown API key or AWS credentials that live on Ari's machine.

**When actually building an issue:** pull unused entries (oldest first, or whichever Ari points at), confirm with him the summaries are still accurate, then feed the finalized set into `build_issue.py`'s `ISSUE` structure, regenerate, and mark those entries `"status": "used"` with `used_in_issue` set.

## Sun Phase Tools (`tools/sun-phase/`)

Astronomical sun calculation toolkit for streetlight operations. Contains CLI tools, a desktop GUI, and an AWS Lambda backend (SAM).

### Architecture

`sun_utils.py` is the core math library. Everything else builds on it:
- **CLI tools**: `phase_calculator.py` (tag CSV records with twilight phase), `twilight_times.py` (yearly schedules)
- **`core/`**: Wrapper modules (`phase_processor.py`, `twilight_processor.py`) used by CLI and GUI
- **`gui/`**: Desktop app (`app.py` + `tabs/`) using CustomTkinter
- **`web/`**: SAM stack — Lambda functions, shared layer, Step Functions state machine

Code is intentionally duplicated across CLI and Lambda (`sun_utils.py` exists in both `tools/sun-phase/` and `tools/sun-phase/web/layers/deps/`) for deployment isolation. When you change `sun_utils.py`, you must update both copies.

### Frontend

The tools web UI lives in Hugo, not in `tools/sun-phase/`:
- **Layout**: `layouts/_default/tools.html` (markup + inline JS)
- **Styles**: inline `<style>` block in the template (no separate CSS file)
- **Content**: `content/tools.md`

API routing: `photometrics.ai/tools/` → `/api/*` → Amplify rewrite → API Gateway (`xtfuhgnw3k.execute-api.us-east-2.amazonaws.com/prod`) → Lambda. Amplify has a rewrite rule that proxies `/api/<*>` directly to API Gateway (status 200), so all API calls are same-origin from the browser's perspective — no CORS headers needed on Lambdas. The S3 DataBucket CORS config allows direct PUT uploads from `https://photometrics.ai` and `https://www.photometrics.ai`.

### AWS Infrastructure (SAM stack: `tools/sun-phase/web/`)

Stack name: `sun-phase-web` | Region: `us-east-2` | Config: `web/samconfig.toml`

**S3 Buckets:**
- **DataBucket** — Temp storage for user CSV uploads and processed chunks. Auto-expires after 3 days. CORS allows PUT/GET from `photometrics.ai` and `www.photometrics.ai`.

**API Gateway** (Regional, stage: `prod`):
Routes map to Lambda functions — all share the `DepsLayer` (pandas, pytz, timezonefinder, sun_utils, phase_calculator_core, twilight_core).

**Lambda Functions (8 total):**

| Function | Route / Trigger | What it does |
|----------|----------------|--------------|
| `twilight_api` | `GET /api/twilight` | Generates yearly twilight CSV for a lat/lon/year. Returns CSV blob. |
| `phase_api` | `POST /api/phase` | Synchronous JSON endpoint — up to 10k rows, returns sun elevation + phase. |
| `phase_csv_api` | `POST /api/phase/csv` | Synchronous CSV endpoint — send CSV text, get CSV back with phase columns appended. |
| `upload_initiator` | `POST /api/phase/upload` | Creates job ID, returns presigned S3 PUT URL for direct browser→S3 upload. |
| `detect_columns` | `POST /api/phase/detect-columns` | Reads first rows from S3, auto-detects lat/lon/date/time columns. |
| `start_processing` | `POST /api/phase/start` | Writes job metadata to S3, starts Step Functions execution. |
| `status_api` | `GET /api/phase/status` | Polls job metadata from S3, returns status + download URL when complete. |
| `splitter` | Step Functions | Reads uploaded CSV from S3, splits into chunks, writes chunks back to S3. |
| `chunk_processor` | Step Functions (Map, 10x parallel) | Processes one chunk: calculates sun elevation + phase for each row. |
| `combiner` | Step Functions | Combines processed chunks into final CSV, writes result + presigned download URL. |

**Step Functions State Machine** (`phase_processor.asl.json`):
```
Split → ProcessChunks (Map, 10 concurrent) → Combine
```
Handles large CSV files (up to 2.5M rows) by splitting into chunks processed in parallel. Each step catches errors and routes to FailState.

**Data flow for Phase Calculator (large file upload):**
1. Browser → `upload_initiator` → gets presigned URL
2. Browser → PUT directly to S3 (DataBucket)
3. Browser → `detect_columns` → reads S3 file header, returns column names
4. Browser → `start_processing` → starts Step Functions
5. Step Functions: `splitter` → `chunk_processor` (×N parallel) → `combiner`
6. Browser polls `status_api` → gets download URL when complete

### Running CLI Locally

```bash
cd tools/sun-phase
pip install -r requirements.txt

# Generate twilight schedule
python twilight_times.py --lat 33.75 --lon -117.87 --year 2026 --output schedule.csv

# Tag a CSV with sun phase
python phase_calculator.py input.csv output.csv --lat LAT --lon LON --date DATE --time TIME
```

### Deploying Lambda Backend

The SAM stack deploys separately from the Hugo site:

```bash
cd tools/sun-phase/web
sam build
sam deploy          # uses samconfig.toml defaults (us-east-2, sun-phase-web stack)
```

### Key Files

| File | Purpose |
|------|---------|
| `tools/sun-phase/sun_utils.py` | Core astronomical calculations (CLI copy) |
| `tools/sun-phase/web/layers/deps/sun_utils.py` | Core astronomical calculations (Lambda copy — keep in sync) |
| `tools/sun-phase/web/layers/deps/phase_calculator_core.py` | Shared phase calculation logic for Lambda |
| `tools/sun-phase/web/layers/deps/twilight_core.py` | Shared twilight calculation logic for Lambda |
| `tools/sun-phase/web/template.yaml` | SAM/CloudFormation — all AWS resources defined here |
| `tools/sun-phase/web/samconfig.toml` | SAM deploy config (stack name, region) |
| `tools/sun-phase/web/statemachine/phase_processor.asl.json` | Step Functions definition |
| `tools/sun-phase/web/lambdas/*/handler.py` | Individual Lambda function handlers |
| `tools/sun-phase/phase_calculator.py` | CLI: tag CSV records with twilight phase |
| `tools/sun-phase/twilight_times.py` | CLI: generate yearly streetlight schedules |
| `tools/sun-phase/main_gui.py` | Desktop GUI entry point |
| `layouts/_default/tools.html` | Hugo layout (markup + inline JS) |
| (inline `<style>` in tools.html) | Tool-specific component styles |

## Take Action Lambda (`lambda/take-action/`)

Backend for the citizen-advocacy tool at `/take-action/` — a visitor picks a street-lighting priority, the Lambda finds their local officials and drafts a letter, and can send it to those officials on the visitor's behalf. The Google Ads campaign that drives traffic here is tracked outside this repo, in the separate `Ads` repo's `google/take-action-campaign.md`.

- **Function:** `photometrics-take-action`
- **Region:** `us-east-2`
- **Account:** `794038225197`
- **Role:** `photometrics-take-action-lambda-role`
- **Source:** `lambda/take-action/lambda_function.py` (single file)

### Routing

A Lambda Function URL, dispatched on `rawPath`:
- `/generate` — search for local officials, draft a letter, write a generate row
- `/send` — managed SES send to the officials verified during that session's `/generate`
- `/track` — event tracking
- `/flag` — a visitor flags an official's address as no longer current
- an SNS branch (not a `rawPath` route) — receives SES bounce/complaint notifications and records them

### Environment variables (names only — never a value here)

`DYNAMODB_TABLE`, `BOOSTED_TABLE`, `FLAGGED_TABLE`, `SEND_LOG_TABLE`, `BOUNCE_TABLE`, `ANTHROPIC_API_KEY`, `GOOGLE_CIVIC_API_KEY`, `SES_SENDER_EMAIL`, `SES_CONFIGURATION_SET`.

### DynamoDB tables

| Table | Key |
|---|---|
| `photometrics-take-action` | PK `session_id` — generate rows |
| `photometrics-take-action-sends` | PK `session_id` — send rows |
| `photometrics-email-bounces` | PK `email`, SK `timestamp` — bounce/complaint events |
| `photometrics-flagged-officials` | PK `email` — user-flagged ("Not current?") addresses |
| `photometrics-boosted-officials` | PK `region`, SK `email` — boosted/trusted officials |

### SNS bounce wiring

SES configuration set `take-action-sends` → SNS topic `photometrics-ses-bounces` → this Lambda → `photometrics-email-bounces`. A bounce addressed to the sender itself (`SES_SENDER_EMAIL`) is logged loudly (`WARNING: bounce for sender address ... — not recording`) and NOT written to the table — this keeps the sender's own address from ever ending up excluded via `get_bounced_emails()`.

### Deploy

```bash
bash lambda/take-action/deploy.sh           # real deploy
bash lambda/take-action/deploy.sh --dry-run # print the plan, make no AWS calls
```

Packages `lambda_function.py` into `function.zip`, updates the function code, waits for the update to settle, then compares the local artifact's SHA-256 to the deployed `CodeSha256` and fails loudly on a mismatch. `zip` is absent on this host, so the script falls back to a Python `zipfile`-module packer. Currently deployed `CodeSha256`: `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=` (as of 2026-09-03).

### Tests

```bash
python -m pytest lambda/take-action/tests -q
```

20 tests, all green. `moto` is not installed — the module-level `dynamodb`/`ses` clients are monkeypatched with in-repo fakes, so no test touches real AWS.

### Harness

`lambda/take-action/tools/funnel_test.py` — subcommands `seed`, `send`, `wait-bounce`, `check-sends`, `check-exclusion`, `check-regenerate`, `cleanup`, `all`. Seeds DynamoDB directly and drives `/send` via the AWS Lambda Invoke API; it never calls `/generate`. Every representative address is an SES mailbox-simulator address (`success@simulator.amazonses.com`, `bounce@simulator.amazonses.com`, plus-variants); the only real inbox it ever touches is `ari@sdgis.com` as CC. `check-regenerate` proves a hard-bounced (and simultaneously boosted/trusted) address is suppressed at send time rather than mailed.

### Report

```bash
python lambda/take-action/tools/report.py            # markdown to stdout
python lambda/take-action/tools/report.py --out DIR   # also write cut1.csv / cut2.csv / totals.csv
```

Read-only: joins generate rows to send rows on `session_id` and cuts the result two ways — (ad group × keyword × top priority × location) and (top priority × state) — plus a totals row. Ad-group names resolve through `lambda/take-action/tools/adgroups.json`, which currently maps placeholder ids `TBD-1`..`TBD-7` to the 7 real ad group names; those placeholders need to be swapped for the real numeric Google Ads ad group ids before `source.utm_content` on real traffic resolves to a name instead of printing raw.

### Data contract

- **Generate row** (`photometrics-take-action`): `source` — a map of up to 9 keys (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `utm_match`, `gclid`, `landed_priorities`, `referrer`), each present only if non-empty; `location_city`, `location_state`, `location_country` — normalized from the visitor's raw location string via Haiku's `normalized_location` field, falling back to a raw-string parse and `"US"` when that field is absent.
- **Sends row** (`photometrics-take-action-sends`): `priorities`, `source`, `location_city`, `location_state` copied from the matching generate row whenever present; `representatives_offered` (count of officials on the generate row); `representatives_failed` — a list of `{email, reason}`, `reason` ∈ `suppressed` (address is hard-bounced or flagged) | `ses_error` (SES rejected the send).
- **Frontend `/generate` payload** (`layouts/_default/take-action.html`): existing keys plus `source` — the visitor's first-touch campaign attribution (same key set as above), captured once per session and persisted in `sessionStorage['ta_source']` so later actions in the same session agree with it. This frontend change is live in production (commit `ac10a0b`, Amplify job 164).
- **GA4 params** added to `take_action_submit`, `send_intent_clicked`, and `send_confirmed`: `landed_priorities`, `utm_content`, `preselected` (boolean — true only when the page loaded with at least one valid `?priorities=` value).
