# -*- coding: utf-8 -*-
"""`vehicleMonitor.baseUrl`（默认 127.0.0.1:9901）的最小桩服务。

外部 Python「车辆监测」服务不在本仓库里，Java 的 Forest 客户端与 Rust 的
`service/remote.rs` 都指向它。没有桩进程时两端各自报错，`/base/*` 与
`/manager/cartrackinfo/*` 一批端点无法对拍（此前是临时手搓的进程，没入库）。

桩只保证「服务可达 + 返回结构合法」：列表返回空页、单条返回空对象，
让两端都走完整的 反序列化 → 组装 → 出参 路径，比的是两端一致性而不是数据本身。

用法：
    python -m tools.endpoint_parity.mock_vehicle_monitor            # 9901
    python -m tools.endpoint_parity.mock_vehicle_monitor --port 9901 --verbose
"""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

#: 桩只给「部分字段」的样本：真实上游也不会把实体的每个字段都返回，
#: 而 Java 会用 Forest 反序列化成实体再序列化出去（缺的字段变成显式 null），
#: 这正是两端最容易分叉的地方，所以这里刻意不给全。
SAMPLE_ROW = {
    'bigId': 'mock-big-id-1',
    'vehicleplate': '粤A12345',
    'axlecount': 2,
    'transtime': '2025-08-21 10:20:00',
    'gantryName': '上塘互通门架1',
}

EMPTY_PAGE = {'total': 0, 'rows': [], 'code': 200, 'msg': '查询成功'}

VERBOSE = False


def classify(path):
    """把请求路径归到一个形状标签。"""
    if path.endswith('/listToExport') or path.endswith('/listAll'):
        return 'array'
    if path.endswith('/list'):
        return 'page'
    if path.endswith('/earliest-time'):
        return 'time'
    if path.startswith('/base/feestationexit/'):
        return 'hutool'
    parts = [item for item in path.split('/') if item]
    if len(parts) >= 3:
        return 'object'
    return 'unknown'


def payload(kind, query):
    if kind == 'array':
        return [dict(SAMPLE_ROW)]
    if kind == 'page':
        return {'total': 1, 'rows': [dict(SAMPLE_ROW)], 'code': 200, 'msg': '查询成功'}
    if kind == 'object':
        return dict(SAMPLE_ROW)
    if kind == 'time':
        # Java 侧是 Date：给 null，两端都不报错即可（返回结构本身在 §5 已列 KNOWN）。
        return {'data': None}
    if kind == 'hutool':
        # hutool JSONObject：必须带 code，否则 Rust 视为上游失败。
        return {'total': 1, 'rows': [dict(SAMPLE_ROW)], 'code': 200, 'msg': '查询成功'}
    return {'total': 1, 'rows': [dict(SAMPLE_ROW)], 'code': 200, 'msg': '查询成功'}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler 约定
        parsed = urlparse(self.path)
        kind = classify(parsed.path)
        body = json.dumps(payload(kind, parsed.query), ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json;charset=UTF-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        if VERBOSE:
            print('%s -> %s' % (parsed.path, kind))

    def log_message(self, fmt, *args):  # 默认打 stderr，静音
        if os.environ.get('PARITY_MOCK_LOG') == '1':
            super().log_message(fmt, *args)


def main():
    global VERBOSE
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PARITY_MOCK_PORT', '9901')))
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    VERBOSE = args.verbose
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print('vehicleMonitor mock on http://127.0.0.1:%d' % args.port)
    server.serve_forever()


if __name__ == '__main__':
    main()
