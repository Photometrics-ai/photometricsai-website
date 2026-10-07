"""
ACC Street Light Value - API and Step Functions handlers (one module, one Lambda per handler).

Upload and status reuse the Phase Calculator's generic upload_initiator / status_api (same
uploads/<jobId>/ layout and meta.json status channel). Everything ACC-specific is here:

    detect      POST /api/acc/detect-columns  {jobId} -> {columns, detected}
    start       POST /api/acc/start           {jobId, columns, defaults} -> starts the state machine
    split       SFN: input.csv -> chunks/chunk_NNNN.csv (text preserved, CHUNK_ROWS rows each)
    chunk       SFN: value one chunk -> processed/chunk_NNNN.csv + small summary
    combine     SFN: concatenate processed chunks -> result.csv, summary into meta.json
    mark_failed SFN catch: meta.json status=error so the UI stops polling

Valuation is acc_core (layer). Lights outside PG&E/SCE/SDG&E, in combos the ACC model doesn't
offer, or with invalid inputs get no value and are left out of result.csv; meta.summary counts them.
"""

import csv
import io
import json
import os
import re
import time

import boto3
import numpy as np
import pandas as pd

import acc_core

DATA_BUCKET = os.environ.get('DATA_BUCKET', '')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')
# Measured (tools/acc-value/README.md, "Performance"): ~144 ms twilight per unique location + ~34 ms
# valuation per light. 1,000 all-unique rows ~ 3 min locally, < 5 min on Lambda; 50k rows = 50 chunks.
CHUNK_ROWS = 1000
MAX_ROWS = 50_000
# Twilight is cached per lat/lon rounded to 3 dp (~110 m): on the 210 prototype points this changes
# acc_value by at most $0.00087 and no value at the cent. None = exact coordinates.
TWILIGHT_DP = 3

s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')

REQUIRED = ('lat', 'lon', 'baseline_w')
OPTIONAL = ('ref_id', 'fixture_count', 'dim_pct', 'deep_dim_pct', 'pc_on_offset_min', 'pc_off_offset_min')
LIMITS = {  # inclusive valid ranges for numeric inputs
    'lat': (-90, 90), 'lon': (-180, 180), 'baseline_w': (0.001, 100_000), 'fixture_count': (0.001, 10_000),
    'dim_pct': (0, 100), 'deep_dim_pct': (0, 100), 'pc_on_offset_min': (0, 240), 'pc_off_offset_min': (0, 240),
}
PATTERNS = {
    'ref_id': r'^(ref_?id|id|object_?id|fid|pole_?(id|no|num(ber)?)|asset_?id|light_?id|streetlight_?id)$',
    'lat': r'^(lat|latitude|y|lat_?dd|point_?y)$',
    'lon': r'^(lon|lng|long|longitude|x|lon_?dd|point_?x)$',
    'baseline_w': r'^(baseline_?w|watts?|wattage|input_?watts?|lamp_?watts?|fixture_?watts?|power_?w|kw?)$',
    'fixture_count': r'^(fixture_?count|fixtures|heads|count|qty|quantity)$',
    'dim_pct': r'^dim_?pct$',
    'deep_dim_pct': r'^deep_?dim_?pct$',
    'pc_on_offset_min': r'^pc_?on_?offset(_?min)?$',
    'pc_off_offset_min': r'^pc_?off_?offset(_?min)?$',
}
DROP_REASONS = (acc_core.OUTSIDE, acc_core.NO_ZONE, acc_core.INVALID_COMBO, 'invalid_input')
OUT_FIELDS = ['acc_note'] + acc_core.RESULT_FIELDS


def _resp(code, body):
    return {'statusCode': code, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(body)}


def _put_meta(bucket, job_id, meta):
    s3.put_object(Bucket=bucket, Key=f'uploads/{job_id}/meta.json', Body=json.dumps(meta),
                  ContentType='application/json')


def _valid_job_id(job_id):
    return bool(job_id) and re.fullmatch(r'[0-9a-f-]{36}', job_id) is not None


# ---------------------------------------------------------------- API

def detect_columns(columns):
    found = {}
    for field, pat in PATTERNS.items():
        for c in columns:
            if re.match(pat, c.strip().lower()) and c not in found.values():
                found[field] = c
                break
    return found


def detect(event, context):
    body = json.loads(event.get('body') or '{}')
    job_id = body.get('jobId')
    if not _valid_job_id(job_id):
        return _resp(400, {'error': 'jobId is required'})
    try:
        head = s3.get_object(Bucket=DATA_BUCKET, Key=f'uploads/{job_id}/input.csv', Range='bytes=0-65535')
        text = head['Body'].read().decode('utf-8-sig', errors='replace')
    except s3.exceptions.NoSuchKey:
        return _resp(404, {'error': 'CSV not found. Upload may not be complete.'})
    columns = next(csv.reader(io.StringIO(text)), [])
    columns = [c.strip() for c in columns]
    detected = detect_columns(columns)
    print(f'[acc-detect] jobId={job_id} columns={len(columns)} detected={detected}')
    return _resp(200, {'columns': columns, 'detected': detected, 'defaults': acc_core.DEFAULTS})


def validate_start(columns, defaults):
    """Returns (error, columns, defaults) with defaults merged over acc_core.DEFAULTS."""
    for f in REQUIRED:
        if not columns.get(f):
            return f'columns.{f} is required', None, None
    columns = {k: v for k, v in columns.items() if k in REQUIRED + OPTIONAL and v}
    merged = dict(acc_core.DEFAULTS)
    for k, v in (defaults or {}).items():
        if k not in acc_core.DEFAULTS:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            return f'defaults.{k} must be a number', None, None
        lo, hi = LIMITS[k]
        if not lo <= v <= hi:
            return f'defaults.{k} must be between {lo} and {hi}', None, None
        merged[k] = v
    return None, columns, merged


def start(event, context):
    body = json.loads(event.get('body') or '{}')
    job_id = body.get('jobId')
    if not _valid_job_id(job_id):
        return _resp(400, {'error': 'jobId is required'})
    err, columns, defaults = validate_start(body.get('columns') or {}, body.get('defaults'))
    if err:
        return _resp(400, {'error': err})
    s3_key = f'uploads/{job_id}/input.csv'
    try:
        s3.head_object(Bucket=DATA_BUCKET, Key=s3_key)
    except Exception:
        return _resp(404, {'error': 'CSV not found. Upload may not be complete.'})
    _put_meta(DATA_BUCKET, job_id, {'jobId': job_id, 'status': 'processing', 'tool': 'acc'})
    sfn.start_execution(stateMachineArn=STATE_MACHINE_ARN, name=job_id, input=json.dumps(
        {'jobId': job_id, 'bucket': DATA_BUCKET, 's3Key': s3_key, 'columns': columns, 'defaults': defaults}))
    print(f'[acc-start] jobId={job_id} columns={columns} defaults={defaults}')
    return _resp(200, {'jobId': job_id, 'status': 'processing'})


# ---------------------------------------------------------------- Step Functions

def _read_text_csv(body):
    return pd.read_csv(body, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def split(event, context):
    t0 = time.time()
    job_id, bucket = event['jobId'], event['bucket']
    obj = s3.get_object(Bucket=bucket, Key=event['s3Key'])
    df = _read_text_csv(obj['Body'])
    missing = [c for c in event['columns'].values() if c not in df.columns]
    if missing:
        raise ValueError(f'Columns not found in CSV: {", ".join(missing)}')
    if len(df) > MAX_ROWS:
        raise ValueError(f'CSV has {len(df):,} rows. Maximum allowed is {MAX_ROWS:,}.')
    if not len(df):
        raise ValueError('CSV has no data rows.')
    chunks = []
    for i, start_row in enumerate(range(0, len(df), CHUNK_ROWS)):
        key = f'uploads/{job_id}/chunks/chunk_{i:04d}.csv'
        part = df.iloc[start_row:start_row + CHUNK_ROWS]
        s3.put_object(Bucket=bucket, Key=key, Body=part.to_csv(index=False, lineterminator='\n'),
                      ContentType='text/csv')
        chunks.append({'chunkKey': key, 'chunkIndex': i, 'rowCount': len(part)})
    _put_meta(bucket, job_id, {'jobId': job_id, 'status': 'processing', 'tool': 'acc',
                               'totalRows': len(df), 'totalChunks': len(chunks)})
    print(f'[acc-split] jobId={job_id} rows={len(df)} chunks={len(chunks)} duration={time.time() - t0:.2f}s')
    return {'jobId': job_id, 'bucket': bucket, 'columns': event['columns'], 'defaults': event['defaults'],
            'chunks': chunks, 'totalRows': len(df)}


def _numeric(df, columns, defaults, n):
    """Parse mapped columns -> dict of float arrays; blank optional cells take the default."""
    vals, bad = {}, np.zeros(n, dtype=bool)
    for f in REQUIRED + OPTIONAL[1:]:
        if f in columns:
            raw = df[columns[f]].str.strip()
            v = pd.to_numeric(raw, errors='coerce').to_numpy(dtype=np.float64)
            if f in acc_core.DEFAULTS:
                v = np.where(raw == '', defaults[f], v)
        else:
            v = np.full(n, defaults[f], dtype=np.float64)
        lo, hi = LIMITS[f]
        bad |= ~np.isfinite(v) | (v < lo) | (v > hi)
        vals[f] = v
    return vals, bad


def value_frame(df, columns, defaults):
    """Value every row of a text DataFrame. Returns (output DataFrame of valued rows, summary)."""
    n = len(df)
    v, bad = _numeric(df, columns, defaults, n)
    zones = np.full(n, None, dtype=object)
    notes = np.full(n, '', dtype=object)
    ok_idx = np.flatnonzero(~bad)
    if len(ok_idx):
        zones[ok_idx], notes[ok_idx] = acc_core.zone_at(v['lat'][ok_idx], v['lon'][ok_idx])

    drops = dict.fromkeys(DROP_REASONS, 0)
    drops['invalid_input'] = int(bad.sum())
    tw_cache, kw_cache = {}, {}
    rows, keep = [], []
    comp_sum = {}
    for i in ok_idx:
        lat, lon = v['lat'][i], v['lon'][i]
        status, iou, cz = acc_core.acc_zone_key(zones[i], lat, lon)
        if status != 'ok':
            drops[status] += 1
            continue
        tk = (lat, lon) if TWILIGHT_DP is None else (round(lat, TWILIGHT_DP), round(lon, TWILIGHT_DP))
        if tk not in tw_cache:
            tw_cache[tk] = acc_core.twilight_minutes(*tk)
        if tw_cache[tk] is None:
            drops['invalid_input'] += 1
            continue
        s = tuple(float(v[f][i]) for f in ('dim_pct', 'deep_dim_pct', 'pc_on_offset_min', 'pc_off_offset_min'))
        kk = (tk, iou, cz, s)
        if kk not in kw_cache:
            kw_cache[kk] = acc_core.value_per_kw(*tw_cache[tk], iou, cz, *s)
        per_kw, comp = kw_cache[kk]
        kw = v['baseline_w'][i] / 1000 * v['fixture_count'][i]
        r = acc_core.scale(per_kw, kw, iou, cz)
        r['acc_note'] = notes[i]
        rows.append(r)
        keep.append(i)
        for k, c in comp.items():
            comp_sum[k] = comp_sum.get(k, 0.0) + c * kw

    out = df.iloc[keep].reset_index(drop=True)
    out.columns = [f'{c}_input' if c in OUT_FIELDS else c for c in out.columns]
    res = pd.DataFrame(rows, columns=OUT_FIELDS)
    num = [c for c in acc_core.RESULT_FIELDS if c not in ('acc_iou', 'acc_cz')]
    res[num] = res[num].astype(float).round(4)
    out = pd.concat([out, res], axis=1)
    summary = {'drops': drops, 'valued': len(keep), 'components': comp_sum,
               'twilightLocations': len(tw_cache), 'valuations': len(kw_cache)}
    return out, summary


def chunk(event, context):
    t0 = time.time()
    bucket = event['bucket']
    df = _read_text_csv(s3.get_object(Bucket=bucket, Key=event['chunkKey'])['Body'])
    out, summary = value_frame(df, event['columns'], event['defaults'])
    out_key = event['chunkKey'].replace('/chunks/', '/processed/')
    s3.put_object(Bucket=bucket, Key=out_key, Body=out.to_csv(index=False, lineterminator='\n'),
                  ContentType='text/csv')
    print(f'[acc-chunk] jobId={event["jobId"]} chunk={event["chunkIndex"]} rows={len(df)} valued={summary["valued"]} '
          f'locations={summary["twilightLocations"]} duration={time.time() - t0:.2f}s')
    return {'chunkIndex': event['chunkIndex'], 'outputKey': out_key, 'rowsProcessed': len(df), 'summary': summary}


def summarize(frames, chunk_summaries):
    """Job summary from the combined valued rows and the per-chunk drop/component tallies."""
    drops = dict.fromkeys(DROP_REASONS, 0)
    comps = {}
    for s in chunk_summaries:
        for k, c in s['drops'].items():
            drops[k] += c
        for k, c in s['components'].items():
            comps[k] = comps.get(k, 0.0) + c
    df = pd.concat(frames) if frames else pd.DataFrame(columns=acc_core.RESULT_FIELDS)
    valued = len(df)
    vals = df['acc_value'].astype(float) if valued else pd.Series(dtype=float)
    total = float(vals.sum())
    out = {
        'valued': valued, 'dropped': drops,
        'acc_value_total': total,
        'acc_value_median': float(vals.median()) if valued else None,
        'acc_value_min': float(vals.min()) if valued else None,
        'acc_value_max': float(vals.max()) if valued else None,
        'acc_value_summer_total': float(df['acc_value_summer'].astype(float).sum()) if valued else 0.0,
        'acc_value_winter_total': float(df['acc_value_winter'].astype(float).sum()) if valued else 0.0,
        'acc_trim_total': float(df['acc_trim'].astype(float).sum()) if valued else 0.0,
        'acc_dim_total': float(df['acc_dim'].astype(float).sum()) if valued else 0.0,
        'kwh_saved_total': float(df['kwh_saved'].astype(float).sum()) if valued else 0.0,
        'kwh_base_total': float(df['kwh_base'].astype(float).sum()) if valued else 0.0,
        'component_share': {k: c / comps['total'] for k, c in comps.items() if k != 'total'}
        if comps.get('total') else {},
        'by_utility': df.groupby('acc_iou').size().to_dict() if valued else {},
        'with_overlap_note': int((df['acc_note'].fillna('') != '').sum()) if valued else 0,
        'acc': {k: acc_core.load_meta()[k] for k in ('acc_version', 'time_basis', 'seasons')},
    }
    return out


def combine(event, context):
    t0 = time.time()
    job_id, bucket = event['jobId'], event['bucket']
    results = sorted(event['chunkResults'], key=lambda c: c['chunkIndex'])
    buf = io.StringIO()
    frames = []
    for i, c in enumerate(results):
        text = s3.get_object(Bucket=bucket, Key=c['outputKey'])['Body'].read().decode('utf-8')
        buf.write(text if i == 0 else text.split('\n', 1)[1] if '\n' in text else '')
        frames.append(pd.read_csv(io.StringIO(text), usecols=acc_core.RESULT_FIELDS + ['acc_note'],
                                  keep_default_na=False, dtype={'acc_note': str}))
    frames = [f for f in frames if len(f)]
    summary = summarize(frames, [c['summary'] for c in results])
    out_key = f'uploads/{job_id}/result.csv'
    s3.put_object(Bucket=bucket, Key=out_key, Body=buf.getvalue().encode('utf-8'), ContentType='text/csv')
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': out_key}, ExpiresIn=3600)
    total_rows = sum(c['rowsProcessed'] for c in results)
    _put_meta(bucket, job_id, {'jobId': job_id, 'status': 'complete', 'tool': 'acc', 'totalRows': total_rows,
                               'resultKey': out_key, 'downloadUrl': url, 'summary': summary})
    print(f'[acc-combine] jobId={job_id} rows={total_rows} valued={summary["valued"]} '
          f'chunks={len(results)} duration={time.time() - t0:.2f}s')
    return {'jobId': job_id, 'status': 'complete', 'totalRows': total_rows}


def mark_failed(event, context):
    """Catch target: record the error so the status endpoint reports it instead of 'processing'."""
    job_id, bucket = event['jobId'], event['bucket']
    err = event.get('error') or {}
    cause = err.get('Cause', '')
    try:
        cause = json.loads(cause).get('errorMessage', cause)
    except (ValueError, AttributeError):
        pass
    msg = cause if err.get('Error') in ('ValueError',) else 'Processing failed. Please check the file and try again.'
    _put_meta(bucket, job_id, {'jobId': job_id, 'status': 'error', 'tool': 'acc', 'error': msg})
    print(f'[acc-failed] jobId={job_id} error={err.get("Error")} cause={cause[:500]}')
    return {'jobId': job_id, 'status': 'error'}
