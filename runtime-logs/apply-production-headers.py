#!/usr/bin/env python3
"""
@description 批量为历史脚本与新维护脚本补充生产级文件头；保留原有逻辑，仅规范化文件级说明。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python apply-production-headers.py
@dependencies 仅依赖 Python 标准库；会扫描固定的 runtime-logs 与两仓库 harness 路径。
"""
import ast
import re
from pathlib import Path

TODAY = '2026-11-22'
AUTHOR = 'AI Assistant'
BASE = Path(r'D:\work\runtime-logs')
PROJECT_FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\scripts\v3\ops\junit\compare_load.py'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\scripts\v3\ops\junit\generate_junit_suite.py'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\scripts\v3\ops\parity\parity_compare.py'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\scripts\v3\ops\junit\compare_load.py'),
    Path(r'D:\work\IdeaProjects\car-monit-api\scripts\v3\ops\junit\generate_junit_suite.py'),
    Path(r'D:\work\IdeaProjects\car-monit-api\scripts\v3\ops\parity\parity_compare.py'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
EXCLUDE_PARTS = {
    '__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts',
    'junit-bk17-artifact', 'junit3-api25-artifact', 'junit3-bk17-artifact',
    'junit-api-v3-artifact', 'junit-api-boot3-artifact', 'junit-bk-v3-artifact',
    'crosslang-evidence', 'junit-logs', 'native-logs', 'local-rerun-check',
    'local-junit-smoke', 'wsl-jars', 'wsl-retest-evidence', 'local-package-evidence',
    'out', 'classes', 'generated', 'contract-reports', 'load-reports',
}
CODING_RE = re.compile(r'^\s*#.*coding[:=]')
TRIPLE_RE = re.compile(r'^(\s*)("""|\'\'\')')


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')


def infer_description(path: Path) -> str:
    name = path.name
    rules = [
        ('dispatch', '派发或重派云端 runner 任务'),
        ('collect', '收集云端 run、job 或 artifact 状态'),
        ('diagnose', '批量提取失败任务错误摘要'),
        ('survey', '只读盘点脚本、注释或配置状态'),
        ('annotate', '批量补充脚本或代码注释'),
        ('patch', '修改 workflow、脚本或测试口径'),
        ('fix', '修复本地或云端验证中暴露的问题'),
        ('generate', '生成测试套件、报告或证据文件'),
        ('compare', '对比基线/候选结果并产出报告'),
        ('push', '通过 Git 或 API 推送本地材料'),
        ('fetch', '从远端读取文件或状态'),
        ('save', '保存日志或证据到本地'),
        ('check', '只读校验环境、语法或结果'),
        ('scan', '扫描远端或本地状态'),
        ('local', '执行本机复测或打包'),
        ('wsl', '驱动 WSL Docker/数据库完成本机验证'),
        ('commit', '创建集中提交或改写指定提交'),
        ('squash', '按提交信息合并历史提交'),
        ('verify', '验证配置、构建或安全不变量'),
        ('restore', '恢复工作树、提交元数据或容器状态'),
        ('probe', '探测 API、端口或解析错误'),
        ('append', '向交接文档追加结构化记录'),
    ]
    low = name.lower()
    purpose = next((desc for key, desc in rules if low.startswith(key)), '执行运维或验证流程中的辅助操作')
    return f'历史脚本 {name}：{purpose}；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。'


def infer_usage(path: Path) -> str:
    n = path.name
    if path.suffix == '.py':
        return f'python {n} [args]；具体参数以脚本 argparse 或源码说明为准。'
    if path.suffix == '.ps1':
        return f'powershell -File {n} [params]；参数含义见脚本原有注释。'
    if path.suffix == '.sh':
        return f'bash {n} [args]；执行前确认目标环境与本地容器状态。'
    return f'GitHub Actions workflow_dispatch 或 push/PR 触发；输入参数见 workflow inputs。'


def infer_dependencies(text: str, path: Path) -> str:
    deps = []
    low = text.lower()
    if 'github.com' in low or 'gh_api' in low or 'get_token' in low:
        deps.append('GitHub API 访问凭据（从本地缓存读取，不落盘）')
    if 'docker' in low:
        deps.append('Docker CLI 与已启动的守护进程')
    if 'mvn' in low or 'maven' in low:
        deps.append('Maven 与对应 JDK')
    if 'java -jar' in low:
        deps.append('Java 运行时')
    if path.suffix == '.py':
        deps.append('Python 3 标准库及脚本原有第三方依赖')
    if path.suffix == '.yml':
        deps.append('GitHub Actions runner、云上数据库容器与 Secrets')
    return '；'.join(deps) if deps else '按脚本原有逻辑准备环境变量、参数与权限。'


def header_lines(path: Path, text: str) -> list[str]:
    desc = infer_description(path)
    usage = infer_usage(path)
    deps = infer_dependencies(text, path)
    return [
        '@description ' + desc,
        '@author ' + AUTHOR,
        '@date ' + TODAY,
        '@usage ' + usage,
        '@dependencies ' + deps,
    ]


def consume_triple(lines: list[str], idx: int) -> tuple[list[str], int]:
    match = TRIPLE_RE.match(lines[idx])
    if not match:
        return [], idx
    delim = match.group(2)
    block = [lines[idx]]
    if delim in lines[idx][len(match.group(1)) + 3:]:
        return block, idx + 1
    idx += 1
    while idx < len(lines):
        block.append(lines[idx])
        if lines[idx].rstrip().endswith(delim):
            return block, idx + 1
        idx += 1
    return block, idx


def process_python(path: Path) -> bool:
    """为单个 Python 脚本生成规范文件头，并保留原有模块说明。"""
    raw = read_text(path)
    if '@description' in '\n'.join(raw.splitlines()[:25]):
        return False
    lines = raw.splitlines(keepends=True)
    prefix_idx = 0
    if lines and lines[0].startswith('#!'):
        prefix_idx = 1
    if prefix_idx < len(lines) and CODING_RE.match(lines[prefix_idx]):
        prefix_idx += 1

    idx = prefix_idx
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    original = ''
    block, end = consume_triple(lines, idx)
    if block:
        inner = '\n'.join(block[1:-1]) if len(block) > 1 else ''
        if 'LEGACY-SCRIPT-ANNOTATION' in inner:
            idx = end
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            block2, end2 = consume_triple(lines, idx)
            if block2:
                original = '\n'.join(block2[1:-1]) if len(block2) > 1 else ''
                idx = end2
        else:
            original = inner
            idx = end

    meta = '\n'.join(header_lines(path, raw))
    doc = f'"""\n{meta}\n'
    if original.strip():
        doc += '\n' + original.strip() + '\n'
    doc += '"""\n'
    new = ''.join(lines[:prefix_idx]) + doc + ''.join(lines[idx:])
    try:
        ast.parse(new)
    except SyntaxError:
        return False
    write_text(path, new)
    return True


def process_hash_header(path: Path) -> bool:
    raw = read_text(path)
    if '@description' in '\n'.join(raw.splitlines()[:25]):
        return False
    lines = raw.splitlines(keepends=True)
    idx = 1 if lines and lines[0].startswith('#!') else 0
    meta = '\n'.join('# ' + x for x in header_lines(path, raw)) + '\n'
    new = ''.join(lines[:idx]) + meta + ''.join(lines[idx:])
    write_text(path, new)
    return True


def main() -> None:
    changed = 0
    skipped = 0
    candidates = []
    for p in sorted(BASE.rglob('*')):
        if p.suffix.lower() not in {'.py', '.ps1', '.sh'}:
            continue
        if any(part in EXCLUDE_PARTS for part in p.parts):
            continue
        candidates.append(p)
    candidates.extend(PROJECT_FILES)
    for p in candidates:
        if not p.exists():
            continue
        ok = process_python(p) if p.suffix.lower() == '.py' else process_hash_header(p)
        if ok:
            changed += 1
        else:
            skipped += 1
    print('CHANGED', changed)
    print('SKIPPED_EXISTING_OR_INVALID', skipped)


if __name__ == '__main__':
    main()
