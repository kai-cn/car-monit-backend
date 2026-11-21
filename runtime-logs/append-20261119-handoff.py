#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：append-20261119-handoff.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
from pathlib import Path

APPENDS = {
    r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md': '''

## 2026-11-19 收尾更新
- 流程：云 runner 快速迭代期间允许先推最小修复；任务收尾前统一独立只读审核。
- DB 升级 GA：3 个暂停 run 均 success（`44285673201`/`44285699892`/`44285716860`），79/79 `fails=0`。
- H9 跨语言：**全部候选 fails=0**。Rust 根因是内嵌默认配置优先于 CWD 磁盘文件，实际仍连 3307；
  已改用 `APP_DATABASE__*` / `APP_REDIS__*` 环境变量覆盖，清理诊断代码后
  run `44521046877`：2 端点 `status_match=2`、semantic=1、nondet=1、**fails=0**。
- H8 backend native：逐层修复 Forest 代理 bean 缺失；jdk25 commit `5d10e75f` 将 7 个 Forest 字段改为
  `@Autowired(required=false)` 并补 import。run `44524395943` 收尾时仍在 native build，结果待最终确认。
''',
    r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''

## J. 2026-11-19 快速迭代脚本与证据
- `patch-backend-forest-optional.py` / `fix-forest-imports.py` / `fix-forest-resource-fields.py`：
  backend native 的 Forest 动态代理字段批量改为 native 可选注入。
- `patch-rust-env-config.py` / `cleanup-rust-diagnostics.py`：Rust 数据源改由 `APP_*` env 覆盖，并清理 trace/探针。
- `patch-rust-direct-probe.py` / `patch-rust-log-pool.py` / `patch-rust-log-trace.py`：临时诊断脚本，已不再需要执行。
- `fix-forest-resource-fields.py` 注意点：字段正则要用 `search` 且从最近注解向上找；此前两版补丁漏改。
- 关键 run：DB GA `44285673201`/`44285699892`/`44285716860`；Rust `44521046877`（fails=0）；
  H8 `44524395943`（收尾时仍在 native build）。
- 关键日志：`h9-rust-directprobe.log`（Connection refused 根因）、`h9-rust-envfix.log`、`h9-rust-clean-final.log`、
  `h8-final-success.log`、`h8-forest-batch-final.log`。
- 远端提交：backend master `440f8073`（移除 Rust 临时探针）；backend jdk25 `5d10e75f`（Forest 字段可选）。
''',
    r'D:\work\runtime-logs\SESSION-HANDOFF.md': '''

## 8. 2026-11-19 收尾交接
- 当前流程：云 runner 快速迭代时先推最小修复；收尾前统一独立审核。
- DB 升级 GA 已全部 success，12 号 DB 文档已补录四分支。
- H9 跨语言已全部 `fails=0`（Java8 基线、Go、Python、Rust）；Rust 根因与 `APP_*` env 修复见当日记忆。
- H8 backend native 仍在快速迭代：Forest 代理字段已批量改为可选注入（`5d10e75f`），
  最终 run `44524395943` 收尾时仍在 native build，需先查结论再决定是否继续。
- 今日工作记忆：`car-monit-api-java-V3/.workbuddy/memory/2026-11-19.md`；
  脚本索引：`公开仓库安全加固-脚本与证据索引.md` J 节。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md': '''

## 2026-11-19 增补
- DB 升级 GA 三分支 run 均 success：79/79 `fails=0`。
- H9 跨语言全部候选 `fails=0`：Rust 通过 `APP_DATABASE__*` / `APP_REDIS__*` env 覆盖内嵌默认配置，
  清理诊断后 run `44521046877` 仍 `fails=0`（302 ms / 14.7 MB / 3.45 ms）。
- H8 backend native：Forest 代理字段批量改为 native 可选注入（jdk25 commit `5d10e75f`），
  最终 run `44524395943` 收尾时仍在 native build，结果待确认。
- 当日工作记忆：`.workbuddy/memory/2026-11-19.md`。
''',
    r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md': '''

## 2026-11-19 增补
- Forest optional 批量补丁：`D:/work/runtime-logs/fix-forest-resource-fields.py`（注意 search + 向上最近注解）。
- Rust env 修复：`D:/work/runtime-logs/patch-rust-env-config.py`、`cleanup-rust-diagnostics.py`。
- 关键 run：Rust `44521046877`、H8 `44524395943`、DB GA `44285673201`/`44285699892`/`44285716860`。
- 关键日志：`h9-rust-clean-final.log`、`h9-rust-directprobe.log`、`h8-final-success.log`。
- 远端提交：backend master `440f8073`，backend jdk25 `5d10e75f`。
''',
}

for path_str, text in APPENDS.items():
    p = Path(path_str)
    if not p.exists():
        print('MISSING', p)
        continue
    cur = p.read_text(encoding='utf-8')
    marker = text.strip().splitlines()[0]
    if marker in cur:
        print('SKIP', p.name)
        continue
    p.write_text(cur.rstrip() + '\n' + text, encoding='utf-8')
    print('APPENDED', p.name)
