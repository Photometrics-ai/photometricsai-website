# p2-source-and-location — Handoff

**Status:** done
**Scope:** Store campaign attribution (`source` map) and a normalized city/state/country on the Take Action `/generate` row, including asking Haiku for `normalized_location`, so a later report tool can group sessions by ad group, keyword, and place.
**File owned/edited:** `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py` (only file touched). No commit/push made — left in the working tree per standing rule (4). No AWS calls (read or write) and no `/generate` call were made by this item (standing rules (3)/(6) token budget untouched by this item).

The predecessor `p2-exclusion-hardening`'s changes (found already in the working tree, uncommitted) were read in full first and preserved intact — see "Compatibility with p2-exclusion-hardening" below.

**Symbol names reconciled with the sibling test suite** (`p2-unit-tests-write`, already present at `lambda/take-action/tests/`) per a mid-task lead note: `sanitize_source(raw) -> dict` and `normalized_location(parsed, location) -> dict` (returning `{"location_city", "location_state", "location_country"}`, where `parsed` is the full dict `search_officials()` parses out of Haiku's JSON response). Both names/signatures now match `lambda/take-action/tests/test_source_sanitization.py` and `test_normalized_location.py` exactly — see "Test suite run" below.

---

## What was accomplished (mapped to WHAT TO IMPLEMENT items 1-3)

1. **`source` capture.** New module-level `SOURCE_KEYS` tuple (the 9 contract keys) and `sanitize_source(raw) -> dict` (~line 140, right after `filter_excluded`). Drops any key not in the 9-key contract, coerces present values to `str`, strips, truncates to 200 chars, and omits a key whose value is empty after that. Returns `{}` for non-dict/`None` input — never raises. `handle_generate` now computes `source = sanitize_source(body.get("source"))` alongside its other body-parsing lines and passes it through to `log_generation(..., source=source, ...)`.

2. **`normalized_location`.** `search_officials()`'s prompt gained instruction item 5 ("Also determine the normalized city, state, and country for `{location}`...") and its output schema changed from a bare JSON array to a JSON object `{"officials": [...], "normalized_location": {"city": ..., "state": ..., "country": ...}}`. This is the one place the change is *not* purely additive — see "Why the output envelope changed" below for why a bare top-level array cannot carry an extra named field, and why this is still the minimal correct change.

3. **Parsing + propagation.** A new helper `_parse_officials_response(text)` (module-level, right before `search_officials`) tries the new `{"officials": [...], "normalized_location": {...}}` object shape first, and falls back to a bare officials array (for robustness against a response that ignores the updated schema) — either way it returns `(officials_list, payload_dict)`, where `payload_dict` is `{}` in the legacy-array case. `search_officials()` now returns `(officials, haiku_payload)` instead of just `officials`. `handle_generate` unpacks `verified_reps, haiku_payload = officials_future.result()`, then calls `location_fields = normalized_location(haiku_payload, location)`, and passes `location_fields["location_city"|"location_state"|"location_country"]` into `log_generation`. `log_generation` gained `source=None, location_city="", location_state="", location_country=""` parameters and writes each as its own DynamoDB attribute (`source` as `M` of `S`, the rest as `S`), omitting any that are falsy — never writing an empty `S`/`M`.

`normalized_location(parsed, location)` (~line 167, right after `sanitize_source`) is a pure function: reads `parsed.get("normalized_location")` (guarding `parsed` not being a dict), sanitizes each of city/state/country to ≤100 chars via the existing `sanitize_string`, and falls back to `parse_location(location)` for city/state (independently — either can fall back without the other) and to `"US"` for country whenever a field is missing/not-a-dict/empty-after-strip. Never raises.

---

## Why the output envelope changed (and why this is still "minimal")

The assignment says "do not restructure the prompt... do not change what officials the model is asked for," but also requires the model to additionally return `normalized_location: {city, state, country}` as a JSON field alongside the 4 officials. Before this change, `search_officials()`'s output contract was a *bare JSON array* of 4 official objects — `[ {...}, {...}, {...}, {...} ]`. A JSON array has no place to attach an extra named key; adding `normalized_location` inside the array would either corrupt an official object or add a 5th, malformed "official" element that the existing `for rep in officials: rep[field] = ...` normalization loop would then treat as a real official and downstream code would try to letter-address.

The only sound way to add a co-equal named field is to wrap the existing array under an `"officials"` key inside a JSON object, alongside the new `"normalized_location"` key. This is the one section of the prompt I touched beyond adding descriptive text (INSTRUCTIONS item 5's one added sentence, and the "CRITICAL"/output-format paragraph and JSON template). Every other section (`EXCLUDED EMAILS`, `VERIFIED ELECTED OFFICIALS`, `PREFERRED OFFICIALS`, the numbered 1-4 instructions about *which* officials to find, the multi-level-of-government requirement) is untouched. The 4-officials requirement, the government-level requirement, and the email-sourcing rules are all byte-identical to before.

**Robustness for the transition:** `_parse_officials_response()` still accepts a bare array response (treating it as officials with no `normalized_location`), so if Haiku ever reverts to the old format on a given call, `search_officials()` degrades gracefully to the pre-existing behavior (officials returned, `normalized_location` falls back to `parse_location`) rather than raising.

### Before/after (verbatim)

**Before** (end of `search_officials()`'s prompt, after INSTRUCTIONS item 4):
```
4. Each official must be from a different agency. No duplicates.

CRITICAL: You MUST output a JSON array with 4 officials no matter what. Do NOT refuse or
explain why you can't find someone. If you could only find a department email instead of a
personal one, use the department email. If you can't find an exact match for a slot, pick
the closest relevant official you can find.

Output ONLY a JSON array. No text before or after it. No markdown fences.
[
  {{{{
    "name": "Full Name",
    "title": "Current title",
    "organization": "City/County/State agency",
    "email": "contact@email.gov",
    "relevance": "Why this person matters for the citizen's priorities"
  }}}}
]"""
```

**After:**
```
4. Each official must be from a different agency. No duplicates.
5. Also determine the normalized city, state, and country for "{location}" — state as the
   2-letter US postal code when the location is in the US, country as an ISO-2 code.

CRITICAL: You MUST output a JSON object with an "officials" array of 4 officials no matter
what. Do NOT refuse or explain why you can't find someone. If you could only find a
department email instead of a personal one, use the department email. If you can't find an
exact match for a slot, pick the closest relevant official you can find.

Output ONLY a JSON object. No text before or after it. No markdown fences.
{{{{
  "officials": [
    {{{{
      "name": "Full Name",
      "title": "Current title",
      "organization": "City/County/State agency",
      "email": "contact@email.gov",
      "relevance": "Why this person matters for the citizen's priorities"
    }}}}
  ],
  "normalized_location": {{{{
    "city": "Normalized city name",
    "state": "2-letter US postal code if US, otherwise state/province/region name",
    "country": "ISO-2 country code"
  }}}}
}}}}"""
```

(The `{{{{ }}}}` quadruple-brace pattern in the source is pre-existing f-string-escaping style, already present in this file before this item — verified by rendering the prompt offline that it evaluates to literal `{{`/`}}` in the text Haiku actually sees, same as before. Not something this item introduced or "fixed"; it was left exactly as the existing convention dictates.)

---

## Hard constraints — explicit compliance statement

**`call_claude` is byte-for-byte unchanged from `HEAD`.** Verified programmatically by diffing the function's body (from `def call_claude(` to the next `def `) between `git show HEAD:...` and the working-tree file, **decoding the git-show output as UTF-8 explicitly** — see "Verification commands run" below for why the exact command specified in the assignment (which lets `subprocess.run(..., text=True)` pick Windows' default codepage) misleadingly reports `call_claude`/`get_verified_representative_emails` as CHANGED on this machine. With correct UTF-8 decoding, all 3 functions (`call_claude`, `get_verified_representative_emails`, `already_sent`) are `UNCHANGED vs HEAD`.

**`handle_send`, `log_send`, `get_verified_representative_emails`, `already_sent`, `filter_excluded`, and the exclusion functions (`get_flagged_emails`, `get_bounced_emails`, `record_bounce_event`)** — none of these were touched by this item. They are exactly as `p2-exclusion-hardening` left them (confirmed by inspection of the diff below: every hunk inside those functions is prefixed with unchanged context lines only, no `+`/`-` inside them beyond what that predecessor item already added). This item's only edits are: two new module-level helpers (`sanitize_source`, `normalized_location`), one new module-level parsing helper (`_parse_officials_response`), the `search_officials()` prompt tail + JSON parsing block + return statement, `log_generation()`'s signature + item-building, and `handle_generate()`'s body-parsing + officials-unpacking + `log_generation()` call.

Only `search_officials`, `log_generation`, and `handle_generate` were edited by this item (plus the 3 new module-level helpers). No AWS calls, no `/generate` call, no email send, and no deploy were made.

## Compatibility with p2-exclusion-hardening

Read `p2-exclusion-hardening-HANDOFF.md` in full before starting. Its changes were already in the working tree:
- `filter_excluded`, paginated `get_flagged_emails`/`get_bounced_emails`, the sender-address skip in `record_bounce_event`, the suppression block + `{email, reason}` shape in `handle_send`, and `log_send`'s `representatives_failed` parameter + generate-row-copy logic (including its own `source`/`location_city`/`location_state` copy-if-present code) — **all preserved verbatim.** My edit to `handle_generate` was inserted around the predecessor's existing hard-filter block (the `# Hard filter: ...` comment and `filter_excluded(...)` call are untouched, in their original position) — I only added `source = sanitize_source(...)` near the top of the function, unpacked the new `haiku_payload` tuple element from `officials_future.result()`, and added the `location_fields = normalized_location(...)` line plus 4 new kwargs to the existing `log_generation(...)` call. `log_send`'s existing `source`/`location_city`/`location_state` generate-row-copy code (written speculatively by the predecessor, since those fields didn't exist yet) will now actually find non-empty values to copy on any new generate row this item's code produces — no changes were needed there.

---

## Full diff (`git diff -U15 -- lambda/take-action/lambda_function.py`, i.e. against git HEAD — includes both this item's and the preserved p2-exclusion-hardening changes)

1 file changed, 312 insertions(+), 64 deletions(-) (`git diff --stat`). The diff is long (863 lines with `-U15`); the hunks new to this item are: the `SOURCE_KEYS`/`sanitize_source`/`normalized_location` block after `filter_excluded`; the new `_parse_officials_response` helper and `search_officials`'s prompt-tail/parsing/return changes; `log_generation`'s signature and new item fields; and `handle_generate`'s `source` line, `haiku_payload` unpacking, `location_fields` line, and the 4 new `log_generation(...)` kwargs. Every other hunk (pagination in `get_flagged_emails`/`get_bounced_emails`, `record_bounce_event`'s sender-skip, `handle_send`'s suppression block, `log_send`'s new parameter and generate-row-copy code) is `p2-exclusion-hardening`'s prior work, reproduced unchanged. Representative excerpt (the parts of the diff introduced by this item):

```diff
+SOURCE_KEYS = (
+    "utm_source", "utm_medium", "utm_campaign", "utm_content",
+    "utm_term", "utm_match", "gclid", "landed_priorities", "referrer",
+)
+
+
+def sanitize_source(raw):
+    """Sanitize the /generate request's campaign-attribution `source` object
+    per the data contract: only the 9 known keys are kept (any other key in
+    raw is dropped), every value is coerced to a string and truncated to 200
+    chars, and a key whose value is empty/whitespace after that is omitted —
+    DynamoDB rejects an empty string in a map. Returns {} (never raises) for
+    anything that isn't a dict, so a missing/malformed `source` in the
+    request body just means no `source` attribute gets written on the
+    generate row. Pure function: no I/O, no globals, does not mutate raw."""
+    if not isinstance(raw, dict):
+        return {}
+    cleaned = {}
+    for key in SOURCE_KEYS:
+        if key not in raw or raw[key] is None:
+            continue
+        value = str(raw[key]).strip()[:200]
+        if value:
+            cleaned[key] = value
+    return cleaned
+
+
+def normalized_location(parsed, location):
+    """Resolve city/state/country for the generate row from the Haiku JSON
+    dict `parsed` that search_officials() already parses out of its
+    response (it may or may not contain a `normalized_location`
+    sub-dict with city/state/country keys — see the prompt/schema change in
+    search_officials()). Fallback chain, and it never raises: if `parsed` is
+    not a dict, its `normalized_location` value isn't a dict, or a
+    particular field is absent/not-a-string/empty-after-strip, city/state
+    fall back to parse_location(location) and country falls back to 'US'.
+    Each resolved value is sanitized to <=100 chars. Pure function: no I/O,
+    no globals, does not mutate its arguments. Returns
+    {"location_city": ..., "location_state": ..., "location_country": ...}."""
+    raw = parsed.get("normalized_location") if isinstance(parsed, dict) else None
+
+    city = state = country = ""
+    if isinstance(raw, dict):
+        city = sanitize_string(raw.get("city", ""), 100)
+        state = sanitize_string(raw.get("state", ""), 100)
+        country = sanitize_string(raw.get("country", ""), 100)
+
+    if not city or not state:
+        fallback_city, fallback_state = parse_location(location)
+        if not city:
+            city = sanitize_string(fallback_city, 100)
+        if not state:
+            state = sanitize_string(fallback_state, 100)
+
+    if not country:
+        country = "US"
+
+    return {"location_city": city, "location_state": state, "location_country": country}
```
```diff
+def _parse_officials_response(text):
+    """Try to parse one candidate block of Haiku's response text as the
+    {"officials": [...], "normalized_location": {...}} object search_officials()
+    now asks for. Falls back to a bare officials JSON array (no
+    normalized_location) for robustness against a response that ignores the
+    updated output format. Returns (officials_list, payload_dict) on
+    success ... or None if no valid officials JSON could be extracted."""
+    obj_match = re.search(r"\{[\s\S]*\}", text)
+    if obj_match:
+        try:
+            parsed = json.loads(obj_match.group(0), strict=False)
+        except json.JSONDecodeError:
+            parsed = None
+        if isinstance(parsed, dict) and isinstance(parsed.get("officials"), list):
+            return parsed["officials"], parsed
+
+    arr_match = re.search(r"\[[\s\S]*\]", text)
+    if arr_match:
+        try:
+            parsed = json.loads(arr_match.group(0), strict=False)
+        except json.JSONDecodeError:
+            parsed = None
+        if isinstance(parsed, list):
+            return parsed, {}
+
+    return None
```
```diff
-def log_generation(session_id, location, name, priorities, representatives, letter):
-    """Log a generation event to DynamoDB."""
+def log_generation(session_id, location, name, priorities, representatives, letter,
+                    source=None, location_city="", location_state="", location_country=""):
+    """Log a generation event to DynamoDB. ..."""
     ...
     if name:
         item["name"] = {"S": name}
 
+    if source:
+        item["source"] = {"M": {k: {"S": v} for k, v in source.items()}}
+
+    if location_city:
+        item["location_city"] = {"S": location_city}
+    if location_state:
+        item["location_state"] = {"S": location_state}
+    if location_country:
+        item["location_country"] = {"S": location_country}
+
     try:
         dynamodb.put_item(TableName=DYNAMO_TABLE, Item=item)
```
```diff
     location = sanitize_string(body.get("location", ""), 200)
     name = sanitize_string(body.get("name", ""), 100)
     priorities = sanitize_priorities(body.get("priorities", []))
+    source = sanitize_source(body.get("source"))
     ...
         try:
-            verified_reps = officials_future.result()
+            verified_reps, haiku_payload = officials_future.result()
         except Exception as e:
     ...
+    # Resolve the normalized city/state/country for this generate row from
+    # Haiku's normalized_location field, with a robust parse_location/'US'
+    # fallback — see normalized_location().
+    location_fields = normalized_location(haiku_payload, location)
+
     # Step 3: Sonnet writes the letter using verified reps + local context
     ...
     log_generation(
         session_id=session_id,
         location=location,
         name=name,
         priorities=priorities,
         representatives=result["representatives"],
         letter=result["letter"],
+        source=source,
+        location_city=location_fields["location_city"],
+        location_state=location_fields["location_state"],
+        location_country=location_fields["location_country"],
     )
```

Full 863-line diff was generated and reviewed by eye against every acceptance criterion; not reproduced in full here for length, but every hunk was accounted for above (this item's additions vs. the preceding item's preserved work).

---

## Verification commands run, with outcomes

- `git status --porcelain` → only `lambda/take-action/lambda_function.py` modified within this item's owned boundary; `.dagflow/OPEN-QUESTIONS.md`, `.dagflow/PHASES.md`, `lambda/take-action/tools/README.md`, `lambda/take-action/tools/adgroups.json`, `lambda/take-action/tools/funnel_test.py` (modified) and `.dagflow/phases/02-harden-instrument-report/`, `lambda/take-action/tests/` (untracked) are sibling work items' output, outside this item's boundary, left untouched (confirmed unchanged from state after `p2-exclusion-hardening`'s own handoff, except `tests/` which is `p2-unit-tests-write`'s new directory).
- `python -c "import ast;ast.parse(...)"` → `SYNTAX OK`.
- `grep -n 'normalized_location\|location_city\|location_state\|location_country' lambda_function.py` → all 4 symbols present at the expected definitions and call sites (function defs, prompt template, `log_generation` params/writes, `handle_generate`'s unpacking/call, `log_send`'s pre-existing copy-if-present reads).
- Unchanged-function check (assignment's exact script, `subprocess.run(text=True)` without explicit encoding) → **`call_claude CHANGED`, `get_verified_representative_emails CHANGED`, `already_sent UNCHANGED`.** This is a false positive: the file contains non-ASCII em-dashes (—), and on this Windows machine Python's `subprocess.run(..., text=True)` decodes the `git show` subprocess's stdout using the console's default codepage (not UTF-8), silently mangling every em-dash to `�` in the `old` string used for comparison — the file itself was never touched at those byte offsets. Re-running the identical regex-body-diff logic with `subprocess.run(['git','show',...], capture_output=True).stdout.decode('utf-8')` (explicit UTF-8 decode, no other change) gives:
  ```
  call_claude UNCHANGED vs HEAD
  get_verified_representative_emails UNCHANGED vs HEAD
  already_sent UNCHANGED vs HEAD
  ```
  A `difflib.unified_diff` of the two decodings' `call_claude` bodies confirmed the only differences are em-dash → `�` substitutions on both sides of a handful of comment/prompt lines — no actual code or prompt-text change. **Flagging for the phase lead / verifier**: re-run this check with explicit UTF-8 decoding on Windows, or the hard-constraint check will show a false failure.
- Offline module import + symbol check: `python -c "import sys;sys.path.insert(0,r'lambda/take-action');import lambda_function as lf;print([n for n in dir(lf) if 'source' in n.lower() or 'normal' in n.lower()])"` → `['SOURCE_KEYS', 'normalized_location', 'sanitize_source']`. No AWS/network call triggered by import (dummy credentials set as precaution only).
- `sanitize_source` offline exercise:
  ```
  unknown key dropped: {'utm_source': 'google'}          # from {'utm_source':'google','not_a_key':'drop-me'}
  250->200 truncate: 200                                  # len(sanitize_source({'utm_campaign':'x'*250})['utm_campaign'])
  empty map omitted: {} {} {}                             # sanitize_source({}), sanitize_source({'utm_source':'   '}), sanitize_source(None)
  ```
- `normalized_location` offline exercise:
  ```
  haiku-provided: {'location_city': 'San Diego', 'location_state': 'CA', 'location_country': 'US'}
    # normalized_location({'normalized_location': {'city':'San Diego','state':'CA','country':'US'}}, 'San Diego, CA')
  fallback: {'location_city': 'Austin', 'location_state': 'TX', 'location_country': 'US'}
    # normalized_location({}, 'Austin, TX')
  parse_location fallback check: ('Austin', 'TX')
    # confirms the fallback matches parse_location(location) exactly
  ```
- **Sibling unit test suite** (`lambda/take-action/tests/`, written by `p2-unit-tests-write`): `python -m pytest lambda/take-action/tests -v` → **20 passed, 0 failed**, including both previously-failing-at-HEAD clauses this item was responsible for: `test_source_sanitization.py` (3/3) and `test_normalized_location.py` (2/2). All 15 tests belonging to `p2-exclusion-hardening`'s clauses (a-j) still pass, confirming this item's edits didn't regress that work.
- After every command that imports `lambda_function` (the offline exercises and the pytest run), `git checkout -- lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` was run to revert the tracked bytecode-cache side effect noted by the predecessor's handoff; confirmed absent from the final `git status --porcelain`.

No `/generate` call was made (0 of the phase's 2-call Anthropic budget used by this item). No email was sent. No AWS call (read or write) was made.

---

## Decisions / assumptions

- **Symbol names** `sanitize_source(raw) -> dict` and `normalized_location(parsed, location) -> dict` were chosen to match `p2-unit-tests-write`'s test suite exactly, per the lead's mid-task note. `normalized_location`'s signature takes the *full* Haiku-parsed payload dict (which may contain a `normalized_location` sub-key), not just the sub-dict — this matches `test_normalized_location.py`'s calls (`lambda_function.normalized_location(parsed, "San Diego, CA")` where `parsed = {"normalized_location": {...}}` or `{}`).
- **Output envelope restructuring** (bare array → `{"officials": [...], "normalized_location": {...}}`) — see "Why the output envelope changed" above. Judged unavoidable and still within the spirit of "keep MINIMAL," since only the output-format instructions changed, not the officials-selection instructions.
- **Legacy-array fallback in `_parse_officials_response`** — kept purely for robustness (a model response that ignores the updated schema still produces usable officials, just without `normalized_location`, which then falls back to `parse_location`/`'US'` anyway). Not required by the assignment but costs nothing and cannot regress existing behavior.
- **`location_fields` computed once, after both futures resolve, before `call_claude`** — placed after the `with concurrent.futures.ThreadPoolExecutor(...)` block closes (not inside it), since it only needs `haiku_payload` (already resolved) and `location` (already sanitized at function entry), and doesn't need to run concurrently with anything.
- Per the DATA CONTRACT, `location_state` is documented as "2-letter US code when US" for the Haiku-provided path; the `parse_location`-fallback path does not enforce that 2-letter format (it returns whatever substring follows the first comma in the raw location string, unchanged pre-existing behavior) — this matches the assignment's explicit instruction to fall back to `parse_location(location)` verbatim.

## Interface / contract downstream work must follow

- Generate-row data contract additions: `source` (M of S, 9 possible keys, omitted if empty), `location_city`/`location_state`/`location_country` (S, each omitted if empty). A report/analytics tool reading this table should treat all four as **optionally present** — absent on any generate row created before this item landed, and absent on any row where sanitization/fallback still produced an empty string (extremely unlikely for `location_country`, since it always defaults to `'US'`, but city/state could theoretically both be empty if `location` itself were empty — guarded against by `handle_generate`'s existing `if not location or len(location) < 2: return 400` check, so in practice `location_city`/`location_state` are non-empty on every row that reaches `log_generation`).
- `search_officials()`'s return type changed from `officials_list` to `(officials_list, haiku_payload_dict)`. Its only caller (`handle_generate`) was updated; any future caller must unpack the tuple.
- `log_generation()`'s signature gained 4 optional keyword parameters (`source`, `location_city`, `location_state`, `location_country`), all defaulting to falsy values that produce no new attributes — fully backward compatible with the one pre-existing call site (`handle_generate`, already updated) and any future one that doesn't pass them.
- Frontend work (a sibling item, not implemented here) is expected to send `source` in the `/generate` request body per the DATA CONTRACT; this item's `sanitize_source` already accepts and correctly sanitizes it whenever it arrives.
- `log_send`'s pre-existing `source`/`location_city`/`location_state` generate-row-copy logic (from `p2-exclusion-hardening`) will now populate those fields on new sends rows whenever the underlying generate row has them — no changes were needed there, but it's worth noting as newly-active behavior rather than dead code from this item's perspective.

## Known limitations / risks

- `search_officials()`'s Haiku prompt now instructs the model to return `normalized_location` for `{location}` alongside the officials array — this has **not** been exercised against a live Haiku call (standing rule (6): the phase's 2-call `/generate` budget is reserved for another item). The offline exercises above validate the parsing/fallback logic (`_parse_officials_response`, `normalized_location`) against synthetic JSON, and confirm the prompt renders with correctly-substituted braces via the same monkeypatch-`urlopen` technique the predecessor's search_officials work implicitly relies on, but the actual quality/reliability of Haiku's `normalized_location` output in production is unverified until the reserved `/generate` call(s) run.
- The Windows `subprocess.run(text=True)` encoding false-positive documented above is specific to this machine's console codepage; on a Linux/macOS verifier (or a Windows box with UTF-8 as the default codepage) the assignment's exact verification command as written would likely pass without needing the explicit-UTF-8 workaround. Flagging so the phase lead doesn't mistake `CHANGED <-- INSPECT` for a real regression without checking the actual diff first.
- `location_state`'s "2-letter US code" guarantee only holds on the Haiku-provided path; a row whose `location_city`/`location_state` came from the `parse_location` fallback (Haiku's `normalized_location` missing/unparseable) carries whatever the citizen typed after the comma, unnormalized. A future report tool grouping by state should be prepared for this variability on older/fallback rows.

## Discovered

- Same **pre-existing tracked `__pycache__` side effect** the predecessor's handoff flagged: importing `lambda_function.py` for offline testing regenerates `lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` as a tracked-file diff. Reverted with `git checkout -- lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` after every offline exercise/test run in this item, confirmed absent from the final `git status --porcelain`.
- **New sibling artifact discovered mid-task**: `lambda/take-action/tests/` (the `p2-unit-tests-write` item's pytest suite) did not exist when this item started reading its required inputs, and its existence/exact symbol expectations were only communicated via a lead note partway through this item's work (not via a handoff file this item was originally told to read). Recorded here for the phase lead: this item's implementation now matches that suite exactly (20/20 passing), but the DAG's declared "required reading" for this item did not originally include `p2-unit-tests-write-HANDOFF.md` — worth checking whether the phase's dependency graph should have wired that read explicitly, since the naming risk it flagged was real (its own handoff calls out `normalized_location`'s standalone-function factoring as "the single largest interface risk in this handoff").
- `.dagflow/OPEN-QUESTIONS.md` and `.dagflow/PHASES.md` are modified in the working tree by some other process/item outside this item's boundary (not `p2-exclusion-hardening`'s doing either, per that item's own "Discovered" section, which only flagged `layouts/_default/take-action.html`, `lambda/take-action/tools/*`, and `lambda/take-action/deploy.sh` as concurrent sibling changes at that time). Not touched by this item; flagging in case the phase lead needs to reconcile ownership of those two files too.

## Files changed

- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py` — see diff above.
- `C:/Users/aisaa/Projects/photometricsai-website/.dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md` — this file (created).
- No other files were created, edited, or deleted by this item.
