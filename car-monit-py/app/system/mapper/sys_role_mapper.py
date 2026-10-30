"""角色表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml

迁移范围：权限切片（``selectRolePermissionByUserId``）加上 ``sys_user`` 管理页需要的
四条——``selectRoleList`` / ``selectRoleAll`` / ``selectRoleListByUserId`` /
``selectRolesByUserName``，以及 ``selectRoleById``；``sys_role`` 切片又补齐了
``checkRoleNameUnique`` / ``checkRoleKeyUnique`` / ``insertRole`` / ``updateRole`` /
``deleteRoleById`` / ``deleteRoleByIds``。至此 ``SysRoleMapper.xml`` 里 12 条语句全部
落地（其中 ``selectRoleAll`` 在 Java 里没有任何调用者，属保留）。

``${params.dataScope}``
---------------------
``selectRoleList`` 里有一句 ``${params.dataScope}``（**未被注释**，与
``SysUserMapper.xml`` 的 ``selectUserList`` 不同）。它的值由 ``@DataScope`` 切面写入入参
实体，见 :mod:`app.framework.aspectj.data_scope_aspect`。因此本方法必须先由 Service 调用
``apply_data_scope``，否则拼接出来的就是空串——与"切面未生效"的 Java 结果一致。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope

#: Verbatim from SysRoleMapper.xml -> ``<sql id="selectRoleVo">``.
#: ``distinct`` matters: the fragment joins ``sys_user_role`` and ``sys_user``, so a role
#: shared by two users would otherwise appear once per user.
_SELECT_ROLE_VO = """
    select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope, r.menu_check_strictly, r.dept_check_strictly,
                    r.status, r.del_flag, r.create_time, r.remark
    from sys_role r
        left join sys_user_role ur on ur.role_id = r.role_id
        left join sys_user u on u.user_id = ur.user_id
        left join sys_dept d on u.dept_id = d.dept_id
"""

#: ``selectRoleVo`` 的 11 列，顺序与 ``resultMap="SysRoleResult"`` 一致。
#: 分页查询不能从 CursorResult 取 keys（``select_page`` 只回 row），所以写死。
_ROLE_COLUMNS: Tuple[str, ...] = (
    "role_id",
    "role_name",
    "role_key",
    "role_sort",
    "data_scope",
    "menu_check_strictly",
    "dept_check_strictly",
    "status",
    "del_flag",
    "create_time",
    "remark",
)

#: Verbatim from SysRoleMapper.xml -> ``<select id="selectRolePermissionByUserId">``.
#: ``r.del_flag = '0'`` -- a soft-deleted role grants nothing.
_SELECT_ROLE_PERMISSION_BY_USER_ID = _SELECT_ROLE_VO + """
        WHERE r.del_flag = '0' and ur.user_id = :user_id
"""

#: Verbatim from SysRoleMapper.xml -> ``<select id="selectRoleAll">``.
_SELECT_ROLE_ALL = _SELECT_ROLE_VO

#: Verbatim from SysRoleMapper.xml -> ``<select id="selectRoleListByUserId">``.
_SELECT_ROLE_LIST_BY_USER_ID = """
		select r.role_id
        from sys_role r
	        left join sys_user_role ur on ur.role_id = r.role_id
	        left join sys_user u on u.user_id = ur.user_id
	    where u.user_id = :user_id
"""

#: Verbatim from SysRoleMapper.xml -> ``<select id="selectRolesByUserName">``.
_SELECT_ROLES_BY_USER_NAME = _SELECT_ROLE_VO + """
        WHERE r.del_flag = '0' and u.user_name = :user_name
"""

#: Verbatim from SysRoleMapper.xml -> ``<select id="selectRoleById">``.
_SELECT_ROLE_BY_ID = _SELECT_ROLE_VO + """
        where r.role_id = :role_id
"""

#: Verbatim from SysRoleMapper.xml -> ``<select id="checkRoleNameUnique">``.
#: ``limit 1`` 写在 XML 里，**不是**分页插件加的；也不过滤 ``del_flag``，
#: 所以已删除角色仍会占住名称（Java 原样）。
_CHECK_ROLE_NAME_UNIQUE = _SELECT_ROLE_VO + """
		 where r.role_name=:role_name limit 1
"""

#: Verbatim from SysRoleMapper.xml -> ``<select id="checkRoleKeyUnique">``.
_CHECK_ROLE_KEY_UNIQUE = _SELECT_ROLE_VO + """
		 where r.role_key=:role_key limit 1
"""

#: Verbatim from SysRoleMapper.xml -> ``<delete id="deleteRoleById">``.
#: 名为 delete，实际是**软删除**：``del_flag = '2'``。
_DELETE_ROLE_BY_ID = """
		update sys_role set del_flag = '2' where role_id = :role_id
"""


class SysRoleMapper:
    """Java: ``interface SysRoleMapper``（XML 里 12 条语句全部在此）。"""

    # Java: List<SysRole> selectRolePermissionByUserId(Long userId)
    def select_role_permission_by_user_id(self, user_id: int) -> List[SysRole]:
        """All non-deleted roles of one user, mapped like ``resultMap="SysRoleResult"``."""
        with session_scope() as session:
            result = session.execute(text(_SELECT_ROLE_PERMISSION_BY_USER_ID), {"user_id": user_id})
            keys = list(result.keys())
            return [_map_role(row, keys) for row in result.all()]

    # Java: List<SysRole> selectRoleAll()
    def select_role_all(self) -> List[SysRole]:
        """全部角色（**不**过滤 ``del_flag``，Java 原样如此）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_ROLE_ALL))
            keys = list(result.keys())
            return [_map_role(row, keys) for row in result.all()]

    # Java: List<Integer> selectRoleListByUserId(Long userId)
    def select_role_list_by_user_id(self, user_id: int) -> List[int]:
        """返回的是**角色 id 列表**（``resultType="Integer"``），给下拉框回显用。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_ROLE_LIST_BY_USER_ID), {"user_id": user_id})
            return [row[0] for row in result.all()]

    # Java: List<SysRole> selectRolesByUserName(String userName)
    def select_roles_by_user_name(self, user_name: str) -> List[SysRole]:
        with session_scope() as session:
            result = session.execute(text(_SELECT_ROLES_BY_USER_NAME), {"user_name": user_name})
            keys = list(result.keys())
            return [_map_role(row, keys) for row in result.all()]

    # Java: SysRole selectRoleById(Long roleId)
    def select_role_by_id(self, role_id: int) -> Optional[SysRole]:
        with session_scope() as session:
            result = session.execute(text(_SELECT_ROLE_BY_ID), {"role_id": role_id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_role(rows[0], keys)

    # Java: SysRole checkRoleNameUnique(String roleName)
    def check_role_name_unique(self, role_name: str) -> Optional[SysRole]:
        """按名称查一行（Java 返回 ``SysRole``，不是计数）。

        结果里一定带 ``role_id``，Service 靠它区分"重名的那条是不是自己"。
        """
        with session_scope() as session:
            result = session.execute(text(_CHECK_ROLE_NAME_UNIQUE), {"role_name": role_name})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_role(rows[0], keys)

    # Java: SysRole checkRoleKeyUnique(String roleKey)
    def check_role_key_unique(self, role_key: str) -> Optional[SysRole]:
        with session_scope() as session:
            result = session.execute(text(_CHECK_ROLE_KEY_UNIQUE), {"role_key": role_key})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_role(rows[0], keys)

    # Java: int insertRole(SysRole role)
    def insert_role(self, role: SysRole) -> int:
        """新增角色，``useGeneratedKeys="true" keyProperty="roleId"``。

        列清单完全由 ``<if>`` 决定，顺序与 XML 一致。两个特殊点：

        * ``roleId != null and roleId != 0`` —— 传 0 与传 ``null`` 一样都会被跳过；
        * ``menuCheckStrictly != null`` / ``deptCheckStrictly != null`` —— 字段是
          **primitive boolean**，OGNL 装箱后永远不为 ``null``，所以这两列**必定**参与
          insert（值只能是 0/1）。别“优化”成条件列。

        ``create_time`` 恒为 ``sysdate()``，不走参数。生成的主键写回 ``role.role_id``
        （MyBatis 的 ``Jdbc3KeyGenerator`` 同样是直接 set 到实体上）。
        """
        columns: List[str] = []
        values: List[str] = []
        params: Dict[str, Any] = {}

        if role.role_id is not None and role.role_id != 0:
            columns.append("role_id")
            values.append(":role_id")
            params["role_id"] = role.role_id
        for column, attribute in (
            ("role_name", "role_name"),
            ("role_key", "role_key"),
            ("role_sort", "role_sort"),
            ("data_scope", "data_scope"),
        ):
            value = getattr(role, attribute)
            if _text(value):
                columns.append(column)
                values.append(f":{attribute}")
                params[attribute] = value
        # Java: <if test="menuCheckStrictly != null"> —— primitive boolean，永不跳过
        columns.extend(["menu_check_strictly", "dept_check_strictly"])
        values.extend([":menu_check_strictly", ":dept_check_strictly"])
        params["menu_check_strictly"] = 1 if role.menu_check_strictly else 0
        params["dept_check_strictly"] = 1 if role.dept_check_strictly else 0
        for column, attribute in (
            ("status", "status"),
            ("remark", "remark"),
            ("create_by", "create_by"),
        ):
            value = getattr(role, attribute)
            if _text(value):
                columns.append(column)
                values.append(f":{attribute}")
                params[attribute] = value

        sql = (
            f"insert into sys_role({', '.join(columns)}, create_time) "
            f"values({', '.join(values)}, sysdate())"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            generated = result.lastrowid
            rows = result.rowcount or 0
        # Java: useGeneratedKeys -> keyProperty="roleId"
        if generated is not None:
            role.role_id = int(generated)
        return rows

    # Java: int updateRole(SysRole role)
    def update_role(self, role: SysRole) -> int:
        """动态 ``<set>`` 更新。

        两条容易看错的判据：

        * ``role_name`` / ``role_key`` / ``role_sort`` / ``data_scope`` / ``status`` /
          ``update_by`` 是 ``!= null and != ''``，空串**不会**覆盖旧值；
        * ``remark`` 只有 ``!= null``，所以**空串会把备注清空**。

        ``menu_check_strictly`` / ``dept_check_strictly`` 同 ``insert_role``：primitive
        boolean，必定参与更新。``update_time`` 恒为 ``sysdate()``。
        """
        sets: List[str] = []
        params: Dict[str, Any] = {}

        for column, attribute in (
            ("role_name", "role_name"),
            ("role_key", "role_key"),
            ("role_sort", "role_sort"),
            ("data_scope", "data_scope"),
        ):
            value = getattr(role, attribute)
            if _text(value):
                sets.append(f"{column} = :{attribute}")
                params[attribute] = value
        # Java: <if test="menuCheckStrictly != null"> —— primitive boolean，永不跳过
        sets.extend(["menu_check_strictly = :menu_check_strictly", "dept_check_strictly = :dept_check_strictly"])
        params["menu_check_strictly"] = 1 if role.menu_check_strictly else 0
        params["dept_check_strictly"] = 1 if role.dept_check_strictly else 0
        if _text(role.status):
            sets.append("status = :status")
            params["status"] = role.status
        # Java: <if test="remark != null"> —— 没有 != ''，空串会真的写进去
        if role.remark is not None:
            sets.append("remark = :remark")
            params["remark"] = role.remark
        if _text(role.update_by):
            sets.append("update_by = :update_by")
            params["update_by"] = role.update_by
        sets.append("update_time = sysdate()")

        params["role_id"] = role.role_id
        sql = f"update sys_role set {', '.join(sets)} where role_id = :role_id"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return result.rowcount or 0

    # Java: int deleteRoleById(Long roleId)
    def delete_role_by_id(self, role_id: int) -> int:
        """软删除单个角色（``del_flag = '2'``），关联表由 Service 负责。"""
        with session_scope() as session:
            result = session.execute(text(_DELETE_ROLE_BY_ID), {"role_id": role_id})
            return result.rowcount or 0

    # Java: int deleteRoleByIds(Long[] roleIds)
    def delete_role_by_ids(self, role_ids: Sequence[int]) -> int:
        """批量软删除。<foreach> 展开成 ``in (:p0, :p1, ...)``，空数组生成
        ``in ()`` 由 MySQL 报语法错 —— 与 Java 一致。"""
        clause, params = _in_clause("role_id", role_ids, "p")
        sql = f"update sys_role set del_flag = '2' where {clause}"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            return result.rowcount or 0

    # Java: List<SysRole> selectRoleList(SysRole role)
    def select_role_list(self, role: Optional[SysRole] = None) -> List[SysRole]:
        """按条件查角色，``order by r.role_sort``（分页点在这里）。

        ``${params.dataScope}`` 原样插入 —— 调用方（Service）必须先跑过
        ``apply_data_scope``，否则这里拿到的是空串，与切面未生效时的 Java 一致。
        注意 ``selectRoleVo`` 自带 ``distinct``，因为片段 join 了 ``sys_user_role``。

        分页：``SysRoleController#list`` 调了 ``startPage()``，所以这条 select 是
        PageHelper 的拦截对象 —— 必须 ``take_page()`` 并走 :func:`select_page`，
        否则 ``GET /system/role/list`` 会返回全表（``total`` 变成行数）。
        语句自带 ``order by``，因此客户端点表头传的 ``orderByColumn`` 会被忽略，
        见 ``COMPATIBILITY.md`` §25.6。
        """
        role = role or SysRole()
        where: List[str] = ["where r.del_flag = '0'"]
        params: Dict[str, Any] = {}

        if _text(role.role_name):
            where.append("AND r.role_name like concat('%', :role_name, '%')")
            params["role_name"] = role.role_name
        if _text(role.status):
            where.append("AND r.status = :status")
            params["status"] = role.status
        if _text(role.role_key):
            where.append("AND r.role_key =  :role_key")
            params["role_key"] = role.role_key
        begin_time = role.params.get("beginTime")
        if _text(begin_time):
            where.append("and date_format(r.create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')")
            params["begin_time"] = begin_time
        end_time = role.params.get("endTime")
        if _text(end_time):
            where.append("and date_format(r.create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')")
            params["end_time"] = end_time

        # <!-- 数据范围过滤 --> ${params.dataScope}  —— 唯一合法的 ${} 拼接点
        data_scope = role.params.get("dataScope") or ""
        clause = "\n".join(where) + "\n" + data_scope + "\n\t\torder by r.role_sort"
        data_sql = _SELECT_ROLE_VO + clause
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_role(row, list(_ROLE_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )


def _map_role(row: Any, keys: Sequence[str]) -> SysRole:
    """One result row -> one ``SysRole`` (Java: ``resultMap="SysRoleResult"``)."""
    values = {label: row[keys.index(label)] for label in keys}
    return SysRole(
        role_id=values["role_id"],
        role_name=values["role_name"],
        role_key=values["role_key"],
        role_sort=values["role_sort"],
        data_scope=values["data_scope"],
        menu_check_strictly=_as_bool(values["menu_check_strictly"]),
        dept_check_strictly=_as_bool(values["dept_check_strictly"]),
        status=values["status"],
        del_flag=values["del_flag"],
        create_time=values["create_time"],
        remark=values["remark"],
    )


def _text(value: Any) -> bool:
    """``test="x != null and x != ''"`` 的等价判断（``None`` 与空串都为假）。"""
    return value is not None and value != ""


def _in_clause(column: str, values: Sequence[int], prefix: str) -> tuple[str, Dict[str, int]]:
    """``<foreach open="(" separator="," close=")">`` -> ``(:p0, :p1, ...)``."""
    placeholders = ", ".join(f":{prefix}{index}" for index in range(len(values)))
    params = {f"{prefix}{index}": value for index, value in enumerate(values)}
    return f"{column} in ({placeholders})", params


def _as_bool(value: Any) -> bool:
    """``tinyint(1)`` -> ``boolean``.

    MyBatis maps a ``tinyint(1)`` column to Java's primitive ``boolean``; PyMySQL hands back
    an ``int``. The fields are non-nullable ``boolean`` in Java, so ``None`` is coerced to
    ``False`` rather than modelled as a tri-state.
    """
    if value is None:
        return False
    return bool(value)


__all__ = ["SysRoleMapper"]
