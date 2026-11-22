#!/usr/bin/env python3
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
