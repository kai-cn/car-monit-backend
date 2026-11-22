#!/usr/bin/env python3

"""
@description 历史脚本 dedupe-handoff.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python dedupe-handoff.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md')

t = p.read_text(encoding='utf-8')

block = '''## 2026-11-19 最后增补

- runtime-logs 已清理凭据后入库 backend 源分支，最终提交 `a38f49a1`（先前 `f9cbd8cb` 被安全审核否决）。

- H9 已收口（Java8/Go/Python/Rust 全 fails=0）。

- H8 仍在迭代：`44544743332` native build 中；OSS 仅 native 禁用，AWS SDK 资源 include 已撤销。

'''

print('count before', t.count(block))

if t.count(block) == 2:

    first = t.index(block)

    second = t.index(block, first + len(block))

    t = t[:second] + t[second + len(block):]

p.write_text(t, encoding='utf-8')

print('count after', t.count(block))

