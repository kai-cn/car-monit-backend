#!/usr/bin/env python3

"""
@description 历史脚本 append-commit-squash.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python append-commit-squash.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path



A={

 r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-21.md': '''



## 提交历史整理

- 新增通用脚本 `squash-commits-by-message.py`：按提交信息精确匹配，把连续目标提交区间合并为一个提交。

- 支持 --repo/--branch/--message/--new-message，默认 dry-run；--apply 才写远端。

- 护栏：拒绝 main/master，force-with-lease，写前创建 backup ref。

- 已对 `car-monit-backend-java-V3` 执行：394 个 `docs(scripts): add rationale and risk notes to historical scripts` 提交合并为 1 个。

- 新 head：`765cec76eb6fd9587dc5b4577f8e101bd0e69351`；远端目标提交计数=1。

- 回滚 backup：`refs/backup/squash-car-monit-backend-java-V3-20261121151255`（本地）与远端 `backup/car-monit-backend-java-V3-before-squash`。

''',

 r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''



## O. 提交历史整理

- `squash-commits-by-message.py`：通用按提交信息合并脚本；参数化 repo/branch/message/new-message；

  默认 dry-run，--apply 才写远端；拒绝 main/master；force-with-lease；自动 backup ref。

- 实际执行：`car-monit-backend-java-V3` 中 394 个 `docs(scripts): ...` 提交合并为 1 个，

  新 head `765cec76`，目标提交计数=1。

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

