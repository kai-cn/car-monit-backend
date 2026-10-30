"""省界抓拍 ``ods_rt_szdn_snapshot_flow_provcapture_addcode``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowProvcaptureAddcode.java

``base`` 包里最宽的一张表（78 个字段）。字段名全部是**小写无下划线**，所以
Python 属性名与数据库列名完全一致 —— 这也是它不需要任何别名映射的原因。

类型速查
--------
* ``Date``（``@JsonFormat("yyyy-MM-dd")``）： ``sidecapturetime`` / ``uploadtime`` /
  ``headcapturetime``
* ``Date``（**没有** ``@JsonFormat``，输出 ISO 文本）： ``tailcapturetime`` / ``loadtime``
* ``Long``： ``bigId`` / ``tailcapturetimeunix`` / ``sidecapturetimeunix`` /
  ``uploadtimeunix`` / ``headcapturetimeunix``
* 其余整数都是 ``Integer``；``speed`` 是 **String**（不是数字！），``plateposition`` /
  ``extendattribute`` / ``axletype`` / ``cover`` / ``envstate`` 也都是 String。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate, OdsEpochDate
from app.common.core.domain.domain_model import DomainModel


class OdsRtSzdnSnapshotFlowProvcaptureAddcode(DomainModel):
    """Java: ``public class OdsRtSzdnSnapshotFlowProvcaptureAddcode implements Custom``."""

    big_id: Optional[int] = None
    deviceip: Optional[str] = None
    tailcapturetimeunix: Optional[int] = None
    #: Java 没有 ``@JsonFormat`` -> ISO 文本，且时间部分**不**截断.
    tailcapturetime: OdsEpochDate = None
    extendattribute: Optional[str] = None
    smallsideimagewidth: Optional[int] = None
    axletype: Optional[str] = None
    smallsideimageheight: Optional[int] = None
    platecolorcode: Optional[int] = None
    platecolor: Optional[str] = None
    cover: Optional[str] = None
    averageauthoritative: Optional[int] = None
    headlanecode: Optional[int] = None
    specialvehicle: Optional[int] = None
    carlength: Optional[int] = None
    resulttype: Optional[str] = None
    carhight: Optional[int] = None
    carmodelscode: Optional[int] = None
    carmodels: Optional[str] = None
    laneposition: Optional[str] = None
    firstauthoritative: Optional[int] = None
    tailplateimageheight: Optional[int] = None
    axlecount: Optional[int] = None
    plateimagewidth: Optional[int] = None
    specialclass: Optional[str] = None
    tailplatenumber: Optional[str] = None
    tailimage: Optional[str] = None
    sidecapturetimeunix: Optional[int] = None
    sidecapturetime: OdsDate = None
    sidelanecode: Optional[int] = None
    wheelbase: Optional[int] = None
    attached: Optional[str] = None
    wheelcount: Optional[int] = None
    guid: Optional[str] = None
    sideimagewidth: Optional[int] = None
    plateimageheight: Optional[int] = None
    datasource: Optional[str] = None
    carclass: Optional[str] = None
    gantryid: Optional[str] = None
    smallsideimage: Optional[str] = None
    headimageheight: Optional[int] = None
    sidescenetypecode: Optional[int] = None
    sidescenetype: Optional[str] = None
    tailimagewidth: Optional[int] = None
    envstate: Optional[str] = None
    headscenetypecode: Optional[int] = None
    headscenetype: Optional[str] = None
    sidedrivingdirectioncode: Optional[int] = None
    sidedrivingdirection: Optional[str] = None
    sideimageheight: Optional[int] = None
    #: 车速 —— **String**（XML 判据是 ``!= null and != ''``）。
    speed: Optional[str] = None
    tailplateimage: Optional[str] = None
    headdrivingdirectioncode: Optional[int] = None
    headdrivingdirection: Optional[str] = None
    cartype: Optional[str] = None
    plateimage: Optional[str] = None
    changelane: Optional[str] = None
    sideimage: Optional[str] = None
    tailplateposition: Optional[str] = None
    headimagewidth: Optional[int] = None
    headimage: Optional[str] = None
    carweight: Optional[int] = None
    tailimageheight: Optional[int] = None
    devicecode: Optional[str] = None
    platenumber: Optional[str] = None
    tailplatecolorcode: Optional[int] = None
    tailplatecolor: Optional[str] = None
    uploadtimeunix: Optional[int] = None
    uploadtime: OdsDate = None
    impostoraxlecount: Optional[int] = None
    taillanecode: Optional[int] = None
    siteid: Optional[int] = None
    headcapturetimeunix: Optional[int] = None
    headcapturetime: OdsDate = None
    plateposition: Optional[str] = None
    tailplateimagewidth: Optional[int] = None
    #: Java 没有 ``@JsonFormat`` -> ISO 文本，且时间部分**不**截断.
    loadtime: OdsEpochDate = None
    gradelevel: Optional[int] = None
    datauuid: Optional[str] = None
    reserve1: Optional[str] = None
    reserve2: Optional[str] = None
    reserve3: Optional[str] = None


__all__ = ["OdsRtSzdnSnapshotFlowProvcaptureAddcode"]
