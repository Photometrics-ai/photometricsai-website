"""
Step Functions: Combiner
Concatenates all processed chunks into a single output CSV.
"""

import json
import os
import io
import time

import boto3
import pandas as pd

DATA_BUCKET = os.environ['DATA_BUCKET']
s3 = boto3.client('s3')


def lambda_handler(event, context):
    start = time.time()
    job_id = event['jobId']
    bucket = event['bucket']
    chunk_results = event['chunkResults']

    # Sort by chunk index to preserve row order
    chunk_results.sort(key=lambda x: x['chunkIndex'])

    # Read and concatenate all processed chunks
    output_key = f"uploads/{job_id}/result.csv"

    # Use multipart upload for large files
    mpu = s3.create_multipart_upload(
        Bucket=bucket,
        Key=output_key,
        ContentType='text/csv'
    )
    upload_id = mpu['UploadId']

    try:
        parts = []
        accumulated = b""
        part_number = 1
        MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum for multipart

        for i, chunk_result in enumerate(chunk_results):
            resp = s3.get_object(Bucket=bucket, Key=chunk_result['outputKey'])
            chunk_data = resp['Body'].read()

            if i == 0:
                # First chunk: include header
                accumulated += chunk_data
            else:
                # Skip header line for subsequent chunks
                lines = chunk_data.split(b'\n', 1)
                if len(lines) > 1:
                    accumulated += lines[1]

            # Upload part when accumulated enough data
            if len(accumulated) >= MIN_PART_SIZE:
                part = s3.upload_part(
                    Bucket=bucket,
                    Key=output_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=accumulated
                )
                parts.append({'PartNumber': part_number, 'ETag': part['ETag']})
                part_number += 1
                accumulated = b""

        # Upload remaining data
        if accumulated:
            if not parts:
                # File is small enough for single put — abort multipart and use put_object
                s3.abort_multipart_upload(
                    Bucket=bucket, Key=output_key, UploadId=upload_id
                )
                s3.put_object(
                    Bucket=bucket, Key=output_key,
                    Body=accumulated, ContentType='text/csv'
                )
            else:
                part = s3.upload_part(
                    Bucket=bucket,
                    Key=output_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=accumulated
                )
                parts.append({'PartNumber': part_number, 'ETag': part['ETag']})
                s3.complete_multipart_upload(
                    Bucket=bucket,
                    Key=output_key,
                    UploadId=upload_id,
                    MultipartUpload={'Parts': parts}
                )
        else:
            s3.complete_multipart_upload(
                Bucket=bucket,
                Key=output_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )

    except Exception as e:
        s3.abort_multipart_upload(
            Bucket=bucket, Key=output_key, UploadId=upload_id
        )
        # Update meta with error
        meta = {'jobId': job_id, 'status': 'error', 'error': str(e)}
        s3.put_object(
            Bucket=bucket,
            Key=f"uploads/{job_id}/meta.json",
            Body=json.dumps(meta),
            ContentType='application/json'
        )
        raise

    # Generate presigned download URL (1 hour)
    download_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': output_key},
        ExpiresIn=3600
    )

    # Count total rows
    total_rows = sum(c['rowsProcessed'] for c in chunk_results)

    # Update meta with completion
    meta = {
        'jobId': job_id,
        'status': 'complete',
        'totalRows': total_rows,
        'resultKey': output_key,
        'downloadUrl': download_url
    }
    s3.put_object(
        Bucket=bucket,
        Key=f"uploads/{job_id}/meta.json",
        Body=json.dumps(meta),
        ContentType='application/json'
    )

    elapsed = time.time() - start
    print(f"[combiner] jobId={job_id} rows={total_rows} chunks={len(chunk_results)} duration={elapsed:.2f}s")

    return {
        'jobId': job_id,
        'status': 'complete',
        'totalRows': total_rows,
        'downloadUrl': download_url
    }
