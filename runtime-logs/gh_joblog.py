#!/usr/bin/env python3
"""
@description 历史脚本 gh_joblog.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python gh_joblog.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Fetch a job log following redirects; print last N lines matching filters or tail."""
import os, subprocess, sys, tempfile, urllib.request, urllib.error

def token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

repo=sys.argv[1]; jid=sys.argv[2]
url='https://api.github.com/repos/%s/actions/jobs/%s/logs'%(repo,jid)
req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token(),
    'Accept':'application/vnd.github+json','User-Agent':'carmonit-log'})
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return urllib.request.Request(newurl,headers={'User-Agent':'carmonit-log'})
op=urllib.request.build_opener(NoRedirect)
try:
    r=op.open(req,timeout=40)
    data=r.read().decode(errors='replace')
except urllib.error.HTTPError as e:
    loc=e.headers.get('Location')
    if loc:
        data=urllib.request.urlopen(urllib.request.Request(loc,headers={'User-Agent':'carmonit-log'}),timeout=60).read().decode(errors='replace')
    else:
        print('HTTP',e.code,e.read().decode(errors='replace')[:500]); sys.exit()
lines=data.splitlines()
# Re-encode to avoid Windows GBK console errors on non-GBK chars.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
print('TOTAL_LINES',len(lines))
for l in lines[-60:]: print(l)
