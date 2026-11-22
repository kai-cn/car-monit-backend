#!/usr/bin/env python3
"""
@description 追加生产级注释规范落地记录、已办/待办、脚本与证据索引、复现步骤引用。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python append-production-annotation-docs.py
@dependencies 只改写本地交接 Markdown，幂等检查章节标题。
"""
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')
MEM = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md')

MEM_SECTION = '''## 2026-11-22 生产级注释规范落地

### 已办（DONE）
- 按用户提供规范为历史脚本和新增工程代码补齐文件头：`@description/@author/@date/@usage/@dependencies`。
- `apply-production-headers.py` 处理 631 个脚本，`finalize-production-headers.py` 再补 41 个 YAML 头并修复 3 个历史续行语法问题。
- `verify-production-headers.py` 结果：`MISSING_HEADERS 0`、`PYTHON_SYNTAX_ERRORS 0`；`bad-selfhosted.yml` 是故意保留的负向审计样本。
- 关键 Python 脚本补齐函数级中文 docstring：`generate_junit_suite.py`、`compare_load.py`、`parity_compare.py`。
- 生成的 Java 契约/压测套件补齐类级与方法级 Javadoc，生成后 Java8 编译通过。

### 待办（TODO）
- F1：用户在外部系统轮换真实凭据。
- F2：轮换后更新两仓库 GitHub Secrets；仓库中只保留测试值/占位值。
'''

DOC_SECTION = '''## 2026-11-22 生产级注释、复现与证据索引

- 已办：历史脚本与新生成工程代码统一补齐生产级文件头；Python 关键函数补中文 docstring；生成 Java 套件补 Javadoc。
- 校验：`MISSING_HEADERS 0`、`PYTHON_SYNTAX_ERRORS 0`；`bad-selfhosted.yml` 为负向审计样本，YAML 解析失败是预期。
- 从头复现：`D:\\work\\runtime-logs\\从头复现步骤-20261122.md`，覆盖云端 JUnit、跨语言、本机打包、WSL 服务复测、注释校验。
- 测试与压测证据：
  - `java-junit-results.json`：16/16 cloud success。
  - `crosslang-full-results.json` / `crosslang-evidence.json`：跨语言 workflow 与真实对齐差异。
  - `local-package-evidence/local-package-results.json`：本机 16/16 打包成功。
  - `wsl-retest-evidence/junit-contract.json`、`junit-load.json`：本机 302/302、145354 请求、0 errors。
- 待办：F1/F2 用户侧真实凭据外部轮换与 Secrets 更新。
'''

FILES = [
    BASE / 'SESSION-HANDOFF.md',
    BASE / '公开仓库安全加固-任务清单.md',
    BASE / '公开仓库安全加固-脚本与证据索引.md',
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\docs\v3\review\12-session-handoff-20261118.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md'),
]

for p in FILES:
    t = p.read_text(encoding='utf-8') if p.exists() else '# Handover\n\n'
    if '## 2026-11-22 生产级注释、复现与证据索引' not in t:
        p.write_text(t.rstrip() + '\n\n' + DOC_SECTION + '\n', encoding='utf-8')
        print('APPENDED', p)

t = MEM.read_text(encoding='utf-8') if MEM.exists() else '# 2026-11-22 工作记忆\n\n'
if '## 2026-11-22 生产级注释规范落地' not in t:
    MEM.write_text(t.rstrip() + '\n\n' + MEM_SECTION + '\n', encoding='utf-8')
    print('APPENDED', MEM)
