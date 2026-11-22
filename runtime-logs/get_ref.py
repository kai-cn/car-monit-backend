#!/usr/bin/env python3
# 用途：查询远端分支 SHA（走 GitHub API，token 来自缓存）。
# 用法：python get_ref.py <repo> <branch>
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, branch = sys.argv[1:3]
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0"}
url = "https://api.github.com/repos/%s/git/ref/heads/%s" % (repo, branch)
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
        d = json.loads(r.read())
    print(repo, branch, d["object"]["sha"])
except Exception as e:
    print("REF_ERR", repo, branch, repr(e))
