#!/usr/bin/env python3

"""
@description 历史脚本 gh_cred.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python gh_cred.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：一次性读取 GitHub token 并缓存，避免每次 git credential fill 触发 GCM 账号选择弹窗。

# 缓存文件位于仓库外，仅当前用户可读（icacls 限制）；token 永不打印。

import os

import stat

import subprocess



CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gh_token_cache")

USERNAME = "kai-cn"





def _read_cache():

    try:

        with open(CACHE, "r", encoding="utf-8") as f:

            t = f.read().strip()

        return t or None

    except Exception:

        return None





def _fetch():

    p = subprocess.run(

        ["git", "credential", "fill"],

        input="protocol=https\nhost=github.com\nusername=%s\n\n" % USERNAME,

        capture_output=True, text=True, timeout=90,

    )

    for line in p.stdout.splitlines():

        if line.startswith("password="):

            return line.split("=", 1)[1]

    raise RuntimeError("NO_CREDENTIAL (git credential fill returned no password)")





def get_token(refresh=False):

    t = None if refresh else _read_cache()

    if not t:

        t = _fetch()

        with open(CACHE, "w", encoding="utf-8") as f:

            f.write(t)

        os.chmod(CACHE, stat.S_IRUSR | stat.S_IWUSR)

        try:

            subprocess.run(["icacls", CACHE, "/inheritance:r", "/grant:r",

                            "%s:(F)" % os.environ.get("USERNAME", "Administrators")],

                           capture_output=True)

        except Exception:

            pass

    return t





if __name__ == "__main__":

    print("TOKEN_READY" if get_token() else "NO_TOKEN")

