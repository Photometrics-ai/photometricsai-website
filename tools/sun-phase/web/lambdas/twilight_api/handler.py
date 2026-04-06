"""
GET /api/twilight?lat=&lon=&year=
Returns CSV with nautical twilight times for the year.
"""

import json
import time
from datetime import datetime

from twilight_core import generate_twilight_csv


def lambda_handler(event, context):
    start = time.time()
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
    ua = event.get('headers', {}).get('User-Agent', 'unknown') if event.get('headers') else 'unknown'
    params = event.get('queryStringParameters') or {}

    try:
        lat = float(params.get('lat', ''))
        lon = float(params.get('lon', ''))
    except (ValueError, TypeError):
        print(f"[twilight] ip={ip} error=invalid_params")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'lat and lon are required numeric parameters'})
        }

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        print(f"[twilight] ip={ip} error=out_of_range lat={lat} lon={lon}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'lat must be -90..90, lon must be -180..180'})
        }

    try:
        year = int(params.get('year', datetime.now().year))
    except (ValueError, TypeError):
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'year must be an integer'})
        }

    if not (1900 <= year <= 2100):
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'year must be between 1900 and 2100'})
        }

    try:
        csv_content = generate_twilight_csv(lat, lon, year)
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

    elapsed = time.time() - start
    print(f"[twilight] ip={ip} lat={lat} lon={lon} year={year} duration={elapsed:.2f}s ua={ua}")

    filename = f"twilight_{lat}_{lon}_{year}.csv"
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="{filename}"'
        },
        'body': csv_content
    }
