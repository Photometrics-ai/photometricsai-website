"""
GET /api/phase/status?jobId=
Returns job status and download URL when complete.
"""

import json
import os

import boto3

DATA_BUCKET = os.environ['DATA_BUCKET']
s3 = boto3.client('s3', region_name='us-east-2')


def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    job_id = params.get('jobId')

    if not job_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'jobId is required'})
        }

    try:
        resp = s3.get_object(
            Bucket=DATA_BUCKET,
            Key=f"uploads/{job_id}/meta.json"
        )
        meta = json.loads(resp['Body'].read().decode('utf-8'))

        # Regenerate download URL if complete (in case cached one expired)
        if meta.get('status') == 'complete' and meta.get('resultKey'):
            meta['downloadUrl'] = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': DATA_BUCKET, 'Key': meta['resultKey']},
                ExpiresIn=3600
            )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(meta)
        }
    except s3.exceptions.NoSuchKey:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Job not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
