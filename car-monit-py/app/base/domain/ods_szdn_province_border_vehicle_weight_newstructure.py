"""省界称重 ``ods_szdn_province_border_vehicle_weight_newstructure``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnProvinceBorderVehicleWeightNewstructure.java

这张表的列名是 **camelCase**（``dataSource`` / ``plateNo`` ……），与项目里其它
``ods_*`` 表的 snake_case 不同。因此：

* ``resultMap`` 的 ``property`` 与 ``column`` **同名**（都是 camelCase）；
* 实体字段名仍写成 snake_case（``data_source``），序列化时由
  ``DomainModel.alias_generator=to_camel`` 还原成 ``dataSource``，与 Jackson
  的 ``getDataSource()`` 一致；
* 例外是 ``loadTime`` / ``gradeLevel``：它们的物理列名是 ``load_time`` /
  ``grade_level``（resultMap 里单独写了映射）。这两个字段**只影响 SQL 的列名**，
  不影响 JSON 的键名 —— JSON 仍是 ``loadTime`` / ``gradeLevel``。

主键是 ``datauuid``（``@TableId``），但详情语句过滤的是 **``dataSource``**：

.. code-block:: xml

    where t.dataSource = #{dataSource}

生成器的这个"主键 != 详情条件"不一致是原样保留的（见
:class:`~app.base.mapper.ods_szdn_province_border_vehicle_weight_newstructure_mapper.OdsSzdnProvinceBorderVehicleWeightNewstructureMapper`
的 ``detail_column``）。

类型速查
--------
* ``Long``： ``driveNo`` / ``vehicleSpeed`` / ``isOverweight`` / ``axleNum`` /
  ``overWeight`` / ``vehicleWeight`` / ``limitWeight`` / ``checkTimeUnix`` /
  ``axleModel`` / ``loadRate`` / ``gradeLevel`` —— 判据都是 ``!= null``（``0`` 生效）。
* ``Date``（``@JsonFormat("yyyy-MM-dd")``）： ``checkTime`` / ``loadTime``。
* ``siteId`` 是 **String**（不是数字），``plateColorCode`` / ``plateTypeCode`` /
  ``vehicleColorCode`` / ``vehicleTypeCode`` 也都是 String。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate
from app.common.core.domain.domain_model import DomainModel


class OdsSzdnProvinceBorderVehicleWeightNewstructure(DomainModel):
    """Java: ``public class OdsSzdnProvinceBorderVehicleWeightNewstructure implements Custom``."""

    #: 数据来源.
    data_source: Optional[str] = None

    #: 数据类型.
    data_type: Optional[str] = None

    #: 车牌号.
    plate_no: Optional[str] = None

    #: 站点ID（**String**）.
    site_id: Optional[str] = None

    #: 设备地点.
    location: Optional[str] = None

    #: 车道号（``Long``）.
    drive_no: Optional[int] = None

    #: 车牌颜色索引.
    plate_color: Optional[str] = None

    #: 车牌颜色代码.
    plate_color_code: Optional[str] = None

    #: 车牌类型索引.
    plate_type: Optional[str] = None

    #: 车牌类型代码.
    plate_type_code: Optional[str] = None

    #: 车辆颜色代号.
    vehicle_color: Optional[str] = None

    #: 车辆颜色代码.
    vehicle_color_code: Optional[str] = None

    #: 车辆类型代号.
    vehicle_type: Optional[str] = None

    #: 车辆类型代码.
    vehicle_type_code: Optional[str] = None

    #: 车辆速度（``@Excel(readConverterExp = "k=m/h")``）.
    vehicle_speed: Optional[int] = None

    #: 是否超载.
    is_overweight: Optional[int] = None

    #: 轴数.
    axle_num: Optional[int] = None

    #: 超重量（``@Excel(readConverterExp = "K=G")``）.
    over_weight: Optional[int] = None

    #: 重量（``@Excel(readConverterExp = "K=G")``）.
    vehicle_weight: Optional[int] = None

    #: 车辆限重（``@Excel(readConverterExp = "K=G")``）.
    limit_weight: Optional[int] = None

    #: 检测时间Unix格式.
    check_time_unix: Optional[int] = None

    #: 检测时间 ``@JsonFormat("yyyy-MM-dd")``（列名 ``checkTime``）.
    check_time: OdsDate = None

    #: 轴型.
    axle_model: Optional[int] = None

    #: 超载率.
    load_rate: Optional[int] = None

    #: 轴型详细数据.
    axle_array: Optional[str] = None

    #: 图片数组（生成器把 ``Array`` 拼成了 ``Arry``，照留）.
    weighing_images_arry: Optional[str] = None

    #: 加载时间 ``@JsonFormat("yyyy-MM-dd")``；**物理列名是 ``load_time``**.
    load_time: OdsDate = None

    #: 分类分级（``Long``）；**物理列名是 ``grade_level``**.
    grade_level: Optional[int] = None

    #: 主键. Java: ``@TableId(value = "datauuid", type = IdType.ASSIGN_UUID)``
    datauuid: Optional[str] = None

    #: 预留字段（无 ``@Excel``）.
    reserve1: Optional[str] = None

    #: 预留字段（无 ``@Excel``）.
    reserve2: Optional[str] = None

    #: 预留字段（无 ``@Excel``）.
    reserve3: Optional[str] = None


__all__ = ["OdsSzdnProvinceBorderVehicleWeightNewstructure"]
