You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-frontend-source
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Capture first-touch campaign attribution in the browser, send it to /generate, and add landed_priorities / utm_content / preselected to the three GA4 events — without disturbing the existing ?priorities= preselect behaviour.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/layouts/_default/take-action.html

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Implement the frontend half of the Take Action attribution contract: capture first-touch campaign parameters, send them to /generate, and enrich the three GA4 events — with zero change to how ?priorities= already preselects and messages.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly one file: layouts/_default/take-action.html (Hugo template, ~752 lines, HTML + inline JS). Nothing else. Do not touch lambda/, do not touch hugo.toml, do not build into public/ beyond what `hugo` writes.

CURRENT LANDMARKS (approximate; re-grep)
- /generate payload built ~:589
- /send payload ~:518
- gtagEvent helper ~:248
- GA4 events: take_action_submit ~:619, send_intent_clicked ~:504 / :640 / :652, send_confirmed ~:542
- ?priorities= handling ~:694-748

WHAT TO IMPLEMENT
1. On load, read URLSearchParams: utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid; map the existing `priorities` param to `landed_priorities`; plus document.referrer. Build a plain `source` object containing only non-empty values.
2. First-touch persist: if sessionStorage['ta_source'] is unset, store JSON.stringify(source); otherwise read the stored one and use THAT for the rest of the session — a reload with a bare URL must keep the original attribution. Wrap every sessionStorage read/write in try/catch (private mode / blocked storage must not break the page).
3. Add the resulting `source` object to the /generate request payload.
4. Add three params to take_action_submit, send_intent_clicked and send_confirmed (all call sites of each): landed_priorities (string, '' if absent), utm_content (string, '' if absent), preselected (boolean). Route them through the existing gtagEvent helper rather than bypassing it.
5. `preselected` is true ONLY when the page loaded with at least one VALID priorities value — reuse whatever validity check the existing ?priorities= handling already applies; do not invent a second definition. A bare URL, an empty value, or an unrecognised value ⇒ false.

HARD CONSTRAINTS
- The existing ?priorities= behaviour must be unchanged in effect: the same URLs preselect the same checkboxes and show the same messaging. A verifier diffs every `priorities` line against git HEAD.
- Do not rename or remove any existing GA4 event or param.
- Do not commit or push. The lead pushes to master (Amplify auto-deploys) and verifies live in the browser — that is outside your scope, and so is any GA4 or Google Ads configuration change.
- No Chrome/browser tools are available to you. Verify statically: `hugo --quiet` (Hugo v0.154.5 extended IS installed on this host), `node --check` on the extracted inline script blocks (node IS installed), and greps.

DATA CONTRACT (frontend half)
/generate payload gains a `source` object with keys utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer (omit empties). The Lambda sanitizes each to <=200 chars and drops unknown keys, so sending extra keys is harmless but pointless — send exactly these.
GA4 events take_action_submit, send_intent_clicked, send_confirmed gain landed_priorities (string or ''), utm_content (string or ''), preselected (boolean).
Context: Google Ads will append utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={adgroupid}&utm_term={keyword}&utm_match={matchtype}, so utm_content arrives as a numeric ad group id — treat every value as an opaque string.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
`hugo --quiet` exits 0; every extracted inline script block passes `node --check`; greps show each new param at every relevant call site. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md with: the full diff, the raw hugo and node --check output, a table of the three GA4 events × three new params showing the line number of each call site, the exact rule you used for `preselected`, and evidence (diff of the priorities-related lines vs HEAD) that the preselect behaviour is unchanged.

ACCEPTANCE CRITERIA:
- On page load the script reads URLSearchParams for utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid and the existing priorities param (as landed_priorities), plus document.referrer, and builds a `source` object with only non-empty values.
- First-touch persistence: the source object is written to sessionStorage['ta_source'] only if that key is not already set, so a reload or an internal navigation preserves the original attribution. All sessionStorage access is wrapped so a browser that throws on storage access does not break the page.
- The /generate request payload gains a `source` object (the persisted first-touch one), alongside everything it already sends.
- GA4 events take_action_submit, send_intent_clicked and send_confirmed each gain params landed_priorities (string, '' when absent), utm_content (string, '' when absent) and preselected (boolean).
- `preselected` is true only when the page loaded with at least one VALID priorities value (a value the existing code accepts and applies), and false for a bare URL or an unrecognised value. The definition used is visible in the diff and stated in the handoff.
- The existing ?priorities= behaviour is byte-for-byte equivalent in effect: the same values preselect the same checkboxes and the same messaging appears. No existing GA4 param was renamed or removed.
- `hugo --quiet` builds the site with exit 0 from the repo root.
- The inline script extracted from the template passes `node --check`.
- The working-tree diff touches only layouts/_default/take-action.html.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website && hugo --quiet; echo "hugo exit=$?"
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U20 -- layouts/_default/take-action.html
- grep -n 'ta_source\|landed_priorities\|utm_content\|preselected\|utm_match\|gclid\|document.referrer\|sessionStorage' C:/Users/aisaa/Projects/photometricsai-website/layouts/_default/take-action.html
- cd C:/Users/aisaa/Projects/photometricsai-website && python - <<'PY'
import re,subprocess,tempfile,os
src=open('layouts/_default/take-action.html',encoding='utf-8').read()
blocks=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',src,re.S)
os.makedirs('/tmp/tacheck',exist_ok=True)
for i,b in enumerate(blocks):
    p=f'/tmp/tacheck/block{i}.js'
    open(p,'w',encoding='utf-8').write(b)
    print(p, subprocess.run(['node','--check',p],capture_output=True,text=True).returncode)
PY
- cd C:/Users/aisaa/Projects/photometricsai-website && grep -c 'gtagEvent' layouts/_default/take-action.html && git show HEAD:layouts/_default/take-action.html | grep -c 'gtagEvent'
- cd C:/Users/aisaa/Projects/photometricsai-website && git show HEAD:layouts/_default/take-action.html > /tmp/ta_head.html && diff <(grep -n 'priorities' /tmp/ta_head.html) <(grep -n 'priorities' layouts/_default/take-action.html) | head -40

CONTEXT BUDGET: sized to use no more than ~30% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
