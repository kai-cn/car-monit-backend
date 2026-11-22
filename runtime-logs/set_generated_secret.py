#!/usr/bin/env python3

"""
@description 历史脚本 set_generated_secret.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python set_generated_secret.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 生成高熵随机值并直接写入 GitHub Secret（值不回显、不落盘）。

import base64

import json

import os

import secrets

import string

import sys

import urllib.request



from nacl.public import PublicKey, SealedBox



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gh_cred import get_token



repo, name = sys.argv[1:3]

H = {"Authorization": "Bearer " + get_token(), "Accept": "application/vnd.github+json"}





def api(method, path, body=None):

    data = json.dumps(body).encode() if body is not None else None

    req = urllib.request.Request("https://api.github.com" + path, data=data, method=method,

                                 headers={**H, **({"Content-Type": "application/json"} if data else {})})

    with urllib.request.urlopen(req, timeout=60) as r:

        raw = r.read()

        return json.loads(raw.decode()) if raw else {}





alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+~"

value = "".join(secrets.choice(alphabet) for _ in range(48))

key = api("GET", "/repos/%s/actions/secrets/public-key" % repo)

enc = SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(value.encode())

api("PUT", "/repos/%s/actions/secrets/%s" % (repo, name),

    {"encrypted_value": base64.b64encode(enc).decode(), "key_id": key["key_id"]})

print("GENERATED_SECRET_SET", repo, name, "len", len(value))

