"""数据过滤处理（``@DataScope`` 切面的等价实现）.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/DataScopeAspect.java

Java 是怎么做的
---------------
``@DataScope(deptAlias = "d", userAlias = "u")`` 标在 Service 方法上，切面在方法体**之前**
执行，把生成的 SQL 片段塞进**入参实体**的 ``params.dataScope`` 里：

    baseEntity.getParams().put("dataScope", " AND (" + sqlString.substring(4) + ")");

Mapper XML 再用 ``${params.dataScope}`` 把它拼进 SQL。所以这是一个
"用入参对象当传参通道"的隐式副作用，Service 方法签名里看不到任何数据权限参数。

Python 是怎么做的
-----------------
没有 AOP，改成 Service 方法体**第一行**显式调用 :func:`apply_data_scope`：

    def select_user_list(self, user):
        # Java: @DataScope(deptAlias = "d", userAlias = "u")
        apply_data_scope(user, "d", "u")
        return self._mapper.select_user_list(user)

写进 ``user.params["dataScope"]`` 的结果与 Java 完全一致，Mapper 侧同样用
``params.get("dataScope")`` 读取。

踩坑记录（全部来自 Java 原逻辑，不要"修好"）
-------------------------------------------
1. **只有入参是 ``BaseEntity`` 时才会写**。``dataScopeFilter`` 里有一句
   ``if (StringUtils.isNotNull(params) && params instanceof BaseEntity)``。
2. **``params.dataScope`` 不会自动清空**。切面只在**进入**方法时 ``put``，从不清除；
   RuoYi 上游版本有一个 ``clearDataScope`` 的 ``@After``，但本项目的
   ``DataScopeAspect`` **没有**它。于是同一个实体对象被复用、而第二次调用**没有**
   生成任何片段（例如角色全变成了 ``dataScope=1``，或调用方换成了管理员）时，
   第一次写进去的**陈旧片段会留在线程内继续生效**。注意：两次都有片段时是 ``put``
   **覆盖**，不是 ``AND`` 叠加。Python 保持同样的"脏"行为。
3. **超级管理员不过滤**（``!currentUser.isAdmin()``），无登录用户也不过滤。
4. ``dataScope`` 为 ``1``（全部数据）时直接 ``break`` 并把已拼接的内容**清空**。
5. ``sqlString.substring(4)`` 砍掉开头固定的 ``" OR "``，所以最终片段是
   ``" AND (a OR b)"``；如果只有一条规则，``substring(4)`` 会得到
   ``"d.dept_id = 100"``（前面没有 OR 可砍，实际砍掉的是 ``" OR "`` 四个字符，
   因为循环里每条规则都以 ``" OR "`` 开头）。

安全说明
--------
片段里拼接的是 ``deptId`` / ``userId`` / ``roleId`` —— 全部来自数据库的 ``Long``，
不来自请求参数，因此与 Java 一样不存在注入面。**不要**把这里改成接受字符串参数。
"""

from __future__ import annotations

import logging
from typing import Optional

from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.framework.security.context.security_context import SecurityContextHolder

logger = logging.getLogger("app.framework.aspectj.data_scope_aspect")

#: 全部数据权限
DATA_SCOPE_ALL = "1"
#: 自定数据权限
DATA_SCOPE_CUSTOM = "2"
#: 部门数据权限
DATA_SCOPE_DEPT = "3"
#: 部门及以下数据权限
DATA_SCOPE_DEPT_AND_CHILD = "4"
#: 仅本人数据权限
DATA_SCOPE_SELF = "5"

#: 数据权限过滤关键字
DATA_SCOPE = "dataScope"


def _current_login_user() -> Optional[LoginUser]:
    """Java: ``tokenService.getLoginUser(ServletUtils.getRequest())`` -- 未登录返回 ``None``."""
    try:
        authentication = SecurityContextHolder.get_context().get_authentication()
        if authentication is None:
            return None
        principal = authentication.get_principal()
        if isinstance(principal, LoginUser):
            return principal
        return None
    except Exception:  # noqa: BLE001 - 切面不能因为取不到用户而打断业务
        return None


def data_scope_filter(login_user: LoginUser, dept_alias: str, user_alias: str) -> str:
    """Java: ``DataScopeAspect.dataScopeFilter(...)`` -> 未经 ``substring(4)`` 的原始片段.

    返回值形如 ``" OR d.dept_id = 100 "``；没有任何规则时返回 ``""``。
    """
    user: Optional[SysUser] = login_user.user
    if user is None:
        return ""

    sql_string = ""
    for role in user.roles or []:
        data_scope = _role_data_scope(role)
        if DATA_SCOPE_ALL == data_scope:
            # Java: sqlString = new StringBuilder(); break;
            sql_string = ""
            break
        if DATA_SCOPE_CUSTOM == data_scope:
            sql_string += f" OR {dept_alias}.dept_id IN ( SELECT dept_id FROM sys_role_dept WHERE role_id = {_id(role.role_id)} ) "
        elif DATA_SCOPE_DEPT == data_scope:
            sql_string += f" OR {dept_alias}.dept_id = {_id(user.dept_id)} "
        elif DATA_SCOPE_DEPT_AND_CHILD == data_scope:
            sql_string += (
                f" OR {dept_alias}.dept_id IN ( SELECT dept_id FROM sys_dept WHERE dept_id = "
                f"{_id(user.dept_id)} or find_in_set( {_id(user.dept_id)} , ancestors ) )"
            )
        elif DATA_SCOPE_SELF == data_scope:
            if user_alias is not None and user_alias.strip() != "":
                sql_string += f" OR {user_alias}.user_id = {_id(user.user_id)} "
            else:
                # 数据权限为仅本人且没有 userAlias 别名不查询任何数据
                sql_string += " OR 1=0 "
    return sql_string


def apply_data_scope(entity: Optional[BaseEntity], dept_alias: str, user_alias: str = "") -> None:
    """Java: ``@DataScope`` 切面的 ``handleDataScope`` + ``dataScopeFilter``.

    与 Java 一致：未登录、超级管理员、入参不是 ``BaseEntity`` 时**什么都不做**
    （包括不清理上一次残留的 ``params["dataScope"]``）。
    """
    login_user = _current_login_user()
    if login_user is None:
        return
    user = login_user.user
    if user is None or user.admin:
        return

    sql_string = data_scope_filter(login_user, dept_alias, user_alias)
    if sql_string is not None and sql_string.strip() != "" and isinstance(entity, BaseEntity):
        # Java: " AND (" + sqlString.substring(4) + ")"
        entity.params[DATA_SCOPE] = " AND (" + sql_string[4:] + ")"


def _role_data_scope(role: SysRole) -> Optional[str]:
    return role.data_scope if isinstance(role, SysRole) else None


def _id(value: Optional[int]) -> str:
    """Java 里这些值都是 ``Long``/``Integer``，``String.valueOf(null)`` 会拼出 ``"null"``。

    保持同样的字面量：``deptId`` 为 ``null`` 时 SQL 片段就是
    ``d.dept_id = null``（永远不成立），而不是抛异常。
    """
    return "null" if value is None else str(value)


__all__ = [
    "DATA_SCOPE_ALL",
    "DATA_SCOPE_CUSTOM",
    "DATA_SCOPE_DEPT",
    "DATA_SCOPE_DEPT_AND_CHILD",
    "DATA_SCOPE_SELF",
    "DATA_SCOPE",
    "data_scope_filter",
    "apply_data_scope",
]
