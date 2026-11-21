#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：check_remote_file.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, branch, path, needle = sys.argv[1:5]
url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, branch, path)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + get_token(), "User-Agent": "x"})
s = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
print(repo, branch, path, "needle=", needle, "FOUND" if needle in s else "MISSING")
