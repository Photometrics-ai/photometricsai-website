"""Gate 4a: ACC Lambda handlers end to end against in-memory fakes of S3 and Step Functions."""

import importlib.util
import io
import json
import uuid

import numpy as np
import pandas as pd
import pytest

from conftest import REPO, expected, inputs

HANDLER = REPO / 'tools' / 'sun-phase' / 'web' / 'lambdas' / 'acc' / 'handler.py'


class FakeS3:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType=None):
        self.objects[Key] = Body.encode('utf-8') if isinstance(Body, str) else Body

    def get_object(self, Bucket, Key, Range=None):
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey(Key)
        data = self.objects[Key]
        if Range:
            a, b = map(int, Range.split('=')[1].split('-'))
            data = data[a:b + 1]
        return {'Body': io.BytesIO(data), 'ContentLength': len(data)}

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey(Key)

    def generate_presigned_url(self, op, Params, ExpiresIn):
        return f'https://fake/{Params["Key"]}'

    def meta(self, job_id):
        return json.loads(self.objects[f'uploads/{job_id}/meta.json'])


class FakeSFN:
    def __init__(self):
        self.started = []

    def start_execution(self, stateMachineArn, name, input):
        self.started.append(json.loads(input))


@pytest.fixture
def h(monkeypatch):
    spec = importlib.util.spec_from_file_location('acc_handler', HANDLER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, 's3', FakeS3())
    monkeypatch.setattr(mod, 'sfn', FakeSFN())
    monkeypatch.setattr(mod, 'DATA_BUCKET', 'bucket')
    return mod


def run_job(h, csv_text, columns, defaults=None, chunk_rows=None, twilight_dp='default'):
    """Drive the whole flow the way API Gateway + the state machine would."""
    if chunk_rows:
        h.CHUNK_ROWS = chunk_rows
    if twilight_dp != 'default':
        h.TWILIGHT_DP = twilight_dp
    job = str(uuid.uuid4())
    h.s3.put_object('bucket', f'uploads/{job}/input.csv', csv_text)
    det = h.detect({'body': json.dumps({'jobId': job})}, None)
    assert det['statusCode'] == 200
    r = h.start({'body': json.dumps({'jobId': job, 'columns': columns, 'defaults': defaults})}, None)
    if r['statusCode'] != 200:
        return job, r, None
    ev = h.sfn.started[-1]
    try:
        sp = h.split(ev, None)
        results = [h.chunk({**{k: sp[k] for k in ('jobId', 'bucket', 'columns', 'defaults')}, **c}, None)
                   for c in sp['chunks']]
        h.combine({'jobId': job, 'bucket': 'bucket', 'chunkResults': results}, None)
    except Exception as e:
        h.mark_failed({'jobId': job, 'bucket': 'bucket',
                       'error': {'Error': type(e).__name__, 'Cause': json.dumps({'errorMessage': str(e)})}}, None)
    meta = h.s3.meta(job)
    result = None
    if meta['status'] == 'complete':
        result = pd.read_csv(io.BytesIO(h.s3.objects[meta['resultKey']]), dtype={'acc_note': str},
                             keep_default_na=False)
    return job, meta, result


def fixture_csv():
    pts = inputs()
    return pts.drop(columns=['Utility', 'ACC_ZONE']).to_csv(index=False)


def test_detect_columns(h):
    d = h.detect_columns(['REF_ID', 'latitude', 'longitude', 'baseline_w', 'fixture_count', 'dim_pct',
                          'deep_dim_pct', 'pc_on_offset_min', 'pc_off_offset_min'])
    assert d == {'ref_id': 'REF_ID', 'lat': 'latitude', 'lon': 'longitude', 'baseline_w': 'baseline_w'}
    assert h.detect_columns(['Pole No', 'Lat', 'Long', 'Watts'])['baseline_w'] == 'Watts'


@pytest.mark.parametrize('dp,tol', [(None, 1e-4 + 1e-9), (3, 0.001)])
def test_fixture_job_matches_core(h, dp, tol):
    """The 438-point fixture through split/chunk/combine (small chunks to exercise combining).
    Exact coordinates reproduce the prototype; the deployed 3 dp twilight cache stays under $0.001."""
    cols = h.detect_columns(list(inputs().columns))
    job, meta, res = run_job(h, fixture_csv(), cols, chunk_rows=100, twilight_dp=dp)
    assert meta['status'] == 'complete', meta
    s = meta['summary']
    assert s['valued'] == len(res)
    assert s['valued'] + sum(s['dropped'].values()) == 438
    assert s['dropped']['invalid_input'] == 0
    # every prototype-valued point is valued again, in the same zone (IOU wins overlaps), with the same value
    exp = expected().set_index('REF_ID')
    pts = inputs().set_index('REF_ID')
    res = res.set_index('REF_ID')
    n = 0
    for ref, e in exp[exp.acc_status == 'ok'].iterrows():
        r = res.loc[ref]
        assert (r.acc_iou, r.acc_cz) == (e.acc_iou, e.acc_cz)
        for k in ('acc_trim', 'acc_dim', 'acc_value'):
            assert abs(r[k] - e[k]) <= tol, (ref, k, r[k], e[k])
        if dp is None:
            for k in ('hrs_base', 'hrs_ctrl', 'kwh_saved'):
                assert abs(r[k] - e[k]) <= tol, (ref, k, r[k], e[k])
        n += 1
    assert n == 210
    assert round(s['acc_value_summer_total'] + s['acc_value_winter_total'], 2) == round(res.acc_value.sum(), 2)
    assert sum(s['component_share'].values()) == pytest.approx(1.0)
    # per utility/climate-zone breakdown agrees with the rows and adds up to the totals
    bz = {(z['iou'], z['cz']): z for z in s['by_zone']}
    grp = res.groupby(['acc_iou', 'acc_cz'])
    assert set(bz) == set(grp.groups)
    for k, g in grp:
        assert bz[k]['lights'] == len(g)
        assert bz[k]['acc_value_total'] == pytest.approx(g.acc_value.sum())
        assert bz[k]['acc_value_median'] == pytest.approx(g.acc_value.median())
    assert sum(z['lights'] for z in s['by_zone']) == s['valued']
    assert sum(z['acc_value_total'] for z in s['by_zone']) == pytest.approx(s['acc_value_total'])
    assert [z['lights'] for z in s['by_zone']] == sorted((z['lights'] for z in s['by_zone']), reverse=True)
    # input columns pass through untouched
    assert list(res.reset_index().columns[:len(pts.columns) - 1]) == [c for c in inputs().columns
                                                                       if c not in ('Utility', 'ACC_ZONE')]


def test_schedule_is_fixed(h):
    """Schedule columns in the file and settings sent by a client are ignored: every light gets the
    Photometrics AI schedule (acc_core.DEFAULTS)."""
    csv_text = 'id,lat,lon,watts,dim_pct\n1,36.7378,-119.7871,50,0\n2,36.7378,-119.7871,50,90\n'
    _, meta, res = run_job(h, csv_text, {'lat': 'lat', 'lon': 'lon', 'baseline_w': 'watts', 'dim_pct': 'dim_pct'},
                           defaults={'dim_pct': 90, 'pc_on_offset_min': 0})
    assert meta['status'] == 'complete' and len(res) == 2
    status, ref, _ = h.acc_core.value_light(36.7378, -119.7871, 50)
    assert res.acc_value.tolist() == [round(ref['acc_value'], 4)] * 2
    assert h.sfn.started[-1]['defaults'] == h.acc_core.DEFAULTS
    assert set(h.sfn.started[-1]['columns']) == {'lat', 'lon', 'baseline_w'}


def test_bad_rows_dropped_and_counted(h):
    csv_text = ('id,lat,lon,watts\n'
                'ok,36.7378,-119.7871,50\n'
                'nowatts,36.7378,-119.7871,\n'
                'text,36.7378,-119.7871,fifty\n'
                'badlat,96,-119.7871,50\n'
                'ocean,36.0,-125.5,50\n'
                'ladwp,34.0522,-118.2437,50\n'
                'sce_cz05,"34.566926426176146","-119.61390092622176",50\n')
    _, meta, res = run_job(h, csv_text, {'lat': 'lat', 'lon': 'lon', 'baseline_w': 'watts'})
    assert meta['status'] == 'complete'
    assert res.id.tolist() == ['ok']
    d = meta['summary']['dropped']
    assert d == {'invalid_input': 3, 'outside_acc_area': 1, 'no_acc_zone': 1, 'combo_not_in_acc_model': 1}


def test_text_columns_preserved(h):
    csv_text = 'pole,lat,lon,watts,acc_value\n007,36.7378,-119.7871,50,x\n'
    _, meta, _ = run_job(h, csv_text, {'lat': 'lat', 'lon': 'lon', 'baseline_w': 'watts'})
    out = h.s3.objects[meta['resultKey']].decode()
    header, row = out.splitlines()[:2]
    assert header.startswith('pole,lat,lon,watts,acc_value_input,acc_note,')
    assert row.startswith('007,36.7378,-119.7871,50,x,')


def test_start_validation(h):
    job = str(uuid.uuid4())
    h.s3.put_object('bucket', f'uploads/{job}/input.csv', 'a,b\n1,2\n')
    for cols, field in [({'lat': 'a', 'lon': 'b'}, 'baseline_w'), ({'lat': 'a', 'baseline_w': 'b'}, 'lon')]:
        r = h.start({'body': json.dumps({'jobId': job, 'columns': cols})}, None)
        assert r['statusCode'] == 400 and field in json.loads(r['body'])['error']
    assert h.start({'body': json.dumps({'jobId': '../x', 'columns': {}})}, None)['statusCode'] == 400


def test_failure_marks_meta_error(h):
    _, meta, _ = run_job(h, 'a,b,c\n1,2,3\n', {'lat': 'a', 'lon': 'b', 'baseline_w': 'missing'})
    assert meta['status'] == 'error' and 'missing' in meta['error']
    h.MAX_ROWS = 2
    _, meta, _ = run_job(h, 'a,b,c\n1,2,3\n1,2,3\n1,2,3\n', {'lat': 'a', 'lon': 'b', 'baseline_w': 'c'})
    assert meta['status'] == 'error' and 'Maximum' in meta['error']
