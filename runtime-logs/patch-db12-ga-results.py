#!/usr/bin/env python3

"""
@description 历史脚本 patch-db12-ga-results.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-db12-ga-results.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\db12-doc.md')

t = p.read_text(encoding='utf-8')

old = '- 另三个 api 分支（jdk21/jdk17/java-V3）GA 验证 run：`44285673201`/`44285699892`/`44285716860`。'

new = '''- 另三个 api 分支 GA 验证均已恢复并完成（结论 success）：

  - jdk21 run `44285673201`：79 端点 status_match=79、exact=69、semantic=69、nondet=10、**fails=0**；版本串 3.0.0 build 02c14696 → 7.0.0 build 2397a86f。

  - jdk17 run `44285699892`：同上 79/79 **fails=0**。

  - java-V3 run `44285716860`：同上 79/79 **fails=0**。

  - 三分支均使用 `gs_dump`（容器内位置参数 `RuoYi`、uid70 socket）真实迁移，非夹具回退。'''

assert old in t

p.write_text(t.replace(old, new, 1), encoding='utf-8')

print('patched', new in t)

