"""服务区车辆流水 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsCxztFwqcllsMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml

⚠ 路径与包不同名
----------------
类在 ``com.ruoyi.base.mapper``，但**控制器挂在 ``/manager/fwqclls``** 下，而且
``list`` **带权限点** ``manager:fwqclls:list``。别因为"文件叫 base"就以为它走
``/base/*`` + 无权限 —— 这是本次迁移里唯一一处这样的错位。

其余与生成器模板一致：``WHERE 1=1``（注意没有空格）、**没有 ``order by``**
（所以 PageHelper 的客户端排序对 ``/list`` 生效）。

``crosstime`` 是 ``Date``，判据是 ``!= null``；``loadTime`` / ``gradeLevel`` 是
**String**，判据是 ``!= null and != ''`` —— 按字段名猜类型会猜错。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.domain.ods_cxzt_fwqclls import OdsCxztFwqclls
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql id="selectOdsCxztFwqcllsVo">``.
SELECT_ODS_CXZT_FWQCLLS_VO = """
        t.big_id,
        t.datauuid,
        t.targetpicurl,
        t.vehiclebrand,
        t.platepicurl,
        t.rollvehiclestype,
        t.plateno,
        t.directionname,
        t.platetype,
        t.dangmark,
        t.crosstime,
        t.axles,
        t.devicename,
        t.ipaddress,
        t.servicename,
        t.vehicletype,
        t.load_time,
        t.grade_level
"""

#: ``resultMap`` 的 18 条 ``<result>``（键 = 列名）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "datauuid",
    "targetpicurl",
    "vehiclebrand",
    "platepicurl",
    "rollvehiclestype",
    "plateno",
    "directionname",
    "platetype",
    "dangmark",
    "crosstime",
    "axles",
    "devicename",
    "ipaddress",
    "servicename",
    "vehicletype",
    "load_time",
    "grade_level",
)

#: ``<if>`` 列表，顺序与 XML 一致。三处 ``like``：方向 / 设备名 / 服务区名。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id", null_only=True),
    If("datauuid", "datauuid"),
    If("targetpicurl", "targetpicurl"),
    If("vehiclebrand", "vehiclebrand"),
    If("platepicurl", "platepicurl"),
    If("rollvehiclestype", "rollvehiclestype"),
    If("plateno", "plateno"),
    If("directionname", "directionname", like=True),
    If("platetype", "platetype"),
    If("dangmark", "dangmark"),
    If("crosstime", "crosstime", null_only=True),
    If("axles", "axles"),
    If("devicename", "devicename", like=True),
    If("ipaddress", "ipaddress"),
    If("servicename", "servicename", like=True),
    If("vehicletype", "vehicletype"),
    If("load_time", "load_time"),
    If("grade_level", "grade_level"),
)


class OdsCxztFwqcllsMapper(OdsListMapper):
    """Java: ``interface OdsCxztFwqcllsMapper extends BaseMapper<OdsCxztFwqclls>``."""

    table = "ods_cxzt_fwqclls"
    select_vo = SELECT_ODS_CXZT_FWQCLLS_VO
    entity_cls = OdsCxztFwqclls
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: XML 里**没有** ``order by``。
    order_by: Optional[str] = None
    #: ``where t.big_id = #{bigId}``.
    detail_column = "big_id"


__all__ = [
    "CONDITIONS",
    "OdsCxztFwqcllsMapper",
    "RESULT_COLUMNS",
    "SELECT_ODS_CXZT_FWQCLLS_VO",
]
