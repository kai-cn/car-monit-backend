# -*- coding: utf-8 -*-
"""`manager_crud!` 生成端点的写入对拍（POST -> 按 id 回读 -> DELETE）。

GET 全量矩阵只覆盖 297 条读接口，新增/修改/删除这条路径此前完全没测过
（`last_insert_id`、`importTable`、部门/用户 NPE、TIMESTAMP 会话时区四个缺陷都是在写入路径上发现的）。
本脚本按 `manager_crud!` 宏块自动推导每个表的 route/table/字段，逐表做一轮通用 CRUD 对拍：

1. 从 Java 侧 `{route}/list?pageSize=1` 取第一行当模板；空表用 `SEED_BODIES` 里的最小请求体；
2. 去掉主键、审计列与宏里 `null as xxx` 派生列，把首个可读文本列 + remark 打上唯一标记
   —— **两端标记不同**，因为两端写的是同一张表，标记相同会互相认领对方的行；
3. `POST {route}` 两端各一次，比 `msg`/`code`，`data` 只比有无；
4. 用 POST 返回的 id 调 `{route}/{id}` 回读，比落库内容（不比 id、时间戳、创建人、标记列）；
5. `DELETE {route}/{id}` 比 `msg`/`code`，再回读一次确认两端行为一致。

标记名会打印出来，收尾时用 SQL 硬删（DELETE 端点是软删，行仍留在库里）。

用法（两端已启动）：
    PARITY_USER=admin PARITY_PASSWORD=xxx python -m tools.endpoint_parity.write_crud_matrix
    ... write_crud_matrix --only whiteinfo --verbose   # 按 route 子串过滤
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')
STAMP = str(int(time.time()))[-6:]

#: 不进请求体的列：主键、审计、租户/权限相关与派生列。
SKIP_KEYS = {
    'id', 'createBy', 'createTime', 'updateBy', 'updateTime', 'delFlag', 'epsId',
    'tenantId', 'createInfo', 'sort', 'dataId', 'params', 'pageDomain',
}
#: 打标记时优先用的文本列（按顺序找第一个存在的）。
MARK_KEYS = ['remark', 'name', 'title', 'deptName', 'userName', 'nickName', 'carNo',
             'plateNo', 'ruleName', 'taskName', 'fileName', 'orgName', 'stationName',
             'backCol1', 'backCol2']
#: 列表为空的表：只给最小请求体（业务列全部可空，主键由 MyBatis-Plus 生成；
#: except_id/car_id 是 NOT NULL 无默认值，Java 也要求带上）。
SEED_BODIES = {
    'car_fee_record': {'carNo': '', 'exceptId': '', 'inTime': '2025-08-21 10:20:00',
                       'outTime': '2025-08-22 11:00:00', 'amount': 1.5},
    'car_route_detail': {'carNo': '', 'lastPassTime': '2025-08-21 10:20:00',
                         'nextPassTime': '2025-08-22 11:00:00'},
    'car_route_info': {'carNo': '', 'carId': '', 'startAddress': 'parity'},
    'car_split_record': {'carNo': '', 'inTime': '2025-08-21 10:20:00',
                         'outTime': '2025-08-22 11:00:00', 'amount': 1.5},
}


def crud_blocks():
    """从 src 里的 `manager_crud!` 宏块解析 route / table / 派生列。"""
    blocks = []
    for path in sorted(ROOT.glob('src/api/**/*.rs')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for match in re.finditer(r'manager_crud!\s*\{(.*?)\n\}', text, re.S):
            body = match.group(1)
            route = re.search(r'route:\s*"([^"]+)"', body)
            table = re.search(r'table:\s*"([^"]+)"', body)
            if not route or not table:
                continue
            select = re.search(r'select:\s*"((?:[^"\\]|\\.)*)"', body, re.S)
            derived = set()
            if select:
                clause = select.group(1).replace('\\\n', ' ')
                clause = re.sub(r'\\\s*', '', clause)
                derived = set(re.findall(r'\bas\s+([A-Za-z][A-Za-z0-9_]*)', clause))
                derived |= {name for name in re.findall(r'null\s+as\s+(\w+)', clause)}
                #: select 里以 t.列 出现过的实体字段，只有这些才真的是表列。
                real = set(re.findall(r'\bt\.([a-z0-9_]+)', clause))
            else:
                real = None
            blocks.append({
                'route': route.group(1),
                'table': table.group(1),
                'file': str(path.relative_to(ROOT)).replace('\\', '/'),
                'derived': {snake_to_camel(item) for item in derived},
                'columns': {snake_to_camel(item) for item in real} if real else None,
            })
    return blocks


def snake_to_camel(name):
    parts = name.split('_')
    return parts[0] + ''.join(part.title() for part in parts[1:])


def call(method, base, token, path, body=None):
    _, _, raw = http(method, base + path, token=token, body=body, timeout=90)
    try:
        return json.loads(raw)
    except Exception:
        return {'_raw': raw[:160].decode('utf-8', 'replace')}


def first_row(base, token, route):
    payload = call('GET', base, token, '%s/list?pageSize=1&pageNum=1' % route)
    rows = payload.get('rows') or []
    return rows[0] if rows else None


def by_id(base, token, route, row_id):
    payload = call('GET', base, token, '%s/%s' % (route, row_id))
    return payload.get('data')


def probe_body(template, block, mark):
    """把模板行改造成探针行：去掉主键/审计/派生列，打上唯一标记。"""
    columns = block['columns']
    seed = SEED_BODIES.get(block['table'])
    if template:
        body = {}
        for key, value in template.items():
            if key in SKIP_KEYS or key in block['derived']:
                continue
            if columns is not None and key not in columns:
                continue
            body[key] = value
    else:
        body = dict(seed or {})
    target = next((key for key in MARK_KEYS if key in body and isinstance(body[key], str)), None)
    if target is None:
        for key, value in body.items():
            if isinstance(value, str) and value:
                target = key
                break
    if target is None:
        return None, None
    body[target] = mark
    if 'remark' in body and target != 'remark':
        body['remark'] = mark
    return body, target


def comparable(row, marks):
    """只比稳定字段：id/时间戳/创建人/带标记的列两端必然不同。"""
    if not row:
        return None
    return {key: value for key, value in sorted(row.items())
            if key not in ('id', 'createTime', 'updateTime', 'createBy', 'updateBy',
                           'createInfo', 'params')
            and not (isinstance(value, str) and any(item in value for item in marks))}


def java_db_core(msg):
    """取 Java 那串 MyBatis 包装里的 MySQL 原文（`### Cause: X: <这里>\\n;`）。"""
    match = re.search(r'### Cause: [^.]+(?:\.[^:.]+)+: (.*?)\n;', msg or '', re.S)
    return match.group(1).strip() if match else None


def run_one(block, tj, tr, verbose):
    route, table = block['route'], block['table']
    marks = {'java': 'parityW%s%sJ' % (STAMP, table[:10]),
             'rust': 'parityW%s%sR' % (STAMP, table[:10])}
    template = first_row(JAVA, tj, route) or first_row(RUST, tr, route)
    bodies = {}
    for side in ('java', 'rust'):
        body, _ = probe_body(template, block, marks[side])
        if body is None:
            return 'SKIP', '列表为空且没有内置最小请求体'
        bodies[side] = body

    created = {}
    for side, base, token in (('java', JAVA, tj), ('rust', RUST, tr)):
        payload = call('POST', base, token, route, bodies[side])
        created[side] = {'msg': payload.get('msg'), 'code': payload.get('code'),
                         'has_data': payload.get('data') is not None,
                         'id': payload.get('data')}
    shape = lambda item: {key: value for key, value in item.items() if key != 'id'}
    if shape(created['java']) != shape(created['rust']):
        core = java_db_core(created['java'].get('msg'))
        if (created['java'].get('code') == created['rust'].get('code')
                and core and core in (created['rust'].get('msg') or '')):
            return 'WARN', '同一 MySQL 错误、包装文案不同：%s（java 是 MyBatis 包装，rust 是 SQLx 前缀）' % core
        return 'FAIL', 'POST 响应不同 %s vs %s' % (shape(created['java']), shape(created['rust']))
    if created['java'].get('code') != 200:
        return 'OK', '两端同样拒绝：%s' % (created['java'].get('msg') or '')[:60]
    if not created['java']['has_data']:
        return 'WARN', '新增成功但两端都没有返回主键，无法回读'

    stored = {}
    for side, base, token in (('java', JAVA, tj), ('rust', RUST, tr)):
        stored[side] = comparable(by_id(base, token, route, created[side]['id']), marks.values())
    if stored['java'] is None or stored['rust'] is None:
        return 'FAIL', '回读为空 java=%s rust=%s（id=%s）' % (
            stored['java'] is None, stored['rust'] is None,
            [created[side]['id'] for side in ('java', 'rust')])
    if stored['java'] != stored['rust']:
        keys = set(list(stored['java']) + list(stored['rust']))
        diff = sorted(key for key in keys
                      if (stored['java']).get(key) != (stored['rust']).get(key)
                      or (key in stored['java']) != (key in stored['rust']))
        if verbose:
            print('    java', json.dumps(stored['java'], ensure_ascii=False)[:400])
            print('    rust', json.dumps(stored['rust'], ensure_ascii=False)[:400])
        return 'FAIL', '落库内容不同，差异列 %s' % diff

    removed = {}
    for side, base, token in (('java', JAVA, tj), ('rust', RUST, tr)):
        payload = call('DELETE', base, token, '%s/%s' % (route, created[side]['id']))
        removed[side] = {'msg': payload.get('msg'), 'code': payload.get('code')}
    if removed['java'] != removed['rust']:
        return 'FAIL', 'DELETE 响应不同 %s vs %s' % (removed['java'], removed['rust'])

    left = {}
    for side, base, token in (('java', JAVA, tj), ('rust', RUST, tr)):
        left[side] = bool(by_id(base, token, route, created[side]['id']))
    if left['java'] != left['rust']:
        return 'FAIL', '删除后回读不一致 java=%s rust=%s' % (left['java'], left['rust'])
    note = '标记 %s/%s，已删 id=%s' % (
        marks['java'], marks['rust'], [created[side]['id'] for side in ('java', 'rust')])
    if left['java']:
        # Java 的 selectXxxById 不带 del_flag 条件，软删行仍可按 id 查到；两端一致即可。
        return 'OK', '两端删除后都仍可按 id 查到软删行；' + note
    return 'OK', note


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', action='append', default=[],
                        help='只跑 route 含此子串的表（写 whiteinfo 即可，别写 /manager/...：'
                             'Git Bash 会把以 / 开头的参数改写成盘路径）')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    tally = {'OK': 0, 'WARN': 0, 'FAIL': 0, 'SKIP': 0}
    failures = []
    for block in crud_blocks():
        if args.only and not any(item in block['route'] for item in args.only):
            continue
        try:
            status, note = run_one(block, tj, tr, args.verbose)
        except Exception as error:  # 单个端点异常不影响整体
            status, note = 'FAIL', '异常 %r' % (error,)
        tally[status] = tally.get(status, 0) + 1
        if status == 'FAIL':
            failures.append((block['route'], note))
        print('%-4s %-28s %s' % (status, block['route'], note))
    print('\n汇总', json.dumps(tally, ensure_ascii=False))
    for route, note in failures:
        print('FAIL', route, note[:200])
    print('收尾清理：delete from <table> where id in (...)（两端建的都是软删行，标记前缀 parityW%s）' % STAMP)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
