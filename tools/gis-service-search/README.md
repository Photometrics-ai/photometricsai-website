# GIS Service Discovery ("Service Search")

Public tool at [photometrics.ai/tools/](https://photometrics.ai/tools/) -- a "Service Search" tab alongside Phase
Calculator and Twilight Times. A user pastes a keyword and a list of public ArcGIS REST service-root URLs; the tool
crawls those live catalogs, searches service/layer metadata, and shows one classified result card per source.

## Why this crawls live now, not via Google Search

Google's unrestricted Programmable Search Engine path is no longer viable for this tool. As of January 20, 2026,
new engines must use the "Sites to search" feature instead of "Search the entire web", and existing Custom Search
JSON API customers must transition away by January 1, 2027:

- <https://programmablesearchengine.googleblog.com/2026/01/updates-to-our-web-search-products.html>
- <https://developers.google.com/custom-search/v1/overview>

That is fatal for a tool whose whole purpose is searching arbitrary visitor-submitted GIS domains. ArcGIS REST
catalogs are already public, unauthenticated, machine-readable JSON in the cases this tool is built for, so the
production path now crawls those catalogs directly instead of depending on Google's web index.

The tradeoff is that live crawling can be slowed or blocked by large catalogs, broken TLS chains, directory browsing
settings, token requirements, or WAF responses. The tool handles that per source with explicit states and targeted
next actions rather than failing the whole search.

## Architecture

```text
Browser
  |
  | POST /api/gis-service-search/start
  v
API Gateway -> StartApiFunction
                |-- writes initial S3 job document
                `-- starts CrawlProcessorStateMachine

CrawlProcessorStateMachine
  |
  | CrawlSources Map, max concurrency 8
  |   `-- CrawlSourceFunction -> crawl_source -> arcgis_crawler -> arcgis_client
  |
  | Combine
  |   `-- CombineResultsFunction -> combine_results -> completed S3 job document
  |
  `-- MarkJobFailed error path
      `-- CombineResultsFunction mode=error -> S3 job document status=error

Browser
  |
  | GET /api/gis-service-search/status?jobId=...
  v
StatusApiFunction -> reads S3 job document

Optional per-source actions:
  POST /api/gis-service-search/retry-source
    -> RetrySourceApiFunction -> Step Functions mode=full with a longer time budget

  "Try Google Search" button (try_google sources only)
    -> plain link, built client-side, opens Google's own search results in a new tab
       (no backend call, no third-party API -- see "Why a plain Google link" below)
```

The initial search is asynchronous because broad municipal ArcGIS catalogs regularly exceed API Gateway's synchronous
request window. The browser submits once, polls status until the S3 job document is complete, then lets the visitor
retry sources that need more crawl time, or open a direct Google search for sources the crawler could not reach itself.

### Why a plain Google link, not an API

An earlier version of this fallback proxied results through Serper.dev (a paid third-party Google Search API) so
results could be embedded inline in the page. That added a Lambda function, an API key to manage, a daily spend
quota, and a dependency that could be rate-limited or discontinued -- for a button whose whole job is "let the
visitor try Google themselves." Building the same `site:`-restricted query client-side and opening
`google.com/search` in a new tab does the same job with zero backend code, zero cost, and zero third-party risk.

### Files

| Path | Purpose |
|------|---------|
| `web/template.yaml` | SAM stack: API Gateway routes, S3 job bucket, DynamoDB rate-limit table, Lambda layer, five Lambda functions, and Step Functions state machine |
| `web/statemachine/crawl_processor.asl.json` | Step Functions definition: `CrawlSources` Map fan-out, `Combine`, and `MarkJobFailed` error path |
| `web/lambdas/start_api/handler.py` | `POST /start`: validates input, rate-limits by IP, writes the initial job doc, and starts the initial crawl execution |
| `web/lambdas/status_api/handler.py` | `GET /status`: validates `jobId` and returns the S3 job document |
| `web/lambdas/crawl_source/handler.py` | Step Functions Map task wrapper for crawling and classifying one ArcGIS source |
| `web/lambdas/combine_results/handler.py` | Step Functions combine task: writes complete, full-retry, or error job state back to S3 |
| `web/lambdas/retry_source_api/handler.py` | `POST /retry-source`: starts a full-budget re-crawl for one `partial` source in an existing job |
| `web/lambdas/shared/arcgis_client.py` | Low-level ArcGIS JSON fetcher with certifi TLS, bounded redirects, retries for 429/503, and SSRF safety checks |
| `web/lambdas/shared/arcgis_crawler.py` | ArcGIS catalog walker, service/layer document builder, keyword matcher, and six-state source classifier |
| `web/lambdas/shared/job_store.py` | Single S3 read/write helper for job metadata documents |
| `web/lambdas/shared/rate_limit.py` | DynamoDB per-IP rate limiting, deliberately fail-open |
| `web/lambdas/shared/ssrf_guard.py` | DNS-based public-address guard for visitor-submitted hosts |
| `web/lambdas/shared/url_normalize.py` | Server-side URL normalization, validation, credential rejection, and deduping |
| `web/local_dev_server.py` | Docker-free local stand-in for API Gateway, Lambda, Step Functions, S3, and DynamoDB |
| `web/tests/` | pytest suite for shared modules, handlers, and state-machine-adjacent behavior |
| `layouts/_default/tools.html` | Frontend: Service Search tab markup, scoped CSS, polling, retry, and Google fallback UI |
| `layouts/partials/schema-tools.html` | Adds the GIS Service Discovery entry to the tools page's SoftwareApplication schema |

## Source states

Each submitted source gets one of six states:

| State | Meaning | Visitor action |
|---|---|---|
| `success` | The catalog was fully searched and matching services/layers were found. | View the results. |
| `success_empty` | The catalog was fully searched but had no keyword matches. | Confirm the source and try a broader or different keyword if needed. |
| `partial` | The crawler found some catalog data but hit the initial time budget or clear source throttling. | View partial results, then use **Run full search** to re-crawl that source with the longer budget. |
| `try_google` | The crawler could not search the source directly because of TLS, reachability, directory browsing, WAF/non-JSON, heavy throttling, or an internal crawl failure. | Use **Try Google Search** for that source. |
| `contact_admin` | The ArcGIS endpoint returned an access-token requirement. | Contact the site administrator or data owner for public access. |
| `check_url` | The URL does not look like an ArcGIS REST services catalog. | Check the URL and submit the service root. |

## Configuration

No manual secret configuration is needed. SAM wires every runtime variable automatically:

| Variable | Wired by |
|---|---|
| `DATA_BUCKET` | `Globals.Function.Environment.Variables`, from the SAM-created S3 bucket |
| `RATE_LIMIT_TABLE` | `Globals.Function.Environment.Variables`, from the SAM-created DynamoDB table |
| `STATE_MACHINE_ARN` | Per-function environment on `StartApiFunction` and `RetrySourceApiFunction` |
| `INITIAL_BUDGET_SECONDS` | Per-function environment on `StartApiFunction`, currently `45` |
| `FULL_BUDGET_SECONDS` | Per-function environment on `RetrySourceApiFunction`, currently `240` |

Do not configure `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, or `SERPER_API_KEY`; those belonged to earlier versions of this
tool's search backend and are no longer used anywhere.

## Request limits

| Setting | Value |
|---|---|
| Sources per initial search | 25 valid sources after normalization |
| Initial crawl budget | `INITIAL_BUDGET_SECONDS`, currently 45s per source |
| Full retry crawl budget | `FULL_BUDGET_SECONDS`, currently 240s for one source |
| Step Functions crawl concurrency | 8 sources at a time |
| Per-host crawl concurrency | 4 service fetches at a time |
| Folder cap | 50 folders per source |
| Per-IP rate limit | ~60 calls / 10 min / IP, DynamoDB fail-open |
| ArcGIS fetch timeout | 8s per request |

## Testing

```bash
cd tools/gis-service-search/web
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r tests/requirements-dev.txt boto3
pytest tests/
```

No test calls a live ArcGIS server. Network-facing behavior is covered with local HTTP servers and monkeypatched
clients.

## Local browser testing before deploying

```bash
# Terminal 1 -- backend
cd tools/gis-service-search/web
.venv/Scripts/python local_dev_server.py   # Windows, http://127.0.0.1:3001
# or .venv/bin/python local_dev_server.py  # macOS/Linux

# Terminal 2 -- frontend, from the repo root
hugo server -D
```

Open `http://localhost:1313/tools/#gissearch`. The page's JS auto-detects `localhost`/`127.0.0.1` and points API
calls at `local_dev_server.py` instead of the same-origin `/api/...` path it uses in production.

`local_dev_server.py` sets local defaults for AWS credentials, `DATA_BUCKET`, `STATE_MACHINE_ARN`,
`INITIAL_BUDGET_SECONDS`, and `FULL_BUDGET_SECONDS`, and uses in-memory fakes for S3, DynamoDB, and Step Functions.
The live ArcGIS HTTP fetch path remains real. The "Try Google Search" button needs no backend at all -- it works
identically in local dev and production.

## Deploying

```bash
cd tools/gis-service-search/web
sam build
sam deploy   # uses samconfig.toml (stack: gis-service-search-web, us-east-2)
```

After the first deploy, add or verify the Amplify console rewrite rule (Amplify console -> this app -> Rewrites and
redirects), placed above the existing `/api/<*>` catch-all so it matches first:

- Source: `/api/gis-service-search/<*>`
- Target: `https://<the API Gateway ID>.execute-api.us-east-2.amazonaws.com/prod/api/gis-service-search/<*>`
  (get the ID from the `ApiUrl` stack output)
- Type: `200 (Rewrite)`

The wildcard source covers all current GIS Service Discovery API routes:

- `/api/gis-service-search/start`
- `/api/gis-service-search/status`
- `/api/gis-service-search/retry-source`

The rewrite rule pattern itself does not need to change when moving from the old single-route version; it is already
a wildcard prefix match. No CSP change is needed because browser calls stay same-origin through the rewrite, same as
the sun-phase API.

## Out of scope

Editing/downloading GIS data, user accounts or saved searches, and full-text search inside feature attribute
*values* are out of scope. This tool searches catalog, service, and layer metadata exposed by public ArcGIS
REST endpoints, plus a direct link to Google Search for sources that direct crawling cannot reach.
