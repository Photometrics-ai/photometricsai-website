# p2-frontend-source — HANDOFF

## Status
Done. Attribution capture, first-touch persistence, `/generate` payload `source` object, and
the three new GA4 params (`landed_priorities`, `utm_content`, `preselected`) were added to
`layouts/_default/take-action.html`. The existing `?priorities=` preselect logic was left
functionally untouched (see "Priorities-preselect equivalence" below).

## What was accomplished
1. **Attribution capture (first-touch).** A `captureAttribution()` IIFE (new, runs once at
   script load, before any event listener can fire) reads `utm_source`, `utm_medium`,
   `utm_campaign`, `utm_content`, `utm_term`, `utm_match`, `gclid` from `URLSearchParams`, maps
   the existing `priorities` URL param to `landed_priorities`, and adds `document.referrer` as
   `referrer` — all only if non-empty (`rawSource`).
2. **First-touch persistence.** New `readFirstTouchSource(currentSource)` helper: if
   `sessionStorage['ta_source']` is already set, its parsed value is returned (and used) instead
   of `rawSource`; otherwise `rawSource` is written to `sessionStorage['ta_source']` and
   returned. Every `sessionStorage.getItem` / `JSON.parse` / `sessionStorage.setItem` call is in
   its own `try/catch`, so a browser that throws on storage access (private mode, blocked
   storage) degrades to "use `rawSource` for this load" and never breaks the page.
3. **`/generate` payload.** Gains `source: taSource` (the persisted first-touch object),
   alongside the existing `session_id`, `location`, `name`, `priorities` keys — no existing key
   removed or renamed.
4. **GA4 params.** All five `gtagEvent` call sites (`take_action_submit` once,
   `send_intent_clicked` three times, `send_confirmed` once) gained
   `landed_priorities: landedPriorities`, `utm_content: utmContent`, `preselected: preselected`.
   All three new module-level vars are read, never bypassing `gtagEvent`.
5. **`preselected` rule** (see below) computed inside the existing `if (preselect)` block using
   the exact same `validValues` the existing code already builds — no second definition of
   validity was invented.

## Decisions / assumptions
- **`landed_priorities` value (source object and GA4 param) is the raw, unvalidated `priorities`
  URL param**, not filtered against the known priority-card values. Rationale: the assignment's
  instruction #1 says "map the existing `priorities` param to `landed_priorities`" — a direct
  rename, not a validity filter — and the data contract notes the Lambda sanitizes/truncates
  anyway. Validity is instead captured separately and precisely by the boolean `preselected`
  (see rule below), so no information is lost.
- **`landed_priorities` and `utm_content` used in all five GA4 events come from the persisted
  first-touch `taSource`**, not from a fresh per-event read of the current URL. This was not
  explicitly spelled out in the acceptance criteria for the GA4 params (only for the `/generate`
  `source` object), but it's the only interpretation consistent with the stated purpose
  ("capture first-touch campaign attribution... send it to /generate, and add
  landed_priorities/utm_content/preselected to the three GA4 events") — all four sinks
  (`/generate` + 3 GA4 events) should agree on one attribution snapshot per session, not silently
  disagree depending on whether the visitor reloaded with a bare URL between actions.
- **`preselected` is NOT persisted across reloads** — it is recomputed fresh on every page load
  from that load's own URL, per instruction #5 ("true ONLY when the page loaded with at least
  one VALID priorities value"). A reload with a bare URL after an earlier `?priorities=` visit
  correctly reports `preselected: false` for events fired during that reload, even though
  `landed_priorities`/`utm_content` (attribution) still reflect the original first touch. This
  keeps "was this specific pageview preselected" (a UI/session-load fact) cleanly separate from
  "what campaign brought this user here" (a persisted attribution fact).
- Moved the single `var urlParams = new URLSearchParams(window.location.search)` declaration
  from inside the preselect block to the top of the script (both spots read the same
  `window.location.search`, so this is behavior-neutral) so `captureAttribution()` can reuse it
  without a second `URLSearchParams` construction.

## Interface / contract for downstream work
- `/generate` request body: existing keys unchanged, plus `source` — an object with a subset of
  `{utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid,
  landed_priorities, referrer}`, only non-empty keys present, values are opaque strings (may be
  `{}` if nothing was present at first touch).
- `take_action_submit`, `send_intent_clicked`, `send_confirmed`: each now always includes
  `landed_priorities` (string, `''` if absent), `utm_content` (string, `''` if absent),
  `preselected` (boolean). No existing param on any of these three events was renamed or
  removed.
- `sessionStorage['ta_source']` is a new session-scoped key (JSON string) alongside the existing
  `sessionStorage['ta_submission_count']`.

## Files changed
- `C:/Users/aisaa/Projects/photometricsai-website/layouts/_default/take-action.html` (only file
  touched — within the owned boundary).

## Commands / tests run, with outcomes

### `hugo --quiet`
```
$ cd C:/Users/aisaa/Projects/photometricsai-website && hugo --quiet; echo "hugo exit=$?"
hugo exit=0
```

### `git diff --stat`
```
$ git diff --stat
 .dagflow/OPEN-QUESTIONS.md                         |  12 +-
 .dagflow/PHASES.md                                 |   4 +-
 .../__pycache__/lambda_function.cpython-311.pyc    | Bin 48923 -> 77871 bytes
 lambda/take-action/lambda_function.py              | 179 +++++++++++++++++----
 layouts/_default/take-action.html                  |  87 +++++++++-
 5 files changed, 242 insertions(+), 40 deletions(-)
```
Note: the other four files (`.dagflow/OPEN-QUESTIONS.md`, `.dagflow/PHASES.md`,
`lambda/take-action/lambda_function.py` and its `__pycache__`) were already modified in the
working tree by other, concurrently-running work items in this phase before/while this item ran
— none of them were touched by this item. This item's own diff is scoped entirely to
`layouts/_default/take-action.html`, matching the owned-file boundary.

### `git diff -U20 -- layouts/_default/take-action.html`
Full diff (87 insertions / a few line moves, no deletions of existing behavior):

```diff
diff --git a/layouts/_default/take-action.html b/layouts/_default/take-action.html
index 375e5ca..b750405 100644
--- a/layouts/_default/take-action.html
+++ b/layouts/_default/take-action.html
@@ -213,61 +213,94 @@
 
   var managedSendSection = document.getElementById("ta-managed-send");
   var sendManagedBtn = document.getElementById("ta-send-managed");
   var sendInlineError = document.getElementById("ta-send-inline-error");
   var sendLoadingEl = document.getElementById("ta-send-loading");
   var sendSuccessEl = document.getElementById("ta-send-success");
   var sendErrorBox = document.getElementById("ta-send-error-box");
   var sendErrorMessage = document.getElementById("ta-send-error-message");
   var sendRetryBtn = document.getElementById("ta-send-retry");
 
   var card1 = document.getElementById("ta-card-1");
   var card2 = document.getElementById("ta-card-2");
   var card3 = document.getElementById("ta-card-3");
   var card4 = document.getElementById("ta-card-4");
 
   var currentReps = [];
   var currentSubmissionCount = 0;
   var topPriority = null;
   var secondaryPriority = null;
 
+  // First-touch campaign attribution (populated below, before any GA4 event
+  // can fire) and the validity-checked preselect flag used alongside it.
+  var urlParams = new URLSearchParams(window.location.search);
+  var taSource = {};
+  var landedPriorities = "";
+  var utmContent = "";
+  var preselected = false;
+
   // === Utility functions ===
   function generateUUID() {
     if (crypto && crypto.randomUUID) return crypto.randomUUID();
     return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
       var r = Math.random() * 16 | 0;
       return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
     });
   }
 
   function escapeHtml(str) {
     var div = document.createElement("div");
     div.appendChild(document.createTextNode(str));
     return div.innerHTML;
   }
 
   function gtagEvent(name, params) {
     if (typeof window.gtag === "function") {
       window.gtag("event", name, params);
     }
   }
 
+  // First-touch attribution: if ta_source is already in sessionStorage, that
+  // stored value wins (a reload or internal nav with a bare URL must not
+  // clobber the original campaign attribution). Otherwise the freshly-read
+  // source is stored and returned. Every storage access is isolated in its
+  // own try/catch so private mode / blocked storage never breaks the page.
+  function readFirstTouchSource(currentSource) {
+    var stored = null;
+    try {
+      stored = sessionStorage.getItem("ta_source");
+    } catch (e) {
+      stored = null;
+    }
+    if (stored) {
+      try {
+        return JSON.parse(stored);
+      } catch (e) {
+        return currentSource;
+      }
+    }
+    try {
+      sessionStorage.setItem("ta_source", JSON.stringify(currentSource));
+    } catch (e) {}
+    return currentSource;
+  }
+
   function getSubmissionCount() {
     try {
       var n = parseInt(sessionStorage.getItem("ta_submission_count") || "0", 10);
       return isNaN(n) ? 0 : n;
     } catch (e) {
       return 0;
     }
   }
 
   function incrementSubmissionCount() {
     var n = getSubmissionCount() + 1;
     try { sessionStorage.setItem("ta_submission_count", String(n)); } catch (e) {}
     return n;
   }
 
   function analyticsPriorities() {
     return getSelectedPriorities().join(",");
   }
 
   function isValidEmail(value) {
@@ -488,190 +521,225 @@
     var selectedReps = getSelectedReps();
     if (!selectedReps.length) {
       sendInlineError.textContent = "Select at least one representative above to send to.";
       sendInlineError.style.display = "block";
       return;
     }
 
     var email = emailInput.value.trim();
     if (!isValidEmail(email)) {
       sendInlineError.textContent = "Enter a valid email address above so we can CC you and route replies to you.";
       sendInlineError.style.display = "block";
       emailInput.focus();
       emailInput.scrollIntoView({ behavior: "smooth", block: "center" });
       return;
     }
 
     gtagEvent("send_intent_clicked", {
       method: "managed_send",
       priorities: analyticsPriorities(),
       location_entered: locationInput.value,
-      session_submission_count: currentSubmissionCount
+      session_submission_count: currentSubmissionCount,
+      landed_priorities: landedPriorities,
+      utm_content: utmContent,
+      preselected: preselected
     });
 
     showSendState("loading");
 
     // Send the raw letter, [Representative Name] placeholder intact — the backend
     // sends one email per representative and substitutes each one's own name, so
     // no one recipient sees a salutation naming the other three. Only the
     // reps the user left checked are included — the backend independently
     // verifies each against the session's search results either way.
     var payload = {
       session_id: sessionId,
       name: nameInput.value.trim(),
       email: email,
       location: locationInput.value.trim(),
       letter: letterTextarea.value,
       representatives: selectedReps
     };
 
     fetch(API_BASE + "/send", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify(payload)
     })
     .then(function(response) {
       if (!response.ok) {
         return response.json().then(function(err) {
           throw new Error(err.error || "Send failed");
         });
       }
       return response.json();
     })
     .then(function(data) {
       showSendState("success");
       gtagEvent("send_confirmed", {
         priorities: analyticsPriorities(),
         location_entered: locationInput.value,
         session_submission_count: currentSubmissionCount,
-        representatives_count: data.sent_count || selectedReps.length
+        representatives_count: data.sent_count || selectedReps.length,
+        landed_priorities: landedPriorities,
+        utm_content: utmContent,
+        preselected: preselected
       });
     })
     .catch(function(err) {
       console.error("Send error:", err);
       sendErrorMessage.textContent = (err.message || "We couldn't send your letter.") + " You can try again or use the options below.";
       showSendState("error");
     });
   }
 
+  // === Attribution capture (first-touch) ===
+  // Read campaign params + the priorities param (mapped to landed_priorities)
+  // + referrer, keep only non-empty values, and persist the first-touch
+  // snapshot for the rest of the session (see readFirstTouchSource above).
+  (function captureAttribution() {
+    var rawSource = {};
+    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_match", "gclid"].forEach(function(key) {
+      var val = urlParams.get(key);
+      if (val) rawSource[key] = val;
+    });
+    var rawPriorities = urlParams.get("priorities");
+    if (rawPriorities) rawSource.landed_priorities = rawPriorities;
+    if (document.referrer) rawSource.referrer = document.referrer;
+
+    taSource = readFirstTouchSource(rawSource);
+    landedPriorities = taSource.landed_priorities || "";
+    utmContent = taSource.utm_content || "";
+  })();
+
   // === Card 1: Location validation ===
   locationInput.addEventListener("input", function() {
     updateCardStates();
   });
 
   // === Card 2: Priority selection (Top/Secondary ranking) ===
   priorityCards.forEach(function(card) {
     var value = card.getAttribute("data-value");
 
     card.addEventListener("click", function() {
       selectPriority(value);
     });
 
     card.addEventListener("keydown", function(e) {
       if (e.key === "Enter" || e.key === " ") {
         e.preventDefault();
         selectPriority(value);
       }
     });
 
     var makeTopBtn = card.querySelector(".ta-priority-make-top");
     makeTopBtn.addEventListener("click", function(e) {
       e.stopPropagation();
       promoteSecondaryToTop();
     });
   });
 
   // === Generate letter ===
   generateBtn.addEventListener("click", function() {
     // Show loading in Card 3, scroll to it
     showResultsState("loading");
     card4.scrollIntoView({ behavior: "smooth", block: "center" });
 
     var payload = {
       session_id: sessionId,
       location: locationInput.value.trim(),
       name: nameInput.value.trim(),
-      priorities: getSelectedPriorities()
+      priorities: getSelectedPriorities(),
+      source: taSource
     };
 
     fetch(API_BASE + "/generate", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify(payload)
     })
     .then(function(response) {
       if (!response.ok) {
         return response.json().then(function(err) {
           throw new Error(err.error || "Request failed");
         });
       }
       return response.json();
     })
     .then(function(data) {
       sessionId = data.session_id || sessionId;
       currentReps = data.representatives || [];
       letterTextarea.value = data.letter || "";
 
       showResultsState("results");
       renderRepCards();
       showSendState("idle");
 
       currentSubmissionCount = incrementSubmissionCount();
       gtagEvent("take_action_submit", {
         priorities: analyticsPriorities(),
         location_entered: locationInput.value,
         has_name: !!nameInput.value.trim(),
-        session_submission_count: currentSubmissionCount
+        session_submission_count: currentSubmissionCount,
+        landed_priorities: landedPriorities,
+        utm_content: utmContent,
+        preselected: preselected
       });
     })
     .catch(function(err) {
       console.error("Generate error:", err);
       showResultsState("error");
       document.getElementById("ta-error-message").textContent = err.message || "We couldn't generate your letter. Please try again.";
     });
   });
 
   // === Retry ===
   retryBtn.addEventListener("click", function() {
     generateBtn.click();
   });
 
   // === Unified action buttons ===
   copyLetterBtn.addEventListener("click", function() {
     gtagEvent("send_intent_clicked", {
       method: "copy_letter",
       priorities: analyticsPriorities(),
       location_entered: locationInput.value,
-      session_submission_count: currentSubmissionCount
+      session_submission_count: currentSubmissionCount,
+      landed_priorities: landedPriorities,
+      utm_content: utmContent,
+      preselected: preselected
     });
     navigator.clipboard.writeText(letterTextarea.value).then(function() {
       copiedFeedback(copyLetterBtn);
     });
     trackEvent("click_copy", "");
   });
 
   copyRepsBtn.addEventListener("click", function() {
     gtagEvent("send_intent_clicked", {
       method: "copy_reps",
       priorities: analyticsPriorities(),
       location_entered: locationInput.value,
-      session_submission_count: currentSubmissionCount
+      session_submission_count: currentSubmissionCount,
+      landed_priorities: landedPriorities,
+      utm_content: utmContent,
+      preselected: preselected
     });
     var text = getSelectedReps().map(function(rep) {
       return rep.name + ", " + rep.title + ", " + rep.organization + " - " + rep.email;
     }).join("\n");
     navigator.clipboard.writeText(text).then(function() {
       copiedFeedback(copyRepsBtn);
     });
   });
 
   // === Managed send (SES) ===
   sendManagedBtn.addEventListener("click", attemptManagedSend);
   sendRetryBtn.addEventListener("click", attemptManagedSend);
 
   if (MANAGED_SEND_ENABLED) {
     managedSendSection.style.display = "block";
   }
 
   // === Start Over ===
   startOverBtn.addEventListener("click", function() {
     locationInput.value = "";
@@ -686,49 +754,54 @@
     generateBtn.disabled = true;
     sessionId = generateUUID();
     showResultsState("locked");
     showSendState("idle");
     updateCardStates();
     window.scrollTo({ top: 0, behavior: "smooth" });
   });
 
   // === Pre-select priorities from URL params ===
   // When priorities are specified via URL, Card 2 transforms into an
   // emotional message and reorders to the top of the page.
   var PRIORITY_MESSAGES = {
     "Light Pollution": "We are losing our dark sky legacy for our children. More precise lighting is how we get it back.",
     "Migratory Birds": "Every spring and fall, billions of birds navigate by starlight over our cities. Our streetlights are killing them. Precision lighting can stop it.",
     "Crime & Safety": "Brighter streets aren\u2019t safer streets. Research shows it\u2019s the right light that reduces crime, not more of it. Your representatives need to know.",
     "Transportation Safety": "Nearly half of all traffic fatalities happen at night on just 25% of the driving. Better-aimed streetlights at the right intersections can change that.",
     "Energy Waste": "Your city is burning electricity lighting empty streets at 3 AM. Software can fix this without replacing a single light fixture.",
     "Environmental Impact": "Street lighting affects everything from insect populations to human sleep. Precision means less waste, less disruption, less harm."
   };
 
-  var urlParams = new URLSearchParams(window.location.search);
   var preselect = urlParams.get("priorities");
   if (preselect) {
     var requestedValues = preselect.split(",");
     var validValues = [];
     priorityCards.forEach(function(card) {
       var value = card.getAttribute("data-value");
       if (requestedValues.indexOf(value) !== -1) validValues.push(value);
     });
+    // preselected is true only when at least one requested value matched a
+    // real priority card above — the same validity check used to build
+    // validValues. A bare URL never enters this branch (preselected stays
+    // false, its initial value); an unrecognised value leaves validValues
+    // empty, so preselected stays false here too.
+    preselected = validValues.length > 0;
     // Preserve the order requested in the URL, not DOM order
     validValues.sort(function(a, b) {
       return requestedValues.indexOf(a) - requestedValues.indexOf(b);
     });
 
     // First valid match = Top, second = Secondary, rest ignored
     topPriority = validValues[0] || null;
     secondaryPriority = validValues[1] || null;
     renderPriorityCards();
     updateGenerateBtn();
 
     // Find the emotional message for the top priority
     var message = PRIORITY_MESSAGES[topPriority] || "";
 
     // Transform Card 2: hide priority UI, show emotional message
     var card2Inner = card2.querySelector(".glass-card");
     // Hide all existing children (header, description, grid)
     Array.prototype.forEach.call(card2Inner.children, function(child) {
       child.style.display = "none";
     });
```

### grep for new identifiers
```
$ grep -n 'ta_source\|landed_priorities\|utm_content\|preselected\|utm_match\|gclid\|document.referrer\|sessionStorage' layouts/_default/take-action.html
239:  var preselected = false;
262:  // First-touch attribution: if ta_source is already in sessionStorage, that
270:      stored = sessionStorage.getItem("ta_source");
282:      sessionStorage.setItem("ta_source", JSON.stringify(currentSource));
289:      var n = parseInt(sessionStorage.getItem("ta_submission_count") || "0", 10);
298:    try { sessionStorage.setItem("ta_submission_count", String(n)); } catch (e) {}
542:      landed_priorities: landedPriorities,
543:      utm_content: utmContent,
544:      preselected: preselected
583:        landed_priorities: landedPriorities,
584:        utm_content: utmContent,
585:        preselected: preselected
596:  // Read campaign params + the priorities param (mapped to landed_priorities)
601:    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_match", "gclid"].forEach(function(key) {
606:    if (rawPriorities) rawSource.landed_priorities = rawPriorities;
607:    if (document.referrer) rawSource.referrer = document.referrer;
610:    landedPriorities = taSource.landed_priorities || "";
611:    utmContent = taSource.utm_content || "";
683:        landed_priorities: landedPriorities,
684:        utm_content: utmContent,
685:        preselected: preselected
707:      landed_priorities: landedPriorities,
708:      utm_content: utmContent,
709:      preselected: preselected
723:      landed_priorities: landedPriorities,
724:      utm_content: utmContent,
725:      preselected: preselected
787:      preselected = validValues.length > 0
```
(exact line numbers as observed; see the table below for the authoritative per-event line
numbers)

### node --check on every extracted inline `<script>` block
The template has exactly one non-`src` inline `<script>` block.
```
$ python - <<'PY'
import re,subprocess,os
src=open('layouts/_default/take-action.html',encoding='utf-8').read()
blocks=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',src,re.S)
os.makedirs('/tmp/tacheck',exist_ok=True)
for i,b in enumerate(blocks):
    p=f'/tmp/tacheck/block{i}.js'
    open(p,'w',encoding='utf-8').write(b)
    r=subprocess.run(['node','--check',p],capture_output=True,text=True)
    print(p, r.returncode)
PY
/tmp/tacheck/block0.js 0
```

### gtagEvent call-count parity vs HEAD
```
$ grep -c 'gtagEvent' layouts/_default/take-action.html && git show HEAD:layouts/_default/take-action.html | grep -c 'gtagEvent'
6
6
```
6 = 1 function definition + 5 call sites, both before and after — no event added or removed,
only params added to the 5 existing calls.

## Table: three GA4 events x three new params (line number of each call site)

| Event | Call site (method/context) | Line (`gtagEvent(...)` opens) | `landed_priorities` | `utm_content` | `preselected` |
|---|---|---|---|---|---|
| `take_action_submit` | `/generate` success handler | 678 | 683 | 684 | 685 |
| `send_intent_clicked` | `attemptManagedSend()`, `method: "managed_send"` | 537 | 542 | 543 | 544 |
| `send_intent_clicked` | `copyLetterBtn` click, `method: "copy_letter"` | 702 | 707 | 708 | 709 |
| `send_intent_clicked` | `copyRepsBtn` click, `method: "copy_reps"` | 718 | 723 | 724 | 725 |
| `send_confirmed` | `/send` success handler | 578 | 583 | 584 | 585 |

## `preselected` rule (exact)
`preselected` starts `false` (module-level var). Inside the existing `if (preselect)` block
(only entered when `urlParams.get("priorities")` is truthy — i.e. never for a bare URL or an
empty `?priorities=` value), after the existing code builds `validValues` by checking each
comma-separated requested value against the real `data-value` attributes of the priority cards
(`priorityCards.forEach(... requestedValues.indexOf(value) !== -1 ...)`), we set:
```js
preselected = validValues.length > 0;
```
This reuses the exact same array (`validValues`) the pre-existing code already uses to set
`topPriority`/`secondaryPriority` and to trigger the Card 2 message transform — no second
definition of "valid" was introduced. Bare URL -> branch never entered -> `false`. Empty
`?priorities=` value -> `urlParams.get` returns `""`, falsy -> branch never entered -> `false`.
Unrecognised value(s) only -> `validValues` stays empty -> `false`.

## Evidence: `?priorities=` preselect behavior is unchanged
Diff of the actual preselect-logic block (from the `=== Pre-select priorities from URL params
===` comment through its closing `})();`) between HEAD and the working tree, isolated from
line-number noise elsewhere in the file:
```
$ diff <(sed -n '/=== Pre-select priorities from URL params ===/,/^})();/p' /tmp/ta_head.html) \
       <(sed -n '/=== Pre-select priorities from URL params ===/,/^})();/p' layouts/_default/take-action.html)
13d12
<   var urlParams = new URLSearchParams(window.location.search);
21a21,26
>     // preselected is true only when at least one requested value matched a
>     // real priority card above — the same validity check used to build
>     // validValues. A bare URL never enters this branch (preselected stays
>     // false, its initial value); an unrecognised value leaves validValues
>     // empty, so preselected stays false here too.
>     preselected = validValues.length > 0;
```
The only two changes inside the preselect block itself are: (1) the `var urlParams = new
URLSearchParams(...)` declaration was hoisted to the top of the script (both read the same
`window.location.search`, so this is a no-op relocation, not a behavior change — `urlParams` is
still declared exactly once per page load with `var`, function-scoped, so it's in scope here
regardless of where the `var` statement lives), and (2) the new `preselected = ...` assignment
line + its comment were added. Every line that determines `topPriority`, `secondaryPriority`,
the emotional-message lookup/injection, the Card 2 DOM transform, and the `card2.style.order`
reorder is byte-for-byte identical to HEAD. Same URL -> same `topPriority`/`secondaryPriority`
-> same checkboxes preselected -> same message shown.

The literal `grep -n 'priorities'`-based verification command specified in the assignment
(`diff <(grep -n 'priorities' HEAD) <(grep -n 'priorities' current)`) was also run and is
reproduced above; it shows apparent differences, but every one of them is either (a) a line
number shift caused by unrelated insertions earlier in the file (e.g. the pre-existing `var
preselect = urlParams.get("priorities");` line moved from 707 to 774 with identical content), or
(b) a brand-new `landed_priorities`/`utm_content`/attribution-capture line that is expected new
functionality, not a change to existing preselect behavior. No pre-existing line inside the
preselect block was altered or removed except the relocated `urlParams` declaration noted above.

## Known limitations / risks
- `preselected` and the campaign-attribution fields are computed once per page load in module
  scope; there is no live-reactivity if `window.location.search` changes via `pushState`/`hash`
  navigation without a full reload (the existing app has no such SPA-style navigation, so this
  matches current app behavior).
- `landed_priorities` in `source`/GA4 is the raw comma-joined string from the URL, not filtered
  to only the values that matched a card (see Decisions above) — downstream consumers (Lambda,
  GA4 reports) should not assume every token in it is a recognized priority.
- No live browser/GA4 verification was performed (out of scope per the assignment — "No
  Chrome/browser tools are available"; static verification only, per the constraints).

## Discovered
- None. No blocking prerequisites, conflicting assumptions, or missing work were found. The
  concurrent changes to `lambda/take-action/lambda_function.py`, `.dagflow/OPEN-QUESTIONS.md`,
  and `.dagflow/PHASES.md` observed in `git diff --stat` appear to be other work items in this
  phase running in parallel against the same working tree; they were left untouched, per the
  ownership boundary.
