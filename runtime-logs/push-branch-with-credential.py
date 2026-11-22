#!/usr/bin/env python3
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
