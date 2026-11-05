# -*- coding: utf-8 -*-
"""backend → car-monit-api 调用链的双端对拍（带真实参数）。

`compare.py` 用默认参数跑 GET，遇到「时间段必填」这类接口只会拿到空表，
等于没打到远端。本脚本用**真实存在的上游数据**（从 api 端直接查出来的
bigId / 车牌 / 时间窗）逐个打后端的两端，比原始响应字节；导出类接口解 zip 后
比条目名与内容（Java 用 DEFLATE、Rust 用 STORE，压缩包本身必然不同）。

拓扑（2026-11-04 起）：
    backend-Java(9988, Redis db0) -> car-monit-api 的 Java 端(9902, db0)
    backend-Rust(9990, Redis db15) -> car-monit-api-rust(9911, db15)
同一侧的 backend 与 api 共用一个 db（api 写的 `gantry_list`/`section_list` 等
缓存要被 backend 读到），两侧 db 不同。

用法（四个服务都要在）：
    PARITY_USER=admin PARITY_PASSWORD=xxx PARITY_REDIS_DB_JAVA=0 PARITY_REDIS_DB_RUST=15 \
        python -m tools.endpoint_parity.api_chain_matrix
    ... --only feeGantry --verbose
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')

TS_RE = re.compile(rb'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?|\b1[0-9]{12}\b')
# 上游 feeGantry 每次请求都给行换一个随机 uuid（两端都一样），不比它。
RAND_RE = re.compile(rb'[0-9a-fA-F]{8}(-?[0-9a-fA-F]{4}){3}-?[0-9a-fA-F]{12}|\b[0-9a-f]{32}\b')


def normalize(raw):
    return RAND_RE.sub(b'<rand>', TS_RE.sub(b'<ts>', raw))

#: (标签, 路径, 期望类型)  —— 期望类型 json | xlsx
CASES = [
    # 门架交易流水：上游 200 行，entime 2024-10-26
    ('feeGantry 无过滤', '/base/feeGantry/list?pageNum=1&pageSize=5', 'json'),
    ('feeGantry 时间窗', '/base/feeGantry/list?applyTime1=2024-10-26%2000:00:00&applyTime2=2024-10-27%2000:00:00&pageNum=1&pageSize=5', 'json'),
    ('feeGantry 车牌', '/base/feeGantry/list?vehicleplate=%E9%B2%81H63V17&pageNum=1&pageSize=5', 'json'),
    ('feeGantry 详情', '/base/feeGantry/59', 'json'),
    ('feeGantry 详情缺失', '/base/feeGantry/no-such-id', 'json'),
    ('feeGantry 导出', '/base/feeGantry/export?applyTime1=2024-10-26%2000:00:00&applyTime2=2024-10-27%2000:00:00', 'xlsx'),
    # 抓拍流水：上游 251 行，snapshottime 2025-11-16；backend 优先读本地分表
    ('snapshotflow 无过滤', '/base/snapshotflow/list?pageNum=1&pageSize=5', 'json'),
    ('snapshotflow 时间窗', '/base/snapshotflow/list?applyTime1=2025-11-16%2000:00:00&applyTime2=2025-11-17%2000:00:00&pageNum=1&pageSize=5', 'json'),
    ('snapshotflow 详情', '/base/snapshotflow/1', 'json'),
    ('snapshotflow 最早时间', '/base/snapshotflow/earliest-time', 'json'),
    ('snapshotflow 导出', '/base/snapshotflow/export?applyTime1=2025-11-16%2000:00:00&applyTime2=2025-11-17%2000:00:00', 'xlsx'),
    # 出口站流水：上游 270 行，extime 2025-01-29；hutool JSONObject 透传
    ('feestationexit 无过滤', '/base/feestationexit/list?pageNum=1&pageSize=5', 'json'),
    ('feestationexit 时间窗', '/base/feestationexit/list?applyTime1=2025-01-29%2000:00:00&applyTime2=2025-01-30%2000:00:00&pageNum=1&pageSize=5', 'json'),
    ('feestationexit 详情', '/base/feestationexit/11150377', 'json'),
    ('feestationexit 导出', '/base/feestationexit/export?applyTime1=2025-01-29%2000:00:00&applyTime2=2025-01-30%2000:00:00', 'xlsx'),
    # 收费流水：上游 listAll/list 里 Java SQL 缺失，两端都该原样把远端 500 报出来
    ('feerecords 时间窗', '/base/feerecords/list?inApplyTime1=2025-08-01%2000:00:00&inApplyTime2=2025-08-31%2000:00:00&pageNum=1&pageSize=5', 'json'),
    ('feerecords 缺时间参数', '/base/feerecords/list?pageNum=1&pageSize=5', 'json'),
    ('feerecords 详情', '/base/feerecords/mock-big-id-1', 'json'),
    ('feerecords 导出', '/base/feerecords/export?inApplyTime1=2025-08-01%2000:00:00&inApplyTime2=2025-08-31%2000:00:00', 'xlsx'),
    # 本地表 + 远端补全：门架/收费站列表用 section_list 缓存补路名
    ('gantry 列表(缓存补名)', '/base/gantry/list?pageNum=1&pageSize=5', 'json'),
    ('toll 列表(缓存补名)', '/base/toll/list?pageNum=1&pageSize=5', 'json'),
    ('gantry 导出', '/base/gantry/export', 'xlsx'),
    # 轨迹：Java 侧对每行再打远端，缓存/远端形状最容易分叉
    ('cartrackinfo listByCarId', '/manager/cartrackinfo/listByCarId?carNo=%E9%B2%81H63V17&pageNum=1&pageSize=3', 'json'),
    ('cartrackinfo list', '/manager/cartrackinfo/list?pageNum=1&pageSize=3', 'json'),
]


def field_diff(a, b, path='', out=None, cap=8):
    """结构化差异：定位到具体键，而不是只报「长度不同」。"""
    if out is None:
        out = []
    if len(out) >= cap:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                out.append(('仅rust', '%s.%s' % (path, key), str(b[key])[:60]))
            elif key not in b:
                out.append(('仅java', '%s.%s' % (path, key), str(a[key])[:60]))
            else:
                field_diff(a[key], b[key], '%s.%s' % (path, key), out, cap)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(('长度', path, '%s vs %s' % (len(a), len(b))))
        for index in range(min(len(a), len(b))):
            field_diff(a[index], b[index], '%s[%d]' % (path, index), out, cap)
    elif a != b:
        if rand_like(a) and rand_like(b):
            return out        # 上游每次请求重排的随机 id，不比值
        if path == '.msg' and isinstance(a, str) and isinstance(b, str) and (
                a.endswith(b) or b.endswith(a)):
            # 同一条错误，两端只差框架前缀（Forest / SQLx），docs/03 §7.8 记为已知。
            out.append(('包装', path, '仅框架前缀不同：%s' % (a if a.endswith(b) else b)[:60]))
        else:
            out.append(('值', path, '%s vs %s' % (str(a)[:70], str(b)[:70])))
    return out


UUIDISH = re.compile(r'^(?:[0-9a-fA-F]{8}(-?[0-9a-fA-F]{4}){3}-?[0-9a-fA-F]{12}|[0-9a-f]{32})$')


def rand_like(value):
    return isinstance(value, str) and bool(UUIDISH.match(value))


def normalize(raw):
    return TS_RE.sub(b'<ts>', raw)


def xlsx_cells(raw):
    """解出 xlsx 的单元格值（POI 与 Rust 写出来的 styles/theme/属性顺序本来就不同，
    `docs/03` §1 对二进制的口径也只是状态+Content-Type+文件头，所以这里比数据而不是比字节）。"""
    book = zipfile.ZipFile(io.BytesIO(raw))
    shared = []
    if 'xl/sharedStrings.xml' in book.namelist():
        root = ET.fromstring(book.read('xl/sharedStrings.xml'))
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        for item in root.findall('%ssi' % ns):
            shared.append(''.join(node.text or '' for node in item.iter('%st' % ns)))
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    sheets = sorted(name for name in book.namelist()
                    if re.match(r'xl/worksheets/sheet\d+\.xml$', name))
    out = []
    for sheet in sheets:
        root = ET.fromstring(book.read(sheet))
        for row in root.iter('%srow' % ns):
            cells = []
            for cell in row.iter('%sc' % ns):
                value = cell.find('%sv' % ns)
                text = value.text if value is not None else ''
                if cell.get('t') == 's':
                    text = shared[int(text)] if text not in ('', None) else ''
                cells.append((cell.get('r'), text))
            out.append((sheet, tuple(cells)))
    return out


def coord_order(coord):
    """把 A1/B12 这类单元格坐标按「行优先、再列」排（差异报告要按人眼顺序）。"""
    match = re.match(r'([A-Z]+)(\d+)', coord or '')
    if not match:
        return (0, 0, coord or '')
    column = 0
    for ch in match.group(1):
        column = column * 26 + (ord(ch) - 64)
    return (int(match.group(2)), column, coord)


def run_case(label, path, kind, tj, tr, verbose):
    got = {}
    for side, base, token in (('java', JAVA, tj), ('rust', RUST, tr)):
        status, headers, raw = http('GET', base + path, token=token, timeout=240)
        got[side] = {'status': status, 'ctype': headers.get('Content-Type'),
                     'len': len(raw), 'raw': raw}
    j, r = got['java'], got['rust']
    if kind == 'xlsx':
        if normalize(j['raw']) == normalize(r['raw']):
            return 'OK', '响应逐字节一致（%dB）' % j['len']
        try:
            jz, rz = xlsx_cells(j['raw']), xlsx_cells(r['raw'])
        except Exception as error:
            return 'FAIL', '解不开 xlsx：%r java=%dB rust=%dB' % (error, j['len'], r['len'])
        if jz == rz:
            rows = len(jz[0][1]) if jz else 0
            return 'OK', '单元格数据逐格一致（%d 个工作表 / %d 行；POI 与 Rust 的 styles/theme/docProps 本来就不同字节）' % (
                len(jz), rows)
        flat_j = {(sheet, cell): text for sheet, cells in jz for cell, text in cells}
        flat_r = {(sheet, cell): text for sheet, cells in rz for cell, text in cells}
        # 「空字符串单元格」和「不写这个单元格」在 xlsx 里等价（Excel 一律当空白格），
        # POI 会写出来、rust_xlsxwriter 会省掉，不算数据差异。
        keys = set(flat_j) | set(flat_r)
        sample = []
        for key in sorted(keys, key=lambda item: (item[0], coord_order(item[1]))):
            left = flat_j.get(key) or ''
            right = flat_r.get(key) or ''
            if left != right:
                sample.append('%s!%s %s vs %s' % (key[0].replace('xl/worksheets/', ''), key[1],
                                                   left[:24], right[:24]))
            if len(sample) >= 4:
                break
        differing = sum(1 for key in keys if (flat_j.get(key) or '') != (flat_r.get(key) or ''))
        if not differing:
            return 'OK', '非空单元格逐格一致（%d 个坐标；空白格 POI 写、rust_xlsxwriter 省，等价）' % len(keys)
        return 'FAIL', 'xlsx 数据差异 %d/%d 格起：%s' % (differing, len(keys), '; '.join(sample))
    if normalize(j['raw']) == normalize(r['raw']):
        note = ''
        try:
            payload = json.loads(j['raw'])
            if isinstance(payload, dict):
                rows = payload.get('rows')
                note = ' code=%s total=%s rows=%s' % (
                    payload.get('code'), payload.get('total'),
                    len(rows) if isinstance(rows, list) else '-')
        except Exception:
            pass
        return 'OK', '一致（%dB）%s' % (j['len'], note)
    if verbose:
        print('     java', j['raw'][:260].decode('utf-8', 'replace'))
        print('     rust', r['raw'][:260].decode('utf-8', 'replace'))
    try:
        parsed_j, parsed_r = json.loads(j['raw']), json.loads(r['raw'])
    except Exception:
        return 'FAIL', '非 JSON 且不一致 java=%s rust=%s' % (
            j['raw'][:120].decode('utf-8', 'replace'), r['raw'][:120].decode('utf-8', 'replace'))
    if normalize(j['raw']) == normalize(r['raw']):
        return 'OK', '归一后逐字节一致（%dB）' % j['len']
    if json.dumps(parsed_j, sort_keys=True) == json.dumps(parsed_r, sort_keys=True):
        # hutool JSONObject 走 HashMap 迭代序，Java 的键序与上游无关也不可复制，值一致即可。
        return 'WARN', '解析后一致，只有键顺序不同（%dB vs %dB）' % (j['len'], r['len'])
    if json.dumps(parsed_j) == json.dumps(parsed_r):
        # 只剩 BigDecimal 标度（Java `165.680` / Rust `165.68`）：JSON 数值相等，
        # compare.py 的口径也是按解析后的值比，这里记 OK 并说明。
        return 'OK', '解析后逐字段一致，仅数字标度写法不同（%dB vs %dB）' % (j['len'], r['len'])
    diffs = field_diff(parsed_j, parsed_r)
    if not diffs:
        # 只剩上游每次请求重新生成的随机 id —— 值层面等价。
        return 'OK', '一致（差异仅上游随机 id，%dB）' % j['len']
    note = '; '.join('%s %s: %s' % item for item in diffs[:4])
    if all(item[0] == '包装' for item in diffs):
        return 'WARN', '同一条错误、只差框架前缀（%s）' % note.split(':', 1)[-1].strip()[:60]
    return 'FAIL', note


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', action='append', default=[], help='标签子串过滤')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    tally = {'OK': 0, 'WARN': 0, 'FAIL': 0}
    for label, path, kind in CASES:
        if args.only and not any(item in label for item in args.only):
            continue
        try:
            status, note = run_case(label, path, kind, tj, tr, args.verbose)
        except Exception as error:
            status, note = 'FAIL', '异常 %r' % (error,)
        tally[status] = tally.get(status, 0) + 1
        print('%-4s %-26s %s' % (status, label, note))
    print('\n汇总', json.dumps(tally, ensure_ascii=False))
    return 1 if tally['FAIL'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
