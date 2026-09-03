# funnel_test.py — Take Action funnel test harness

A self-contained boto3 CLI that exercises the Photometrics AI "Take Action"
managed-send path end to end — seed → send → bounce → exclusion → cleanup —
against the live Lambda function `photometrics-take-action` (region
`us-east-2`, account `794038225197`), using **only SES mailbox-simulator
addresses**. It gives this phase (and any later re-test) a repeatable,
non-interactive way to prove the send/bounce/exclusion funnel actually
works, without risking a real inbox and without spending Anthropic tokens.

## Safety rules

1. **No real inbox other than the configured `--cc-email` may ever receive
   mail from this tool.** All representative addresses are hardcoded to SES
   mailbox-simulator addresses:
   - `success@simulator.amazonses.com` — always delivers
   - `bounce@simulator.amazonses.com` — always hard-bounces (Permanent)
   - `success+deselected@simulator.amazonses.com` — delivers, but is never
     included in a `/send` request. It exists to prove `/send` only mails
     the recipients actually present in the request body, not every rep
     ever associated with the session.
   - `dead.official@simulator.amazonses.com` — never actually mailed. It is
     seeded as a prior Permanent bounce (and as a boosted/trusted official)
     so `check-regenerate` can prove `/send` refuses to mail it at all.
2. **This tool never calls `/generate`.** It writes the seeded session row(s)
   directly into DynamoDB (mirroring what `/generate` would have written)
   and only ever invokes `/send`. Zero Anthropic tokens spent.
3. **Every row this tool creates uses a `session_id` prefixed `test-`** and
   is deleted by `cleanup` (run automatically at the end of `all`, unless
   `--keep` is passed).
4. `/send` is invoked via the **AWS Lambda `Invoke` API** with a synthetic
   Function-URL event — never over HTTPS, and never through the real
   Function URL.

## Usage

```bash
# Verify boto3 is importable first
python -c "import boto3; print(boto3.__version__)"

# See all options
python funnel_test.py --help

# Full funnel run against live AWS (seed -> send -> wait-bounce ->
# check-sends -> check-exclusion -> check-regenerate -> cleanup)
python funnel_test.py all

# Same, but leave the test rows in place for manual inspection
python funnel_test.py all --keep

# Dry run: prints every intended AWS action, makes ZERO AWS calls, exits 0
# (works even with no/bogus AWS credentials in the environment)
python funnel_test.py --dry-run all

# Run subcommands individually, in separate shell invocations — state
# (session_id, seeded letter, edit marker, timestamps) is persisted between
# them in .funnel_test_state.json next to this script
python funnel_test.py seed
python funnel_test.py send
python funnel_test.py wait-bounce
python funnel_test.py check-sends
python funnel_test.py check-exclusion
python funnel_test.py check-regenerate
python funnel_test.py cleanup
```

`check-regenerate` is fully self-contained — it seeds its own dedicated
`test-regen-<unixts>` session and doesn't depend on `seed`/`send` having run
first, so it can also be run entirely on its own:

```bash
python funnel_test.py check-regenerate
python funnel_test.py cleanup
```

### Global flags

| Flag | Default | Meaning |
|---|---|---|
| `--dry-run` | off | Print every intended AWS action, make zero AWS calls, exit 0. Never constructs a live boto3 client — safe even with bogus credentials. |
| `--keep` | off | For `all`: skip the final `cleanup` step. |
| `--cc-email` | `ari@sdgis.com` | Constituent CC address used in `/send` and checked by `check-sends`. The only non-simulator address this tool will ever use. |
| `--region` | `us-east-2` | AWS region for all clients. |

### Subcommands

- **`seed`** — `put_item`s a synthetic session row into
  `photometrics-take-action`, matching `log_generation()`'s shape in
  `lambda_function.py` exactly (`session_id`, `timestamp`, `location`,
  `priorities`, `letter`, `representatives`, `actions`, `ttl`, `name`), plus
  the new attribution/location contract fields:
  - `source` (M) — the UTM/attribution contract keys (`utm_source`,
    `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `utm_match`,
    `gclid`, `landed_priorities`, `referrer`), seeded with recognizable
    test values (`utm_source='google'`, `utm_campaign='TESTCAMP'`,
    `gclid='TESTGCLID'`, etc. — see `SOURCE_FIELDS` in the script).
  - `location_city='Austin'`, `location_state='TX'`,
    `location_country='US'` — normalized location, top-level S attributes.

  `session_id = "test-<unixts>"`, `location = "Austin, TX"`,
  `priorities = ["Transportation Safety"]`, `ttl` is 1 day (not the 1-year
  production value). The letter contains the literal `[Representative
  Name]` placeholder. Seeds all three representatives above, in order.
- **`send`** — builds the `/send` request body (only the first two seeded
  reps — the deselected one is intentionally omitted), appends an
  `EDIT-MARKER <timestamp>` sentence to the seeded letter (proving the
  letter text actually sent is the one in the request body, i.e. what the
  user edited client-side, not whatever was stored during seeding), and
  invokes the Lambda via `lambda.invoke()` with a synthetic Function-URL
  event. Asserts `statusCode == 200`, `sent_count == 2`, `failed_count == 0`.
- **`wait-bounce`** — polls `photometrics-email-bounces` every 5s for up to
  150s until a row appears for `bounce@simulator.amazonses.com` with
  `event_type == "Bounce"` and `subtype == "Permanent"`. Prints each poll
  attempt. Non-zero exit on timeout.
- **`check-sends`** — `get_item`s `photometrics-take-action-sends` for the
  test session and asserts `representatives_sent` is exactly the two sent
  addresses (deselected address confirmed absent), `len(message_ids) == 2`,
  and `constituent_email` matches `--cc-email`. Prints the full row.
- **`check-exclusion`** — re-implements `get_bounced_emails()`'s semantics
  from `lambda_function.py` (include an email when `event_type ==
  "Complaint"` OR `(event_type == "Bounce" AND subtype == "Permanent")`),
  but with a **paginated** scan (the production function does a single
  non-paginated scan). Asserts `bounce@simulator.amazonses.com` is in the
  resulting set and prints the full set.
- **`check-regenerate`** — proves a hard-bounced address is refused at
  `/send` time (reason `'suppressed'`) instead of being re-mailed. Fully
  self-contained: it seeds its own dedicated `test-regen-<unixts>` session,
  independent of whatever `seed`/`send` left in state, so it works whether
  run inside `all` or entirely on its own.
  1. Seeds a Permanent bounce row for `dead.official@simulator.amazonses.com`
     into `photometrics-email-bounces` (`event_type='Bounce'`,
     `subtype='Permanent'`), shaped like the rows `record_bounce_event()`
     writes.
  2. Seeds a matching row into `photometrics-boosted-officials` for region
     `'Austin, TX'` (key schema `region` HASH + `email` RANGE, confirmed via
     `aws dynamodb describe-table`) — proving suppression wins even over a
     "boosted"/trusted official, not just an address `/send` has never seen.
  3. Seeds a fresh generate row (with the new `source`/`location_city`
     fields) whose `representatives` list includes both
     `success@simulator.amazonses.com` and
     `dead.official@simulator.amazonses.com`, so the dead address passes the
     `/send` open-relay guard (which only allows addresses stored on the
     session's generate row).
  4. Invokes `/send` (via the Lambda Invoke API, exactly like `send`) with a
     request body listing both representatives.
  5. Asserts: the response reports `failed_count == 1` and a `failed` entry
     `{email: 'dead.official@simulator.amazonses.com', reason: 'suppressed'}`;
     `sent_count == 1`; the dead address is **not** in the sends row's
     `representatives_sent`; the sends row's `representatives_failed`
     contains the suppressed entry; and the sends row also carries
     `representatives_offered == 2`, `priorities`, `source`, and
     `location_city` matching what was seeded. Exits non-zero (via
     `FunnelTestError`) on any assertion failure.
  6. `dead.official@simulator.amazonses.com` is never actually mailed by
     SES — that's the entire point of the assertion.
- **`cleanup`** — deletes the main test session row and sends row, the
  `check-regenerate` session row and sends row (if any), the
  `check-regenerate` boosted-officials row (deterministic
  `region='Austin, TX'`/`email='dead.official@simulator.amazonses.com'`
  key — safe to target unconditionally since delete_item on a missing key
  is a no-op), and every row in the bounce table whose email ends with
  `@simulator.amazonses.com` (this also covers the
  `dead.official@simulator.amazonses.com` bounce row `check-regenerate`
  seeds — no separate code path needed for it). Discovers the bounce
  table's key schema via `describe_table` at runtime (it may be a single
  partition key or a composite partition+sort key — never assumed) and
  builds delete keys from the actual schema. Prints every key deleted,
  then clears the state file.
- **`all`** — runs `seed -> send -> wait-bounce -> check-sends ->
  check-exclusion -> check-regenerate -> cleanup`, stopping at the first
  failure but always attempting cleanup afterwards unless `--keep` was
  passed.

## State file

`lambda/take-action/tools/.funnel_test_state.json` (git-ignored) holds the
current test `session_id`, the `check-regenerate` session's `regen_session_id`,
the seeded letter text, the seed/send timestamps, the `EDIT-MARKER` string,
and the `--cc-email` used for `send`, so each subcommand can be run
independently in its own shell invocation. `cleanup` clears it.

## Notes for operators

- Under Git Bash on Windows, prefix any `aws logs` command with
  `MSYS_NO_PATHCONV=1` (otherwise `/aws/lambda/...` gets path-mangled), and
  set `AWS_PAGER=''` for AWS CLI calls.
- This harness only ever touches `photometrics-take-action`,
  `photometrics-take-action-sends`, `photometrics-email-bounces`, and (for
  `check-regenerate`/`cleanup` only) `photometrics-boosted-officials`, all in
  `us-east-2`. It never modifies `lambda_function.py`, Lambda configuration,
  IAM, Google Ads, GA4, or Google Workspace.
- **`/generate` is still never called by any subcommand**, including
  `check-regenerate` — despite the name, it only ever seeds DynamoDB rows
  directly (as `/generate` would have written them) and invokes `/send`.
  Zero Anthropic tokens spent.
