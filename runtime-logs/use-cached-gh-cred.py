#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：use-cached-gh-cred.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Make all GitHub API helpers use the fixed-account cached token from gh_cred.py."""
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
