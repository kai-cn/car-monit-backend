"""收费站抓拍 ``ods_rt_szdn_snapshot_flow_stationcapture_addcode``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowStationcaptureAddcode.java

类型速查（XML 的 ``<if>`` 判据与之一一对应）
--------------------------------------------
* ``Long``： ``bigId`` / ``orgcode`` / ``siteid`` / ``snapshottimeunix`` / ``receivedtimeunix``
* ``Integer``： ``laneid`` / ``platecolorcode`` / ``platetypecode`` / ``plateconfidence`` /
  ``carcolorcode`` / ``cartypecode`` / ``cardirectioncode`` / ``gradelevel``
* ``Date``（``@JsonFormat("yyyy-MM-dd")``）： ``snapshottime`` / ``receivedtime`` / ``loadtime``
* 其余 ``String``；``tollname`` 与 ``maindirectionname`` 的列表条件是 **like**。

``maindirection`` / ``maindirectionname`` / ``reserve3`` 声明在类尾、**没有** ``@Excel``
（``datauuid`` 也没有），所以它们不出现在导出里 —— 但**出现在 JSON 里**。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate
from app.common.core.domain.domain_model import DomainModel


class OdsRtSzdnSnapshotFlowStationcaptureAddcode(DomainModel):
    """Java: ``public class OdsRtSzdnSnapshotFlowStationcaptureAddcode implements Custom``."""

    #: 主键. Java: ``@TableId(value = "bigId", type = IdType.ASSIGN_UUID)``
    big_id: Optional[int] = None

    #: 数据类型.
    datasource: Optional[str] = None

    #: 设备类型.
    cameratype: Optional[str] = None

    #: 设备编号.
    deviceid: Optional[str] = None

    #: 设备IP.
    deviceip: Optional[str] = None

    #: 收费站编码.
    tollcode: Optional[str] = None

    #: 收费站名称（列表条件是 **like**）.
    tollname: Optional[str] = None

    #: 组织机构编码.
    orgcode: Optional[int] = None

    #: 站点ID.
    siteid: Optional[int] = None

    #: 车道编号.
    laneid: Optional[int] = None

    #: 抓拍时间Unix格式.
    snapshottimeunix: Optional[int] = None

    #: 抓拍时间 ``@JsonFormat("yyyy-MM-dd")``.
    snapshottime: OdsDate = None

    #: 接收时间Unix格式.
    receivedtimeunix: Optional[int] = None

    #: 接收时间 ``@JsonFormat("yyyy-MM-dd")``.
    receivedtime: OdsDate = None

    #: 车牌号.
    platenumber: Optional[str] = None

    #: 车牌颜色编码.
    platecolorcode: Optional[int] = None

    #: 车牌颜色.
    platecolor: Optional[str] = None

    #: 车牌类型编码.
    platetypecode: Optional[int] = None

    #: 车牌类型.
    platetype: Optional[str] = None

    #: 车牌置信度.
    plateconfidence: Optional[int] = None

    #: 车辆品牌.
    carbrand: Optional[str] = None

    #: 车辆颜色编码.
    carcolorcode: Optional[int] = None

    #: 车辆颜色.
    carcolor: Optional[str] = None

    #: 车辆类型编码.
    cartypecode: Optional[int] = None

    #: 车辆类型.
    cartype: Optional[str] = None

    #: 行驶方向编码.
    cardirectioncode: Optional[int] = None

    #: 行驶方向.
    cardirection: Optional[str] = None

    #: 图片路径.
    snappicturepath: Optional[str] = None

    #: 加载时间 ``@JsonFormat("yyyy-MM-dd")``.
    loadtime: OdsDate = None

    #: 分类分级.
    gradelevel: Optional[int] = None

    #: 数据唯一标识（无 ``@Excel``）.
    datauuid: Optional[str] = None

    #: 主方向（无 ``@Excel``）.
    maindirection: Optional[str] = None

    #: 主方向名称（列表条件是 **like**，无 ``@Excel``）.
    maindirectionname: Optional[str] = None

    #: 预留字段（无 ``@Excel``）.
    reserve3: Optional[str] = None


__all__ = ["OdsRtSzdnSnapshotFlowStationcaptureAddcode"]
