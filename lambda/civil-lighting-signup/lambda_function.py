"""
Civil Lighting Design - Newsletter Signup Lambda
Proxies newsletter signups to Buttondown's authenticated REST API server-side,
bypassing the public Turnstile-gated embed-subscribe endpoint (which fails to
render for many visitors). The Buttondown API key lives only in this Lambda's
environment and is never exposed to the browser.
"""

import json
import os
import re
import urllib.request
import urllib.error

BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY", "")
BUTTONDOWN_SUBSCRIBERS_URL = "https://api.buttondown.com/v1/subscribers"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CORS_HEADERS = {
    "Content-Type": "application/json",
}


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def handle_subscribe(body):
    email = body.get("email", "")
    email = email.strip() if isinstance(email, str) else ""

    if not email or not EMAIL_RE.match(email) or len(email) > 254:
        return respond(400, {"error": "Please enter a valid email address."})

    request_body = json.dumps({
        "email_address": email,
        "type": "unactivated",
    })

    req = urllib.request.Request(
        BUTTONDOWN_SUBSCRIBERS_URL,
        data=request_body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response.read()
        return respond(200, {"status": "subscribed"})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"Buttondown API error {e.code}: {error_body}")
        if e.code == 400 and re.search(r"already|exist", error_body, re.IGNORECASE):
            return respond(200, {"status": "already_subscribed"})
        return respond(502, {"error": "We couldn't complete your subscription. Please try again."})
    except Exception as e:
        print(f"Buttondown request error: {e}")
        return respond(502, {"error": "We couldn't complete your subscription. Please try again."})


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return respond(200, {})

    body_str = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64
        body_str = base64.b64decode(body_str).decode("utf-8")

    try:
        body = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        return respond(400, {"error": "Invalid JSON body."})

    return handle_subscribe(body)
