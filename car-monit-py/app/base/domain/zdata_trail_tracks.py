"""轨迹数据 ``zdata_trail_tracks``.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailTracks.java

三组字段，别混在一起看
----------------------
1. **持久字段**（``uuid`` → ``endLat``）：由 ``resultMap`` 显式映射，出现在 SQL 里。
2. **``@TableField(exist = false)`` 瞬态字段**：**不出现在任何 SQL 里**，但
   **会出现在 JSON 里**（值为 ``null``）。它们分三种用途：

   * 查询条件：``carNo`` / ``applyTime1`` / ``applyTime2`` / ``isCylx``；
   * 查询结果回填：``startLonDec`` / ``stratLatDec`` / ``endLonDec`` /
     ``endLatDec`` / ``passCount``；
   * 纯前端展示：``plateColor`` / ``carType`` / ``escapedType`` ……

3. **投影里有、但没有任何映射的列**：``t.create_time``。``resultMap`` 没有
   ``createTime``，实体也没有这个字段，所以 MyBatis 读出来直接丢掉 ——
   ``result_columns`` 里**不要**加它。

拼写错误一律照留
----------------
``trackJosn``（应为 ``track_json``）、``stratLat``（应为 ``startLat``）、
``firtStationCode``（应为 ``firstStationCode``）都是从生成器带过来的，
**不要改**：数据库列名、resultMap、前端都在用这几个名字。

``passCount`` 为什么能被填上
---------------------------
``getCyly`` 的投影是 ``SELECT uuid, passCount FROM (...) a``，其中 ``passCount``
**不在** ``resultMap`` 里。MyBatis 的 ``autoMappingBehavior`` 默认是 ``PARTIAL``，
未被显式映射的列会按"列名 == 属性名"自动映射，于是 ``passCount`` 照样被写入。
（``mybatis-config.xml`` 里 ``mapUnderscoreToCamelCase`` 是**注释掉的**，所以
``create_time`` 不会被自动映射成 ``createTime`` —— 何况属性根本不存在。）

日期形态
--------
``enterTime`` / ``exitTime`` 带 ``@JsonFormat("yyyy-MM-dd HH:mm:ss")``，
输出**字符串**（不是 epoch 毫秒） —— 对应 :data:`~app.base.domain.ods_types.OdsDateTime`。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.ods_types import OdsDateTime
from app.common.core.domain.domain_model import DomainModel


class ZdataTrailTracks(DomainModel):
    """Java: ``public class ZdataTrailTracks implements Custom``."""

    # ------------------------------------------------------------------ 持久字段

    #: 主键. Java: ``@TableId(value = "uuid", type = IdType.ASSIGN_UUID)``
    uuid: Optional[str] = None

    #: 轨迹类型：0 = 不完整，1 = 完整.
    type: Optional[int] = None

    #: 轨迹点数量（``Long``，列名 ``point_count``）.
    point_count: Optional[int] = None

    #: 车牌唯一标识（可脱敏/加密存储）.
    plate_key: Optional[str] = None

    #: 进入时间 —— **月度分区键**，``@JsonFormat("yyyy-MM-dd HH:mm:ss")``.
    enter_time: OdsDateTime = None

    #: 离开时间 —— ``@JsonFormat("yyyy-MM-dd HH:mm:ss")``.
    exit_time: OdsDateTime = None

    #: 轨迹点集合（JSON 文本）.
    trail_points: Optional[str] = None

    #: 进入位置 code.
    enter_locationcode: Optional[str] = None

    #: 离开位置 code.
    exit_locationcode: Optional[str] = None

    #: 集合详情（生成器把 ``json`` 拼成了 ``josn``，照留）.
    track_josn: Optional[str] = None

    #: 入口车轴数（``Integer``，字段名全小写）.
    enaxlecount: Optional[int] = None

    #: 入口车道编号.
    entolllaneid: Optional[str] = None

    #: 入口收费站编号.
    entollstationid: Optional[str] = None

    #: 入口收费站名称.
    entollstationname: Optional[str] = None

    #: 入口车型分类（收费车型）.
    envehicleclass: Optional[str] = None

    #: 入口车辆编号.
    envehicleid: Optional[str] = None

    #: 入口车辆类型代码.
    envehicletype: Optional[str] = None

    #: 入口称重（``BigDecimal`` -> ``float``，见 :mod:`app.base.domain.ods_types`）.
    enweight: Optional[float] = None

    #: 出口车道编号.
    extolllaneid: Optional[str] = None

    #: 出口收费站编号.
    extollstationid: Optional[str] = None

    #: 出口收费站名称.
    extollstationname: Optional[str] = None

    #: 出口车型分类.
    exvehicleclass: Optional[str] = None

    #: 出口车辆编号.
    exvehicleid: Optional[str] = None

    #: 出口车辆类型代码.
    exvehicletype: Optional[str] = None

    #: 出口称重（``BigDecimal`` -> ``float``）.
    exweight: Optional[float] = None

    #: 入口收费站经度（**字符串**，列名 ``start_lon``）.
    start_lon: Optional[str] = None

    #: 入口收费站纬度（**字符串**，列名 ``strat_lat``，拼写照留）.
    strat_lat: Optional[str] = None

    #: 出口收费站经度（**字符串**）.
    end_lon: Optional[str] = None

    #: 出口收费站纬度（**字符串**）.
    end_lat: Optional[str] = None

    # --------------------------------------------------- 瞬态字段（exist = false）

    #: 瞬态：首个收费站编码.
    firt_station_code: Optional[str] = None

    #: 瞬态：首个收费站名称.
    firt_station_name: Optional[str] = None

    #: 瞬态：首个收费站时间.
    firt_station_time: Optional[str] = None

    #: 瞬态：车牌颜色（展示用）.
    plate_color: Optional[str] = None

    #: 瞬态：车辆类型（展示用）.
    car_type: Optional[str] = None

    #: 瞬态：**查询条件** —— ``and t.plate_key = #{carNo}``.
    car_no: Optional[str] = None

    #: 瞬态：车辆（展示用）.
    car_vehicle: Optional[str] = None

    #: 瞬态：车辆数（``Long``）.
    car_num: Optional[int] = None

    #: 瞬态：逃费类型.
    escaped_type: Optional[str] = None

    #: 瞬态：通行类型.
    pass_type: Optional[str] = None

    #: 瞬态：逃费类型备注.
    escaped_type_remark: Optional[str] = None

    #: 瞬态：**查询条件** —— 起始日期，``STR_TO_DATE(?, '%Y-%m-%d')``.
    apply_time1: Optional[str] = None

    #: 瞬态：**查询条件** —— 结束日期（**不含**当天，``< date_add(..., 1 day)``）.
    apply_time2: Optional[str] = None

    #: 瞬态：**查询条件** —— 是否常用路线（``"1"`` 时先走 ``getCyly``）.
    is_cylx: Optional[str] = None

    #: 瞬态：标记位.
    flag: Optional[str] = None

    #: 瞬态：入口经度（``BigDecimal`` -> ``float``）.
    start_lon_dec: Optional[float] = None

    #: 瞬态：入口纬度（``BigDecimal`` -> ``float``）.
    strat_lat_dec: Optional[float] = None

    #: 瞬态：出口经度（``BigDecimal`` -> ``float``）.
    end_lon_dec: Optional[float] = None

    #: 瞬态：出口纬度（``BigDecimal`` -> ``float``）.
    end_lat_dec: Optional[float] = None

    #: 瞬态：**查询条件** —— ``uuid in (...)`（``getHistoryTrail`` 用）.
    uuid_list: Optional[List[str]] = None

    #: 瞬态：通行次数（``getCyly`` 自动映射进来）.
    pass_count: Optional[int] = None

    #: 瞬态：逃费-通行费.
    escaped_tfcj: Optional[str] = None


__all__ = ["ZdataTrailTracks"]
