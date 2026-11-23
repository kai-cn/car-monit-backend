#!/usr/bin/env python3
"""
@description 打印 GitHub workflow dispatch 失败时的响应正文，定位 422 校验错误。
@author AI Assistant
@date 2026-11-23
@usage python probe-dispatch-422.py <repo> <workflow_id> <body_file>
@dependencies GitHub API 本地缓存凭据；Python 3 标准库。
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

repo, wf, body_file = sys.argv[1], sys.argv[2], sys.argv[3]
token = get_token()
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
           'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'dispatch-probe'}
body = Path(body_file).read_bytes()
req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches',
    data=body, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print('OK', r.status, r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode(errors='replace')[:2000])
