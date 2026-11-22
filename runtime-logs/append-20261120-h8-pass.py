#!/usr/bin/env python3
"""
@description 历史脚本 append-20261120-h8-pass.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python append-20261120-h8-pass.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

APPENDS = {
    r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md': '''

## 2026-11-20 H8 收官
- H8 backend native 已通过：run `44683333011`，2 端点 `status_match=2`、**fails=0**。
- 性能：JVM/native 启动 16826/3613 ms，RSS 624.9/395.0 MB，延迟 307.77/6.24 ms。
- 修复：Forest `*Api` 字段可选；`SysFileServiceImpl` 移除 Lombok 全参构造；
  `OssTemplate` 初始化异常降级；AWS 资源 include 撤销。
- H8 与 H9 均已收口，剩余仅 F1/F2 用户侧真实凭据轮换。
''',
    r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''

## L. H8 收官脚本与证据
- 关键 run：`44683333011`（H8 backend native，fails=0）。
- 关键日志：`h8-final-pass.log`，统一报告在 job 日志 `backend-jdk25-linux parity report`。
- 活跃修复：
  - `fix-forest-resource-fields.py`（所有 `*Api`/`Http*Service` 字段可选注入）
  - `patch-sysfile-ctor.py`（移除 Lombok `@AllArgsConstructor`，字段注入）
  - `patch-osstemplate-native.py`（OSS 初始化异常降级）
- 已撤销：`patch-aws-sdk-resources.py`（60 分钟超时）、`patch-oss-disable.py`（JVM 基线失败）。
- `oss.enable=false` 仍保留在 native 命令行，但最终生效的是代码降级兜底。
''',
    r'D:\work\runtime-logs\SESSION-HANDOFF.md': '''

## 10. 2026-11-20 H8 收官
- H8 backend native 已通过，run `44683333011`：2 端点 `status_match=2`、`nondet=2`、**fails=0**。
- 性能：启动 16826→3613 ms，RSS 624.9→395.0 MB，延迟 307.77→6.24 ms。
- 修复要点：Forest 字段可选、SysFileServiceImpl 去 Lombok 全参构造、OssTemplate 初始化降级、AWS 资源 include 撤销。
- H8+H9 均已收口；剩余 F1/F2 用户侧真实凭据轮换。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md': '''

## 2026-11-20 H8 收官
- H8 backend native 已通过：run `44683333011`，2 端点 `status_match=2`、**fails=0**。
- 性能：启动 16826→3613 ms，RSS 624.9→395.0 MB，延迟 307.77→6.24 ms。
- 修复：Forest 可选注入、去 Lombok 全参构造、OSS 初始化降级；AWS 资源 include 撤销。
- H8/H9 全部收口；剩余仅用户侧 F1/F2 凭据轮换。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md': '''

## 2026-11-20 H8 收官增补
- 最终 run：`44683333011`（backend jdk25 native vs JVM，fails=0）。
- 日志：`h8-final-pass.log`。
- 活跃脚本：`fix-forest-resource-fields.py`、`patch-sysfile-ctor.py`、`patch-osstemplate-native.py`。
- 已撤销方案：`patch-aws-sdk-resources.py`、`patch-oss-disable.py`。
''',
}

for path_str, text in APPENDS.items():
    p = Path(path_str)
    if not p.exists():
        print('MISSING', path_str)
        continue
    cur = p.read_text(encoding='utf-8')
    marker = text.strip().splitlines()[0]
    if marker in cur:
        print('SKIP', p.name)
        continue
    p.write_text(cur.rstrip() + '\n' + text, encoding='utf-8')
    print('APPENDED', p.name)
