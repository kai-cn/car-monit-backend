"""``Server`` / ``Cpu`` / ``Mem`` / ``Jvm`` / ``Sys`` / ``SysFileInfo`` —— 服务器监控 DTO.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-framework/.../web/domain/Server.java
#   ruoyi-framework/.../web/domain/server/{Cpu,Jvm,Mem,Sys,SysFileInfo}.java

这一层测什么
------------
这些类没有业务逻辑，**只有算式** —— 但算式里藏着三处"看起来像 bug"的忠实移植，
全都在这里钉住：

1. **``Cpu.getTotal()`` 只乘 100、不除以 total**（§39.2）。JSON 里的 ``cpu.total``
   会是几万的量级，不是百分比。改成 ``/ total`` 就是**行为改变**，前端要重新适配。
2. **字段与 getter 不同源**（§39.1）。``cpu.total`` 存的是 tick 差值，
   ``cpu.get_total()`` 返回的是乘过 100 的数 —— 序列化只用 getter。
3. **``String.format("%.0f")`` 与 Python format 的舍入方向不同**（§39.3）。
   ``convertFileSize`` 走 :func:`app.common.utils.arith.round_half_up` 预舍入。

OSHI -> psutil 的对应关系（§39.4）
----------------------------------
PSutil 是"读一次当前值"，OSHI 是"读两次 tick 求差"，所以 ``set_cpu_info``
按 Java 的节奏采样两次（中间 ``sleep``）。用例把 ``OSHI_WAIT_SECOND`` 改成 0，
免得每个用例都白等 1 秒；**生产代码里那个 1 秒是照抄的，不要改**。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from app.framework.web.domain import server as server_module
from app.framework.web.domain.server import Cpu, Jvm, Mem, Server, Sys, SysFileInfo


# --------------------------------------------------------------------------- fakes


class _FakeTimes:
    """``psutil.cpu_times()`` 的返回值（各平台字段名不同，见 ``_read_cpu_ticks``）。"""

    def __init__(
        self,
        user: float = 0.0,
        system: float = 0.0,
        idle: float = 0.0,
        nice: float = 0.0,
        iowait: float = 0.0,
        irq: float = 0.0,
        softirq: float = 0.0,
        steal: float = 0.0,
    ) -> None:
        self.user = user
        self.system = system
        self.idle = idle
        self.nice = nice
        self.iowait = iowait
        self.irq = irq
        self.softirq = softirq
        self.steal = steal


class _FakePsutil:
    """``psutil`` 的最小替身 —— 只实现 ``Server`` 用到的那几个函数。"""

    def __init__(self) -> None:
        #: 两次采样分别返回什么（``set_cpu_info`` 会按顺序 pop）
        self.cpu_times_answers: List[_FakeTimes] = []
        self.cpu_count_answer: Optional[int] = 8
        self.memory = SimpleNamespace(total=32 * 1024**3, available=12 * 1024**3)
        self.partitions: List[SimpleNamespace] = []
        #: mountpoint -> SimpleNamespace(total, free)；缺键时抛 ``OSError``
        self.usages: Dict[str, SimpleNamespace] = {}
        self.calls: List[str] = []

    def cpu_times(self) -> _FakeTimes:
        self.calls.append("cpu_times")
        if not self.cpu_times_answers:
            raise AssertionError("unexpected extra cpu_times() call")
        return self.cpu_times_answers.pop(0)

    def cpu_count(self, logical: bool = True) -> Optional[int]:
        self.calls.append(f"cpu_count({logical})")
        return self.cpu_count_answer

    def virtual_memory(self) -> SimpleNamespace:
        self.calls.append("virtual_memory")
        return self.memory

    def disk_partitions(self, all: bool = False) -> List[SimpleNamespace]:
        self.calls.append(f"disk_partitions({all})")
        return list(self.partitions)

    def disk_usage(self, mountpoint: str) -> SimpleNamespace:
        self.calls.append(f"disk_usage({mountpoint})")
        if mountpoint not in self.usages:
            raise OSError(21, "device not ready")
        return self.usages[mountpoint]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def fast_oshi(monkeypatch: pytest.MonkeyPatch) -> None:
    """把 1 秒等待降成 0 —— 只影响这个模块的常量，改的是**测试**不是产品行为。"""
    monkeypatch.setattr(server_module, "OSHI_WAIT_SECOND", 0)


@pytest.fixture
def fake_psutil(monkeypatch: pytest.MonkeyPatch) -> _FakePsutil:
    fake = _FakePsutil()
    monkeypatch.setattr(server_module, "psutil", fake)
    return fake


@pytest.fixture
def host(monkeypatch: pytest.MonkeyPatch) -> None:
    """``IpUtils.getHostName`` / ``getHostIp`` 的固定答案（真实调用要碰网卡）。"""
    monkeypatch.setattr(server_module, "get_host_name", lambda: "car-monit-host")
    monkeypatch.setattr(server_module, "get_host_ip", lambda: "10.0.0.7")


# --------------------------------------------------------------------------- Cpu


class TestCpu:
    def test_get_total_multiplies_by_100_without_dividing(self) -> None:
        """§39.2 —— Java 原文 ``Arith.round(Arith.mul(total, 100), 2)``."""
        cpu = Cpu()
        cpu.set_total(1234.5)
        assert cpu.get_total() == 123450.0

    def test_the_four_percentage_getters_divide_by_total(self) -> None:
        """``sys`` / ``used`` / ``wait`` / ``free`` 都是 ``xxx / total * 100``."""
        cpu = Cpu()
        cpu.set_total(1000.0)
        cpu.set_sys(100.0)
        cpu.set_used(200.0)
        cpu.set_wait(50.0)
        cpu.set_free(650.0)
        assert cpu.get_sys() == 10.0
        assert cpu.get_used() == 20.0
        assert cpu.get_wait() == 5.0
        assert cpu.get_free() == 65.0

    def test_raw_fields_are_ticks_not_percentages(self) -> None:
        """§39.1 —— 字段存 tick，getter 才换百分比，所以两者不相等。"""
        cpu = Cpu()
        cpu.set_total(1000.0)
        cpu.set_free(650.0)
        assert cpu.total == 1000.0
        assert cpu.get_free() == 65.0

    def test_json_dict_uses_getters(self) -> None:
        cpu = Cpu()
        cpu.set_cpu_num(16)
        cpu.set_total(1000.0)
        cpu.set_sys(100.0)
        cpu.set_used(200.0)
        cpu.set_wait(50.0)
        cpu.set_free(650.0)
        assert cpu.to_json_dict() == {
            "cpuNum": 16,
            "total": 100000.0,
            "sys": 10.0,
            "used": 20.0,
            "wait": 5.0,
            "free": 65.0,
        }

    def test_zero_total_raises_like_the_java_divide(self) -> None:
        """未采样就序列化 -> Java ``x / 0`` 也是 ``ArithmeticException``。"""
        with pytest.raises(ZeroDivisionError):
            Cpu().get_sys()


# --------------------------------------------------------------------------- Mem


class TestMem:
    def test_getters_convert_bytes_to_gb_with_two_decimals(self) -> None:
        mem = Mem()
        mem.set_total(24 * 1024**3)
        mem.set_used(9 * 1024**3)
        mem.set_free(15 * 1024**3)
        assert mem.get_total() == 24.0
        assert mem.get_used() == 9.0
        assert mem.get_free() == 15.0

    def test_usage_is_four_digit_ratio_times_100(self) -> None:
        mem = Mem()
        mem.set_total(32 * 1024**3)
        mem.set_used(8 * 1024**3)
        mem.set_free(24 * 1024**3)
        assert mem.get_usage() == 25.0

    def test_json_dict(self) -> None:
        mem = Mem()
        mem.set_total(1024**3)
        mem.set_used(1024 // 2 * 1024 * 1024)
        mem.set_free(1024 // 2 * 1024 * 1024)
        assert mem.to_json_dict() == {
            "total": 1.0,
            "used": 0.5,
            "free": 0.5,
            "usage": 50.0,
        }


# --------------------------------------------------------------------------- Jvm


class TestJvm:
    def test_getters_convert_bytes_to_mb_not_gb(self) -> None:
        """Java: ``Arith.div(..., 1024 * 1024, 2)`` —— 单位是 **MB**。"""
        jvm = Jvm()
        jvm.set_total(512 * 1024 * 1024)
        jvm.set_max(1024 * 1024 * 1024)
        jvm.set_free(256 * 1024 * 1024)
        assert jvm.get_total() == 512.0
        assert jvm.get_max() == 1024.0
        assert jvm.get_free() == 256.0

    def test_used_and_usage_are_derived_from_total_minus_free(self) -> None:
        """``used`` / ``usage`` **没有字段**，靠 ``total`` / ``free`` 现算。"""
        jvm = Jvm()
        jvm.set_total(1000 * 1024 * 1024)
        jvm.set_free(250 * 1024 * 1024)
        assert jvm.get_used() == 750.0
        assert jvm.get_usage() == 75.0

    def test_name_is_the_python_interpreter(self) -> None:
        """Java 用 ``getRuntimeMXBean().getVmName()`` -> ``<implement> <version>``."""
        name = Jvm().get_name()
        assert name.startswith(("CPython", "PyPy"))
        assert name.split(" ")[-1][0].isdigit()

    def test_input_args_is_the_java_list_to_string_shape(self) -> None:
        """``List#toString`` -> ``[...]``；空参数表是 ``[]``，不是空串。"""
        rendered = Jvm().get_input_args()
        assert rendered.startswith("[") and rendered.endswith("]")

    def test_json_dict_has_exactly_the_java_keys(self) -> None:
        jvm = Jvm()
        jvm.set_total(100 * 1024 * 1024)
        jvm.set_max(200 * 1024 * 1024)
        jvm.set_free(40 * 1024 * 1024)
        jvm.set_version("3.12.8")
        jvm.set_home("D:/Python312")
        body = jvm.to_json_dict()

        # 顺序即 Jackson 的字段顺序（Jvm 的声明顺序）
        assert list(body) == [
            "total",
            "max",
            "free",
            "used",
            "usage",
            "name",
            "version",
            "home",
            "startTime",
            "runTime",
            "inputArgs",
        ]
        assert body["version"] == "3.12.8"
        assert body["home"] == "D:/Python312"


# --------------------------------------------------------------------------- Sys / SysFileInfo


class TestSys:
    def test_json_dict_keys(self) -> None:
        row = Sys()
        row.computer_name = "host"
        row.computer_ip = "10.0.0.7"
        row.user_dir = "/srv/app"
        row.os_name = "Linux"
        row.os_arch = "amd64"
        assert row.to_json_dict() == {
            "computerName": "host",
            "computerIp": "10.0.0.7",
            "userDir": "/srv/app",
            "osName": "Linux",
            "osArch": "amd64",
        }


class TestSysFileInfo:
    def test_json_dict_keys_and_preformatted_strings(self) -> None:
        """``total`` / ``free`` / ``used`` 是**字符串**（``"237.4 GB"``），不是数字。"""
        row = SysFileInfo()
        row.dir_name = "/"
        row.sys_type_name = "ext4"
        row.type_name = "Local Disk"
        row.total = "100.0 GB"
        row.free = "40.0 GB"
        row.used = "60.0 GB"
        row.usage = 60.0
        assert row.to_json_dict() == {
            "dirName": "/",
            "sysTypeName": "ext4",
            "typeName": "Local Disk",
            "total": "100.0 GB",
            "free": "40.0 GB",
            "used": "60.0 GB",
            "usage": 60.0,
        }


# --------------------------------------------------------------------------- convertFileSize


class TestConvertFileSize:
    """Java: ``Server#convertFileSize(long size)`` —— 四档 + 两种小数位。"""

    def setup_method(self) -> None:
        self.server = Server()

    @pytest.mark.parametrize(
        ("size", "expected"),
        [
            (0, "0 B"),
            (1, "1 B"),
            (1023, "1023 B"),
            # KB：<= 100 保留 1 位，> 100 取整
            (1024, "1.0 KB"),
            (1024 * 100, "100.0 KB"),
            (1024 * 101, "101 KB"),
            # MB：同上
            (1024**2, "1.0 MB"),
            (1024**2 * 100, "100.0 MB"),
            (1024**2 * 101, "101 MB"),
            # GB：恒 1 位
            (1024**3, "1.0 GB"),
            (1024**3 * 237, "237.0 GB"),
            (1024**3 * 1024, "1024.0 GB"),
        ],
    )
    def test_thresholds(self, size: int, expected: str) -> None:
        assert self.server.convert_file_size(size) == expected

    def test_gb_keeps_one_decimal_even_when_huge(self) -> None:
        """与 MB / KB 不同，GB 档**永远**是 ``%.1f``，不取整。"""
        assert self.server.convert_file_size(1024**3 * 512) == "512.0 GB"

    def test_half_up_not_bankers_rounding(self) -> None:
        """§39.3 —— ``%.0f`` 遇到 ``.5`` 要进位；Python 的 format 会舍到偶数。"""
        # 注意：``%.0f`` 只用在 ``value > 100`` 的分支，所以必须超过 100 MB。
        # Java: String.format("%.0f MB", 100.5f) -> "101 MB"
        # Python: format(100.5, '.0f') -> "100"（银行家舍入）
        assert self.server.convert_file_size(int(1024**2 * 100.5)) == "101 MB"

    def test_one_decimal_uses_half_up_too(self) -> None:
        # 1.25 GB -> "%.1f" HALF_UP -> "1.3 GB"（银行家舍入会给 "1.2"）
        assert self.server.convert_file_size(int(1024**3 * 1.25)) == "1.3 GB"


# --------------------------------------------------------------------------- Server 采集


class TestServerCollect:
    def _two_samples(self, fake: _FakePsutil) -> None:
        """构造两次采样：user +0.2s、system +0.1s、idle +1.7s，共 2.0s."""
        fake.cpu_times_answers = [
            _FakeTimes(user=10.0, system=5.0, idle=100.0),
            _FakeTimes(user=10.2, system=5.1, idle=101.7),
        ]

    def test_cpu_info_uses_the_tick_delta(self, fake_psutil: _FakePsutil) -> None:
        self._two_samples(fake_psutil)
        server = Server()
        server.set_cpu_info()

        # 差值（秒）* 100 = tick
        assert server.cpu.cpu_num == 8
        assert server.cpu.total == pytest.approx(200.0)  # 2.0s * 100
        assert server.cpu.used == pytest.approx(20.0)  # user
        assert server.cpu.sys == pytest.approx(10.0)  # system
        assert server.cpu.free == pytest.approx(170.0)  # idle
        assert server.cpu.wait == 0.0
        assert fake_psutil.calls[:2] == ["cpu_times", "cpu_times"]

    def test_missing_platform_fields_are_treated_as_zero(
        self, fake_psutil: _FakePsutil
    ) -> None:
        """Windows 没有 ``iowait`` / ``steal`` —— OSHI 在那里同样恒 0。"""

        class _WindowsTimes:
            def __init__(self, user: float, system: float, idle: float) -> None:
                self.user, self.system, self.idle = user, system, idle

        fake_psutil.cpu_times_answers = [
            _WindowsTimes(user=1.0, system=1.0, idle=8.0),
            _WindowsTimes(user=1.5, system=1.0, idle=17.5),
        ]
        server = Server()
        server.set_cpu_info()

        assert server.cpu.wait == 0.0
        # 差值：user 0.5s + idle 9.5s = 10.0s -> 1000 tick
        assert server.cpu.total == pytest.approx(1000.0)

    def test_mem_info_uses_total_minus_available(self, fake_psutil: _FakePsutil) -> None:
        server = Server()
        server.set_mem_info()

        assert server.mem.total == pytest.approx(32 * 1024**3)
        assert server.mem.free == pytest.approx(12 * 1024**3)
        assert server.mem.used == pytest.approx(20 * 1024**3)
        assert server.mem.get_usage() == 62.5

    def test_sys_info(self, fake_psutil: _FakePsutil, host: None) -> None:
        server = Server()
        server.set_sys_info()

        assert server.sys.computer_name == "car-monit-host"
        assert server.sys.computer_ip == "10.0.0.7"
        assert server.sys.os_name
        assert server.sys.os_arch
        assert server.sys.user_dir

    def test_jvm_info_reuses_host_memory(self, fake_psutil: _FakePsutil) -> None:
        """§39.4 —— Python 没有 JVM，这一栏映射到**宿主机内存**。"""
        server = Server()
        server.set_jvm_info()

        assert server.jvm.total == pytest.approx(32 * 1024**3)
        assert server.jvm.max == server.jvm.total
        assert server.jvm.free == pytest.approx(12 * 1024**3)
        assert server.jvm.get_used() == pytest.approx(20 * 1024)
        assert server.jvm.get_usage() == 62.5
        assert server.jvm.version and server.jvm.home

    def test_sys_files_skip_partitions_that_fail(self, fake_psutil: _FakePsutil) -> None:
        """§39.5 —— ``psutil.disk_usage`` 失败的分区跳过（空光驱）。"""
        fake_psutil.partitions = [
            SimpleNamespace(mountpoint="C:\\", fstype="NTFS", device="C:\\"),
            SimpleNamespace(mountpoint="D:\\", fstype="", device="D:\\"),
        ]
        fake_psutil.usages = {
            "C:\\": SimpleNamespace(total=1024**3 * 100, free=1024**3 * 40)
        }
        server = Server()
        rows = server.set_sys_files()

        assert len(rows) == 1
        assert rows[0].dir_name == "C:\\"
        assert rows[0].total == "100.0 GB"
        assert rows[0].free == "40.0 GB"
        assert rows[0].used == "60.0 GB"
        assert rows[0].usage == 60.0

    def test_copy_to_fills_all_five_panels(self, fake_psutil: _FakePsutil, host: None) -> None:
        self._two_samples(fake_psutil)
        server = Server()
        server.copy_to()

        body = server.to_json_dict()
        assert list(body) == ["cpu", "mem", "jvm", "sys", "sysFiles"]
        assert body["cpu"]["cpuNum"] == 8
        assert body["mem"]["usage"] == 62.5
        assert body["jvm"]["usage"] == 62.5
        assert body["sys"]["computerName"] == "car-monit-host"
        assert body["sysFiles"] == []


class TestJavaOsName:
    """§39.7 —— ``os.name`` 不是 ``platform.system()`` 的直译。"""

    @pytest.mark.parametrize(
        ("system", "release", "expected"),
        [
            ("Windows", "11", "Windows 11"),
            ("Windows", "10", "Windows 10"),
            ("Linux", "5.15.0-91-generic", "Linux"),
            ("Darwin", "23.1.0", "Mac OS X"),
        ],
    )
    def test_os_name(
        self, monkeypatch: pytest.MonkeyPatch, system: str, release: str, expected: str
    ) -> None:
        monkeypatch.setattr(server_module.platform, "system", lambda: system)
        monkeypatch.setattr(server_module.platform, "release", lambda: release)
        assert server_module._java_os_name() == expected


class TestFileStoreName:
    """``SysFileInfo.typeName`` 取 ``OSFileStore#getName()``（卷标），不是设备路径。"""

    def test_posix_falls_back_to_the_device(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(server_module.os, "name", "posix")
        assert server_module._file_store_name("/", "/dev/sda1") == "/dev/sda1"

    def test_windows_uses_the_volume_label(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(server_module.os, "name", "nt")
        monkeypatch.setattr(server_module, "_windows_volume_label", lambda _m: "Windows")
        assert server_module._file_store_name("C:\\", "C:\\") == "Windows"

    def test_windows_falls_back_when_the_label_is_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module.os, "name", "nt")
        monkeypatch.setattr(server_module, "_windows_volume_label", lambda _m: "")
        assert server_module._file_store_name("C:\\", "C:\\") == "C:\\"


class TestRealCollectionSmoke:
    """一次真实采集（不打桩 psutil）—— 确认字段类型与不变量。"""

    def test_copy_to_on_the_real_machine(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ``fast_oshi`` 把等待降成 0，两次采样几乎落在同一瞬间 ⇒ total = 0 ⇒ get_sys()
        # 除零。这里给回 0.1 秒：真实采集必须跨过 Windows 的 15.6ms tick 粒度。
        monkeypatch.setattr(server_module, "OSHI_WAIT_SECOND", 100)

        server = Server()
        server.copy_to()

        body = server.to_json_dict()
        assert isinstance(body["cpu"]["cpuNum"], int)
        assert body["cpu"]["cpuNum"] >= 1
        assert 0.0 <= body["cpu"]["used"] <= 100.0
        assert 0.0 <= body["cpu"]["free"] <= 100.0
        assert body["mem"]["total"] > 0
        assert 0.0 <= body["mem"]["usage"] <= 100.0
        assert isinstance(body["sysFiles"], list)
        for row in body["sysFiles"]:
            assert row["total"].endswith((" B", " KB", " MB", " GB"))
            assert 0.0 <= row["usage"] <= 100.0
