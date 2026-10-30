"""用户常用菜单表 sys_index_menu.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysIndexMenu.java

``extends BaseUuidEntity``（**不是** ``BaseEntity``）
--------------------------------------------------
主键是 UUID 字符串 ``id``，审计人是 ``Long``。JSON 因此同时携带
``epsId`` / ``delFlag`` / ``deptSubCode`` / ``tenantId`` / ``sort`` / ``flag`` /
``params`` 等基类字段，见 :mod:`app.common.core.domain.base_uuid_entity`。

8 个自有字段
------------
``userId`` / ``menuId`` / ``menuName`` / ``menuName1`` / ``menuName2`` /
``menuName3`` / ``menuIds`` / ``menuUrl``。

其中只有 3 个真的被 SQL 填充：

* ``menuName`` / ``menuName2`` —— ``selectSysIndexMenuList`` 的投影列；
* ``menuUrl`` —— ``getList`` 里 ``concat(t2.path,'/',t1.path)`` 拼出来的。

``menuName1`` / ``menuName3`` **没有任何语句写入**，也**不进 ``resultMap``**
（``SysIndexMenuResult`` 只列了 ``menuName``）。照留，见迁移原则第 4 条。

``menuIds`` 是"入参专用"字段
----------------------------
它不进库：``add`` 只把 ``menuIds`` 拆开成一行行 ``menuId`` 去写（见 service）。
库表里没有这一列，所以 ``resultMap`` 里也没有它。

**没有任何校验注解**
------------------
``add`` / ``edit`` 只写了 ``@RequestBody``，连 ``@Validated`` 都没有 —— 所以实体上
一个约束注解也不需要。Python 侧不建 ``*_CONSTRAINTS``。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class SysIndexMenu(BaseUuidEntity):
    """用户常用菜单对象 sys_index_menu."""

    #: 用户 ID
    user_id: Optional[int] = None
    #: 菜单 ID
    menu_id: Optional[int] = None
    #: 菜单名称（``selectSysIndexMenuList`` 投影 ``t1.menu_name``）
    menu_name: Optional[str] = None
    #: 一级菜单名称 —— **无人写入**
    menu_name1: Optional[str] = None
    #: 二级菜单名称（``selectSysIndexMenuList`` 投影 ``t2.menu_name``）
    menu_name2: Optional[str] = None
    #: 三级菜单名称 —— **无人写入**
    menu_name3: Optional[str] = None
    #: 多个菜单 ids（逗号串，仅入参；库里没有这一列）
    menu_ids: Optional[str] = None
    #: 菜单地址（``getList`` 里 ``concat`` 出来的）
    menu_url: Optional[str] = None

    #: ``@Excel`` 注解表 —— 只有 ``userId`` / ``menuId`` 两个字段有注解，
    #: 其余 6 个（含基类的 ``id`` 与审计列）**不导出**。
    #: 两列都是默认的 ``ColumnType.STRING``（Java 同样没写 ``cellType``），所以
    #: 数字会被当成字符串写出。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("user_id", Excel(name="用户ID")),
        ("menu_id", Excel(name="菜单ID")),
    )


__all__ = ["SysIndexMenu"]