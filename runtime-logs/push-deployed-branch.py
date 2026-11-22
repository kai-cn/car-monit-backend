#!/usr/bin/env python3
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
