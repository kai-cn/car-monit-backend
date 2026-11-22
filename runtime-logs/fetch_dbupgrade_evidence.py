#!/usr/bin/env python3
# 用途：下载 db-upgrade-cloud run 的证据 artifact 并解包到本地目录（token 来自缓存）。
# 用法：python fetch_dbupgrade_evidence.py <repo> <run_id> <out_dir>
import io
import os
import sys
import urllib.request
import zipfile

sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

repo, run_id, out_dir = sys.argv[1:4]
H = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",
     "Authorization": "Bearer " + get_token()}


def get(path):
    with urllib.request.urlopen(urllib.request.Request(
            "https://api.github.com" + path, headers=H), timeout=60) as r:
        return json.loads(r.read()) if False else r.read()


import json
arts = json.loads(get("/repos/%s/actions/runs/%s/artifacts?per_page=100" % (repo, run_id)))
os.makedirs(out_dir, exist_ok=True)
for a in arts.get("artifacts", []):
    name = a["name"]
    if not name.startswith("dbupgrade-"):
        continue
    dest = os.path.join(out_dir, name)
    if os.path.exists(dest + ".zip"):
        print("SKIP exists", name); continue
    print("FETCH", name, a.get("size_in_bytes"), "bytes")
    req = urllib.request.Request(a["archive_download_url"], headers=H)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(os.path.join(out_dir, name))
    print("  ->", dest)
print("DONE out_dir=%s" % out_dir)
