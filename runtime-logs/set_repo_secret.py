#!/usr/bin/env python3

"""
@description 历史脚本 set_repo_secret.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python set_repo_secret.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：通过 GitHub API 设置仓库 Secret（libsodium sealed box 加密），值仅从环境变量读取，

# 不落盘、不回显。用法：

#   $env:SECRET_VALUE = '<value>'; python set_repo_secret.py <repo> <SECRET_NAME>

import base64

import json

import os

import sys

import urllib.request



from nacl.public import PublicKey, SealedBox



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gh_cred import get_token



repo, name = sys.argv[1:3]

value = os.environ.pop("SECRET_VALUE", None)

if value is None:

    sys.exit("SECRET_VALUE env missing")



H = {"Authorization": "Bearer " + get_token(), "Accept": "application/vnd.github+json",

     "User-Agent": "car-monit-v3-ops/1.0"}





def api(method, path, body=None):

    data = json.dumps(body).encode() if body is not None else None

    req = urllib.request.Request("https://api.github.com" + path, data=data, method=method,

                                 headers={**H, **({"Content-Type": "application/json"} if data else {})})

    with urllib.request.urlopen(req, timeout=60) as r:

        raw = r.read()

        return r.status, (json.loads(raw.decode()) if raw else {})





_, key = api("GET", "/repos/%s/actions/secrets/public-key" % repo)

pub = PublicKey(base64.b64decode(key["key"]))

enc = SealedBox(pub).encrypt(value.encode())

payload = {"encrypted_value": base64.b64encode(enc).decode(), "key_id": key["key_id"]}

status, _ = api("PUT", "/repos/%s/actions/secrets/%s" % (repo, name), payload)

print("SET_SECRET_OK repo=%s name=%s http=%s" % (repo, name, status))

