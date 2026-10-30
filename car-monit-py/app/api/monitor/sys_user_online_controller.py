"""``/monitor/online`` -- 在线用户监控.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysUserOnlineController.java

端点清单（2 个映射，**全部迁移**）
--------------------------------
    ====================  =======  ==========================  ===============
    Java                   Method   Path                         Access
    ====================  =======  ==========================  ===============
    ``list(String, String)`` GET    ``/monitor/online/list``       online:list
    ``forceLogout(String)``  DELETE ``/monitor/online/{tokenId}``  online:forceLogout
    ====================  =======  ==========================  ===============

``list`` **没有** ``startPage()``
---------------------------------
Java 的 ``list`` 直接 ``getDataTable(userOnlineService.selectOnlineByInfo(...))``，
没有 ``startPage()``。于是 ``PageInfo`` 把 ``total`` 记成列表长度（不是总数），
而 ``pageNum`` / ``pageSize`` 虽然由前端传了，服务端**完全不看** —— 前端传
``pageSize=10`` 也会拿到全部在线用户。这是 Java 现状，照抄。

``ipaddr`` / ``userName`` 都是可选参数
-------------------------------------
Java 的 ``list(String ipaddr, String userName)`` 两个参数都**没有** ``@RequestParam``
注解，于是走 ``RequestParamMethodArgumentResolver`` 的默认值 ``required = false``：
缺省即 ``null``，不会 400。

``DELETE /{tokenId}`` 不管键存不存在都回成功
-------------------------------------------
``redisCache.deleteObject(...)`` 的返回值被丢弃，``return AjaxResult.success();``
是无条件的。所以对一个已经过期的 ``tokenId`` 强退，也是 ``code 200``。

Java 里四个未使用的 import
--------------------------
``ArrayList`` / ``Collection`` / ``Collections`` / ``StringUtils`` / ``LoginUser``
在 ``SysUserOnlineController`` 里被 import 但**从未使用**（逻辑都在 Service 里）。
Java 编译器只警告不报错，它们没有对应的迁移物 —— 记录在此，免得后来者以为漏了。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.controller.base_controller import get_data_table
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.enums.business_type import BusinessType
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.service.sys_user_online_service import (
    SysUserOnlineService,
    get_user_online_service,
)

router = APIRouter(prefix="/monitor/online", tags=["monitor-online"])

#: Java: ``com.ruoyi.web.controller.monitor.SysUserOnlineController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.monitor.SysUserOnlineController"


# --------------------------------------------------------------------------- 依赖

_USER_ONLINE_SERVICE: Optional[SysUserOnlineService] = None
_REDIS_CACHE: Optional[RedisCache] = None


def _user_online_service() -> SysUserOnlineService:
    global _USER_ONLINE_SERVICE
    if _USER_ONLINE_SERVICE is None:
        _USER_ONLINE_SERVICE = get_user_online_service()
    return _USER_ONLINE_SERVICE


def _redis_cache() -> RedisCache:
    """Java: ``@Autowired private RedisCache redisCache``."""
    global _REDIS_CACHE
    if _REDIS_CACHE is None:
        _REDIS_CACHE = get_redis_cache()
    return _REDIS_CACHE


def reset_user_online_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _USER_ONLINE_SERVICE, _REDIS_CACHE
    _USER_ONLINE_SERVICE = None
    _REDIS_CACHE = None


# --------------------------------------------------------------------------- 端点


@router.get("/list", response_model=None)
@pre_authorize_permi("monitor:online:list")
def list_online(
    ipaddr: Optional[str] = None,
    user_name: Optional[str] = Query(default=None, alias="userName"),
) -> TableDataInfo:
    """查询在线用户列表. Java: ``@GetMapping("/list") public TableDataInfo list(String ipaddr, String userName)``.

    两个参数都可选（Java 无 ``@RequestParam``，默认 ``required = false``）。
    第二个参数的 query 名是驼峰的 ``userName``（Java 形参名），所以用
    ``Query(alias="userName")`` 显式声明；``ipaddr`` 没有驼峰形式，直接默认名即可。
    """
    rows = _user_online_service().select_online_by_info(ipaddr, user_name)
    return get_data_table(rows)


@router.delete("/{token_id}", response_model=None)
@pre_authorize_permi("monitor:online:forceLogout")
@log(title="在线用户", business_type=BusinessType.FORCE, java_method="forceLogout")
def force_logout(token_id: str) -> AjaxResult:
    """强退用户. Java: ``@DeleteMapping("/{tokenId}")``.

    只删 Redis 的 ``login_tokens:<tokenId>``；**不**改数据库。审计行由
    ``@log(businessType = FORCE)`` 异步写入，与 Java 的 ``@Log`` 一致。
    下一次请求时该 token 查不到会话，会被判为未认证（401）。

    ``tokenId`` 是 ``LoginUser.token``（UUID），**不是** JWT 本身 —— 换成 JWT
    在这里删不到任何键，但接口仍然回 200。
    """
    _redis_cache().delete_object(LOGIN_TOKEN_KEY + token_id)
    return AjaxResult.success()


__all__ = [
    "router",
    "list_online",
    "force_logout",
    "reset_user_online_controller",
]
