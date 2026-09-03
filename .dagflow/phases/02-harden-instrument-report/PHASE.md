# Phase 02: Harden, instrument, report

## Objective

Make a bounced or flagged official address impossible to re-suggest or re-send; record what was offered, suppressed and failed on every send; capture campaign attribution and a normalized city/state on every generate row and copy it to the sends row; make deploy repeatable and verified; and ship the report tool that answers which ad group, keyword, priority and city actually produce letters and sends.

## Entry Criteria

- [x] Phase 01 exit criteria met: p1-harness-run verified green, baseline captured (118 non-test generate rows, 4 sends, 14 bounce rows), campaign doc updated.
- [x] AWS CLI authenticated for account 794038225197 in us-east-2 (aws sts get-caller-identity succeeds).
- [x] Deployed Lambda CodeSha256 is vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E= (equal to git HEAD~1's function.zip) — the known-good starting point.
- [x] Sender mailbox take-action@photometrics.ai confirmed working, SES suppression cleared (2026-09-03).
- [x] Ari's authorizations recorded: production Lambda deploys pre-authorized; commits to master authorized (lead only); no agent may change Google Ads, GA4, Workspace, IAM or SES config.
- [x] Toolchain present: Python 3.11.5, pytest 9.0.2, boto3 1.42.70, Hugo v0.154.5 extended, node, openssl, base64, aws CLI v2.18.6. moto absent and `zip` absent — both accounted for in the item briefs.
- [x] Working tree clean apart from .dagflow/ (the lead commits; items leave changes in the tree).

## Exit Criteria

- [ ] pytest suite at lambda/take-action/tests/ is green (>=12 tests, 0 skipped) with no test weakened to pass, verified by an independent re-run.
- [ ] Deployed CodeSha256 equals the locally built artifact hash and differs from the pre-phase value; CloudWatch shows no errors across the deploy and harness windows.
- [ ] funnel_test.py `all` — including the new check-regenerate step — passes against production, with independent aws dynamodb corroboration that a hard-bounced address was refused with reason 'suppressed' and that the sends row carries representatives_failed, representatives_offered, priorities, source and location_city.
- [ ] One real /generate call proved the deployed backend stores source.utm_content and location_city 'Columbus' / location_state 'OH' / location_country 'US'; its row was deleted and absence proven.
- [ ] Zero residue: no test- rows remain beyond the two pre-existing test-gap-framing rows; table counts reconcile to the Phase 01 baseline.
- [ ] layouts/_default/take-action.html implements the frontend source capture and the three new GA4 params, hugo builds clean, and the ?priorities= preselect behaviour is provably unchanged (lead pushes and verifies live, outside this DAG).
- [ ] report.py runs clean against production, and its totals reconcile with the Phase 01 baseline (118 generated / 4 sends) with any deviation explained by session_id.
- [ ] CLAUDE.md has a 'Take Action Lambda' section with the full data contract and no secret values; the campaign doc's Funnel verification section reflects current state in its existing readable-cold voice.
- [ ] The open-relay guard (get_verified_representative_emails) and already_sent are provably unchanged from git HEAD, confirmed by an opus verifier on the security-critical items.

## Phase Gate

Status: open — entry criteria verified by the lead 2026-09-03 (Phase 01 closed; sender mailbox confirmed by Ari; deploys pre-authorized).

## Concurrency Limits

- `max_total`: 8
- `max_write`: 3

## Notes

Merges plan-of-record Phases 2, 3, 4 into one DAG per Ari's instruction not to stop at phase boundaries. Planner run wf_afcc15bc-31c (opus/high). Deviation notes:
- STRUCTURAL (not tiering): the task guidance suggested merging work items A and B into a single lambda_function.py item. I kept them separate (p2-exclusion-hardening -> p2-source-and-location). They serialize on `owns` either way, so the only cost is one extra dispatch on the critical path, and the benefit is real: A's failure mode is an authorization gap in handle_send (security_critical, opus verifier diffing the open-relay guard), while B's is a broken Haiku prompt that would break /generate for every visitor and cannot be cheaply re-tested (the phase allows only 2 /generate calls). Putting both classes of risk under one verifier is the likeliest source of a correction round. Six items (A, C-write, D, F-extend, G, I) are ready at wave 0, so the scheduler has plenty of parallel work while A->B runs.
- STRUCTURAL: split the guidance's item C into p2-unit-tests-write (ready at wave 0, authored against the fixed contract, verified by collection against a pristine git HEAD copy of lambda_function.py so a concurrent edit cannot flake it) and p2-unit-tests-run (after B). This takes the test-authoring effort off the critical path entirely.
- STRUCTURAL: split the guidance's item F the same way — p2-harness-extend (wave 0, --dry-run only, plus a read-only describe-table of photometrics-boosted-officials) and p2-harness-run (after the deploy). Only the production run genuinely needs E.
- STRUCTURAL: the guidance had p2-deploy tail CloudWatch 'after the harness run in F', which is circular given E is F's prereq. Resolved by giving E its own post-deploy window (plus a read-only /send smoke invoke against a non-existent session that returns 400 and writes nothing) and putting the post-harness CloudWatch window inside p2-harness-run's own acceptance criteria.
- TIERING deviation (upward): p2-unit-tests-run gets an opus/high verifier rather than the sonnet the guidance implies for test items, and is marked security_critical, because it is permitted to make minimal fixes to lambda_function.py when a test exposes a real defect — so its diff can reach the send path. The verifier must re-run pytest AND diff the file to confirm no test was weakened and no guard loosened. Defects inside the authorization path must be reported, not patched.
- TIERING deviation (upward): p2-deploy is marked security_critical with an opus/high verifier. The action is mechanical, but it is the item that makes the authorization change live in production; the verifier independently re-reads CodeSha256 from AWS and re-runs the CloudWatch window instead of trusting the handoff.
- TIERING deviation (upward): p2-harness-run gets an opus/high verifier rather than the sonnet the guidance suggests for harness items. It is the only end-to-end evidence that suppression actually enforces in production; a false green here would ship an unenforced control, so the verifier independently re-scans all three tables for residue and re-reads CloudWatch.
- TIERING deviation (upward): p2-live-generate-check gets an opus/high verifier. Its evidence is destroyed by its own mandatory cleanup, so verification is judgment about whether the pasted evidence chain is internally consistent plus independent CloudWatch corroboration — not a re-run. The phase's second /generate call is explicitly reserved for this verifier and only if the chain looks inconsistent.
- TIERING as-guided: p2-exclusion-hardening and p2-source-and-location are sonnet/high implementer + opus/high verifier (Lambda code items). p2-deploy-script, p2-harness-extend, p2-report-tool, p2-frontend-source, p2-report-verify, p2-unit-tests-write are sonnet/high both sides (tooling/scripts). p2-docs is sonnet/medium both sides. No item was tiered down from the guidance.
- ENVIRONMENT: per the Phase 01 lesson, no item in this DAG uses Chrome MCP. p2-frontend-source verifies statically (hugo --quiet, node --check on the extracted inline script blocks, greps, and a diff of every priorities-related line against HEAD); the lead does the live browser and GA4 verification outside the DAG after pushing to master.
