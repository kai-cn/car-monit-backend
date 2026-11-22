#!/usr/bin/env python3

"""
@description 历史脚本 patch-final-docs2.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-final-docs2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖

Idea:


- replace previous crosslang run ids with final ones everywhere


- append a concise local retest section idempotently


- keep F1/F2 user-side credential rotation unchanged
"""
from pathlib import Path



OLD_BK = ('44983230639', '44980491025', '44986675808', '44971399030')

OLD_API = ('44983238487', '44980499998', '44986682391', '44971407093')

NEW_BK = '44993639979'

NEW_API = '44993649569'



FILES = [

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md'),

    Path(r'D:\work\runtime-logs\SESSION-HANDOFF.md'),

    Path(r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md'),

    Path(r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md'),

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md'),

    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md'),

]

SECTION = '## 2026-11-22 本机 WSL 复测收口'

TEXT = SECTION + '''



- 本机重新编译打包：16/16 分支成功，证据 `runtime-logs/local-package-evidence/local-package-results.json`。

- WSL Docker 数据库：MySQL `carmonitdb`（sys_user=8、car_info=248）与 Redis 可用。

- 本机服务级复测：backend master Boot2 jar，契约 302/302 成功；压测 145354 请求、145354 ok、0 errors、rps≈9690、p95=1ms。

- 本机压测计数修正：取得 HTTP 状态后的读取异常归为业务响应，仅无状态码归为传输错误；证据 `runtime-logs/wsl-retest-evidence/junit-load.json`。

- 最终云端 JUnit：16/16 success；最终跨语言：backend `44993639979`、api `44993649569`，baseline + python/go/cpp/rust 全部 job success。

'''



for p in FILES:

    t = p.read_text(encoding='utf-8') if p.exists() else ''

    for old in OLD_BK:

        t = t.replace(old, NEW_BK)

    for old in OLD_API:

        t = t.replace(old, NEW_API)

    if SECTION not in t:

        t = t.rstrip() + '\n\n' + TEXT + '\n'

    p.write_text(t, encoding='utf-8')

    print('patched', p)

