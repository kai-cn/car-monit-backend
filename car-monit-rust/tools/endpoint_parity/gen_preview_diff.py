# -*- coding: utf-8 -*-
"""代码生成预览的逐模板对拍：Java 实测输出 vs Rust 渲染输出。

用法（两端已启动）：

    python -m tools.endpoint_parity.gen_preview_diff --table-id 231
    python -m tools.endpoint_parity.gen_preview_diff --table-id 231 --save-oracle

`--save-oracle` 会把 Java 的每个模板输出存到 `build/gen_oracle/`；
之后不带该参数即拿存下的基准做逐字节比较，模板全一致时退出码 0。
Java 侧的 `$datetime` 只到日期，同一天内基准可复用。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import login, http  # noqa: E402

RUST_BASE = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')
JAVA_BASE = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')


def fetch(base: str, table_id: str) -> dict:
    token, status, payload = login(base)
    if not token:
        raise SystemExit(f'{base} 登录失败: {status} {payload}')
    _, _, body = http('GET', f'{base}/tool/gen/preview/{table_id}', token=token, timeout=240)
    try:
        data = json.loads(body)
    except Exception:
        raise SystemExit(f'{base} 预览响应非 JSON: {body[:200]}')
    if data.get('code') != 200:
        raise SystemExit(f'{base} 预览 code={data.get("code")} msg={data.get("msg")}')
    return data.get('data') or {}


def first_diff(expected: str, actual: str) -> tuple[int, str, str]:
    left, right = expected.splitlines(), actual.splitlines()
    for index in range(max(len(left), len(right))):
        a = left[index] if index < len(left) else '<eof>'
        b = right[index] if index < len(right) else '<eof>'
        if a != b:
            return index + 1, a, b
    return 0, '', ''


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--table-id', default='231')
    parser.add_argument('--oracle-dir', default='build/gen_oracle')
    parser.add_argument('--save-oracle', action='store_true')
    parser.add_argument('--context', default=3, type=int, help='差异上下文行数')
    args = parser.parse_args(argv)

    rust = fetch(RUST_BASE, args.table_id)
    oracle = Path(args.oracle_dir)
    if args.save_oracle:
        java = fetch(JAVA_BASE, args.table_id)
        oracle.mkdir(parents=True, exist_ok=True)
        for name, text in java.items():
            (oracle / name.replace('/', '__')).write_text(text, encoding='utf-8', newline='')
        print(f'已保存 Java 基准 {len(java)} 个模板 -> {oracle}')
        return 0

    failed = 0
    for name in sorted(rust):
        path = oracle / name.replace('/', '__')
        if not path.exists():
            print(f'{name:<40} 缺基准（先 --save-oracle）')
            failed += 1
            continue
        with open(path, encoding='utf-8', newline='') as handle:
            expected = handle.read()
        actual = rust[name]
        if expected == actual:
            print(f'{name:<40} 一致 {len(actual)} 字节')
            continue
        failed += 1
        line, a, b = first_diff(expected, actual)
        print(f'{name:<40} 差异 基准{len(expected)}/当前{len(actual)} 首个不同行 {line}')
        print(f'   java: {a[:160]}')
        print(f'   rust: {b[:160]}')
    missing = sorted(set(p.name.replace('__', '/') for p in oracle.glob('*')) - set(rust))
    for name in missing:
        print(f'{name:<40} Rust 未渲染该模板')
        failed += 1
    print('\n模板不一致数：%d' % failed)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
