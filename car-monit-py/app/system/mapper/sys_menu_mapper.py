"""菜单表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysMenuMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml

XML 里 **14 条 statement** 全在这里（11 个 ``<select>`` + 1 ``<insert>`` + 1 ``<update>`` +
1 ``<delete>``，另加 1 个 ``<sql>`` / 1 个 ``<resultMap>``）。按调用方分三组：

* 三个权限查询（``selectMenuPermsByUserId`` / ``selectMenuPermsByRoleId`` / ``selectMenuPerms``），
  其中**两个没有调用者**（见下）；
* 两个树查询（``selectMenuTreeAll`` / ``selectMenuTreeByUserId``），``GET /getRouters`` 用；
* 九个菜单管理语句，``SysMenuController`` 的 7 个端点用。

两个没有调用者的查询
--------------------
* ``<select id="selectMenuPerms">`` 连 ``where`` 都没有（会把全表 ``perms`` 拉出来）；
* ``<select id="selectMenuPermsByRoleId">`` 在 Java 的 ``SysMenuMapper`` **接口里没有对应方法**
  （接口只有 ``selectMenuPermsByUserId``），``ISysMenuService`` 也没有。

两条都是 XML 里的孤儿，Java 侧永远走不到。按迁移原则第 4 条照留、不删（§29.8）。

``insertMenu`` **没有** ``useGeneratedKeys``
------------------------------------------
其他模块的 ``insertXxx`` 都会回写主键，这条**不会**：新增菜单后 Java 侧拿不到
``menuId``。不要去补 ``result.lastrowid`` —— 补了就是行为改变（§29）。

``<if>`` 的判据是 OGNL，不是 ``isBlank``
-------------------------------------------
项目里的 ``string_utils.is_not_empty()`` 照抄 ``StringUtils.isEmpty``，它会先 ``trim``，
所以 ``is_not_empty(" ")`` 是 ``False``；而 XML 里写的是 ``x != null and x != ''``，
对单个空格是 ``True``。这里用 :func:`_text` —— 只判 ``None`` 与空串，**不 trim**。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_menu import SysMenu
from app.config.database import session_scope

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuPermsByUserId">``.
#: ``m.status = '0'`` (menu enabled) **and** ``r.status = '0'`` (role enabled) are both
#: required: disabling a role silently strips its menus from every session created afterwards.
_SELECT_MENU_PERMS_BY_USER_ID = """
        select distinct m.perms
        from sys_menu m
             left join sys_role_menu rm on m.menu_id = rm.menu_id
             left join sys_user_role ur on rm.role_id = ur.role_id
             left join sys_role r on r.role_id = ur.role_id
        where m.status = '0' and r.status = '0' and ur.user_id = :user_id
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuPermsByRoleId">``.
_SELECT_MENU_PERMS_BY_ROLE_ID = """
        select distinct m.perms
        from sys_menu m
             left join sys_role_menu rm on m.menu_id = rm.menu_id
        where m.status = '0' and rm.role_id = :role_id
"""

#: The column list both tree queries share, verbatim from the XML.
#: ``ifnull(m.perms,'')`` is why ``perms`` is never ``null`` on a tree row.
_TREE_COLUMNS = """
        select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible,
               m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type,
               m.icon, m.order_num, m.create_time
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuTreeAll">``.
#: Only directories (``M``) and menus (``C``) -- buttons never appear in the sidebar.
_SELECT_MENU_TREE_ALL = (
    _TREE_COLUMNS
    + """
        from sys_menu m where m.menu_type in ('M', 'C') and m.status = 0
        order by m.parent_id, m.order_num
"""
)

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuTreeByUserId">``.
#: ``ro.status = 0`` drops the menus of a disabled role; without it a disabled role would
#: keep contributing routes even though it no longer contributes permissions.
_SELECT_MENU_TREE_BY_USER_ID = (
    _TREE_COLUMNS
    + """
        from sys_menu m
             left join sys_role_menu rm on m.menu_id = rm.menu_id
             left join sys_user_role ur on rm.role_id = ur.role_id
             left join sys_role ro on ur.role_id = ro.role_id
             left join sys_user u on ur.user_id = u.user_id
        where u.user_id = :user_id and m.menu_type in ('M', 'C') and m.status = 0 and ro.status = 0
        order by m.parent_id, m.order_num
"""
)


#: Verbatim from SysMenuMapper.xml -> ``<sql id="selectMenuVo">``.
#: 列清单比 ``_TREE_COLUMNS`` 少一个 ``m.`` 前缀，其余完全一致，所以两者共用
#: :func:`_to_sys_menu` 做映射。
_SELECT_MENU_VO = """
        select menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, ifnull(perms,'') as perms, icon, create_time
        from sys_menu
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuPerms">``.
#: 没有 ``where``、也没有 ``status`` 过滤 —— 是上游遗留的死代码，见模块 docstring。
_SELECT_MENU_PERMS = """
        select distinct m.perms
        from sys_menu m
             left join sys_role_menu rm on m.menu_id = rm.menu_id
             left join sys_user_role ur on rm.role_id = ur.role_id
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuListByUserId">``.
#: 与 ``_SELECT_MENU_TREE_BY_USER_ID`` 的区别：没有 ``menu_type in ('M','C')``、
#: 没有 ``m.status = 0``、没有 ``ro.status = 0`` —— 这是**管理页**，要看得见停用菜单。
_SELECT_MENU_LIST_BY_USER_ID = (
    _TREE_COLUMNS
    + """
        from sys_menu m
        left join sys_role_menu rm on m.menu_id = rm.menu_id
        left join sys_user_role ur on rm.role_id = ur.role_id
        left join sys_role ro on ur.role_id = ro.role_id
        where ur.user_id = :user_id
"""
)

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuListByRoleId">``.
#: ``#{menuCheckStrictly}`` 是 **primitive boolean**，所以 ``<if>`` 里的真值判断有效
#: （与 ``sys_role`` 里那两个 ``Boolean`` 包类型不同，那里是死条件）。
_SELECT_MENU_LIST_BY_ROLE_ID = """
        select m.menu_id
        from sys_menu m
            left join sys_role_menu rm on m.menu_id = rm.menu_id
        where rm.role_id = :role_id
"""

#: ``<if test="menuCheckStrictly">`` 的真分支：剔除“父节点已勾选”的子节点。
_SELECT_MENU_LIST_BY_ROLE_ID_STRICTLY = """
              and m.menu_id not in (select m.parent_id from sys_menu m inner join sys_role_menu rm on m.menu_id = rm.menu_id and rm.role_id = :role_id)
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="selectMenuById">``.
_SELECT_MENU_BY_ID = _SELECT_MENU_VO + """
        where menu_id = :menu_id
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="hasChildByMenuId">``.
_HAS_CHILD_BY_MENU_ID = """
	    select count(1) from sys_menu where parent_id = :menu_id
"""

#: Verbatim from SysMenuMapper.xml -> ``<select id="checkMenuNameUnique">``.
#: ``limit 1`` 写在 SQL 里（不是内存截断）。
_CHECK_MENU_NAME_UNIQUE = _SELECT_MENU_VO + """
        where menu_name = :menu_name and parent_id = :parent_id limit 1
"""

#: ``updateMenu`` 的动态 ``<set>``，顺序与 XML 一致。第三项表示该列是否额外判
#: ``!= ''``（即 ``<if test="x != null and x != ''">``）。
#:
#: 注意三个**只判 null** 的列：``component`` / ``visible`` / ``status`` / ``perms`` ——
#: 传空串会把列清空，而其他列会被整列跳过。这个不对称是 Java 原文（§29）。
_UPDATE_MENU_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("menu_name", "menu_name", True),
    ("parent_id", "parent_id", False),
    ("order_num", "order_num", True),
    ("path", "path", True),
    ("component", "component", False),
    ("is_frame", "is_frame", True),
    ("is_cache", "is_cache", True),
    ("menu_type", "menu_type", True),
    ("visible", "visible", False),
    ("status", "status", False),
    ("perms", "perms", False),
    ("icon", "icon", True),
    ("remark", "remark", True),
    ("update_by", "update_by", True),
)

#: ``insertMenu`` 的动态列。``menu_id`` 带额外的 ``!= 0`` 校验，单独处理；
#: ``create_time`` 恒为 ``sysdate()``。
_INSERT_MENU_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("parent_id", "parent_id", False),
    ("menu_name", "menu_name", True),
    ("order_num", "order_num", True),
    ("path", "path", True),
    ("component", "component", True),
    ("is_frame", "is_frame", True),
    ("is_cache", "is_cache", True),
    ("menu_type", "menu_type", True),
    ("visible", "visible", False),
    ("status", "status", False),
    ("perms", "perms", True),
    ("icon", "icon", True),
    ("remark", "remark", True),
    ("create_by", "create_by", True),
)


class SysMenuMapper:
    """Java: ``interface SysMenuMapper`` (the permission subset)."""

    # Java: List<String> selectMenuPermsByUserId(Long userId)
    def select_menu_perms_by_user_id(self, user_id: int) -> List[str]:
        """One entry per distinct ``perms`` value; several values may be comma-separated.

        Splitting on commas is *not* done here -- it happens in
        :class:`~app.system.service.sys_menu_service.SysMenuService`, exactly as in Java.
        A menu row with an empty ``perms`` therefore comes back as ``""``.
        """
        with session_scope() as session:
            result = session.execute(text(_SELECT_MENU_PERMS_BY_USER_ID), {"user_id": user_id})
            return [row[0] for row in result.all()]

    # Java: 无（XML 有 <select id="selectMenuPermsByRoleId">，但 Mapper 接口没有这个方法）
    def select_menu_perms_by_role_id(self, role_id: int) -> List[str]:
        """**孤儿 statement**：XML 有、Java 接口没有，全项目无调用者。见模块 docstring。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_MENU_PERMS_BY_ROLE_ID), {"role_id": role_id})
            return [row[0] for row in result.all()]

    # Java: List<SysMenu> selectMenuTreeAll()
    def select_menu_tree_all(self) -> List[SysMenu]:
        """Every enabled ``M``/``C`` menu -- the admin branch of ``selectMenuTreeByUserId``."""
        with session_scope() as session:
            result = session.execute(text(_SELECT_MENU_TREE_ALL))
            return [_to_sys_menu(row) for row in result.mappings().all()]

    # Java: List<SysMenu> selectMenuTreeByUserId(Long userId)
    def select_menu_tree_by_user_id(self, user_id: int) -> List[SysMenu]:
        """Enabled ``M``/``C`` menus reachable through the user's **enabled** roles."""
        with session_scope() as session:
            result = session.execute(
                text(_SELECT_MENU_TREE_BY_USER_ID), {"user_id": user_id}
            )
            return [_to_sys_menu(row) for row in result.mappings().all()]

    # Java: List<SysMenu> selectMenuList(SysMenu menu)
    def select_menu_list(self, menu: SysMenu) -> List[SysMenu]:
        """管理页列表（不分页）。三个 ``<if>`` 全部**不做数据权限过滤**。

        与 ``selectMenuListByUserId`` 的区别只在“查谁”：这里是全表，那里是某个用户
        通过角色能看到的。控制器根据 ``userId == 1`` 二选一（见 service）。
        """
        clauses, params = _menu_filters(menu, alias="")
        sql = _SELECT_MENU_VO + _where(clauses) + "        order by parent_id, order_num\n"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return [_to_sys_menu(row) for row in result.mappings().all()]

    # Java: List<SysMenu> selectMenuListByUserId(SysMenu menu)
    def select_menu_list_by_user_id(self, menu: SysMenu) -> List[SysMenu]:
        """非超管的管理页列表。``userId`` 从 ``menu.params['userId']`` 来。

        Java 侧由 ``SysMenuServiceImpl`` 写进去：``menu.getParams().put("userId", userId)``，
        XML 用 ``#{params.userId}`` 读。**不**过 ``menu.user_id`` 这样的字段。
        """
        clauses, params = _menu_filters(menu, alias="m.")
        params["user_id"] = menu.params.get("userId")
        sql = (
            _SELECT_MENU_LIST_BY_USER_ID
            + _where(clauses)
            + "        order by m.parent_id, m.order_num\n"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return [_to_sys_menu(row) for row in result.mappings().all()]

    # Java: List<Integer> selectMenuListByRoleId(@Param("roleId") Long roleId, @Param("menuCheckStrictly") boolean menuCheckStrictly)
    def select_menu_list_by_role_id(
        self, role_id: int, menu_check_strictly: bool
    ) -> List[int]:
        """角色已勾选的菜单 id。

        ``menu_check_strictly`` 为真时把“父节点已勾选”的子节点剔除，让前端树只勾叶子。
        注意它是 primitive ``boolean``（不可能为 ``null``），所以只需判真假，
        不像 ``sys_role`` 里的 ``menuCheckStrictly`` 那样永远参与 SQL。
        """
        sql = _SELECT_MENU_LIST_BY_ROLE_ID
        if menu_check_strictly:
            sql += _SELECT_MENU_LIST_BY_ROLE_ID_STRICTLY
        sql += "        order by m.parent_id, m.order_num\n"
        with session_scope() as session:
            result = session.execute(text(sql), {"role_id": role_id})
            return [row[0] for row in result.all()]

    # Java: List<String> selectMenuPerms()
    def select_menu_perms(self) -> List[str]:
        """全表 ``perms``（去重）。**没有任何调用者** —— 见模块 docstring。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_MENU_PERMS))
            return [row[0] for row in result.all()]

    # Java: SysMenu selectMenuById(Long menuId)
    def select_menu_by_id(self, menu_id: int) -> Optional[SysMenu]:
        """无行返回 ``None``（MyBatis 单行查询也是 ``null``）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_MENU_BY_ID), {"menu_id": menu_id})
            row = result.mappings().first()
            return None if row is None else _to_sys_menu(row)

    # Java: int hasChildByMenuId(Long menuId)
    def has_child_by_menu_id(self, menu_id: int) -> int:
        with session_scope() as session:
            return int(
                session.execute(text(_HAS_CHILD_BY_MENU_ID), {"menu_id": menu_id}).scalar() or 0
            )

    # Java: SysMenu checkMenuNameUnique(@Param("menuName") String menuName, @Param("parentId") Long parentId)
    def check_menu_name_unique(
        self, menu_name: Optional[str], parent_id: Optional[int]
    ) -> Optional[SysMenu]:
        """判重只在**同一父节点**下做；不同目录下可以有同名菜单。"""
        with session_scope() as session:
            result = session.execute(
                text(_CHECK_MENU_NAME_UNIQUE),
                {"menu_name": menu_name, "parent_id": parent_id},
            )
            row = result.mappings().first()
            return None if row is None else _to_sys_menu(row)

    # Java: int insertMenu(SysMenu menu)
    def insert_menu(self, menu: SysMenu) -> int:
        """动态列插入。

        **没有** ``useGeneratedKeys``，所以**不**回写 ``menu.menu_id`` —— 与其它模块的
        ``insertXxx`` 不同，这里不要补 ``result.lastrowid``。
        """
        columns: List[str] = []
        values: List[str] = []
        params: Dict[str, Any] = {}

        # Java: <if test="menuId != null and menuId != 0">menu_id,</if>
        if menu.menu_id is not None and menu.menu_id != 0:
            columns.append("menu_id")
            values.append(":menu_id")
            params["menu_id"] = menu.menu_id

        for attribute, column, require_text in _INSERT_MENU_COLUMNS:
            value = getattr(menu, attribute)
            if value is None:
                continue
            # Java: parentId 额外判 != 0 —— 父 id 为 0（根）时整列跳过。
            if attribute == "parent_id" and value == 0:
                continue
            if require_text and value == "":
                continue
            columns.append(column)
            values.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        values.append("sysdate()")

        sql = f"insert into sys_menu({','.join(columns)})values({','.join(values)})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateMenu(SysMenu menu)
    def update_menu(self, menu: SysMenu) -> int:
        """动态 ``<set>``；``update_time = sysdate()`` 恒在最后。

        列清单见 :data:`_UPDATE_MENU_COLUMNS` —— ``component`` / ``visible`` / ``status`` /
        ``perms`` 只判 ``null``，传空串会**清列**（§29）。
        """
        assignments: List[str] = []
        params: Dict[str, Any] = {}
        for attribute, column, require_text in _UPDATE_MENU_COLUMNS:
            value = getattr(menu, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            assignments.append(f"{column} = :{attribute}")
            params[attribute] = value

        # XML 里最后一行无条件： ``update_time = sysdate()``
        assignments.append("update_time = sysdate()")
        params["menu_id"] = menu.menu_id

        sql = "update sys_menu set " + ", ".join(assignments) + " where menu_id = :menu_id"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteMenuById(Long menuId)
    def delete_menu_by_id(self, menu_id: int) -> int:
        """**物理删除**（``sys_menu`` 没有 ``del_flag``，与 ``sys_dept`` 不同）。"""
        with session_scope() as session:
            result = session.execute(
                text("delete from sys_menu where menu_id = :menu_id"), {"menu_id": menu_id}
            )
            return result.rowcount or 0


def _text(value: Any) -> bool:
    """Java: ``x != null and x != ''`` —— **不** trim（与 ``is_not_empty`` 相反）。"""
    return value is not None and value != ""


def _string(value: Any) -> Optional[str]:
    """Java: ``ResultSet.getString(column)`` —— 任何列类型都转成字符串。

    本库的 ``sys_menu.is_frame`` / ``is_cache`` 是 ``int``，而 Java 实体声明的是
    ``String``：MyBatis 的 ``resultMap`` 按属性类型选 ``StringTypeHandler``，
    它调的是 ``rs.getString()``，所以 JDBC 把 ``1`` 读成 ``"1"``。
    pydantic 不做这种隐式转换，必须在这里显式还原（真实数据库联调时发现）。
    """
    return None if value is None else str(value)


def _menu_filters(menu: SysMenu, alias: str) -> Tuple[List[str], Dict[str, Any]]:
    """``selectMenuList`` / ``selectMenuListByUserId`` 共用的三个 ``<if>``。

    顺序与 XML 一致（``menuName`` -> ``visible`` -> ``status``）；``alias`` 是表别名前缀
    （``""`` 或 ``"m."``）。``<where>`` 会吃掉开头的 ``AND``，所以这里只存条件本体。
    """
    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if _text(menu.menu_name):
        clauses.append(f"{alias}menu_name like concat('%', :menu_name, '%')")
        params["menu_name"] = menu.menu_name
    if _text(menu.visible):
        clauses.append(f"{alias}visible = :visible")
        params["visible"] = menu.visible
    if _text(menu.status):
        clauses.append(f"{alias}status = :status")
        params["status"] = menu.status
    return clauses, params


def _where(clauses: List[str]) -> str:
    """``<where>`` 的等价物：无条件时什么都不输出（不是 ``where 1=1``）。"""
    if not clauses:
        return ""
    return "        where " + "\n          AND ".join(clauses) + "\n"


def _to_sys_menu(row: Mapping[str, Any]) -> SysMenu:
    """Row -> entity, mirroring ``<resultMap id="SysMenuResult">``.

    Only the columns in ``_TREE_COLUMNS`` are mapped; ``parent_name`` and the
    ``BaseEntity`` audit fields other than ``create_time`` are simply absent from the
    result set, so they stay ``None`` -- exactly what MyBatis does.
    """
    return SysMenu(
        menu_id=row["menu_id"],
        parent_id=row["parent_id"],
        menu_name=row["menu_name"],
        path=row["path"],
        component=row["component"],
        visible=row["visible"],
        status=row["status"],
        perms=row["perms"],
        # int 列 -> String 属性：等价于 JDBC ``getString``，见 :func:`_string`。
        is_frame=_string(row["is_frame"]),
        is_cache=_string(row["is_cache"]),
        menu_type=row["menu_type"],
        icon=row["icon"],
        order_num=row["order_num"],
        create_time=row["create_time"],
    )


__all__ = ["SysMenuMapper"]