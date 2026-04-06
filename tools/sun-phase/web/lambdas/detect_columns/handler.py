"""
POST /api/phase/detect-columns
Reads CSV header from S3, auto-detects column mappings.
Body: {"jobId": "..."}
"""

import json
import os

import boto3
import pandas as pd

from phase_calculator_core import auto_detect_columns

DATA_BUCKET = os.environ['DATA_BUCKET']
s3 = boto3.client('s3')


def lambda_handler(event, context):
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
    body = json.loads(event.get('body', '{}'))
    job_id = body.get('jobId')

    if not job_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'jobId is required'})
        }

    s3_key = f"uploads/{job_id}/input.csv"

    try:
        # Read just the first line to get headers
        resp = s3.get_object(Bucket=DATA_BUCKET, Key=s3_key, Range='bytes=0-8192')
        first_bytes = resp['Body'].read().decode('utf-8', errors='replace')
        first_line = first_bytes.split('\n')[0]
        columns = [col.strip().strip('"') for col in first_line.split(',')]

        detected = auto_detect_columns(columns)

        print(f"[detect] ip={ip} jobId={job_id} columns={len(columns)} detected={detected}")

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'columns': columns,
                'detected': detected
            })
        }
    except s3.exceptions.NoSuchKey:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'CSV not found. Upload may not be complete.'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
