"""省界称重 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml

Java 接口是 ``extends BaseMapper<...>``，但 ``ServiceImpl`` 只做转发、没有一处
``BaseMapper`` CRUD 调用，所以这里**不**继承
:class:`~app.base.mapper.plus_mapper.PlusMapper`。

三处必须照抄、不能"顺手修正"的地方
----------------------------------
1. **没有 ``order by``**。PageHelper 只在语句本身没有 ``order by`` 时追加客户端
   ``orderByColumn`` / ``isAsc``，所以本接口的"点表头排序"是**生效**的；
   给这里补一个 ``order by`` 会悄悄改掉这个行为。
2. **详情语句过滤 ``dataSource``，不是主键 ``datauuid``**。这是生成器的产物：
   ``@TableId`` 是 ``datauuid``，而 ``select...ById`` 的 ``where`` 用的是
   ``t.dataSource``。一个 ``dataSource`` 可能命中多行，``.first()`` 取第一条 ——
   与 MyBatis ``selectOne`` 不同（它会在多行时抛 ``TooManyResultsException``）。
   保留"取第一条"的实际效果，见 ``COMPATIBILITY.md``。
3. 列名是 **camelCase**（``t.dataSource``）而 ``load_time`` / ``grade_level`` 是
   snake_case —— ``result_columns`` 用的就是这些原始列名（MyBatis 用列名回填）。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.domain.ods_szdn_province_border_vehicle_weight_newstructure import (
    OdsSzdnProvinceBorderVehicleWeightNewstructure,
)
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql id="selectOdsSzdnProvinceBorderVehicleWeightNewstructureVo">``.
SELECT_ODS_SZDN_PROVINCE_BORDER_VEHICLE_WEIGHT_NEWSTRUCTURE_VO = """
        t.dataSource,
        t.dataType,
        t.plateNo,
        t.siteId,
        t.location,
        t.driveNo,
        t.plateColor,
        t.plateColorCode,
        t.plateType,
        t.plateTypeCode,
        t.vehicleColor,
        t.vehicleColorCode,
        t.vehicleType,
        t.vehicleTypeCode,
        t.vehicleSpeed,
        t.isOverweight,
        t.axleNum,
        t.overWeight,
        t.vehicleWeight,
        t.limitWeight,
        t.checkTimeUnix,
        t.checkTime,
        t.axleModel,
        t.loadRate,
        t.axleArray,
        t.weighingImagesArry,
        t.load_time,
        t.grade_level,
        t.datauuid,
        t.reserve1,
        t.reserve2,
        t.reserve3
"""

#: ``resultMap`` 的 32 条 ``<result>`` —— 键是**列名**（= 取行时的 key）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "dataSource",
    "dataType",
    "plateNo",
    "siteId",
    "location",
    "driveNo",
    "plateColor",
    "plateColorCode",
    "plateType",
    "plateTypeCode",
    "vehicleColor",
    "vehicleColorCode",
    "vehicleType",
    "vehicleTypeCode",
    "vehicleSpeed",
    "isOverweight",
    "axleNum",
    "overWeight",
    "vehicleWeight",
    "limitWeight",
    "checkTimeUnix",
    "checkTime",
    "axleModel",
    "loadRate",
    "axleArray",
    "weighingImagesArry",
    "load_time",
    "grade_level",
    "datauuid",
    "reserve1",
    "reserve2",
    "reserve3",
)

#: ``<if>`` 列表，顺序与 XML 一致。``null_only=True`` 对应 ``test="x != null"``。
CONDITIONS: Tuple[If, ...] = (
    If("data_source", "dataSource"),
    If("data_type", "dataType"),
    If("plate_no", "plateNo"),
    If("site_id", "siteId"),
    If("location", "location"),
    If("drive_no", "driveNo", null_only=True),
    If("plate_color", "plateColor"),
    If("plate_color_code", "plateColorCode"),
    If("plate_type", "plateType"),
    If("plate_type_code", "plateTypeCode"),
    If("vehicle_color", "vehicleColor"),
    If("vehicle_color_code", "vehicleColorCode"),
    If("vehicle_type", "vehicleType"),
    If("vehicle_type_code", "vehicleTypeCode"),
    If("vehicle_speed", "vehicleSpeed", null_only=True),
    If("is_overweight", "isOverweight", null_only=True),
    If("axle_num", "axleNum", null_only=True),
    If("over_weight", "overWeight", null_only=True),
    If("vehicle_weight", "vehicleWeight", null_only=True),
    If("limit_weight", "limitWeight", null_only=True),
    If("check_time_unix", "checkTimeUnix", null_only=True),
    If("check_time", "checkTime", null_only=True),
    If("axle_model", "axleModel", null_only=True),
    If("load_rate", "loadRate", null_only=True),
    If("axle_array", "axleArray"),
    If("weighing_images_arry", "weighingImagesArry"),
    If("load_time", "load_time", null_only=True),
    If("grade_level", "grade_level", null_only=True),
    If("datauuid", "datauuid"),
    If("reserve1", "reserve1"),
    If("reserve2", "reserve2"),
    If("reserve3", "reserve3"),
)


class OdsSzdnProvinceBorderVehicleWeightNewstructureMapper(OdsListMapper):
    """Java: ``interface OdsSzdnProvinceBorderVehicleWeightNewstructureMapper``."""

    table = "ods_szdn_province_border_vehicle_weight_newstructure"
    select_vo = SELECT_ODS_SZDN_PROVINCE_BORDER_VEHICLE_WEIGHT_NEWSTRUCTURE_VO
    entity_cls = OdsSzdnProvinceBorderVehicleWeightNewstructure
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: XML 里**没有** ``order by`` —— 不要补。
    order_by: Optional[str] = None
    #: ``where t.dataSource = #{dataSource}``（**不是** ``datauuid``）。
    detail_column = "dataSource"


__all__ = [
    "OdsSzdnProvinceBorderVehicleWeightNewstructureMapper",
    "SELECT_ODS_SZDN_PROVINCE_BORDER_VEHICLE_WEIGHT_NEWSTRUCTURE_VO",
    "RESULT_COLUMNS",
    "CONDITIONS",
]
