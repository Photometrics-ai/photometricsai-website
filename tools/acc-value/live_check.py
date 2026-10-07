"""
Gate 4b: run a CSV through the deployed ACC endpoints and compare with a local run of the same handler code.

Usage:
    python tools/acc-value/live_check.py [BASE_URL] [CSV] [--live-only]
BASE_URL defaults to https://photometrics.ai/api (the Amplify /api/<*> rewrite); pass the API Gateway
stage URL + /api to bypass Amplify. CSV defaults to the 438-point fixture.
"""
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'tests'))


def call(method, url, body=None, headers=None):
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    h = {'Content-Type': 'application/json', **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw) if r.headers.get('Content-Type', '').startswith('application/json') else raw


def run_live(base, csv_bytes):
    t0 = time.time()
    up = call('POST', f'{base}/acc/upload', {})
    call('PUT', up['uploadUrl'], csv_bytes, {'Content-Type': 'text/csv'})
    det = call('POST', f'{base}/acc/detect-columns', {'jobId': up['jobId']})
    call('POST', f'{base}/acc/start', {'jobId': up['jobId'], 'columns': det['detected']})
    while True:
        time.sleep(5)
        st = call('GET', f'{base}/acc/status?jobId={up["jobId"]}')
        if st['status'] in ('complete', 'error'):
            break
    print(f'live job {up["jobId"]}: {st["status"]} in {time.time() - t0:.0f}s')
    if st['status'] != 'complete':
        raise SystemExit(f'live job failed: {st}')
    with urllib.request.urlopen(st['downloadUrl'], timeout=60) as r:
        return r.read(), st, det['detected']


def run_local(csv_bytes, columns):
    import test_handlers as th
    import importlib.util
    spec = importlib.util.spec_from_file_location('acc_handler', th.HANDLER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.s3, h.sfn, h.DATA_BUCKET = th.FakeS3(), th.FakeSFN(), 'bucket'
    job, meta, _ = th.run_job(h, csv_bytes.decode('utf-8'), columns)
    return h.s3.objects[meta['resultKey']], meta


def compare(live, local):
    """Same rows, same columns, text identical, numbers within 1e-4 (4-dp rounding ties can resolve
    differently between NumPy builds: Lambda/Linux vs the local machine)."""
    import pandas as pd
    a = pd.read_csv(io.BytesIO(live), dtype=str, keep_default_na=False)
    b = pd.read_csv(io.BytesIO(local), dtype=str, keep_default_na=False)
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False
    ties = 0
    for c in a.columns:
        if (a[c] == b[c]).all():
            continue
        x, y = pd.to_numeric(a[c], errors='coerce'), pd.to_numeric(b[c], errors='coerce')
        if x.isna().any() or y.isna().any() or ((x - y).abs() > 1e-4 + 1e-9).any():
            print(f'  column {c} differs')
            return False
        ties += int((a[c] != b[c]).sum())
    print(f'  {ties} cells differ only by a 4-dp rounding tie')
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    base = args[0] if args else 'https://photometrics.ai/api'
    if len(args) > 1:
        csv_bytes = Path(args[1]).read_bytes()
    else:
        from conftest import inputs
        csv_bytes = inputs().drop(columns=['Utility', 'ACC_ZONE']).to_csv(index=False).encode()
    live, st, cols = run_live(base, csv_bytes)
    if '--live-only' in sys.argv:  # load test: report the live summary without the (slow) local rerun
        print(json.dumps({k: v for k, v in st['summary'].items() if k != 'acc'}, indent=1))
        return
    local, meta = run_local(csv_bytes, cols)
    same = compare(live, local)
    print(f'result.csv matches local run: {same} ({len(live):,} bytes)')
    ls, ms = st['summary'], meta['summary']
    for k in ('valued', 'dropped', 'acc_value_total', 'acc_value_median'):
        print(f'  {k}: live={ls[k]} local={ms[k]}')
    if not same:
        raise SystemExit('MISMATCH')


if __name__ == '__main__':
    main()
