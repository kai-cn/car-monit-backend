"""用户常用菜单表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysIndexMenuMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysIndexMenuMapper.xml

XML 里共 8 条 statement，本模块**全部迁移**（``deleteSysIndexMenuById`` 在 Java 侧
没有任何控制器调用，但按迁移原则第 4 条照留）。

列名大小写是"混着写"的
----------------------
这张表的列在 XML 里全大写（``ID`` / ``USER_ID`` / ``MENU_ID`` / ``DEL_FLAG`` …），
唯独 ``getList`` 里用 ``t.id``、``t.MENU_ID``、``t.USER_ID`` 混写，``sys_menu`` 那侧
又是小写（``t1.menu_id``）。MySQL 在 Linux 上列名不区分大小写，所以能跑；照抄，
不要"统一大小写" —— 那会让 SQL 文本与 Java 侧对不上。

``selectSysIndexMenuList`` 的两个特殊点
---------------------------------------
1. **不是单表查询**：``from sys_menu t1, sys_menu t2``（隐式笛卡尔 + ``where`` 关联），
   投影只有 3 列且**列名是别名或原名**：``t2.menu_name as menuName2`` / ``t1.menu_id`` /
   ``t1.menu_name``。``resultMap`` 里 ``menuName2`` 这个 property 就靠这个别名。
2. **自带 ``order by``**（``t2.parent_id,t2.order_num,t1.order_num,t1.menu_id``），
   所以分页不会追加客户端排序列（见 :mod:`app.common.core.page.page_helper` 的
   ``_has_order_by`` 分支）。

``userId != 1`` 这个 ``<if>``
----------------------------
判据是 **OGNL 的 ``!=``**（不是 ``!= null``）：

* ``userId == 1``（超管）→ 条件**不生效**，返回所有人的候选菜单；
* 其它值（含 ``null``）→ 条件生效，用 ``exists`` 只保留"该用户有角色授权"的菜单。

``#{userId}`` 在 ``userId`` 为 ``null`` 时会绑定成 SQL ``NULL``（``exists`` 恒假）。
Java 侧一样；service 总会先 ``setUserId(getUserId())``，所以正常路径不会是 ``null``。

``getList`` 的 ``limit 9``
--------------------------
"我常用的菜单"固定取 9 条（前端九宫格）。这条语句**不进 ``resultMap`` 之外的映射**，
``menuUrl`` 是 ``concat(t2.path,'/',t1.path)`` 现算的。控制器**不**调 ``startPage()``，
所以分页参数对它不起作用（``take_page()`` 返回 ``None`` 即可）。

``insertSysIndexMenu`` 不回写主键
--------------------------------
``<trim>`` 拼的是动态列，且**没有** ``useGeneratedKeys``。主键 ``id`` 是 UUID，由
service 侧 ``StringUtils.getUUID()`` 先生成好再放进来（见 service），不是数据库生成。

``deleteSysIndexMenuById`` / ``ByIds`` 是**软删除**
--------------------------------------------------
两条都是 ``update ... set del_flag = '1'``。**没有**真正的物理删除，
除 ``deleteByMenuUserId``（``delete from``，供 ``insertSysIndexMenu`` 先删后插用）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysIndexMenuMapper.xml -> ``<sql id="selectSysIndexMenuVo">``.
SELECT_SYS_INDEX_MENU_VO = (
    " t.ID, t.USER_ID, t.MENU_ID, t.SORT, t.EPS_ID, t.DEL_FLAG, t.CREATE_BY, "
    "t.CREATE_TIME, t.UPDATE_BY, t.UPDATE_TIME, t.TENANT_ID "
)

#: ``insertSysIndexMenu`` 的 ``<trim>`` 分支，顺序与 XML 一致；全部 ``!= null``。
_INSERT_COLUMNS: Tuple[str, ...] = (
    "id",
    "user_id",
    "menu_id",
    "sort",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``_INSERT_COLUMNS`` / ``_UPDATE_COLUMNS`` 里的属性名 -> XML 里的列名（大写，照抄）。
_INSERT_COLUMN_NAMES: Dict[str, str] = {
    "id": "ID",
    "user_id": "USER_ID",
    "menu_id": "MENU_ID",
    "sort": "SORT",
    "eps_id": "EPS_ID",
    "del_flag": "DEL_FLAG",
    "create_by": "CREATE_BY",
    "create_time": "CREATE_TIME",
    "update_by": "UPDATE_BY",
    "update_time": "UPDATE_TIME",
    "tenant_id": "TENANT_ID",
}

#: ``updateSysIndexMenu`` 的 ``<trim>`` 分支，顺序与 XML 一致；全部 ``!= null``。
#: **没有** ``id``（它在 ``where`` 里）。
_UPDATE_COLUMNS: Tuple[str, ...] = (
    "user_id",
    "menu_id",
    "sort",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``resultMap="SysIndexMenuResult"`` 的列 -> 属性。键是**小写**列名/别名。
#: ``menuName2`` / ``menuUrl`` 是 SQL 里显式起的别名（camelCase），其余是原名。
_COLUMN_TO_FIELD: Dict[str, str] = {
    "id": "id",
    "user_id": "user_id",
    "menu_id": "menu_id",
    "sort": "sort",
    "eps_id": "eps_id",
    "del_flag": "del_flag",
    "create_by": "create_by",
    "create_time": "create_time",
    "update_by": "update_by",
    "update_time": "update_time",
    "tenant_id": "tenant_id",
    "menu_name": "menu_name",
    "menuname2": "menu_name2",
    "menuurl": "menu_url",
}

#: ``selectSysIndexMenuList`` 的投影列（顺序即 SQL 的选择顺序）。
_LIST_COLUMNS: Tuple[str, ...] = ("menuName2", "menu_id", "menu_name")


class SysIndexMenuMapper:
    """Java: ``interface SysIndexMenuMapper``."""

    # Java: SysIndexMenu selectSysIndexMenuById(Long id)
    def select_sys_index_menu_by_id(self, id: Any) -> Optional[SysIndexMenu]:
        sql = f"select {SELECT_SYS_INDEX_MENU_VO} from sys_index_menu t where t.ID = :id"
        with session_scope() as session:
            result = session.execute(text(sql), {"id": id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_index_menu(rows[0], keys)

    # Java: List<SysIndexMenu> selectSysIndexMenuList(SysIndexMenu sysIndexMenu)
    def select_sys_index_menu_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        """控制器在调用前已 ``startPage()``，分页点在这条 select 上。"""
        data_sql, params = _build_index_menu_list_sql(entity)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_index_menu(row, list(_LIST_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<SysIndexMenu> getList(SysIndexMenu sysIndexMenu)
    def get_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        """常用菜单九宫格。自带 ``limit 9``；**不**受 ``startPage()`` 影响。"""
        sql = (
            "select t.id,t1.menu_name,concat(t2.path,'/',t1.path) as menuUrl\n"
            "from SYS_INDEX_MENU t\n"
            "left join sys_menu t1 on t.MENU_ID = t1.menu_id\n"
            "left join sys_menu t2 on t1.parent_id = t2.menu_id\n"
            "where t.del_flag='0'\n"
            "and t.USER_ID = :user_id\n"
            "order by t.CREATE_TIME desc\n"
            "limit 9"
        )
        with session_scope() as session:
            result = session.execute(text(sql), {"user_id": entity.user_id})
            keys = list(result.keys())
            rows = result.all()
        return [_map_index_menu(row, keys) for row in rows]

    # Java: int insertSysIndexMenu(SysIndexMenu sysIndexMenu)
    def insert_sys_index_menu(self, entity: SysIndexMenu) -> int:
        """动态列插入；**不回写** ``entity.id``（XML 没有 ``useGeneratedKeys``）。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute in _INSERT_COLUMNS:
            value = getattr(entity, attribute)
            if value is None:
                continue
            columns.append(_INSERT_COLUMN_NAMES[attribute])
            names.append(f":{attribute}")
            params[attribute] = value

        sql = f"insert into sys_index_menu ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateSysIndexMenu(SysIndexMenu sysIndexMenu)
    def update_sys_index_menu(self, entity: SysIndexMenu) -> int:
        sql, params = _build_update_sql(entity)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteSysIndexMenuById(Long id)
    def delete_sys_index_menu_by_id(self, id: Any) -> int:
        """软删除：``update ... set del_flag = '1'``。"""
        with session_scope() as session:
            result = session.execute(
                text("update sys_index_menu set del_flag = '1' where ID = :id"), {"id": id}
            )
            return result.rowcount or 0

    # Java: int deleteSysIndexMenuByIds(Long[] ids)
    def delete_sys_index_menu_by_ids(self, ids: Sequence[Any]) -> int:
        """软删除。``<foreach collection="array">`` —— 空数组会拼出 ``in ()``。"""
        clause, params = _in_clause("ID", ids, "p")
        with session_scope() as session:
            result = session.execute(
                text(f"update sys_index_menu set del_flag = '1' where {clause}"), params
            )
            return result.rowcount or 0

    # Java: int deleteByMenuUserId(SysIndexMenu sysIndexMenu)
    def delete_by_menu_user_id(self, entity: SysIndexMenu) -> int:
        """**物理**删除 —— 供 ``insertSysIndexMenu`` "先删后插"用。"""
        with session_scope() as session:
            result = session.execute(
                text("delete from sys_index_menu where menu_id = :menu_id and user_id = :user_id"),
                {"menu_id": entity.menu_id, "user_id": entity.user_id},
            )
            return result.rowcount or 0


#: ``_INSERT_COLUMNS`` / ``_UPDATE_COLUMNS`` 里的属性名 -> XML 里的列名（大写，照抄）。
#: ``selectSysIndexMenuVo`` 的列清单与之一一对应。
_UPDATE_COLUMN_NAMES = _INSERT_COLUMN_NAMES


def _build_index_menu_list_sql(entity: SysIndexMenu) -> Tuple[str, Dict[str, Any]]:
    """``selectSysIndexMenuList`` 的 ``where``；**自带** ``order by``（照抄）。

    这条语句**没有** ``<where>`` 标签 —— ``where`` 和 ``and`` 都是**硬编码**的，
    所以拼接方式与其它模块不同：直接按 XML 的行顺序 ``and`` 连起来即可。
    """
    # Java: 前三行无条件生效
    conditions: List[str] = [
        "t1.menu_type='C'",
        "t1.visible = '0'",
        "t2.menu_id = t1.parent_id",
    ]
    params: Dict[str, Any] = {"user_id": entity.user_id}

    # Java: <if test="userId != 1 "> —— OGNL 的 != 对 null 也成立，所以只有 1 被排除
    if entity.user_id != 1:
        conditions.append(
            "exists (select 1 from sys_role_menu rm,sys_user_role ur "
            "where rm.role_id = ur.role_id and rm.menu_id = t1.menu_id "
            "and ur.user_id = :user_id)"
        )

    conditions.append(
        "not exists (select 1 from sys_index_menu tim where tim.del_flag = '0' "
        "and tim.menu_id = t1.menu_id and tim.user_id = :user_id)"
    )
    conditions.append(
        "not exists (select 1 from sys_menu t3 where t3.menu_type = 'C' "
        "and t3.parent_id = t1.menu_id)"
    )

    # Java: <if test="menuName != null and menuName != ''">
    if entity.menu_name is not None and entity.menu_name != "":
        conditions.append("t1.menu_name like concat('%',:menu_name,'%')")
        params["menu_name"] = entity.menu_name
    # Java: <if test="menuName2 != null and menuName2 != ''">
    if entity.menu_name2 is not None and entity.menu_name2 != "":
        conditions.append("t2.menu_name like concat('%',:menu_name2,'%')")
        params["menu_name2"] = entity.menu_name2

    sql = (
        "select t2.menu_name as menuName2,t1.menu_id,t1.menu_name\n"
        "from sys_menu t1, sys_menu t2\n"
        "where " + "\nand ".join(conditions) + "\n"
        "order by  t2.parent_id,t2.order_num,t1.order_num,t1.menu_id"
    )
    return sql, params


def _build_update_sql(entity: SysIndexMenu) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_index_menu set ... where ID = :id``（Java: ``<trim prefix="SET">``）。"""
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute in _UPDATE_COLUMNS:
        value = getattr(entity, attribute)
        if value is None:
            continue
        sets.append(f"{_UPDATE_COLUMN_NAMES[attribute]} = :{attribute}")
        params[attribute] = value

    params["id"] = entity.id
    sql = "update sys_index_menu set " + ",".join(sets) + " where ID = :id"
    return sql, params


def _map_index_menu(row: Any, keys: Sequence[str]) -> SysIndexMenu:
    """One result row -> one ``SysIndexMenu`` (Java: ``resultMap="SysIndexMenuResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields: Dict[str, Any] = {}
    for label, value in values.items():
        attribute = _COLUMN_TO_FIELD.get(str(label).lower())
        if attribute is not None:
            fields[attribute] = value
    return SysIndexMenu(**fields)


__all__ = ["SysIndexMenuMapper", "SELECT_SYS_INDEX_MENU_VO"]