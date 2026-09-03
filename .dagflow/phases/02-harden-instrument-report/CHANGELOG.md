# Phase <NN> DAG Changelog

Append-only. Only the lead writes entries here. Every DAG.md change —
new item, edge change, ownership reassignment, scope split, approved or
rejected discovery — gets one entry, oldest first.

## <date> — <short title>

**Source:** <item-id whose handoff/discovery prompted this, or "lead" if self-identified>
**Change:** <exactly what changed in DAG.md — new node, new edge, split item, reassigned owner, etc.>
**Rationale:** <why>
**Affected items:** <item-ids>
**Downstream impact:** <what this unblocks, re-blocks, or changes for other items>
**Decision:** approved | rejected — <if rejected, why the proposal wasn't applied>

---
## 2026-09-03 — Initial DAG authored (merged plan Phases 2+3+4)

**Source:** lead (planner run wf_afcc15bc-31c, opus/high)
**Change:** 14 items created; planner split unit tests and harness into write/run halves, kept the two lambda_function.py items sequential, and made p2-deploy its own smoke-tested step. No browser items (lead does Ads/GA4/live checks outside the DAG).
**Rationale:** Ari asked not to stop at phase boundaries; merging lets frontend, tests, deploy script, harness extension and report tool run while the Lambda items serialize.
**Affected items:** all
**Downstream impact:** none yet
**Decision:** approved — planner output accepted unchanged.

---
## 2026-09-03 — Lead applied Google Ads Final URL suffix

**Source:** lead
**Change:** No DAG change. Recorded in decisions/lead-ads-ga4-actions.md so p2-docs can cite it.
**Rationale:** Attribution contract requires the suffix; Ads changes are lead-only.
**Affected items:** p2-docs (may now describe the suffix as live), p2-report-tool (adgroups.json gets id 199915882237 for Environmental Impact)
**Downstream impact:** none
**Decision:** approved

---
## 2026-09-03 — Lead one-line fix after p2-source-and-location verification

**Source:** p2-source-and-location verifier (non-blocking finding)
**Change:** lambda_function.py:433 third user turn now says "output ONLY the JSON object (with "officials" and "normalized_location")" instead of "the JSON array", so Haiku is not told to omit the new field. No DAG change.
**Rationale:** Contradictory instruction would silently defeat normalized-location capture.
**Affected items:** p2-unit-tests-run, p2-deploy, p2-live-generate-check (which will prove the field is populated)
**Downstream impact:** none
**Decision:** approved

---
