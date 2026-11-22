#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：probe-crosslang-dispatch.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
"""Print the GitHub API error body for a crosslang workflow dispatch.

Idea: 422 usually means a workflow_dispatch input is missing/invalid or the
workflow file is not active on the selected ref. Reading the response body is
the fastest way to distinguish those cases.
"""
import json
import sys
import urllib.error
import urllib.request
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'User-Agent': 'crosslang-probe'}
repo = sys.argv[1]
body = json.loads(sys.argv[2])
wf = json.loads(urllib.request.urlopen(urllib.request.Request(
    f'https://api.github.com/repos/{repo}/actions/workflows/crosslang-full-parity-cloud.yml', headers=H), timeout=60).read())['id']
req = urllib.request.Request(f'https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches',
                             data=json.dumps(body).encode(), headers=H, method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print('OK', r.status)
except urllib.error.HTTPError as e:
    print('HTTP', e.code)
    print(e.read().decode())
