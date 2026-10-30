"""省界设备ip ``ods_szdn_gantry_ip``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantryIp.java

三个照抄的细节
--------------
1. ``id`` 声明成 ``Long``，却挂了 ``@TableId(type = IdType.ASSIGN_UUID)`` —— UUID 是
   32 位字符串，塞不进 ``Long``。本模块**没有**新增/修改端点，``insert`` 永远不被
   调用，所以这个矛盾在线上不会暴露；字段类型仍按 Java 声明取整型。
2. ``brand`` **没有** ``@Excel``（其余 5 个字段有），不过本控制器没有 ``/export``，
   注解不产生任何可观察行为 —— 所以这里不维护 ``EXCEL_FIELDS``。
3. ``odsSzdnGantry`` 是 ``@TableField(exist = false)`` 的关联对象，XML 的
   ``resultMap`` 也**没有**映射它，因此它永远是 ``null``；只为与 Java 的字段表对齐。

字段顺序 = Jackson 的输出顺序（父类字段在前，本类按声明顺序）。
"""

from __future__ import annotations

from typing import Any, Optional

from app.common.core.domain.domain_model import DomainModel


class OdsSzdnGantryIp(DomainModel):
    """Java: ``public class OdsSzdnGantryIp implements Custom``."""

    #: 主键. Java: ``@TableId(value = "id", type = IdType.ASSIGN_UUID) private Long id;``
    id: Optional[int] = None

    #: 门架编号.
    gantry_code: Optional[str] = None

    #: 门架名称.
    gantry_name: Optional[str] = None

    #: 机构编码.
    org_code: Optional[str] = None

    #: 设备ip.
    ip: Optional[str] = None

    #: 品牌（无 ``@Excel``）.
    brand: Optional[str] = None

    #: 类型1是省界门架.
    type: Optional[str] = None

    #: Java: ``@TableField(exist = false) private OdsSzdnGantry odsSzdnGantry;``
    #: 永不填值（XML 未映射），声明在此只为让 JSON 里出现同名的 ``null``。
    ods_szdn_gantry: Optional[Any] = None


__all__ = ["OdsSzdnGantryIp"]
