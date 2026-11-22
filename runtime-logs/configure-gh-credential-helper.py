#!/usr/bin/env python3
"""
@description 历史脚本 configure-gh-credential-helper.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python configure-gh-credential-helper.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

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
