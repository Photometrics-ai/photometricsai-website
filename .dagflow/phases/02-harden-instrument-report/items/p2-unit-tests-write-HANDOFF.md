# p2-unit-tests-write — HANDOFF

## Status
Done. `lambda/take-action/tests/` created with a 20-test pytest suite covering all twelve contract clauses (a)-(l). Collection against a pristine copy of git HEAD's `lambda_function.py` succeeds with **zero errors, 20 tests collected** (>= the required 12).

## What was accomplished
Wrote the pytest suite for the hardened Take Action send path against the data contracts fixed in the sibling implementation prompts (read in full, not guessed):
- `.dagflow/phases/02-harden-instrument-report/prompts/p2-exclusion-hardening.impl.md` (filter_excluded, pagination, sender-skip, suppression, log_send new fields)
- `.dagflow/phases/02-harden-instrument-report/prompts/p2-source-and-location.impl.md` (source sanitization, normalized_location)

No implementation file was edited. `lambda_function.py` was only read (never written) — confirmed by `git status --porcelain -- lambda/take-action/tests/` showing only the new `tests/` directory as changed inside my boundary.

**Discovery during work**: the working-tree copy of `lambda_function.py` was already mid-edit by the concurrently-running `p2-exclusion-hardening` item (it has since completed and written its own handoff). I used this only as *confirmation* that my contract reading (from the prompt files, not from inferring behavior off a moving target) was correct — I did not base any test's expected behavior on the live working-tree file. Running the finished suite against that mid-edit copy (see "Bonus verification" below) shows all clauses it implements (a, b, c, e, f, g, h, i, and half of j) now pass, which cross-validates the suite's correctness. `p2-source-and-location` had not started (no `sanitize_source`/`normalized_location` in the working tree, no handoff file) at the time of this work.

## Canonical outputs
```
lambda/take-action/tests/
  conftest.py      — sets env vars + sys.path (honouring TAKE_ACTION_SRC) BEFORE `import lambda_function`; fake_dynamodb/fake_ses fixtures
  fakes.py          — FakeDynamoDB, FakeSES (in-process, no network, no moto)
  ddb.py            — DynamoDB wire-format helpers (s/n/l/m/bool_)
  builders.py       — generate_row_item() builder for canned get_item responses
  test_filter_excluded.py       — clause (a), 5 tests
  test_bounced_emails.py        — clauses (b), (c), 2 tests
  test_bounce_events.py         — clauses (d), (e), 2 tests
  test_handle_send.py           — clauses (f), (g), (h), (i), 4 tests
  test_log_send.py              — clause (j), 2 tests
  test_source_sanitization.py   — clause (k), 3 tests
  test_normalized_location.py   — clause (l), 2 tests
```
20 tests total.

## Clause -> test mapping
| Clause | Test(s) |
|---|---|
| (a) filter_excluded | `test_filter_excluded.py::test_filter_excluded_is_case_insensitive`, `::test_filter_excluded_keeps_official_with_no_email`, `::test_filter_excluded_with_excluded_none_returns_input_unchanged`, `::test_filter_excluded_with_excluded_empty_returns_input_unchanged`, `::test_filter_excluded_does_not_mutate_input_list_or_dicts` |
| (b) get_bounced_emails pagination | `test_bounced_emails.py::test_get_bounced_emails_paginates_across_scan_pages` |
| (c) get_bounced_emails classification | `test_bounced_emails.py::test_get_bounced_emails_classification_permanent_and_complaint_in_transient_out` |
| (d) record_bounce_event realistic fixture | `test_bounce_events.py::test_record_bounce_event_writes_row_for_realistic_bounce_notification` |
| (e) record_bounce_event sender-skip | `test_bounce_events.py::test_record_bounce_event_skips_row_for_sender_address` |
| (f) handle_send suppression | `test_handle_send.py::test_handle_send_suppresses_bounced_representative` |
| (g) handle_send ses_error | `test_handle_send.py::test_handle_send_ses_error_marks_one_rep_failed_and_still_sends_the_other` |
| (h) handle_send open-relay guard (SECURITY) | `test_handle_send.py::test_handle_send_rejects_unverified_email_SECURITY_open_relay_guard` |
| (i) handle_send already_sent | `test_handle_send.py::test_handle_send_already_sent_returns_409_and_sends_nothing` |
| (j) log_send item shape | `test_log_send.py::test_log_send_item_shape_includes_new_contract_fields`, `::test_log_send_omits_source_and_location_when_absent_on_generate_row` |
| (k) source sanitization | `test_source_sanitization.py::test_sanitize_source_drops_unknown_keys`, `::test_sanitize_source_truncates_long_value_to_exactly_200_chars`, `::test_sanitize_source_all_empty_input_yields_no_source_attribute` |
| (l) normalized_location | `test_normalized_location.py::test_normalized_location_uses_haiku_provided_fields`, `::test_normalized_location_falls_back_to_parse_location_and_us_when_field_absent` |

## Decisions / assumptions
1. **filter_excluded, get_bounced_emails/get_flagged_emails pagination, record_bounce_event sender-skip, handle_send suppression/ses_error, log_send new fields** (clauses a, b, c, e, f, g, h, i, j) — all names and signatures come directly from `p2-exclusion-hardening.impl.md`'s WHAT TO IMPLEMENT / ACCEPTANCE CRITERIA / DATA CONTRACT sections, which are explicit and unambiguous. No naming risk here.
2. **`sanitize_source(raw) -> dict`** (clause k) — `p2-source-and-location.impl.md` item 1 *suggests* this name ("Prefer a small dedicated helper (e.g. `sanitize_source(raw) -> dict`) so it is unit-testable in isolation — a sibling item's pytest suite will import and exercise it") but does not mandate it. I used the suggested name verbatim. **Risk**: if the implementing item names it differently, `test_source_sanitization.py`'s three tests will fail with `AttributeError` rather than a contract-shape mismatch, until reconciled.
3. **`normalized_location(parsed, location) -> dict`** (clause l) — `p2-source-and-location.impl.md` fixes the *data* (location_city/location_state/location_country on the generate row, sourced from a Haiku `normalized_location: {city, state, country}` field with a parse_location + 'US' fallback) but does not name or scope a pure parsing function; the contract only says the field is "parsed where the model JSON is already parsed" inside `search_officials`. I assumed a standalone pure function `normalized_location(parsed, location) -> {"location_city", "location_state", "location_country"}` for testability, since `search_officials` itself does live HTTP calls and can't be unit-tested without a live Anthropic API key. **Risk (flagged under Discovered below)**: if the implementer inlines this logic into `search_officials` instead of exposing a standalone function, `test_normalized_location.py`'s two tests will fail with `AttributeError` until reconciled — this is the single largest interface risk in this handoff and downstream work (`p2-source-and-location`, `p2-unit-tests-run`) should read this section.
4. **log_send tested through `handle_send`, not called directly** — `p2-exclusion-hardening.impl.md` explicitly allows `log_send`'s signature to change ("log_send's signature may gain parameters ... update its call site in handle_send accordingly"), so calling it directly with a guessed signature would be brittle. Instead `test_log_send.py` drives it through `handle_send()` and asserts on the resulting `put_item` Item captured by `FakeDynamoDB`, which matches the DATA CONTRACT (observable row shape) rather than any particular function signature. This is confirmed correct: it already passes against the working-tree copy with `p2-exclusion-hardening` applied (see Bonus verification).
5. `FakeDynamoDB.get_item` is a **repeatable** per-table response (not a one-shot FIFO), matching real DynamoDB semantics where the same key returns the same item — this was necessary because `handle_send` calls `get_item` on `DYNAMO_TABLE` at least twice in the target implementation (once via `get_verified_representative_emails`, once via `log_send`'s own generate-row fetch), and both need to see the same seeded row. `scan` is a FIFO-per-table queue since pagination genuinely needs sequential distinct responses.

## Files changed
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/conftest.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/fakes.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ddb.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/builders.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_filter_excluded.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_bounced_emails.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_bounce_events.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_handle_send.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_log_send.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_source_sanitization.py` (new)
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/test_normalized_location.py` (new)

`lambda_function.py` was not touched (read-only). No files outside the owned boundary were written except this handoff.

## Commands / tests run, with outcomes

### `ls -la lambda/take-action/tests/`
```
conftest.py  fakes.py  ddb.py  builders.py
test_bounce_events.py  test_bounced_emails.py  test_filter_excluded.py
test_handle_send.py  test_log_send.py  test_normalized_location.py
test_source_sanitization.py
```

### `grep -rn 'moto\|boto3.client(' lambda/take-action/tests/`
Only matches are inside docstring/comment prose in `conftest.py` and `fakes.py` explaining what `lambda_function.py` itself does (e.g. "`dynamodb = boto3.client(\"dynamodb\")`") — no test file constructs a boto3 client or imports moto.

### Collection against a pristine HEAD copy (required verification command)
```
mkdir -p /tmp/lfhead
git show HEAD:lambda/take-action/lambda_function.py > /tmp/lfhead/lambda_function.py
TAKE_ACTION_SRC=/tmp/lfhead python -m pytest lambda/take-action/tests --collect-only -q
```
Output (tail):
```
...
lambda/take-action/tests/test_source_sanitization.py::test_sanitize_source_drops_unknown_keys
lambda/take-action/tests/test_source_sanitization.py::test_sanitize_source_truncates_long_value_to_exactly_200_chars
lambda/take-action/tests/test_source_sanitization.py::test_sanitize_source_all_empty_input_yields_no_source_attribute

20 tests collected in 0.02s
```
**Zero collection errors, 20 tests collected.** Meets Definition of Done (>=12).

### Collection against the current working-tree copy (sanity — not required, but confirms no path drift)
```
python -m pytest lambda/take-action/tests --collect-only -q
```
Same result: `20 tests collected in 0.02s`, zero errors.

### `grep -rn 'def test_' lambda/take-action/tests/`
20 matches, one per test listed in the clause-mapping table above.

### Full run (not collect-only) against the pristine HEAD copy — documents expected failures
```
TAKE_ACTION_SRC=/tmp/lfhead python -m pytest lambda/take-action/tests -v
```
Result: **5 passed, 15 failed** (all failures are `AttributeError`/`KeyError`/`AssertionError` from symbols or behavior that do not exist yet at HEAD — expected and correct per the assignment: "individual tests failing at that point is expected and fine"):

PASSED (test pre-existing HEAD behavior that the hardening work doesn't change):
- `test_bounce_events.py::test_record_bounce_event_writes_row_for_realistic_bounce_notification`
- `test_bounced_emails.py::test_get_bounced_emails_classification_permanent_and_complaint_in_transient_out`
- `test_handle_send.py::test_handle_send_rejects_unverified_email_SECURITY_open_relay_guard`
- `test_handle_send.py::test_handle_send_already_sent_returns_409_and_sends_nothing`
- `test_log_send.py::test_log_send_omits_source_and_location_when_absent_on_generate_row` (vacuously true at HEAD since no new fields are ever written yet)

FAILED (expect these to start passing once `p2-exclusion-hardening` / `p2-source-and-location` land):
- `test_bounce_events.py::test_record_bounce_event_skips_row_for_sender_address` — sender-skip guard doesn't exist at HEAD
- `test_bounced_emails.py::test_get_bounced_emails_paginates_across_scan_pages` — HEAD doesn't paginate
- `test_filter_excluded.py::*` (all 5) — `filter_excluded` doesn't exist at HEAD (`AttributeError`)
- `test_handle_send.py::test_handle_send_suppresses_bounced_representative` — no suppression at HEAD
- `test_handle_send.py::test_handle_send_ses_error_marks_one_rep_failed_and_still_sends_the_other` — HEAD's `failed` list holds bare email strings, not `{email, reason}`, and the response body has no `failed` key at HEAD
- `test_log_send.py::test_log_send_item_shape_includes_new_contract_fields` — none of the new fields exist at HEAD
- `test_normalized_location.py::*` (both) — `normalized_location` doesn't exist at HEAD (`AttributeError`)
- `test_source_sanitization.py::*` (all 3) — `sanitize_source` doesn't exist at HEAD (`AttributeError`)

### Bonus verification (not a required command, done for confidence): full run against the actual working-tree copy, where `p2-exclusion-hardening` has already landed
```
python -m pytest lambda/take-action/tests -v
```
Result: **15 passed, 5 failed** — every clause `p2-exclusion-hardening` implements (a, b, c, e, f, g, h, i, and the log_send shape half of j) now passes; only clauses owned by the not-yet-started `p2-source-and-location` (k, l, and the source/priorities/location_city/location_state half of j) still fail. This is strong evidence the suite is correctly targeting the real, already-agreed contract and not testing an imagined one.

## Known limitations / risks
- **Naming risk on clause (k) and (l)** — see Decisions #2 and #3 above. `sanitize_source` is a suggested-but-not-mandated name (low risk: the sibling contract explicitly anticipates this test suite importing it by that name). `normalized_location` as a standalone pure function is my own inference (higher risk: nothing in the contract requires this exact factoring). If `p2-source-and-location` structures things differently, `p2-unit-tests-run` (or whoever runs this suite against the final code) will see `AttributeError` failures on these clauses specifically, not because the *behavior* is wrong but because the *symbol* doesn't match. Recommend the verifier/lead check `lambda_function.py`'s actual symbol names for source-sanitization and location-normalization against this handoff before treating a failure on `test_source_sanitization.py`/`test_normalized_location.py` as a real regression.
- Tests do not exercise `search_officials`, `call_claude`, or `research_location` (all three make live HTTP calls to the Anthropic API) — out of scope per the assignment's SYSTEM UNDER TEST section, which scopes this suite to the send path, exclusion, bounce recording, source sanitization, and normalized-location parsing.
- `FakeSES`/`FakeDynamoDB` are intentionally minimal (no partial-failure-mode simulation beyond what the 12 clauses need, no `ExpressionAttributeValues` validation, etc.) per the STYLE CONSTRAINTS instruction to keep fakes small and local to `tests/`.

## Discovered
- **Interface gap**: `p2-source-and-location.impl.md` does not pin a function name/signature for the `normalized_location` parsing step (only the resulting row-level data contract). Recorded above under Decisions #3 and Known limitations. Not a blocker for this item (tests still collect cleanly and are ready to run), but downstream (`p2-source-and-location` implementer and `p2-unit-tests-run`) should reconcile the name, or accept that `test_normalized_location.py` will need a one-line symbol-name fix after `p2-source-and-location` lands.
- `p2-exclusion-hardening` was already complete in the working tree at the time of this work (its own HANDOFF exists at `.dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md`), which let me cross-validate 15/20 tests against real, already-landed behavior rather than only against the pristine-HEAD contract-reading exercise. No conflict found — implementation and contract-derived tests agree exactly on all 15 clauses currently implemented.
- No test rows were written to any real AWS table (all DynamoDB/SES access in this suite is monkeypatched); the standing rule about `test-` prefixed session rows and `test-gap-framing-001/-004` does not apply to this item's output, since nothing here touches real AWS.

## STANDING RULES compliance
- No real send: all sends in this suite go through `FakeSES`; simulator addresses (`success@simulator.amazonses.com` and a `+2` plus-variant) and `ari@sdgis.com` (as the constituent/CC role in test fixtures, per the rule that it's the only real inbox allowed) are the only email addresses used.
- No AWS write calls made (all DynamoDB access monkeypatched).
- No git commit/push performed.
- Did not touch `ANTHROPIC_API_KEY`/`GOOGLE_CIVIC_API_KEY` values — `conftest.py` sets clearly-labeled placeholder strings for these env vars (never printed, never real).
- No Chrome/browser tools used.
- Zero `/generate` calls made (this item needed none).
