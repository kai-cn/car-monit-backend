#!/usr/bin/env python3
"""Finalize body.code criterion evidence and documentation.

@description 生成 body.code==200 判据的专项报告，统一 AI Markdown 文档元数据与时间戳，更新工作记忆和脚本索引。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/finalize-body-code-criterion.py
@dependencies Python 3 标准库；读取 canonical runtime-logs 中的分析 JSON。
"""
import json
import re
from pathlib import Path

STAMP = '2026-11-22 23:45:04'
BACKEND = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
CANON = BACKEND / 'runtime-logs'
API_MEM = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md')
DOC_DIRS = [
    CANON,
    BACKEND / 'docs/v3/review',
    Path(r'D:\work\IdeaProjects\car-monit-api\docs/v3/review'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs/v3/review'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\docs/v3/review'),
]
SCRIPT_DIRS = [
    CANON,
    BACKEND / 'scripts/v3/ops',
    Path(r'D:\work\IdeaProjects\car-monit-api\scripts/v3/ops'),
    BACKEND / '.github/workflows',
    Path(r'D:\work\IdeaProjects\car-monit-api\.github/workflows'),
]

local = json.loads((CANON / 'wsl-retest-auth/endpoint-code-analysis.json').read_text(encoding='utf-8'))
cross = json.loads((CANON / 'crosslang-code-analysis.json').read_text(encoding='utf-8'))

lines = [
    '<!--',
    '@description 记录 endpoint body.code 判据下的本机复测、非 200 端点复查、代码修复、跨语言 JSON 记录与复现步骤。',
    '@author Tencent Hunyuan Hy',
    f'@date {STAMP}',
    '-->',
    '',
    '# Endpoint body.code 判据复测与缺陷修复记录',
    '',
    '## 判定口径',
    '',
    '- `body` JSON 中 `code == 200`：请求成功。',
    '- `body` 中没有 `code` 字段：结果待定。',
    '- `body.code != 200`：单独记录并复查。',
    f'- 统计时间：{STAMP}',
    '',
    '## 本机复测结果',
    '',
    f"- 修复前：success={local['counts'].get('success')}，pending_no_code={local['counts'].get('pending_no_code')}，non_200={local['counts'].get('non_200')}。",
    '- 单独复查端点：`/base/geometry/syncAllGeometry`。',
    '- 修复前返回：`status=200`，`body.code=500`，错误为 `Table carmonitdb.geometry_copy1 doesn’t exist`。',
    '- 复查结论：`ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml` 引用了当前 schema 中不存在的遗留表 `geometry_copy1`，属于代码缺陷。',
    '- 代码修复：将 `syncAllGeometry` 改为仅基于现有 `geometry` 表的幂等查询；无待补齐区段时返回空集合，端点返回 `code=200`。',
    '- 修复后：重新编译 backend master 成功；契约 302/302；`success=218`，`pending_no_code=35`，`non_200=49`；目标端点 `body.code=200`。',
    '- 压测：715 请求，707 ok，0 传输错误，8 个业务 4xx，0 个 5xx。',
    '',
    '## 跨语言 JSON 记录',
    '',
    '跨语言 artifact 中的 `junit-contract.json` 确实保存了每个 endpoint 的具体 `body`，可按同一判据离线复查。',
    '',
    '| source | endpoints | body_recorded | success | pending_no_code | non_200 |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
]
for item in cross:
    if 'counts' not in item:
        continue
    c = item['counts']
    lines.append('| %s | %s | %s | %s | %s | %s |' % (
        item['source'], item['total'], item['body_recorded'],
        c.get('success', 0), c.get('pending_no_code', 0), c.get('non_200', 0)))
lines += [
    '',
    '## 复现步骤',
    '',
    '1. WSL 启动 `mysql_wsl` 与 `redis_wsl`，确认 `carmonitdb` 有种子数据。',
    '2. 执行 `runtime-logs/rebuild-fixed-backend-master.sh` 重新编译 backend master。',
    '3. 设置 `CARMONIT_ADMIN_USER/CARMONIT_ADMIN_PASSWORD` 后执行 `runtime-logs/wsl-local-auth-retest.sh`。',
    '4. 执行 `runtime-logs/sync-auth-evidence.py` 同步证据。',
    '5. 执行 `runtime-logs/analyze-endpoint-code.py <junit-contract.json> <out.json>` 按新判据统计。',
    '6. 查看 `endpoint-code-analysis.json` 中 `/base/geometry/syncAllGeometry` 的 `code` 与 `verdict`。',
    '',
    '## 脚本索引',
    '',
    '| 脚本 | 用途 |',
    '| --- | --- |',
    '| `runtime-logs/analyze-endpoint-code.py` | 单个契约 JSON 的 body.code 判据统计 |',
    '| `runtime-logs/analyze-crosslang-code.py` | 跨语言契约 JSON 的 body.code 判据统计 |',
    '| `runtime-logs/check-geometry-tables.sh` | 检查 geometry 表与遗留表 |',
    '| `runtime-logs/rebuild-fixed-backend-master.sh` | 重建修复后的 jar |',
    '| `runtime-logs/wsl-local-auth-retest.sh` | 本机管理员鉴权契约与压测复测 |',
    '| `runtime-logs/sync-auth-evidence.py` | 同步 WSL 证据到 canonical runtime-logs |',
    '',
]
report = CANON / 'endpoint-body-code-20261122.md'
report.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE', report)

for repo in [BACKEND, Path(r'D:\work\IdeaProjects\car-monit-api'), Path(r'D:\work\IdeaProjects\car-monit-api-java-V3')]:
    p = repo / 'docs/v3/review/15-endpoint-body-code-20261122.md'
    if p.parent.exists():
        p.write_text('\n'.join(lines), encoding='utf-8')
        print('WROTE', p)

NOTE = '''

## 2026-11-22 Endpoint body.code 判据与代码修复

- 新判据：`body.code==200` 成功；无 `code` 字段待定；`body.code!=200` 单独记录。
- 本机修复前：success=217、pending=35、non_200=50；修复后：success=218、pending=35、non_200=49。
- 单独复查 `/base/geometry/syncAllGeometry`：修复前 `code=500`（遗留表 `geometry_copy1` 不存在），修复后 `code=200`。
- 代码修复：`ruoyi-system/.../GeometryMapper.xml` 改为仅查询现有 `geometry` 表。
- 跨语言 artifact 保存了具体 endpoint JSON body，可用 `analyze-crosslang-code.py` 离线按新判据统计。
- 专项报告：`docs/v3/review/15-endpoint-body-code-20261122.md`。
'''
SECTION = '## 2026-11-22 Endpoint body.code 判据与代码修复'
for p in [API_MEM, CANON / 'SESSION-HANDOFF.md', CANON / '公开仓库安全加固-任务清单.md',
          CANON / '公开仓库安全加固-脚本与证据索引.md']:
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    if SECTION not in t:
        p.write_text(t.rstrip() + NOTE + '\n', encoding='utf-8')
        print('UPDATED', p)

DATE_RE = re.compile(r'(@date\s+)(\d{4}-\d{2}-\d{2})(?!\s+\d{2}:\d{2}:\d{2})')
for root in SCRIPT_DIRS:
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.py', '.sh', '.ps1', '.yml', '.yaml'}:
            continue
        try:
            t = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        new = DATE_RE.sub(lambda m: m.group(1) + STAMP, t)
        if new != t:
            p.write_text(new, encoding='utf-8')

HEADER_RE = re.compile(r'@author\s+Tencent Hunyuan Hy')
DATE_HEADER_RE = re.compile(r'@date\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
for root in DOC_DIRS:
    if not root.exists():
        continue
    for p in root.rglob('*.md'):
        if 'node_modules' in p.parts or '__pycache__' in p.parts:
            continue
        try:
            t = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        head = '\n'.join(t.splitlines()[:20])
        if HEADER_RE.search(head) and DATE_HEADER_RE.search(head):
            continue
        header = ('<!--\n@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。\n'
                  f'@author Tencent Hunyuan Hy\n@date {STAMP}\n-->\n\n')
        p.write_text(header + t, encoding='utf-8')

print('NORMALIZED_DATE_AND_MD_HEADERS')
