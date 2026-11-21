"""门架抓拍流水.

# Migrated from: com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml

生成器模板 + 只读：只有 ``list`` 与 ``{pk}`` 两条 XML 语句，
外加固定的逻辑删除语句。``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import bindparam, text

from app.base.mapper.plus_mapper import logic_delete_by_id, logic_delete_by_ids
from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import OdsRtSzdnSnapshotFlowAddcode
from app.base.mapper.ods_sql import If, OdsListMapper, build_conditions, map_row
from app.config.database import session_scope
from app.manager.domain.vo.bigscreen.top_ten_vo import TopTenVO

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_ADDCODE_VO = """
        t.big_id,
        t.datasource,
        t.cameratype,
        t.deviceid,
        t.gantrycode,
        t.gantryname,
        t.roadcode,
        t.roadname,
        t.sectioncode,
        t.sectionname,
        t.tollcode,
        t.tollname,
        t.orgcode,
        t.orgname,
        t.direction,
        t.hexcode,
        t.pileno,
        t.lon,
        t.lat,
        t.deviceip,
        t.siteid,
        t.laneid,
        t.snapshottimeunix,
        t.snapshottime,
        t.receivedtimeunix,
        t.receivedtime,
        t.platenumber,
        t.platecolor,
        t.platecolorcode,
        t.platetype,
        t.platetypecode,
        t.plateconfidence,
        t.carbrand,
        t.carcolor,
        t.carcolorcode,
        t.cartype,
        t.cartypecode,
        t.cardirection,
        t.snappicturepath,
        t.loadtime,
        t.gradelevel,
        t.datauuid,
        t.reserve3
    
"""

#: resultMap 声明的 43 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "big_id",
    "datasource",
    "cameratype",
    "deviceid",
    "gantrycode",
    "gantryname",
    "roadcode",
    "roadname",
    "sectioncode",
    "sectionname",
    "tollcode",
    "tollname",
    "orgcode",
    "orgname",
    "direction",
    "hexcode",
    "pileno",
    "lon",
    "lat",
    "deviceip",
    "siteid",
    "laneid",
    "snapshottimeunix",
    "snapshottime",
    "receivedtimeunix",
    "receivedtime",
    "platenumber",
    "platecolor",
    "platecolorcode",
    "platetype",
    "platetypecode",
    "plateconfidence",
    "carbrand",
    "carcolor",
    "carcolorcode",
    "cartype",
    "cartypecode",
    "cardirection",
    "snappicturepath",
    "loadtime",
    "gradelevel",
    "datauuid",
    "reserve3",
)

#: ``selectOdsRtSzdnSnapshotFlowAddcodeList`` 的 43 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id"),
    If("datasource", "datasource"),
    If("cameratype", "cameratype"),
    If("deviceid", "deviceid"),
    If("gantrycode", "gantrycode"),
    If("gantryname", "gantryname", like=True),
    If("roadcode", "roadcode"),
    If("roadname", "roadname", like=True),
    If("sectioncode", "sectioncode"),
    If("sectionname", "sectionname", like=True),
    If("tollcode", "tollcode"),
    If("tollname", "tollname", like=True),
    If("orgcode", "orgcode"),
    If("orgname", "orgname", like=True),
    If("direction", "direction", null_only=True),
    If("hexcode", "hexcode"),
    If("pileno", "pileno"),
    If("lon", "lon", null_only=True),
    If("lat", "lat", null_only=True),
    If("deviceip", "deviceip"),
    If("siteid", "siteid", null_only=True),
    If("laneid", "laneid", null_only=True),
    If("snapshottimeunix", "snapshottimeunix", null_only=True),
    If("snapshottime", "snapshottime", null_only=True),
    If("receivedtimeunix", "receivedtimeunix", null_only=True),
    If("receivedtime", "receivedtime", null_only=True),
    If("platenumber", "platenumber"),
    If("platecolor", "platecolor"),
    If("platecolorcode", "platecolorcode", null_only=True),
    If("platetype", "platetype"),
    If("platetypecode", "platetypecode", null_only=True),
    If("plateconfidence", "plateconfidence", null_only=True),
    If("carbrand", "carbrand"),
    If("carcolor", "carcolor"),
    If("carcolorcode", "carcolorcode", null_only=True),
    If("cartype", "cartype"),
    If("cartypecode", "cartypecode", null_only=True),
    If("cardirection", "cardirection"),
    If("snappicturepath", "snappicturepath"),
    If("loadtime", "loadtime", null_only=True),
    If("gradelevel", "gradelevel", null_only=True),
    If("datauuid", "datauuid"),
    If("reserve3", "reserve3"),
)


#: ``selectShardingList`` / ``selectShardingCount`` 的 ``<if>`` 列表。
#:
#: 与 :data:`CONDITIONS` **不同**：分表语句只覆盖 22 个条件，且 ``applyTime1`` /
#: ``applyTime2`` 不是等值而是 ``snapshottime`` 的不等式、``sectionCodeStr`` 用
#: ``find_in_set``。逐条照抄 XML，不要"复用" 上面的列表。
SHARDING_CONDITIONS: Tuple[If, ...] = (
    If("big_id", "big_id"),
    If("datasource", "datasource"),
    If("cameratype", "cameratype"),
    If("deviceid", "deviceid"),
    If("gantrycode", "gantrycode"),
    If("gantryname", "gantryname", like=True),
    If("roadcode", "roadcode"),
    If("roadname", "roadname", like=True),
    If("sectioncode", "sectioncode"),
    If("sectionname", "sectionname", like=True),
    If("tollcode", "tollcode"),
    If("tollname", "tollname", like=True),
    If("orgcode", "orgcode"),
    If("orgname", "orgname", like=True),
    If("direction", "direction", null_only=True),
    If("platenumber", "platenumber"),
    If("platecolor", "platecolor"),
    If("cartype", "cartype"),
    If("apply_time1", "snapshottime", template="and t.snapshottime >= {p}"),
    If("apply_time2", "snapshottime", template="and t.snapshottime <= {p}"),
    If(
        "section_code_str",
        "sectioncode",
        template="and find_in_set(t.sectioncode, {p})",
    ),
)


class OdsRtSzdnSnapshotFlowAddcodeMapper(OdsListMapper):
    """Java: ``interface OdsRtSzdnSnapshotFlowAddcodeMapper``."""

    table = "ods_rt_szdn_snapshot_flow_addcode"
    select_vo = SELECT_ODS_RT_SZDN_SNAPSHOT_FLOW_ADDCODE_VO
    entity_cls = OdsRtSzdnSnapshotFlowAddcode
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.big_id"
    #: XML 的 ``selectXxxById`` 过滤的是 ``datauuid``（Java 形参名叫 ``bigId`` 但没用它）——
    #: 这是原代码的偏差，照抄。
    detail_column = "datauuid"
    #: ``@TableId(value = "big_id", type = IdType.INPUT)`` —— ``updateById`` / ``insert`` 用 ``big_id``。
    pk_column = "big_id"

    def delete_ods_rt_szdn_snapshot_flow_addcode_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "big_id", entity_ids)

    # Java: int deleteOdsRtSzdnSnapshotFlowAddcodeById(String bigId)
    def delete_ods_rt_szdn_snapshot_flow_addcode_by_id(self, entity_id) -> int:
        """XML 原文：``update ... set del_flag = '1' where big_id = #{bigId}``。

        不能用基类的 ``delete_by_id`` —— 那会按 :attr:`detail_column` (``datauuid``) 删。
        """
        return logic_delete_by_id(self.table, "big_id", entity_id)

    # ------------------------------------------------------------ 分表语句

    # Java: List<OdsRtSzdnSnapshotFlowAddcode> selectShardingList(
    #           @Param("tableName") String tableName,
    #           @Param("odsRtSzdnSnapshotFlowAddcode") OdsRtSzdnSnapshotFlowAddcode q,
    #           @Param("offset") int offset)
    def select_sharding_list(self, table_name: str, query: Any, offset: int) -> List[Any]:
        """分表分页查询。``LIMIT #{offset}, #{pageSize}`` 只在 ``pageNum`` / ``pageSize``
        都非空时追加 —— 增强服务的调用点总会先给默认值，所以**实际总是带 LIMIT**。
        """
        sql, params = self.build_sharding_list_sql(table_name, query, offset)
        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        return [map_row(self.entity_cls, self.result_columns, row) for row in rows]

    # Java: Long selectShardingCount(
    #           @Param("tableName") String tableName,
    #           @Param("odsRtSzdnSnapshotFlowAddcode") OdsRtSzdnSnapshotFlowAddcode q)
    def select_sharding_count(self, table_name: str, query: Any) -> int:
        fragments, params = build_conditions(query, SHARDING_CONDITIONS)
        sql = f"SELECT COUNT(1) FROM {table_name} t WHERE 1=1"
        if fragments:
            sql = sql + " " + " ".join(fragments)
        with session_scope() as session:
            return int(session.execute(text(sql), params).scalar() or 0)

    # Java: Long getTableApproximateCount(@Param("tableName") String tableName)
    def get_table_approximate_count(self, table_name: str) -> Optional[int]:
        """``INFORMATION_SCHEMA.TABLES.TABLE_ROWS`` —— 表不存在时**没有行**，
        返回 ``None``（Java 侧是 ``null``，由调用方降级到精确 COUNT）。
        """
        sql = (
            "SELECT TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name"
        )
        with session_scope() as session:
            value = session.execute(text(sql), {"table_name": table_name}).scalar()
        return None if value is None else int(value)

    # 分表统计批量版：一条 ``INFORMATION_SCHEMA`` 查询取回所有历史分表的近似行数，
    # 把"每张表一次往返"降到一次（P2-2）。
    def get_table_approximate_counts(self, table_names: Sequence[str]) -> Dict[str, int]:
        names = sorted({name for name in table_names if name})
        if not names:
            return {}
        statement = text(
            "SELECT TABLE_NAME, TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN :names"
        ).bindparams(bindparam("names", expanding=True))
        with session_scope() as session:
            rows = session.execute(statement, {"names": names}).all()
        # TABLE_ROWS 对视图/尚未 analyze 的表可能是 NULL -> 交给调用方降级精确 COUNT。
        return {str(row[0]): int(row[1]) for row in rows if row[1] is not None}

    # --------------------------------------------------- 分表维护（同步任务用）

    # Java: int checkTableExists(@Param("tableName") String tableName)
    def check_table_exists(self, table_name: str) -> int:
        """分表是否存在：存在返回 ``1``，不存在返回 ``0``（Java 的语义就是计数）。"""
        sql = (
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name"
        )
        with session_scope() as session:
            return int(session.execute(text(sql), {"table_name": table_name}).scalar() or 0)

    # Java: void createShardingTable(@Param("tableName") String tableName)
    def create_sharding_table(self, table_name: str) -> int:
        """``CREATE TABLE IF NOT EXISTS ${tableName} LIKE ods_rt_szdn_snapshot_flow_addcode``.

        表名走 MyBatis 的 ``${}``（原样替换，不是绑定参数），这里同样用 f-string ——
        调用方是 :class:`~app.base.sharding.sharding_table_util.ShardingTableUtil`，
        表名完全由代码生成，不含外部输入。

        DDL 在 MySQL 里**隐式提交**，回滚不掉。
        """
        sql = (
            f"CREATE TABLE IF NOT EXISTS {table_name} "
            f"LIKE {self.table}"
        )
        with session_scope() as session:
            session.execute(text(sql))
        return 0

    # Java: Date getMaxSnapshottime(@Param("tableName") String tableName)
    def get_max_snapshottime(self, table_name: str) -> Optional[Any]:
        """增量同步的水位线：分表里最大的 ``snapshottime``（空表 / 表不存在时 ``None``）。"""
        sql = f"SELECT MAX(t.snapshottime) FROM {table_name} t"
        with session_scope() as session:
            return session.execute(text(sql)).scalar()

    # Java: void insertBatchToTable(@Param("tableName") String t, @Param("list") List<...> list)
    def insert_batch_to_table(self, table_name: str, entity_list: List[Any]) -> int:
        """批量插入到指定分表（XML 里是一条多值 ``INSERT ... <foreach>``）.

        **与 XML 的差异（有意为之）**：``insertBatchToTable`` / ``insertToTable`` 的
        62 个 ``#{item.xxx}`` 里，下表中这 25 个属性**在实体
        ``OdsRtSzdnSnapshotFlowAddcode`` 上并不存在**（实体只有 43 个字段）::

            smallpicturepath, plategnssstatus, gpsinfo, devicename, devicetype,
            carclass, gantryid, smallsideimage, headimageheight, sidescenetypecode,
            sidescenetype, tailimagewidth, envstate, headscenetypecode,
            headscenetype, sidedrivingdirectioncode, sidedrivingdirection,
            sideimageheight, speed, tailplateimage, headdrivingdirectioncode,
            headdrivingdirection, laneidcode, carlength, imagelevel

        MyBatis 解析 ``#{item.smallpicturepath}`` 时会抛
        ``ReflectionException: There is no getter for property named
        'smallpicturepath' in 'class ...OdsRtSzdnSnapshotFlowAddcode'`` —— 也就是说
        这条语句在 Java 侧**从未成功执行过**（两边都有用例之外的原样记录，见
        ``COMPATIBILITY.md`` §42.3）。

        这里按实体真实拥有的 43 列（:data:`RESULT_COLUMNS`）生成同样形状的多值
        ``INSERT``：只修"引用了不存在的属性"这个崩溃，不动业务规则。
        """
        if not entity_list:
            # Java: ``<foreach>`` 空列表会生成 ``VALUES`` 后面空无一物 -> SQL 语法错误。
            # 调用方（``syncSnapshotFlowByDateRange``）在这之前就 break 了，走不到这里。
            return 0
        columns = list(RESULT_COLUMNS)
        rows_sql: List[str] = []
        params: dict = {}
        for row_index, entity in enumerate(entity_list):
            placeholders: List[str] = []
            for column in columns:
                key = f"v{row_index}_{column}"
                placeholders.append(f":{key}")
                params[key] = getattr(entity, column, None)
            rows_sql.append("(" + ", ".join(placeholders) + ")")
        sql = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES "
            + ", ".join(rows_sql)
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: void insertToTable(@Param("tableName") String t, @Param("item") ... data)
    def insert_to_table(self, table_name: str, entity: Any) -> int:
        """单条插入到指定分表（XML ``insertToTable``；同样只写实体真实拥有的列）。"""
        return self.insert_batch_to_table(table_name, [entity])

    def build_sharding_list_sql(
        self, table_name: str, query: Any, offset: int
    ) -> Tuple[str, dict]:
        """拼出 ``selectShardingList`` 的完整 SQL（供单元测试直接断言）。"""
        fragments, params = build_conditions(query, SHARDING_CONDITIONS)
        sql = f"SELECT {self.select_vo} FROM {table_name} t WHERE 1=1"
        if fragments:
            sql = sql + " " + " ".join(fragments)
        sql = sql + " ORDER BY t.snapshottime DESC"
        page_num = getattr(query, "page_num", None)
        page_size = getattr(query, "page_size", None)
        if page_num is not None and page_size is not None:
            params["offset"] = offset
            params["page_size"] = page_size
            sql = sql + " LIMIT :offset, :page_size"
        return sql, params

    # Java: List<TopTenVO> getTopTen()
    def get_top_ten(self) -> List[TopTenVO]:
        """XML 原文：按“路线 + 路段”统计告警车辆数，降序取前 10。"""
        sql = (
            "select t1.road_code roadCode,t1.section_name sectionName, count(1) carNum "
            "from car_warning_info t,ods_szdn_section t1 "
            "where t.del_flag = '0' and t.section_code = t1.section_code "
            "group by t1.road_code,t1.section_name "
            "order by carNum desc "
            "limit 10"
        )
        with session_scope() as session:
            rows = session.execute(text(sql)).all()
        return [
            TopTenVO(
                road_code=row._mapping.get("roadCode"),
                section_name=row._mapping.get("sectionName"),
                car_num=row._mapping.get("carNum"),
            )
            for row in rows
        ]


__all__ = [
    "CONDITIONS",
    "OdsRtSzdnSnapshotFlowAddcodeMapper",
    "RESULT_COLUMNS",
    "SHARDING_CONDITIONS",
]
