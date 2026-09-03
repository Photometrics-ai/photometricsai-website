You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-source-and-location
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Store campaign attribution (`source` map) and a normalized city/state/country on the generate row, including asking Haiku for normalized_location, so the report tool can group sessions by ad group, keyword and place.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Add campaign attribution and a normalized location to the Take Action generate row, so every session can later be attributed to an ad group / keyword / city.

REPO / FILE
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly one file: C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py. Do not edit any other file except your handoff.

REQUIRED READING (in order)
1. .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md — the immediately preceding change to this same file. Your edit builds on it; do not revert or reflow any of it.
2. lambda_function.py: handle_generate (~:757), log_generation (~:706), search_officials (~:202, ~220 lines including the Haiku prompt and its JSON/tool schema; the model response JSON is parsed around :380-425), parse_location (~:194), sanitize_string (~:97).

WHAT TO IMPLEMENT
1. `source` capture. handle_generate accepts body['source'] as a dict. Sanitize per contract (below) and pass it through to log_generation so it lands on the generate row as a DynamoDB map of strings. Prefer a small dedicated helper (e.g. `sanitize_source(raw) -> dict`) so it is unit-testable in isolation — a sibling item's pytest suite will import and exercise it.
2. `normalized_location`. Extend the existing Haiku prompt and its JSON/tool schema in search_officials so the model also returns `normalized_location: {"city": str, "state": str, "country": str}` — state as the 2-letter US postal code when the location is in the US, country as an ISO-2 code. Read the current prompt and schema carefully and keep the change MINIMAL: add the field, describe it in one or two sentences, do not restructure the prompt, do not rename existing fields, do not change what officials the model is asked for.
3. Parse it where the model JSON is already parsed. Return/propagate city/state/country to handle_generate and store them on the generate row as `location_city`, `location_state`, `location_country`. Fallback chain, and it must never raise: if `normalized_location` is missing or not a dict, or a field is empty/whitespace, fall back to parse_location(location) for city and state and to 'US' for country. Sanitize each to a sane length (<=100). Omit any attribute that is still empty (DynamoDB rejects empty S).

HARD CONSTRAINTS
- Nothing in the LETTER prompt (call_claude) changes. A verifier diffs call_claude against git HEAD and expects it identical.
- Do not touch handle_send, log_send, get_verified_representative_emails, already_sent, or the exclusion functions — the previous item just changed those and its work must survive your edit intact.
- Do NOT call /generate to test. The phase budget is 2 /generate calls total and both are reserved for another item. Verify statically and by exercising your pure helpers offline (`AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c "import sys;sys.path.insert(0,'lambda/take-action');import lambda_function as lf; ..."` — module import creates boto3 clients but makes no network calls).
- Do not deploy. Do not make AWS write calls.

DATA CONTRACT (generate row — photometrics-take-action, PK session_id) — new attributes:
- `source` (M): string keys utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer. Each value sanitized to <=200 chars. Absent/empty keys omitted. Whole map omitted if empty. Unknown keys dropped.
- `location_city` (S), `location_state` (S, 2-letter US code when US), `location_country` (S, ISO-2).
Existing fields unchanged.
Context you do not need to implement: the frontend sends this `source` object in the /generate payload (another item), and Google Ads will populate utm_content with a numeric ad group id.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
All acceptance criteria met; ast.parse clean; handoff at .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md containing the full diff, the before/after text of the Haiku prompt fragment and schema you changed (quoted verbatim), and the output of an offline exercise of your sanitizer showing: unknown key dropped, 250-char value truncated to 200, empty map omitted, and normalized_location fallback producing city/state from parse_location plus country 'US'.

ACCEPTANCE CRITERIA:
- handle_generate reads body['source'], accepts only the 9 contract keys (utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer), drops unknown keys, coerces values to str, truncates each to 200 chars, omits keys whose value is empty after sanitization, and omits the whole `source` attribute when the resulting map is empty or the request had no source.
- The generate row written by log_generation carries `source` (M of S) when non-empty, and `location_city` (S), `location_state` (S), `location_country` (S) when non-empty.
- search_officials' Haiku prompt and JSON/tool schema request a `normalized_location` object with keys city, state (2-letter US code when US), country (ISO-2); the response parser reads it if present.
- Fallback is robust: if normalized_location is absent, unparseable, or partially empty, city/state fall back to parse_location(location) and country falls back to 'US'. A missing field never raises and never blocks letter generation.
- call_claude and the letter prompt are unchanged; the officials-search behaviour (which officials are returned, and the hard filter added by p2-exclusion-hardening) is unchanged.
- The file parses (ast.parse) and the working-tree diff touches only lambda_function.py.
- No AWS calls, no /generate call, no deploy.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py
- python -c "import ast;ast.parse(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read());print('SYNTAX OK')"
- grep -n 'normalized_location\|location_city\|location_state\|location_country' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py
- cd C:/Users/aisaa/Projects/photometricsai-website && python - <<'PY'
import re,subprocess
new=open(r'lambda/take-action/lambda_function.py',encoding='utf-8').read()
old=subprocess.run(['git','show','HEAD:lambda/take-action/lambda_function.py'],capture_output=True,text=True).stdout
def body(src,name):
    m=re.search(r'\ndef '+name+r'\(.*?(?=\ndef )',src,re.S)
    return m.group(0) if m else None
for fn in ('call_claude','get_verified_representative_emails','already_sent'):
    print(fn,'UNCHANGED vs HEAD' if body(old,fn)==body(new,fn) else 'CHANGED <-- INSPECT')
PY
- AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c "import sys;sys.path.insert(0,r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action');import lambda_function as lf;print([n for n in dir(lf) if 'source' in n.lower() or 'normal' in n.lower()])"

CONTEXT BUDGET: sized to use no more than ~30% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
