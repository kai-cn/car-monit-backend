#!/usr/bin/env python3

"""
@description 历史脚本 patch-final-docs.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-final-docs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- replace stale crosslang run ids everywhere


- replace stale backend Rust parity summary with final numbers


- append a final report reference section idempotently
"""
from pathlib import Path



FILES = [

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md'),

    Path(r'D:\work\runtime-logs\SESSION-HANDOFF.md'),

    Path(r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md'),

    Path(r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md'),

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md'),

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md'),

]

SECTION = '## 2026-11-22 最终全量验证报告引用'

TEXT = SECTION + '''



- 最终报告：`docs/v3/review/13-final-junit-crosslang-20261122.md`

- Java JUnit：16/16 success。

- crosslang workflow：backend `45031566682`、api `45031576935`，baseline success，严格对拍候选 failure。

- 对齐差异与压测比值为 artifact 真实记录，未用断言掩盖。

'''



for p in FILES:

    t = p.read_text(encoding='utf-8') if p.exists() else ''

    t = t.replace('44980491025', '44983230639').replace('44980499998', '44983238487')

    t = t.replace('backend Rust：302 端点 status_match=0，fails=302，已如实记录。',

                  'backend Rust 等候选的 status_match/exact/fails 以最终 crosslang-evidence.json 为准，严格门禁下存在差异即失败。')

    if SECTION not in t:

        t = t.rstrip() + '\n\n' + TEXT + '\n'

    p.write_text(t, encoding='utf-8')

    print('patched', p)

