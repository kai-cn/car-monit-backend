"""确认补缴 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarConfimFreeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml

标准 ``manager`` 模板：26 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import bindparam, text

from app.base.mapper.ods_sql import If, build_conditions, map_result_row, map_row
from app.config.database import session_scope
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.mapper.manager_mapper import ManagerListMapper
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO

#: Java: ``<sql id="selectCarConfimFreeVo">``
SELECT_CAR_CONFIM_FREE_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.link_name,
        t.link_phone,
        t.org_id,
        sd.dept_name org_name,
        t.user_ids,
        t.user_names,
        t.amount,
        t.aduit_amount,
        t.except_ids,
        t.escaped_types,
        t.back_col1,
        t.back_col2,
        t.remark,
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

#: ``resultMap`` 的 27 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "car_type",
    "car_vehicle",
    "link_name",
    "link_phone",
    "org_id",
    "org_name",
    "user_ids",
    "user_names",
    "amount",
    "aduit_amount",
    "except_ids",
    "escaped_types",
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

#: ``selectCarConfimFreeList`` 的 26 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("link_name", "link_name", like=True),
    If("link_phone", "link_phone"),
    If("org_id", "org_id"),
    If(
        "org_name",
        "sd.dept_name",
        template="and sd.dept_name like concat('%', {p}, '%')",
    ),
    If("user_ids", "user_ids"),
    If("user_names", "user_names"),
    If("amount", "amount", null_only=True),
    If("escaped_types", "escaped_types"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If(
        "except_ids",
        "find_in_set(t.id,#{exceptIds})",
        template="and find_in_set(t.id,{p}) > 0",
    ),
    If("car_no_query", "car_no", like=True),
    If(
        "apply_time1",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time3",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time4",
        "create_time<",
        template="and t.create_time< date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
)

#: ``selectConcernedList`` 的 ``<if>``（**照抄** XML，尽管 ``t`` 指向 ``car_info``：
#: ``user_ids`` / ``amount`` / ``back_col1`` 等列在 ``car_info`` 上并不存在，
#: 一旦传值 Java 就会抛 SQL 异常 —— 照抄，不修正）。
CONDITIONS_CONCERNED: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("link_name", "link_name", like=True),
    If("link_phone", "link_phone"),
    If("org_id", "org_id"),
    If(
        "org_name",
        "sd.dept_name",
        template="and sd.dept_name like concat('%', {p}, '%')",
    ),
    If("user_ids", "user_ids"),
    If("user_names", "user_names"),
    If("amount", "amount", null_only=True),
    If("escaped_types", "escaped_types"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If(
        "except_ids",
        "find_in_set",
        template="and find_in_set(t.id,{p}) > 0",
    ),
    If("car_no_query", "car_no", like=True),
    If(
        "apply_time1",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
)

#: ``selectConcernedList`` 的 ``resultType`` 属性（别名即属性名）。
CONCERNED_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_no",
    "car_type",
    "car_vehicle",
    "escaped_type",
    "org_id",
    "org_name",
    "total_amount",
    "charge_amount",
    "dif_amount",
    "except_ids",
)

#: ``getPCCarStatistics`` 的 ``resultType`` 属性。
PC_STATISTICS_COLUMNS: Tuple[str, ...] = (
    "eps_id",
    "org_name",
    "escaped_type",
    "escaped_amount",
    "number",
)


class CarConfimFreeMapper(ManagerListMapper):
    """Java: ``interface CarConfimFreeMapper extends BaseMapper<CarConfimFree>``."""

    table = "car_confim_free"
    select_vo = SELECT_CAR_CONFIM_FREE_VO
    entity_cls = CarConfimFree
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    from_clause = "car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id"

    # Java: List<CarConfimFree> selectCarConfimFreeByExceptIds(List<String> exceptIds)
    def select_by_except_ids(self, except_ids: Sequence[str]) -> List[Any]:
        """按异常流水 id 集合反查补缴单 —— ``<foreach>`` 拼 ``OR`` 的
        ``find_in_set(#{id}, t.except_ids) > 0``。

        空集合在 Java 里会拼出 ``and ()``（MySQL 语法错）；照抄成"查不到"更安全。
        """
        if not except_ids:
            return []
        conditions = " OR ".join(
            f"find_in_set(:id{index}, t.except_ids) > 0"
            for index in range(len(except_ids))
        )
        sql = (
            f"SELECT {self.select_vo} FROM {self._from()} "
            f"WHERE t.del_flag = '0' and ({conditions})"
        )
        params = {f"id{index}": value for index, value in enumerate(except_ids)}
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    # Java: String selectOrgId(@Param("carId") String carId, @Param("id") String id)
    def select_org_id(self, car_id: str, entity_id: str) -> Optional[str]:
        sql = (
            "select org_id from car_confim_free "
            "where car_id = :carId and find_in_set(except_ids, :id) > 0"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"carId": car_id, "id": entity_id}).first()
        return None if row is None else row[0]

    # 大屏 ``/exceptRecordList`` 批量版：一条 SQL 取回本页所有 ``car_id`` 的候选行，
    # ``find_in_set`` 在 Python 侧按逗号切分复刻，避免每行一次往返。
    def select_org_ids(self, pairs: Sequence[Tuple[str, str]]) -> Dict[Tuple[str, str], Optional[str]]:
        result: Dict[Tuple[str, str], Optional[str]] = {
            (car_id, entity_id): None for car_id, entity_id in pairs
        }
        car_ids = sorted({car_id for car_id, _ in pairs if car_id})
        if not car_ids:
            return result

        statement = text(
            "select car_id, except_ids, org_id from car_confim_free "
            "where car_id in :carIds"
        ).bindparams(bindparam("carIds", expanding=True))
        with session_scope() as session:
            rows = session.execute(statement, {"carIds": car_ids}).all()

        for row in rows:
            row_car_id, except_ids, org_id = row[0], row[1], row[2]
            tokens = {token for token in str(except_ids or "").split(",") if token}
            for pair in result:
                if pair[0] == row_car_id and str(pair[1]) in tokens and result[pair] is None:
                    result[pair] = org_id
        return result

    # Java: List<CarConfimFree> getPCCarStatistics(CarConfimFreeQueryRo queryRo)
    def get_pc_car_statistics(self, query_ro: Any) -> List[Any]:
        """按部门 + 逃费类型汇总 —— ``group by`` 三列，别名走 ``camelCase``。"""
        sql = (
            "select d.dept_id eps_id,d.dept_name org_name,a.escaped_type escapedType,"
            " sum(ifnull(a.dif_amount, 0)) escapedAmount, count(distinct a.car_no) number "
            "from car_except_record a "
            "inner join sys_dept d on a.eps_id = d.dept_id and d.del_flag = '0' "
            "where a.del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        apply_time1 = getattr(query_ro, "apply_time1", None)
        apply_time2 = getattr(query_ro, "apply_time2", None)
        escaped_type = getattr(query_ro, "escaped_type", None)
        org_id = getattr(query_ro, "org_id", None)
        if apply_time1 is not None and apply_time1 != "":
            sql = f"{sql} and a.create_time >= STR_TO_DATE(:applyTime1,'%Y-%m-%d')"
            params["applyTime1"] = apply_time1
        if apply_time2 is not None and apply_time2 != "":
            sql = (
                f"{sql} and a.create_time < "
                "date_add(STR_TO_DATE(:applyTime2,'%Y-%m-%d'), interval 1 day)"
            )
            params["applyTime2"] = apply_time2
        if escaped_type is not None and escaped_type != "":
            sql = f"{sql} and a.escaped_type = :escapedType"
            params["escapedType"] = escaped_type
        if org_id is not None and org_id != "":
            sql = f"{sql} and a.eps_id = :orgId"
            params["orgId"] = org_id
        sql = f"{sql} group by d.dept_id,d.dept_name,a.escaped_type"
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [
            map_result_row(self.entity_cls, PC_STATISTICS_COLUMNS, row) for row in rows
        ]

    # ---------------------------------------------------------------- 待关注车辆

    # Java: List<CarConfimFree> selectConcernedList(CarConfimFree carConfimFree)
    def select_concerned_list(self, query: Any) -> List[Any]:
        """待关注车辆 —— ``car_info`` 与一张按车牌聚合的派生表 ``JOIN``。

        派生表里 ``except_num`` = 未处理（``status = '0'``）条数，只保留
        ``count_num > 0 and except_num = 0``（即"有条目但全部处理完"）的车牌。
        """
        sql = (
            "select t.id, t.car_no, t.car_type, t.car_vehicle, t.escaped_type, "
            "t.org_id, sd.dept_name org_name, "
            "k.total_amount totalAmount, k.charge_amount chargeAmount, "
            "k.dif_amount difAmount, k.except_ids "
            "from car_info t JOIN "
            "(select t1.car_no,sum(t1.total_amount) total_amount,"
            "sum(t1.charge_amount) charge_amount,sum(t1.dif_amount) dif_amount, "
            "sum(case when t1.status = '0' then 1 else 0 end) except_num, "
            "count(1) count_num, GROUP_CONCAT(t1.id SEPARATOR ',') except_ids "
            "from car_except_record t1 where t1.del_flag = '0' "
            "group by t1.car_no) k on k.count_num > 0 and k.except_num = 0 "
            "and t.car_no = k.car_no "
            "left join sys_dept sd on sd.dept_id = t.eps_id and sd.del_flag = '0' "
            "WHERE t.del_flag = '0'"
        )
        fragments, params = build_conditions(query, CONDITIONS_CONCERNED)
        for fragment in fragments:
            sql = f"{sql} {fragment}"

        from app.common.core.page.page_helper import PageList, select_page, take_page

        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(
                session, f"select count(0) from ({sql}) table_count", sql, params, page
            )
        mapped = [
            map_result_row(self.entity_cls, CONCERNED_COLUMNS, row) for row in page_list
        ]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # ---------------------------------------------------------------- 单车牌汇总

    # Java: CarConfimFree listCount(CarConfimFree carConfimFree)
    def list_count(self, query: Any) -> Optional[Any]:
        """按车牌汇总补缴次数与金额（``sum(aduit_amount) + sum(amount)``）。

        ``resultMap`` 没声明 ``confimFreeNum`` / ``confimFreeAmount`` 两个别名列，
        但 MyBatis 默认 ``autoMappingBehavior=PARTIAL`` 会把未声明的列按名字自动
        映射到同名属性 —— 所以这两个值**有值**。
        """
        sql = (
            "select t.car_no,count(1) confimFreeNum,"
            "round(ifnull(sum(t.aduit_amount),0) + ifnull(sum(t.amount),0),2) "
            "confimFreeAmount "
            "from car_confim_free t "
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
        return map_result_row(
            self.entity_cls,
            ("car_no", "confim_free_num", "confim_free_amount"),
            row,
        )

    # ---------------------------------------------------------------- 大屏统计

    # Java: List<CarStatisticsVO> getCarStatistics(IncomeStatisticParam param)
    def get_car_statistics(self, param: Any) -> List[CarStatisticsVO]:
        """按逃费类型汇总（``car_except_record``）。"""
        sql = (
            "select a.escaped_type escapedType, sum(ifnull(a.dif_amount, 0)) "
            "escapedAmount, count(distinct a.car_no) number "
            "from car_except_record a where a.del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        apply_time1 = getattr(param, "apply_time1", None)
        apply_time2 = getattr(param, "apply_time2", None)
        escaped_type = getattr(param, "escaped_type", None)
        org_id = getattr(param, "org_id", None)
        if apply_time1 is not None and apply_time1 != "":
            sql = f"{sql} and a.create_time >= STR_TO_DATE(:applyTime1,'%Y-%m-%d')"
            params["applyTime1"] = apply_time1
        if apply_time2 is not None and apply_time2 != "":
            sql = (
                f"{sql} and a.create_time < "
                "date_add(STR_TO_DATE(:applyTime2,'%Y-%m-%d'), interval 1 day)"
            )
            params["applyTime2"] = apply_time2
        if escaped_type is not None and escaped_type != "":
            sql = f"{sql} and a.escaped_type = :escapedType"
            params["escapedType"] = escaped_type
        if org_id is not None and org_id != "":
            sql = f"{sql} and a.eps_id = :orgId"
            params["orgId"] = org_id
        sql = f"{sql} group by a.escaped_type"
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [
            map_result_row(CarStatisticsVO, ("escaped_type", "escaped_amount", "number"), row)
            for row in rows
        ]

    # Java: CarStatisticsVO getCarConfirm(IncomeStatisticParam param)
    def get_car_confirm(self, param: Any) -> Optional[CarStatisticsVO]:
        """补缴合计（``amount + aduit_amount``，只算 ``status = '0'``）。"""
        sql = (
            "select sum(ifnull(a.amount, 0) + ifnull(a.aduit_amount, 0)) escapedAmount,"
            "count(distinct a.car_no) number "
            "from car_confim_free a where a.del_flag = '0' and a.status = '0'"
        )
        params: Dict[str, Any] = {}
        apply_time1 = getattr(param, "apply_time1", None)
        apply_time2 = getattr(param, "apply_time2", None)
        if apply_time1 is not None and apply_time1 != "":
            sql = f"{sql} and a.create_time >= STR_TO_DATE(:applyTime1,'%Y-%m-%d')"
            params["applyTime1"] = apply_time1
        if apply_time2 is not None and apply_time2 != "":
            sql = (
                f"{sql} and a.create_time < "
                "date_add(STR_TO_DATE(:applyTime2,'%Y-%m-%d'), interval 1 day)"
            )
            params["applyTime2"] = apply_time2
        with session_scope() as session:
            row = session.execute(text(sql), params).first()
        if row is None:
            return None
        return map_result_row(CarStatisticsVO, ("escaped_amount", "number"), row)


__all__ = [
    "CONCERNED_COLUMNS",
    "CONDITIONS",
    "CONDITIONS_CONCERNED",
    "PC_STATISTICS_COLUMNS",
    "CarConfimFreeMapper",
    "RESULT_COLUMNS",
    "SELECT_CAR_CONFIM_FREE_VO",
]
