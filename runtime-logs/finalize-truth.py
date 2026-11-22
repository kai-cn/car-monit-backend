#!/usr/bin/env python3
"""
@description 将最终严格对拍结论、本机鉴权复测证据和最终 run 号统一写入 canonical runtime-logs 与两仓库 review 文档。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/finalize-truth.py
@dependencies 读取旧 runtime-logs 与 canonical 目录中的证据 JSON。
"""
import json
import shutil
from pathlib import Path

OLD = Path(r'D:\work\runtime-logs')
BASE = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
BK_V3 = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')
API_V3 = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3')
RUNS = [('backend', 45031566682), ('api', 45031576935)]

for name in ['crosslang-evidence.json', 'crosslang-evidence.md']:
    src = OLD / name
    if src.exists():
        shutil.copy2(src, BASE / name)

runs = []
for app, rid in RUNS:
    runs.append({'repo': f'kai-cn/car-monit-{app}', 'app': app, 'ref': 'master',
                 'run_id': rid, 'status': 'completed', 'conclusion': 'failure'})
(BASE / 'crosslang-full-runs.json').write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding='utf-8')
(BASE / 'crosslang-full-results.json').write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding='utf-8')

report = BASE / 'final-java-junit-crosslang-20261122.md'
for p in [BK_V3 / 'docs/v3/review/13-final-junit-crosslang-20261122.md',
          API_V3 / 'docs/v3/review/13-final-junit-crosslang-20261122.md']:
    if report.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report, p)

DOC_FILES = [
    BASE / 'SESSION-HANDOFF.md',
    BASE / '公开仓库安全加固-任务清单.md',
    BASE / '公开仓库安全加固-脚本与证据索引.md',
    API_V3 / '.workbuddy/memory/2026-11-22.md',
    BK_V3 / 'docs/v3/review/12-session-handoff-20261118.md',
    API_V3 / 'docs/v3/review/12-session-handoff-20261118.md',
    BK_V3 / 'docs/v3/review/12-repro-index-20261118.md',
    API_V3 / 'docs/v3/review/12-repro-index-20261118.md',
]
SECTION = '## 2026-11-22 最终严格对拍结论'
TEXT = SECTION + '''

- Java JUnit：16/16 success；本机重新编译打包：16/16 rc=0。
- 本机管理员鉴权复测：302 端点、认证失败 0；压测 533 请求、传输错误 0。
- 跨语言严格门禁：baseline 成功；backend `45031566682`、api `45031576935` 因候选返回与 Java 不一致而 failure。
- 严格门禁要求与 Java 返回一致；所有 DIFF/NONDET 如实保留在 `crosslang-evidence.json`，不得改写为 success。
'''
for p in DOC_FILES:
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    t = t.replace('44993639979', '45031566682').replace('44993649569', '45031576935')
    t = t.replace('baseline + python/go/cpp/rust 全部 job success',
                  'baseline success；严格对拍候选 job failure，返回差异如实记录')
    t = t.replace('最终跨语言：backend `45031566682`、api `45031576935`，baseline + python/go/cpp/rust 全部 job success',
                  '最终跨语言：backend `45031566682`、api `45031576935`，baseline success；严格门禁下候选 failure')
    if SECTION not in t:
        t = t.rstrip() + '\n\n' + TEXT + '\n'
    p.write_text(t, encoding='utf-8')
    print('UPDATED', p)
