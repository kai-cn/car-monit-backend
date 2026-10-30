"""找出正在运行的 `run.py` 进程 PID。

# Migrated from: (no Java equivalent -- 替代 `jps -l | findstr %AppName%`)

Java 侧 `ry.sh` / `ry.bat` 用 `jps -l` 列 JVM 进程、再按 jar 名过滤。Windows 上
没有同类的 `python -l` 命令，所以这里用 `psutil`（本来就是依赖，见
`requirements.txt`）读命令行，交给 `start.sh` / `start.bat` 共用 —— 两个启动脚本
不再各写一套进程发现逻辑，也不会因为 `powershell` 不在 PATH 上而失效。

用法 / Usage::

    python scripts/app_pid.py          # 每行一个 PID；没有进程时什么都不输出
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

import psutil

#: 与 `ry.sh` 的 `AppName=ruoyi-admin.jar` 对应：按**入口文件名**匹配，不看目录。
ENTRY_NAME = "run.py"


def find_pids(entry_name: str = ENTRY_NAME) -> List[int]:
    """Return PIDs whose command line names ``entry_name`` as an argument."""
    pids: List[int] = []
    own_pid = os.getpid()
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if proc.info["pid"] == own_pid:
            continue
        cmdline = proc.info.get("cmdline") or []
        # 只比文件名：`python run.py` / `/usr/bin/python3 ./run.py` 都算，
        # 但 `python scripts/app_pid.py` 不算（basename 是 app_pid.py）。
        for arg in cmdline[1:]:
            if Path(arg).name == entry_name:
                pids.append(proc.info["pid"])
                break
    return pids


def main() -> int:
    for pid in find_pids():
        print(pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
