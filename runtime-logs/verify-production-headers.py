#!/usr/bin/env python3
"""
@description 校验生产级文件头覆盖范围与脚本语法，防止批量注释引入不可解析文件。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python verify-production-headers.py
@dependencies Python 3 标准库；YAML 校验依赖 PyYAML（缺失时跳过 YAML 语法检查）。
"""
import ast
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')
EXCLUDE = {'__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts',
           'crosslang-evidence', 'junit-logs', 'native-logs', 'local-rerun-check',
           'local-junit-smoke', 'wsl-jars', 'wsl-retest-evidence', 'local-package-evidence'}
REQUIRED = ('@description', '@author', '@date', '@usage', '@dependencies')

py_files = []
other_files = []
for p in sorted(BASE.rglob('*')):
    if p.suffix.lower() not in {'.py', '.ps1', '.sh', '.yml'}:
        continue
    if any(part in EXCLUDE for part in p.parts):
        continue
    (py_files if p.suffix.lower() == '.py' else other_files).append(p)

missing = []
for p in py_files + other_files:
    text = p.read_text(encoding='utf-8', errors='replace')
    head = '\n'.join(text.splitlines()[:25])
    if any(tag not in head for tag in REQUIRED):
        missing.append(p)

syntax_errors = []
for p in py_files:
    try:
        ast.parse(p.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError as e:
        syntax_errors.append((p, str(e)))

yaml_errors = []
try:
    import yaml
    for p in [x for x in other_files if x.suffix.lower() == '.yml']:
        try:
            yaml.safe_load(p.read_text(encoding='utf-8', errors='replace'))
        except Exception as e:
            yaml_errors.append((p, str(e)))
except ImportError:
    pass

print('PY_FILES', len(py_files))
print('HEADER_FILES', len(other_files))
print('MISSING_HEADERS', len(missing))
for p in missing[:30]:
    print(' ', p.relative_to(BASE))
print('PYTHON_SYNTAX_ERRORS', len(syntax_errors))
for p, e in syntax_errors[:30]:
    print(' ', p.relative_to(BASE), e)
print('YAML_ERRORS', len(yaml_errors))
for p, e in yaml_errors[:30]:
    print(' ', p.relative_to(BASE), e)
