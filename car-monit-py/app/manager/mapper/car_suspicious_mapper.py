"""可疑车辆 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarSuspiciousMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml

与其它 ``manager`` XML 的差异
-----------------------------
1. 列表排序是 ``order by t.out_time desc,t.id``（不是固定的 ``create_time``）；
2. ``selectCarSuspiciousVo`` **不含** ``track_josn`` / ``track_names``，只有详情
   语句额外拼 ``,t.track_josn``；
3. ``selectCarSuspiciousListLimit10`` 用的是 ``resultType``（自动映射）而不是
   ``resultMap``，所以只有 ``car_no`` / ``car_type`` / ``escaped_type`` /
   ``section_name`` 四列有值；
4. 历史表 ``car_suspicious_back`` 的列表排序是 ``order by t.id``（升序）；
5. ``deleteChangeCarSuspicious`` 是**物理删除**，不是逻辑删除。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If, build_conditions, map_row
from app.manager.domain.car_suspicious import CarSuspicious
from app.manager.mapper.manager_mapper import ManagerListMapper
from app.config.database import session_scope

#: Java: ``<sql id="selectCarSuspiciousVo">``
SELECT_CAR_SUSPICIOUS_VO = """
        t.id,
        t.plate_color,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.pass_type,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.out_station_id,
        t.out_station,
        t.out_time,
        t.gantry_station_id,
        t.gantryt_station,
        t.gantry_time,
        t.file_ids,
        t.out_gantry_station_id,
        t.out_gantryt_station,
        t.out_gantry_time,
        t.out_file_ids,
        t.escaped_type,
        t.escaped_type_name,
        t.escaped_num,
        t.is_except,
        t.except_remark,
        t.except_file_ids,
        t.check_status,
        t.org_id,
        t.org_name,
        t.is_white,
        t.white_remark,
        t.white_file_ids,
        t.road_code,
        t.road_name,
        t.section_code,
        t.section_name,
        t.track_id,
        t.back_col1,
        t.back_col2,
        t.remark,
        t.status,
        t.create_time
"""

#: ``resultMap`` 的 52 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "plate_color",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "pass_type",
    "in_station_id",
    "in_station",
    "in_time",
    "out_station_id",
    "out_station",
    "out_time",
    "gantry_station_id",
    "gantryt_station",
    "gantry_time",
    "file_ids",
    "out_gantry_station_id",
    "out_gantryt_station",
    "out_gantry_time",
    "out_file_ids",
    "escaped_type",
    "escaped_type_name",
    "escaped_num",
    "is_except",
    "except_remark",
    "except_file_ids",
    "check_status",
    "org_id",
    "org_name",
    "is_white",
    "white_remark",
    "white_file_ids",
    "road_code",
    "road_name",
    "section_code",
    "section_name",
    "track_id",
    "track_josn",
    "track_names",
    "back_col1",
    "back_col2",
    "remark",
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

#: ``selectCarSuspiciousList`` 的 50 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("plate_color", "plate_color"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("pass_type", "pass_type"),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station"),
    If("out_time", "out_time", null_only=True),
    If("gantry_station_id", "gantry_station_id"),
    If("gantryt_station", "gantryt_station"),
    If("gantry_time", "gantry_time", null_only=True),
    If("file_ids", "file_ids"),
    If("out_gantry_station_id", "out_gantry_station_id"),
    If("out_gantryt_station", "out_gantryt_station"),
    If("out_gantry_time", "out_gantry_time", null_only=True),
    If("out_file_ids", "out_file_ids"),
    If("escaped_type", "escaped_type"),
    If("escaped_type_name", "escaped_type_name", like=True),
    If("escaped_num", "escaped_num", null_only=True),
    If("is_except", "is_except"),
    If("except_remark", "except_remark"),
    If("except_file_ids", "except_file_ids"),
    If("check_status", "check_status"),
    If("org_id", "org_id"),
    If("org_name", "org_name", like=True),
    If("is_white", "is_white"),
    If("white_remark", "white_remark"),
    If("white_file_ids", "white_file_ids"),
    If("road_code", "road_code"),
    If("road_name", "road_name", like=True),
    # 路段编码 / 路段名称 / 查询范围三者都打在 track_names 上
    If("section_code", "track_names", like=True),
    If("section_name", "track_names", like=True),
    If("track_names", "track_names", like=True),
    If("track_id", "track_id"),
    If("track_josn", "track_josn"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If("car_no_query", "car_no", like=True),
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
)

#: ``selectCarSuspiciousListLimit10`` —— ``resultType``，只映射 4 个字段。
LIMIT10_COLUMNS: Tuple[str, ...] = ("car_no", "car_type", "escaped_type", "section_name")


class CarSuspiciousMapper(ManagerListMapper):
    """Java: ``interface CarSuspiciousMapper extends BaseMapper<CarSuspicious>``."""

    table = "car_suspicious"
    select_vo = SELECT_CAR_SUSPICIOUS_VO
    entity_cls = CarSuspicious
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.out_time desc,t.id"
    detail_suffix = ",t.track_josn"

    # ------------------------------------------------------------ 历史表（back）

    # Java: List<CarSuspicious> selectCarSuspiciousListHistroy(CarSuspicious x)
    def select_list_history(self, query: Any) -> List[Any]:
        """历史列表：``FROM car_suspicious_back t`` + ``order by t.id``（升序）。"""
        sql = f"SELECT {self.select_vo} FROM car_suspicious_back t WHERE t.del_flag = '0'"
        fragments, params = build_conditions(query, self.conditions)
        for fragment in fragments:
            sql = f"{sql} {fragment}"
        sql = f"{sql} order by t.id"

        from app.common.core.page.page_helper import PageList, select_page, take_page

        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(
                session, f"select count(0) from ({sql}) table_count", sql, params, page
            )
        mapped = [map_row(self.entity_cls, self.result_columns, row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: CarSuspicious selectCarSuspiciousHistoryById(String id)
    def select_history_by_id(self, entity_id: Any) -> Optional[Any]:
        sql = (
            f"select {self.select_vo}{self.detail_suffix} from car_suspicious_back t "
            f"where t.id = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        return None if row is None else map_row(self.entity_cls, self.result_columns, row)

    # ------------------------------------------------------------ 大屏 top10

    # Java: List<CarSuspicious> selectCarSuspiciousListLimit10()
    def select_list_limit10(self) -> List[Any]:
        """大屏前 10 条 —— ``resultType`` 自动映射，只有 4 列有值。"""
        sql = (
            "SELECT t.car_no,t.car_type, t.escaped_type, t.section_name "
            "FROM car_suspicious t "
            "WHERE t.del_flag = '0' and is_except = '1' and check_status = '1' "
            "order by t.create_time desc,t.id limit 10"
        )
        with session_scope() as session:
            rows = session.execute(text(sql)).all()
        return [map_row(self.entity_cls, LIMIT10_COLUMNS, row) for row in rows]

    # ------------------------------------------------------------ 迁移（保留一个月）

    # Java: insert into car_suspicious_back select * from car_suspicious ...
    def change_car_suspicious(self, query_start_time: str) -> int:
        """把 ``in_time <= ?`` 的行搬到历史表（``insert ... select *``）。"""
        sql = (
            "insert into car_suspicious_back "
            "select * from car_suspicious t "
            "where t.del_flag = '0' "
            "and t.in_time <= STR_TO_DATE(:applyTime,'%Y-%m-%d %H:%i:%s')"
        )
        with session_scope() as session:
            result = session.execute(text(sql), {"applyTime": query_start_time})
            return result.rowcount or 0

    # Java: delete from car_suspicious where in_time <= ...
    def delete_change_car_suspicious(self, query_start_time: str) -> int:
        """**物理删除** —— XML 用的是 ``<delete>`` 而不是逻辑删除。"""
        sql = (
            "delete from car_suspicious "
            "where in_time <= STR_TO_DATE(:applyTime,'%Y-%m-%d %H:%i:%s')"
        )
        with session_scope() as session:
            result = session.execute(text(sql), {"applyTime": query_start_time})
            return result.rowcount or 0


def build_conditions_for(query: Any) -> Tuple[List[str], Dict[str, Any]]:
    """Test helper: 直接拿列表 ``<if>`` 的片段与参数。"""
    return build_conditions(query, CONDITIONS)


__all__ = [
    "CarSuspiciousMapper",
    "CONDITIONS",
    "LIMIT10_COLUMNS",
    "RESULT_COLUMNS",
    "SELECT_CAR_SUSPICIOUS_VO",
    "build_conditions_for",
]
