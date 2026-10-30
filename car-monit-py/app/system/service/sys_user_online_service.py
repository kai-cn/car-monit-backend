"""在线用户 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUserOnlineService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserOnlineServiceImpl.java

数据源是 **Redis**，不是数据库 —— 这在本项目里是唯一一处。Java 的做法是
``redisCache.keys("login_tokens:*")`` 扫出全部会话键，再逐个
``getCacheObject(key)`` 反序列化回 :class:`LoginUser`。没有分页、没有排序，
**每次请求都全量扫描一遍**（``KEYS`` 是 O(N) 阻塞命令）。

三个必须照抄的细节
------------------
1. **``Collections.reverse`` 之后才 ``removeAll(null)``**：所以结果是"键顺序的倒序、
   丢掉 null"。若先过滤再倒序，顺序完全一样，但这里按源码顺序写，方便 diff。
2. **两个过滤条件用的是本项目的 ``isNotEmpty``，它和 commons 的同名方法不一样**：
   ``StringUtils.isEmpty(String)`` 的实现是 ``isNull(str) || "".equals(str.trim())``，
   所以**全空格串 ``" "`` 算空** —— 等同于不传该过滤条件，会返回全部在线用户。
   这是 RuoYi 自己覆写的行为，照抄。
3. **传了 ``ipaddr`` 时**Java **不检查** ``user.getUser()``，直接
   ``user.getIpaddr()``；只要某个 ``login_tokens:*`` 的值不是合法 ``LoginUser``
   （例如 ``@type`` 未知、或值已被删空），就是一个 **NPE -> HTTP 200 + code 500**。
   这里不兜底，保持同样的失败面。

``selectUserOnlineList`` 没有调用方
-----------------------------------
Java 的 ``SysUserOnlineController`` 只调 ``selectOnlineByInfo``；``selectUserOnlineList``
是**死代码**（与 ``selectOnlineByInfo`` 的区别仅在于不做过滤）。按原则第 4 条照搬。

``loginUserToUserOnline`` 返回 ``null``
---------------------------------------
``user == null`` 或 ``user.getUser() == null`` 时返回 ``null``，而不是抛异常 ——
调用方靠 ``removeAll(singleton(null))`` 把这些占位扔掉。这条是"扫到脏键也不炸"的
唯一一道闸，不能省。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.string_utils import equals, is_not_empty
from app.system.domain.sys_user_online import SysUserOnline


class SysUserOnlineService:
    """Java: ``ISysUserOnlineService`` (impl: ``SysUserOnlineServiceImpl``)."""

    def __init__(self, redis_cache: Optional[RedisCache] = None) -> None:
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``（懒解析单例）。"""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    # Java: public List<SysUserOnline> selectOnlineByInfo(String ipaddr, String userName)
    def select_online_by_info(
        self, ipaddr: Optional[str] = None, user_name: Optional[str] = None
    ) -> List[SysUserOnline]:
        """通过登录地址/用户名称查询在线用户信息.

        分支顺序与 Java 完全一致（"都有" -> "只有 ip" -> "只有用户名" -> "都没有"）。
        第三个分支多一个 ``isNotNull(user.getUser())`` 判断，第一、二个没有 ——
        这是 Java 原文，不是笔误。
        """
        keys = self.redis_cache.keys(LOGIN_TOKEN_KEY + "*")
        rows: List[Optional[SysUserOnline]] = []
        for key in keys:
            user: Optional[LoginUser] = self.redis_cache.get_cache_object(key)
            if is_not_empty(ipaddr) and is_not_empty(user_name):
                if equals(ipaddr, user.ipaddr) and equals(user_name, user.username):
                    rows.append(self.login_user_to_user_online(user))
            elif is_not_empty(ipaddr):
                if equals(ipaddr, user.ipaddr):
                    rows.append(self.login_user_to_user_online(user))
            elif is_not_empty(user_name) and user.user is not None:
                # Java: ``else if (isNotEmpty(userName) && isNotNull(user.getUser()))`` ——
                # ``user`` 为 null 时 Java 在这里直接 NPE（先求 ``user.getUser()``），
                # 所以这里也**不**加 ``user is not None`` 兜底。
                if equals(user_name, user.username):
                    rows.append(self.login_user_to_user_online(user))
            else:
                rows.append(self.login_user_to_user_online(user))
        rows.reverse()
        # Java: userOnlineList.removeAll(Collections.singleton(null));
        return [row for row in rows if row is not None]

    # Java: public List<SysUserOnline> selectUserOnlineList()
    def select_user_online_list(self) -> List[SysUserOnline]:
        """查询全部在线用户（**无调用方**，死代码照搬，见模块 docstring）。"""
        keys = self.redis_cache.keys(LOGIN_TOKEN_KEY + "*")
        rows: List[Optional[SysUserOnline]] = []
        for key in keys:
            user: Optional[LoginUser] = self.redis_cache.get_cache_object(key)
            rows.append(self.login_user_to_user_online(user))
        rows.reverse()
        return [row for row in rows if row is not None]

    # Java: public SysUserOnline loginUserToUserOnline(LoginUser user)
    def login_user_to_user_online(self, user: Optional[LoginUser]) -> Optional[SysUserOnline]:
        """设置在线用户信息（``user`` / ``user.getUser()`` 为 ``null`` 时返回 ``None``）。"""
        if user is None or user.user is None:
            return None
        online = SysUserOnline()
        online.token_id = user.token
        online.session_id = user.session_id
        online.user_name = user.username
        online.ipaddr = user.ipaddr
        online.login_location = user.login_location
        online.browser = user.browser
        online.os = user.os
        online.login_time = user.login_time
        # Java: if (StringUtils.isNotNull(user.getUser().getDept())) { setDeptName(...) }
        if user.user.dept is not None:
            online.dept_name = user.user.dept.dept_name
        return online


_SERVICE: Optional[SysUserOnlineService] = None


def get_user_online_service() -> SysUserOnlineService:
    """Java: ``@Autowired ISysUserOnlineService`` —— Spring 默认单例。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysUserOnlineService()
    return _SERVICE


def reset_user_online_service() -> None:
    """Test helper: drop the cached service so a fake Redis can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysUserOnlineService", "get_user_online_service", "reset_user_online_service"]
