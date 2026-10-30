"""异常车辆流水 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarExceptRecordMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml

与其它 ``manager`` XML 的差异
-----------------------------
1. 列表带两个 ``left join``（``sys_user`` / ``sys_dept``）算 ``createInfo``，
   但 ``createInfo`` **不在** ``resultMap`` 里 —— 响应体恒为 ``null``；
2. ``applyTime2`` 在**基础列表**里打在 ``out_time`` 上（疑似笔误），而
   ``selectCarExceptRecordListNew`` 里打在 ``create_time`` 上；
3. ``selectCarExceptRecordListNew`` 排序是 ``order by t.dif_amount desc,t.id``；
4. ``deleteCarExceptRecordByCarId`` 是**物理删除**。

补缴状态相关的三个聚合语句（``exceptRecordCount`` / ``exceptRecordList`` /
``buildPCCarStatisticsVO*``）用 ``resultType`` 自动映射，列名必须能对上 VO。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If, build_conditions, map_row
from app.config.database import session_scope
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.pc_car_statistics_vo import PCCarStatisticsDetailVO
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarExceptRecordVo">``
SELECT_CAR_EXCEPT_RECORD_VO = """
        t.id,
        t.car_id,
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
        t.total_amount,
        t.charge_amount,
        t.dif_amount,
        t.escaped_type,
        t.remark,
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
        t.tenant_id
"""

#: ``resultMap`` 的 30 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
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
    "total_amount",
    "charge_amount",
    "dif_amount",
    "escaped_type",
    "remark",
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

#: ``selectCarExceptRecordList`` 的 30 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("pass_type", "pass_type"),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station", like=True),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station", like=True),
    If("out_time", "out_time", null_only=True),
    If("total_amount", "total_amount", null_only=True),
    If("charge_amount", "charge_amount", null_only=True),
    If("dif_amount", "dif_amount", null_only=True),
    If("escaped_type", "escaped_type"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    # 基础列表：applyTime2 打在 out_time 上（照抄这个笔误）
    If(
        "apply_time1",
        "in_time",
        template="and t.in_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time2",
        "out_time",
        template="and t.out_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time3",
        "out_time",
        template="and t.out_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time4",
        "out_time",
        template="and t.out_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If("car_no_query", "car_no", like=True),
    If(
        "except_ids",
        "find_in_set",
        template="and find_in_set(t.id,{p}) > 0",
    ),
)

#: ``selectCarExceptRecordListNew`` 的 31 条 ``<if>`` —— ``applyTime1/2`` 换到
#: ``create_time``（``%Y-%m-%d`` + ``date_add(..., interval 1 day)``），且多一个
#: ``orgId -> t.eps_id``。
CONDITIONS_NEW: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("pass_type", "pass_type"),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station", like=True),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station", like=True),
    If("out_time", "out_time", null_only=True),
    If("total_amount", "total_amount", null_only=True),
    If("charge_amount", "charge_amount", null_only=True),
    If("dif_amount", "dif_amount", null_only=True),
    If("escaped_type", "escaped_type"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If(
        "apply_time1",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
    If("org_id", "eps_id"),
    If(
        "apply_time3",
        "out_time",
        template="and t.out_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time4",
        "out_time",
        template="and t.out_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If("car_no_query", "car_no", like=True),
    If(
        "except_ids",
        "find_in_set",
        template="and find_in_set(t.id,{p}) > 0",
    ),
)

#: ``exceptRecordCount`` / ``exceptRecordList`` 的 ``resultMap`` 列（部分列被
#: 聚合表达式覆盖，未出现在 ``select`` 里的属性保持 ``null``）。
COUNT_COLUMNS: Tuple[str, ...] = ("car_no", "except_num", "except_amount")


class CarExceptRecordMapper(ManagerListMapper):
    """Java: ``interface CarExceptRecordMapper extends BaseMapper<CarExceptRecord>``."""

    table = "car_except_record"
    select_vo = SELECT_CAR_EXCEPT_RECORD_VO
    entity_cls = CarExceptRecord
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    select_suffix = ",concat(sd.dept_name, ' ', su.nick_name) createInfo"
    from_clause = (
        "car_except_record t "
        "left join sys_user su on su.user_id = t.create_by "
        "left join sys_dept sd on t.eps_id = sd.dept_id"
    )

    # -------------------------------------------------------- 新列表（按差额排序）

    # Java: List<CarExceptRecord> selectCarExceptRecordListNew(CarExceptRecord x)
    def select_list_new(self, query: Any) -> List[Any]:
        sql = f"SELECT {self.select_vo}{self.select_suffix} FROM {self.from_clause} WHERE t.del_flag = '0'"
        fragments, params = build_conditions(query, CONDITIONS_NEW)
        for fragment in fragments:
            sql = f"{sql} {fragment}"
        sql = f"{sql} order by t.dif_amount desc,t.id"

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

    # -------------------------------------------------------- 区间重复校验

    # Java: Integer isExitsTime(CarExceptRecord x)
    def is_exists_time(self, query: Any) -> int:
        """判断录入区间是否重复：``id != ?`` + ``out_time >= inTime`` + ``in_time <= outTime``。"""
        sql = "select count(1) from car_except_record t where t.del_flag = '0'"
        params: Dict[str, Any] = {}
        if query.id is not None and query.id != "":
            sql = f"{sql} and t.id != :id"
            params["id"] = query.id
        if query.in_time is not None:
            sql = f"{sql} and t.out_time >= :inTime"
            params["inTime"] = query.in_time
        if query.out_time is not None:
            sql = f"{sql} and t.in_time <= :outTime"
            params["outTime"] = query.out_time
        if query.car_no is not None and query.car_no != "":
            sql = f"{sql} and t.car_no = :carNo"
            params["carNo"] = query.car_no
        with session_scope() as session:
            row = session.execute(text(sql), params).first()
        return 0 if row is None else int(row[0] or 0)

    # -------------------------------------------------------- 按车牌统计

    # Java: CarExceptRecord exceptRecordCount(CarExceptRecord x)
    def except_record_count(self, query: Any) -> Optional[Any]:
        sql = (
            "select t.car_no,count(1) exceptNum,round(sum(t.dif_amount),2) exceptAmount,"
            "round(sum(t.total_amount),2) total_amount,"
            "round(sum(t.charge_amount),2) charge_amount "
            "from car_except_record t "
            "where t.del_flag = '0' and t.car_no = :carNo"
        )
        params: Dict[str, Any] = {"carNo": query.car_no}
        if query.status is not None and query.status != "":
            sql = f"{sql} and t.status = :status"
            params["status"] = query.status
        sql = f"{sql} group by t.car_no"
        with session_scope() as session:
            row = session.execute(text(sql), params).first()
        if row is None:
            return None
        return map_row(self.entity_cls, self.result_columns, row)

    # Java: List<CarExceptRecord> exceptRecordList(CarExceptRecord x)
    def except_record_list(self, query: Any) -> List[Any]:
        """按车牌统计逃费类型（``group_concat``）—— ``saveCarExcept`` 用。"""
        sql = (
            "select t.car_no,count(1) exceptNum,round(sum(t.dif_amount),2) exceptAmount,"
            "round(sum(t.total_amount),2) total_amount,"
            "round(sum(t.charge_amount),2) charge_amount,"
            "group_concat(distinct t.escaped_type SEPARATOR ',') escaped_type "
            "from car_except_record t where t.del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        if query.car_no is not None and query.car_no != "":
            sql = f"{sql} and t.car_no = :carNo"
            params["carNo"] = query.car_no
        if query.status is not None and query.status != "":
            sql = f"{sql} and t.status = :status"
            params["status"] = query.status
        sql = f"{sql} group by t.car_no"
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    # -------------------------------------------------------- 大屏统计

    # Java: List<CarStatisticsVO> buildPCCarStatisticsVO(ids, escapedType)
    def build_pc_car_statistics_vo(
        self, ids: Optional[Sequence[str]], escaped_type: Optional[str]
    ) -> List[CarStatisticsVO]:
        sql = (
            "select escaped_type, sum(ifnull(dif_amount, 0)) escapedAmount, "
            "count(distinct car_no) number "
            "from car_except_record where del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        if ids:
            placeholders = ",".join(f":id{index}" for index in range(len(ids)))
            sql = f"{sql} and id in ({placeholders})"
            params.update({f"id{index}": value for index, value in enumerate(ids)})
        if escaped_type is not None and escaped_type != "":
            sql = f"{sql} and escaped_type = :escapedType"
            params["escapedType"] = escaped_type
        sql = f"{sql} group by escaped_type"
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [
            map_row(CarStatisticsVO, ("escaped_type", "escaped_amount", "number"), row)
            for row in rows
        ]

    # Java: List<PCCarStatisticsDetailVO> buildPCCarStatisticsVODetail(ids, escapedType)
    def build_pc_car_statistics_vo_detail(
        self, ids: Optional[Sequence[str]], escaped_type: Optional[str]
    ) -> List[PCCarStatisticsDetailVO]:
        sql = (
            "select c.plate_color, e.car_no, e.car_type, e.escaped_type, "
            "e.dif_amount escapedAmount, e.create_time "
            "from car_except_record e "
            "left join car_info c on e.car_no = c.car_no "
            "where e.del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        if ids:
            placeholders = ",".join(f":id{index}" for index in range(len(ids)))
            sql = f"{sql} and e.id in ({placeholders})"
            params.update({f"id{index}": value for index, value in enumerate(ids)})
        if escaped_type is not None and escaped_type != "":
            sql = f"{sql} and e.escaped_type = :escapedType"
            params["escapedType"] = escaped_type
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [
            map_row(
                PCCarStatisticsDetailVO,
                ("plate_color", "car_no", "car_type", "escaped_type", "escaped_amount", "create_time"),
                row,
            )
            for row in rows
        ]

    # -------------------------------------------------------- 状态回写 / 物理删除

    # Java: void updateStatusByExceptId(List<String> exceptIdList, String status)
    def update_status_by_except_id(
        self, except_id_list: Sequence[str], status: str
    ) -> int:
        if not except_id_list:
            # Java 会拼出 ``in ()`` —— MySQL 报语法错；这里照抄"空列表不发语句"更安全
            return 0
        placeholders = ",".join(f":id{index}" for index in range(len(except_id_list)))
        sql = f"update car_except_record set status = :status where id in ({placeholders})"
        params: Dict[str, Any] = {"status": status}
        params.update({f"id{index}": value for index, value in enumerate(except_id_list)})
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return result.rowcount or 0

    # Java: int deleteCarExceptRecordByCarId(String fkId)
    def delete_by_car_id(self, fk_id: str) -> int:
        """按车辆删除异常流水 —— XML 是 ``<delete>``（物理删除）。"""
        sql = "delete from car_except_record where car_id = :fkId"
        with session_scope() as session:
            result = session.execute(text(sql), {"fkId": fk_id})
            return result.rowcount or 0


__all__ = [
    "CarExceptRecordMapper",
    "CONDITIONS",
    "CONDITIONS_NEW",
    "COUNT_COLUMNS",
    "RESULT_COLUMNS",
    "SELECT_CAR_EXCEPT_RECORD_VO",
]
