#!/usr/bin/env python3

"""
@description 历史脚本 push-branch-with-credential.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python push-branch-with-credential.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：用本地缓存 token 经 HTTPS 推送分支（令牌不打印、不弹账号选择）。

# 用法：python push-branch-with-credential.py <repo_dir> <remote_url> <branch>

import subprocess

import sys



sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



repo_dir, remote, branch = sys.argv[1:4]

token = get_token()

url = remote.replace("https://", "https://x-access-token:" + token + "@")

r = subprocess.run(["git", "push", url, branch], cwd=repo_dir, capture_output=True, text=True)

sys.stdout.write(r.stdout[-3000:])

sys.stderr.write(r.stderr[-3000:])

sys.exit(r.returncode)

