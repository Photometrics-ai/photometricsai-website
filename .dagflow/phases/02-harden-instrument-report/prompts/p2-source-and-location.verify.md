You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-source-and-location — Store campaign attribution (`source` map) and a normalized city/state/country on the generate row, including asking Haiku for normalized_location, so the report tool can group sessions by ad group, keyword and place.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- handle_generate reads body['source'], accepts only the 9 contract keys (utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer), drops unknown keys, coerces values to str, truncates each to 200 chars, omits keys whose value is empty after sanitization, and omits the whole `source` attribute when the resulting map is empty or the request had no source.
- The generate row written by log_generation carries `source` (M of S) when non-empty, and `location_city` (S), `location_state` (S), `location_country` (S) when non-empty.
- search_officials' Haiku prompt and JSON/tool schema request a `normalized_location` object with keys city, state (2-letter US code when US), country (ISO-2); the response parser reads it if present.
- Fallback is robust: if normalized_location is absent, unparseable, or partially empty, city/state fall back to parse_location(location) and country falls back to 'US'. A missing field never raises and never blocks letter generation.
- call_claude and the letter prompt are unchanged; the officials-search behaviour (which officials are returned, and the hard filter added by p2-exclusion-hardening) is unchanged.
- The file parses (ast.parse) and the working-tree diff touches only lambda_function.py.
- No AWS calls, no /generate call, no deploy.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
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

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
