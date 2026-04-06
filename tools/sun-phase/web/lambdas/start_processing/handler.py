"""
POST /api/phase/start
Validates column selections, starts Step Functions execution.
Body: {"jobId": "...", "columns": {"lat": "...", "lon": "...", "date": "...", "time": "..."}}
"""

import json
import os

import boto3

DATA_BUCKET = os.environ['DATA_BUCKET']
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']
s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')


def lambda_handler(event, context):
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
    body = json.loads(event.get('body', '{}'))
    job_id = body.get('jobId')
    columns = body.get('columns', {})

    if not job_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'jobId is required'})
        }

    mode = columns.get('mode', 'combined')
    if mode == 'separate':
        required = ('lat', 'lon', 'year', 'month', 'day_of_month', 'hour', 'minute')
    else:
        required = ('lat', 'lon', 'date', 'time')

    for field in required:
        if not columns.get(field):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'columns.{field} is required'})
            }

    s3_key = f"uploads/{job_id}/input.csv"

    # Verify file exists
    try:
        s3.head_object(Bucket=DATA_BUCKET, Key=s3_key)
    except Exception:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'CSV not found. Upload may not be complete.'})
        }

    # Update meta
    meta = {
        'jobId': job_id,
        'status': 'processing',
        's3Key': s3_key,
        'columns': columns
    }
    s3.put_object(
        Bucket=DATA_BUCKET,
        Key=f"uploads/{job_id}/meta.json",
        Body=json.dumps(meta),
        ContentType='application/json'
    )

    # Start Step Functions
    sfn_input = {
        'jobId': job_id,
        'bucket': DATA_BUCKET,
        's3Key': s3_key,
        'columns': columns
    }

    sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=job_id,
        input=json.dumps(sfn_input)
    )

    print(f"[start] ip={ip} jobId={job_id} columns={columns}")

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'jobId': job_id, 'status': 'processing'})
    }
