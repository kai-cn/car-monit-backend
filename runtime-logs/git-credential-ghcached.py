#!/usr/bin/env python3
"""Git credential helper: use the cached GitHub token without GCM account picker.

设计思路：
- Git 在 HTTPS push/fetch 时调用 credential helper；GCM 默认会弹出账号选择框。
- 这里实现一个最小 helper：只处理 protocol=https、host=github.com，
  输出固定账号 kai-cn 和 .gh_token_cache 中的 token。
- 直接读缓存文件，不调用 gh_cred.get_token()，避免 helper 递归调用 git credential fill。
- store/erase 不做任何事：token 已由 gh_cred.py 管理，Git 不应再写入其他凭据存储。

配置方式（一次性）：
  git config --global --unset-all credential.https://github.com.helper
  git config --global --add credential.https://github.com.helper ''
  git config --global --add credential.https://github.com.helper '!python D:/work/runtime-logs/git-credential-ghcached.py'
第一条空值用于清掉 system/global 的 manager helper，避免它先弹框；第二条注册本 helper。
"""
import os
import sys
from pathlib import Path

CACHE = Path(r'D:\work\runtime-logs\.gh_token_cache')
USERNAME = 'kai-cn'


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action in ('store', 'erase'):
        return 0
    if action != 'get':
        return 1

    req = {}
    for line in sys.stdin:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            req[k] = v
    if req.get('protocol') != 'https' or req.get('host', '').lower() not in ('github.com', 'www.github.com'):
        return 1

    try:
        token = CACHE.read_text(encoding='utf-8').strip()
    except Exception:
        return 1
    if not token:
        return 1

    sys.stdout.write(
        f'protocol=https\nhost=github.com\nusername={USERNAME}\npassword={token}\n\n'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
