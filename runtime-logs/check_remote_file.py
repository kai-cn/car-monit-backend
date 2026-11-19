#!/usr/bin/env python3
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, branch, path, needle = sys.argv[1:5]
url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, branch, path)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + get_token(), "User-Agent": "x"})
s = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
print(repo, branch, path, "needle=", needle, "FOUND" if needle in s else "MISSING")
