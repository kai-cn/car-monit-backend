#!/usr/bin/env python3

"""
@description 历史脚本 use-cached-gh-cred.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python use-cached-gh-cred.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import re

from pathlib import Path



ROOT = Path(r'D:\work\runtime-logs')

FILES = [

    'add_deploy_key.py', 'do_rotate_temp.py', 'set_gh_secrets.py',

    'update_gh_secrets.py', 'gh_joblog.py', 'save_joblog.py',

    'save_full_joblog.py', 'download_artifact.py',

]



changed = []

for name in FILES:

    p = ROOT / name

    text = p.read_text(encoding='utf-8', errors='replace')

    m = re.search(r'(?ms)^def (token|get_token)\(\):\n.*?(?=^\S|\Z)', text)

    if not m:

        print('SKIP no-token-func', name)

        continue

    fn = m.group(1)

    new_fn = (f'def {fn}():\n'

              '    # Fixed account (kai-cn) cached token; avoids GCM account picker.\n'

              '    from gh_cred import get_token as _cached_get_token\n'

              '    return _cached_get_token()\n\n')

    text = text[:m.start()] + new_fn + text[m.end():]

    p.write_text(text, encoding='utf-8')

    changed.append(name)

print('patched', len(changed), ', '.join(changed))

