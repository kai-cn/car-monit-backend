"""收费站抓拍 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml

生成器模板的标准产物：``WHERE 1 = 1``、33 条 ``<if>``、末尾 ``order by t.big_id``。
两个 ``like``：``tollname``（收费站名称）与 ``maindirectionname``（主方向名称）。

字段名全部是**小写无下划线**（``platenumber`` / ``snapshottimeunix``），所以
Python 属性名与列名、JSON 键名三者完全一致，不存在别名问题。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.domain.ods_rt_szdn_snapshot_flow_stationcapture_addcode import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcode,
)
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql id="selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeVo">``.
SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_STATIONCAPTURE_ADDCODE_VO = """
        t.big_id,
        t.datasource,
        t.cameratype,
        t.deviceid,
        t.deviceip,
        t.tollcode,
        t.tollname,
        t.orgcode,
        t.siteid,
        t.laneid,
        t.snapshottimeunix,
        t.snapshottime,
        t.receivedtimeunix,
        t.receivedtime,
        t.platenumber,
        t.platecolorcode,
        t.platecolor,
        t.platetypecode,
        t.platetype,
        t.plateconfidence,
        t.carbrand,
        t.carcolorcode,
        t.carcolor,
        t.cartypecode,
        t.cartype,
        t.cardirectioncode,
        t.cardirection,
        t.snappicturepath,
        t.loadtime,
        t.gradelevel,
        t.datauuid,
        t.maindirection,
        t.maindirectionname,
        t.reserve3
"""

#: ``resultMap`` 的 33 条 ``<result>``（键 = 列名）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "datasource",
    "cameratype",
    "deviceid",
    "deviceip",
    "tollcode",
    "tollname",
    "orgcode",
    "siteid",
    "laneid",
    "snapshottimeunix",
    "snapshottime",
    "receivedtimeunix",
    "receivedtime",
    "platenumber",
    "platecolorcode",
    "platecolor",
    "platetypecode",
    "platetype",
    "plateconfidence",
    "carbrand",
    "carcolorcode",
    "carcolor",
    "cartypecode",
    "cartype",
    "cardirectioncode",
    "cardirection",
    "snappicturepath",
    "loadtime",
    "gradelevel",
    "datauuid",
    "maindirection",
    "maindirectionname",
    "reserve3",
)

#: ``<if>`` 列表，顺序与 XML 一致。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id", null_only=True),
    If("datasource", "datasource"),
    If("cameratype", "cameratype"),
    If("deviceid", "deviceid"),
    If("deviceip", "deviceip"),
    If("tollcode", "tollcode"),
    If("tollname", "tollname", like=True),
    If("orgcode", "orgcode", null_only=True),
    If("siteid", "siteid", null_only=True),
    If("laneid", "laneid", null_only=True),
    If("snapshottimeunix", "snapshottimeunix", null_only=True),
    If("snapshottime", "snapshottime", null_only=True),
    If("receivedtimeunix", "receivedtimeunix", null_only=True),
    If("receivedtime", "receivedtime", null_only=True),
    If("platenumber", "platenumber"),
    If("platecolorcode", "platecolorcode", null_only=True),
    If("platecolor", "platecolor"),
    If("platetypecode", "platetypecode", null_only=True),
    If("platetype", "platetype"),
    If("plateconfidence", "plateconfidence", null_only=True),
    If("carbrand", "carbrand"),
    If("carcolorcode", "carcolorcode", null_only=True),
    If("carcolor", "carcolor"),
    If("cartypecode", "cartypecode", null_only=True),
    If("cartype", "cartype"),
    If("cardirectioncode", "cardirectioncode", null_only=True),
    If("cardirection", "cardirection"),
    If("snappicturepath", "snappicturepath"),
    If("loadtime", "loadtime", null_only=True),
    If("gradelevel", "gradelevel", null_only=True),
    If("datauuid", "datauuid"),
    If("maindirection", "maindirection"),
    If("maindirectionname", "maindirectionname", like=True),
    If("reserve3", "reserve3"),
)


class OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper(OdsListMapper):
    """Java: ``interface OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper``."""

    table = "ods_rt_szdn_snapshot_flow_stationcapture_addcode"
    select_vo = SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_STATIONCAPTURE_ADDCODE_VO
    entity_cls = OdsRtSzdnSnapshotFlowStationcaptureAddcode
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: XML 末尾的 ``order by t.big_id``。
    order_by: Optional[str] = "big_id"
    #: ``where t.big_id = #{bigId}``.
    detail_column = "big_id"


__all__ = [
    "CONDITIONS",
    "OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper",
    "RESULT_COLUMNS",
    "SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_STATIONCAPTURE_ADDCODE_VO",
]
