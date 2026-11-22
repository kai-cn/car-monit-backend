#!/usr/bin/env python3
"""
@description 历史脚本 save_joblog.py：保存日志或证据到本地；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python save_joblog.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Persist a job log or artifact for later inspection.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Save a job log verbatim to a local file (no truncation)."""
import os, subprocess, sys, tempfile, urllib.request, urllib.error

def token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

repo=sys.argv[1]; jid=sys.argv[2]; out=sys.argv[3]
url='https://api.github.com/repos/%s/actions/jobs/%s/logs'%(repo,jid)
req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token(),
    'Accept':'application/vnd.github+json','User-Agent':'carmonit-log'})
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return urllib.request.Request(newurl,headers={'User-Agent':'carmonit-log'})
op=urllib.request.build_opener(NoRedirect)
try:
    data=op.open(req,timeout=60).read()
except urllib.error.HTTPError as e:
    loc=e.headers.get('Location')
    data=urllib.request.urlopen(urllib.request.Request(loc,headers={'User-Agent':'carmonit-log'}),timeout=120).read() if loc else b''
open(out,'wb').write(data)
print('saved', len(data), 'bytes to', out)
