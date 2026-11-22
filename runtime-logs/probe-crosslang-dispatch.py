#!/usr/bin/env python3
"""
@description 历史脚本 probe-crosslang-dispatch.py：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python probe-crosslang-dispatch.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

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
