# -*- coding: utf-8 -*-
"""采集 Java 侧响应的 JSON 键顺序，作为 Rust 端 reorder 的依据。

Java 的 Jackson 顺序是「BaseEntity 字段在前 + 实体声明顺序 + 派生 getter」，
与 SQL 列序无关，只能实测。结果写 `build/java_orders.json`：

    {端点路径: {容器路径: [键...]}}

容器路径与 compare.py 的差异定位一致（如 `rows[0]`、`data`、`data.dept`）。

用法（Java 已启动）：

    python -m tools.endpoint_parity.entity_order --report build/parity-report.json
    python -m tools.endpoint_parity.entity_order --path /system/user/list   # 只采指定端点
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402
from compare import SKIP, build_url, is_slow  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
HERE = Path(__file__).resolve().parent


def walk(node, prefix: str, out: dict) -> None:
    if isinstance(node, dict):
        if prefix:
            out[prefix] = list(node.keys())
        for key, value in node.items():
            walk(value, f'{prefix}.{key}' if prefix else key, out)
    elif isinstance(node, list) and node:
        walk(node[0], f'{prefix}[0]', out)


def needed_containers(report_path: Path) -> dict[str, set[str]]:
    rows = json.load(open(report_path, encoding='utf-8'))
    out: dict[str, set[str]] = {}
    for row in rows:
        for issue in row.get('issues') or []:
            if issue[0] == 'ORDER-DIFF':
                container = issue[1] or ''
                out.setdefault(row['path'], set()).add(container)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--endpoints', default=str(HERE / 'endpoints.json'))
    parser.add_argument('--report', default=None,
                        help='parity report；给出后只采集其中 ORDER-DIFF 的端点/容器')
    parser.add_argument('--path', action='append', default=[], help='只采集指定端点（可重复）')
    parser.add_argument('--out', default='build/java_orders.json')
    args = parser.parse_args(argv)

    rows = json.load(open(args.endpoints, encoding='utf-8'))
    gets = [r for r in rows if r['method'] == 'GET']
    wanted = set(args.path)
    targets = {}
    report_orders = needed_containers(Path(args.report)) if args.report else {}
    for row in gets:
        path = row['path']
        if path in SKIP:
            continue
        if args.report and path not in report_orders:
            continue
        if wanted and path not in wanted:
            continue
        targets[path] = report_orders.get(path, set())

    token, status, payload = login(JAVA)
    if not token:
        raise SystemExit(f'{JAVA} 登录失败: {status} {payload}')

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {}
    if out_path.exists():
        result = json.load(open(out_path, encoding='utf-8'))

    for path in sorted(targets):
        timeout = 240 if is_slow(path) else 45
        status, _, body = http('GET', build_url(JAVA, path), token=token, timeout=timeout)
        try:
            data = json.loads(body)
        except Exception:
            print(f'{path:<50} 非 JSON（HTTP {status}）')
            continue
        orders: dict[str, list[str]] = {}
        walk(data, '', orders)
        picked = targets[path]
        if picked:
            orders = {key: value for key, value in orders.items() if key in picked}
        if orders:
            result.setdefault(path, {}).update(orders)
        print(f'{path:<50} {len(orders)} 个容器')

    json.dump(result, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(len(v) for v in result.values())
    print(f'\n共 {len(result)} 个端点 / {total} 个容器 -> {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
