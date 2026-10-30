"""轨迹点 VO（``TrailBo``）—— 轨迹 JSON 里的单个抓拍/流水点.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailBo.java

两个容易踩的坑，都是照着 Java 原文抄下来的结果
------------------------------------------------
1. **包级私有字段照样会被序列化。** Java 里 ``borderWeighingCaptureBO`` 等 9 个
   嵌套对象没有写 ``private``，但类上是 Lombok ``@Data`` —— ``@Data`` 会给**所有**
   非 static 字段生成 ``public`` 的 getter/setter，访问修饰符不影响它。Jackson 只看
   有没有 getter，于是这 9 个字段在响应体里是**存在的**（值为 ``null``）。
   早先的版本误以为它们不参与序列化而加了 ``exclude=True``，实测
   ``/manager/cartrackinfo/listByCarByTime`` 因此少了 9 个键 × 每条轨迹点。

2. **``pointJosn`` / ``locationJosn`` 是 Java 原文的拼写（``Josn`` 不是 ``Json``）。**
   前端按这个名字取值，所以别名必须逐字照抄；Python 属性名保留可读的
   ``point_json`` / ``location_json``。

3. **缩写的 ``BO`` 后缀不会被 ``to_camel`` 还原。** ``borderWeighingCaptureBO`` 之类的
   名字最后一个词是大写缩写，``snake -> camel`` 只能拼出 ``...CaptureBo``。这 5 个
   字段必须显式写 ``alias``，否则响应体里会多出 5 个 Java 没有的键、同时丢掉 5 个
   Java 有的键（``/manager/cartrackinfo/listByCarByTime`` 实测如此）。

嵌套对象的类型在 Java 里是具体实体（``OdsSzdnGantryIp`` 等），Python 侧用 ``Any``
承载：这些值本身来自库里 ``track_josn`` 保存的 JSON（本来就已经是 Java 属性名），
原样透传比套一层可能字段不全的模型更安全。
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from app.common.core.domain.domain_model import DomainModel


class TrailBo(DomainModel):
    """Java: ``com.ruoyi.base.domain.TrailBo``."""

    #: 流水唯一标识符
    point_uuid: Optional[str] = None
    #: 流水来源类型：BorderWeighingCapture / GantryCapture / ProvCapture /
    #: ServiceAreaCapture / StationCapture
    state_type: Optional[str] = None
    #: 是否有值 0 否 1 是
    point_flag: Optional[str] = None
    #: pointUuid 的 json 对象（Java 原拼写 ``pointJosn``）
    point_json: Optional[str] = Field(default=None, alias="pointJosn")

    # -------------------------------------------------- 嵌套流水对象（Java 包级私有）
    # 按 Java 声明顺序排在 ``pointJosn`` 之后、``captureTime`` 之前。

    #: 省界称重
    border_weighing_capture_bo: Optional[Any] = Field(
        default=None, alias="borderWeighingCaptureBO"
    )
    #: 门架抓拍
    gantry_capture_bo: Optional[Any] = Field(default=None, alias="gantryCaptureBO")
    #: 省界抓拍
    prov_capture_bo: Optional[Any] = Field(default=None, alias="provCaptureBO")
    #: 收费站抓拍
    station_capture: Optional[Any] = None
    #: 卡口流水
    fee_record: Optional[Any] = None
    #: 收费站入口流水
    fee_station_enter: Optional[Any] = None
    #: 收费站出口流水
    fee_station_exit: Optional[Any] = None

    #: 抓拍流水发生时间
    capture_time: Optional[str] = None
    #: 进出方向（true 进入 / false 驶出 / null 非进出类）
    direction_in: Optional[bool] = None
    #: 设备 IP 地址
    location_code: Optional[str] = None
    #: 位置是否有值
    location_flag: Optional[str] = None
    #: ip 类型：gantryip / stationip
    ip_type: Optional[str] = None
    #: 位置 json 对象（Java 原拼写 ``locationJosn``）
    location_json: Optional[str] = Field(default=None, alias="locationJosn")

    #: 门架 IP
    gantry_ip_bo: Optional[Any] = Field(default=None, alias="gantryIpBO")
    #: 收费站 IP
    station_ip_bo: Optional[Any] = Field(default=None, alias="stationIpBO")

    #: 设备编码
    dev_code: Optional[str] = None
    #: 设备名称
    dev_name: Optional[str] = None
    #: 抓拍图片
    images_arry: Optional[str] = None
    #: 经度
    lon: Optional[float] = None
    #: 维度（原文就是"维度"）
    lat: Optional[float] = None
    #: 路线编号
    road_code: Optional[str] = None
    #: 路段编号
    section_code: Optional[str] = None
    #: 方向（0 上行 / 1 下行）
    direction: Optional[str] = None
    #: 桩号
    pileno: Optional[str] = None
    #: 上一个抓拍时间
    pre_capture_time: Optional[str] = None
    #: 数量
    count_num: Optional[int] = None
    #: 桩号（数值）
    pileno_dec: Optional[float] = None
    #: 是否查询：1 查询
    is_query: Optional[str] = None


__all__ = ["TrailBo"]
