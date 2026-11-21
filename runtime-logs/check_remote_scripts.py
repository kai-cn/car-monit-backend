#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：check_remote_scripts.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
import base64
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}
repo, branch, path = sys.argv[1:4]
url = "https://api.github.com/repos/%s/contents/%s?ref=%s" % (repo, path, branch)
with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
    d = json.loads(r.read())
b = base64.b64decode(d["content"])
print("bytes", len(b), "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"))
s = b.decode("utf-8", "replace")
for needle in ['"$dbname" -Fp', "OG_NEW_IMAGES", "pick_image"]:
    print(needle, needle in s)
