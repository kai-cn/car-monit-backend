"""部门 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDeptService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java

``ISysDeptService`` 的 16 个方法全部落地（含两个 Java ``private`` 辅助方法）。这是
``sys_dept`` 切片的主战场，四段逻辑必须逐行对照读：

``insertDept`` / ``updateDept``
    ``sub_code`` 的生成规则、``is_uint`` / ``is_zbg`` 的联动、插完再回写
    ``tenant_id``。两者前 50 行**逐字相同**，是 Java 的复制粘贴，不要抽公共方法 ——
    抽了以后改一处就会同时影响新增和修改。

``updateTenantId``
    批量刷新子树的 ``tenant_id``。注意它调的是 ``selectDeptList``，而
    ``deptSubCode`` 为 ``null`` 时那个 ``<if>`` 不生效 → **扫全表**。Java 就是这样。

``buildDeptTree`` / ``recursionFn``
    纯内存建树，就地改 ``dept.children``。找不到任何根节点时**原样返回入参**
    （``returnList = depts``），不是返回空列表。

``getQxSql``
    三级权限降级：分管领导 -> 部门负责人 -> 只看自己创建的。返回的是**拼好的 SQL
    片段**（含 ``userId`` 字符串拼接），调用方自己塞进 where 里。

``Set<SysDept>`` 不是真的去重
----------------------------
``SysDept`` **没有**重写 ``equals`` / ``hashCode``，所以 Java 的 ``Collectors.toSet()``
建的是身份哈希表：同一个 ``dept_id`` 但不同实例不会被合并。这里用 ``id()`` 做键，
保持同样的"只按对象身份去重"语义。返回值用 ``list`` 承载（Python 侧调用方只用
``if dept_set:`` 和迭代），并在文档里标明顺序不确定这一点与 ``HashSet`` 一致。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.constant.user_constants import NOT_UNIQUE_OLD, UNIQUE_OLD
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.tree_select import TreeSelect
from app.common.utils import security_utils as SecurityUtils
from app.framework.aspectj.data_scope_aspect import apply_data_scope
from app.system.mapper.sys_dept_mapper import SysDeptMapper
from app.system.mapper.sys_role_mapper import SysRoleMapper


class SysDeptService:
    """Java: ``ISysDeptService`` (impl: ``SysDeptServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysDeptMapper] = None,
        role_mapper: Optional[SysRoleMapper] = None,
    ) -> None:
        self._mapper = mapper or SysDeptMapper()
        self._role_mapper = role_mapper or SysRoleMapper()

    @property
    def mapper(self) -> SysDeptMapper:
        return self._mapper

    # ---------------------------------------------------------------- 查询

    # Java: List<SysDept> selectDeptList(SysDept dept)
    def select_dept_list(self, dept: SysDept) -> List[SysDept]:
        """查询部门管理数据.

        Java: ``@DataScope(deptAlias = "d")``。切面会写 ``dept.params["dataScope"]``，
        但 ``SysDeptMapper.xml#selectDeptList`` 里对应的 ``${params.dataScope}`` 是**被注释
        掉的**，所以片段不进 SQL。保留调用只为与 Java 的调用链一致。
        """
        apply_data_scope(dept, "d")
        return self._mapper.select_dept_list(dept)

    # Java: SysDept selectDeptById(Long deptId)
    def select_dept_by_id(self, dept_id: Optional[int]) -> Optional[SysDept]:
        return self._mapper.select_dept_by_id(dept_id)

    # Java: Set<SysDept> selectHeadOffice()
    def select_head_office(self) -> Optional[List[SysDept]]:
        """获取总公司部门. 无任何部门时返回 ``None``（Java 也是 ``null``）。"""
        dept_list = self.select_dept_list(SysDept())
        if not dept_list:
            return None

        # 获取 tree_level 为 1 和 2
        filter_set = [
            dept
            for dept in dept_list
            if _equals(dept.tree_leavel, 1) or _equals(dept.tree_leavel, 2)
        ]
        filter_dept_id_set = {dept.dept_id for dept in filter_set}

        dept_set = [dept for dept in dept_list if dept.tenant_id in filter_dept_id_set]

        # Java: filterSet.addAll(deptSet) —— 身份去重，不按 deptId
        merged: List[SysDept] = []
        seen: set = set()
        for dept in list(filter_set) + list(dept_set):
            key = id(dept)
            if key in seen:
                continue
            seen.add(key)
            merged.append(dept)
        return merged

    # Java: List<Integer> selectDeptListByRoleId(Long roleId)
    def select_dept_list_by_role_id(self, role_id: int) -> List[int]:
        """角色已勾选的部门 ID。角色不存在时 Java NPE，这里抛 ``AttributeError``。"""
        role = self._role_mapper.select_role_by_id(role_id)
        return self._mapper.select_dept_list_by_role_id(
            role_id, role.dept_check_strictly
        )

    # Java: int selectNormalChildrenDeptById(Long deptId)
    def select_normal_children_dept_by_id(self, dept_id: int) -> int:
        return self._mapper.select_normal_children_dept_by_id(dept_id)

    # Java: boolean hasChildByDeptId(Long deptId)
    def has_child_by_dept_id(self, dept_id: int) -> bool:
        return self._mapper.has_child_by_dept_id(dept_id) > 0

    # Java: boolean checkDeptExistUser(Long deptId)
    def check_dept_exist_user(self, dept_id: int) -> bool:
        return self._mapper.check_dept_exist_user(dept_id) > 0

    # Java: String checkDeptNameUnique(SysDept dept)
    def check_dept_name_unique(self, dept: SysDept) -> str:
        """``"1"`` = 冲突，``"0"`` = 唯一。

        ``deptId`` 缺失时用 ``-1`` 作哨兵（Java ``-1L``）—— 因为数据库里的主键不可能
        是负数，所以"新增"永远撞不上"自己"。
        """
        dept_id = -1 if dept.dept_id is None else dept.dept_id
        info = self._mapper.check_dept_name_unique(dept.dept_name, dept.parent_id)
        if info is not None and info.dept_id != dept_id:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # ---------------------------------------------------------------- 树

    # Java: List<SysDept> buildDeptTree(List<SysDept> depts)
    def build_dept_tree(self, depts: List[SysDept]) -> List[SysDept]:
        """把扁平列表就地建成树，返回根节点列表。

        ``parentId`` 不在本列表里的就是根。**一个根都没有时返回入参本身**
        （Java: ``returnList = depts``），此时列表是扁平的、每个节点的 ``children``
        还是 ``[]`` —— 前端会平铺展示。
        """
        return_list: List[SysDept] = []
        temp_list: List[Optional[int]] = []
        for dept in depts:
            temp_list.append(dept.dept_id)
        for dept in depts:
            # 如果是顶级节点, 遍历该父节点的所有子节点
            if dept.parent_id not in temp_list:
                self._recursion_fn(depts, dept)
                return_list.append(dept)
        if not return_list:
            return_list = depts
        return return_list

    # Java: List<TreeSelect> buildDeptTreeSelect(List<SysDept> depts)
    def build_dept_tree_select(self, depts: List[SysDept]) -> List[TreeSelect]:
        dept_trees = self.build_dept_tree(depts)
        return [TreeSelect.of_dept(dept) for dept in dept_trees]

    # ---------------------------------------------------------------- 增删改

    # Java: int insertDept(SysDept dept)
    def insert_dept(self, dept: SysDept) -> int:
        """新增部门，返回受影响行数（恒为 1）。

        与 :meth:`update_dept` 的前半段逐字相同，**故意不抽公共方法**。
        """
        # 修改部门编码
        parent_sub_code = ""  # 父节点 code
        if dept.parent_id is None:
            dept.parent_id = 0
            dept.is_uint = "1"  # 顶级节点一定是单位
        # 设置树级别
        if dept.parent_id == 0:
            dept.tree_leavel = 1
            parent_sub_code = "001"
        else:
            # 查询父节点（父节点不存在时 Java 在 parentBO.getTreeLeavel() 处 NPE）
            parent_bo = self._mapper.select_dept_by_id(dept.parent_id)
            dept.tree_leavel = parent_bo.tree_leavel + 1
            parent_sub_code = parent_bo.sub_code

        flag = True
        if dept.dept_id is not None:
            tmp_bo = self._mapper.select_dept_by_id(dept.dept_id)
            if tmp_bo.parent_id == dept.parent_id:
                flag = False

        if flag:
            # 设置 subCode
            pbo = SysDept(parent_id=dept.parent_id)
            counts = len(self._mapper.select_dept_list(pbo))
            dept.sub_code = _build_sub_code(dept.parent_id, parent_sub_code, counts)

        # 如果是部门 -没有招标
        if dept.is_uint == "0":
            dept.is_zbzg = "0"

        count = self._mapper.insert_dept(dept)

        # 修改租户id
        if dept.is_uint == "0":
            dept_eps_id = self._mapper.select_tenant_id(dept)
            if dept_eps_id is not None:
                self._mapper.update_dept(
                    SysDept(dept_id=dept.dept_id, tenant_id=dept_eps_id.dept_id)
                )
        else:
            # 是单位
            self._mapper.update_dept(SysDept(dept_id=dept.dept_id, tenant_id=dept.dept_id))

        return count

    # Java: int updateDept(SysDept dept)
    def update_dept(self, dept: SysDept) -> int:
        """修改部门。前半段与 :meth:`insert_dept` 逐字相同，后半段多一次租户批量刷新。"""
        # 修改部门编码
        parent_sub_code = ""  # 父节点 code
        if dept.parent_id is None:
            dept.parent_id = 0
            dept.is_uint = "1"  # 顶级节点一定是单位
        # 设置树级别
        if dept.parent_id == 0:
            dept.tree_leavel = 1
            parent_sub_code = "001"
        else:
            parent_bo = self._mapper.select_dept_by_id(dept.parent_id)
            dept.tree_leavel = parent_bo.tree_leavel + 1
            parent_sub_code = parent_bo.sub_code

        flag = True
        if dept.dept_id is not None:
            tmp_bo = self._mapper.select_dept_by_id(dept.dept_id)
            if tmp_bo.parent_id == dept.parent_id:
                flag = False

        if flag:
            pbo = SysDept(parent_id=dept.parent_id)
            counts = len(self._mapper.select_dept_list(pbo))
            dept.sub_code = _build_sub_code(dept.parent_id, parent_sub_code, counts)

        # 如果是部门 -没有招标
        if dept.is_uint == "0":
            dept.is_zbzg = "0"

        result = self._mapper.update_dept(dept)

        # 批量修改 租户id
        self._update_tenant_id(dept.sub_code)
        return result

    # Java: private void updateTenantId(String deptSubCode)
    def _update_tenant_id(self, dept_sub_code: Optional[str]) -> None:
        """把 ``sub_code`` 以 ``deptSubCode`` 开头的整棵子树的 ``tenant_id`` 刷一遍。

        **注意** ``deptSubCode`` 为 ``None`` 时 ``selectDeptList`` 那条 ``<if>`` 不生效，
        于是扫的是**全表**（``del_flag = '0'``）。Java 原样如此：``updateDept`` 在
        ``flag == false``（父级没变）时不会重算 ``subCode``，客户端又没传的话就是此情形。
        """
        query_bo = SysDept(dept_sub_code=dept_sub_code)
        query_list = self._mapper.select_dept_list(query_bo)
        for dept in query_list:
            if dept.is_uint == "0":
                dept_eps_id = self._mapper.select_tenant_id(dept)
                if dept_eps_id is not None:
                    self._mapper.update_dept(
                        SysDept(dept_id=dept.dept_id, tenant_id=dept_eps_id.dept_id)
                    )
            else:
                # 是单位
                self._mapper.update_dept(
                    SysDept(dept_id=dept.dept_id, tenant_id=dept.dept_id)
                )

    # Java: private void updateParentDeptStatus(SysDept dept)
    def _update_parent_dept_status(self, dept: SysDept) -> None:
        """把"当前部门"当父级刷状态。

        名字带 parent，实际改的是 ``dept.dept_id`` 自己的 ``status``（Java 就这么写的，
        而且 ``${ancestors}`` 那句才是真正按祖级批量改）。**当前无调用方** ——
        ``updateDept`` 里那段是被注释掉的，保留迁移。
        """
        update_by = dept.update_by
        current = self._mapper.select_dept_by_id(dept.dept_id)
        current.update_by = update_by
        self._mapper.update_dept_status(current)

    # Java: public void updateDeptChildren(Long deptId, String newAncestors, String oldAncestors)
    def update_dept_children(
        self, dept_id: int, new_ancestors: str, old_ancestors: str
    ) -> None:
        """改父级后重写所有后代的 ``ancestors``。

        用 ``str.replace`` 做前缀替换 —— 与 Java 的
        ``child.getAncestors().replace(oldAncestors, newAncestors)`` 完全一致，
        包括"旧串是空串时在每个字符间插入新串"这种病态行为。
        """
        children = self._mapper.select_children_dept_by_id(dept_id)
        for child in children:
            child.ancestors = child.ancestors.replace(old_ancestors, new_ancestors)
        if children:
            self._mapper.update_dept_children(children)

    # Java: int deleteDeptById(Long deptId)
    def delete_dept_by_id(self, dept_id: int) -> int:
        """逻辑删除（``del_flag = '2'``）。"""
        return self._mapper.delete_dept_by_id(dept_id)

    # ---------------------------------------------------------------- 其它

    # Java: String getQxSql(String type)
    def get_qx_sql(self, type: Optional[str] = None) -> Optional[str]:
        """按当前登录人算一段权限 SQL 片段（三级降级）。

        1. 是某个部门的**分管领导**（``fgld_id``）→ ``t.eps_id in (...)``；
        2. 否则是某个部门的**负责人**（``leader_id``）→ ``t.eps_id in (...)``；
        3. 否则 → ``t.create_by=<userId>``。

        参数 ``type`` 在 Java 里**根本没用**，保留签名只是为了跟接口对齐。
        """
        sql = ""
        table_col = "t.eps_id"
        user_id = SecurityUtils.get_user_id()

        # 判断是否是分管领导
        bo = SysDept(fgld_id=user_id)
        fg_dept_list = self._mapper.select_dept_list(bo)
        if fg_dept_list:
            sql = table_col + " in (" + self._get_sql_dept_ids(fg_dept_list) + ")"
        else:
            # 判断是部门负责人
            bo1 = SysDept(leader_id=user_id)
            fzr_dept_list = self._mapper.select_dept_list(bo1)
            if fzr_dept_list:
                sql = table_col + " in (" + self._get_sql_dept_ids(fzr_dept_list) + ")"
            else:
                sql = " t.create_by=" + str(user_id)
        return sql

    # Java: public void saveAll(List<SysDept> depts)
    def save_all(self, depts: Optional[Sequence[SysDept]]) -> None:
        """先清 ``create_by = '-9999'`` 的种子数据，再逐条插入。

        注意它**不是** upsert：``deleteDeptAll`` 只删种子数据，重复调用会插重复行。
        """
        if depts:
            self._mapper.delete_dept_all()
            for dept in depts:
                self._mapper.insert_dept(dept)

    # ---------------------------------------------------------------- helpers

    # Java: private void recursionFn(List<SysDept> list, SysDept t)
    def _recursion_fn(self, depts: List[SysDept], node: SysDept) -> None:
        child_list = self._get_child_list(depts, node)
        node.children = child_list
        for child in child_list:
            if self._has_child(depts, child):
                self._recursion_fn(depts, child)

    # Java: private List<SysDept> getChildList(List<SysDept> list, SysDept t)
    def _get_child_list(self, depts: List[SysDept], node: SysDept) -> List[SysDept]:
        """``n.parentId != null && n.parentId == t.deptId``。

        接收者 ``node.dept_id`` 为 ``None`` 时 Java 在 ``t.getDeptId().longValue()``
        处 NPE；这里抛 ``AttributeError`` 让脏数据以 500 的形式暴露，而不是悄悄少挂节点。
        """
        if node.dept_id is None:
            raise AttributeError("'NoneType' object has no attribute 'longValue'")
        return [
            candidate
            for candidate in depts
            if candidate.parent_id is not None and candidate.parent_id == node.dept_id
        ]

    # Java: private boolean hasChild(List<SysDept> list, SysDept t)
    def _has_child(self, depts: List[SysDept], node: SysDept) -> bool:
        return len(self._get_child_list(depts, node)) > 0

    # Java: private String getSqlDeptIds(List<SysDept> deptList)
    def _get_sql_dept_ids(self, dept_list: Optional[Sequence[SysDept]]) -> str:
        """``"1,2,3"`` —— 末尾不带逗号；空列表返回空串。"""
        dept_ids = ""
        if dept_list:
            for vo in dept_list:
                dept_ids += str(vo.dept_id) + ","
            dept_ids = dept_ids[: len(dept_ids) - 1]
        return dept_ids


def _build_sub_code(
    parent_id: Optional[int], parent_sub_code: Optional[str], counts: int
) -> str:
    """``subCode = "00" + (counts+1)`` / ``parentSubCode + "-00" + (counts+1)`` …

    三级补零规则照抄 Java：``counts < 9`` 补两位，``< 99`` 补一位，再多就不补。
    由于 ``counts`` 是"当前父节点下已有的子节点数"，第 10 个子节点（``counts == 9``）
    走 ``-010`` 分支而不是 ``-0010`` —— 位数会跳一次，但这是 Java 的行为。
    """
    next_index = counts + 1
    if parent_id == 0:
        return "00" + str(next_index)
    if counts < 9:
        return f"{parent_sub_code}-00{next_index}"
    if counts < 99:
        return f"{parent_sub_code}-0{next_index}"
    return f"{parent_sub_code}-{next_index}"


def _equals(value: Any, target: int) -> bool:
    """Java: ``Integer.equals(int)`` —— 接收者为 ``null`` 时 NPE，这里抛 ``AttributeError``。

    ``selectHeadOffice`` 直接写 ``dept.getTreeLeavel().equals(1)``，没有判空。``tree_leavel``
    在 ``insertDept`` 里总会被赋值，所以正常数据走不到这里；保留抛错是为了让"脏数据"
    的表现与 Java 一致（500），而不是悄悄少算几个部门。
    """
    if value is None:
        raise AttributeError("'NoneType' object has no attribute 'equals'")
    return value == target


_SERVICE: Optional[SysDeptService] = None


def get_dept_service() -> SysDeptService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysDeptService()
    return _SERVICE


def reset_dept_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysDeptService", "get_dept_service", "reset_dept_service"]
