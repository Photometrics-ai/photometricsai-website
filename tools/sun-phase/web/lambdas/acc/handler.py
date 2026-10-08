"""
ACC Street Light Value - API and Step Functions handlers (one module, one Lambda per handler).

Upload and status reuse the Phase Calculator's generic upload_initiator / status_api (same
uploads/<jobId>/ layout and meta.json status channel). Everything ACC-specific is here:

    detect      POST /api/acc/detect-columns  {jobId} -> {columns, detected}
    start       POST /api/acc/start           {jobId, columns} -> starts the state machine
    split       SFN: input.csv -> chunks/chunk_NNNN.csv (text preserved, CHUNK_ROWS rows each)
    chunk       SFN: value one chunk -> processed/chunk_NNNN.csv + small summary
    combine     SFN: concatenate processed chunks -> result.csv, summary into meta.json
    mark_failed SFN catch: meta.json status=error so the UI stops polling

Valuation is acc_core (layer). Lights outside PG&E/SCE/SDG&E, in combos the ACC model doesn't
offer, or with invalid inputs get no value and are left out of result.csv; meta.summary counts them.
The schedule (dimming, 1-5 AM deep dim, photocell offsets, one fixture per row) is fixed at
acc_core.DEFAULTS, the Photometrics AI schedule being valued; uploads supply only location and wattage.
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
OPTIONAL = ('ref_id',)
LIMITS = {  # inclusive valid ranges for numeric inputs
    'lat': (-90, 90), 'lon': (-180, 180), 'baseline_w': (0.001, 100_000), 'fixture_count': (0.001, 10_000),
    'dim_pct': (0, 100), 'deep_dim_pct': (0, 100), 'pc_on_offset_min': (0, 240), 'pc_off_offset_min': (0, 240),
}
PATTERNS = {
    'ref_id': r'^(ref_?id|id|object_?id|fid|pole_?(id|no|num(ber)?)|asset_?id|light_?id|streetlight_?id)$',
    'lat': r'^(lat|latitude|y|lat_?dd|point_?y)$',
    'lon': r'^(lon|lng|long|longitude|x|lon_?dd|point_?x)$',
    'baseline_w': r'^(baseline_?w|watts?|wattage|input_?watts?|lamp_?watts?|fixture_?watts?|power_?w|kw?)$',
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


def validate_start(columns):
    """Returns (error, columns). Only location/wattage/ID columns are kept; schedule settings are fixed."""
    for f in REQUIRED:
        if not columns.get(f):
            return f'columns.{f} is required', None
    return None, {k: v for k, v in columns.items() if k in REQUIRED + OPTIONAL and v}


def start(event, context):
    body = json.loads(event.get('body') or '{}')
    job_id = body.get('jobId')
    if not _valid_job_id(job_id):
        return _resp(400, {'error': 'jobId is required'})
    err, columns = validate_start(body.get('columns') or {})
    defaults = dict(acc_core.DEFAULTS)
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
    """Parse mapped columns -> dict of float arrays; unmapped fields (the fixed schedule) take the default."""
    vals, bad = {}, np.zeros(n, dtype=bool)
    for f in REQUIRED + tuple(acc_core.DEFAULTS):
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


def value_frame(df, columns, defaults, row_offset=0):
    """Value every row of a text DataFrame.

    Returns (output DataFrame of valued rows, summary, points). points has one entry per row with
    plottable coordinates, valued or not, for the results map: [lat, lon, zone or drop reason, $/yr, id].
    """
    n = len(df)
    v, bad = _numeric(df, columns, defaults, n)
    zones = np.full(n, None, dtype=object)
    notes = np.full(n, '', dtype=object)
    ok_idx = np.flatnonzero(~bad)
    if len(ok_idx):
        zones[ok_idx], notes[ok_idx] = acc_core.zone_at(v['lat'][ok_idx], v['lon'][ok_idx])
    ids = (df[columns['ref_id']].astype(str).to_numpy() if 'ref_id' in columns
           else np.array([f'row {row_offset + i + 1}' for i in range(n)]))
    plottable = (np.isfinite(v['lat']) & np.isfinite(v['lon']) & (np.abs(v['lat']) <= 90) & (np.abs(v['lon']) <= 180))
    point_of = {}  # row index -> [zone or drop reason, value]

    drops = dict.fromkeys(DROP_REASONS, 0)
    drops['invalid_input'] = int(bad.sum())
    for i in np.flatnonzero(bad):
        point_of[i] = ['invalid_input', None]
    tw_cache, kw_cache = {}, {}
    rows, keep = [], []
    comp_sum = {}
    for i in ok_idx:
        lat, lon = v['lat'][i], v['lon'][i]
        status, iou, cz = acc_core.acc_zone_key(zones[i], lat, lon)
        if status != 'ok':
            drops[status] += 1
            point_of[i] = [status, None]
            continue
        tk = (lat, lon) if TWILIGHT_DP is None else (round(lat, TWILIGHT_DP), round(lon, TWILIGHT_DP))
        if tk not in tw_cache:
            tw_cache[tk] = acc_core.twilight_minutes(*tk)
        if tw_cache[tk] is None:
            drops['invalid_input'] += 1
            point_of[i] = ['invalid_input', None]
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
        point_of[i] = [f'{iou} {cz}', round(r['acc_value'], 2)]
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
    points = [[round(float(v['lat'][i]), 6), round(float(v['lon'][i]), 6), *point_of[i], ids[i]]
              for i in range(n) if plottable[i] and i in point_of]
    return out, summary, points


def chunk(event, context):
    t0 = time.time()
    bucket = event['bucket']
    df = _read_text_csv(s3.get_object(Bucket=bucket, Key=event['chunkKey'])['Body'])
    out, summary, points = value_frame(df, event['columns'], event['defaults'],
                                       row_offset=event['chunkIndex'] * CHUNK_ROWS)
    out_key = event['chunkKey'].replace('/chunks/', '/processed/')
    s3.put_object(Bucket=bucket, Key=out_key, Body=out.to_csv(index=False, lineterminator='\n'),
                  ContentType='text/csv')
    points_key = out_key.replace('/processed/', '/points/').replace('.csv', '.json')
    s3.put_object(Bucket=bucket, Key=points_key, Body=json.dumps(points, separators=(',', ':')),
                  ContentType='application/json')
    print(f'[acc-chunk] jobId={event["jobId"]} chunk={event["chunkIndex"]} rows={len(df)} valued={summary["valued"]} '
          f'locations={summary["twilightLocations"]} duration={time.time() - t0:.2f}s')
    return {'chunkIndex': event['chunkIndex'], 'outputKey': out_key, 'pointsKey': points_key,
            'rowsProcessed': len(df), 'summary': summary}


def _clip_ring(xy, box):
    """Sutherland-Hodgman clip of one ring (list of (x, y)) to box = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    pts = list(xy)
    for inside, cross in edges:
        if not pts:
            break
        out, prev = [], pts[-1]
        for cur in pts:
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
        pts = out
    return pts


def _padded(lat, lon, pad, min_pad):
    span = max(lon.max() - lon.min(), lat.max() - lat.min())  # square-ish padding: the map is not the extent's shape
    p = max(span * pad, min_pad)
    return (lon.min() - p, lat.min() - p, lon.max() + p, lat.max() + p)


def zone_outlines(points):
    """ACC zone polygons clipped to a padded box around the plotted lights, as GeoJSON for the results map.
    Returns (feature collection, view bounds). The map can't pan past the view bounds, which sit well inside
    the clip box, so the clip box's straight edges never show as zone boundaries."""
    if not points:
        return {'type': 'FeatureCollection', 'features': []}, None
    lat = np.array([p[0] for p in points])
    lon = np.array([p[1] for p in points])
    view = _padded(lat, lon, 1.0, 0.05)
    box = _padded(lat, lon, 2.0, 0.15)
    codes, poly_zone, _, poly_bbox, _ = acc_core.load_zones()
    d = np.load(acc_core.DATA_DIR / 'acc2026_zones.npz')
    rs, coords, ring_poly = d['ring_start'], d['coords'], d['ring_poly']
    features = []
    for p in range(len(poly_zone)):
        bx0, by0, bx1, by1 = poly_bbox[p]
        if poly_zone[p] < 0 or bx1 < box[0] or bx0 > box[2] or by1 < box[1] or by0 > box[3]:
            continue
        rings = []
        for r in np.flatnonzero(ring_poly == p):
            clipped = _clip_ring(coords[rs[r]:rs[r + 1], :2].tolist(), box)  # stored rings carry a zero Z
            if len(clipped) >= 3:
                rings.append([[round(x, 5), round(y, 5)] for x, y in clipped + [clipped[0]]])
        if rings:
            iou, cz = codes[poly_zone[p]].split('_CZ')
            features.append({'type': 'Feature', 'properties': {'zone': f'{acc_core.IOU[iou]} CZ{int(cz)}'},
                             'geometry': {'type': 'Polygon', 'coordinates': rings}})
    return {'type': 'FeatureCollection', 'features': features}, [round(b, 5) for b in view]


def by_zone(df):
    """Valued lights per utility / ACC climate zone, largest first: each combination has its own hourly prices."""
    num = df[['acc_value', 'acc_value_summer', 'kwh_saved']].astype(float)
    g = num.assign(acc_iou=df['acc_iou'], acc_cz=df['acc_cz']).groupby(['acc_iou', 'acc_cz'])
    out = [{'iou': iou, 'cz': cz, 'lights': int(len(z)), 'acc_value_total': float(z.acc_value.sum()),
            'acc_value_median': float(z.acc_value.median()), 'acc_value_summer_total': float(z.acc_value_summer.sum()),
            'kwh_saved_total': float(z.kwh_saved.sum())}
           for (iou, cz), z in g]
    return sorted(out, key=lambda r: (-r['lights'], r['iou'], r['cz']))


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
        'by_zone': by_zone(df) if valued else [],
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
    points = []
    for c in results:
        points.extend(json.loads(s3.get_object(Bucket=bucket, Key=c['pointsKey'])['Body'].read()))
    outlines, box = zone_outlines(points)
    map_key = f'uploads/{job_id}/map.json'
    s3.put_object(Bucket=bucket, Key=map_key, ContentType='application/json',
                  Body=json.dumps({'points': points, 'zones': outlines, 'bounds': box}, separators=(',', ':')))
    map_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': map_key}, ExpiresIn=3600)
    total_rows = sum(c['rowsProcessed'] for c in results)
    _put_meta(bucket, job_id, {'jobId': job_id, 'status': 'complete', 'tool': 'acc', 'totalRows': total_rows,
                               'resultKey': out_key, 'downloadUrl': url, 'mapUrl': map_url, 'summary': summary})
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
