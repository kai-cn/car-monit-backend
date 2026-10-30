# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysLogininfor.java
"""系统访问记录 sys_logininfor / login audit record.

Every login attempt, logout and failed captcha lands in this table, written asynchronously by
:class:`app.framework.manager.factory.async_factory.AsyncFactory`. Two details worth knowing:

* ``loginTime`` is **not** set by Java code -- the MyBatis ``insertLogininfor`` statement
  writes ``sysdate()``, so the timestamp comes from the database clock, not the JVM. That is
  why :class:`SysLogininfor` is never assigned a value for it during an insert.
* ``status`` is the string ``"0"`` (成功) / ``"1"`` (失败), mapped from ``Constants.SUCCESS`` /
  ``Constants.FAIL``. It is *not* the ``Constants.LOGIN_SUCCESS`` ("Success") value; the
  factory translates between the two.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import field_serializer, field_validator

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.json_utils import format_date_time, parse_date_time


class SysLogininfor(BaseEntity):
    """Java: ``SysLogininfor extends BaseEntity``."""

    #: ID
    info_id: Optional[int] = None
    #: 用户账号
    user_name: Optional[str] = None
    #: 登录状态 0成功 1失败
    status: Optional[str] = None
    #: 登录IP地址
    ipaddr: Optional[str] = None
    #: 登录地点
    login_location: Optional[str] = None
    #: 浏览器类型
    browser: Optional[str] = None
    #: 操作系统
    os: Optional[str] = None
    #: 提示消息
    msg: Optional[str] = None
    #: 访问时间 -- Java ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    login_time: Optional[datetime] = None

    #: ``@Excel`` 注解表，**顺序与 Java 字段声明顺序逐字一致**（共 9 列）。
    #: 列名里有两处容易抄错的地方，都与 Java 原文一致：
    #: ``ipaddr`` 的表头是"登录**地址**"（不是 IP），``userName`` 是"用户账号"。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("info_id", Excel(name="序号", cell_type=ColumnType.NUMERIC)),
        ("user_name", Excel(name="用户账号")),
        ("status", Excel(name="登录状态", read_converter_exp="0=成功,1=失败")),
        ("ipaddr", Excel(name="登录地址")),
        ("login_location", Excel(name="登录地点")),
        ("browser", Excel(name="浏览器")),
        ("os", Excel(name="操作系统")),
        ("msg", Excel(name="提示消息")),
        (
            "login_time",
            Excel(name="访问时间", width=30, date_format="yyyy-MM-dd HH:mm:ss"),
        ),
    )

    @field_serializer("login_time")
    def _serialize_login_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        return format_date_time(value)

    @field_validator("login_time", mode="before")
    @classmethod
    def _parse_login_time(cls, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        return parse_date_time(value)


__all__ = ["SysLogininfor"]
