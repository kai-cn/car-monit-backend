"""收费站ip ``ods_szdn_toll_station_ip``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnTollStationIp.java

两个照抄的细节
--------------
1. ``id`` 同样是 ``Long`` + ``@TableId(type = IdType.ASSIGN_UUID)`` 的矛盾组合；
   本模块只有查询端点，``insert`` 不会被调用。
2. 所有字段都**没有** ``@Excel``（对比 :class:`OdsSzdnGantryIp`），也没有
   ``type`` 字段。``odsSzdnToll`` 是 ``@TableField(exist = false)`` 的关联对象，
   ``resultMap`` 未映射 -> 永远 ``null``。
"""

from __future__ import annotations

from typing import Any, Optional

from app.common.core.domain.domain_model import DomainModel


class OdsSzdnTollStationIp(DomainModel):
    """Java: ``public class OdsSzdnTollStationIp implements Custom``."""

    #: 主键. Java: ``@TableId(value = "id", type = IdType.ASSIGN_UUID) private Long id;``
    id: Optional[int] = None

    #: 收费站编号.
    toll_code: Optional[str] = None

    #: 收费站名称.
    toll_name: Optional[str] = None

    #: 机构编码.
    org_code: Optional[str] = None

    #: 设备ip.
    ip: Optional[str] = None

    #: 品牌.
    brand: Optional[str] = None

    #: Java: ``@TableField(exist = false) private OdsSzdnToll odsSzdnToll;``
    ods_szdn_toll: Optional[Any] = None


__all__ = ["OdsSzdnTollStationIp"]
