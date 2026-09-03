# p2-exclusion-hardening — Handoff

**Status:** done
**Scope:** Harden the Take Action Lambda so a hard-bounced or user-flagged official address can neither be re-suggested by `/generate` nor be mailed by `/send`, paginate the exclusion scans, stop the sender address polluting the bounce table, and record what failed on the sends row.
**File owned/edited:** `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py` (only file touched). No commit/push made — left in the working tree per standing rule (4). No AWS calls (read or write) were made by this item; no `/generate` call was made (standing rule (6) token budget untouched by this item).

---

## What was accomplished (mapped to WHAT TO IMPLEMENT items 1-6)

1. **`filter_excluded(officials, excluded_emails) -> list`** — new module-level pure function, placed right after `sanitize_priorities` (~line 119). Case-insensitive on `official['email']`; officials with no/empty email are kept; `excluded_emails` of `None`/empty returns the input list unchanged (via `list(officials)`, a shallow copy — never mutates the input list, and no dict in it is ever mutated). Verified functionally (see Commands run below).

2. **`handle_generate`** now applies `filter_excluded` to `verified_reps` (the `search_officials` result) immediately after `officials_future.result()`, before `call_claude` is called, using the same `excluded_emails` set (`get_flagged_emails() | get_bounced_emails()`) already computed earlier in the function for the prompt's EXCLUDED EMAILS section. New log line: `print(f"Hard filter dropped {n_dropped} excluded officials")` (printed unconditionally, including when `n_dropped == 0`).

3. **`get_bounced_emails()` and `get_flagged_emails()`** now paginate via a `while True` loop keyed on `resp.get("LastEvaluatedKey")`, passing it back in as `ExclusiveStartKey` on the next `scan()` call, breaking when absent. `ProjectionExpression` and the `#st` → `"subtype"` `ExpressionAttributeNames` alias are unchanged. The Permanent/Complaint classification rule (`event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent")`) is byte-identical to before, just re-indented one level into the loop. The `try/except` wraps the entire pagination loop, so a scan failure at any page still returns whatever was accumulated so far as a `set()`, never raises.

4. **`record_bounce_event`**: before writing each recipient's row, compares `email.lower()` against `SES_SENDER_EMAIL.lower()` (computed once per call as `sender_email_lower`). On a match it prints `print(f"WARNING: bounce for sender address {email} — not recording")` and `continue`s — no `put_item` for that recipient — then proceeds with the remaining recipients in the loop as before. This is exactly the case the Phase 1 baseline flagged: `take-action@photometrics.ai` had 6 self-bounce rows in `photometrics-email-bounces` (see `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md`, "Discovered dependencies" #2).

5. **`handle_send`**: after the existing verification loop produces `verified_reps` and the `if not verified_reps: return 400` check (both untouched), a new block computes `excluded = get_bounced_emails() | get_flagged_emails()` and partitions `verified_reps` into `to_send` (goes to SES) and entries appended to `failed` as `{"email": ..., "reason": "suppressed"}` (does not go to SES — `ses.send_email` is only ever called from the loop over `to_send`, not `verified_reps`). An SES exception in that loop now appends `{"email": rep["email"], "reason": "ses_error"}` instead of the old bare email string. `sent_count`/`failed_count` are unchanged in the 200 response; a new `"failed"` key carries the full list of `{email, reason}` dicts.

6. **`log_send`**: gained a `representatives_failed=None` parameter (default preserves old callers, though the only call site is in this same file and was updated). Does exactly one `dynamodb.get_item(TableName=DYNAMO_TABLE, Key={"session_id": ...})` to fetch the generate row, then conditionally copies `priorities` (L), `source` (M), `location_city` (S), `location_state` (S) — each only if the raw DynamoDB attribute is present and non-empty on the generate row, otherwise the key is omitted from the sends-row item entirely (never written as an empty S/L/M). `representatives_offered` (N) = `str(len(...))` of the generate row's `representatives` L list (0 if absent), written whenever the generate row itself was found. `representatives_failed` (L of M, each `{email: S, reason: S}`) is always written, built from the new `representatives_failed` parameter (empty list writes fine as `{"L": []}` — DynamoDB only rejects empty `S`, not empty `L`). All previously-existing fields (`session_id`, `timestamp`, `constituent_email`, `location`, `representatives_sent`, `message_ids`, `ttl`) are unchanged in shape and are still always written.

---

## Hard constraints — explicit compliance statement

**`get_verified_representative_emails` and `already_sent` are byte-for-byte unchanged.** Verified programmatically by diffing each function's body (from `def <name>(` to the next `def `) between `git show HEAD:...` and the working-tree file:

```
get_verified_representative_emails UNCHANGED
already_sent UNCHANGED
```

Their call sites in `handle_send` are unchanged in order and effect — see the diff below: `already_sent(session_id)` is still called first (409 on duplicate), then `get_verified_representative_emails(session_id)` (400 if session unknown), then the existing per-rep verification loop and its `if not verified_reps: return 400` gate, all untouched. Only *after* that gate does the new suppression block run — suppression is strictly additive, layered after verification, and never replaces it. No rep bypasses `is_valid_email(...) and email.lower() in verified_emails` to reach `to_send`.

Neither `search_officials`'s prompt, `call_claude`, nor any other part of the letter-generation path was touched. Only `filter_excluded` (new), `handle_generate` (the new filter application before `call_claude`), `get_flagged_emails`, `get_bounced_emails`, `record_bounce_event`, `log_send`, and `handle_send` were edited.

No `/generate` call, no email send, no deploy, and no AWS write call (or any AWS call at all) was made by this item.

---

## Full diff (`git diff -U15 -- lambda/take-action/lambda_function.py`)

```diff
diff --git a/lambda/take-action/lambda_function.py b/lambda/take-action/lambda_function.py
index 59e4b3a..4440b00 100644
--- a/lambda/take-action/lambda_function.py
+++ b/lambda/take-action/lambda_function.py
@@ -104,30 +104,51 @@ def is_valid_email(value):
     return isinstance(value, str) and bool(EMAIL_RE.match(value.strip()))
 
 
 def sanitize_priorities(priorities):
     """Cap at 2 — the UI only ever lets a citizen pick a Top and a Secondary
     priority, so more than 2 should never be legitimate."""
     if not isinstance(priorities, list):
         return []
     cleaned = []
     for p in priorities[:2]:
         if isinstance(p, str) and p.strip():
             cleaned.append(p.strip()[:100])
     return cleaned
 
 
+def filter_excluded(officials, excluded_emails):
+    """Hard filter: drop any official whose 'email' matches (case-insensitively)
+    an entry in excluded_emails. This is the enforcement layer behind the
+    EXCLUDED EMAILS prompt section in search_officials() — the model is told
+    not to use these addresses, but nothing stopped it from doing so anyway
+    until this filter existed. An official with no email (or an empty one) is
+    KEPT, since there is nothing to exclude on. excluded_emails may be None or
+    empty, in which case the input list is returned unchanged. Pure function:
+    no I/O, no globals, does not mutate its arguments."""
+    if not excluded_emails:
+        return list(officials)
+    excluded_lower = {e.lower() for e in excluded_emails}
+    kept = []
+    for official in officials:
+        email = (official.get("email") or "").strip()
+        if email and email.lower() in excluded_lower:
+            continue
+        kept.append(official)
+    return kept
+
+
 def get_boosted_officials(location):
     """Find officials who have been emailed before or manually flagged for this area."""
     boosted = {}
 
     # 1) Auto-boost: query location-index GSI for sessions with send actions
     try:
         resp = dynamodb.query(
             TableName=DYNAMO_TABLE,
             IndexName="location-index",
             KeyConditionExpression="#loc = :loc",
             ExpressionAttributeNames={"#loc": "location"},
             ExpressionAttributeValues={":loc": {"S": location}},
             Limit=50,
             ScanIndexForward=False,
         )
@@ -776,30 +797,38 @@ def handle_generate(body):
         o for o in boosted_officials if o.get("email", "").lower() not in excluded_emails
     ]
 
     # Step 2: Haiku searches for officials + local context in parallel
     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
         officials_future = executor.submit(search_officials, location, priorities, civic_officials, boosted_officials, excluded_emails)
         research_future = executor.submit(research_location, location, priorities)
 
         # Officials are required — propagate errors
         try:
             verified_reps = officials_future.result()
         except Exception as e:
             print(f"Official search error: {e}")
             return respond(502, {"error": f"Failed to verify representatives: {e}"})
 
+        # Hard filter: the EXCLUDED EMAILS section in the search prompt is a
+        # soft instruction the model can ignore — this makes exclusion
+        # actually enforced before the letter is ever written for these reps.
+        before_filter_count = len(verified_reps)
+        verified_reps = filter_excluded(verified_reps, excluded_emails)
+        n_dropped = before_filter_count - len(verified_reps)
+        print(f"Hard filter dropped {n_dropped} excluded officials")
+
         # Research is optional — swallow errors
         try:
             local_context = research_future.result()
         except Exception as e:
             print(f"Local research error: {e}")
             local_context = ""
 
     # Step 3: Sonnet writes the letter using verified reps + local context
     try:
         result = call_claude(location, priorities, name, verified_reps, local_context)
     except Exception as e:
         print(f"Claude API error: {e}")
         return respond(502, {"error": f"Failed to generate letter: {e}"})
 
     # Log to DynamoDB (non-blocking — don't fail the request)
@@ -833,67 +862,88 @@ def handle_flag(body):
             Item={
                 "email": {"S": email},
                 "location": {"S": location},
                 "timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                 "ttl": {"N": str(int(time.time()) + (180 * 24 * 60 * 60))},  # 6 month TTL
             },
         )
     except Exception as e:
         print(f"Flag write error: {e}")
         return respond(500, {"error": "Failed to save flag."})
 
     return respond(200, {"status": "flagged"})
 
 
 def get_flagged_emails():
-    """Return set of emails that users have flagged as not current."""
+    """Return set of emails that users have flagged as not current. Paginates
+    the full table via LastEvaluatedKey — a plain single scan silently
+    truncates at ~1MB and would let flagged addresses past the truncation
+    point keep being suggested."""
     flagged = set()
     try:
-        resp = dynamodb.scan(
-            TableName=FLAGGED_TABLE,
-            ProjectionExpression="email",
-        )
-        for item in resp.get("Items", []):
-            email = item.get("email", {}).get("S", "")
-            if email:
-                flagged.add(email.lower())
+        exclusive_start_key = None
+        while True:
+            scan_kwargs = {
+                "TableName": FLAGGED_TABLE,
+                "ProjectionExpression": "email",
+            }
+            if exclusive_start_key:
+                scan_kwargs["ExclusiveStartKey"] = exclusive_start_key
+            resp = dynamodb.scan(**scan_kwargs)
+            for item in resp.get("Items", []):
+                email = item.get("email", {}).get("S", "")
+                if email:
+                    flagged.add(email.lower())
+            exclusive_start_key = resp.get("LastEvaluatedKey")
+            if not exclusive_start_key:
+                break
     except Exception as e:
         print(f"Flagged scan error: {e}")
     return flagged
 
 
 def get_bounced_emails():
     """Return set of emails that hard-bounced or triggered a spam complaint
     on a prior managed send, so they're excluded from future suggestions the
     same way a manually flagged 'Not current?' email is. Transient bounces
     (mailbox full, temporary server issue) are excluded from this set — those
-    are delivery hiccups, not evidence the official is no longer there."""
+    are delivery hiccups, not evidence the official is no longer there.
+    Paginates the full table via LastEvaluatedKey for the same reason as
+    get_flagged_emails() above."""
     bounced = set()
     try:
-        resp = dynamodb.scan(
-            TableName=BOUNCE_TABLE,
-            ProjectionExpression="email, event_type, #st",
-            ExpressionAttributeNames={"#st": "subtype"},  # "subtype" is a DynamoDB reserved word
-        )
-        for item in resp.get("Items", []):
-            email = item.get("email", {}).get("S", "")
-            event_type = item.get("event_type", {}).get("S", "")
-            subtype = item.get("subtype", {}).get("S", "")
-            if not email:
-                continue
-            if event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"):
-                bounced.add(email.lower())
+        exclusive_start_key = None
+        while True:
+            scan_kwargs = {
+                "TableName": BOUNCE_TABLE,
+                "ProjectionExpression": "email, event_type, #st",
+                "ExpressionAttributeNames": {"#st": "subtype"},  # "subtype" is a DynamoDB reserved word
+            }
+            if exclusive_start_key:
+                scan_kwargs["ExclusiveStartKey"] = exclusive_start_key
+            resp = dynamodb.scan(**scan_kwargs)
+            for item in resp.get("Items", []):
+                email = item.get("email", {}).get("S", "")
+                event_type = item.get("event_type", {}).get("S", "")
+                subtype = item.get("subtype", {}).get("S", "")
+                if not email:
+                    continue
+                if event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"):
+                    bounced.add(email.lower())
+            exclusive_start_key = resp.get("LastEvaluatedKey")
+            if not exclusive_start_key:
+                break
     except Exception as e:
         print(f"Bounced scan error: {e}")
     return bounced
 
 
 def get_verified_representative_emails(session_id):
     """Look up the officials we actually returned for this session during
     /generate. /send is restricted to this set so the endpoint can't be used
     as an open relay to arbitrary recipients — Function URLs have no built-in
     auth, so anyone who finds the endpoint could otherwise POST any address
     they want into the To/Cc fields of a mail sent from our verified domain.
     Returns None if the session can't be found (caller should reject)."""
     try:
         resp = dynamodb.get_item(
             TableName=DYNAMO_TABLE,
@@ -932,46 +982,92 @@ def already_sent(session_id):
 
 def build_single_salutation(rep):
     """Title-prefix + last name for one official, e.g. 'Mayor Smith' — the
     per-recipient counterpart to what used to be a single group salutation
     when one mailto/Gmail message went to all officials at once. Now that
     each official gets their own email, each one sees only their own name."""
     name = (rep.get("name") or "").strip()
     title = (rep.get("title") or "").strip()
     if not name:
         return title or "Official"
     last_name = name.split()[-1]
     title_prefix = title.split()[0] if title else ""
     return f"{title_prefix} {last_name}".strip() if title_prefix else last_name
 
 
-def log_send(session_id, constituent_email, location, representatives_sent, message_ids):
+def log_send(session_id, constituent_email, location, representatives_sent, message_ids, representatives_failed=None):
     """Log a managed-send event. 1-year TTL to match the retention already
     used for the rest of the take-action log (session, letter, reps) —
-    see the take-action privacy-policy note for why this needs disclosure."""
+    see the take-action privacy-policy note for why this needs disclosure.
+
+    Also copies a few fields from this session's /generate row (priorities,
+    source, location_city, location_state, and a representatives_offered
+    count) via a single get_item, so the sends row can be compared against
+    what was actually offered. source/location_city/location_state are new
+    generate-row attributes that a separate item is adding going forward —
+    existing generate rows (all 118 as of the Phase 1 baseline) don't have
+    them yet, so each is copied only if present; DynamoDB rejects an empty
+    S value, so an absent field is omitted entirely rather than written as
+    an empty string/list/map."""
     ttl = int(time.time()) + (365 * 24 * 60 * 60)
 
     item = {
         "session_id": {"S": session_id or str(uuid.uuid4())},
         "timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
         "constituent_email": {"S": constituent_email},
         "location": {"S": location},
         "representatives_sent": {"L": [{"S": e} for e in representatives_sent]},
         "message_ids": {"L": [{"S": m} for m in message_ids]},
+        "representatives_failed": {
+            "L": [
+                {"M": {"email": {"S": f["email"]}, "reason": {"S": f["reason"]}}}
+                for f in (representatives_failed or [])
+            ]
+        },
         "ttl": {"N": str(ttl)},
     }
 
+    try:
+        gen_resp = dynamodb.get_item(
+            TableName=DYNAMO_TABLE,
+            Key={"session_id": {"S": session_id}},
+        )
+        gen_item = gen_resp.get("Item")
+    except Exception as e:
+        print(f"Generate row lookup error for sends log: {e}")
+        gen_item = None
+
+    if gen_item:
+        priorities = gen_item.get("priorities", {}).get("L")
+        if priorities:
+            item["priorities"] = {"L": priorities}
+
+        source = gen_item.get("source", {}).get("M")
+        if source:
+            item["source"] = {"M": source}
+
+        location_city = gen_item.get("location_city", {}).get("S")
+        if location_city:
+            item["location_city"] = {"S": location_city}
+
+        location_state = gen_item.get("location_state", {}).get("S")
+        if location_state:
+            item["location_state"] = {"S": location_state}
+
+        representatives = gen_item.get("representatives", {}).get("L") or []
+        item["representatives_offered"] = {"N": str(len(representatives))}
+
     try:
         dynamodb.put_item(TableName=SEND_LOG_TABLE, Item=item)
     except Exception as e:
         print(f"Send log write error: {e}")
 
 
 def handle_send(body):
     """Handle POST /send — managed send via SES.
 
     Recipients are restricted to the officials verified during this session's
     /generate call (see get_verified_representative_emails) and a session can
     only be sent once (see already_sent) — both are abuse guards, since a
     Lambda Function URL has no built-in auth and would otherwise let anyone
     who finds the endpoint use our verified sending domain as an open relay.
     """
@@ -1000,104 +1096,131 @@ def handle_send(body):
 
     verified_reps = []
     for rep in representatives:
         if not isinstance(rep, dict):
             continue
         email = (rep.get("email") or "").strip()
         if is_valid_email(email) and email.lower() in verified_emails:
             verified_reps.append({
                 "email": email,
                 "name": sanitize_string(rep.get("name", ""), 200),
                 "title": sanitize_string(rep.get("title", ""), 200),
             })
     if not verified_reps:
         return respond(400, {"error": "No valid, verified representative email addresses to send to."})
 
+    # Suppression: an ADDITIONAL filter layered after the open-relay
+    # verification above, never a replacement for it — every rep here has
+    # already passed get_verified_representative_emails. This just stops a
+    # hard-bounced or user-flagged address from actually being mailed, even
+    # if it slipped past the /generate-time hard filter (e.g. a session
+    # generated before this address was flagged/bounced).
+    excluded = get_bounced_emails() | get_flagged_emails()
+    failed = []
+    to_send = []
+    for rep in verified_reps:
+        if rep["email"].lower() in excluded:
+            failed.append({"email": rep["email"], "reason": "suppressed"})
+        else:
+            to_send.append(rep)
+
     letter = letter.strip()[:20000]
     sender_name = constituent_name or "A Concerned Resident"
     subject = f"Street Lighting Improvement Request – {location}" if location else "Street Lighting Improvement Request"
 
     # One SES call per official (not one message with all officials in To) —
     # each gets their own message personalized with their own name, and a
     # bounce/complaint on one address never affects delivery to the others.
     sent = []
-    failed = []
-    for rep in verified_reps:
+    for rep in to_send:
         personalized_letter = letter.replace("[Representative Name]", build_single_salutation(rep))
         send_kwargs = {
             "FromEmailAddress": f'"{sender_name}" <{SES_SENDER_EMAIL}>',
             "Destination": {
                 "ToAddresses": [rep["email"]],
                 "CcAddresses": [constituent_email],
                 "BccAddresses": [SES_SENDER_EMAIL],
             },
             "ReplyToAddresses": [constituent_email],
             "Content": {
                 "Simple": {
                     "Subject": {"Data": subject, "Charset": "UTF-8"},
                     "Body": {"Text": {"Data": personalized_letter, "Charset": "UTF-8"}},
                 }
             },
         }
         if SES_CONFIGURATION_SET:
             send_kwargs["ConfigurationSetName"] = SES_CONFIGURATION_SET
 
         try:
             result = ses.send_email(**send_kwargs)
             sent.append({"email": rep["email"], "message_id": result.get("MessageId", "")})
         except Exception as e:
             print(f"SES send error for {rep['email']}: {e}")
-            failed.append(rep["email"])
+            failed.append({"email": rep["email"], "reason": "ses_error"})
 
     if not sent:
         return respond(502, {"error": "Failed to send email. Please try again or use the manual options below."})
 
     log_send(
         session_id=session_id,
         constituent_email=constituent_email,
         location=location,
         representatives_sent=[s["email"] for s in sent],
         message_ids=[s["message_id"] for s in sent],
+        representatives_failed=failed,
     )
 
     return respond(200, {
         "status": "sent",
         "sent_count": len(sent),
         "failed_count": len(failed),
+        "failed": failed,
     })
 
 
 def record_bounce_event(message, event_type):
     """Write one bounce/complaint event per affected recipient, keyed by the
     official's email address. get_bounced_emails() reads this table so a
     permanently-bounced or complained-about address stops being suggested,
     the same way a manually flagged 'Not current?' email does."""
     ttl = int(time.time()) + (180 * 24 * 60 * 60)
     timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
 
     if event_type == "Bounce":
         detail = message.get("bounce", {})
         recipients = [r.get("emailAddress", "") for r in detail.get("bouncedRecipients", [])]
         subtype = detail.get("bounceType", "")
     else:
         detail = message.get("complaint", {})
         recipients = [r.get("emailAddress", "") for r in detail.get("complainedRecipients", [])]
         subtype = detail.get("complaintFeedbackType", "")
 
+    sender_email_lower = SES_SENDER_EMAIL.lower()
     for email in recipients:
         if not email:
             continue
+        if email.lower() == sender_email_lower:
+            # Our own sender/reply-to address bouncing is not a signal about
+            # a discovered official's address — recording it here would pull
+            # take-action@photometrics.ai into get_bounced_emails() and start
+            # excluding it from things that check that set, plus it pollutes
+            # the bounce table with rows that were never a suggestable
+            # official in the first place (see p1-baseline-data-HANDOFF.md:
+            # 6 such self-bounce rows were already found in this table).
+            print(f"WARNING: bounce for sender address {email} — not recording")
+            continue
         try:
             dynamodb.put_item(
                 TableName=BOUNCE_TABLE,
                 Item={
                     "email": {"S": email.lower()},
                     "timestamp": {"S": timestamp},
                     "event_type": {"S": event_type},
                     "subtype": {"S": subtype},
                     "ttl": {"N": str(ttl)},
                 },
             )
         except Exception as e:
             print(f"Bounce log write error for {email}: {e}")
```

---

## New log lines added (exact strings)

1. `print(f"Hard filter dropped {n_dropped} excluded officials")` — in `handle_generate`, after applying `filter_excluded`. Printed on every `/generate` call, including when `n_dropped == 0`.
2. `print(f"WARNING: bounce for sender address {email} — not recording")` — in `record_bounce_event`, when the bouncing recipient equals `SES_SENDER_EMAIL` (case-insensitively).
3. `print(f"Generate row lookup error for sends log: {e}")` — in `log_send`, only on a `get_item` exception when fetching the generate row (does not abort the sends-row write; `gen_item` falls back to `None` and the copied fields are simply omitted).

No other new log lines were added.

---

## Commands run, with outcomes

- `git status --porcelain` (final, after reverting the pycache side effect noted under "Discovered") →
  ```
   M .dagflow/OPEN-QUESTIONS.md
   M .dagflow/PHASES.md
   M lambda/take-action/lambda_function.py
   M lambda/take-action/tools/README.md
   M lambda/take-action/tools/funnel_test.py
   M layouts/_default/take-action.html
  ?? .dagflow/phases/02-harden-instrument-report/
  ?? lambda/take-action/deploy.sh
  ?? lambda/take-action/tools/adgroups.json
  ?? lambda/take-action/tools/report.py
  ```
  `lambda/take-action/lambda_function.py` is the only file within this item's owned boundary and the only one this item modified. Every other entry (`.dagflow/OPEN-QUESTIONS.md`, `.dagflow/PHASES.md`, `layouts/_default/take-action.html`, `lambda/take-action/tools/README.md`, `lambda/take-action/tools/funnel_test.py`, `lambda/take-action/deploy.sh`, `lambda/take-action/tools/adgroups.json`, `lambda/take-action/tools/report.py`) is a sibling work item's concurrent change, not this item's; see "Discovered" below.
- `git diff --stat -- lambda/take-action/lambda_function.py` → `1 file changed, 151 insertions(+), 28 deletions(-)`.
- `git diff -U15 -- lambda/take-action/lambda_function.py` → full diff reproduced above; verified by eye against every acceptance criterion.
- `python -c "import ast;ast.parse(open(r'...lambda_function.py',encoding='utf-8').read());print('SYNTAX OK')"` → `SYNTAX OK`.
- `git diff -- lambda/take-action/lambda_function.py | grep -c 'LastEvaluatedKey'` → `4` (2 in `get_flagged_emails`'s added pagination code, 2 in `get_bounced_emails`'s — each function references the literal string `"LastEvaluatedKey"` once as a dict key and the diff shows it as an added `+` line).
- Open-relay/already_sent unchanged-body check (diffing `git show HEAD:...` against the working tree by regex-extracting each function body) → `get_verified_representative_emails UNCHANGED`, `already_sent UNCHANGED`.
- `filter_excluded` functional smoke test (module imported directly with dummy AWS creds, no network/AWS calls triggered by import):
  ```
  filter_excluded([{'email':'A@x.com','name':'a'},{'email':'b@x.com'},{'name':'no-email'}], {'a@x.com'})
  → [{'email': 'b@x.com'}, {'name': 'no-email'}]
  filter_excluded([{'email':'b@x.com'}], None)
  → [{'email': 'b@x.com'}]
  ```
  Confirms: case-insensitive match drops `A@x.com`, an official with no `email` key is kept, `excluded_emails=None` returns the input unchanged.
- `grep -n 'SES_SENDER_EMAIL' lambda_function.py` →
  ```
  34:SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "take-action@photometrics.ai")
  1137:            "FromEmailAddress": f'"{sender_name}" <{SES_SENDER_EMAIL}>',
  1141:                "BccAddresses": [SES_SENDER_EMAIL],
  1198:    sender_email_lower = SES_SENDER_EMAIL.lower()
  ```

No `/generate` call was made (0 of the phase's 2-call Anthropic budget used by this item). No email was sent. No `aws` CLI or boto3 call against a live AWS account was made — the only "AWS" call in the commands above is the local `filter_excluded` smoke test, which is a pure function and never reaches `boto3`/network (dummy credentials were only set as a precaution; nothing in the import path or `filter_excluded` itself performs I/O).

---

## Decisions / assumptions

- `filter_excluded`'s hard-log line in `handle_generate` prints unconditionally (including `n_dropped == 0`) rather than only when something was actually dropped — the acceptance criterion only requires the log line to exist and contain the count; printing unconditionally makes every `/generate` invocation's log self-describing without needing to infer from absence.
- In `log_send`, "field is absent" from the DATA CONTRACT's omission rule was implemented as "falsy" (missing key OR present-but-empty value) for `priorities`, `source`, `location_city`, `location_state` — not just "key literally missing." This is a superset of the literal requirement and is strictly safer: it guarantees no empty-`S`/empty-`M`/empty-`L` value is ever written for these four fields regardless of what shape a partially-populated generate row might have, without changing behavior for any row that actually has real values.
- `representatives_failed` is always written to the sends row (even as `{"L": []}` when nothing was suppressed/failed) rather than omitted when empty — unlike the four generate-row-derived fields, this one is not "copied from the generate row" and DynamoDB does not reject an empty `L` (only an empty `S`), so there's no reason to omit it; keeping it always-present makes it queryable/consistent across all future sends rows.
- The existing `if not sent: return respond(502, ...)` early-return in `handle_send` (when every rep was suppressed and/or every SES send failed) was left exactly as-is — it still returns before `log_send`/the 200 response are reached, so a fully-suppressed send never reaches the new `failed` list in a response body at all in that edge case. This matches the assignment's instruction to keep "whatever failed_count/other response fields already exist" and not otherwise touch that control-flow branch; it wasn't called out as something to change.

## Interface / contract downstream work must follow

- `log_send`'s new keyword parameter is `representatives_failed` (list of `{"email": str, "reason": str}` dicts, default `None`/treated as empty). Any future caller of `log_send` should pass this explicitly.
- The sends-row data contract now includes `priorities`, `source`, `location_city`, `location_state`, `representatives_offered`, `representatives_failed` as documented above — a report/analytics item reading this table should treat `priorities`/`source`/`location_city`/`location_state` as **optionally present** (absent on any sends row whose generate row predates the item that starts writing `source`/`location_city`/`location_state` onto generate rows, and also absent if that `get_item` call itself fails).
- `/send`'s 200 response body now has a `failed` array of `{email, reason}` with `reason` ∈ `{"suppressed", "ses_error"}` — any frontend/report consuming this response can now distinguish "we didn't even try" (suppressed) from "SES rejected it" (ses_error).
- `record_bounce_event` will no longer ever write a `photometrics-email-bounces` row for `SES_SENDER_EMAIL`. A future one-time cleanup could delete the 6 pre-existing self-bounce rows found in the Phase 1 baseline (`take-action@photometrics.ai`, all dated 2026-09-02) — this item did not delete them (no AWS write calls permitted), only stops new ones from being written going forward.

## Known limitations / risks

- `handle_send` now does two additional DynamoDB scans per call (`get_bounced_emails()` and `get_flagged_emails()`, each already-paginated) on top of the one already done for `already_sent`/`get_verified_representative_emails` — this adds latency to `/send` proportional to the size of the bounce/flagged tables (currently tiny: 14 and presumably-small rows respectively per the Phase 1 baseline). Not a correctness issue, but worth watching if either table grows large, since `Scan` cost/latency grows with table size regardless of how few rows match.
- `log_send` now also does one extra `get_item` per `/send` call to fetch the generate row. If that `get_item` fails, the function degrades gracefully (prints a warning, omits the four copied fields, still writes `representatives_failed`/existing fields) rather than failing the send — this was the safer choice per the assignment's emphasis on "if absent, omit" but means a transient DynamoDB blip on this specific read would silently produce an incomplete-but-valid sends row rather than surfacing an error.
- Pagination in `get_bounced_emails`/`get_flagged_emails` was not exercised against a real multi-page dataset in this item (no AWS calls were made, per the standing "no AWS write call... you should need none at all" instruction, which I read as covering reads too, given the DEFINITION OF DONE's verification commands never call AWS or run the Lambda live). The loop logic was reviewed by inspection (`ExclusiveStartKey` only added to `scan_kwargs` when truthy, loop breaks when `LastEvaluatedKey` is absent from the response) and mirrors the same pattern already proven working in `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md`'s `scan_all()` helper (paginator-based there, hand-rolled here to match the existing `dynamodb.scan(**kwargs)` call style already in the file), but has not been exercised against live DynamoDB.

## Discovered

- **Unrelated concurrent changes in the working tree, outside this item's ownership boundary.** A `git status --porcelain` taken immediately before starting this item's edits showed only `.dagflow/OPEN-QUESTIONS.md`, `.dagflow/PHASES.md` (modified) and the new `.dagflow/phases/02-harden-instrument-report/` directory (untracked) — no changes to `layouts/_default/take-action.html` or anything under `lambda/take-action/` besides `lambda_function.py`. By the time this item finished, `git status --porcelain` additionally showed `layouts/_default/take-action.html` modified, `lambda/take-action/tools/README.md` and `lambda/take-action/tools/funnel_test.py` modified, and three new untracked files (`lambda/take-action/deploy.sh`, `lambda/take-action/tools/adgroups.json`, `lambda/take-action/tools/report.py`) — none of which this item created or edited. These are almost certainly the output of a sibling work item running concurrently in this same phase's wave (per the DAG-based parallel-execution model this phase is run under) and are outside this item's owned boundary (`lambda/take-action/lambda_function.py` only), so they were left untouched. Flagging for the phase lead in case the verifier's `git status --porcelain` check for "nothing else outside .dagflow" is scoped to this item's own changes rather than the whole tree's state at verification time — if the latter, the lead will need to reconcile which item owns `deploy.sh`/`tools/*`/`take-action.html`.
- **Side effect caught and reverted:** the `filter_excluded` functional smoke test (`import lambda_function as lf`) regenerated the tracked bytecode cache file `lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` as an unavoidable interpreter side effect of importing the edited module. This was outside the owned boundary, so it was reverted with `git checkout -- lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` immediately after being noticed, before writing this handoff. Confirmed absent from the final `git status --porcelain`. Worth noting for future items in this phase that also need to `import lambda_function` for testing: expect the same side effect and revert it the same way, since it's currently a tracked file in this repo.

## Files changed

- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py` — see full diff above.
- `C:/Users/aisaa/Projects/photometricsai-website/.dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md` — this file (created).
- No other files were created, edited, or deleted by this item.
