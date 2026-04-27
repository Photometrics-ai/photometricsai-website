"""
POST /api/phase/upload
Returns a presigned S3 URL for CSV upload and a jobId.
"""

import json
import os
import uuid

import boto3

DATA_BUCKET = os.environ['DATA_BUCKET']
s3 = boto3.client('s3', region_name='us-east-2')


def lambda_handler(event, context):
    ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
    ua = event.get('headers', {}).get('User-Agent', 'unknown') if event.get('headers') else 'unknown'
    job_id = str(uuid.uuid4())
    s3_key = f"uploads/{job_id}/input.csv"

    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': DATA_BUCKET,
            'Key': s3_key,
            'ContentType': 'text/csv'
        },
        ExpiresIn=3600
    )

    # Write initial meta
    meta = {'jobId': job_id, 'status': 'uploaded', 's3Key': s3_key}
    s3.put_object(
        Bucket=DATA_BUCKET,
        Key=f"uploads/{job_id}/meta.json",
        Body=json.dumps(meta),
        ContentType='application/json'
    )

    print(f"[upload] ip={ip} jobId={job_id} ua={ua}")

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'jobId': job_id,
            'uploadUrl': presigned_url
        })
    }
