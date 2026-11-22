#!/usr/bin/env python3
# 用途：通过 Contents API 取远端文件内容到本地（token 来自缓存）。
# 用法：python fetch_file_api.py <repo> <branch> <remote_path> <local_out>
import base64
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, branch, path, out = sys.argv[1:5]
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}
url = "https://api.github.com/repos/%s/contents/%s?ref=%s" % (repo, path, branch)
with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
    d = json.loads(r.read())
data = base64.b64decode(d["content"])
open(out, "wb").write(data)
print("saved", out, len(data), "bytes")
