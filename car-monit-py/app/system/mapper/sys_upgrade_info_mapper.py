"""系统升级信息表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUpgradeInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysUpgradeInfoMapper.xml

XML 里共 7 条 statement，本模块**全部迁移**（``deleteSysUpgradeInfoById`` 在 Java 侧
没有任何控制器调用，但按迁移原则第 4 条照留）。

``selectSysUpgradeInfoList`` 的 ``where`` 是硬编码的
---------------------------------------------------
前两行是写死的 ``where t.del_flag = '0'``，后面 7 个 ``<if>`` 各自带 ``and`` ——
XML 里**没有** ``<where>`` 标签，所以拼接时条件片段**不带**前导 ``AND``，统一用
``and`` 连起来（与 :mod:`app.system.mapper.sys_index_menu_mapper` 同一形态）。

7 个条件的判据分两类：

=========================================  ====================================
字段                                       判据
=========================================  ====================================
``id`` / ``ver`` / ``info`` / ``backCol1``  ``!= null and != ''``（``=`` 等值）
``epsId`` / ``tenantId`` / ``createBy``     ``!= null``（空串也照发）
=========================================  ====================================

``order by t.create_time desc,t.id`` 是自带的 —— 所以**不会**追加客户端排序列，
前端点表头排序对这张表**不生效**。

``selectSysUpgradeInfoById`` **没有** ``del_flag`` 过滤
------------------------------------------------------
```sql
select <include refid="selectSysUpgradeInfoVo"/> from sys_upgrade_info t where t.id = #{id}
```

与 ``selectSysUpgradeInfoList``（始终带 ``del_flag = '0'``）不对称：**被软删除的记录
仍能按 id 查到**。照抄。

``selectSysUpgradeInfoNewest`` 有三个特殊点
------------------------------------------
1. ``resultType`` 而不是 ``resultMap`` —— 靠 ``mapUnderscoreToCamelCase`` 自动映射
   （``back_col1`` -> ``backCol1``）。11 个属性名与列名一一对得上，所以结果一致。
2. SQL **完全无视入参**：Java 声明了 ``SysUpgradeInfo sysUpgradeInfo`` 但语句里没有
   一个 ``#{...}``（传什么都一样，照抄）。
3. ``back_col1 = 1`` 是**字符串列与数字比较**（MySQL 会做隐式转换），并且
   ``ORDER BY t.UPDATE_TIME`` 用大写列名。两处都照抄。

``insertSysUpgradeInfo`` 不回写主键
-----------------------------------
``<trim>`` 拼 11 个动态列，**没有** ``useGeneratedKeys``；主键是 service 侧
``StringUtils.getUUID()`` 先生成好的。

两条 ``delete`` 都是**软删除**
-----------------------------
``update sys_upgrade_info set del_flag = '1'`` —— 没有物理删除。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_upgrade_info import SysUpgradeInfo
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysUpgradeInfoMapper.xml -> ``<sql id="selectSysUpgradeInfoVo">``.
SELECT_SYS_UPGRADE_INFO_VO = (
    "t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, t.create_time, "
    "t.update_by, t.update_time, t.tenant_id"
)

#: ``insertSysUpgradeInfo`` 的 ``<trim>`` 分支，顺序与 XML 一致；11 列全是 ``!= null``。
_INSERT_COLUMNS: Tuple[str, ...] = (
    "id",
    "ver",
    "info",
    "back_col1",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``updateSysUpgradeInfo`` 的 ``<trim prefix="SET">`` 分支；**没有** ``id``（在 ``where`` 里）。
_UPDATE_COLUMNS: Tuple[str, ...] = (
    "ver",
    "info",
    "back_col1",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``resultMap="SysUpgradeInfoResult"`` 的列 -> 属性（11 个，顺序即 VO 的列顺序）。
_COLUMN_TO_FIELD: Dict[str, str] = {
    "id": "id",
    "ver": "ver",
    "info": "info",
    "back_col1": "back_col1",
    "eps_id": "eps_id",
    "del_flag": "del_flag",
    "create_by": "create_by",
    "create_time": "create_time",
    "update_by": "update_by",
    "update_time": "update_time",
    "tenant_id": "tenant_id",
}

#: ``selectSysUpgradeInfoList`` 的投影列（顺序即 SQL 的选择顺序）。
_LIST_COLUMNS: Tuple[str, ...] = tuple(_COLUMN_TO_FIELD)


class SysUpgradeInfoMapper:
    """Java: ``interface SysUpgradeInfoMapper``."""

    # Java: SysUpgradeInfo selectSysUpgradeInfoById(String id)
    def select_sys_upgrade_info_by_id(self, id: Any) -> Optional[SysUpgradeInfo]:
        """**没有** ``del_flag`` 过滤 —— 软删除的行也能查到。"""
        sql = f"select {SELECT_SYS_UPGRADE_INFO_VO}\nfrom sys_upgrade_info t\nwhere t.id = :id"
        with session_scope() as session:
            result = session.execute(text(sql), {"id": id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_upgrade_info(rows[0], keys)

    # Java: List<SysUpgradeInfo> selectSysUpgradeInfoList(SysUpgradeInfo sysUpgradeInfo)
    def select_sys_upgrade_info_list(self, entity: SysUpgradeInfo) -> List[SysUpgradeInfo]:
        """控制器在调用前已 ``startPage()``，分页点在这条 select 上。"""
        data_sql, params = _build_upgrade_info_list_sql(entity)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_upgrade_info(row, list(_LIST_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: SysUpgradeInfo selectSysUpgradeInfoNewest(SysUpgradeInfo sysUpgradeInfo)
    def select_sys_upgrade_info_newest(self, entity: SysUpgradeInfo) -> Optional[SysUpgradeInfo]:
        """``limit 1``，**无视入参**（Java 语句里没有 ``#{...}``）。"""
        sql = (
            f"select {SELECT_SYS_UPGRADE_INFO_VO}\n"
            "from sys_upgrade_info t\n"
            "where t.del_flag = '0'\n"
            "and t.back_col1 = 1\n"
            "ORDER BY t.UPDATE_TIME desc LIMIT 1"
        )
        with session_scope() as session:
            result = session.execute(text(sql))
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_upgrade_info(rows[0], keys)

    # Java: int insertSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo)
    def insert_sys_upgrade_info(self, entity: SysUpgradeInfo) -> int:
        """动态列插入；**不回写** ``entity.id``（XML 没有 ``useGeneratedKeys``）。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute in _INSERT_COLUMNS:
            value = getattr(entity, attribute)
            if value is None:
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        sql = f"insert into sys_upgrade_info ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo)
    def update_sys_upgrade_info(self, entity: SysUpgradeInfo) -> int:
        sql, params = _build_update_sql(entity)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteSysUpgradeInfoById(String id)
    def delete_sys_upgrade_info_by_id(self, id: Any) -> int:
        """软删除。Java 侧无控制器调用，照留。"""
        with session_scope() as session:
            result = session.execute(
                text("update sys_upgrade_info set del_flag = '1' where id = :id"), {"id": id}
            )
            return result.rowcount or 0

    # Java: int deleteSysUpgradeInfoByIds(String[] ids)
    def delete_sys_upgrade_info_by_ids(self, ids: Sequence[Any]) -> int:
        """软删除。``<foreach collection="array">`` —— 空数组会拼出 ``in ()``。"""
        clause, params = _in_clause("id", ids, "p")
        with session_scope() as session:
            result = session.execute(
                text(f"update sys_upgrade_info set del_flag = '1' where {clause}"), params
            )
            return result.rowcount or 0


def _build_upgrade_info_list_sql(entity: SysUpgradeInfo) -> Tuple[str, Dict[str, Any]]:
    """``selectSysUpgradeInfoList`` 的 ``where``；**自带** ``order by``（照抄）。

    ``where t.del_flag = '0'`` 与后面每个条件的 ``and`` 都是 XML 里写死的，所以这里
    条件片段**不带**前导 ``AND``，直接用 ``and`` 连接。
    """
    conditions: List[str] = ["t.del_flag = '0'"]
    params: Dict[str, Any] = {}

    # Java: <if test="x != null  and x != ''">and t.x = #{x}</if> —— 四个等值条件
    for attribute, column in (
        ("id", "t.id"),
        ("ver", "t.ver"),
        ("info", "t.info"),
        ("back_col1", "t.back_col1"),
    ):
        value = getattr(entity, attribute)
        if value is None or value == "":
            continue
        conditions.append(f"{column} = :{attribute}")
        params[attribute] = value

    # Java: <if test="x != null ">and t.x = #{x}</if> —— 三个只判 null 的条件
    for attribute, column in (
        ("eps_id", "t.eps_id"),
        ("tenant_id", "t.tenant_id"),
        ("create_by", "t.create_by"),
    ):
        value = getattr(entity, attribute)
        if value is None:
            continue
        conditions.append(f"{column} = :{attribute}")
        params[attribute] = value

    sql = (
        f"select {SELECT_SYS_UPGRADE_INFO_VO}\n"
        "from sys_upgrade_info t\n"
        "where " + "\nand ".join(conditions) + "\n"
        "order by t.create_time desc,t.id"
    )
    return sql, params


def _build_update_sql(entity: SysUpgradeInfo) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_upgrade_info set ... where id = :id``（Java: ``<trim prefix="SET">``）。

    ``<set>`` 全是 ``!= null``（**没有** ``!= ''`` 的特例），所以传空串会**清列**。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute in _UPDATE_COLUMNS:
        value = getattr(entity, attribute)
        if value is None:
            continue
        sets.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    params["id"] = entity.id
    sql = "update sys_upgrade_info set " + ",".join(sets) + " where id = :id"
    return sql, params


def _map_upgrade_info(row: Any, keys: Sequence[str]) -> SysUpgradeInfo:
    """One result row -> one ``SysUpgradeInfo`` (Java: ``resultMap="SysUpgradeInfoResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields: Dict[str, Any] = {}
    for label, value in values.items():
        attribute = _COLUMN_TO_FIELD.get(str(label).lower())
        if attribute is not None:
            fields[attribute] = value
    return SysUpgradeInfo(**fields)


__all__ = ["SysUpgradeInfoMapper", "SELECT_SYS_UPGRADE_INFO_VO"]
