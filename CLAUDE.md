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

The frontend calls the Lambda backend via `/api` (same-origin). Amplify has a rewrite rule that proxies `/api/<*>` → `https://tools.photometrics.ai/api/<*>` (status 200), so all API calls are same-origin from the browser's perspective — no CORS headers needed on Lambdas. The S3 DataBucket CORS config allows direct PUT uploads from both `tools.photometrics.ai` and `photometrics.ai`.

### AWS Infrastructure (SAM stack: `tools/sun-phase/web/`)

Stack name: `sun-phase-web` | Region: `us-east-2` | Config: `web/samconfig.toml`

**S3 Buckets:**
- **DataBucket** — Temp storage for user CSV uploads and processed chunks. Auto-expires after 3 days. CORS allows PUT/GET from `tools.photometrics.ai` and `photometrics.ai`.
- **FrontendBucket** — Serves the old standalone frontend via CloudFront (will become unused after migration redirect). Private, CloudFront OAC only.
- **LogBucket** — CloudFront access logs. Auto-expires after 30 days.

**CloudFront Distribution** (`tools.photometrics.ai`):
- Default behavior → FrontendBucket (S3 via OAC)
- `/api/*` → API Gateway origin (cache disabled, all HTTP methods)
- Custom domain with ACM cert (must be us-east-1 for CloudFront)

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
