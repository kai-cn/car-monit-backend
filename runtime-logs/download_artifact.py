#!/usr/bin/env python3

"""
@description 历史脚本 download_artifact.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python download_artifact.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Download a build artifact or log through the GitHub API.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Download a workflow artifact zip by artifact id (follows redirect)."""

import io, os, subprocess, sys, tempfile, urllib.request, zipfile





def token():

    # Fixed account (kai-cn) cached token; avoids GCM account picker.

    from gh_cred import get_token as _cached_get_token

    return _cached_get_token()



repo, aid, outdir = sys.argv[1], sys.argv[2], sys.argv[3]

url = 'https://api.github.com/repos/%s/actions/artifacts/%s/zip' % (repo, aid)





class NR(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):

        return urllib.request.Request(newurl, headers={'User-Agent': 'carmonit-dl'})





req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token(),

                                           'Accept': 'application/vnd.github+json',

                                           'User-Agent': 'carmonit-dl'})

data = urllib.request.build_opener(NR).open(req, timeout=600).read()

os.makedirs(outdir, exist_ok=True)

with zipfile.ZipFile(io.BytesIO(data)) as z:

    z.extractall(outdir)

print('extracted ->', outdir)

