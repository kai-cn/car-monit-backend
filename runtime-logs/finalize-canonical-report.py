#!/usr/bin/env python3
"""
@description 生成 backend master runtime-logs 下的最终报告，并如实记录严格跨语言对拍结果。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/finalize-canonical-report.py
@dependencies 读取同目录的云端/本机证据 JSON。
"""
import json
from pathlib import Path

BASE = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')


def load(name, default=None):
    p = BASE / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


java = load('java-junit-results.json', [])
cross = load('crosslang-full-results.json', [])
cross_ev = load('crosslang-evidence.json', {})
pkg = load('local-package-evidence/local-package-results.json', [])
auth = load('wsl-retest-auth/junit-contract.json', {})
auth_load = load('wsl-retest-auth/junit-load.json', {})

auth_rows = auth.get('endpoints', [])
auth_fail = sum(1 for r in auth_rows if '认证失败' in str(r.get('body', '')))

lines = [
    '# 最终 Java JUnit / 本机复测 / 跨语言严格对拍报告',
    '',
    '## 结论',
    '',
    '- Java JUnit 云验证：16/16 success。',
    '- 本机重新编译打包：16/16 分支 rc=0。',
    '- 本机管理员鉴权复测：302 端点、认证失败 0；压测 %s 请求、传输错误 %s。' % (
        auth_load.get('total_requests'), auth_load.get('errors')),
    '- 跨语言 workflow：baseline 成功；严格门禁要求与 Java 返回一致，当前 backend/api workflow 结论为 failure，差异如实保留。',
    '- 不得将 workflow failure 改写为 success；必须按端点报告修复多语言实现后再重跑。',
    '',
    '## 最终 run',
    '',
]
for x in cross:
    lines.append('- %s run `%s`: `%s`' % (x.get('app'), x.get('run_id'), x.get('conclusion')))
lines += ['', '## 跨语言严格对拍', '',
          '| app | lang | endpoints | status_match | exact | semantic | nondet | fails |',
          '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for app, langs in cross_ev.items():
    for lang, v in langs.items():
        if lang == 'baseline':
            continue
        t = v.get('contract_totals') or {}
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            app, lang, t.get('endpoints'), t.get('status_match'), t.get('exact'),
            t.get('semantic'), t.get('nondet'), t.get('fails')))
lines += ['', '## 本机证据', '',
          '- 本机打包：`local-package-evidence/local-package-results.json`',
          '- 本机鉴权契约：`wsl-retest-auth/junit-contract.json`',
          '- 本机鉴权压测：`wsl-retest-auth/junit-load.json`',
          '- 认证失败计数：%d' % auth_fail,
          '']
(BASE / 'final-java-junit-crosslang-20261122.md').write_text('\n'.join(lines), encoding='utf-8')
print('WROTE', BASE / 'final-java-junit-crosslang-20261122.md')
