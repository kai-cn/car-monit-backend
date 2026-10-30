"""补缴处理 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarAduitFreeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarAduitFreeMapper.xml

标准 ``manager`` 模板：18 条 ``<if>`` + ``order by t.create_time,t.id``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If, map_result_row
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.manager.domain.car_aduit_free import CarAduitFree
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.bigscreen.income_statistic_param import IncomeStatisticVO
from app.manager.domain.vo.pc_income_statics_vo import PCIncomeStaticsVO
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarAduitFreeVo">``
SELECT_CAR_ADUIT_FREE_VO = """
        t.id,
        t.confirm_id,
        t.car_id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.org_id,
        t.user_ids,
        t.user_names,
        t.amount,
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

#: ``resultMap`` 的 23 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "confirm_id",
    "car_id",
    "car_no",
    "car_type",
    "car_vehicle",
    "org_id",
    "org_name",
    "user_ids",
    "user_names",
    "amount",
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

#: ``selectCarAduitFreeList`` 的 18 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("confirm_id", "confirm_id"),
    If("car_id", "car_id"),
    If("car_no", "car_no", like=True),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("org_id", "org_id"),
    If(
        "org_name",
        "d.dept_name",
        template="and d.dept_name like concat('%', {p}, '%')",
    ),
    If("user_ids", "user_ids"),
    If("user_names", "user_names"),
    If("amount", "amount", null_only=True),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
)


class CarAduitFreeMapper(ManagerListMapper):
    """Java: ``interface CarAduitFreeMapper extends BaseMapper<CarAduitFree>``."""

    table = "car_aduit_free"
    select_vo = SELECT_CAR_ADUIT_FREE_VO
    entity_cls = CarAduitFree
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    from_clause = "car_aduit_free t left join sys_dept d on d.dept_id = t.org_id and d.del_flag = '0'"
    #: XML 的投影是 ``<include refid="selectCarAduitFreeVo"/>,d.dept_name org_name``
    #: —— ``org_name`` **不在** ``<sql>`` 里，少拼这一段的话列表里 ``orgName`` 恒为 null。
    select_suffix = ",d.dept_name org_name"
    #: 详情语句也拼同样的 ``org_name``（否则 ``select_by_id`` 的 ``orgName`` 恒为 null）。
    detail_suffix = ",d.dept_name org_name"
    order_by = "t.create_time,t.id"

    # ---------------------------------------------------------------- 物理删除

    # Java: int deleteCarAduitFreeByConfirmId(String fkId)
    def delete_by_confirm_id(self, fk_id: str) -> int:
        """按补缴单 id 删除明细 —— XML 是 ``<delete>``（**物理删除**，不是软删）。"""
        sql = "delete from car_aduit_free where confirm_id = :fkId"
        with session_scope() as session:
            result = session.execute(text(sql), {"fkId": fk_id})
            return result.rowcount or 0

    # ---------------------------------------------------------------- 大屏统计

    # Java: CarStatisticsVO getCarAudit(IncomeStatisticParam param)
    def get_car_audit(self, param: Any) -> Optional[CarStatisticsVO]:
        """补缴处理的逃费合计（注意数据源是 ``car_except_record``）。"""
        sql = (
            "select sum(ifnull(a.dif_amount, 0)) escapedAmount,"
            "count(distinct a.car_no) number "
            "from car_except_record a where a.del_flag = '0'"
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

    # Java: List<incomeStatisticVO> incomeStatistic(IncomeStatisticParam param)
    def income_statistic(self, param: Any) -> List[IncomeStatisticVO]:
        """按机构汇总收入 —— ``car_confim_free``（只算 ``status = '0'``）
        与 ``car_aduit_free`` 两段 ``UNION ALL`` 后再 ``group by``。
        """
        sql = (
            "select sum(ifnull(amount, 0)) amount, count(distinct car_no) carNum, "
            "d.dept_name orgName, a.org_id "
            "from ("
            "select t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status "
            "from car_confim_free t where t.del_flag = '0' and t.status = '0' "
            "UNION all "
            "select t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status "
            "from car_aduit_free t where t.del_flag = '0') a "
            "left join sys_dept d on d.dept_id = a.org_id and d.del_flag = '0' "
            "where a.del_flag = '0'"
        )
        params: Dict[str, Any] = {}
        query_date_type = getattr(param, "query_date_type", None)
        start_date = getattr(param, "start_date", None)
        apply_time1 = getattr(param, "apply_time1", None)
        apply_time2 = getattr(param, "apply_time2", None)
        if query_date_type is not None and query_date_type == "suo":
            sql = f"{sql} and a.status = '0'"
        if start_date is not None and start_date != "":
            sql = (
                f"{sql} and a.create_time >= STR_TO_DATE(:startDate,'%Y-%m-%d') "
                "and a.create_time < LAST_DAY(:startDate)"
            )
            params["startDate"] = start_date
        if query_date_type is not None and query_date_type == "suo":
            sql = f"{sql} and d.tree_leavel = 2"
        if query_date_type is not None and query_date_type == "zhan":
            sql = f"{sql} and d.tree_leavel = 3"
        if apply_time1 is not None and apply_time1 != "":
            sql = f"{sql} and a.create_time >= STR_TO_DATE(:applyTime1,'%Y-%m-%d')"
            params["applyTime1"] = apply_time1
        if apply_time2 is not None and apply_time2 != "":
            sql = (
                f"{sql} and a.create_time < "
                "date_add(STR_TO_DATE(:applyTime2,'%Y-%m-%d'), interval 1 day)"
            )
            params["applyTime2"] = apply_time2
        sql = f"{sql} group by a.org_id order by amount desc"
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [
            map_result_row(IncomeStatisticVO, ("org_name", "amount", "car_num"), row)
            for row in rows
        ]

    # Java: Integer selectAuditCount(IncomeStatisticParam param)
    def select_audit_count(self, param: Any) -> int:
        """补缴单条数（别名 ``confirmCount`` 不参与映射，只取 count）。"""
        sql = "select count(1) confirmCount from car_confim_free a where a.del_flag = '0'"
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
        return 0 if row is None or row[0] is None else int(row[0])

    # MyBatis-Plus: ``carAduitFreeService.lambdaQuery()
    # .eq(CarAduitFree::getCarId, carId).count()`` —— 大屏 ``/exceptRecordList`` 专用。
    def count_by_car_id(self, car_id: Optional[str]) -> int:
        """按车辆 id 数补缴明细条数。

        ``CarAduitFree`` 继承的 ``BasePlusEntity`` 带 ``@TableLogic(value="0")``，
        所以 MP 会自动追一个 ``del_flag = '0'`` —— 这里手写同一条条件。
        ``carId`` 为 ``null`` 时 MP 生成 ``car_id = null``（恒不命中），这里同样回 0。
        """
        sql = "select count(1) from car_aduit_free where del_flag = '0' and car_id = :carId"
        with session_scope() as session:
            row = session.execute(text(sql), {"carId": car_id}).first()
        return 0 if row is None or row[0] is None else int(row[0])

    # ---------------------------------------------------------------- PC 堵漏增收

    # Java: List<PCIncomeStaticsVO> PCIncomeStatics(CarConfimFreeQueryRo queryRo)
    def pc_income_statics(self, query_ro: Any) -> List[PCIncomeStaticsVO]:
        """按机构汇总堵漏增收 —— 两段 ``UNION ALL`` 各带一份相同的 ``<if>``。"""
        sql = (
            "select sum(t.amount) amount, count(distinct t.car_no) carNum, "
            "t.org_id, t.orgName "
            "from ("
            "select ifnull(a.amount, 0) amount, a.car_no, a.org_id, "
            "d.dept_name orgName "
            "from  car_aduit_free a "
            "left join sys_dept d on d.dept_id = a.org_id "
            "where a.del_flag = '0' and a.status = '0'"
        )
        params: Dict[str, Any] = {}
        sql = sql + self._pc_income_filter(query_ro, params)
        sql = sql + (
            " UNION all "
            "select ifnull(a.amount, 0) amount, a.car_no, a.org_id, "
            "d.dept_name orgName "
            "from car_confim_free a "
            "left join sys_dept d on d.dept_id = a.org_id "
            "where a.del_flag = '0'"
        )
        sql = sql + self._pc_income_filter(query_ro, params)
        sql = sql + ") t group by t.org_id, t.orgName  order by amount desc"
        # Java: ``BaseController.startPage()`` -> PageHelper 拦截上面这条语句。
        # Controller 里已经 ``startPage()``，这里必须把分页参数消费掉，否则返回全部
        # 机构（实测 21 行），而 Java 只返回第 1 页的 10 行、``total`` 仍是 21。
        # 映射之后必须把 ``PageList`` 的 ``total`` 一起带出去 —— 换成普通 list 的话
        # ``get_data_table`` 只能拿 ``len(rows)``，``total`` 就退化成 10。
        count_sql = f"select count(0) from ({sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, sql, params, page)
        mapped = [
            map_result_row(PCIncomeStaticsVO, ("org_id", "org_name", "amount", "car_num"), row)
            for row in page_list
        ]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    def _pc_income_filter(self, query_ro: Any, params: Dict[str, Any]) -> str:
        """``PCIncomeStatics`` 两段子查询里**完全相同**的那 4 条 ``<if>``。"""
        sql = ""
        org_id = getattr(query_ro, "org_id", None)
        apply_time1 = getattr(query_ro, "apply_time1", None)
        apply_time2 = getattr(query_ro, "apply_time2", None)
        car_no = getattr(query_ro, "car_no", None)
        if org_id is not None and org_id != "":
            sql = f"{sql} and a.org_id = :orgId"
            params["orgId"] = org_id
        if apply_time1 is not None and apply_time1 != "":
            sql = f"{sql} and a.create_time >= STR_TO_DATE(:applyTime1,'%Y-%m-%d')"
            params["applyTime1"] = apply_time1
        if apply_time2 is not None and apply_time2 != "":
            sql = (
                f"{sql} and a.create_time < "
                "date_add(STR_TO_DATE(:applyTime2,'%Y-%m-%d'), interval 1 day)"
            )
            params["applyTime2"] = apply_time2
        if car_no is not None and car_no != "":
            sql = f"{sql} and a.car_no like concat('%', :carNo, '%')"
            params["carNo"] = car_no
        return sql

    # Java: List<CarConfimFree> incomeDetailList(CarConfimFree confimFree)
    def income_detail_list(self, confim_free: Any) -> List[CarConfimFree]:
        """堵漏增收明细 —— 返回的是 ``CarConfimFree``（``resultType``）。"""
        sql = (
            "select  t.* from  ("
            "select ifnull(a.amount, 0) amount, a.car_no, a.org_id, "
            "d.dept_name orgName,a.create_time "
            "from  car_aduit_free a "
            "left join sys_dept d on d.dept_id = a.org_id "
            "where a.del_flag = '0' and a.status = '0'"
        )
        params: Dict[str, Any] = {}
        sql = sql + self._pc_income_filter(confim_free, params)
        sql = sql + (
            " UNION all "
            "select ifnull(a.amount, 0) amount, a.car_no, a.org_id, "
            "d.dept_name orgName,a.create_time "
            "from car_confim_free a "
            "left join sys_dept d on d.dept_id = a.org_id "
            "where a.del_flag = '0'"
        )
        sql = sql + self._pc_income_filter(confim_free, params)
        sql = sql + ") t order by t.create_time desc"
        # Java: 同样被 ``startPage()`` 拦截，见 :meth:`pc_income_statics`。
        count_sql = f"select count(0) from ({sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, sql, params, page)
        mapped = [
            map_result_row(
                CarConfimFree,
                ("amount", "car_no", "org_id", "org_name", "create_time"),
                row,
            )
            for row in page_list
        ]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )


__all__ = [
    "CarAduitFreeMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_ADUIT_FREE_VO",
]