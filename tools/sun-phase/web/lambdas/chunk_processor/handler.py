"""
Step Functions: ChunkProcessor
Processes a single CSV chunk — adds sun elevation, twilight phase, streetlights columns.
"""

import json
import os
import io
import time
from datetime import datetime

import boto3
import pandas as pd
from timezonefinder import TimezoneFinder

from phase_calculator_core import calculate_phase_for_row

DATA_BUCKET = os.environ['DATA_BUCKET']
s3 = boto3.client('s3')

# Reuse across warm invocations
tf = TimezoneFinder()


MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}


def _assemble_datetime_from_separate(row, columns):
    """
    Assemble date string and military time int from separate columns.

    Returns:
        (date_str, time_int) on success
        (None, error_message) on failure
    """
    try:
        year = int(row.get(columns['year'], 0))
        day = int(row.get(columns['day_of_month'], 0))
        hour_raw = int(row.get(columns['hour'], 99))
        minute_raw = int(row.get(columns['minute'], 99))

        # FARS uses 99 for unknown hour/minute
        if hour_raw == 99 or minute_raw == 99:
            return None, "Error: Unknown time (99)"

        # Parse month — could be int or name string
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
    bucket = event['bucket']
    chunk_key = event['chunkKey']
    chunk_index = event['chunkIndex']
    job_id = event['jobId']
    columns = event['columns']

    mode = columns.get('mode', 'combined')
    lat_col = columns['lat']
    lon_col = columns['lon']

    # Read chunk
    resp = s3.get_object(Bucket=bucket, Key=chunk_key)
    df = pd.read_csv(resp['Body'], low_memory=False)

    # Process each row
    results = []
    for _, row in df.iterrows():
        if mode == 'separate':
            date_val, time_val = _assemble_datetime_from_separate(row, columns)
            if date_val is None:
                results.append({
                    'evSunElevAngle': None,
                    'evPhase': time_val,  # error message
                    'evStreetlightsOn': False
                })
                continue
        else:
            date_val = row.get(columns['date'])
            time_val = row.get(columns['time'])

        sun_elev, phase, lights_on, error = calculate_phase_for_row(
            row.get(lat_col), row.get(lon_col),
            date_val, time_val, tf
        )
        results.append({
            'evSunElevAngle': sun_elev,
            'evPhase': phase,
            'evStreetlightsOn': lights_on
        })

    results_df = pd.DataFrame(results)
    df = pd.concat([df.reset_index(drop=True), results_df], axis=1)

    # Write processed chunk
    output_key = f"uploads/{job_id}/processed/chunk_{chunk_index:04d}.csv"
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )

    elapsed = time.time() - start
    print(f"[chunk] jobId={job_id} chunk={chunk_index} rows={len(df)} duration={elapsed:.2f}s")

    return {
        'chunkIndex': chunk_index,
        'outputKey': output_key,
        'rowsProcessed': len(df)
    }
