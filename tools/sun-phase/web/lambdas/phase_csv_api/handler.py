"""
Synchronous Phase CSV API — POST /api/phase/csv
Accepts CSV upload, returns CSV with appended phase columns.
"""

import io
import time
import base64

import pandas as pd
from timezonefinder import TimezoneFinder

from phase_calculator_core import calculate_phase_for_row, auto_detect_columns

# Reuse across warm invocations
tf = TimezoneFinder()

MAX_ROWS = 10_000

MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}


def _assemble_datetime_from_separate(row, columns):
    """Assemble date string and military time int from separate columns."""
    try:
        year = int(row.get(columns['year'], 0))
        day = int(row.get(columns['day_of_month'], 0))
        hour_raw = int(row.get(columns['hour'], 99))
        minute_raw = int(row.get(columns['minute'], 99))

        if hour_raw == 99 or minute_raw == 99:
            return None, "Error: Unknown time (99)"

        month_val = row.get(columns['month'])
        if pd.isna(month_val):
            return None, "Error: Missing month"
        if isinstance(month_val, str):
            month_lower = month_val.strip().lower()
            if month_lower in MONTH_NAMES:
                month = MONTH_NAMES[month_lower]
            else:
                month = int(month_val)
        else:
            month = int(month_val)

        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        time_int = hour_raw * 100 + minute_raw
        return date_str, time_int
    except Exception as e:
        return None, f"Error: {e}"


def lambda_handler(event, context):
    start = time.time()
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', '?')

    csv_headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="phase_results.csv"',
        'Access-Control-Allow-Origin': '*'
    }
    err_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    # Read CSV from body
    body = event.get('body', '')
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')

    if not body or not body.strip():
        return {'statusCode': 400, 'headers': err_headers,
                'body': '{"error": "Empty request body — expected CSV data"}'}

    try:
        df = pd.read_csv(io.StringIO(body), low_memory=False)
    except Exception as e:
        return {'statusCode': 400, 'headers': err_headers,
                'body': f'{{"error": "Failed to parse CSV: {e}"}}'}

    if len(df) == 0:
        return {'statusCode': 400, 'headers': err_headers,
                'body': '{"error": "CSV contains no data rows"}'}

    if len(df) > MAX_ROWS:
        return {'statusCode': 400, 'headers': err_headers,
                'body': f'{{"error": "CSV has {len(df):,} rows — maximum is {MAX_ROWS:,}"}}'}

    # Auto-detect columns, allow query param overrides
    qsp = event.get('queryStringParameters') or {}
    detected = auto_detect_columns(df.columns.tolist())

    # Apply overrides from query params
    override_map = {
        'lat': 'lat', 'lon': 'lon',
        'date': 'date', 'time': 'time',
        'year': 'year', 'month': 'month',
        'day': 'day_of_month', 'hour': 'hour', 'minute': 'minute'
    }
    for param, field in override_map.items():
        if param in qsp and qsp[param]:
            detected[field] = qsp[param]

    # Determine mode — override if separate fields provided via query params
    if all(qsp.get(f) for f in ('year', 'month', 'day', 'hour', 'minute')):
        detected['mode'] = 'separate'
    elif qsp.get('date') and qsp.get('time'):
        detected['mode'] = 'combined'

    mode = detected.get('mode', 'combined')
    lat_col = detected.get('lat')
    lon_col = detected.get('lon')

    if not lat_col or not lon_col:
        return {'statusCode': 400, 'headers': err_headers,
                'body': '{"error": "Could not detect latitude/longitude columns. Use ?lat=COL&lon=COL query params."}'}

    if mode == 'combined':
        if not detected.get('date') or not detected.get('time'):
            return {'statusCode': 400, 'headers': err_headers,
                    'body': '{"error": "Could not detect date/time columns. Use ?date=COL&time=COL or ?year=COL&month=COL&day=COL&hour=COL&minute=COL"}'}
    else:
        for f in ('year', 'month', 'day_of_month', 'hour', 'minute'):
            if not detected.get(f):
                return {'statusCode': 400, 'headers': err_headers,
                        'body': f'{{"error": "Could not detect {f} column. Use query params to specify."}}'}

    # Process rows
    results = []
    for _, row in df.iterrows():
        if mode == 'separate':
            date_val, time_val = _assemble_datetime_from_separate(row, detected)
            if date_val is None:
                results.append({
                    'evSunElevAngle': None,
                    'evPhase': time_val,  # error message
                    'evStreetlightsOn': False
                })
                continue
        else:
            date_val = row.get(detected['date'])
            time_val = row.get(detected['time'])

        sun_elev, phase, lights_on, _err = calculate_phase_for_row(
            row.get(lat_col), row.get(lon_col),
            date_val, time_val, tf
        )
        results.append({
            'evSunElevAngle': round(sun_elev, 2) if sun_elev is not None else None,
            'evPhase': phase,
            'evStreetlightsOn': lights_on
        })

    results_df = pd.DataFrame(results)
    df = pd.concat([df.reset_index(drop=True), results_df], axis=1)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    elapsed = time.time() - start
    print(f"[phase-csv] ip={ip} rows={len(df)} cols={len(df.columns)} duration={elapsed:.2f}s")

    return {
        'statusCode': 200,
        'headers': csv_headers,
        'body': csv_buffer.getvalue(),
        'isBase64Encoded': False
    }
