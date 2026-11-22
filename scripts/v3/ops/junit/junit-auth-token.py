#!/usr/bin/env python3
"""
@description 为 JUnit 全接口套件获取管理员 Bearer Token；凭据只从环境变量读取，不落盘、不回显。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage CARMONIT_ADMIN_USER=admin CARMONIT_ADMIN_PASSWORD=... python junit-auth-token.py --base-url http://127.0.0.1:19903 > token.txt
@dependencies Python 3 标准库；被测服务需提供 POST /login，且验证码允许空 code。
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request


def main() -> None:
    """登录目标服务并只输出 token，避免凭据进入日志或证据文件。"""
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', default='http://127.0.0.1:19903')
    a = ap.parse_args()
    user = __import__('os').environ.get('CARMONIT_ADMIN_USER', '')
    password = __import__('os').environ.get('CARMONIT_ADMIN_PASSWORD', '')
    if not user or not password:
        raise SystemExit('Missing CARMONIT_ADMIN_USER/CARMONIT_ADMIN_PASSWORD')
    body = json.dumps({'username': user, 'password': password, 'code': '', 'uuid': ''}).encode()
    req = urllib.request.Request(a.base_url.rstrip('/') + '/login', data=body,
                                 headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                                 method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        # api 服务未暴露 /login；跳过 Header，由基线/候选统一按匿名响应对拍。
        if e.code == 404:
            return
        raise
    m = re.search(r'"token"\s*:\s*"([^"]+)"', text)
    if not m:
        raise SystemExit('Login response has no token: ' + text[:200])
    print(m.group(1))


if __name__ == '__main__':
    main()
