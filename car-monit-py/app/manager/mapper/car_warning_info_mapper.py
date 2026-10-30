"""预警车辆 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarWarningInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml

标准 ``manager`` 模板：37 条 ``<if>`` + ``order by t.gantry_time desc,t.id``。

与其它模块不同的三处
--------------------
1. ``from_clause`` 多一个 ``left join car_info c on t.car_id = c.id``；两个条件直接
   落在 ``c.`` 上（``escapedType`` / ``plateColor``）。
2. 4 条 ``<if>`` 无法用 :class:`If` 表达（``flag`` 字符串等值、``<foreach>`` 多值
   OR），由 :meth:`CarWarningInfoMapper.fragment_before` 按 XML 相对顺序插入。
3. 详情语句多投影 ``t.track_josn`` 与 3 个别名列。**注意** ``escaped_type`` /
   ``escaped_amount`` / ``plate_color`` 不在 ``resultMap`` 里，所以即使查出来了，
   MyBatis 也不会把它们放进实体 —— 与 ``CarInfo.createInfo`` 同一个性质，照抄。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If, map_row
from app.config.database import session_scope
from app.manager.domain.car_warning_info import CarWarningInfo
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarWarningInfoVo">``
SELECT_CAR_WARNING_INFO_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.gantry_station_id,
        t.gantryt_station,
        t.gantry_time,
        t.file_ids,
        t.next_pass_time,
        t.next_pass_type,
        t.next_pass_address,
        t.next_pass_longitude,
        t.next_pass_latitude,
        t.road_code,
        t.road_name,
        t.section_code,
        t.section_name,
        t.back_col1,
        t.back_col2,
        t.status,
        t.sort,
        t.eps_id,
        t.del_flag,
        t.create_by,
        t.create_time,
        t.update_by,
        t.update_time,
        t.tenant_id,
        t.track_id,
        t.track_names
"""

#: ``resultMap`` 的 36 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "in_station_id",
    "in_station",
    "in_time",
    "gantry_station_id",
    "gantryt_station",
    "gantry_time",
    "file_ids",
    "next_pass_time",
    "next_pass_type",
    "next_pass_address",
    "next_pass_longitude",
    "next_pass_latitude",
    "road_code",
    "road_name",
    "section_code",
    "section_name",
    "track_id",
    "track_josn",
    "track_names",
    "back_col1",
    "back_col2",
    "status",
    "sort",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``selectCarWarningInfoList`` 的 41 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no", like=True),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("gantry_station_id", "gantry_station_id"),
    If("gantryt_station", "gantryt_station", like=True),
    If("gantry_time", "gantry_time", null_only=True),
    If("file_ids", "file_ids"),
    If("next_pass_time", "next_pass_time", null_only=True),
    If("next_pass_type", "next_pass_type"),
    If("next_pass_address", "next_pass_address"),
    If("next_pass_longitude", "next_pass_longitude"),
    If("next_pass_latitude", "next_pass_latitude"),
    If("road_code", "track_names", like=True),
    If("road_name", "road_name", like=True),
    If("section_code", "track_names", like=True),
    If("section_name", "section_name", like=True),
    If("track_id", "track_id"),
    If("track_josn", "track_josn"),
    If("track_names", "track_names", like=True),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If(
        "apply_time1",
        "in_time",
        template="and t.in_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time2",
        "in_time",
        template="and t.in_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If("car_no_query", "car_no", like=True),
    If(
        "escaped_type",
        "c.escaped_type",
        template="and c.escaped_type like concat('%', {p}, '%')",
    ),
    If(
        "plate_color",
        "c.plate_color",
        template="and c.plate_color = {p}",
    ),
)


class CarWarningInfoMapper(ManagerListMapper):
    """Java: ``interface CarWarningInfoMapper extends BaseMapper<CarWarningInfo>``."""

    table = "car_warning_info"
    select_vo = SELECT_CAR_WARNING_INFO_VO
    entity_cls = CarWarningInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    from_clause = "car_warning_info t left join car_info c on t.car_id = c.id"
    order_by = "t.gantry_time desc,t.id"
    # Java: ``<include refid="selectCarWarningInfoVo"/>,t.track_josn, c.escaped_type escapedType, ...``
    detail_suffix = (
        ",t.track_josn, c.escaped_type escapedType, c.escaped_amount escapedAmount,"
        "c.plate_color plateColor"
    )

    def fragment_before(
        self, anchor: Optional[str], query: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """XML 里 4 条无法用 :class:`If` 表达的 ``<if>``。

        1. ``<if test="flag != null and flag == 'curDate'">`` —— 判据是 ``flag``
           的**字符串等值**，绑定参数是 ``flagTime``：

            .. code-block:: sql

                and c.status = '1' and t.back_col1 = :flag_time

        2. ``<if test="flag != null and flag == 'histhory'">``（原文就是这么拼的）:

            .. code-block:: sql

                and t.back_col1 != :flag_time

           这两条夹在 ``carNoQuery`` 与 ``escapedType`` 之间，所以挂在
           ``escaped_type`` 的插入点上。

        3. ``sectionCodeList`` / ``codeList`` —— ``<foreach open="("
           separator="or" close=")">`` 生成的多值 OR（**不是** ``in``），
           空列表整条跳过；它们在 ``plateColor`` 之后，用 ``anchor=None`` 追加。
        """
        if anchor == "escaped_type":
            flag = query.flag
            if flag == "curDate":
                return "and c.status = '1' and t.back_col1 = :flag_time", {
                    "flag_time": query.flag_time
                }
            if flag == "histhory":
                return "and t.back_col1 != :flag_time", {"flag_time": query.flag_time}
            return "", {}

        if anchor is None:
            fragments: List[str] = []
            params: Dict[str, Any] = {}
            for name in ("section_code_list", "code_list"):
                values = list(getattr(query, name, None) or ())
                if not values:
                    continue
                placeholders = []
                for index, value in enumerate(values):
                    key = f"{name}_{index}"
                    placeholders.append(f":{key}")
                    params[key] = value
                joined = " or ".join(
                    f"t.track_names like concat('%', {holder}, '%')"
                    for holder in placeholders
                )
                fragments.append(f"and ({joined})")
            return " ".join(fragments), params

        return "", {}

    # Java: List<CarWarningInfo> selectCarWarningInfoListLimit100(CarWarningInfo q)
    def select_car_warning_info_list_limit100(self, query: Any) -> List[Any]:
        """大屏告警列表 —— 固定只查**在线**车辆当前日期的预警（无 limit，名字不实）。

        ``inner join`` 且带 ``c.del_flag = '0' and c.status = '1'``；
        虽然 SELECT 里取了 ``escapedType`` / ``escapedAmount``，但 ``resultMap``
        没有这两个属性，所以返回的实体里它们恒为 ``None``（照抄）。
        """
        sql = (
            f"SELECT {self.select_vo}, c.escaped_type escapedType, "
            "c.escaped_amount escapedAmount FROM car_warning_info t "
            "inner join car_info c on c.del_flag = '0' and t.car_id = c.id "
            "and c.status = '1' "
            "WHERE t.del_flag = '0' and t.back_col1 = :track_id "
            f"order by {self.order_by}"
        )
        with session_scope() as session:
            rows = session.execute(
                text(sql), {"track_id": getattr(query, "track_id", None)}
            ).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    # Java: int deleteCarWarningInfoByUUid(@Param("idList") List<String> idList)
    def delete_car_warning_info_by_uuid(self, id_list: Any) -> int:
        """**物理删除**（不是逻辑删除）—— ``delete from ... where track_id in (..)``."""
        values = list(id_list or ())
        if not values:
            return 0
        placeholders = []
        params: Dict[str, Any] = {}
        for index, value in enumerate(values):
            key = f"track_id_{index}"
            placeholders.append(f":{key}")
            params[key] = value
        sql = (
            "delete from car_warning_info where track_id in ("
            + ",".join(placeholders)
            + ")"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return int(result.rowcount or 0)


__all__ = [
    "CarWarningInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_WARNING_INFO_VO",
]
