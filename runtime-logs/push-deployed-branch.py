#!/usr/bin/env python3

"""
@description 历史脚本 push-deployed-branch.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python push-deployed-branch.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：把 plumbing 部署后的远端跟踪 ref 推送到真正的远端分支（token 来自缓存）。

# 用法：python push-deployed-branch.py <repo_dir> <local_repo> <remote_url> <branch> <ref>

import subprocess

import sys

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



repo_dir, local_repo, remote, branch, ref = sys.argv[1:6]

token = get_token()

url = remote.replace("https://", "https://x-access-token:" + token + "@")

spec = "%s:refs/heads/%s" % (ref, branch)

r = subprocess.run(["git", "-C", local_repo, "push", url, spec],

                   cwd=repo_dir, capture_output=True, text=True)

sys.stdout.write(r.stdout[-2500:])

sys.stderr.write(r.stderr[-2500:])

sys.exit(r.returncode)

