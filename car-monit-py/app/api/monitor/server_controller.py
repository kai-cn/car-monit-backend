"""``/monitor/server`` -- 服务器监控.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/ServerController.java

端点清单（1 个映射）
--------------------
    ==============  =======  ===================  ==============
    Java             Method   Path                 Access
    ==============  =======  ===================  ==============
    ``getInfo()``    GET      ``/monitor/server``  server:list
    ==============  =======  ===================  ==============

返回体（``AjaxResult.success(Object)``）
---------------------------------------
Java 传的是 ``Server`` **对象本身**，Jackson 序列化时调 getter，得到::

    {"code": 200, "msg": "操作成功", "data": {
        "cpu":  {"cpuNum": 8, "total": 1234.5, "sys": 1.2, "used": 3.4,
                 "wait": 0.0, "free": 95.4},
        "mem":  {"total": 31.25, "used": 12.5, "free": 18.75, "usage": 40.0},
        "jvm":  {"total": 31.25, "max": 31.25, "free": 18.75, "used": 12.5,
                 "usage": 40.0, "version": "3.12.8", "home": "...",
                 "name": "CPython 3.12.8", "startTime": "...", "runTime": "...",
                 "inputArgs": "[...]"},
        "sys":  {"computerName": "...", "computerIp": "...", "userDir": "...",
                 "osName": "...", "osArch": "..."},
        "sysFiles": [{"dirName": "/", "sysTypeName": "ext4", "typeName": "本地固定磁盘 (ext4)",
                      "total": "100.0 GB", "free": "40.0 GB", "used": "60.0 GB",
                      "usage": 60.0}, ...]
    }}

``Server`` 的字段语义、``Cpu.total`` 的既有 bug、``Jvm`` 面板与 JVM 的对应关系，
全部记录在 :mod:`app.framework.web.domain.server` 的模块 docstring 与
``COMPATIBILITY.md`` §39 —— 那个文件是本次迁移里"最不像 Java"的一处，
改之前请先读它。

``copyTo()`` 会**阻塞 1 秒**
---------------------------
``Server.setCpuInfo()`` 为了算 CPU 占用率，先取一次 ticks、``Thread.sleep(1000)``、
再取一次。所以本接口的响应时间下限就是 1 秒（``OSHI_WAIT_SECOND = 1000``）。这是
Java 现状，照抄 —— 不要为了"性能"把睡眠去掉，否则 ``total``/``used`` 会算成 0。

异常处理
--------
Java 的 ``getInfo() throws Exception`` 把 OSHI 的 ``IOException`` 交给
``GlobalExceptionHandler``，回 **HTTP 200 + code 500**。这里同样不 catch，
``psutil.Error`` / ``OSError`` 走同一条兜底路径。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.common.core.domain.ajax_result import AjaxResult
from app.framework.web.domain.server import Server
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/monitor/server", tags=["monitor-server"])


@router.get("", response_model=None)
@pre_authorize_permi("monitor:server:list")
def get_info() -> AjaxResult:
    """获取服务器监控信息. Java: ``@GetMapping() public AjaxResult getInfo() throws Exception``.

    对应 ``new Server(); server.copyTo(); return AjaxResult.success(server);``。
    ``copy_to()`` 内部会 ``time.sleep(1)``（见模块 docstring），所以这是一个
    **阻塞约 1 秒**的同步端点。
    """
    server = Server()
    server.copy_to()
    return AjaxResult.success_data(server.to_json_dict())


__all__ = ["router", "get_info"]
