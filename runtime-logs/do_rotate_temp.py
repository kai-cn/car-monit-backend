#!/usr/bin/env python3
"""
@description 历史脚本 do_rotate_temp.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python do_rotate_temp.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""One-shot rotation for public-repo CICD testing.
Self-contained secrets -> fresh random values; external creds -> obvious test placeholders.
Values are generated in memory, never printed, never written to disk.
"""
import base64, json, os, secrets, subprocess, tempfile, urllib.request, urllib.error
from nacl.public import SealedBox, PublicKey

API = "https://api.github.com"
REPOS = {"api": "kai-cn/car-monit-api", "backend": "kai-cn/car-monit-backend"}


def get_token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

TOKEN = get_token()
if not TOKEN:
    print("NO_TOKEN")
    raise SystemExit(1)
HEADERS = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "carmonit-temp-rotate"}


def api_call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def set_secret(repo, name, value):
    st, key = api_call("GET", "/repos/%s/actions/secrets/public-key" % repo)
    if st != 200:
        print("  [ERR] public-key status", st)
        return False
    pk = PublicKey(base64.b64decode(key["key"]))
    enc = base64.b64encode(SealedBox(pk).encrypt(value.encode())).decode()
    st, resp = api_call("PUT", "/repos/%s/actions/secrets/%s" % (repo, name),
                        {"encrypted_value": enc, "key_id": key["key_id"]})
    ok = st in (201, 204)
    print("  [%s] %s :: %s" % ("OK" if ok else "ERR " + str(st), repo, name))
    return ok


# ---- self-contained: fresh random values (64 hex chars) ----
internal_token = secrets.token_hex(32)
export_secret = secrets.token_hex(32)
jwt_secret = secrets.token_hex(32)

api_secrets = {
    "CI_INTERNAL_TOKEN": internal_token,
    "TRAFFIC_INTERNAL_TOKEN": internal_token,
    "CI_OPENGAUSS_PASSWORD": "OpenGauss@123",
    "SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD": "OpenGauss@123",
}
bk_secrets = {
    "CI_INTERNAL_TOKEN": internal_token,
    "TRAFFIC_API_INTERNAL_TOKEN": internal_token,
    "CI_EXPORT_SECRET": export_secret,
    "EXPORT_DOWNLOAD_SECRET": export_secret,
    "JWT_SECRET": jwt_secret,
    "CI_MYSQL_PASSWORD": "root",
    "SPRING_DATASOURCE_DRUID_MASTER_PASSWORD": "root",
    # external-system creds -> obvious non-production test placeholders (CICD builds do not need real ones)
    "OSS_ACCESS_KEY": "test-oss-ak",
    "OSS_SECRET_KEY": "test-oss-sk",
    "HENDA_SECRET": "test-henda-secret",
    "ALIYUN_SMS_ACCESS_KEY_ID": "test-aliyun-ak",
    "ALIYUN_SMS_ACCESS_KEY_SECRET": "test-aliyun-sk",
    "DRUID_LOGIN_USERNAME": "test-druid",
    "DRUID_LOGIN_PASSWORD": "test-druid-pw",
}

print("Rotating self-contained secrets (fresh random) + external placeholders (test only)...")
print("internal/export/jwt token lengths:", len(internal_token), len(export_secret), len(jwt_secret))
for n, v in api_secrets.items():
    set_secret(REPOS["api"], n, v)
for n, v in bk_secrets.items():
    set_secret(REPOS["backend"], n, v)
print("Done. Values never displayed or written to disk.")
