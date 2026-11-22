#!/usr/bin/env python3
"""
@description 收尾修复生产级注释：规范 generate_junit_suite.py 文件头、补齐 yml 文件头、移除反斜杠续行后的空行。
@author AI Assistant
@date 2026-11-22
@usage python finalize-production-headers.py
@dependencies Python 3 标准库；仅处理固定工作目录中的本地文件。
"""
import ast
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')
EXCLUDE = {'__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts',
           'crosslang-evidence', 'junit-logs', 'native-logs', 'local-rerun-check',
           'local-junit-smoke', 'wsl-jars', 'wsl-retest-evidence', 'local-package-evidence'}
TAGS = ('@description', '@author', '@date', '@usage', '@dependencies')


def header(path: Path) -> str:
    usage = ('GitHub Actions workflow_dispatch 或事件触发；输入参数见 workflow inputs。'
             if path.suffix.lower() in {'.yml', '.yaml'} else f'{path.name} 按脚本原有参数执行。')
    return '\n'.join([
        '# @description 历史运维/验证配置快照，保留用于复现与审计；本文件头补充维护背景与运行约束。',
        '# @author AI Assistant',
        '# @date 2026-11-22',
        '# @usage ' + usage,
        '# @dependencies 按原 workflow 声明的 runner、Actions 与外部服务依赖执行。',
    ]) + '\n'


def fix_generate() -> None:
    p = BASE / 'generate_junit_suite.py'
    t = p.read_text(encoding='utf-8', errors='replace')
    marker = '"""Generate Java 8 compatible JUnit 5 full-endpoint contract and load suites.'
    if marker not in t:
        return
    start = t.index('"""\nLEGACY-SCRIPT-ANNOTATION')
    body_start = t.index(marker)
    body_end = t.index('"""', body_start + 3) + 3
    body = t[body_start:body_end]
    new_head = '''"""
@description 从端点清单生成 Java8 兼容的 JUnit5 全接口契约与压测套件；结果以 JSON 记录，便于跨版本/跨语言对比。
@author AI Assistant
@date 2026-11-22
@usage python generate_junit_suite.py --endpoints <file> --out <dir>
@dependencies Python 3 标准库；生成的 Java 源码依赖 JUnit 5 Platform Console 与 JDK 8+。
"""'''
    p.write_text(t[:start] + new_head + '\n' + body + t[body_end:], encoding='utf-8')
    print('FIXED', p.name)


def fix_yaml_headers() -> None:
    count = 0
    for p in sorted(BASE.rglob('*')):
        if p.suffix.lower() not in {'.yml', '.yaml'}:
            continue
        if any(part in EXCLUDE for part in p.parts):
            continue
        t = p.read_text(encoding='utf-8', errors='replace')
        head = '\n'.join(t.splitlines()[:25])
        if all(tag in head for tag in TAGS):
            continue
        lines = t.splitlines(keepends=True)
        idx = 1 if lines and lines[0].strip() == '---' else 0
        p.write_text(''.join(lines[:idx]) + header(p) + ''.join(lines[idx:]), encoding='utf-8')
        count += 1
    print('YAML_HEADERS', count)


def fix_continuations() -> None:
    for p in sorted(BASE.glob('*.py')):
        try:
            t = p.read_text(encoding='utf-8', errors='replace')
            ast.parse(t)
            continue
        except SyntaxError:
            pass
        lines = t.splitlines(keepends=True)
        out = []
        for line in lines:
            if out and out[-1].rstrip('\r\n').rstrip().endswith('\\') and not line.strip():
                continue
            out.append(line)
        new = ''.join(out)
        try:
            ast.parse(new)
        except SyntaxError:
            continue
        p.write_text(new, encoding='utf-8')
        print('FIXED_CONTINUATION', p.name)


def main() -> None:
    fix_generate()
    fix_yaml_headers()
    fix_continuations()


if __name__ == '__main__':
    main()
