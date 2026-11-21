#!/usr/bin/env python3
# 用途：用 GitHub Contents API 更新多个文件（绕开 git HTTPS 连接重置）。
# 用法：python push_files_api.py <repo> <branch> <local_base_dir> <relpath1> [relpath2 ...]
import base64
import json
import os
import sys
import urllib.error
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",
     "Accept": "application/vnd.github+json"}
MSG = "fix(dbupgrade): sync gs_dump positional fix"


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://api.github.com" + path, data=data, method=method,
                                 headers={**H, **({"Content-Type": "application/json"} if data else {})})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        return r.status, (json.loads(raw.decode()) if raw else {})


def put_files(repo, branch, base, files, message=MSG):
    for rel in files:
        content = open(os.path.join(base, rel), "rb").read()
        # Windows git autocrlf may produce CRLF; shell scripts must be LF on Linux runners.
        if rel.endswith(".sh"):
            content = content.replace(b"\r\n", b"\n")
        path = "/repos/%s/contents/%s" % (repo, rel)
        try:
            _, cur = api("GET", path + "?ref=" + branch)
            sha = cur.get("sha")
        except urllib.error.HTTPError:
            sha = None
        body = {"message": message, "content": base64.b64encode(content).decode("ascii"),
                "branch": branch}
        if sha:
            body["sha"] = sha
        st, res = api("PUT", path, body)
        print("PUT", repo, branch, rel, st, res.get("commit", {}).get("sha", "")[:10])


if __name__ == "__main__":
    repo, branch, base = sys.argv[1:4]
    put_files(repo, branch, base, sys.argv[4:])
