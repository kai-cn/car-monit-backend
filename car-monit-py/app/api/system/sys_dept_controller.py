"""部门信息.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDeptController.java

端点清单（11 个映射，全部迁移）
-------------------------------
    ==================================  =======  ====================================  ==========
    Java                                Method   Path                                  Access
    ==================================  =======  ====================================  ==========
    ``list(SysDept)``                    GET      ``/system/dept/list``                 list
    ``getList(SysDept)``                 GET      ``/system/dept/getList``              登录
    ``excludeChild(Long)``               GET      ``/system/dept/list/exclude/{deptId}`` list
    ``getInfo(Long)``                    GET      ``/system/dept/{deptId}``             query
    ``treeselect(SysDept)``              GET      ``/system/dept/treeselect``           登录
    ``treeselectNew(SysDept)``           GET      ``/system/dept/treeselectNew``        登录
    ``roleDeptTreeselect(Long)``         GET      ``/system/dept/roleDeptTreeselect/{roleId}`` 登录
    ``add(SysDept)``                     POST     ``/system/dept``                      add
    ``edit(SysDept)``                    PUT      ``/system/dept``                      edit
    ``remove(Long)``                     DELETE   ``/system/dept/{deptId}``             remove
    ``getCompanyList()``                 GET      ``/system/dept/getCompanyList``        登录
    ==================================  =======  ====================================  ==========

只有 ``list`` / ``excludeChild`` / ``getInfo`` / ``add`` / ``edit`` / ``remove`` 带
``@PreAuthorize``；其余六个连权限点都不校验，**任何登录用户**都能拿到全量部门树。
这不是遗漏，是 Java 源码如此（``getList`` 和 ``treeselectNew`` 是前端下拉框在用的）。

``list`` 与 ``getList`` 完全重复
--------------------------------
两个映射的函数体一字不差（都返回 ``AjaxResult.success(List<SysDept>)``，都**不分页**），
区别只是 ``getList`` 没有 ``@PreAuthorize``。不要合并成一个 —— 权限差异是实质性的。

``@Validated @RequestBody`` 与 ``@PreAuthorize`` 的先后
-------------------------------------------------------
同 ``sys_post`` 切片：Spring MVC 先解析参数（触发 Hibernate Validator），**再**进入
``@PreAuthorize`` 的方法代理，顺序是::

    安全过滤器链(401) -> 路由 -> 反序列化+校验(500) -> @PreAuthorize(403) -> 方法体

所以校验做成 FastAPI 的 ``Depends``（:data:`ValidDept`），依赖在端点函数体之前解析。
:class:`app.common.utils.bean_validation.BeanValidationError` 继承 ``RuntimeError``，
落到通用处理器后是 ``{"code": 500, "msg": "部门名称不能为空"}``，与 Java 一致。

路由声明顺序
------------
所有**字面量**路径（``/list`` / ``/getList`` / ``/treeselect`` / ``/treeselectNew`` /
``/roleDeptTreeselect/{roleId}`` / ``/getCompanyList``）必须写在 ``/{dept_id}`` 之前：
FastAPI 按注册顺序匹配，否则 ``GET /system/dept/treeselect`` 会被当成
``dept_id = "treeselect"``（并且因为类型是 ``int`` 直接 422）。Spring 的
``AntPathMatcher`` 本来就优先字面量，两者结果一致。

``@Log(title = "部门管理", ...)``
--------------------------------
``add`` / ``edit`` / ``remove`` 带 ``@Log``，由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType`` 依次是
``INSERT`` / ``UPDATE`` / ``DELETE``。见 ``COMPATIBILITY.md`` §27.2。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.constant.user_constants import DEPT_DISABLE, NOT_UNIQUE_OLD
from app.common.core.controller.base_controller import bind_query_params, to_ajax
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dept import DEPT_CONSTRAINTS, SysDept
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.common_util import is_null
from app.common.utils.string_utils import split
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.service.sys_dept_service import SysDeptService, get_dept_service

logger = logging.getLogger("app.api.system.sys_dept_controller")

router = APIRouter(prefix="/system/dept", tags=["system-dept"])

#: Java: ``com.ruoyi.web.controller.system.SysDeptController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysDeptController"

#: Java: ``private static final String UNIT_FLAG = "1";`` —— ``is_uint`` 的"是单位"取值。
UNIT_FLAG = "1"

#: Java: ``新增部门'" + dept.getDeptName() + "'失败，部门名称已存在``
ADD_DEPT_NAME_EXISTS = "新增部门'{}'失败，部门名称已存在"
#: Java: ``修改部门'" + dept.getDeptName() + "'失败，部门名称已存在``
EDIT_DEPT_NAME_EXISTS = "修改部门'{}'失败，部门名称已存在"
#: Java: ``修改部门'" + dept.getDeptName() + "'失败，上级部门不能是自己``
EDIT_DEPT_SELF_PARENT = "修改部门'{}'失败，上级部门不能是自己"
#: Java: ``该部门包含未停用的子部门！`` —— 注意是**全角**感叹号
EDIT_DEPT_HAS_ACTIVE_CHILD = "该部门包含未停用的子部门！"
#: Java: ``存在下级部门,不允许删除`` —— 半角逗号
REMOVE_HAS_CHILD = "存在下级部门,不允许删除"
#: Java: ``部门存在用户,不允许删除``
REMOVE_HAS_USER = "部门存在用户,不允许删除"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysDeptService deptService``。Spring 默认单例，
# 这里用模块级缓存复刻；测试直接替换 ``controller._DEPT_SERVICE``。

_DEPT_SERVICE: Optional[SysDeptService] = None


def _dept_service() -> SysDeptService:
    global _DEPT_SERVICE
    if _DEPT_SERVICE is None:
        _DEPT_SERVICE = get_dept_service()
    return _DEPT_SERVICE


def reset_dept_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _DEPT_SERVICE
    _DEPT_SERVICE = None


def _query_dept(request: Request) -> SysDept:
    """Java: 形参 ``SysDept dept``（**没有** ``@RequestBody``）—— 由 query string 绑定。"""
    return bind_query_params(SysDept, request.query_params)


#: 查询条件实体（``?deptName=...&status=...&flag=...``）。
DeptParam = Annotated[SysDept, Depends(_query_dept)]


def _validated_dept(dept: SysDept) -> SysDept:
    """Java: ``@Validated @RequestBody SysDept``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` 之前 ——
    见模块 docstring 的"先后"一节。约束表来自实体旁边，与 Java 注解同位置。
    """
    validate(dept, DEPT_CONSTRAINTS)
    return dept


#: 已校验的请求体。
ValidDept = Annotated[SysDept, Depends(_validated_dept)]


def _is_not_unique(result: str) -> bool:
    """Java: ``UserConstants.NOT_UNIQUE_OLD.equals(...)`` —— 字面量 ``"1"``。"""
    return NOT_UNIQUE_OLD == result


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:dept:list")
def list_depts(dept: DeptParam) -> AjaxResult:
    """获取部门列表. Java: ``@GetMapping("/list") public AjaxResult list(SysDept dept)``.

    **不分页**：返回 ``AjaxResult`` 而不是 ``TableDataInfo``，``data`` 直接是数组。
    """
    return AjaxResult.success_data(_dept_service().select_dept_list(dept))


@router.get("/getList", response_model=None)
def get_list(dept: DeptParam) -> AjaxResult:
    """``getList`` 与 ``list`` 函数体相同，但**没有** ``@PreAuthorize``。"""
    return AjaxResult.success_data(_dept_service().select_dept_list(dept))


@router.get("/list/exclude/{dept_id}", response_model=None)
@pre_authorize_permi("system:dept:list")
def exclude_child(dept_id: int) -> AjaxResult:
    """查询部门列表（排除节点）.

    Java: ``@GetMapping("/list/exclude/{deptId}")`` —— 排除"自己"和"自己的所有后代"。
    判据是 ``ancestors`` 的**字符串**包含（``ArrayUtils.contains(ancestors.split(","), deptId+"")``），
    不是树遍历；因此 ``ancestors = null`` 的脏数据**不会**被排除。
    """
    depts = _dept_service().select_dept_list(SysDept())
    return AjaxResult.success_data(
        [dept for dept in depts if not _is_excluded(dept, dept_id)]
    )


@router.get("/treeselect", response_model=None)
def treeselect(dept: DeptParam) -> AjaxResult:
    """获取部门下拉树列表. Java: ``@GetMapping("/treeselect")``.

    返回 ``TreeSelect`` 数组：``{"id":..,"label":..}``，叶子节点**没有** ``children`` 键。
    """
    depts = _dept_service().select_dept_list(dept)
    return AjaxResult.success_data(_dept_service().build_dept_tree_select(depts))


@router.get("/treeselectNew", response_model=None)
def treeselect_new(dept: DeptParam) -> AjaxResult:
    """获取部门下拉树列表（按 ``flag`` 切查询范围）.

    Java: ``@GetMapping("/treeselectNew")``。``flag`` 分支见 :func:`_apply_flag`；
    **未知 flag 落到 else，查的是一个不存在的部门（``deptId = -1``）**，不是查全部。
    """
    _apply_flag(dept)
    depts = _dept_service().select_dept_list(dept)
    return AjaxResult.success_data(_dept_service().build_dept_tree_select(depts))


@router.get("/roleDeptTreeselect/{role_id}", response_model=None)
def role_dept_treeselect(role_id: int) -> AjaxResult:
    """加载对应角色部门列表树. Java: ``@GetMapping("/roleDeptTreeselect/{roleId}")``.

    返回 ``{"code","msg","checkedKeys":[...],"depts":[...]}`` —— 先 ``success()`` 再
    ``put``，所以 ``checkedKeys`` 排在 ``code``/``msg`` 之后（``AjaxResult`` 是
    ``LinkedHashMap`` 语义）。
    """
    depts = _dept_service().select_dept_list(SysDept())
    ajax = AjaxResult.success()
    ajax.put_chain("checkedKeys", _dept_service().select_dept_list_by_role_id(role_id))
    ajax.put_chain("depts", _dept_service().build_dept_tree_select(depts))
    return ajax


@router.get("/getCompanyList", response_model=None)
def get_company_list() -> AjaxResult:
    """获取单位列表信息. Java: ``@GetMapping("/getCompanyList")``.

    等价于 ``GET /list?isUint=1``，但没有权限点、也不接受任何查询条件。
    """
    query_bo = SysDept(is_uint=UNIT_FLAG)
    return AjaxResult.success_data(_dept_service().select_dept_list(query_bo))


@router.get("/{dept_id}", response_model=None)
@pre_authorize_permi("system:dept:query")
def get_info(dept_id: int) -> AjaxResult:
    """根据部门编号获取详细信息.

    Java: ``@GetMapping(value = "/{deptId}")`` —— ``value`` 是单值，没有尾斜杠变体。
    部门不存在时 ``data`` 键整体消失（Java ``AjaxResult.success(null)``）。
    """
    return AjaxResult.success_data(_dept_service().select_dept_by_id(dept_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:dept:add")
@log(title="部门管理", business_type=BusinessType.INSERT, java_method="add")
def add(dept: ValidDept) -> AjaxResult:
    """新增部门. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysDept dept)``.

    判重只在**同一父节点**下做（``checkDeptNameUnique`` 的 where 带 ``parent_id``），
    所以不同分公司下可以有同名部门。
    """
    if _is_not_unique(_dept_service().check_dept_name_unique(dept)):
        return AjaxResult.error_message(ADD_DEPT_NAME_EXISTS.format(dept.dept_name))
    dept.create_by = SecurityUtils.get_username()
    return to_ajax(_dept_service().insert_dept(dept))


@router.put("", response_model=None)
@pre_authorize_permi("system:dept:edit")
@log(title="部门管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(dept: ValidDept) -> AjaxResult:
    """修改部门. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysDept dept)``.

    三道闸，顺序不能变：名称判重 -> 上级不能是自己 -> 停用前不能有未停用的子部门。
    """
    if _is_not_unique(_dept_service().check_dept_name_unique(dept)):
        return AjaxResult.error_message(EDIT_DEPT_NAME_EXISTS.format(dept.dept_name))
    elif _same_id(dept.parent_id, dept.dept_id):
        return AjaxResult.error_message(EDIT_DEPT_SELF_PARENT.format(dept.dept_name))
    elif DEPT_DISABLE == dept.status and (
        _dept_service().select_normal_children_dept_by_id(dept.dept_id) > 0
    ):
        return AjaxResult.error_message(EDIT_DEPT_HAS_ACTIVE_CHILD)
    dept.update_by = SecurityUtils.get_username()
    return to_ajax(_dept_service().update_dept(dept))


@router.delete("/{dept_id}", response_model=None)
@pre_authorize_permi("system:dept:remove")
@log(title="部门管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(dept_id: int) -> AjaxResult:
    """删除部门. Java: ``@DeleteMapping("/{deptId}")``.

    有下级 -> 拒绝；有用户 -> 拒绝；否则逻辑删除（``del_flag = '2'``）。
    两道检查都是 ``count > 0``，错误信息里带半角逗号。
    """
    if _dept_service().has_child_by_dept_id(dept_id):
        return AjaxResult.error_message(REMOVE_HAS_CHILD)
    if _dept_service().check_dept_exist_user(dept_id):
        return AjaxResult.error_message(REMOVE_HAS_USER)
    return to_ajax(_dept_service().delete_dept_by_id(dept_id))


__all__ = [
    "router",
    "UNIT_FLAG",
    "ADD_DEPT_NAME_EXISTS",
    "EDIT_DEPT_NAME_EXISTS",
    "EDIT_DEPT_SELF_PARENT",
    "EDIT_DEPT_HAS_ACTIVE_CHILD",
    "REMOVE_HAS_CHILD",
    "REMOVE_HAS_USER",
    "DeptParam",
    "ValidDept",
    "list_depts",
    "get_list",
    "exclude_child",
    "treeselect",
    "treeselect_new",
    "role_dept_treeselect",
    "get_company_list",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_dept_controller",
]


# --------------------------------------------------------------------------- helpers


def _is_excluded(dept: SysDept, dept_id: int) -> bool:
    """Java ``excludeChild`` 的循环体：``d.deptId == deptId || ancestors 含 deptId``.

    ``d.getDeptId().intValue()`` 在 ``deptId`` 为 ``null`` 时 NPE；这里同样抛错，
    免得脏数据被静默放过。
    """
    if dept.dept_id is None:
        raise AttributeError("'NoneType' object has no attribute 'intValue'")
    if dept.dept_id == dept_id:
        return True
    ancestors = split(dept.ancestors, ",")
    # Java: ArrayUtils.contains(String[], String) —— 数组为 null 时返回 false。
    return ancestors is not None and str(dept_id) in ancestors


def _apply_flag(dept: SysDept) -> None:
    """Java ``treeselectNew`` 里那串 ``if (flag.equals(...))``。

    ==================  ==========================================================
    flag                动作
    ==================  ==========================================================
    ``myDept``          ``tenantId = SecurityUtils.getTenantId()``（本单位）
    ``myDeptCg``        同上
    ``sjzbDept``        ``dataId = getTenantId() + ""``（上级有资格的招标单位）
    ``sjzbDeptCg``      同上
    ``isUint``          ``isUint = "1"``（查单位）
    ``allDept``         什么都不做（查全部）
    ``onlyMyDept``      ``deptId = SecurityUtils.getEpsId()``（只看自己所在部门）
    （其他 / 空）        ``deptId = -1`` —— **不是查全部**
    ==================  ==========================================================

    ``flag`` 先用 :func:`app.common.utils.common_util.is_null` 归一（``null`` -> ``""``
    并 trim），所以 ``flag`` 传 ``null`` 时走最后一个分支。
    """
    flag = is_null(dept.flag)
    if flag in ("myDept", "myDeptCg"):
        # 本单位
        dept.tenant_id = SecurityUtils.get_tenant_id()
    elif flag in ("sjzbDept", "sjzbDeptCg"):
        # 上级有资格的招标单位
        dept.data_id = str(SecurityUtils.get_tenant_id())
    elif flag == "isUint":
        # 查询单位
        dept.is_uint = UNIT_FLAG
    elif flag == "allDept":
        pass
    elif flag == "onlyMyDept":
        dept.dept_id = SecurityUtils.get_eps_id()
    else:
        dept.dept_id = -1


def _same_id(left: Optional[int], right: Optional[int]) -> bool:
    """Java: ``dept.getParentId().equals(dept.getDeptId())``.

    接收者为 ``null`` 时 NPE（这里抛 ``AttributeError``）；参数为 ``null`` 时返回
    ``false``。**不能**写成 ``left == right``：``None == None`` 会变成 ``True``，
    而 Java 会炸。
    """
    if left is None:
        raise AttributeError("'NoneType' object has no attribute 'equals'")
    return left == right
