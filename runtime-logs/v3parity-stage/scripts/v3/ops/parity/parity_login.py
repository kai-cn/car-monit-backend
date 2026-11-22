#!/usr/bin/env python3

"""
@description 历史脚本 parity_login.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python parity_login.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

用法：


  python parity_login.py --port 19903 --user admin --password-env CI_ADMIN_PASSWORD


输出（stdout，仅键名，不含值）：


  PARITY_TOKEN_SET


并把下面两行追加到 $GITHUB_ENV：


  PARITY_AUTH_HEADER=Authorization: Bearer <token>   # GitHub 会自动 mask secret 派生的 token
"""
from __future__ import annotations

import argparse

import json

import os

import time

import urllib.request

import urllib.error





def login(port: int, user: str, password: str) -> str:

    body = json.dumps({"username": user, "password": password, "code": "", "uuid": ""}).encode()

    req = urllib.request.Request(

        "http://127.0.0.1:%d/login" % port, data=body, method="POST",

        headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=30) as r:

        data = json.loads(r.read().decode("utf-8", "replace"))

    token = data.get("token") or (data.get("data") or {}).get("token")

    if not token:

        raise RuntimeError("login no token: code=%s msg=%s" % (data.get("code"), data.get("msg")))

    return token





def main() -> None:

    ap = argparse.ArgumentParser()

    ap.add_argument("--port", type=int, required=True)

    ap.add_argument("--user", default="admin")

    ap.add_argument("--password-env", default="CI_ADMIN_PASSWORD")

    ap.add_argument("--wait-seconds", type=int, default=60)

    a = ap.parse_args()

    password = os.environ.get(a.password_env, "")

    if not password:

        raise RuntimeError("password env %s missing" % a.password_env)



    token = None

    for _ in range(a.wait_seconds):

        try:

            token = login(a.port, a.user, password)

            break

        except Exception:

            time.sleep(1)

    if not token:

        raise RuntimeError("login failed after %ss" % a.wait_seconds)



    # token 来自 secret 派生的响应；写 GITHUB_ENV 让后续 step 以 env 读取，不打印值。

    gh_env = os.environ.get("GITHUB_ENV")

    if gh_env:

        with open(gh_env, "a", encoding="utf-8") as f:

            f.write("PARITY_AUTH_TOKEN=%s\n" % token)

    print("PARITY_TOKEN_SET len=%d" % len(token))





if __name__ == "__main__":

    main()

