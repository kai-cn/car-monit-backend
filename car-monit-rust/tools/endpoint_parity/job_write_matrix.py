# -*- coding: utf-8 -*-
"""/monitor/job 写入端点的 Java 语义矩阵：两端逐条对比请求与落库结果。

覆盖 `docs/03-INTERFACE-VERIFICATION.md` §7.3 里实测到的每一条分支：null cron 与空串
走不同文案、insertJob 强制 status='1'、misfire 非法回滚、never-fire 不回滚、
changeStatus/run/remove 的 NPE 与 SchedulerException、Long[] 路径变量绑定失败。

用法（两端已启动）：
    PARITY_USER=admin PARITY_PASSWORD=xxx python -m tools.endpoint_parity.job_write_matrix
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')

VALID = '0 0 2 ? * *'
NEVER_FIRE = '0 0 2 1 1 ? 1969'


def normalize(value):
    if not isinstance(value, str):
        return value
    return re.sub(r'TASK_CLASS_NAME\d+', 'TASK_CLASS_NAME{id}', value)


def call(method, base, token, path, body=None):
    _, _, raw = http(method, base + path, token=token, body=body, timeout=90)
    try:
        return normalize(json.loads(raw).get('msg'))
    except Exception:
        return 'NON-JSON %s' % raw[:120].decode('utf-8', 'replace')


def row_of(base, token, name):
    """按任务名读回库里那一行（端点走 Java/Rust 自己的 list），没有则 None。"""
    _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
    try:
        rows = (json.loads(raw) or {}).get('rows') or []
    except Exception:
        return None
    if not rows:
        return None
    row = rows[0]
    return {k: row.get(k) for k in ('jobName', 'jobGroup', 'cronExpression', 'status',
                                    'misfirePolicy', 'concurrent', 'remark')}


def drop(base, token, name):
    _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
    try:
        rows = (json.loads(raw) or {}).get('rows') or []
    except Exception:
        rows = []
    for row in rows:
        http('DELETE', base + '/monitor/job/%s' % row['jobId'], token=token, timeout=60)


OMIT = object()


def create(base, token, name, body):
    """建一个任务，返回 (msg, 落库行)。调用方负责用完 drop。

    body 里给 OMIT 表示**连键都不发**（Java 的实体默认值只在字段缺席时生效，
    显式发 null 会被 Jackson 覆盖成 null）。
    """
    payload = {'jobName': name, 'jobGroup': 'DEFAULT',
               'invokeTarget': 'ryTask.ryNoParams', 'cronExpression': VALID,
               'misfirePolicy': '3', 'concurrent': '1', 'status': '1'}
    payload.update(body)
    payload = {k: v for k, v in payload.items() if v is not OMIT}
    msg = call('POST', base, token, '/monitor/job', payload)
    return msg, row_of(base, token, name)


def case_add_null_cron(base, token, name):
    return {'msg': call('POST', base, token, '/monitor/job',
                        {'jobName': name, 'jobGroup': 'DEFAULT', 'invokeTarget': 'ryTask.ryNoParams',
                         'misfirePolicy': '3', 'concurrent': '1', 'status': '1'}),
            'row': row_of(base, token, name)}


def case_add_empty_cron(base, token, name):
    return {'msg': call('POST', base, token, '/monitor/job',
                        {'jobName': name, 'jobGroup': 'DEFAULT', 'invokeTarget': 'ryTask.ryNoParams',
                         'cronExpression': '', 'misfirePolicy': '3', 'concurrent': '1', 'status': '1'}),
            'row': row_of(base, token, name)}


def case_add_bad_misfire(base, token, name):
    # Java: TaskException 是 RuntimeException -> @Transactional 回滚，库里不能留行。
    msg, row = create(base, token, name, {'misfirePolicy': '9'})
    return {'msg': msg, 'row': row}


def case_add_forces_pause(base, token, name):
    msg, row = create(base, token, name, {'status': '0'})
    return {'msg': msg, 'status': (row or {}).get('status')}


def case_add_default_misfire(base, token, name):
    """不给 misfirePolicy：Java 实体字段初值是 MISFIRE_DEFAULT("0")，落库也是 "0"。"""
    msg, row = create(base, token, name, {'misfirePolicy': OMIT})
    return {'msg': msg, 'misfire': (row or {}).get('misfire')}


def case_add_explicit_null_misfire(base, token, name):
    """显式发 null：Jackson 把初值覆盖成 null，Java 的 switch(null) 直接 NPE。"""
    msg, row = create(base, token, name, {'misfirePolicy': None})
    return {'msg': msg, 'row': row is not None}


def case_add_without_group(base, token, name):
    msg, row = create(base, token, name, {'jobGroup': None})
    return {'msg': msg, 'group': (row or {}).get('jobGroup')}


def case_add_never_fire_then_run(base, token, name):
    """Java: SchedulerException 是 checked -> 不回滚，行留在库里；再试 /run 看调度器认不认。"""
    msg, row = create(base, token, name, {'cronExpression': NEVER_FIRE})
    out = {'add': msg, 'row': row is not None}
    if row is not None:
        _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
        job_id = ((json.loads(raw) or {}).get('rows') or [{}])[0].get('jobId')
        out['run'] = call('PUT', base, token, '/monitor/job/run',
                          {'jobId': job_id, 'jobGroup': 'DEFAULT'})
    drop(base, token, name)
    return out


def case_edit_missing_id(base, token, name):
    return {'msg': call('PUT', base, token, '/monitor/job',
                        {'jobId': 999999, 'jobName': name, 'jobGroup': 'DEFAULT',
                         'invokeTarget': 'ryTask.ryNoParams', 'cronExpression': VALID,
                         'misfirePolicy': '3', 'concurrent': '1', 'status': '1'})}


def case_edit_no_status(base, token, name):
    """Java: createScheduleJob 末尾 getStatus().equals(PAUSE)，status 为 null 直接 NPE。"""
    msg, row = create(base, token, name, {})
    job_id = (row or {}).get('jobName') and _id_of(base, token, name)
    body = {'jobId': job_id, 'jobName': name, 'jobGroup': 'DEFAULT',
            'invokeTarget': 'ryTask.ryNoParams', 'cronExpression': VALID, 'misfirePolicy': '3',
            'concurrent': '1'}
    out = {'created': msg, 'edit': call('PUT', base, token, '/monitor/job', body)}
    drop(base, token, name)
    return out


def _id_of(base, token, name):
    _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
    rows = (json.loads(raw) or {}).get('rows') or []
    return rows[0]['jobId'] if rows else None


def case_change_status_missing(base, token, name):
    return {'msg': call('PUT', base, token, '/monitor/job/changeStatus', {'jobId': 999999, 'status': '0'})}


def case_change_status_unknown_value(base, token, name):
    _, row = create(base, token, name, {})
    job_id = _id_of(base, token, name)
    before = (row or {}).get('status')
    msg = call('PUT', base, token, '/monitor/job/changeStatus', {'jobId': job_id, 'status': '2'})
    after = (row_of(base, token, name) or {}).get('status')
    drop(base, token, name)
    return {'msg': msg, 'before': before, 'after': after}


def case_change_status_toggle(base, token, name):
    _, _ = create(base, token, name, {})
    job_id = _id_of(base, token, name)
    msg = call('PUT', base, token, '/monitor/job/changeStatus', {'jobId': job_id, 'status': '0'})
    after = (row_of(base, token, name) or {}).get('status')
    drop(base, token, name)
    return {'msg': msg, 'after': after}


def case_run_missing(base, token, name):
    return {'msg': call('PUT', base, token, '/monitor/job/run', {'jobId': 999999, 'jobGroup': 'DEFAULT'})}


def case_run_paused(base, token, name):
    """Java 启动时把**全部**行装进调度器（暂停的也在），所以暂停任务照样能立即执行。"""
    _, _ = create(base, token, name, {'status': '1'})
    job_id = _id_of(base, token, name)
    msg = call('PUT', base, token, '/monitor/job/run', {'jobId': job_id, 'jobGroup': 'DEFAULT'})
    time.sleep(2.0)
    _, _, raw = http('GET', base + '/monitor/jobLog/list?jobName=' + name, token=token, timeout=60)
    logs = (json.loads(raw) or {}).get('rows') or []
    for log in logs:
        http('DELETE', base + '/monitor/jobLog/%s' % log['jobLogId'], token=token, timeout=60)
    drop(base, token, name)
    return {'msg': msg, 'logs': len(logs)}


def case_remove_missing(base, token, name):
    return {'msg': call('DELETE', base, token, '/monitor/job/999999')}


def case_remove_type_mismatch(base, token, name):
    return {'msg': call('DELETE', base, token, '/monitor/job/abc')}


def case_get_info_missing(base, token, name):
    _, _, raw = http('GET', base + '/monitor/job/999999', token=token, timeout=60)
    try:
        body = json.loads(raw)
    except Exception:
        return {'raw': raw[:80]}
    return {'hasData': 'data' in body, 'msg': normalize(body.get('msg')), 'code': body.get('code')}


CASES = [
    ('add 缺 cronExpression', case_add_null_cron),
    ('add 空串 cron', case_add_empty_cron),
    ('add misfire 非法（应回滚）', case_add_bad_misfire),
    ('add 强制 status=1', case_add_forces_pause),
    ('add 不给 misfire（实体默认 0）', case_add_default_misfire),
    ('add 显式 null misfire（Java NPE）', case_add_explicit_null_misfire),
    ('add 不给 jobGroup（落 DEFAULT）', case_add_without_group),
    ('add 永不触发（不回滚）+ run', case_add_never_fire_then_run),
    ('edit 不存在的 jobId', case_edit_missing_id),
    ('edit 不带 status', case_edit_no_status),
    ('changeStatus 不存在的 jobId', case_change_status_missing),
    ('changeStatus 非法 status（不改库）', case_change_status_unknown_value),
    ('changeStatus 0（恢复）', case_change_status_toggle),
    ('run 不存在的 jobId', case_run_missing),
    ('run 暂停中的任务', case_run_paused),
    ('remove 不存在的 jobId', case_remove_missing),
    ('remove 路径变量非数字', case_remove_type_mismatch),
    ('getInfo 不存在的 jobId（无 data 键）', case_get_info_missing),
]


def main() -> int:
    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    bad = 0
    for index, (label, fn) in enumerate(CASES):
        name = 'parity-write-%d' % index
        a = fn(JAVA, tj, name)
        drop(JAVA, tj, name)
        b = fn(RUST, tr, name)
        drop(RUST, tr, name)
        same = a == b
        bad += 0 if same else 1
        print(('==' if same else '!=') + '  ' + label)
        print('    java: ' + json.dumps(a, ensure_ascii=False))
        if not same:
            print('    rust: ' + json.dumps(b, ensure_ascii=False))
    print('\n不一致 %d / %d' % (bad, len(CASES)))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
