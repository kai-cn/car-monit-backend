#!/usr/bin/env python3

"""
@description 历史脚本 push_dbupgrade_all_branches_api.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python push_dbupgrade_all_branches_api.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# 用途：用 Contents API 把 dbupgrade 脚本同步到指定仓库的多个分支。

# 用法：python push_dbupgrade_all_branches_api.py <api|backend> <local_base_dir> <branch1> [branch2 ...]

import sys

sys.path.insert(0, "D:/work/runtime-logs")

from push_files_api import put_files



key, base, branches = sys.argv[1], sys.argv[2], sys.argv[3:]

FILES = ["scripts/v3/ops/dbupgrade/db_cell.sh",

         "scripts/v3/ops/dbupgrade/db_dump.sh",

         "scripts/v3/ops/dbupgrade/gate.py",

         "scripts/v3/ops/dbupgrade/report.py"]

repo = "kai-cn/car-monit-" + ("api" if key == "api" else "backend")

for br in branches:

    try:

        put_files(repo, br, base, FILES)

    except Exception as e:

        print("BRANCH_FAIL", repo, br, repr(e))

