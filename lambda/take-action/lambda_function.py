"""
Photometrics AI - Take Action Lambda
Generates personalized letters and finds relevant representatives using Claude API.
Two routes: POST /generate (AI letter) and POST /track (click tracking).
"""

import json
import os
import uuid
import time
import urllib.request
import urllib.parse
import urllib.error
import re
import concurrent.futures

import boto3
from boto3.dynamodb.types import TypeSerializer

DYNAMO_TABLE = os.environ.get("DYNAMODB_TABLE", "photometrics-take-action")
BOOSTED_TABLE = os.environ.get("BOOSTED_TABLE", "photometrics-boosted-officials")
FLAGGED_TABLE = os.environ.get("FLAGGED_TABLE", "photometrics-flagged-officials")
SEND_LOG_TABLE = os.environ.get("SEND_LOG_TABLE", "photometrics-take-action-sends")
BOUNCE_TABLE = os.environ.get("BOUNCE_TABLE", "photometrics-email-bounces")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_CIVIC_API_KEY = os.environ.get("GOOGLE_CIVIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-5"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Managed send (SES) — see handle_send() below for why this is gated off in
# production until the SES use-case update is approved. SES_CONFIGURATION_SET
# is intentionally blank until that configuration set exists; sends work
# without one, just without bounce/complaint event tracking.
SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "take-action@photometrics.ai")
SES_CONFIGURATION_SET = os.environ.get("SES_CONFIGURATION_SET", "")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PRIORITY_URLS = {
    "Crime & Safety": "https://www.photometrics.ai/best-practices/public-safety/",
    "Transportation Safety": "https://www.photometrics.ai/best-practices/transportation-safety/",
    "Migratory Birds": "https://www.photometrics.ai/best-practices/birds/",
    "Energy Waste": "https://www.photometrics.ai/best-practices/utilities/",
    "Light Pollution": "https://www.photometrics.ai/best-practices/dark-sky/",
    "Environmental Impact": "https://www.photometrics.ai/best-practices/",
}
BEST_PRACTICES_DEFAULT = "https://www.photometrics.ai/best-practices/"

PRODUCT_CONTEXT = """
THE PROBLEM (THE GAP):
Street lighting today is trapped in a false binary: more light (for safety) vs. less light (for the environment). This is a false choice. The real answer is precision -- delivering exactly the light needed for safety, nothing more. Municipalities over-light to avoid political risk. Advocates demand lights-off because they have no other lever. Both sides lose. The technology to resolve this impasse exists now.

Human eyes cannot perceive brightness changes under 20% at night. Most street lighting operates far above what safety standards require. The over-illumination being removed was never perceptible in the first place.

THE BRIDGE (PHOTOMETRICS AI):
Photometrics AI is a software-only platform that works with existing networked lighting controls -- no new hardware, no infrastructure changes. It designs lighting levels for each individual luminaire based on published safety standards (IES RP-8), road classification, and real-time conditions. The system replaces static, worst-case lighting with precision engineering that adapts. The core principle: right light, right place, right time.

A strict priority hierarchy ensures safety is never compromised: dispatch response > demand response > transportation safety > crime prevention > special events > migratory birds > default schedule. The system cannot dim for energy savings or conservation when an active safety need exists.

Energy savings compound: 25% from precision design (eliminating over-illumination) + 50% early-morning dimming (when standards permit lower levels) = 35% overall reduction.

PRIORITY-SPECIFIC FACTS:

Crime & Safety: LAPD data shows 39% crime reduction with improved lighting. "Improved" means properly designed -- better uniformity and appropriate levels -- not simply brighter. Over-illumination creates harsh shadows and glare that reduce visibility. Precision design produces lighting that actually deters crime. The priority hierarchy hardcodes safety above all other objectives.

Transportation Safety: FHWA documents 28-42% crash reduction potential with proper roadway lighting (varies by road type: intersection, midblock, interchange). Static lighting ignores weather and traffic changes. Precision design adjusts for rain, fog, and wet pavement -- conditions that change visibility requirements. RP-8 defines different lighting levels for different conditions; Photometrics AI applies them dynamically.

Migratory Birds: Photometrics AI has a recognized partnership with Cornell Lab of Ornithology, integrating BirdCast migration forecasts directly into lighting schedules. Cornell has published about this collaboration: https://www.birds.cornell.edu/home/photometrics-ai-uses-bird-data-to-adjust-streetlights/ . The system dims lights only on high-migration nights (approximately 20 or fewer per year). Minimal impact on other priorities. The priority hierarchy ensures transportation safety and crime prevention always take precedence over bird migration dimming. When migratory birds is selected, the letter MUST include the full Cornell URL as plain text.

Light Pollution: Eliminates unnecessary over-illumination that contributes to skyglow. Precision design delivers light where it is needed and reduces it where it is not. Every luminaire can follow a different schedule based on its location and surroundings.

Energy Waste: 35% overall energy savings through precision design. Benefits extend beyond energy to include extended luminaire life, reduced maintenance, and avoided utility costs — significant cost savings where the benefits easily outweigh the costs. Do NOT cite specific dollar-per-light values or annual totals in the letter — a citizen would not know these figures. The 35% energy savings figure is publicly citable.

Environmental Impact: Reduces light pollution, energy consumption, and ecological disruption simultaneously. BirdCast integration protects migratory birds. Precision dimming reduces the carbon footprint of street lighting without compromising any safety standard.

THE ASK:
Ask the official to evaluate Photometrics AI as a solution for their community and to reach out to the company directly to learn more. Do not mention pricing, pilot scope, number of luminaires, or dollar amounts — a citizen would not know these details. The ask should feel like a concerned resident pointing their representative toward a technology worth investigating, not a sales pitch.
"""

dynamodb = boto3.client("dynamodb")
ses = boto3.client("sesv2")
serializer = TypeSerializer()

# Response headers (CORS handled by Lambda Function URL config)
CORS_HEADERS = {
    "Content-Type": "application/json",
}


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def sanitize_string(value, max_len):
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def is_valid_email(value):
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
        for item in resp.get("Items", []):
            actions = item.get("actions", {}).get("L", [])
            sent_emails = set()
            for action in actions:
                m = action.get("M", {})
                evt = m.get("event", {}).get("S", "")
                email = m.get("rep_email", {}).get("S", "")
                if evt in ("click_mailto", "click_gmail") and email:
                    sent_emails.add(email)

            if sent_emails:
                reps = item.get("representatives", {}).get("L", [])
                for rep_item in reps:
                    rep = rep_item.get("M", {})
                    email = rep.get("email", {}).get("S", "")
                    if email in sent_emails:
                        if email not in boosted:
                            boosted[email] = {
                                "name": rep.get("name", {}).get("S", ""),
                                "title": rep.get("title", {}).get("S", ""),
                                "organization": rep.get("organization", {}).get("S", ""),
                                "email": email,
                                "send_count": 0,
                                "source": "auto",
                            }
                        boosted[email]["send_count"] += 1
    except Exception as e:
        print(f"Auto-boost query error: {e}")

    # 2) Manual boost: query boosted-officials table
    try:
        resp = dynamodb.query(
            TableName=BOOSTED_TABLE,
            KeyConditionExpression="#r = :r",
            ExpressionAttributeNames={"#r": "region"},
            ExpressionAttributeValues={":r": {"S": location}},
        )
        for item in resp.get("Items", []):
            email = item.get("email", {}).get("S", "")
            if email and email not in boosted:
                boosted[email] = {
                    "name": item.get("name", {}).get("S", ""),
                    "title": item.get("title", {}).get("S", ""),
                    "organization": item.get("organization", {}).get("S", ""),
                    "email": email,
                    "reason": item.get("reason", {}).get("S", ""),
                    "source": "manual",
                }
    except Exception as e:
        print(f"Manual boost query error: {e}")

    return list(boosted.values())


def get_civic_officials(location):
    """Placeholder — Google Civic API representatives endpoint was sunset.
    Returns empty list. Haiku web search handles all official lookups."""
    return []


def parse_location(location):
    """Parse a location string into city and region components."""
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else location
    region = parts[1] if len(parts) > 1 else ""
    return city, region


def search_officials(location, priorities, civic_officials=None, boosted_officials=None, excluded_emails=None):
    """Use Haiku + web search to find verified current officials."""
    priorities_text = ", ".join(priorities)
    city, region = parse_location(location)

    flagged_section = ""
    if excluded_emails:
        flagged_section = (
            "\n\nEXCLUDED EMAILS (reported no longer current, or bounced/complained on a prior send — do NOT use them):\n"
            + "\n".join(f"- {e}" for e in excluded_emails)
        )

    civic_section = ""
    if civic_officials:
        lines = [
            f"- {o['name']}, {o['title']}" + (f" ({o['email']})" if o.get("email") else "")
            for o in civic_officials
        ]
        civic_section = (
            "\n\nVERIFIED ELECTED OFFICIALS (confirmed current via government records):\n"
            + "\n".join(lines)
            + "\nYou may include relevant ones. Their names/titles are verified."
            + " Search for email addresses if missing."
        )

    boosted_section = ""
    if boosted_officials:
        lines = []
        for o in boosted_officials:
            if o.get("source") == "auto":
                count = o.get("send_count", 1)
                detail = f"received {count} letter(s) previously"
            else:
                detail = f"flagged as receptive: {o.get('reason', '')}"
            lines.append(f"- {o['name']}, {o['title']}, {o['organization']} ({detail})")
        boosted_section = (
            "\n\nPREFERRED OFFICIALS (soft suggestion, not required):\n"
            + "\n".join(lines)
            + "\nIf these people are still current and relevant, consider including them."
        )

    prompt = f"""Find exactly 4 government officials who influence street lighting decisions
relevant to {location}. The citizen's priorities are: {priorities_text}.
{civic_section}{boosted_section}{flagged_section}

INSTRUCTIONS:
1. Use web search to find CURRENT officials. Check official city/county/state/federal websites,
   staff directories, and government contact pages.
2. For each official, find their contact email. Acceptable email sources (in order of preference):
   a) Personal official email from a .gov staff directory (e.g. jane.doe@sandiego.gov)
   b) Department or office email from the official website (e.g. publicworks@sandiego.gov)
   c) General contact email for their office (e.g. citycouncil@sandiego.gov)
   NEVER invent or guess an email. Every email must come from a web search result.
3. You MUST include officials from MULTIPLE LEVELS of government. The 4 slots should span:
   - 1 LOCAL official: mayor, city council member, or county supervisor
   - 1 LOCAL department head: public works director, transportation director, or city engineer
     (the person with direct operational authority over street lighting)
   - 1 STATE-LEVEL official or agency head whose portfolio matches the citizen's priorities.
     Examples by state:
     California: CA Energy Commission (CEC), CA Public Utilities Commission (CPUC), Caltrans
     Texas: Public Utility Commission of Texas (PUCT), ERCOT, TxDOT
     New York: NY Public Service Commission, NYSERDA, NYSDOT
     Other states: the equivalent energy, utility, or transportation regulator
   - 1 additional official at ANY level whose portfolio best matches the citizen's priorities:
     energy waste -> utility regulator, grid operator, sustainability office
     crime/safety -> police chief, public safety director
     migratory birds/environment -> state fish & wildlife, environmental affairs
     transportation safety -> state DOT district engineer, traffic safety
     light pollution -> planning commission, dark sky program
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

    tool_def = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
    }
    if city and region:
        tool_def["user_location"] = {
            "type": "approximate",
            "city": city,
            "region": region,
            "country": "US",
        }

    request_body = json.dumps({
        "model": HAIKU_MODEL,
        "max_tokens": 4096,
        "tools": [tool_def],
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I'll search for current officials now."},
            {"role": "user", "content": "Go ahead. Remember: output ONLY the JSON array when done. No commentary."},
        ],
    })

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=request_body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Haiku search API error {e.code}: {error_body}")

    # Debug: log response structure
    stop_reason = result.get("stop_reason", "unknown")
    block_types = [b.get("type") for b in result.get("content", [])]
    print(f"Haiku response: stop_reason={stop_reason}, block_types={block_types}")

    # Handle pause_turn: if Haiku paused mid-turn, continue the conversation
    if stop_reason == "pause_turn":
        # Send the response back to continue
        continue_body = json.dumps({
            "model": HAIKU_MODEL,
            "max_tokens": 2048,
            "tools": [tool_def],
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": result["content"]},
                {"role": "user", "content": "Continue."},
            ],
        })
        continue_req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=continue_body.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(continue_req, timeout=60) as response2:
                result = json.loads(response2.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Haiku continue API error {e.code}: {error_body}")

        stop_reason2 = result.get("stop_reason", "unknown")
        block_types2 = [b.get("type") for b in result.get("content", [])]
        print(f"Haiku continue: stop_reason={stop_reason2}, block_types={block_types2}")

    # Collect all text blocks — the JSON array is typically in the last one
    text_blocks = [
        block["text"] for block in result.get("content", [])
        if block.get("type") == "text" and block.get("text", "").strip()
    ]

    if not text_blocks:
        # Log full response for debugging
        print(f"Haiku full response: {json.dumps(result)[:2000]}")
        raise RuntimeError(f"Haiku returned no text. stop_reason={stop_reason}, blocks={block_types}")

    # Log all text blocks for debugging
    for i, tb in enumerate(text_blocks):
        print(f"Haiku text block {i}: {tb[:500]}")

    # Try each text block from last to first looking for the JSON array
    officials = None
    for tb in reversed(text_blocks):
        tb = tb.strip()
        tb = re.sub(r"```(?:json)?\s*\n?", "", tb)
        tb = re.sub(r"\n?```\s*", "", tb)
        match = re.search(r"\[[\s\S]*\]", tb)
        if match:
            try:
                officials = json.loads(match.group(0), strict=False)
                break
            except json.JSONDecodeError:
                continue

    if officials is None:
        # Last resort: concatenate ALL text blocks and try to find JSON
        all_text = "\n".join(text_blocks)
        all_text = re.sub(r"```(?:json)?\s*\n?", "", all_text)
        all_text = re.sub(r"\n?```\s*", "", all_text)
        match = re.search(r"\[[\s\S]*\]", all_text)
        if match:
            try:
                officials = json.loads(match.group(0), strict=False)
            except json.JSONDecodeError:
                pass

    if officials is None:
        last_text = text_blocks[-1] if text_blocks else "(empty)"
        print(f"PARSE FAILURE: {len(text_blocks)} text blocks, last={last_text[:1000]}")
        raise RuntimeError(f"No valid JSON array found in {len(text_blocks)} text blocks")
    if not isinstance(officials, list) or len(officials) == 0:
        raise ValueError("No officials returned from search")

    for rep in officials:
        for field in ("name", "title", "organization", "email", "relevance"):
            if field not in rep:
                rep[field] = ""

    return officials


def research_location(location, priorities):
    """Use Haiku + web search to find 2-3 local facts relevant to the citizen's priorities."""
    priorities_text = ", ".join(priorities) if priorities else "street lighting"
    city, region = parse_location(location)

    prompt = f"""Search for 2-3 specific, recent facts about {priorities_text} in {location} that relate to street lighting or outdoor lighting.

If the location is a zip code, first identify the city and county it belongs to, then search using the city/county name.

Look for:
- Local statistics (crime rates, traffic accidents, energy costs)
- Recent news stories or government initiatives
- Geographic/ecological facts (migration flyways, dark sky designations)
- Local government lighting projects or complaints

RULES:
- Every fact MUST include its source (organization name, publication, or government agency that published it).
- Format each fact as: "fact (Source: organization/publication name)"
- Only include facts you found in web search results. Do NOT extrapolate, round, or paraphrase loosely.
- If a search result gives a range, report the range, not a single number.
- If you cannot find anything specific to this location with a clear source, return 'No local context found.'
- Every statistic MUST include the year it was published or refers to (e.g., "In 2023, the city reported...").
- Strongly prefer data from the last 3 years (2024-2026). Data from 2020-2023 is acceptable if nothing newer exists.
- Data older than 2020 should only be included if it is a landmark study or no newer data exists, and MUST be flagged with its year prominently.
- If the only available data is old, say so: "The most recent data available is from [year]."

Do NOT include opinions or recommendations."""

    tool_def = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
    }
    if city and region:
        tool_def["user_location"] = {
            "type": "approximate",
            "city": city,
            "region": region,
            "country": "US",
        }

    request_body = json.dumps({
        "model": HAIKU_MODEL,
        "max_tokens": 1024,
        "tools": [tool_def],
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I'll search for local facts now."},
            {"role": "user", "content": "Go ahead. Return ONLY the sourced facts when done. No preamble."},
        ],
    })

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=request_body.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    stop_reason = result.get("stop_reason", "unknown")
    block_types = [b.get("type") for b in result.get("content", [])]
    print(f"Research response: stop_reason={stop_reason}, block_types={block_types}")

    # Handle pause_turn: Haiku paused mid-turn to do web searches, continue
    if stop_reason == "pause_turn":
        continue_body = json.dumps({
            "model": HAIKU_MODEL,
            "max_tokens": 1024,
            "tools": [tool_def],
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": result["content"]},
                {"role": "user", "content": "Continue. Return ONLY the sourced facts. No preamble."},
            ],
        })
        continue_req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=continue_body.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(continue_req, timeout=30) as response2:
            result = json.loads(response2.read().decode("utf-8"))
        print(f"Research continue: stop_reason={result.get('stop_reason')}, blocks={[b.get('type') for b in result.get('content', [])]}")

    text_blocks = [
        block["text"] for block in result.get("content", [])
        if block.get("type") == "text" and block.get("text", "").strip()
    ]

    local_context = "\n".join(text_blocks).strip() if text_blocks else ""
    print(f"Local research for {location}: {local_context[:500]}")
    return local_context


def call_claude(location, priorities, name, verified_reps=None, local_context=""):
    """Call Anthropic Claude API to generate letter (and optionally find representatives)."""
    priorities_text = ", ".join(priorities) if priorities else "general street lighting improvements"
    name_instruction = f'The letter should be signed by "{name}".' if name else 'Use "[Your Name]" as the signature since no name was provided.'

    # Link to the Top priority's specific best-practices page whenever there
    # is one — priorities[0] is always the Top priority (see sanitize_priorities;
    # UI caps selection to Top + optional Secondary), so this no longer needs
    # to fall back to the generic page just because a Secondary is also set.
    best_practices_url = PRIORITY_URLS.get(priorities[0], BEST_PRACTICES_DEFAULT) if priorities else BEST_PRACTICES_DEFAULT

    # Secondary priority (if any) gets folded into the top-priority paragraph
    # when the two share an underlying cause, or a brief closing mention when
    # they don't — rather than its own full paragraph, which is what made
    # multi-priority letters run long before this was capped to Top + Secondary.
    secondary_priority_instruction = ""
    if len(priorities) > 1:
        secondary_priority_instruction = f""" The citizen also selected a secondary priority: {priorities[1]}. First check whether it shares an underlying cause with the top priority (for example, Light Pollution and Energy Waste both come from eliminating unnecessary illumination). If it does, weave it into this same paragraph so it reads as one unified argument, not two bolted-together topics. If it does not naturally connect (for example, Crime & Safety and Migratory Birds), give it a brief mention only, one to two sentences, not a full paragraph of its own. The secondary priority MUST appear somewhere in the letter in one of these two forms; do not drop it entirely, and do not let it be displaced by an unselected topic even if local context research surfaced a more compelling story elsewhere."""

    # Build representatives section based on whether we have verified reps
    if verified_reps:
        reps_lines = []
        for r in verified_reps:
            reps_lines.append(
                f"- {r['name']}, {r['title']}, {r['organization']} ({r['email']})"
                + (f" — {r['relevance']}" if r.get('relevance') else "")
            )
        reps_section = f"""
REPRESENTATIVES (pre-verified, current officials):
The following officials have been verified as currently serving via web search.
Return them exactly as provided in your JSON response. Do not search for or
suggest different officials.

""" + "\n".join(reps_lines)
        reps_instructions = """
For the "representatives" array in your JSON response, return the pre-verified
officials listed above exactly as provided (same name, title, organization,
email, relevance). Do not modify or replace them."""
    else:
        reps_section = ""
        reps_instructions = f"""
For representatives, find exactly 4 people who actually influence street lighting decisions in or near {location}.

CRITICAL RULES:
- Each representative MUST be from a DIFFERENT category. Never return two people from the same type of role or agency. Pick one from each of 4 different categories.
- Match representatives to the citizen's priorities. For example:
  - "Crime & Safety" -> police chief, public safety director
  - "Migratory Birds" or "Environmental Impact" -> environmental affairs director, fish & wildlife regional contact
  - "Light Pollution" -> planning commission member, dark sky advocate in local government
  - "Energy Waste" -> sustainability officer, public utility commission member
  - "Transportation Safety" -> DOT district engineer, traffic safety manager
- Always include at least one person with direct authority over street lighting (public works director, transportation director, or city engineer).
- Fill the remaining 3 slots with officials whose portfolio aligns with the citizen's specific priorities.
- Use real government office email formats (e.g., mayor@cityof__.gov, firstname.lastname@state.gov). Do NOT make up personal email addresses."""

    local_context_section = ""
    if local_context and "No local context found" not in local_context:
        local_context_section = f"""

LOCAL CONTEXT (sourced facts from web search — each includes its source):
{local_context}

RULES FOR USING LOCAL CONTEXT:
- Use these facts only to support the citizen's selected priorities ({priorities_text}). If a fact relates to a different, unselected topic, do not let it take over the letter or replace the selected priorities' narrative, even if it is the most compelling story you found.
- You may weave these facts into the letter to make it specific to this location.
- When using a fact, mention the source naturally (e.g. "according to the FBI's Uniform Crime Report" or "data from the California Energy Commission shows").
- Only use facts that appear above AND have a named source. If a fact above has no source attribution, skip it.
- Do NOT invent, embellish, or extrapolate beyond what is stated above. Do NOT round numbers or change dates.
- Do NOT invent local statistics, news stories, events, or sources that do not appear in the LOCAL CONTEXT.
- RECENCY CHECK: If a statistic is from before 2021, do NOT use it unless no newer alternative exists. If you must use older data, explicitly note the year (e.g., "as of a 2018 study" or "based on 2019 data"). Never present old data as if it reflects current conditions.
- Prefer statistics from 2023 or later. If the local context only contains old data, it is better to omit it than to make the sender appear out of touch."""

    prompt = f"""You are helping a citizen write a persuasive letter to local officials about street lighting in their area.

{PRODUCT_CONTEXT}

Location: {location}
Their priorities: {priorities_text}
{name_instruction}{reps_section}{local_context_section}

Return a JSON object with exactly this structure (no markdown, no code blocks, just raw JSON):

{{
  "letter": "A letter addressed to [Official Name] (this placeholder will be replaced per recipient). Structure:\n\n1. Opening paragraph: Introduce yourself as a resident of the location concerned about street lighting. Do NOT invent personal anecdotes, stories, or events. State the core problem: street lighting in most communities is stuck in a false choice between safety and the environment. There is a better way.\n\n2. A full paragraph on the citizen's top priority. This paragraph MUST:\n   - Open with the human cost of the current state (the gap): what is broken, who is affected, what the real-world consequence is\n   - Name the false assumption behind the status quo (e.g., 'brighter means safer' when LAPD data shows properly designed lighting reduces crime 39%)\n   - Show how precision closes the gap: connect to a specific Photometrics AI capability from the context above\n   - Cite sourced numbers where relevant (35% energy savings, 39% crime reduction, 28-42% crash reduction per FHWA, 20% perception threshold). Do NOT cite dollar-per-light values or annual savings totals.\n   - Do NOT lead with product features. Lead with the problem, then show how precision solves it.{secondary_priority_instruction}\n\n3. Closing paragraph: The gap between what exists and what is possible is large, but closing it starts with a conversation. Ask the official to evaluate Photometrics AI as a solution and reach out to the company to learn more. Do NOT mention pricing, pilot costs, number of luminaires, or any dollar amounts — a citizen would not know these details. Frame it as pointing a leader toward a technology worth investigating, not prescribing a specific program. Near the closing, include a link to the Photometrics AI website where the official can learn more. Since Photometrics AI is already mentioned earlier in the letter, do NOT re-introduce the company. Instead, frame the link as pointing to additional detail, e.g. 'You can read more about how this works here:' or 'Their best practices page has more detail:'. In place of the URL, write the literal placeholder text [[BEST_PRACTICES_URL]] exactly as shown, including the double square brackets. Do not write out any URL yourself, real or invented; the placeholder will be substituted automatically after you respond. Do NOT use marketing language around the link.\n\n4. Sign off with the appropriate signature.\n\nTone: An earnest, informed citizen making a case, not a salesperson pitching a product. Professional and factual. The letter should make the official feel the distance between what their community has and what it could have.\n\nFORMATTING RULE: NEVER use em-dashes (the long dash character). Use commas, periods, semicolons, or parentheses instead. This is a strict formatting requirement.\n\nCORE CONCEPT: Every letter must express the idea of 'right light, right place, right time' — but in the citizen's own voice, not as a branded tagline. It should sound like a resident articulating common sense, e.g. 'It just makes sense to have the right amount of light where and when it is needed' or 'Why would we not light our streets based on what is actually needed?' Do NOT use the exact phrase 'right light, right place, right time' as if quoting marketing copy.",
  "representatives": [
    {{
      "name": "Full Name",
      "title": "Their actual title",
      "organization": "City/County/State agency",
      "email": "their@official.email.gov",
      "relevance": "One sentence on why this person specifically influences street lighting decisions"
    }}
  ]
}}
{reps_instructions}

Return ONLY the JSON object, no other text."""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
    })

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=request_body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Claude API error {e.code}: {error_body}")

    # Extract text from Claude response
    text = ""
    for block in result.get("content", []):
        if block.get("type") == "text":
            text += block["text"]

    # Strip markdown code blocks if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # strict=False: Claude's JSON output can contain literal (unescaped) newlines
    # inside string values, which Python's default strict JSON parser rejects.
    parsed = json.loads(text, strict=False)

    # Validate structure
    if "letter" not in parsed or "representatives" not in parsed:
        raise ValueError("Claude response missing required fields")
    if not isinstance(parsed["representatives"], list) or len(parsed["representatives"]) == 0:
        raise ValueError("No representatives returned")

    # Substitute the placeholder deterministically rather than trusting the
    # model to copy an arbitrary URL string correctly — it has been observed
    # to substitute a different (wrong) priority's best-practices URL when
    # the letter's content drifted toward an unselected topic.
    parsed["letter"] = parsed["letter"].replace("[[BEST_PRACTICES_URL]]", best_practices_url)

    # Normalize representatives
    for rep in parsed["representatives"]:
        for field in ("name", "title", "organization", "email", "relevance"):
            if field not in rep:
                rep[field] = ""

    return parsed


def dynamo_serialize(obj):
    """Recursively serialize a Python object for DynamoDB."""
    if isinstance(obj, dict):
        return {"M": {k: dynamo_serialize(v) for k, v in obj.items()}}
    elif isinstance(obj, list):
        return {"L": [dynamo_serialize(item) for item in obj]}
    elif isinstance(obj, str):
        return {"S": obj}
    elif isinstance(obj, (int, float)):
        return {"N": str(obj)}
    elif isinstance(obj, bool):
        return {"BOOL": obj}
    elif obj is None:
        return {"NULL": True}
    return {"S": str(obj)}


def log_generation(session_id, location, name, priorities, representatives, letter):
    """Log a generation event to DynamoDB."""
    ttl = int(time.time()) + (365 * 24 * 60 * 60)  # 1 year TTL

    item = {
        "session_id": {"S": session_id},
        "timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "location": {"S": location},
        "priorities": {"L": [{"S": p} for p in priorities]},
        "letter": {"S": letter},
        "representatives": dynamo_serialize(representatives),
        "actions": {"L": []},
        "ttl": {"N": str(ttl)},
    }

    if name:
        item["name"] = {"S": name}

    try:
        dynamodb.put_item(TableName=DYNAMO_TABLE, Item=item)
    except Exception as e:
        print(f"DynamoDB write error: {e}")


def log_tracking(session_id, event, rep_email):
    """Append a tracking action to an existing DynamoDB record."""
    try:
        dynamodb.update_item(
            TableName=DYNAMO_TABLE,
            Key={"session_id": {"S": session_id}},
            UpdateExpression="SET #actions = list_append(if_not_exists(#actions, :empty), :new_action)",
            ExpressionAttributeNames={"#actions": "actions"},
            ExpressionAttributeValues={
                ":empty": {"L": []},
                ":new_action": {
                    "L": [
                        {
                            "M": {
                                "event": {"S": event},
                                "rep_email": {"S": rep_email},
                                "timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                            }
                        }
                    ]
                },
            },
        )
    except Exception as e:
        print(f"DynamoDB tracking error: {e}")


def handle_generate(body):
    """Handle POST /generate — AI letter generation."""
    location = sanitize_string(body.get("location", ""), 200)
    name = sanitize_string(body.get("name", ""), 100)
    priorities = sanitize_priorities(body.get("priorities", []))

    if not location or len(location) < 2:
        return respond(400, {"error": "Location is required (minimum 2 characters)."})

    if not priorities:
        return respond(400, {"error": "At least one priority is required."})

    session_id = body.get("session_id", str(uuid.uuid4()))

    # Step 1: Gather context for official search
    civic_officials = get_civic_officials(location)
    boosted_officials = get_boosted_officials(location)
    excluded_emails = get_flagged_emails() | get_bounced_emails()
    boosted_officials = [
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
    log_generation(
        session_id=session_id,
        location=location,
        name=name,
        priorities=priorities,
        representatives=result["representatives"],
        letter=result["letter"],
    )

    return respond(200, {
        "session_id": session_id,
        "letter": result["letter"],
        "representatives": result["representatives"],
    })


def handle_flag(body):
    """Handle POST /flag — user reports an official as no longer current."""
    email = sanitize_string(body.get("email", ""), 200).lower()
    location = sanitize_string(body.get("location", ""), 200)

    if not email:
        return respond(400, {"error": "email is required."})

    try:
        dynamodb.put_item(
            TableName=FLAGGED_TABLE,
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
    """Return set of emails that users have flagged as not current."""
    flagged = set()
    try:
        resp = dynamodb.scan(
            TableName=FLAGGED_TABLE,
            ProjectionExpression="email",
        )
        for item in resp.get("Items", []):
            email = item.get("email", {}).get("S", "")
            if email:
                flagged.add(email.lower())
    except Exception as e:
        print(f"Flagged scan error: {e}")
    return flagged


def get_bounced_emails():
    """Return set of emails that hard-bounced or triggered a spam complaint
    on a prior managed send, so they're excluded from future suggestions the
    same way a manually flagged 'Not current?' email is. Transient bounces
    (mailbox full, temporary server issue) are excluded from this set — those
    are delivery hiccups, not evidence the official is no longer there."""
    bounced = set()
    try:
        resp = dynamodb.scan(
            TableName=BOUNCE_TABLE,
            ProjectionExpression="email, event_type, #st",
            ExpressionAttributeNames={"#st": "subtype"},  # "subtype" is a DynamoDB reserved word
        )
        for item in resp.get("Items", []):
            email = item.get("email", {}).get("S", "")
            event_type = item.get("event_type", {}).get("S", "")
            subtype = item.get("subtype", {}).get("S", "")
            if not email:
                continue
            if event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"):
                bounced.add(email.lower())
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
            Key={"session_id": {"S": session_id}},
        )
    except Exception as e:
        print(f"Session lookup error: {e}")
        return None

    item = resp.get("Item")
    if not item:
        return None

    emails = set()
    for rep_item in item.get("representatives", {}).get("L", []):
        rep = rep_item.get("M", {})
        email = rep.get("email", {}).get("S", "")
        if email:
            emails.add(email.strip().lower())
    return emails


def already_sent(session_id):
    """Check whether this session already has a managed-send log entry, so a
    double-click (or a replayed request) can't send the same letter twice."""
    try:
        resp = dynamodb.get_item(
            TableName=SEND_LOG_TABLE,
            Key={"session_id": {"S": session_id}},
        )
    except Exception as e:
        print(f"Send-log lookup error: {e}")
        return False
    return "Item" in resp


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


def log_send(session_id, constituent_email, location, representatives_sent, message_ids):
    """Log a managed-send event. 1-year TTL to match the retention already
    used for the rest of the take-action log (session, letter, reps) —
    see the take-action privacy-policy note for why this needs disclosure."""
    ttl = int(time.time()) + (365 * 24 * 60 * 60)

    item = {
        "session_id": {"S": session_id or str(uuid.uuid4())},
        "timestamp": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "constituent_email": {"S": constituent_email},
        "location": {"S": location},
        "representatives_sent": {"L": [{"S": e} for e in representatives_sent]},
        "message_ids": {"L": [{"S": m} for m in message_ids]},
        "ttl": {"N": str(ttl)},
    }

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
    session_id = sanitize_string(body.get("session_id", ""), 100)
    constituent_name = sanitize_string(body.get("name", ""), 100)
    constituent_email = sanitize_string(body.get("email", ""), 200)
    location = sanitize_string(body.get("location", ""), 200)
    letter = body.get("letter", "")
    representatives = body.get("representatives", [])

    if not session_id:
        return respond(400, {"error": "session_id is required."})
    if not is_valid_email(constituent_email):
        return respond(400, {"error": "A valid email address is required to send."})
    if not isinstance(letter, str) or not letter.strip():
        return respond(400, {"error": "Letter text is required."})
    if not isinstance(representatives, list) or len(representatives) == 0:
        return respond(400, {"error": "At least one representative is required."})

    if already_sent(session_id):
        return respond(409, {"error": "This letter has already been sent."})

    verified_emails = get_verified_representative_emails(session_id)
    if verified_emails is None:
        return respond(400, {"error": "We couldn't verify this session. Please generate your letter again."})

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

    letter = letter.strip()[:20000]
    sender_name = constituent_name or "A Concerned Resident"
    subject = f"Street Lighting Improvement Request – {location}" if location else "Street Lighting Improvement Request"

    # One SES call per official (not one message with all officials in To) —
    # each gets their own message personalized with their own name, and a
    # bounce/complaint on one address never affects delivery to the others.
    sent = []
    failed = []
    for rep in verified_reps:
        personalized_letter = letter.replace("[Official Name]", build_single_salutation(rep))
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
            failed.append(rep["email"])

    if not sent:
        return respond(502, {"error": "Failed to send email. Please try again or use the manual options below."})

    log_send(
        session_id=session_id,
        constituent_email=constituent_email,
        location=location,
        representatives_sent=[s["email"] for s in sent],
        message_ids=[s["message_id"] for s in sent],
    )

    return respond(200, {
        "status": "sent",
        "sent_count": len(sent),
        "failed_count": len(failed),
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

    for email in recipients:
        if not email:
            continue
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


def handle_ses_notification(event):
    """Process SES bounce/complaint notifications delivered via SNS.

    Wired to the 'take-action-sends' SES configuration set's event
    destination, which publishes Bounce/Complaint events to the
    photometrics-ses-bounces SNS topic this Lambda is subscribed to.
    """
    for record in event.get("Records", []):
        try:
            message = json.loads(record.get("Sns", {}).get("Message", "{}"))
        except json.JSONDecodeError:
            continue
        notification_type = message.get("notificationType") or message.get("eventType")
        if notification_type == "Bounce":
            record_bounce_event(message, "Bounce")
        elif notification_type == "Complaint":
            record_bounce_event(message, "Complaint")
    return {"statusCode": 200}


def handle_track(body):
    """Handle POST /track — click event tracking."""
    session_id = sanitize_string(body.get("session_id", ""), 100)
    event = sanitize_string(body.get("event", ""), 50)
    rep_email = sanitize_string(body.get("representative_email", ""), 200)

    valid_events = {"click_copy"}
    if event not in valid_events:
        return respond(400, {"error": "Invalid event type."})

    if not session_id:
        return respond(400, {"error": "session_id is required."})

    log_tracking(session_id, event, rep_email)
    return respond(200, {"status": "tracked"})


def lambda_handler(event, context):
    """Main Lambda entry point — routes by path (Function URL) or by trigger
    source (SNS, for SES bounce/complaint notifications)."""
    records = event.get("Records")
    if records and records[0].get("EventSource") == "aws:sns":
        return handle_ses_notification(event)

    # Handle CORS preflight
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return respond(200, {})

    path = event.get("rawPath", event.get("path", ""))

    # Parse body
    body_str = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64
        body_str = base64.b64decode(body_str).decode("utf-8")

    try:
        body = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        return respond(400, {"error": "Invalid JSON body."})

    if path.endswith("/generate"):
        return handle_generate(body)
    elif path.endswith("/send"):
        return handle_send(body)
    elif path.endswith("/track"):
        return handle_track(body)
    elif path.endswith("/flag"):
        return handle_flag(body)
    else:
        return respond(404, {"error": "Not found."})
