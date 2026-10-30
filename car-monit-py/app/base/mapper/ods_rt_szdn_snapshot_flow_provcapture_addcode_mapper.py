"""省界抓拍 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml

``base`` 包里最宽的声明：82 条 ``<if>``、78 列投影。全部是**等值**条件
（一个 ``like`` 都没有），字段名全是小写无下划线，所以属性名 / 列名 / JSON
键名三者相同。

判据分布（逐条照抄，不要按"看起来像数字"推断）：

* ``!= null and != ''``（String）：``deviceip`` / ``extendattribute`` /
  ``axletype`` / ``platecolor`` / ``cover`` / ``resulttype`` / ``carmodels`` /
  ``laneposition`` / ``specialclass`` / ``tailplatenumber`` / ``tailimage`` /
  ``attached`` / ``guid`` / ``datasource`` / ``carclass`` / ``gantryid`` /
  ``smallsideimage`` / ``sidescenetype`` / ``envstate`` / ``headscenetype`` /
  ``sidedrivingdirection`` / ``speed`` / ``tailplateimage`` /
  ``headdrivingdirection`` / ``cartype`` / ``plateimage`` / ``changelane`` /
  ``sideimage`` / ``tailplateposition`` / ``headimage`` / ``devicecode`` /
  ``platenumber`` / ``tailplatecolor`` / ``plateposition`` / ``datauuid`` /
  ``reserve1`` / ``reserve2`` / ``reserve3``
* ``!= null``（数字 / 日期）：其余。

末尾 ``order by t.big_id`` —— 客户端排序不生效。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.domain.ods_rt_szdn_snapshot_flow_provcapture_addcode import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcode,
)
from app.base.mapper.ods_sql import If, OdsListMapper

#: Verbatim from ``<sql id="selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeVo">``.
SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_PROVCAPTURE_ADDCODE_VO = """
        t.big_id,
        t.deviceip,
        t.tailcapturetimeunix,
        t.tailcapturetime,
        t.extendattribute,
        t.smallsideimagewidth,
        t.axletype,
        t.smallsideimageheight,
        t.platecolorcode,
        t.platecolor,
        t.cover,
        t.averageauthoritative,
        t.headlanecode,
        t.specialvehicle,
        t.carlength,
        t.resulttype,
        t.carhight,
        t.carmodelscode,
        t.carmodels,
        t.laneposition,
        t.firstauthoritative,
        t.tailplateimageheight,
        t.axlecount,
        t.plateimagewidth,
        t.specialclass,
        t.tailplatenumber,
        t.tailimage,
        t.sidecapturetimeunix,
        t.sidecapturetime,
        t.sidelanecode,
        t.wheelbase,
        t.attached,
        t.wheelcount,
        t.guid,
        t.sideimagewidth,
        t.plateimageheight,
        t.datasource,
        t.carclass,
        t.gantryid,
        t.smallsideimage,
        t.headimageheight,
        t.sidescenetypecode,
        t.sidescenetype,
        t.tailimagewidth,
        t.envstate,
        t.headscenetypecode,
        t.headscenetype,
        t.sidedrivingdirectioncode,
        t.sidedrivingdirection,
        t.sideimageheight,
        t.speed,
        t.tailplateimage,
        t.headdrivingdirectioncode,
        t.headdrivingdirection,
        t.cartype,
        t.plateimage,
        t.changelane,
        t.sideimage,
        t.tailplateposition,
        t.headimagewidth,
        t.headimage,
        t.carweight,
        t.tailimageheight,
        t.devicecode,
        t.platenumber,
        t.tailplatecolorcode,
        t.tailplatecolor,
        t.uploadtimeunix,
        t.uploadtime,
        t.impostoraxlecount,
        t.taillanecode,
        t.siteid,
        t.headcapturetimeunix,
        t.headcapturetime,
        t.plateposition,
        t.tailplateimagewidth,
        t.loadtime,
        t.gradelevel,
        t.datauuid,
        t.reserve1,
        t.reserve2,
        t.reserve3
"""

#: ``resultMap`` 的 78 条 ``<result>``（键 = 列名）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "deviceip",
    "tailcapturetimeunix",
    "tailcapturetime",
    "extendattribute",
    "smallsideimagewidth",
    "axletype",
    "smallsideimageheight",
    "platecolorcode",
    "platecolor",
    "cover",
    "averageauthoritative",
    "headlanecode",
    "specialvehicle",
    "carlength",
    "resulttype",
    "carhight",
    "carmodelscode",
    "carmodels",
    "laneposition",
    "firstauthoritative",
    "tailplateimageheight",
    "axlecount",
    "plateimagewidth",
    "specialclass",
    "tailplatenumber",
    "tailimage",
    "sidecapturetimeunix",
    "sidecapturetime",
    "sidelanecode",
    "wheelbase",
    "attached",
    "wheelcount",
    "guid",
    "sideimagewidth",
    "plateimageheight",
    "datasource",
    "carclass",
    "gantryid",
    "smallsideimage",
    "headimageheight",
    "sidescenetypecode",
    "sidescenetype",
    "tailimagewidth",
    "envstate",
    "headscenetypecode",
    "headscenetype",
    "sidedrivingdirectioncode",
    "sidedrivingdirection",
    "sideimageheight",
    "speed",
    "tailplateimage",
    "headdrivingdirectioncode",
    "headdrivingdirection",
    "cartype",
    "plateimage",
    "changelane",
    "sideimage",
    "tailplateposition",
    "headimagewidth",
    "headimage",
    "carweight",
    "tailimageheight",
    "devicecode",
    "platenumber",
    "tailplatecolorcode",
    "tailplatecolor",
    "uploadtimeunix",
    "uploadtime",
    "impostoraxlecount",
    "taillanecode",
    "siteid",
    "headcapturetimeunix",
    "headcapturetime",
    "plateposition",
    "tailplateimagewidth",
    "loadtime",
    "gradelevel",
    "datauuid",
    "reserve1",
    "reserve2",
    "reserve3",
)

#: ``<if>`` 列表，顺序与 XML 一致（82 条）。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id", null_only=True),
    If("deviceip", "deviceip"),
    If("tailcapturetimeunix", "tailcapturetimeunix", null_only=True),
    If("tailcapturetime", "tailcapturetime", null_only=True),
    If("extendattribute", "extendattribute"),
    If("smallsideimagewidth", "smallsideimagewidth", null_only=True),
    If("axletype", "axletype"),
    If("smallsideimageheight", "smallsideimageheight", null_only=True),
    If("platecolorcode", "platecolorcode", null_only=True),
    If("platecolor", "platecolor"),
    If("cover", "cover"),
    If("averageauthoritative", "averageauthoritative", null_only=True),
    If("headlanecode", "headlanecode", null_only=True),
    If("specialvehicle", "specialvehicle", null_only=True),
    If("carlength", "carlength", null_only=True),
    If("resulttype", "resulttype"),
    If("carhight", "carhight", null_only=True),
    If("carmodelscode", "carmodelscode", null_only=True),
    If("carmodels", "carmodels"),
    If("laneposition", "laneposition"),
    If("firstauthoritative", "firstauthoritative", null_only=True),
    If("tailplateimageheight", "tailplateimageheight", null_only=True),
    If("axlecount", "axlecount", null_only=True),
    If("plateimagewidth", "plateimagewidth", null_only=True),
    If("specialclass", "specialclass"),
    If("tailplatenumber", "tailplatenumber"),
    If("tailimage", "tailimage"),
    If("sidecapturetimeunix", "sidecapturetimeunix", null_only=True),
    If("sidecapturetime", "sidecapturetime", null_only=True),
    If("sidelanecode", "sidelanecode", null_only=True),
    If("wheelbase", "wheelbase", null_only=True),
    If("attached", "attached"),
    If("wheelcount", "wheelcount", null_only=True),
    If("guid", "guid"),
    If("sideimagewidth", "sideimagewidth", null_only=True),
    If("plateimageheight", "plateimageheight", null_only=True),
    If("datasource", "datasource"),
    If("carclass", "carclass"),
    If("gantryid", "gantryid"),
    If("smallsideimage", "smallsideimage"),
    If("headimageheight", "headimageheight", null_only=True),
    If("sidescenetypecode", "sidescenetypecode", null_only=True),
    If("sidescenetype", "sidescenetype"),
    If("tailimagewidth", "tailimagewidth", null_only=True),
    If("envstate", "envstate"),
    If("headscenetypecode", "headscenetypecode", null_only=True),
    If("headscenetype", "headscenetype"),
    If("sidedrivingdirectioncode", "sidedrivingdirectioncode", null_only=True),
    If("sidedrivingdirection", "sidedrivingdirection"),
    If("sideimageheight", "sideimageheight", null_only=True),
    If("speed", "speed"),
    If("tailplateimage", "tailplateimage"),
    If("headdrivingdirectioncode", "headdrivingdirectioncode", null_only=True),
    If("headdrivingdirection", "headdrivingdirection"),
    If("cartype", "cartype"),
    If("plateimage", "plateimage"),
    If("changelane", "changelane"),
    If("sideimage", "sideimage"),
    If("tailplateposition", "tailplateposition"),
    If("headimagewidth", "headimagewidth", null_only=True),
    If("headimage", "headimage"),
    If("carweight", "carweight", null_only=True),
    If("tailimageheight", "tailimageheight", null_only=True),
    If("devicecode", "devicecode"),
    If("platenumber", "platenumber"),
    If("tailplatecolorcode", "tailplatecolorcode", null_only=True),
    If("tailplatecolor", "tailplatecolor"),
    If("uploadtimeunix", "uploadtimeunix", null_only=True),
    If("uploadtime", "uploadtime", null_only=True),
    If("impostoraxlecount", "impostoraxlecount", null_only=True),
    If("taillanecode", "taillanecode", null_only=True),
    If("siteid", "siteid", null_only=True),
    If("headcapturetimeunix", "headcapturetimeunix", null_only=True),
    If("headcapturetime", "headcapturetime", null_only=True),
    If("plateposition", "plateposition"),
    If("tailplateimagewidth", "tailplateimagewidth", null_only=True),
    If("loadtime", "loadtime", null_only=True),
    If("gradelevel", "gradelevel", null_only=True),
    If("datauuid", "datauuid"),
    If("reserve1", "reserve1"),
    If("reserve2", "reserve2"),
    If("reserve3", "reserve3"),
)


class OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper(OdsListMapper):
    """Java: ``interface OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper``."""

    table = "ods_rt_szdn_snapshot_flow_provcapture_addcode"
    select_vo = SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_PROVCAPTURE_ADDCODE_VO
    entity_cls = OdsRtSzdnSnapshotFlowProvcaptureAddcode
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: XML 末尾的 ``order by t.big_id``。
    order_by: Optional[str] = "big_id"
    #: ``where t.big_id = #{bigId}``.
    detail_column = "big_id"


__all__ = [
    "CONDITIONS",
    "OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper",
    "RESULT_COLUMNS",
    "SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_PROVCAPTURE_ADDCODE_VO",
]
