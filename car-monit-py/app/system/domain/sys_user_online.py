# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserOnline.java
"""当前在线会话 SysUserOnline / one online session row.

**不继承 ``BaseEntity``**（Java 是裸 POJO + Lombok ``@Data``），所以：
没有 ``searchValue`` / ``remark`` / ``params``，也没有审计列；它也不对应任何表 ——
数据来自 Redis 里 ``login_tokens:*`` 反序列化出来的 ``LoginUser``。

``loginTime`` 是 ``Long``（epoch **毫秒**），不是 ``Date``
---------------------------------------------------------
Java 的 ``LoginUser.loginTime`` 就是 ``Long``，``SysUserOnline`` 原样搬运，所以 JSON 里是
**数字**而不是 ``"yyyy-MM-dd HH:mm:ss"`` 字符串。前端在线用户表格自己用 ``parseTime``
转格式 —— 改成字符串反而是行为改变。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class SysUserOnline(DomainModel):
    """Java: ``@Data class SysUserOnline``."""

    #: token编号（Redis 键 ``login_tokens:`` 之后的那一段；**不是** JWT 本身）
    token_id: Optional[str] = None
    #: 会话（``LoginUser.sessionId``）
    session_id: Optional[str] = None
    #: 部门名称（``user.dept.deptName``；没有部门时为 ``None``）
    dept_name: Optional[str] = None
    #: 用户名称（``user.userName``）
    user_name: Optional[str] = None
    #: 登录IP地址
    ipaddr: Optional[str] = None
    #: 登录地址
    login_location: Optional[str] = None
    #: 浏览器类型
    browser: Optional[str] = None
    #: 操作系统
    os: Optional[str] = None
    #: 登录时间（epoch 毫秒）
    login_time: Optional[int] = None


__all__ = ["SysUserOnline"]
