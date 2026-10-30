"""部门表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDeptMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml

``SysDeptMapper.xml`` 里 1 个 ``<resultMap>`` + 1 个 ``<sql>`` 片段 + **16 条语句**，
这里全部落地。前 2 条（``selectDeptById`` / ``selectDeptList``）在 ``sys_user`` 切片里
就已迁好，本切片补齐其余 14 条。

四条容易踩的坑
--------------
1. ``selectDeptById`` / ``checkDeptNameUnique`` **不过滤** ``del_flag``。Java 原样如此：
   ``insertDept`` 要能读到已被逻辑删除的父节点。这里不"顺手"补 ``del_flag = '0'``。
2. ``where dept_id = #{deptId}`` 没有 ``d.`` 前缀。当前 SQL 只 from 了 ``sys_dept``
   自己，不存在歧义；以后加了 join 会变成 "Column 'dept_id' in where clause is
   ambiguous" —— 与 Java 完全一致地坏掉，而不是悄悄换个语义。
3. ``updateDept`` 里 ``phone`` / ``email`` 只判 ``!= null``（**没有** ``!= ''``），
   所以空串会被真的写进库；而 ``insertDept`` 里这两个字段判的是 ``!= null and != ''``。
   同一列在两条语句里判据不同，是 XML 原文如此。
4. ``updateDeptStatus`` 的 ``where dept_id in (${ancestors})`` 用 ``$`` 而非 ``#``
   —— **字符串拼接**，不绑定参数。值来自 ``SysDept.ancestors``（``"0,100,101"``）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_dept import SysDept
from app.config.database import session_scope

#: Verbatim from SysDeptMapper.xml -> ``<sql id="selectDeptVo">``.
SELECT_DEPT_VO = """
        select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader, d.fgld_id, d.fgld_name,
        d.bank_name, d.account, d.social_code, d.postal_code, d.address,
         d.phone, d.email, d.status, d.del_flag, d.create_by, d.create_time,
         d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc,d.tenant_id
        from sys_dept d
"""

#: Verbatim from SysDeptMapper.xml -> ``<select id="selectDeptById">``.
_SELECT_DEPT_BY_ID = SELECT_DEPT_VO + """
        where dept_id = :dept_id
"""

#: Verbatim from SysDeptMapper.xml -> ``<select id="selectDeptListByRoleId">``.
#: ``deptCheckStrictly`` 为真时追加"排除父节点"的子查询（``<if>`` 无 else）。
_SELECT_DEPT_LIST_BY_ROLE_ID = """
		select d.dept_id
		from sys_dept d
            left join sys_role_dept rd on d.dept_id = rd.dept_id
        where rd.role_id = :role_id
{strictly}		order by d.parent_id, d.order_num
"""

_SELECT_DEPT_LIST_BY_ROLE_ID_STRICTLY = (
    "              and d.dept_id not in (select d.parent_id from sys_dept d "
    "inner join sys_role_dept rd on d.dept_id = rd.dept_id and rd.role_id = :role_id)\n"
)

#: Verbatim from SysDeptMapper.xml -> ``<select id="checkDeptExistUser">``.
_CHECK_DEPT_EXIST_USER = (
    "select count(1) from sys_user where dept_id = :dept_id and del_flag = '0'"
)

#: Verbatim from SysDeptMapper.xml -> ``<select id="hasChildByDeptId">``.
_HAS_CHILD_BY_DEPT_ID = (
    "select count(1) from sys_dept\n\t\twhere del_flag = '0' and parent_id = :dept_id limit 1"
)

#: Verbatim from SysDeptMapper.xml -> ``<select id="selectChildrenDeptById">``.
#: 注意是 ``select *``，不是 ``selectDeptVo`` —— 会多带 ``update_by`` / ``update_time`` /
#: ``remark``（见 :data:`_DEPT_SELECT_ALL_COLUMNS`）。
_SELECT_CHILDREN_DEPT_BY_ID = "select * from sys_dept where find_in_set(:dept_id, ancestors)"

#: Verbatim from SysDeptMapper.xml -> ``<select id="selectNormalChildrenDeptById">``.
#: ``status = 0`` 是"字符串列比数字"，MySQL 隐式转换，原样保留。
_SELECT_NORMAL_CHILDREN_BY_DEPT_ID = (
    "select count(*) from sys_dept where status = 0 and del_flag = '0' "
    "and find_in_set(:dept_id, ancestors)"
)

#: Verbatim from SysDeptMapper.xml -> ``<select id="checkDeptNameUnique">``。
#: 按 ``(dept_name, parent_id)`` 组合判重，**不是**全表按名称判重。
_CHECK_DEPT_NAME_UNIQUE = SELECT_DEPT_VO + """
		where dept_name=:dept_name and parent_id = :parent_id limit 1
"""

#: Verbatim from SysDeptMapper.xml -> ``<select id="selectTenantId">``。
#: ``#{subCode}`` 在**左**边：``'001-001' like concat(d.sub_code, '%')`` —— 找自己的祖先单位。
_SELECT_TENANT_ID = SELECT_DEPT_VO + """
		where d.del_flag = '0' and :sub_code like concat(d.sub_code, '%')
		and d.is_uint = '1'
		order by d.tree_leavel desc
		limit 1
"""

#: Verbatim from SysDeptMapper.xml -> ``<update id="updateTenantId">``。
#: 注意 ``tenant_id`` 在 ``set`` 和 ``where`` 里是**同一个**参数。
_UPDATE_TENANT_ID = """update sys_dept set tenant_id = :tenant_id
	   where  is_uint = '0' and parent_id = :tenant_id"""

#: Verbatim from SysDeptMapper.xml -> ``<delete id="deleteDeptById">``。
#: 名字叫 delete，SQL 是 ``update ... set del_flag = '2'``。
_DELETE_DEPT_BY_ID = "update sys_dept set del_flag = '2' where dept_id = :dept_id"

#: Verbatim from SysDeptMapper.xml -> ``<delete id="deleteDeptAll">``。
#: 只删 ``create_by = '-9999'`` 的种子数据，供 ``saveAll`` 先清后灌。
_DELETE_DEPT_ALL = "delete from  sys_dept   where create_by = '-9999'"

#: 列名 -> SysDept 属性，对应 ``resultMap="SysDeptResult"``。
#: ``parent_name`` / ``update_by`` / ``update_time`` 在 map 里，但 ``selectDeptVo`` 不查，
#: 所以走 ``selectDeptVo`` 的语句里它们恒为 ``None``。
_DEPT_COLUMNS = (
    "dept_id",
    "parent_id",
    "ancestors",
    "dept_name",
    "order_num",
    "leader_id",
    "leader",
    "fgld_id",
    "fgld_name",
    "bank_name",
    "account",
    "social_code",
    "postal_code",
    "address",
    "phone",
    "email",
    "status",
    "del_flag",
    "create_by",
    "create_time",
    "is_zbzg",
    "is_uint",
    "tree_leavel",
    "sub_code",
    "dept_jc",
    "tenant_id",
)

#: ``select *`` 专供 :meth:`SysDeptMapper.select_children_dept_by_id`。
#: MyBatis 的 ``autoMappingBehavior=PARTIAL`` 会把 resultMap 没列的 ``remark`` /
#: ``update_by`` / ``update_time`` 也自动映射上，所以这条语句的结果比
#: :data:`_DEPT_COLUMNS` 多三个字段。
_DEPT_SELECT_ALL_COLUMNS = _DEPT_COLUMNS + ("update_by", "update_time", "remark")

#: ``insertDept`` 的动态列，顺序与 XML 一致。第三项 ``require_text`` 表示该列是否
#: 额外判 ``!= ''``（即 ``<if test="x != null and x != ''">``）。
_INSERT_DEPT_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("parent_id", "parent_id", False),  # 另有 != 0，单独处理
    ("dept_name", "dept_name", True),
    ("ancestors", "ancestors", True),
    ("order_num", "order_num", True),
    ("leader_id", "leader_id", False),
    ("leader", "leader", False),
    ("fgld_id", "fgld_id", False),
    ("fgld_name", "fgld_name", False),
    ("bank_name", "bank_name", False),
    ("account", "account", False),
    ("social_code", "social_code", False),
    ("postal_code", "postal_code", False),
    ("address", "address", False),
    ("phone", "phone", True),
    ("email", "email", True),
    ("status", "status", False),
    ("create_by", "create_by", True),
    ("is_zbzg", "is_zbzg", False),
    ("is_uint", "is_uint", False),
    ("tree_leavel", "tree_leavel", False),
    ("sub_code", "sub_code", False),
    ("dept_jc", "dept_jc", False),
    ("tenant_id", "tenant_id", False),
)

#: ``updateDept`` 的 ``<set>``，顺序与 XML 一致。
#: **注意** ``phone`` / ``email`` 只有 ``!= null``（第三项为 ``False``），空串照样写库。
_UPDATE_DEPT_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("parent_id", "parent_id", False),  # 另有 != 0，单独处理
    ("dept_name", "dept_name", True),
    ("ancestors", "ancestors", True),
    ("order_num", "order_num", True),
    ("leader_id", "leader_id", False),
    ("leader", "leader", False),
    ("fgld_id", "fgld_id", False),
    ("fgld_name", "fgld_name", False),
    ("bank_name", "bank_name", False),
    ("account", "account", False),
    ("social_code", "social_code", False),
    ("postal_code", "postal_code", False),
    ("address", "address", False),
    ("phone", "phone", False),
    ("email", "email", False),
    ("status", "status", True),
    ("update_by", "update_by", True),
    ("is_zbzg", "is_zbzg", False),
    ("is_uint", "is_uint", False),
    ("tree_leavel", "tree_leavel", False),
    ("sub_code", "sub_code", False),
    ("dept_jc", "dept_jc", False),
    ("tenant_id", "tenant_id", False),
)


class SysDeptMapper:
    """Java: ``interface SysDeptMapper``."""

    # Java: SysDept selectDeptById(Long deptId)
    def select_dept_by_id(self, dept_id: Optional[int]) -> Optional[SysDept]:
        """按主键取部门；``selectOne`` 语义，找不到返回 ``None``。

        ``dept_id`` 允许为 ``None``（``#{deptId}`` 传 null → ``where dept_id = null``
        → 永远匹配不到），与 Java 一致地返回 ``None``。
        """
        return self._select_one(_SELECT_DEPT_BY_ID, {"dept_id": dept_id})

    # Java: List<SysDept> selectDeptList(SysDept dept)
    def select_dept_list(self, dept: Optional[SysDept] = None) -> List[SysDept]:
        """按条件查部门列表，``order by d.parent_id, d.order_num``。

        动态条件与 ``SysDeptMapper.xml`` 的 ``<if>`` 一一对应，判断方式也保持一致：
        ``deptName`` / ``status`` / ``isZbzg`` / ``isUint`` / ``subCode`` / ``deptJc`` /
        ``leader`` / ``fgldName`` / ``deptSubCode`` 用 ``!= null and != ''``（OGNL 对
        空串才为假，单个空格**会**保留条件）；``parentId`` / ``treeLeavel`` /
        ``leaderId`` / ``fgldId`` / ``tenantId`` 只判 ``!= null``。
        """
        dept = dept or SysDept()
        where: List[str] = ["d.del_flag = '0'"]
        params: Dict[str, Any] = {}

        if dept.parent_id is not None:
            where.append("AND d.parent_id = :parent_id")
            params["parent_id"] = dept.parent_id
        if _text(dept.dept_name):
            where.append("AND d.dept_name like concat('%', :dept_name, '%')")
            params["dept_name"] = dept.dept_name
        if _text(dept.status):
            where.append("AND d.status = :status")
            params["status"] = dept.status
        if dept.dept_id is not None:
            where.append("AND d.dept_id = :dept_id")
            params["dept_id"] = dept.dept_id
        if _text(dept.is_zbzg):
            where.append("and d.is_zbzg = :is_zbzg")
            params["is_zbzg"] = dept.is_zbzg
        if _text(dept.is_uint):
            where.append("and d.is_uint = :is_uint")
            params["is_uint"] = dept.is_uint
        if dept.tree_leavel is not None:
            where.append("and d.tree_leavel = :tree_leavel")
            params["tree_leavel"] = dept.tree_leavel
        if _text(dept.sub_code):
            where.append("and d.sub_code = :sub_code")
            params["sub_code"] = dept.sub_code
        if _text(dept.dept_jc):
            where.append("and d.dept_jc = :dept_jc")
            params["dept_jc"] = dept.dept_jc
        if dept.tenant_id is not None:
            where.append("and d.tenant_id = :tenant_id")
            params["tenant_id"] = dept.tenant_id
        # <!--上级单位-->  OGNL 里 flag == 'sjzbDept' 对字符串等价于 equals。
        if dept.flag == "sjzbDept":
            where.append(
                """and exists (
			select 1 from sys_dept tb,sys_dept tb1
			where tb.del_flag = '0' and  tb.del_flag = '0' and tb1.dept_id = tb.parent_id
			and tb.dept_id = :data_id  and tb1.dept_id = d.tenant_id
		   )"""
            )
            params["data_id"] = dept.data_id
        if dept.leader_id is not None:
            where.append("and d.leader_id = :leader_id")
            params["leader_id"] = dept.leader_id
        if _text(dept.leader):
            where.append("and d.leader = :leader")
            params["leader"] = dept.leader
        if dept.fgld_id is not None:
            where.append("and d.fgld_id = :fgld_id")
            params["fgld_id"] = dept.fgld_id
        if _text(dept.fgld_name):
            where.append("and d.fgld_name like concat('%', :fgld_name, '%')")
            params["fgld_name"] = dept.fgld_name
        if _text(dept.dept_sub_code):
            # 注意是前缀匹配：concat(#{deptSubCode}, '%')，没有前导 %
            where.append("and d.sub_code like concat(:dept_sub_code, '%')")
            params["dept_sub_code"] = dept.dept_sub_code

        sql = (
            SELECT_DEPT_VO
            + "        where "
            + "\n        ".join(where)
            + "\n        order by d.parent_id, d.order_num"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            return [_map_dept(row, keys) for row in result.all()]

    # Java: List<Integer> selectDeptListByRoleId(Long roleId, boolean deptCheckStrictly)
    def select_dept_list_by_role_id(
        self, role_id: int, dept_check_strictly: bool
    ) -> List[int]:
        """角色已勾选的部门 ID 列表。

        ``deptCheckStrictly`` 为真时排除"有父节点也被勾选"的部门 —— 前端树是父子联动
        勾选的，回显时要砍掉父节点，否则一展开就自动选中整棵子树。
        """
        strictly = _SELECT_DEPT_LIST_BY_ROLE_ID_STRICTLY if dept_check_strictly else ""
        sql = _SELECT_DEPT_LIST_BY_ROLE_ID.format(strictly=strictly)
        with session_scope() as session:
            result = session.execute(text(sql), {"role_id": role_id})
            return [row[0] for row in result.all()]

    # Java: int checkDeptExistUser(Long deptId)
    def check_dept_exist_user(self, dept_id: int) -> int:
        return self._select_count(_CHECK_DEPT_EXIST_USER, {"dept_id": dept_id})

    # Java: int hasChildByDeptId(Long deptId)
    def has_child_by_dept_id(self, dept_id: int) -> int:
        return self._select_count(_HAS_CHILD_BY_DEPT_ID, {"dept_id": dept_id})

    # Java: List<SysDept> selectChildrenDeptById(Long deptId)
    def select_children_dept_by_id(self, dept_id: int) -> List[SysDept]:
        """按 ``ancestors`` 找所有后代（``find_in_set``，不含自己）。

        只有 ``updateDeptChildren`` 用得到，而那段调用在 Java 里是**注释掉的**，
        所以这条语句目前没有活的调用方 —— 依旧迁移，别删。
        """
        with session_scope() as session:
            result = session.execute(text(_SELECT_CHILDREN_DEPT_BY_ID), {"dept_id": dept_id})
            keys = list(result.keys())
            return [_map_dept(row, keys, _DEPT_SELECT_ALL_COLUMNS) for row in result.all()]

    # Java: int selectNormalChildrenDeptById(Long deptId)
    def select_normal_children_dept_by_id(self, dept_id: int) -> int:
        return self._select_count(_SELECT_NORMAL_CHILDREN_BY_DEPT_ID, {"dept_id": dept_id})

    # Java: SysDept checkDeptNameUnique(String deptName, Long parentId)
    def check_dept_name_unique(
        self, dept_name: Optional[str], parent_id: Optional[int]
    ) -> Optional[SysDept]:
        """同父节点下部门名判重。``limit 1``，多条同名只返回第一条。"""
        return self._select_one(
            _CHECK_DEPT_NAME_UNIQUE, {"dept_name": dept_name, "parent_id": parent_id}
        )

    # Java: int insertDept(SysDept dept)  -- useGeneratedKeys="true" keyProperty="deptId"
    def insert_dept(self, dept: SysDept) -> int:
        """动态列插入；回写 ``dept.dept_id``（MyBatis ``keyProperty`` 的等价物）。

        ``create_time`` 在 XML 里是**无条件**的一列（``sysdate()``），所以列清单永远非空。
        """
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        # Java: <if test="deptId != null and deptId != 0">dept_id,</if>
        if dept.dept_id is not None and dept.dept_id != 0:
            columns.append("dept_id")
            names.append(":dept_id")
            params["dept_id"] = dept.dept_id

        for attribute, column, require_text in _INSERT_DEPT_COLUMNS:
            value = getattr(dept, attribute)
            if value is None:
                continue
            if attribute == "parent_id" and value == 0:
                continue
            if require_text and value == "":
                continue
            columns.append(column)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_dept({','.join(columns)})values({','.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            dept.dept_id = result.lastrowid
            return result.rowcount or 0

    # Java: int updateDept(SysDept dept)
    def update_dept(self, dept: SysDept) -> int:
        sql, params = _build_update_dept_sql(dept)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateDeptChildren(List<SysDept> depts)
    def update_dept_children(self, depts: Sequence[SysDept]) -> int:
        """一条 ``case ... when`` 批量改 ``ancestors``（``<foreach>`` 的等价物）。

        空列表会拼出 ``case dept_id end where dept_id in ()`` —— Java 同样是语法错，
        调用方 ``updateDeptChildren`` 已经用 ``children.size() > 0`` 挡住。
        """
        cases: List[str] = []
        ids: List[str] = []
        params: Dict[str, Any] = {}
        for index, child in enumerate(depts):
            cases.append(f"when :dept_id_{index} then :ancestors_{index}")
            ids.append(f":dept_id_{index}")
            params[f"dept_id_{index}"] = child.dept_id
            params[f"ancestors_{index}"] = child.ancestors
        sql = (
            "update sys_dept set ancestors = case dept_id "
            + " ".join(cases)
            + " end where dept_id in ("
            + ",".join(ids)
            + ")"
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateDeptStatus(SysDept dept)
    def update_dept_status(self, dept: SysDept) -> int:
        """``where dept_id in (${ancestors})`` —— **字符串拼接**，不是绑定参数。

        这是 XML 原文（``$`` 而非 ``#``）。``ancestors`` 形如 ``"0,100,101"``；
        为 ``None`` 时 MyBatis 的 ``${}`` 会渲染成字面量 ``null``，这里照抄。
        """
        sets: List[str] = []
        params: Dict[str, Any] = {}
        if _text(dept.status):
            sets.append("status = :status")
            params["status"] = dept.status
        if _text(dept.update_by):
            sets.append("update_by = :update_by")
            params["update_by"] = dept.update_by
        sets.append("update_time = sysdate()")

        ancestors = "null" if dept.ancestors is None else str(dept.ancestors)
        sql = (
            "update sys_dept\n\t    set "
            + ", ".join(sets)
            + f"\n\t    where dept_id in ({ancestors})"
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteDeptById(Long deptId)
    def delete_dept_by_id(self, dept_id: int) -> int:
        """逻辑删除（``del_flag = '2'``），不是物理删除。"""
        with session_scope() as session:
            return session.execute(text(_DELETE_DEPT_BY_ID), {"dept_id": dept_id}).rowcount or 0

    # Java: SysDept selectTenantId(SysDept dept)
    def select_tenant_id(self, dept: SysDept) -> Optional[SysDept]:
        """按 ``sub_code`` 前缀反查最近的一个"单位"（``is_uint = '1'``）。

        ``order by tree_leavel desc limit 1`` 取**最深**的那个，也就是最近的分公司。
        """
        return self._select_one(_SELECT_TENANT_ID, {"sub_code": dept.sub_code})

    # Java: int updateTenantId(SysDept dept)
    def update_tenant_id(self, dept: SysDept) -> int:
        """把某单位直属下级的 ``tenant_id`` 统一改成该单位 ID。"""
        return self._execute(
            _UPDATE_TENANT_ID, {"tenant_id": dept.tenant_id}
        )

    # Java: int deleteDeptAll()
    def delete_dept_all(self) -> int:
        """只清 ``create_by = '-9999'`` 的种子数据，供 ``saveAll`` 先清后灌。"""
        return self._execute(_DELETE_DEPT_ALL, {})

    # ------------------------------------------------------------------ helpers

    def _select_one(
        self,
        sql: str,
        params: Mapping[str, Any],
        columns: Sequence[str] = _DEPT_COLUMNS,
    ) -> Optional[SysDept]:
        with session_scope() as session:
            result = session.execute(text(sql), dict(params))
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_dept(rows[0], keys, columns)

    def _select_count(self, sql: str, params: Mapping[str, Any]) -> int:
        with session_scope() as session:
            value = session.execute(text(sql), dict(params)).scalar()
        return 0 if value is None else int(value)

    def _execute(self, sql: str, params: Mapping[str, Any]) -> int:
        with session_scope() as session:
            return session.execute(text(sql), dict(params)).rowcount or 0


def _build_update_dept_sql(dept: SysDept) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_dept set ... where dept_id = :dept_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 是**无条件**的，所以 ``<set>`` 永不为空 ——
    即使所有 ``<if>`` 都不命中，SQL 依然合法（Java 也一样）。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_DEPT_COLUMNS:
        value = getattr(dept, attribute)
        if value is None:
            continue
        # Java: parentId != null and parentId != 0 —— 父节点 0 表示"不改父级"
        if attribute == "parent_id" and value == 0:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["dept_id"] = dept.dept_id

    sql = "update sys_dept set " + ", ".join(sets) + " where dept_id = :dept_id"
    return sql, params


def _text(value: Optional[str]) -> bool:
    """``test="x != null and x != ''"`` 的等价判断（``None`` 与空串都为假）。"""
    return value is not None and value != ""


def _map_dept(
    row: Any,
    keys: Sequence[str],
    columns: Sequence[str] = _DEPT_COLUMNS,
) -> SysDept:
    """One result row -> one ``SysDept`` (Java: ``resultMap="SysDeptResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in columns if name in values}
    return SysDept(**fields)


__all__ = ["SysDeptMapper", "SELECT_DEPT_VO"]
