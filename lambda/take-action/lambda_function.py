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

import boto3
from boto3.dynamodb.types import TypeSerializer

DYNAMO_TABLE = os.environ.get("DYNAMODB_TABLE", "photometrics-take-action")
BOOSTED_TABLE = os.environ.get("BOOSTED_TABLE", "photometrics-boosted-officials")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_CIVIC_API_KEY = os.environ.get("GOOGLE_CIVIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

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


def sanitize_priorities(priorities):
    if not isinstance(priorities, list):
        return []
    cleaned = []
    for p in priorities[:10]:
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


def search_officials(location, priorities, civic_officials=None, boosted_officials=None):
    """Use Haiku + web search to find verified current officials."""
    priorities_text = ", ".join(priorities)
    city, region = parse_location(location)

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
{civic_section}{boosted_section}

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
                officials = json.loads(match.group(0))
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
                officials = json.loads(match.group(0))
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


def call_claude(location, priorities, name, verified_reps=None):
    """Call Anthropic Claude API to generate letter (and optionally find representatives)."""
    priorities_text = ", ".join(priorities) if priorities else "general street lighting improvements"
    name_instruction = f'The letter should be signed by "{name}".' if name else 'Use "[Your Name]" as the signature since no name was provided.'

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

    prompt = f"""You are helping a citizen write a persuasive letter to local officials about street lighting in their area.

{PRODUCT_CONTEXT}

Location: {location}
Their priorities: {priorities_text}
{name_instruction}{reps_section}

Return a JSON object with exactly this structure (no markdown, no code blocks, just raw JSON):

{{
  "letter": "A letter addressed to [Official Name] (this placeholder will be replaced per recipient). Structure:\n\n1. Opening paragraph: Introduce yourself as a resident of the location concerned about street lighting. Do NOT invent personal anecdotes, stories, or events. State the core problem: street lighting in most communities is stuck in a false choice between safety and the environment. There is a better way.\n\n2. One paragraph per priority the citizen selected. Each paragraph MUST:\n   - Open with the human cost of the current state (the gap): what is broken, who is affected, what the real-world consequence is\n   - Name the false assumption behind the status quo (e.g., 'brighter means safer' when LAPD data shows properly designed lighting reduces crime 39%)\n   - Show how precision closes the gap: connect to a specific Photometrics AI capability from the context above\n   - Cite sourced numbers where relevant (35% energy savings, 39% crime reduction, 28-42% crash reduction per FHWA, 20% perception threshold). Do NOT cite dollar-per-light values or annual savings totals.\n   - Do NOT lead with product features. Lead with the problem, then show how precision solves it.\n\n3. Closing paragraph: The gap between what exists and what is possible is large, but closing it starts with a conversation. Ask the official to evaluate Photometrics AI as a solution and reach out to the company to learn more. Do NOT mention pricing, pilot costs, number of luminaires, or any dollar amounts — a citizen would not know these details. Frame it as pointing a leader toward a technology worth investigating, not prescribing a specific program.\n\n4. Sign off with the appropriate signature.\n\nTone: An earnest, informed citizen making a case, not a salesperson pitching a product. Professional and factual. The letter should make the official feel the distance between what their community has and what it could have.\n\nFORMATTING RULE: NEVER use em-dashes (the long dash character). Use commas, periods, semicolons, or parentheses instead. This is a strict formatting requirement.\n\nCORE CONCEPT: Every letter must express the idea of 'right light, right place, right time' — but in the citizen's own voice, not as a branded tagline. It should sound like a resident articulating common sense, e.g. 'It just makes sense to have the right amount of light where and when it is needed' or 'Why would we not light our streets based on what is actually needed?' Do NOT use the exact phrase 'right light, right place, right time' as if quoting marketing copy.",
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

    parsed = json.loads(text)

    # Validate structure
    if "letter" not in parsed or "representatives" not in parsed:
        raise ValueError("Claude response missing required fields")
    if not isinstance(parsed["representatives"], list) or len(parsed["representatives"]) == 0:
        raise ValueError("No representatives returned")

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

    # Step 2: Haiku + web search finds verified officials
    try:
        verified_reps = search_officials(location, priorities, civic_officials, boosted_officials)
    except Exception as e:
        print(f"Official search error: {e}")
        return respond(502, {"error": f"Failed to verify representatives: {e}"})

    # Step 3: Sonnet writes the letter using verified reps
    try:
        result = call_claude(location, priorities, name, verified_reps)
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


def handle_track(body):
    """Handle POST /track — click event tracking."""
    session_id = sanitize_string(body.get("session_id", ""), 100)
    event = sanitize_string(body.get("event", ""), 50)
    rep_email = sanitize_string(body.get("representative_email", ""), 200)

    valid_events = {"click_mailto", "click_gmail", "click_copy"}
    if event not in valid_events:
        return respond(400, {"error": "Invalid event type."})

    if not session_id:
        return respond(400, {"error": "session_id is required."})

    log_tracking(session_id, event, rep_email)
    return respond(200, {"status": "tracked"})


def lambda_handler(event, context):
    """Main Lambda entry point — routes by path."""
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
    elif path.endswith("/track"):
        return handle_track(body)
    else:
        return respond(404, {"error": "Not found."})
