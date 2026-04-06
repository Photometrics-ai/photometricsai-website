"""
Synchronous Phase API — POST /api/phase
Accepts JSON with rows of lat/lon/datetime, returns enriched results.
"""

import json
import time
from datetime import datetime

from timezonefinder import TimezoneFinder

from phase_calculator_core import calculate_phase_for_row

# Reuse across warm invocations
tf = TimezoneFinder()

MAX_ROWS = 10_000

MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}


def _parse_row(row):
    """
    Parse a JSON row into (lat, lon, date_str, time_int) or return an error dict.

    Accepts either:
      - date + time (combined)
      - year + month + day + hour + minute (separate / FARS-style)
    """
    lat = row.get('latitude')
    lon = row.get('longitude')

    if lat is None or lon is None:
        return None, "Missing latitude or longitude"

    # Combined mode: date + time
    if 'date' in row and 'time' in row:
        return (lat, lon, row['date'], row['time']), None

    # Separate mode: year/month/day/hour/minute
    for field in ('year', 'month', 'day', 'hour', 'minute'):
        if field not in row:
            return None, f"Missing field: {field} (provide date+time or year/month/day/hour/minute)"

    try:
        year = int(row['year'])
        day = int(row['day'])
        hour_raw = int(row['hour'])
        minute_raw = int(row['minute'])
    except (ValueError, TypeError) as e:
        return None, f"Invalid numeric field: {e}"

    # FARS uses 99 for unknown
    if hour_raw == 99 or minute_raw == 99:
        return None, "Unknown time (99)"

    # Parse month — int or name string
    month_val = row['month']
    if isinstance(month_val, str):
        month_lower = month_val.strip().lower()
        if month_lower in MONTH_NAMES:
            month = MONTH_NAMES[month_lower]
        else:
            try:
                month = int(month_val)
            except ValueError:
                return None, f"Invalid month: {month_val}"
    else:
        try:
            month = int(month_val)
        except (ValueError, TypeError):
            return None, f"Invalid month: {month_val}"

    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    time_int = hour_raw * 100 + minute_raw
    return (lat, lon, date_str, time_int), None


def lambda_handler(event, context):
    start = time.time()
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', '?')

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    # Parse body
    body_str = event.get('body', '')
    if event.get('isBase64Encoded'):
        import base64
        body_str = base64.b64decode(body_str).decode('utf-8')

    try:
        body = json.loads(body_str or '{}')
    except json.JSONDecodeError:
        return {'statusCode': 400, 'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON'})}

    rows = body.get('rows')
    if not isinstance(rows, list) or len(rows) == 0:
        return {'statusCode': 400, 'headers': headers,
                'body': json.dumps({'error': 'Request must contain a non-empty "rows" array'})}

    if len(rows) > MAX_ROWS:
        return {'statusCode': 400, 'headers': headers,
                'body': json.dumps({'error': f'Maximum {MAX_ROWS:,} rows per request'})}

    # Process rows
    results = []
    for row in rows:
        parsed, error = _parse_row(row)
        if error:
            result = dict(row)
            result.update({
                'evSunElevAngle': None,
                'evPhase': f"Error: {error}",
                'evStreetlightsOn': False
            })
            results.append(result)
            continue

        lat, lon, date_val, time_val = parsed
        sun_elev, phase, lights_on, _err = calculate_phase_for_row(
            lat, lon, date_val, time_val, tf
        )

        result = dict(row)
        result.update({
            'evSunElevAngle': round(sun_elev, 2) if sun_elev is not None else None,
            'evPhase': phase,
            'evStreetlightsOn': lights_on
        })
        results.append(result)

    elapsed = time.time() - start
    print(f"[phase-api] ip={ip} rows={len(rows)} duration={elapsed:.2f}s")

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'rows': results})
    }
