#!/usr/bin/env python3
"""
@description 历史脚本 append-20261119-final.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python append-20261119-final.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

APPENDS = {
    r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-19.md': '''

## runtime-logs 入库与本轮收尾
- 用户将 `D:\\work\\runtime-logs` 复制到 `car-monit-backend-java-V3` 工作树后要求提交到源分支。
- 首次提交 `f9cbd8cb` 被独立审核 BLOCKED：含 `.gh_token_cache`、`*token*.txt`、明文测试口令脚本、日志/压缩包/node_modules。
- 已删除 13 个含字面凭据的脚本/配置，移除 62 个可疑暂存文件，补强 `.gitignore`
  （`*.env`、`*.pw`、`secret-values.env`、日志、token txt、node_modules 等）。
- 修正提交 `a38f49a1` 经独立审核 PASS，并通过 HTTPS 凭据推送到
  `kai-cn/car-monit-backend/car-monit-backend-java-V3`，远端 HEAD 已核验。
- H8 后续：`RoadPathApi` 等所有 Forest `*Api` 字段也已改为可选注入；
  OSS 初始化先用全局 `OSS_ENABLE=false` 导致 JVM 基线失败，已改成仅 native 进程
  `env OSS_ENABLE=false "$NATIVE" ...`；AWS SDK v1 资源 include 使 native 构建约 60 分钟超时，已撤销。
  当前 run `44544743332` 仍在 native build 阶段，结果待确认。
''',
    r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md': '''

## 2026-11-19 最后更新
- runtime-logs 已作为脚本/文档入库 backend 源分支：最终提交 `a38f49a1`（`f9cbd8cb` 被安全审核否决后修正），独立审核 PASS。
- H8：所有 Forest `*Api` 字段改为可选注入；OSS 只在 native 进程禁用；
  AWS SDK v1 资源 include 因 60 分钟超时已撤销。run `44544743332` 仍在 native build，待确认。
- H9：Rust 已通过，Go/Python/Java8 基线均通过；H9 收口完成。
''',
    r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''

## K. runtime-logs 入库与 H8 最新处置
- 入库脚本/文档最终提交：`a38f49a1`（backend/car-monit-backend-java-V3）；`f9cbd8cb` 因明文凭据被否决。
- `.gitignore` 现在排除 `.gh_token_cache`、`*token*.txt`、`*.env`、`*.pw`、`secret-values.env`、
  `*.log/*.err/*.out/*.gz/*.zip/*.csv`、`node_modules/`。
- 安全扫描脚本：`scan-staged-secrets.py`、`show-staged-secret-matches.py`、`unstage-secret-candidates.py`。
- H8 活跃修复脚本：`fix-forest-resource-fields.py`（`*Api` 字段可选注入）、
  `patch-oss-native-only.py`（仅 native 禁用 OSS）。
- H8 已撤销脚本/方案：`patch-aws-sdk-resources.py` / `patch-oss-disable.py`（60 分钟超时、JVM 基线失败）。
- 关键 run：H8 `44544743332`（native build 中）；Rust 最终通过 `44521046877`。
''',
    r'D:\work\runtime-logs\SESSION-HANDOFF.md': '''

## 9. 2026-11-19 最后交接
- runtime-logs 已清理凭据后入库 backend 源分支：最终 `a38f49a1`，独立审核 PASS，HTTPS 推送成功。
- H9 已收口：Java8/Go/Python/Rust 均 fails=0；Rust 通过 `APP_DATABASE__*`/`APP_REDIS__*` env 覆盖内嵌配置。
- H8 仍在快速迭代：所有 Forest `*Api` 字段可选；OSS 只禁用 native 进程；AWS 资源方案已撤销。
  当前 run `44544743332` native build 中，结果待确认。
- 下一会话恢复点：先查 `44544743332`；若仍失败，以完整 app log tail 定位下一阻塞，不再盲试 AWS include。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md': '''

## 2026-11-19 最后增补
- runtime-logs 已清理凭据后入库 backend 源分支，最终提交 `a38f49a1`（先前 `f9cbd8cb` 被安全审核否决）。
- H9 已收口（Java8/Go/Python/Rust 全 fails=0）。
- H8 仍在迭代：`44544743332` native build 中；OSS 仅 native 禁用，AWS SDK 资源 include 已撤销。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md': '''

## 2026-11-19 最后增补
- runtime-logs 入库最终提交：`a38f49a1`（backend/car-monit-backend-java-V3）。
- 凭据清理：`scan-staged-secrets.py`、`show-staged-secret-matches.py`、`unstage-secret-candidates.py`。
- H8 活跃脚本：`fix-forest-resource-fields.py`、`patch-oss-native-only.py`。
- H8 最新 run：`44544743332`（native build 中）；H9 Rust 通过 run：`44521046877`。
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
