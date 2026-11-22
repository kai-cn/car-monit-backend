#!/usr/bin/env python3

"""
@description 历史脚本 set_ci_db_secret.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python set_ci_db_secret.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：为两仓库写入随机生成的 CI-only DB 测试口令为 GitHub Actions Secret（自动脱敏，不打印值）。

# 用法：python set_ci_db_secret.py

import base64

import json

import os

import subprocess

import sys

import urllib.request



sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



# 生成满足 openGauss 复杂度的新口令（大写/小写/数字/特殊），仅存在于内存。

pw = base64.b64encode(os.urandom(18)).decode().rstrip("=") + "Aa1@"

token = get_token()

H = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",

     "Authorization": "Bearer " + token, "Content-Type": "application/json"}



# 取得仓库 public key（libsodium 加密），用 PyNaCl 若无则用明文 API 的 fallback。

for repo in ("kai-cn/car-monit-api", "kai-cn/car-monit-backend"):

    with urllib.request.urlopen(urllib.request.Request(

            "https://api.github.com/repos/%s/actions/secrets/public-key" % repo,

            headers=H), timeout=40) as r:

        key = json.loads(r.read())

    try:

        from nacl.public import PublicKey, SealedBox

        enc = base64.b64encode(SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(pw.encode())).decode()

        body = {"encrypted_value": enc, "key_id": key["key_id"]}

    except ImportError:

        print("PyNaCl_MISSING", repo)

        continue

    req = urllib.request.Request(

        "https://api.github.com/repos/%s/actions/secrets/CI_DB_TEST_PASSWORD" % repo,

        data=json.dumps(body).encode(), method="PUT", headers=H)

    with urllib.request.urlopen(req, timeout=40) as r:

        print("SECRET_SET", repo, "http", r.status)

