# -*- coding: utf-8 -*-
"""把 xlsx 以 multipart 上传到两端的两个导入端点，比对真实响应（配合 xlsx_fixture 造夹具）。

用法：python -m tools.endpoint_parity.import_probe <xlsx 路径> [java|rust|both]
"""
import json
import os
import sys
import uuid
from pathlib import Path

from .client import http, login  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')


def upload(base, token, path, file_path):
    """client.http 会对 body 做 json.dumps，multipart 要自己发。"""
    import urllib.request

    boundary = '----parity' + uuid.uuid4().hex
    name = os.path.basename(file_path)
    with open(file_path, 'rb') as handle:
        data = handle.read()
    body = b''.join([
        ('--%s\r\n' % boundary).encode(),
        ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % name).encode(),
        b'Content-Type: application/octet-stream\r\n\r\n',
        data,
        ('\r\n--%s--\r\n' % boundary).encode(),
    ])
    request = urllib.request.Request(
        base + path,
        data=body,
        method='POST',
        headers={
            'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
            'Authorization': 'Bearer ' + token,
            'Content-Length': str(len(body)),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except Exception as error:  # 连接失败/超时
        return -1, str(error).encode('utf-8')


def main():
    file_path = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else 'both'
    endpoints = {'except': '/manager/exceptrecord/import', 'car': '/manager/carinfo/import'}
    for label, path in endpoints.items():
        for side, base in (('java', JAVA), ('rust', RUST)):
            if which != 'both' and which != side:
                continue
            token, _, _ = login(base)
            if not token:
                print(side, '登录失败')
                continue
            status, raw = upload(base, token, path, file_path)
            text = raw.decode('utf-8', 'replace')
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass
            print('%-6s %-5s %s -> HTTP %s %s' % (label, side, os.path.basename(file_path), status, text[:700]))


if __name__ == '__main__':
    main()
