"""轨迹数据 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/mapper/ZdataTrailTracksMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml

这份 XML 比 ``base`` 包里其它表"豪华"：除生成器的两条标准语句外，还手写了
``getHistoryTrail`` / ``getCyly`` / ``removeRealData`` 三条。三条都**有调用点**
（``ZdataTrailTracksServiceImpl.carTrackQuery`` 与
``manager`` 包的 ``CarTrackInfoServiceImpl``），所以必须一起迁移。

与 :class:`~app.base.mapper.ods_sql.OdsListMapper` 的关系
---------------------------------------------------------
``selectXxxList`` / ``selectXxxById`` 严格符合模板，直接继承；三条手写语句各自
拼 SQL，保持与 XML 逐行对应。

分页谁先被消费
--------------
``carTrackQuery`` 是在 ``startPage()`` 之后调用的，而它内部会执行 **1~2 条**
select。PageHelper（以及这里的 ``take_page()``）只给"紧随其后的第一条 select"
加分页，所以：

* ``isCylx == "1"`` -> ``getCyly`` **被分页**，随后的 ``getHistoryTrail`` 不分页；
* 否则 -> ``getHistoryTrail`` 被分页。

两条语句都走 :func:`~app.common.core.page.page_helper.select_page`（``page is None``
时退化为普通查询），因此这个次序自动成立，**不要**为了"性能"调整调用顺序。

``passCount`` 的来历
--------------------
``getCyly`` 的 ``passCount`` 不在 ``resultMap`` 里，靠 MyBatis 的
``autoMappingBehavior=PARTIAL`` 自动映射（列名 == 属性名）。所以
:data:`CYLY_RESULT_COLUMNS` 里**要**包含它，否则通行次数会丢。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.mapper.ods_sql import If, OdsListMapper, build_conditions, map_row
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from ``<sql id="selectZdataTrailTracksVo">``.
#: 注意其中 ``t.create_time`` —— ``resultMap`` 没有 ``createTime``，实体也没有，
#: 读出来即丢弃（见 :data:`RESULT_COLUMNS`）。
SELECT_ZDATA_TRAIL_TRACKS_VO = """
        t.uuid,
        t.type,
        t.point_count,
        t.plate_key,
        t.enter_time,
        t.exit_time,
        t.trail_points,
        t.create_time,
        t.enter_locationcode,
        t.exit_locationcode,
        t.track_josn,
        t.enaxlecount,
        t.entolllaneid,
        t.entollstationid,
        t.entollstationname,
        t.envehicleclass,
        t.envehicleid,
        t.envehicletype,
        t.enweight,
        t.extolllaneid,
        t.extollstationid,
        t.extollstationname,
        t.exvehicleclass,
        t.exvehicleid,
        t.exvehicletype,
        t.exweight,
        t.start_lon,
        t.strat_lat,
        t.end_lon,
        t.end_lat
"""

#: ``resultMap`` 的 29 条 ``<result>``（键是**列名**；``create_time`` **不在其中**）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "uuid",
    "type",
    "point_count",
    "plate_key",
    "enter_time",
    "exit_time",
    "trail_points",
    "enter_locationcode",
    "exit_locationcode",
    "track_josn",
    "enaxlecount",
    "entolllaneid",
    "entollstationid",
    "entollstationname",
    "envehicleclass",
    "envehicleid",
    "envehicletype",
    "enweight",
    "extolllaneid",
    "extollstationid",
    "extollstationname",
    "exvehicleclass",
    "exvehicleid",
    "exvehicletype",
    "exweight",
    "start_lon",
    "strat_lat",
    "end_lon",
    "end_lat",
)

#: ``getCyly`` 的投影：``resultMap`` 里的 ``uuid`` + 自动映射的 ``passCount``。
CYLY_RESULT_COLUMNS: Tuple[str, ...] = ("uuid", "passCount")

#: ``selectZdataTrailTracksList`` 的 ``<if>``（顺序与 XML 一致）。
LIST_CONDITIONS: Tuple[If, ...] = (
    If("uuid", "uuid"),
    If("type", "type", null_only=True),
    If("point_count", "point_count", null_only=True),
    If("plate_key", "plate_key"),
    If("enter_time", "enter_time", null_only=True),
    If("exit_time", "exit_time", null_only=True),
    If("trail_points", "trail_points"),
    # 瞬态字段 carNo 复用 plate_key 列（等值）。
    If("car_no", "plate_key", template="and t.plate_key = {p}"),
    If(
        "apply_time1",
        "enter_time",
        template="and t.enter_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "enter_time",
        template="and t.enter_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
)

#: ``getHistoryTrail`` 的 ``<if>``（**不含** ``uuidList``，它单独做 ``in`` 展开）。
HISTORY_CONDITIONS: Tuple[If, ...] = (
    If("car_no", "plate_key", template="and t.plate_key = {p}"),
    If("plate_key", "plate_key", like=True),
    If(
        "apply_time1",
        "enter_time",
        template="and t.enter_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "enter_time",
        template="and t.enter_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
    If("entollstationid", "entollstationid"),
)

#: ``getCyly`` 内层子查询的 ``<if>``。
CYLY_CONDITIONS: Tuple[If, ...] = (
    If("car_no", "plate_key", template="and t.plate_key = {p}"),
    If(
        "apply_time1",
        "enter_time",
        template="and t.enter_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "enter_time",
        template="and t.enter_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
)


class ZdataTrailTracksMapper(OdsListMapper):
    """Java: ``interface ZdataTrailTracksMapper extends BaseMapper<ZdataTrailTracks>``."""

    table = "zdata_trail_tracks"
    select_vo = SELECT_ZDATA_TRAIL_TRACKS_VO
    entity_cls = ZdataTrailTracks
    result_columns = RESULT_COLUMNS
    conditions = LIST_CONDITIONS
    #: XML 末尾的 ``order by t.enter_time desc`` —— 分页不会追加客户端排序。
    order_by: Optional[str] = "t.enter_time desc"
    #: ``where t.uuid = #{uuid}``。
    detail_column = "uuid"

    # Java: List<ZdataTrailTracks> getHistoryTrail(ZdataTrailTracks x)
    def get_history_trail(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        """按车牌 / 时间段 / 入口收费站查历史轨迹（**含** ``uuidList`` 过滤）。"""
        data_sql, params = build_history_trail_sql(query)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [map_row(self.entity_cls, self.result_columns, row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<ZdataTrailTracks> getCyly(ZdataTrailTracks x)
    def get_cyly(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        """常用路线：按 (车牌, 入口站, 出口站) 取通行次数 Top 3，每组再取最新一条。"""
        data_sql, params = build_cyly_sql(query)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [map_row(self.entity_cls, CYLY_RESULT_COLUMNS, row) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: int removeRealData(@Param("carNoList") List<String> carNoList)
    def remove_real_data(self, car_no_list: Sequence[str]) -> int:
        """按车牌批量删除。

        ``<where>`` 在集合为 ``null`` / 空时**什么都不生成** —— 于是语句退化成
        ``delete from zdata_trail_tracks t``，即**全表删除**。这是 Java 侧的原始
        行为（调用方自己保证非空），照抄，不要在 Python 里加保护。
        """
        params: Dict[str, Any] = {}
        if car_no_list:
            clause, params = _in_clause("plate_key", list(car_no_list), "p")
            sql = f"delete from zdata_trail_tracks t WHERE {clause}"
        else:
            sql = "delete from zdata_trail_tracks t"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0


def build_history_trail_sql(
    query: ZdataTrailTracks,
) -> Tuple[str, Dict[str, Any]]:
    """``getHistoryTrail`` 的完整 SQL（``uuid in (...)`` 单独展开）。"""
    fragments, params = build_conditions(query, HISTORY_CONDITIONS)
    uuid_list = query.uuid_list
    if uuid_list:
        clause, in_params = _in_clause("uuid", list(uuid_list), "uuid")
        fragments.append(f"and {clause}")
        params.update(in_params)
    sql = f"select {SELECT_ZDATA_TRAIL_TRACKS_VO} from zdata_trail_tracks t where 1=1"
    if fragments:
        sql = sql + " " + " ".join(fragments)
    return sql + " order by t.enter_time desc", params


def build_cyly_sql(query: ZdataTrailTracks) -> Tuple[str, Dict[str, Any]]:
    """``getCyly`` 的完整 SQL（三层嵌套 + 窗口函数，逐行照抄 XML）。"""
    fragments, params = build_conditions(query, CYLY_CONDITIONS)
    inner_where = " WHERE  1=1"  # XML 里就是两个空格
    if fragments:
        inner_where = inner_where + " " + " ".join(fragments)
    sql = (
        "SELECT uuid, passCount\n"
        "FROM (SELECT\n"
        "t.uuid,\n"
        "gc.passCount,\n"
        "ROW_NUMBER() OVER (\n"
        "PARTITION BY t.plate_key, t.entollstationid, t.extollstationid\n"
        "ORDER BY t.enter_time DESC\n"
        ") as rn\n"
        "FROM zdata_trail_tracks t\n"
        "INNER JOIN (SELECT\n"
        "    plate_key,\n"
        "    entollstationid,\n"
        "    extollstationid,\n"
        "    COUNT(*) as passCount\n"
        "    FROM zdata_trail_tracks t"
        f"{inner_where}\n"
        "    GROUP BY plate_key, entollstationid, extollstationid\n"
        "    ORDER BY passCount DESC\n"
        "    LIMIT 3) gc ON t.plate_key = gc.plate_key\n"
        "                AND t.entollstationid = gc.entollstationid\n"
        "                AND t.extollstationid = gc.extollstationid) a\n"
        "WHERE rn = 1\n"
        "order by passCount desc"
    )
    return sql, params


__all__ = [
    "CYLY_RESULT_COLUMNS",
    "HISTORY_CONDITIONS",
    "LIST_CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_ZDATA_TRAIL_TRACKS_VO",
    "ZdataTrailTracksMapper",
    "build_cyly_sql",
    "build_history_trail_sql",
]
