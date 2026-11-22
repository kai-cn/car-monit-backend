#!/usr/bin/env python3
"""一次性配置 Git：github.com 使用本地 token 缓存 helper，不再弹 GCM 账号框。

思路：
- Git 会按配置顺序调用 credential helper；system gitconfig 中的 manager 会弹账号选择框。
- 对 `credential.https://github.com.helper` 先写入一个空值，Git 语义是清空此前 helper；
  再追加我们自己的 helper，这样只影响 github.com，不破坏其他站点的 GCM 配置。
- 用 Python subprocess 传参，避免 PowerShell 丢掉空字符串参数。

验证：`git credential fill` 只输出 username/password 键；不应弹出窗口。
"""
import subprocess

KEY = 'credential.https://github.com.helper'
HELPER = '!python D:/work/runtime-logs/git-credential-ghcached.py'

subprocess.run(['git', 'config', '--global', '--unset-all', KEY], check=False,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
subprocess.run(['git', 'config', '--global', '--add', KEY, ''], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
subprocess.run(['git', 'config', '--global', '--add', KEY, HELPER], check=True,
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
r = subprocess.run(['git', 'config', '--global', '--get-all', KEY], check=True,
                   capture_output=True, text=True)
print('CONFIGURED:')
print(r.stdout.strip())
