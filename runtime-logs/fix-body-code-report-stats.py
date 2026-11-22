#!/usr/bin/env python3
"""Fix before/after statistics in the body.code report.

@description 修正专项报告中修复前后统计，并生成修复前端点证据摘要。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/fix-body-code-report-stats.py
@dependencies Python 3 标准库。
"""
import json
from pathlib import Path

CANON = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
before = {
    'phase': 'before_fix',
    'counts': {'success': 217, 'pending_no_code': 35, 'non_200': 50},
    'selected_endpoint': {
        'endpoint': '/base/geometry/syncAllGeometry',
        'status': 200,
        'code': 500,
        'body_prefix': '{"msg":"\\n### Error querying database.  Cause: java.sql.SQLSyntaxErrorException: Table \'carmonitdb.geometry_copy1\' doesn\'t exist',
    },
}
(CANON / 'wsl-retest-auth/endpoint-code-analysis-before-fix.json').write_text(
    json.dumps(before, indent=2, ensure_ascii=False), encoding='utf-8')

old = '- 修复前：success=218，pending_no_code=35，non_200=49。'
new = '- 修复前：success=217，pending_no_code=35，non_200=50。'
for p in [CANON / 'endpoint-body-code-20261122.md',
          Path(r'D:\work\IdeaProjects\car-monit-backend-new\docs\v3\review\15-endpoint-body-code-20261122.md'),
          Path(r'D:\work\IdeaProjects\car-monit-api\docs\v3\review\15-endpoint-body-code-20261122.md'),
          Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\15-endpoint-body-code-20261122.md')]:
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8').replace(old, new)
    p.write_text(t, encoding='utf-8')
    print('FIXED', p)
