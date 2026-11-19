#!/usr/bin/env python3
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
