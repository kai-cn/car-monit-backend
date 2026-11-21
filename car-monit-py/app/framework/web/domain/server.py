"""web层通用domain（服务器监控）/ web-layer domain objects.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/Server.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Cpu.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Jvm.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Mem.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Sys.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/SysFileInfo.java

为什么六个类在**同一个文件**里
--------------------------------
Java 的布局是 ``web/domain/Server.java`` + ``web/domain/server/{Cpu,Jvm,Mem,Sys,SysFileInfo}.java``。
Python**不允许**同目录下 ``server.py`` 与 ``server/`` 并存（模块与包同名会互相遮蔽），
所以把 ``Server`` 的五个内部 DTO 一并放进 ``server.py``。类名、字段名、getter 的算式
与 Java 逐字对应，只是少了那层目录。

三类"getter 不等于字段"的地方
------------------------------
1. ``Cpu`` 的 ``total`` / ``sys`` / ``used`` / ``wait`` / ``free``：字段里存的是
   **tick 差值**，getter 返回的是**百分比**。所以 ``cpu.total``（原始 tick）与
   ``cpu.get_total()``（百分比）不是同一个值 —— Java 就是这样，序列化时只用 getter。
2. ``Mem`` / ``Jvm`` 的 ``total`` / ``used`` / ``free``：字段是字节数，getter 换成
   GB / MB 并保留 2 位小数。
3. ``Jvm`` 的 ``name`` / ``startTime`` / ``runTime`` / ``inputArgs``：**没有字段**，
   getter 每次现算。

``Cpu.getTotal()`` 是 Java 的既有怪癖
--------------------------------------
Java 原文是 ``Arith.round(Arith.mul(total, 100), 2)`` —— 只乘 100，**没有**除以
``total``。其余四个 getter 都是 ``xxx / total * 100``。结果就是 JSON 里的
``cpu.total`` 是"tick 总和 × 100"这种量级（正常机器上会看到几万），而不是百分比。
这是上游 RuoYi 3.8.7 的行为，前端拿它当"总使用率"显示确实会溢出，但**改了就是
行为改变**，按原则第 1 条照抄。见 ``COMPATIBILITY.md`` §39。

``to_json_dict()`` 而不是 pydantic
-----------------------------------
这五个 DTO 只在 ``GET /monitor/server`` 一处出现，且全部字段都由 getter 现算，
用 ``DomainModel`` 反而要写一堆 ``computed_field(alias=...)``，可读性更差。因此用
普通类 + 显式 :meth:`to_json_dict`，JSON 键名手写成 Java 的属性名。
"""

from __future__ import annotations

import logging
import os
import platform
import socket
import sys
import time
from typing import Any, Dict, List, Optional

import psutil

from app.common.utils import arith
from app.common.utils.date_utils import (
    get_server_start_date,
    parse_date_to_str,
    time_distance,
)
from app.common.utils.ip_utils import get_host_ip, get_host_name

logger = logging.getLogger("app.framework.web.domain.server")

#: Java: ``Server.OSHI_WAIT_SECOND`` —— CPU 使用率靠"两次采样之间的差值"算，
#: 所以这个请求**必然阻塞 1 秒**。用例通过改写本常量把等待时间降到 0。
OSHI_WAIT_SECOND: int = 1000

#: OSHI 在 Linux 上以 ``HZ = 100`` 的 tick 计数；psutil 给的是**秒**。
#: 乘回 100 只是为了让 ``Cpu.total`` 的量级与 Java 侧可比（百分比那几个字段
#: 是比值，与单位无关）。
_TICKS_PER_SECOND: float = 100.0

#: Java: ``DateUtils.YYYY_MM_DD_HH_MM_SS``
_DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss"


def _java_format(value: float, digits: int) -> str:
    """Java: ``String.format("%.<digits>f", value)``.

    Java 的 ``%f`` 用 ``RoundingMode.HALF_UP``，而 Python 的 ``format`` 用
    银行家舍入，所以先经 :func:`arith.round_half_up` 定量，再交给格式化。
    """
    return f"{arith.round_half_up(value, digits):.{digits}f}"


def _java_os_name() -> str:
    """Java: ``System.getProperty("os.name")``.

    Java 给的值不是 ``platform.system()``：

    ==========  ===========================  =========================
    平台        Java ``os.name``            Python 取法
    ==========  ===========================  =========================
    Windows     ``Windows 11`` / ``Windows 10``  ``system() + release()``
    Linux       ``Linux``                    ``system()``
    macOS       ``Mac OS X``                 写死字面量
    ==========  ===========================  =========================

    直接拼 ``system() + " " + release()`` 在 Linux 上会变成
    ``Linux 5.15.0-91-generic``（Java 只有 ``Linux``），所以按平台分别处理。
    """
    system = platform.system()
    if system == "Windows":
        return f"{system} {platform.release()}".strip()
    if system == "Darwin":
        return "Mac OS X"
    return system


def _windows_volume_label(mountpoint: str) -> Optional[str]:
    """Windows 卷标. Java: ``OSFileStore#getName()`` （``C:\\`` -> ``Windows``）.

    psutil 不提供卷标，只能直接问 Win32：``GetVolumeInformationW``。失败返回
    ``None``，由调用方退回到设备名。非 Windows 平台不进这个函数。
    """
    import ctypes

    label = ctypes.create_unicode_buffer(261)
    # GetVolumeInformationW(rootPathName, volumeNameBuffer, volumeNameSize,
    #                       volumeSerialNumber, maximumComponentLength,
    #                       fileSystemFlags, fileSystemNameBuffer, fileSystemNameSize)
    ok = ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
        mountpoint, label, len(label), None, None, None, None, 0
    )
    return label.value if ok else None


def _file_store_name(mountpoint: str, device: str) -> str:
    """``SysFileInfo.typeName`` 的来源. Java: ``sysFile.setTypeName(fs.getName())``.

    ``OSFileStore#getName()`` 是**卷标**，不是挂载点也不是设备路径。Windows 上取
    真实卷标（取不到则退回 ``C:\\``）；POSIX 上 OSHI 取的是块设备名，与
    ``psutil.Partition.device`` 等价，直接用。
    """
    if os.name == "nt":
        label = _windows_volume_label(mountpoint)
        if label:
            return label
    return device


def _read_cpu_ticks() -> Dict[str, float]:
    """一次 CPU tick 快照（秒）。Java: ``CentralProcessor#getSystemCpuLoadTicks()``.

    返回的键与 ``TickType`` 同名；psutil 在 Windows 上不给 ``nice`` / ``irq`` /
    ``softirq`` / ``steal`` / ``iowait``，缺失的一律按 0 处理（OSHI 在 Windows 上
    同样恒为 0）。
    """
    times = psutil.cpu_times()
    return {
        "nice": float(getattr(times, "nice", 0.0)),
        "irq": float(getattr(times, "irq", 0.0)),
        "softirq": float(getattr(times, "softirq", 0.0)),
        "steal": float(getattr(times, "steal", 0.0)),
        "system": float(getattr(times, "system", 0.0)),
        "user": float(getattr(times, "user", 0.0)),
        "iowait": float(getattr(times, "iowait", 0.0)),
        "idle": float(getattr(times, "idle", 0.0)),
    }


# --------------------------------------------------------------------------- Cpu


class Cpu:
    """CPU相关信息. Java: ``com.ruoyi.framework.web.domain.server.Cpu``."""

    def __init__(self) -> None:
        #: 核心数
        self.cpu_num: int = 0
        #: 下面五个字段都存**原始 tick 差值**，getter 才换成百分比（见模块 docstring）
        self.total: float = 0.0
        self.sys: float = 0.0
        self.used: float = 0.0
        self.wait: float = 0.0
        self.free: float = 0.0

    # Java: public int getCpuNum()
    def get_cpu_num(self) -> int:
        return self.cpu_num

    # Java: public void setCpuNum(int cpuNum)
    def set_cpu_num(self, cpu_num: int) -> None:
        self.cpu_num = cpu_num

    # Java: public double getTotal()
    def get_total(self) -> float:
        """**只乘 100、不除以 total** —— Java 原文，见模块 docstring。"""
        return arith.round_half_up(arith.mul(self.total, 100), 2)

    # Java: public void setTotal(double total)
    def set_total(self, total: float) -> None:
        self.total = total

    # Java: public double getSys()
    def get_sys(self) -> float:
        return arith.round_half_up(arith.mul(self.sys / self.total, 100), 2)

    # Java: public void setSys(double sys)
    def set_sys(self, sys_ticks: float) -> None:
        self.sys = sys_ticks

    # Java: public double getUsed()
    def get_used(self) -> float:
        return arith.round_half_up(arith.mul(self.used / self.total, 100), 2)

    # Java: public void setUsed(double used)
    def set_used(self, used_ticks: float) -> None:
        self.used = used_ticks

    # Java: public double getWait()
    def get_wait(self) -> float:
        return arith.round_half_up(arith.mul(self.wait / self.total, 100), 2)

    # Java: public void setWait(double wait)
    def set_wait(self, wait_ticks: float) -> None:
        self.wait = wait_ticks

    # Java: public double getFree()
    def get_free(self) -> float:
        return arith.round_half_up(arith.mul(self.free / self.total, 100), 2)

    # Java: public void setFree(double free)
    def set_free(self, free_ticks: float) -> None:
        self.free = free_ticks

    def to_json_dict(self) -> Dict[str, Any]:
        """Jackson 序列化的结果：键是 Java 属性名，值是 **getter** 的返回值。"""
        return {
            "cpuNum": self.get_cpu_num(),
            "total": self.get_total(),
            "sys": self.get_sys(),
            "used": self.get_used(),
            "wait": self.get_wait(),
            "free": self.get_free(),
        }


# --------------------------------------------------------------------------- Mem


class Mem:
    """內存相关信息. Java: ``...server.Mem``. 字段是**字节**，getter 换成 GB。"""

    def __init__(self) -> None:
        self.total: float = 0.0
        self.used: float = 0.0
        self.free: float = 0.0

    # Java: public double getTotal()
    def get_total(self) -> float:
        return arith.div(self.total, 1024 * 1024 * 1024, 2)

    # Java: public void setTotal(long total)
    def set_total(self, total: float) -> None:
        self.total = total

    # Java: public double getUsed()
    def get_used(self) -> float:
        return arith.div(self.used, 1024 * 1024 * 1024, 2)

    # Java: public void setUsed(long used)
    def set_used(self, used: float) -> None:
        self.used = used

    # Java: public double getFree()
    def get_free(self) -> float:
        return arith.div(self.free, 1024 * 1024 * 1024, 2)

    # Java: public void setFree(long free)
    def set_free(self, free: float) -> None:
        self.free = free

    # Java: public double getUsage()
    def get_usage(self) -> float:
        return arith.mul(arith.div(self.used, self.total, 4), 100)

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "total": self.get_total(),
            "used": self.get_used(),
            "free": self.get_free(),
            "usage": self.get_usage(),
        }


# --------------------------------------------------------------------------- Jvm


class Jvm:
    """JVM相关信息. Java: ``...server.Jvm``.

    Python 没有 JVM，这一栏的取值来源见 :meth:`Server.set_jvm_info`；字段名与
    getter 的算式保持与 Java 完全一致（``used = total - free``、
    ``usage = (total - free) / total * 100``），所以只要喂进去的三个值自洽，
    展示结果就是自洽的。
    """

    def __init__(self) -> None:
        self.total: float = 0.0
        self.max: float = 0.0
        self.free: float = 0.0
        self.version: Optional[str] = None
        self.home: Optional[str] = None

    # Java: public double getTotal()
    def get_total(self) -> float:
        return arith.div(self.total, 1024 * 1024, 2)

    # Java: public void setTotal(double total)
    def set_total(self, total: float) -> None:
        self.total = total

    # Java: public double getMax()
    def get_max(self) -> float:
        return arith.div(self.max, 1024 * 1024, 2)

    # Java: public void setMax(double max)
    def set_max(self, max_size: float) -> None:
        self.max = max_size

    # Java: public double getFree()
    def get_free(self) -> float:
        return arith.div(self.free, 1024 * 1024, 2)

    # Java: public void setFree(double free)
    def set_free(self, free: float) -> None:
        self.free = free

    # Java: public double getUsed()
    def get_used(self) -> float:
        return arith.div(self.total - self.free, 1024 * 1024, 2)

    # Java: public double getUsage()
    def get_usage(self) -> float:
        return arith.mul(arith.div(self.total - self.free, self.total, 4), 100)

    # Java: public String getName() -> ManagementFactory.getRuntimeMXBean().getVmName()
    def get_name(self) -> str:
        """Python 里对应「解释器名称」：``CPython 3.12.x``。"""
        return f"{platform.python_implementation()} {platform.python_version()}"

    # Java: public String getVersion()
    def get_version(self) -> Optional[str]:
        return self.version

    # Java: public void setVersion(String version)
    def set_version(self, version: Optional[str]) -> None:
        self.version = version

    # Java: public String getHome()
    def get_home(self) -> Optional[str]:
        return self.home

    # Java: public void setHome(String home)
    def set_home(self, home: Optional[str]) -> None:
        self.home = home

    # Java: public String getStartTime()
    def get_start_time(self) -> str:
        return parse_date_to_str(_DATE_TIME_PATTERN, get_server_start_date()) or ""

    # Java: public String getRunTime()
    def get_run_time(self) -> str:
        from datetime import datetime

        return time_distance(datetime.now(), get_server_start_date())

    # Java: public String getInputArgs()
    def get_input_args(self) -> str:
        """Java: ``getInputArguments().toString()`` -> 形如 ``[-Xms512m, -Xmx1024m]``。"""
        return str(sys.argv)

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "total": self.get_total(),
            "max": self.get_max(),
            "free": self.get_free(),
            "used": self.get_used(),
            "usage": self.get_usage(),
            "name": self.get_name(),
            "version": self.get_version(),
            "home": self.get_home(),
            "startTime": self.get_start_time(),
            "runTime": self.get_run_time(),
            "inputArgs": self.get_input_args(),
        }


# --------------------------------------------------------------------------- Sys


class Sys:
    """系统相关信息. Java: ``...server.Sys``."""

    def __init__(self) -> None:
        self.computer_name: Optional[str] = None
        self.computer_ip: Optional[str] = None
        self.user_dir: Optional[str] = None
        self.os_name: Optional[str] = None
        self.os_arch: Optional[str] = None

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "computerName": self.computer_name,
            "computerIp": self.computer_ip,
            "userDir": self.user_dir,
            "osName": self.os_name,
            "osArch": self.os_arch,
        }


# --------------------------------------------------------------------------- SysFileInfo


class SysFileInfo:
    """系统文件相关信息. Java: ``...server.SysFileInfo``.

    ``total`` / ``free`` / ``used`` 是**已经格式化好的字符串**（``"237.4 GB"``），
    不是数字 —— 与 Java 一致，前端直接显示。
    """

    def __init__(self) -> None:
        self.dir_name: Optional[str] = None
        self.sys_type_name: Optional[str] = None
        self.type_name: Optional[str] = None
        self.total: Optional[str] = None
        self.free: Optional[str] = None
        self.used: Optional[str] = None
        self.usage: float = 0.0

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "dirName": self.dir_name,
            "sysTypeName": self.sys_type_name,
            "typeName": self.type_name,
            "total": self.total,
            "free": self.free,
            "used": self.used,
            "usage": self.usage,
        }


# --------------------------------------------------------------------------- Server


class Server:
    """服务器相关信息. Java: ``com.ruoyi.framework.web.domain.Server``."""

    def __init__(self) -> None:
        self.cpu: Cpu = Cpu()
        self.mem: Mem = Mem()
        self.jvm: Jvm = Jvm()
        self.sys: Sys = Sys()
        self.sys_files: List[SysFileInfo] = []

    # Java: public void copyTo()
    def copy_to(self) -> None:
        """一次性采集五项指标。Java 里 ``copyTo`` 声明为 ``throws Exception``。"""
        self.set_cpu_info()
        self.set_mem_info()
        self.set_sys_info()
        self.set_jvm_info()
        self.set_sys_files()

    # Java: private void setCpuInfo(CentralProcessor processor)
    def set_cpu_info(self) -> None:
        """两次采样求差 -> 各 tick 的增量（Java 同样 ``Util.sleep(1000)``）。"""
        prev_ticks = _read_cpu_ticks()
        if OSHI_WAIT_SECOND > 0:
            time.sleep(OSHI_WAIT_SECOND / 1000.0)
        ticks = _read_cpu_ticks()

        def delta(key: str) -> float:
            return (ticks[key] - prev_ticks[key]) * _TICKS_PER_SECOND

        nice = delta("nice")
        irq = delta("irq")
        softirq = delta("softirq")
        steal = delta("steal")
        c_sys = delta("system")
        user = delta("user")
        iowait = delta("iowait")
        idle = delta("idle")
        total_cpu = user + nice + c_sys + idle + iowait + irq + softirq + steal
        self.cpu.set_cpu_num(psutil.cpu_count(logical=True) or 0)
        self.cpu.set_total(total_cpu)
        self.cpu.set_sys(c_sys)
        self.cpu.set_used(user)
        self.cpu.set_wait(iowait)
        self.cpu.set_free(idle)

    # Java: private void setMemInfo(GlobalMemory memory)
    def set_mem_info(self) -> None:
        memory = psutil.virtual_memory()
        self.mem.set_total(memory.total)
        self.mem.set_used(memory.total - memory.available)
        self.mem.set_free(memory.available)

    # Java: private void setSysInfo()
    def set_sys_info(self) -> None:
        """``System.getProperties()`` 的 ``os.name`` / ``os.arch`` / ``user.dir``."""
        self.sys.computer_name = get_host_name()
        self.sys.computer_ip = get_host_ip()
        # Java: os.name -> "Windows 11" / "Linux"（不是 platform.system()，见 _java_os_name）
        self.sys.os_name = _java_os_name()
        # Java: os.arch -> "amd64" / "aarch64"
        self.sys.os_arch = platform.machine()
        self.sys.user_dir = os.getcwd()

    # Java: private void setJvmInfo() throws UnknownHostException
    def set_jvm_info(self) -> None:
        """Python 没有 JVM，这里换成**宿主机内存**的读数（见 ``COMPATIBILITY.md`` §39.4）。

        取值自洽性：``total`` 与 ``max`` 都是物理内存，``free`` 是可用内存，
        于是 getter 算出的 ``used = total - free`` / ``usage = (total-free)/total*100``
        就是"整机内存使用率"，与 ``Mem`` 面板同源但含义明确，不会是 0% 或 100% 的假值。
        """
        memory = psutil.virtual_memory()
        self.jvm.set_total(memory.total)
        self.jvm.set_max(memory.total)
        self.jvm.set_free(memory.available)
        self.jvm.set_version(platform.python_version())
        self.jvm.set_home(sys.prefix)

    # Java: private void setSysFiles(OperatingSystem os)
    def set_sys_files(self) -> List[SysFileInfo]:
        """逐个挂载点采集容量。``psutil.disk_usage`` 失败的分区**跳过**。

        Java 的 OSHI 遇到无介质的光驱会抛 ``IOException``，整个 ``copyTo`` 随之失败；
        这里选择跳过该分区。差异记在 ``COMPATIBILITY.md`` §39.5，理由是"少一块盘"
        比"整页监控 500"更接近运维预期，且 OSHI 在同样场景下的行为在本项目无法实测。
        """
        rows: List[SysFileInfo] = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except OSError as exc:  # 空光驱 / 权限不足
                logger.debug("[磁盘采集跳过] %s: %s", partition.mountpoint, exc)
                continue
            total = usage.total
            free = usage.free
            used = total - free
            info = SysFileInfo()
            info.dir_name = partition.mountpoint
            info.sys_type_name = partition.fstype
            # Java: sysFile.setTypeName(fs.getName()) —— 卷标，不是设备路径
            info.type_name = _file_store_name(partition.mountpoint, partition.device)
            info.total = self.convert_file_size(total)
            info.free = self.convert_file_size(free)
            info.used = self.convert_file_size(used)
            info.usage = arith.mul(arith.div(used, total, 4), 100)
            rows.append(info)
        self.sys_files = rows
        return rows

    # Java: public String convertFileSize(long size)
    def convert_file_size(self, size: float) -> str:
        """字节转换：``GB`` 恒 1 位小数，``MB`` / ``KB`` 在大于 100 时取整。"""
        kb = 1024
        mb = kb * 1024
        gb = mb * 1024
        if size >= gb:
            return _java_format(size / gb, 1) + " GB"
        if size >= mb:
            value = size / mb
            return (_java_format(value, 0) if value > 100 else _java_format(value, 1)) + " MB"
        if size >= kb:
            value = size / kb
            return (_java_format(value, 0) if value > 100 else _java_format(value, 1)) + " KB"
        return f"{int(size)} B"

    def to_json_dict(self) -> Dict[str, Any]:
        """Jackson 的字段顺序：``cpu`` -> ``mem`` -> ``jvm`` -> ``sys`` -> ``sysFiles``。"""
        return {
            "cpu": self.cpu.to_json_dict(),
            "mem": self.mem.to_json_dict(),
            "jvm": self.jvm.to_json_dict(),
            "sys": self.sys.to_json_dict(),
            "sysFiles": [item.to_json_dict() for item in self.sys_files],
        }


__all__ = ["OSHI_WAIT_SECOND", "Cpu", "Mem", "Jvm", "Sys", "SysFileInfo", "Server"]
