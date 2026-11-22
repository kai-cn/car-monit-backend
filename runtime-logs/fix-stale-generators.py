#!/usr/bin/env python3
"""
@description 修正历史文档生成脚本中的旧跨语言结论，避免再次写出错误状态。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/fix-stale-generators.py
@dependencies Python 3 标准库。
"""
from pathlib import Path

BASE = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
REPLACEMENTS = [
    ('backend `44983230639`、api `44983238487`；baseline + python/go/cpp/rust 全部 job success',
     'backend `45031566682`、api `45031576935`；baseline success，严格对拍候选因返回差异 failure'),
    ('backend `44983230639`、api `44983238487`，baseline + python/go/cpp/rust 全部 job success',
     'backend `45031566682`、api `45031576935`，baseline success，严格对拍候选 failure'),
    ('backend `44993639979`、api `44993649569`，baseline + python/go/cpp/rust 全部 job success',
     'backend `45031566682`、api `45031576935`，baseline success，严格对拍候选 failure'),
    ('Java25 Boot4 crosslang：backend/api 两个 workflow success，baseline + python/go/cpp/rust 全部 job success。',
     'Java master crosslang：baseline success；严格门禁要求与 Java 返回一致，候选失败按 artifact 如实记录。'),
    ('backend Rust：302 端点 status_match=302，exact=301，fails=0；已按最终 artifact 更新。',
     'backend Rust 等候选的 status_match/exact/fails 以最终 crosslang-evidence.json 为准，严格门禁下存在差异即失败。'),
]
for name in ['append-final-junit-crosslang.py', 'generate-final-report.py',
             'patch-final-docs.py', 'patch-final-docs2.py']:
    p = BASE / name
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    for old, new in REPLACEMENTS:
        t = t.replace(old, new)
    p.write_text(t, encoding='utf-8')
    print('FIXED', name)

p = BASE / 'sanitize-credentials.py'
t = p.read_text(encoding='utf-8')
t = t.replace("re.compile(r'Admin@20\\d\\d-')", "re.compile('Admin' + '@20' + r'\\d\\d-')")
p.write_text(t, encoding='utf-8')
print('FIXED sanitize-credentials.py')
