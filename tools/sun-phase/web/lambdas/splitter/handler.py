"""
Step Functions: Splitter
Counts rows, enforces 2.5M limit, splits CSV into 50k-row chunks in S3.
"""

import json
import os
import io
import time

import boto3
import pandas as pd

DATA_BUCKET = os.environ['DATA_BUCKET']
CHUNK_SIZE = 50000
MAX_ROWS = 2_500_000
s3 = boto3.client('s3')


def lambda_handler(event, context):
    start = time.time()
    job_id = event['jobId']
    bucket = event['bucket']
    s3_key = event['s3Key']

    # Stream CSV and count rows + split
    resp = s3.get_object(Bucket=bucket, Key=s3_key)
    file_size = resp.get('ContentLength', 0)
    chunks = []
    total_rows = 0
    chunk_index = 0

    reader = pd.read_csv(resp['Body'], chunksize=CHUNK_SIZE, low_memory=False)

    for chunk_df in reader:
        total_rows += len(chunk_df)

        if total_rows > MAX_ROWS:
            # Update meta with error
            meta = {
                'jobId': job_id,
                'status': 'error',
                'error': f'CSV has more than {MAX_ROWS:,} rows. Maximum allowed is {MAX_ROWS:,}.'
            }
            s3.put_object(
                Bucket=bucket,
                Key=f"uploads/{job_id}/meta.json",
                Body=json.dumps(meta),
                ContentType='application/json'
            )
            raise ValueError(f"Row limit exceeded: {total_rows:,} > {MAX_ROWS:,}")

        # Write chunk to S3
        chunk_key = f"uploads/{job_id}/chunks/chunk_{chunk_index:04d}.csv"
        csv_buffer = io.StringIO()
        chunk_df.to_csv(csv_buffer, index=False)
        s3.put_object(
            Bucket=bucket,
            Key=chunk_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        chunks.append({
            'chunkKey': chunk_key,
            'chunkIndex': chunk_index,
            'rowCount': len(chunk_df)
        })
        chunk_index += 1

    # Update meta with chunk info
    meta = {
        'jobId': job_id,
        'status': 'processing',
        'totalRows': total_rows,
        'totalChunks': len(chunks)
    }
    s3.put_object(
        Bucket=bucket,
        Key=f"uploads/{job_id}/meta.json",
        Body=json.dumps(meta),
        ContentType='application/json'
    )

    elapsed = time.time() - start
    print(f"[splitter] jobId={job_id} rows={total_rows} chunks={len(chunks)} fileSize={file_size} duration={elapsed:.2f}s")

    return {
        'jobId': job_id,
        'bucket': bucket,
        'columns': event['columns'],
        'chunks': chunks,
        'totalRows': total_rows
    }
