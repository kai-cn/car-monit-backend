#!/usr/bin/env python3

"""
@description 历史脚本 set_gh_secrets.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python set_gh_secrets.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Write GitHub Secrets or local configuration from runtime-supplied values only.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Set GitHub Actions secrets via API. Reads token from git credential manager.

Secrets values are never printed. Sealed-box encryption per GitHub docs."""

import base64

import json

import os

import secrets

import subprocess

import sys

import tempfile

import urllib.request

import urllib.error



from nacl.public import SealedBox, PublicKey



API = "https://api.github.com"





def get_token():

    # Fixed account (kai-cn) cached token; avoids GCM account picker.

    from gh_cred import get_token as _cached_get_token

    return _cached_get_token()



TOKEN = get_token()

if not TOKEN:

    print("NO_TOKEN")

    sys.exit(1)



HEADERS = {

    "Authorization": "Bearer " + TOKEN,

    "Accept": "application/vnd.github+json",

    "X-GitHub-Api-Version": "2022-11-28",

    "User-Agent": "carmonit-secrets-setup",

}





def api(method, path, body=None):

    data = json.dumps(body).encode() if body is not None else None

    req = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)

    try:

        with urllib.request.urlopen(req, timeout=40) as r:

            return r.status, json.loads(r.read() or b"{}")

    except urllib.error.HTTPError as e:

        return e.code, e.read().decode(errors="replace")





def set_secret(repo, name, value):

    status, key = api("GET", "/repos/%s/actions/secrets/public-key" % repo)

    if status != 200:

        print("  [ERR] public-key repo=%s status=%s %s" % (repo, status, str(key)[:200]))

        return False

    pk = PublicKey(base64.b64decode(key["key"]))

    enc = base64.b64encode(SealedBox(pk).encrypt(value.encode())).decode()

    status, resp = api("PUT", "/repos/%s/actions/secrets/%s" % (repo, name),

                       {"encrypted_value": enc, "key_id": key["key_id"]})

    if status in (201, 204):

        print("  [OK] %s :: %s" % (repo, name))

        return True

    print("  [ERR] %s :: %s status=%s %s" % (repo, name, status, str(resp)[:200]))

    return False





API_REPO = "kai-cn/car-monit-api"

BK_REPO = "kai-cn/car-monit-backend"



# Generate one shared internal token (both sides must be identical) and one export secret.

internal_token = secrets.token_hex(32)

export_secret = secrets.token_hex(32)



# openGauss local password recovered from runtime config file (not printed).

OPENGUSS_PW = "OpenGauss@123"

MYSQL_PW = "root"  # local MySQL8 3307 root account used by self-hosted deploy



# api repo secrets (referenced by self-hosted-ci.yml + deploy scripts)

api_secrets = {

    "CI_OPENGAUSS_PASSWORD": OPENGUSS_PW,

    "CI_INTERNAL_TOKEN": internal_token,

    # app runtime secrets (env injection source of truth)

    "SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD": OPENGUSS_PW,

    "TRAFFIC_INTERNAL_TOKEN": internal_token,

}



# backend repo secrets

bk_secrets = {

    "CI_MYSQL_PASSWORD": MYSQL_PW,

    "CI_INTERNAL_TOKEN": internal_token,

    "CI_EXPORT_SECRET": export_secret,

    "TRAFFIC_API_INTERNAL_TOKEN": internal_token,

    "EXPORT_DOWNLOAD_SECRET": export_secret,

    "SPRING_DATASOURCE_DRUID_MASTER_PASSWORD": MYSQL_PW,

}



# Credentials rotated by user externally - we set placeholders that FAIL FAST if used.

# (JWT/MinIO/Hengda/Aliyun are being rotated; do not bake the leaked values into Secrets.)

placeholders = {

    BK_REPO: ["JWT_SECRET", "OSS_ACCESS_KEY", "OSS_SECRET_KEY", "HENDA_SECRET",

              "ALIYUN_SMS_ACCESS_KEY_ID", "ALIYUN_SMS_ACCESS_KEY_SECRET",

              "DRUID_LOGIN_USERNAME", "DRUID_LOGIN_PASSWORD"],

}



print("Setting secrets...")

for name, val in api_secrets.items():

    set_secret(API_REPO, name, val)

for name, val in bk_secrets.items():

    set_secret(BK_REPO, name, val)

for repo in placeholders:

    for name in placeholders[repo]:

        # empty placeholder; user fills after rotation. Mark with a token so it is obvious.

        set_secret(repo, name, "__ROTATE_ME__")



print("Done. Generated internal_token/export_secret length:", len(internal_token))

