#!/usr/bin/env python3
"""
report.py - Take Action attribution report.

Answers, in one command: "which ad group, keyword, priority and city
actually produced letters and sends" by joining the two Take Action
DynamoDB tables (photometrics-take-action + photometrics-take-action-sends)
on session_id and cutting the result by ad group / keyword / top priority /
location, and separately by priority / state.

READ-ONLY. Issues only dynamodb:Scan calls, paginated via LastEvaluatedKey.
Makes no DynamoDB write calls of any kind.
Never prints a constituent_email or a letter body.

Built against the fixed data contract (source.utm_content / utm_term,
location_city / location_state / location_country on the generate table;
priorities / source / location_city / location_state /
representatives_offered / representatives_failed on the sends table) before
any row actually carries those attributes, so it is ready the moment
attributed rows start arriving. Today, with zero rows carrying `source` or
`location_city`, every row is expected to bucket as ad group
'pre-attribution' with the raw `location` string used verbatim.

Usage:
    python report.py                  # markdown report to stdout
    python report.py --out ./out_dir  # also writes cut1.csv, cut2.csv,
                                       # totals.csv into out_dir

Requires: boto3, AWS credentials for account 794038225197, region us-east-2.
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

import boto3
from boto3.dynamodb.types import TypeDeserializer

REGION = "us-east-2"
GEN_TABLE = "photometrics-take-action"
SENDS_TABLE = "photometrics-take-action-sends"
BOUNCE_TABLE = "photometrics-email-bounces"
ADGROUPS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adgroups.json")

_deser = TypeDeserializer()

# Lightweight best-effort state extraction from a messy raw `location`
# string, used ONLY as the Cut 2 fallback when location_state is absent
# (per assignment: "state (from location_state, else parsed/blank)"). This
# is not authoritative - it is a word-boundary match against known USPS
# abbreviations and full state names, and returns blank when nothing
# matches. Zip codes and city-only strings (the bulk of current production
# data) will parse to blank, which is expected and documented in the
# handoff as a known limitation.
_STATE_ABBR = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}
_STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}
_STATE_NAME_RE = re.compile(
    r"\b(" + "|".join(sorted(_STATE_NAMES.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def parse_state_from_raw(raw):
    """Best-effort state guess from a raw `location` string. Returns '' if
    nothing recognizable is found. Never raises."""
    if not raw:
        return ""
    text = raw.strip()
    # Try full state names first (more specific match).
    m = _STATE_NAME_RE.search(text)
    if m:
        return _STATE_NAMES[m.group(1).lower()]
    # Try a bare 2-letter USPS abbreviation as its own token.
    for tok in re.split(r"[\s,]+", text):
        tok_clean = tok.strip(".").upper()
        if tok_clean in _STATE_ABBR:
            return tok_clean
    return ""


def item_to_py(item):
    """Deserialize a raw DynamoDB item (AttributeValue dicts) into native
    Python types (str / Decimal / list / dict / bool / None)."""
    return {k: _deser.deserialize(v) for k, v in item.items()}


def scan_all(ddb, table_name, projection_expression=None, expr_attr_names=None):
    """Fully paginated read-only Scan. Returns a list of native-Python dicts."""
    paginator = ddb.get_paginator("scan")
    kwargs = {"TableName": table_name}
    if projection_expression:
        kwargs["ProjectionExpression"] = projection_expression
    if expr_attr_names:
        kwargs["ExpressionAttributeNames"] = expr_attr_names
    items = []
    for page in paginator.paginate(**kwargs):
        for raw in page.get("Items", []):
            items.append(item_to_py(raw))
    return items


def is_test_row(row):
    return str(row.get("session_id", "")).startswith("test-")


def load_adgroups_map():
    with open(ADGROUPS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k != "_note"}


def resolve_ad_group(source, adgroups_map):
    if not source or not isinstance(source, dict):
        return "pre-attribution"
    utm_content = source.get("utm_content")
    if not utm_content:
        return "pre-attribution"
    return adgroups_map.get(utm_content, utm_content)


def resolve_keyword(source):
    if not source or not isinstance(source, dict):
        return ""
    return source.get("utm_term") or ""


def resolve_top_priority(priorities):
    if isinstance(priorities, list) and priorities:
        return priorities[0] or ""
    return ""


def resolve_location_display(row):
    city = row.get("location_city") or ""
    state = row.get("location_state") or ""
    if city or state:
        parts = [p for p in (city, state) if p]
        return ", ".join(parts)
    return row.get("location") or ""


def is_hard_bounce(event_type, subtype):
    """Per contract: hard bounce = (Bounce AND Permanent) OR Complaint."""
    if event_type == "Complaint":
        return True
    if event_type == "Bounce" and subtype == "Permanent":
        return True
    return False


def new_metrics():
    return {
        "generated": 0,
        "sent_sessions": 0,
        "reps_emailed": 0,
        "suppressed": 0,
        "hard_bounces": 0,
    }


def build_report(ddb, adgroups_map):
    # ---------- Scan photometrics-take-action (generate rows) ----------
    # Never projects `letter`. `location` and `source` are DynamoDB
    # reserved words, so both are aliased.
    gen_proj = "session_id, priorities, #src, #loc, location_city, location_state, location_country"
    gen_names = {"#src": "source", "#loc": "location"}
    gen_raw = scan_all(ddb, GEN_TABLE, gen_proj, gen_names)
    gen_rows = [r for r in gen_raw if not is_test_row(r)]

    # ---------- Scan photometrics-take-action-sends ----------
    # Only what's needed for the metrics below: whether a send happened,
    # who it reached, and who was suppressed/failed. No constituent_email,
    # no message_ids.
    sends_proj = "session_id, representatives_sent, representatives_failed"
    sends_raw = scan_all(ddb, SENDS_TABLE, sends_proj)
    sends_rows = [r for r in sends_raw if not is_test_row(r)]
    sends_by_session = {r.get("session_id"): r for r in sends_rows if r.get("session_id")}

    # ---------- Scan photometrics-email-bounces ----------
    bounce_proj = "email, event_type, #st"
    bounce_names = {"#st": "subtype"}
    bounce_raw = scan_all(ddb, BOUNCE_TABLE, bounce_proj, bounce_names)
    hard_bounced_emails = set()
    for b in bounce_raw:
        email = (b.get("email") or "").strip().lower()
        if email and is_hard_bounce(b.get("event_type"), b.get("subtype")):
            hard_bounced_emails.add(email)

    cut1 = collections.OrderedDict()  # key -> metrics
    cut2 = collections.OrderedDict()
    totals = new_metrics()

    for row in gen_rows:
        session_id = row.get("session_id")
        source = row.get("source")
        priorities = row.get("priorities")

        ad_group = resolve_ad_group(source, adgroups_map)
        keyword = resolve_keyword(source)
        top_priority = resolve_top_priority(priorities)
        location_display = resolve_location_display(row)

        send_row = sends_by_session.get(session_id)
        reps_sent = []
        reps_failed = []
        if send_row:
            reps_sent = send_row.get("representatives_sent") or []
            reps_failed = send_row.get("representatives_failed") or []

        suppressed_count = sum(
            1 for f in reps_failed
            if isinstance(f, dict) and f.get("reason") == "suppressed"
        )
        hard_bounce_count = sum(
            1 for e in reps_sent
            if isinstance(e, str) and e.strip().lower() in hard_bounced_emails
        )

        # ---- Cut 1: ad group x keyword x top priority x location ----
        key1 = (ad_group, keyword, top_priority, location_display)
        m1 = cut1.setdefault(key1, new_metrics())
        m1["generated"] += 1
        if send_row:
            m1["sent_sessions"] += 1
            m1["reps_emailed"] += len(reps_sent)
        m1["suppressed"] += suppressed_count
        m1["hard_bounces"] += hard_bounce_count

        # ---- Cut 2: priority x state ----
        state = row.get("location_state") or parse_state_from_raw(row.get("location"))
        key2 = (top_priority, state)
        m2 = cut2.setdefault(key2, new_metrics())
        m2["generated"] += 1
        if send_row:
            m2["sent_sessions"] += 1
            m2["reps_emailed"] += len(reps_sent)
        m2["suppressed"] += suppressed_count
        m2["hard_bounces"] += hard_bounce_count

        # ---- Totals ----
        totals["generated"] += 1
        if send_row:
            totals["sent_sessions"] += 1
            totals["reps_emailed"] += len(reps_sent)
        totals["suppressed"] += suppressed_count
        totals["hard_bounces"] += hard_bounce_count

    counts = {
        "gen_raw_scanned": len(gen_raw),
        "gen_test_excluded": len(gen_raw) - len(gen_rows),
        "gen_counted": len(gen_rows),
        "sends_raw_scanned": len(sends_raw),
        "sends_test_excluded": len(sends_raw) - len(sends_rows),
        "sends_counted": len(sends_rows),
        "bounce_raw_scanned": len(bounce_raw),
    }

    return cut1, cut2, totals, counts


def fmt_cell(v):
    if v is None or v == "":
        return "(blank)"
    return str(v)


CUT1_HEADER = ["ad_group", "keyword", "top_priority", "location", "generated", "sent_sessions", "reps_emailed", "suppressed", "hard_bounces"]
CUT2_HEADER = ["top_priority", "state", "generated", "sent_sessions", "reps_emailed", "suppressed", "hard_bounces"]


def cut1_rows(cut1):
    rows = []
    for (ad_group, keyword, top_priority, location), m in cut1.items():
        rows.append([ad_group, keyword, top_priority, location, m["generated"], m["sent_sessions"], m["reps_emailed"], m["suppressed"], m["hard_bounces"]])
    rows.sort(key=lambda r: (-r[4], r[0], r[1], r[2], r[3]))
    return rows


def cut2_rows(cut2):
    rows = []
    for (top_priority, state), m in cut2.items():
        rows.append([top_priority, state, m["generated"], m["sent_sessions"], m["reps_emailed"], m["suppressed"], m["hard_bounces"]])
    rows.sort(key=lambda r: (-r[2], r[0], r[1]))
    return rows


def print_markdown_table(header, rows):
    display_header = [h.replace("_", " ") for h in header]
    print("| " + " | ".join(display_header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        cells = [fmt_cell(c) for c in r]
        print("| " + " | ".join(cells) + " |")


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([("" if c in (None, "") else c) for c in r])


def main():
    parser = argparse.ArgumentParser(description="Take Action attribution report (read-only).")
    parser.add_argument("--out", metavar="DIR", help="directory to write per-cut CSV files into")
    args = parser.parse_args()

    ddb = boto3.client("dynamodb", region_name=REGION)
    adgroups_map = load_adgroups_map()

    cut1, cut2, totals, counts = build_report(ddb, adgroups_map)
    r1 = cut1_rows(cut1)
    r2 = cut2_rows(cut2)

    print("# Take Action Attribution Report\n")
    print(
        f"Scanned: generate table {counts['gen_raw_scanned']} raw "
        f"({counts['gen_test_excluded']} test- excluded, "
        f"{counts['gen_counted']} counted); sends table "
        f"{counts['sends_raw_scanned']} raw "
        f"({counts['sends_test_excluded']} test- excluded, "
        f"{counts['sends_counted']} counted); bounce table "
        f"{counts['bounce_raw_scanned']} raw rows.\n"
    )

    print("## Cut 1 - Ad Group x Keyword x Top Priority x Location\n")
    print_markdown_table(CUT1_HEADER, r1)

    print("\n## Cut 2 - Top Priority x State\n")
    print_markdown_table(CUT2_HEADER, r2)

    print("\n## Totals\n")
    print("| generated | sent sessions | reps emailed | suppressed | hard bounces |")
    print("|---|---|---|---|---|")
    print(
        f"| {totals['generated']} | {totals['sent_sessions']} | "
        f"{totals['reps_emailed']} | {totals['suppressed']} | "
        f"{totals['hard_bounces']} |"
    )

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        write_csv(os.path.join(args.out, "cut1.csv"), CUT1_HEADER, r1)
        write_csv(os.path.join(args.out, "cut2.csv"), CUT2_HEADER, r2)
        write_csv(
            os.path.join(args.out, "totals.csv"),
            ["generated", "sent_sessions", "reps_emailed", "suppressed", "hard_bounces"],
            [[totals["generated"], totals["sent_sessions"], totals["reps_emailed"], totals["suppressed"], totals["hard_bounces"]]],
        )
        print(f"\nCSV files written to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
