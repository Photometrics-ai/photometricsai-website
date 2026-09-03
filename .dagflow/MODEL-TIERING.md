# Model Tiering Log

Cross-phase, repo-root calibration log — persists across every phase and
every task run through this orchestrator in this repo. Read by the planning
stage before it assigns per-item model tiers; appended to by the lead at
phase close.

**Who writes entries:** the lead drafts a suggested entry from observable
signals (how much the plan needed revision, how many items turned out to
have real cross-item subtlety vs. being flat independent checks, how many
correction rounds were needed and why). The human confirms or edits the
verdict before it's treated as guidance — a felt sense of "that was
overkill" or "that actually needed the stronger model" is the real signal
here, not something to infer and self-certify.

**How the planner uses it:** given a new task, skim entries whose task type
matches or is similar. Default to the most recent matching guidance unless
there's a specific reason in front of you to deviate — if you deviate, say
why in `model_rationale` for the affected items.

---

## <date> — <task type, e.g. "standard security checklist audit">

**Planning model used:** opus / high
**Verdict:** right-sized | overpowered | underpowered
**Why:** <e.g. "DAG had almost no real dependency structure — 20 of 22 items were flat independent checks against a well-known checklist; that judgment call didn't need Opus.">
**Guidance for next similar task:** <e.g. "Use sonnet/high for planning on standard checklist-style audits. Reserve opus for planning when the task requires discovering the dependency structure itself (unclear scope, novel architecture, cross-cutting integration checks).">

**Implementer default used:** <model/effort> — verdict: <...> — why: <...>
**Verifier default used:** <model/effort> — verdict: <...> — why: <...>

---
## 2026-09-03 — Phase 01 verify-funnel: infra verification + test harness + read-only investigations (DRAFT, awaiting Ari's confirmation)

**Planning model used:** opus / high
**Verdict:** right-sized
**Why:** The plan needed zero structural revision; the planner correctly identified the shared-table lock and the browser lock, and its two upward tiering deviations (opus verifiers on security-critical investigations, sonnet for docs) were justified. 7 items, 0 correction rounds needed on any item that ran.
**Guidance for next similar task:** Keep opus/high for planning phases that mix production-touching tests with read-only investigations. For a pure read-only investigation phase, sonnet/high planning would likely suffice.

**Implementer default used:** sonnet/high (harness, run), sonnet/medium (investigations, docs) — verdict: right-sized — why: every implementer passed its verifier on round 0; handoffs were thorough and honest (negative findings reported as such).
**Verifier default used:** opus/high on security-critical items, sonnet/medium elsewhere — verdict: right-sized — why: the opus verifiers independently recomputed data (baseline) and re-ran production reads (harness-run) rather than trusting handoffs; the sonnet verifier on docs traced every claim to a handoff. No false verifies observed.
**Environment lesson (not a tiering issue):** browser-driven items cannot run from subagents here (shared Chrome tab group with the lead → tab eviction). Assign browser items to the lead.

---
