#!/usr/bin/env python3
# @description WSL 版 git credential helper：为 HTTPS github.com 提供缓存 token，避免 GCM 弹窗与交互输入。
#              与 Windows 版 git-credential-ghcached.py 等价，但缓存路径指向 WSL 仓库内的
#              runtime-logs/.gh_token_cache（由 gh_cred.py 管理）。
# @author Tencent Hunyuan Hy
# @date 2026-11-28 16:30:00
# @usage git 通过 `credential.https://github.com.helper` 自动调用；不要直接执行。
# @dependencies gh_cred.py（同目录）、Python 3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_cred import get_token  # noqa: E402

USERNAME = "kai-cn"


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action in ("store", "erase"):
        return 0
    if action != "get":
        return 1

    req = {}
    for line in sys.stdin:
        if "=" in line:
            key, value = line.strip().split("=", 1)
            req[key] = value

    if req.get("protocol") != "https" or req.get("host", "").lower() not in (
        "github.com", "www.github.com"
    ):
        return 1

    try:
        token = get_token()
    except Exception:
        return 1
    if not token:
        return 1

    sys.stdout.write(
        f"protocol=https\nhost=github.com\nusername={USERNAME}\npassword={token}\n\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
