"""服务区对象 base_config_service_area.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/BaseConfigServiceArea.java

Java 侧 ``@TableName("base_config_service_area")`` +
``extends BasePlusEntity implements Custom``。``Custom`` 是空标记接口，不迁移。

注意这一族实体的两点"反直觉"：

* 主键是 ``id``（UUID），但**业务唯一键是 ``fwqbm``**；``getInfo`` / ``remove``
  走的是 ``fwqbm``，不是 ``id``。列表条件里 ``id`` 和 ``fwqbm`` 各自独立。
* 表上有 ``del_flag`` 列（``BasePlusEntity``），但**所有 XML 语句都没有过滤它**：
  列表和详情会把已"逻辑删除"的行一起查出来。删除语句本身还是**物理** ``delete``
  （见 ``BaseConfigServiceAreaMapper``）。照抄，不要补 ``del_flag = '0'``。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class BaseConfigServiceArea(BasePlusEntity):
    """服务区对象 entity."""

    #: 判定进入的服务区编码
    fwqbm: Optional[str] = None
    #: 判定进入的服务区名称
    fwqmc: Optional[str] = None
    #: 经度
    lon: Optional[str] = None
    #: 维度
    lat: Optional[str] = None
    #: 路线编码
    road_code: Optional[str] = None
    #: 路段编码
    section_code: Optional[str] = None
    #: 桩号
    pile_no: Optional[str] = None

    #: ``@Excel`` 注解表；``BasePlusEntity`` 上一句 ``@Excel`` 都没有，所以只有这 7 列。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("fwqbm", Excel(name="判定进入的服务区编码")),
        ("fwqmc", Excel(name="判定进入的服务区名称")),
        ("lon", Excel(name="经度")),
        ("lat", Excel(name="维度")),
        ("road_code", Excel(name="路线编码")),
        ("section_code", Excel(name="路段编码")),
        ("pile_no", Excel(name="桩号")),
    )


__all__ = ["BaseConfigServiceArea"]
