#!/usr/bin/env python3
"""
@description 历史脚本 append-native-rerun-final.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python append-native-rerun-final.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

A={
 r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md': '''

## 2026-11-21 Native/跨语言重跑收口
- 10 个 Boot3/Boot4 Java 分支 native-image-cloud success；Boot2 无 native profile，标记 N/A。
- crosslang-parity-cloud（backend master, langs=all）success。
- 最终 11/11 run success，证据 `native-crosslang-status.json`，未下载 artifact。
- 关键修复：Mandrel25、Lombok annotationProcessorPaths、LOG_PATH 覆盖、install 阶段注入 LOG_PATH。
- 历史脚本 157 个补齐思路/用途/风险注释，复扫 0 缺失、0 语法跳过。
- Git 凭据改为本地缓存 helper，不再弹 GCM 账号选择框。
''',
 r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''

## N. Native/跨语言重跑与脚本注释
- 派发：`dispatch-native-and-crosslang.py`、`redispatch-java-upgrade.py`。
- 状态：`collect-native-crosslang-status.py`、`native-crosslang-status.json`（11/11 success）。
- 诊断：`diagnose-native-failures.py`、`native-logs/`。
- native 修复：`local-enable-lombok-ap.py`、`local-add-native-logdir.py`、
  `local-fix-native-logdir-condition.py`、`local-inline-native-logdir.py`、
  `local-force-native-logdir.py`、`local-use-temp-logpath.py`、`local-fix-install-step-logpath.py`。
- 脚本注释：`survey-script-comments.py`、`annotate-all-historical-scripts.py`（157 个脚本，复扫 0 缺失）。
- 认证：`git-credential-ghcached.py`、`configure-gh-credential-helper.py`。
''',
 r'D:\work\runtime-logs\SESSION-HANDOFF.md': '''

## 12. 2026-11-21 Native/跨语言重跑收口
- Boot3/Boot4 10 个 Java 分支 native 构建 success；Boot2 无 native profile，N/A。
- 跨语言 workflow success；10 native + 1 crosslang 共 11/11 success。
- 证据 `native-crosslang-status.json`；失败迭代日志 `native-logs/` 仅作过程记录。
- 157 个历史脚本补齐注释，复扫 0 缺失；认证不再弹账号选择框。
- 工作记忆：api-java-V3 `.workbuddy/memory/2026-11-21.md`。
''',
 r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md': '''

## 2026-11-21 Native/跨语言重跑
- Boot3/Boot4 10 个 Java 分支 native success；Boot2 无 native profile，N/A。
- crosslang-parity-cloud success；11/11 云任务 success，证据 `native-crosslang-status.json`。
- Mandrel25 + Lombok annotationProcessorPaths + LOG_PATH 修复完成。
- 157 个历史脚本补齐注释，复扫 0 缺失。
''',
 r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md': '''

## 2026-11-21 Native/跨语言增补
- 派发/状态/诊断：`dispatch-native-and-crosslang.py`、`collect-native-crosslang-status.py`、`diagnose-native-failures.py`。
- 证据：`native-crosslang-status.json`（11/11 success）、`native-logs/`。
- native 修复脚本见本地 `local-*.py`；日志路径修复以 `local-fix-install-step-logpath.py` 为最终有效方案。
- 历史脚本注释：`survey-script-comments.py`、`annotate-all-historical-scripts.py`。
''',
}
for path_str,text in A.items():
    p=Path(path_str)
    if not p.exists():
        print('MISSING',path_str); continue
    cur=p.read_text(encoding='utf-8')
    marker=text.strip().splitlines()[0]
    if marker in cur:
        print('SKIP',p.name); continue
    p.write_text(cur.rstrip()+'\n'+text,encoding='utf-8')
    print('APPENDED',p.name)
