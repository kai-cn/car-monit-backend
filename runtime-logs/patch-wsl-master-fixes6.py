#!/usr/bin/env python3
"""Apply sixth batch of WSL master fixes.

@description 修复 backend C++ geometry_copy1、跨语言 workflow 的 token/下游 baseUrl 环境变量。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python runtime-logs/patch-wsl-master-fixes6.py
@dependencies WSL master clones。
"""
from pathlib import Path

W = Path('/home/dev/IdeaProjects')
B = W / 'car-monit-backend'
A = W / 'car-monit-api'
TOKEN = 'junit-cloud-secret-deterministic-0123456789abcdef'
BASE_URL = 'http://127.0.0.1:9902'


def replace(path, old, new):
    if not path.exists():
        print('MISSING', path)
        return
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8', errors='replace')
    if old not in text:
        print('NOT_FOUND', path)
        return
    new_text = text.replace(old, new)
    data = (new_text.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else new_text).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)


replace(B / 'car-monit-cpp/src/cm/web/controller/base/GeometrySyncController.cpp',
        'FROM geometry_copy1', 'FROM geometry')

for app, repo in [('backend', B), ('api', A)]:
    wf = repo / '.github/workflows/crosslang-full-parity-cloud.yml'
    raw = wf.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8', errors='replace')
    # Add shared env to every candidate step's env block that already has TOKEN__SECRET.
    marker = '          TOKEN__SECRET: ' + TOKEN + '\n'
    additions = [
        '          VEHICLE_MONITOR_BASE_URL: "' + BASE_URL + '"\n',
        '          APP_VEHICLEMONITOR__BASEURL: "' + BASE_URL + '"\n',
    ]
    if marker in text:
        text = text.replace(marker, marker + ''.join(additions))
    # Rust token must match Java-issued token semantics for parity.
    old_rust_token = '          APP_TOKEN__SECRET: "Y3Jvc3NsYW5nLWRldGVybWluaXN0aWMtc2VjcmV0LTAxMjM0NTY3ODkw"\n'
    if old_rust_token in text:
        text = text.replace(old_rust_token, '          APP_TOKEN__SECRET: "' + TOKEN + '"\n')
    data = (text.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else text).encode('utf-8')
    wf.write_bytes(data)
    print('WORKFLOW', app)
