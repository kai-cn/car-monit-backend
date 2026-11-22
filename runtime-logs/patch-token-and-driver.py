#!/usr/bin/env python3
"""
@description 让鉴权助手兼容无 /login 的 api 服务，并为 backend Java/Python 显式关闭 p6spy 驱动。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/patch-token-and-driver.py
@dependencies 修改 backend master runtime-logs 与两仓库 master 工作树。
"""
from pathlib import Path

ROOT = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
p = ROOT / 'junit-auth-token.py'
t = p.read_text(encoding='utf-8')
t = t.replace('import urllib.request\n', 'import urllib.error\nimport urllib.request\n', 1)
old = '''    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode('utf-8', errors='replace')
    m = re.search(r'"token"\\s*:\\s*"([^"]+)"', text)
    if not m:
        raise SystemExit('Login response has no token: ' + text[:200])
    print(m.group(1))
'''
new = '''    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        # api 服务未暴露 /login；跳过 Header，由基线/候选统一按匿名响应对拍。
        if e.code == 404:
            return
        raise
    m = re.search(r'"token"\\s*:\\s*"([^"]+)"', text)
    if not m:
        raise SystemExit('Login response has no token: ' + text[:200])
    print(m.group(1))
'''
assert old in t
p.write_text(t.replace(old, new, 1), encoding='utf-8')

for repo in [Path(r'D:\work\IdeaProjects\car-monit-backend-new'), Path(r'D:\work\IdeaProjects\car-monit-api')]:
    wf = repo / '.github/workflows/crosslang-full-parity-cloud.yml'
    t = wf.read_text(encoding='utf-8')
    old_env = "          SPRING__DATASOURCE__DRUID__MASTER__PASSWORD: root\n"
    if old_env in t and 'SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME' not in t:
        t = t.replace(old_env, old_env + "          SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME: com.mysql.cj.jdbc.Driver\n")
    old_token = '''          TOKEN=$(python3 harness/scripts/v3/ops/junit/junit-auth-token.py --base-url "$BASE_URL")
          export ENDPOINT_HEADERS="Authorization: Bearer ${TOKEN}"
'''
    new_token = '''          TOKEN=$(python3 harness/scripts/v3/ops/junit/junit-auth-token.py --base-url "$BASE_URL")
          if [ -n "$TOKEN" ]; then export ENDPOINT_HEADERS="Authorization: Bearer ${TOKEN}"; fi
'''
    t = t.replace(old_token, new_token)
    wf.write_text(t, encoding='utf-8')
    # 同步 harness 副本
    target = repo / 'scripts/v3/ops/junit/junit-auth-token.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(p.read_text(encoding='utf-8'), encoding='utf-8')
    print('PATCHED', repo)
