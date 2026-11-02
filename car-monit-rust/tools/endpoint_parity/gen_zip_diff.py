# -*- coding: utf-8 -*-
"""代码生成 zip 的两端对拍：HTTP 头 + 条目名顺序 + 解压后的字节内容。

用法（两端已启动）：

    python -m tools.endpoint_parity.gen_zip_diff --table-name car_except_record
    python -m tools.endpoint_parity.gen_zip_diff --tables car_except_record,car_info

Java 用 java.util.zip（DEFLATE + data descriptor），Rust 用 STORE；
压缩字节必然不同，因此这里比的是「解压后是否同一批文件、同样内容」，
外加 Content-Disposition / Content-Type 这类前端会用到的响应头。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

RUST_BASE = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')
JAVA_BASE = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')

INTERESTING = ('Content-Type', 'Content-Disposition', 'Content-Length')


def fetch_zip(base: str, url: str, token: str = None, tolerate: bool = False):
    """返回 (响应头, {条目名: 字节}, 原始包体)；tolerate 时 HTTP 非 200 返回空结果。"""
    if token is None:
        token, status, payload = login(base)
        if not token:
            raise SystemExit(f'{base} 登录失败: {status} {payload}')
    status, headers, body = http('GET', base + url, token=token, timeout=240)
    if status != 200:
        detail = body[:200].decode('utf-8', 'replace') if isinstance(body, bytes) else str(body)[:200]
        if tolerate:
            print(f'  HTTP {status}: {detail}')
            return {}, {}, b''
        raise SystemExit(f'{base}{url} HTTP {status}: {detail}')
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        for info in archive.infolist():
            entries[info.filename] = archive.read(info)
    lower = {key.lower(): value for key, value in headers.items()}
    return {key: lower.get(key.lower()) for key in INTERESTING}, entries, body


def first_diff(expected: bytes, actual: bytes) -> tuple[int, str, str]:
    left, right = expected.decode('utf-8', 'replace').splitlines(), actual.decode(
        'utf-8', 'replace').splitlines()
    for index in range(max(len(left), len(right))):
        a = left[index] if index < len(left) else '<eof>'
        b = right[index] if index < len(right) else '<eof>'
        if a != b:
            return index + 1, a, b
    return 0, '', ''


def diff_entries(java: dict[str, bytes], rust: dict[str, bytes], verbose: bool) -> list[str]:
    """返回不一致说明；空列表表示两端完全一致。"""
    problems: list[str] = []
    names_j, names_r = list(java), list(rust)
    if names_j != names_r:
        only_java = sorted(set(names_j) - set(names_r))
        only_rust = sorted(set(names_r) - set(names_j))
        problems.append(f'条目名不一致 java={len(names_j)} rust={len(names_r)} '
                        f'仅java={only_java[:3]} 仅rust={only_rust[:3]}')
    for name in names_j:
        if name not in rust:
            continue
        if java[name] == rust[name]:
            if verbose:
                print(f'  {name:<60} 一致 {len(rust[name])} 字节')
            continue
        line, a, b = first_diff(java[name], rust[name])
        problems.append(f'{name} 差异 java={len(java[name])}/rust={len(rust[name])} 首行 {line}')
        if verbose:
            print(f'  {name:<60} 差异 java={len(java[name])}/rust={len(rust[name])} 首行 {line}')
            print(f'     java: {a[:160]}')
            print(f'     rust: {b[:160]}')
    return problems


def table_names() -> list[str]:
    token, status, payload = login(RUST_BASE)
    if not token:
        raise SystemExit(f'{RUST_BASE} 登录失败: {status} {payload}')
    status, _, body = http('GET', RUST_BASE + '/tool/gen/all/list', token=token, timeout=60)
    data = json.loads(body)
    if data.get('code') != 200:
        raise SystemExit('/tool/gen/all/list code=%s' % data.get('code'))
    return sorted(row.get('tableName', '') for row in data.get('data') or [] if row.get('tableName'))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--table-name', default=None, help='单表下载 /tool/gen/download/{tableName}')
    parser.add_argument('--tables', default=None, help='批量下载 /tool/gen/batchGenCode?tables=')
    parser.add_argument('--all-tables', action='store_true',
                        help='逐表跑 /tool/gen/download，覆盖 gen_table 全表')
    args = parser.parse_args(argv)

    if args.all_tables:
        failed = 0
        names = table_names()
        java_token, status, payload = login(JAVA_BASE)
        rust_token, status, payload = login(RUST_BASE)
        if not java_token or not rust_token:
            raise SystemExit('登录失败: %s %s' % (status, payload))
        for name in names:
            url = '/tool/gen/download/%s' % name
            _, java, _ = fetch_zip(JAVA_BASE, url, token=java_token, tolerate=True)
            _, rust, _ = fetch_zip(RUST_BASE, url, token=rust_token, tolerate=True)
            problems = diff_entries(java, rust, verbose=False)
            if problems:
                failed += 1
                print(f'{name}: {len(problems)} 处不一致')
                for item in problems[:3]:
                    print('   ', item[:180])
            else:
                print(f'{name}: 一致（{len(rust)} 个条目）')
        print('\n不一致表数：%d / %d' % (failed, len(names)))
        return 1 if failed else 0

    if args.tables:
        url = '/tool/gen/batchGenCode?tables=%s' % args.tables
    else:
        url = '/tool/gen/download/%s' % (args.table_name or 'car_except_record')

    java_headers, java, java_raw = fetch_zip(JAVA_BASE, url)
    rust_headers, rust, rust_raw = fetch_zip(RUST_BASE, url)

    print(f'请求 {url}')
    print('响应头:')
    for key in INTERESTING:
        mark = '=' if java_headers.get(key) == rust_headers.get(key) else '≠'
        print(f'  {mark} {key}: java={java_headers.get(key)!r} rust={rust_headers.get(key)!r}')
    print(f'包体字节: java={len(java_raw)} rust={len(rust_raw)}（压缩方式不同，仅供留意）')

    names_j, names_r = list(java), list(rust)
    if names_j != names_r:
        only_java = sorted(set(names_j) - set(names_r))
        only_rust = sorted(set(names_r) - set(names_j))
        print(f'\n条目名不一致 java={len(names_j)} rust={len(names_r)}')
        failed += 1
        only_java = sorted(set(names_j) - set(names_r))
        only_rust = sorted(set(names_r) - set(names_j))
        print(f'\n条目名不一致 java={len(names_j)} rust={len(names_r)}')
        if names_j == sorted(names_j, key=names_r.index) and not only_java and not only_rust:
            print('  （仅顺序不同）')
        for name in only_java:
            print(f'  仅 Java: {name}')
        for name in only_rust:
            print(f'  仅 Rust : {name}')
        for index, (a, b) in enumerate(zip(names_j, names_r)):
            if a != b:
                print(f'  第 {index + 1} 个条目顺序不同: java={a} rust={b}')
                break
    else:
        print(f'\n条目名与顺序一致（{len(names_j)} 个）')

    problems = diff_entries(java, rust, verbose=True)

    print('\n不一致条目数：%d' % len(problems))
    return 1 if (problems or names_j != names_r) else 0


if __name__ == '__main__':
    raise SystemExit(main())
