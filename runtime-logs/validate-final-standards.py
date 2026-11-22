#!/usr/bin/env python3
"""Validate final annotation, timestamp, syntax and secret requirements.

@description 校验脚本时间戳、AI Markdown 元数据、Python/YAML 语法及仓库内敏感信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/validate-final-standards.py
@dependencies Python 3 标准库；PyYAML 可选。
"""
import ast
import os
import re
from pathlib import Path

ROOTS = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new'),
    Path(r'D:\work\IdeaProjects\car-monit-api'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3'),
]
SKIP = {'__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts',
        'target', 'build', '_deps', '.claude', 'out'}
STAMP = re.compile(r'@date\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
ADMIN_PATTERN = 'Admin' + '@20' + r'\d\d-'
EXPORT_PATTERN = 'wK' + 'laJ6'
SECRET = re.compile(ADMIN_PATTERN + '|' + EXPORT_PATTERN + '|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}')

py_bad, yaml_bad, md_missing, stamp_missing, secret_hits = [], [], [], [], []
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() not in {'.py', '.sh', '.ps1', '.yml', '.yaml', '.md'}:
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            if SECRET.search(text):
                secret_hits.append(str(p))
            head = '\n'.join(text.splitlines()[:25])
            if p.suffix.lower() in {'.py', '.sh', '.ps1', '.yml', '.yaml'} and '@date' in head and not STAMP.search(head):
                stamp_missing.append(str(p))
            if p.suffix.lower() == '.md' and ('review' in p.parts or 'runtime-logs' in p.parts or '.workbuddy' in p.parts):
                if '@author' not in head or not STAMP.search(head):
                    md_missing.append(str(p))
            if p.suffix.lower() == '.py':
                try:
                    ast.parse(text)
                except SyntaxError as e:
                    py_bad.append(f'{p}: {e}')
            if p.suffix.lower() in {'.yml', '.yaml'} and p.name != 'bad-selfhosted.yml':
                try:
                    import yaml
                    list(yaml.safe_load_all(text))
                except Exception as e:
                    yaml_bad.append(f'{p}: {e}')

for label, items in [('PY_SYNTAX_BAD', py_bad), ('YAML_BAD', yaml_bad),
                     ('TIMESTAMP_MISSING', stamp_missing), ('MD_METADATA_MISSING', md_missing),
                     ('SECRET_HITS', secret_hits)]:
    print(label, len(items))
    for x in items[:10]:
        print(' ', x)
