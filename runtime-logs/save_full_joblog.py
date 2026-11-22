#!/usr/bin/env python3

"""
@description 历史脚本 save_full_joblog.py：保存日志或证据到本地；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python save_full_joblog.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Persist a job log or artifact for later inspection.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Save full job log to a file (UTF-8) for grepping."""

import os, subprocess, sys, tempfile, urllib.request, urllib.error





def token():

    # Fixed account (kai-cn) cached token; avoids GCM account picker.

    from gh_cred import get_token as _cached_get_token

    return _cached_get_token()



repo, jid, outp = sys.argv[1], sys.argv[2], sys.argv[3]

url = 'https://api.github.com/repos/%s/actions/jobs/%s/logs' % (repo, jid)

req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token(),

                                           'Accept': 'application/vnd.github+json',

                                           'User-Agent': 'carmonit-log'})





class NR(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):

        return urllib.request.Request(newurl, headers={'User-Agent': 'carmonit-log'})





data = urllib.request.build_opener(NR).open(req, timeout=60).read().decode(errors='replace')

open(outp, 'w', encoding='utf-8').write(data)

print('saved', len(data), 'chars ->', outp)

