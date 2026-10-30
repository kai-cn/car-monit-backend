"""车俩白名单对象 car_white_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWhiteInfo.java

``extends BasePlusEntity``（``ASSIGN_UUID``）。三个 ``@TableField(exist = false)``
字段只参与 JSON：

* ``createTimeStr`` —— 导出时由 ``createTime`` 格式化而来；
* ``createInfo`` —— 列表 SQL 里有 ``concat(...) createInfo`` 别名，但
  ``resultMap`` **没有**映射它，所以列表接口返回的 ``createInfo`` 永远是 ``null``
  （见 ``CarWhiteInfoMapper`` 注释）；
* ``carNoQuery`` —— 车牌号模糊查询条件。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarWhiteInfo(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarWhiteInfo``."""

    #: 车牌颜色（字典：1白色2黑色）
    plate_color: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 相关附件(附件ids)
    file_ids: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 查询时间 —— ``@TableField(exist = false)``
    create_time_str: Optional[str] = None
    #: 录入单位以及用户 —— ``@TableField(exist = false)``
    create_info: Optional[str] = None
    #: 车牌号查询 —— ``@TableField(exist = false)``
    car_no_query: Optional[str] = None

    #: ``@Excel`` 注解表。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("plate_color", Excel(name="车牌颜色", read_converter_exp="字=典：1白色2黑色")),
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("car_num", Excel(name="轴数")),
        ("file_ids", Excel(name="相关附件(附件ids)")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarWhiteInfo"]
