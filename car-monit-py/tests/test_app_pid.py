"""``scripts/app_pid.py`` 的用例。

# Migrated from: (no Java equivalent -- 对应 `jps -l | findstr %AppName%` 的选择逻辑)

这个模块只服务于 `start.sh` / `start.bat` 的 `stop` / `status`，但一旦它认错进程，
`stop` 就会 kill 掉别人的 python —— 所以「认哪个、不认哪个」必须钉住。
"""

from __future__ import annotations

import os
from typing import List, Optional

import pytest

from scripts import app_pid


class _FakeProcess:
    """Stand-in for ``psutil.Process``：只暴露 ``info`` 字典。"""

    def __init__(self, pid: int, cmdline: Optional[List[str]]) -> None:
        self.info = {"pid": pid, "cmdline": cmdline}


def _patch(monkeypatch: pytest.MonkeyPatch, procs: List[_FakeProcess]) -> None:
    monkeypatch.setattr(app_pid.psutil, "process_iter", lambda attrs=None: iter(procs))


def test_matches_entry_file_name_anywhere_in_the_command_line(monkeypatch) -> None:
    """`python run.py` / `python ./run.py` / `/usr/bin/python3 x/run.py` 都算。"""
    _patch(
        monkeypatch,
        [
            _FakeProcess(101, ["C:\\venv\\python.exe", "run.py"]),
            _FakeProcess(102, ["/usr/bin/python3", "./run.py", "--reload"]),
            _FakeProcess(103, ["python", "D:/work/car-monit-py/run.py"]),
        ],
    )

    assert app_pid.find_pids() == [101, 102, 103]


def test_does_not_match_other_scripts_or_prefixes(monkeypatch) -> None:
    """`app_pid.py` / `run_service.py` / `runner.py` 都不能被当成启动进程。

    Java 侧是 `jps -l | findstr ruoyi-admin.jar`，同样只比名字，不做模糊前缀匹配。
    """
    _patch(
        monkeypatch,
        [
            _FakeProcess(201, ["python", "scripts/app_pid.py"]),
            _FakeProcess(202, ["python", "run_service.py"]),
            _FakeProcess(203, ["python", "runner.py"]),
            _FakeProcess(204, ["python", "run.py.bak"]),
        ],
    )

    assert app_pid.find_pids() == []


def test_skips_its_own_process(monkeypatch) -> None:
    """自查时 `scripts/app_pid.py` 自己的命令行也带 "run.py" 子串吗？不带 —— 但仍要排除自己。"""
    real_pid = os.getpid()
    _patch(
        monkeypatch,
        [
            _FakeProcess(real_pid, ["python", "run.py"]),
            _FakeProcess(301, ["python", "run.py"]),
        ],
    )

    assert app_pid.find_pids() == [301]


@pytest.mark.parametrize("cmdline", [None, []])
def test_tolerates_processes_without_a_readable_command_line(monkeypatch, cmdline) -> None:
    """权限不足时 psutil 给的是 ``None``（cmdline）或空列表，不能因此抛异常。"""
    _patch(monkeypatch, [_FakeProcess(401, cmdline)])

    assert app_pid.find_pids() == []


def test_main_prints_one_pid_per_line(monkeypatch, capsys) -> None:
    """``start.sh`` / ``start.bat`` 直接读 stdout，一行一个 PID。"""
    _patch(monkeypatch, [_FakeProcess(501, ["python", "run.py"]), _FakeProcess(502, ["python", "run.py"])])

    assert app_pid.main() == 0
    assert capsys.readouterr().out.splitlines() == ["501", "502"]
