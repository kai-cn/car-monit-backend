"""系统升级信息表 sys_upgrade_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUpgradeInfo.java

``extends BaseUuidEntity``（与 ``SysIndexMenu`` 同一个基类）
-----------------------------------------------------------
主键是 UUID 字符串 ``id``，审计人是 ``Long``，JSON 里因此携带 ``epsId`` /
``delFlag`` / ``deptSubCode`` / ``tenantId`` / ``sort`` / ``flag`` / ``params``
等基类字段，见 :mod:`app.common.core.domain.base_uuid_entity`。

只有 3 个自有字段
-----------------
``ver``（版本）/ ``info``（更新信息）/ ``backCol1``（备用字段）。

``backCol1`` 是"标记位"
-----------------------
``selectSysUpgradeInfoNewest`` 写死了 ``t.back_col1 = 1``，而这一列是 ``varchar``：

* 只有值恰好为 ``"1"`` 的行会被当作"最新更新日志"；
* 其余值（含 ``"0"`` / ``""`` / ``NULL``）全部被排除。

``info`` 在 Python 侧**不是保留字**，可以原样当属性名（与 Java 同名）。

**没有任何校验注解**
------------------
控制器上的 ``add`` / ``edit`` 只写了 ``@RequestBody``，连 ``@Validated`` 都没有 ——
所以本模块同样**不建** ``*_CONSTRAINTS``。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class SysUpgradeInfo(BaseUuidEntity):
    """系统升级信息对象 sys_upgrade_info."""

    #: 版本
    ver: Optional[str] = None
    #: 更新信息
    info: Optional[str] = None
    #: 备用字段1 —— ``selectSysUpgradeInfoNewest`` 用它筛"最新日志"（值必须是 ``"1"``）
    back_col1: Optional[str] = None

    #: ``@Excel`` 注解表 —— **空**。Java 的 ``SysUpgradeInfo`` 一个 ``@Excel`` 都没写，
    #: 所以 ``/system/upgradeInfo/export`` 产出的 xlsx 只有表名、没有列头，每个实体
    #: 只占一行空行。这是既有行为，照抄（见 COMPATIBILITY §37）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = ()


__all__ = ["SysUpgradeInfo"]
