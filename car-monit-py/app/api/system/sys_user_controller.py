"""用户信息.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUserController.java

端点清单（19 个映射，全部迁移）
---------------------------------
    =======================================  =======  ===============================  ==========
    Java                                      Method   Path                             Access
    =======================================  =======  ===============================  ==========
    ``list(SysUser)``                          GET      ``/system/user/list``            login
    ``listAll(SysUser)``                       GET      ``/system/user/listAll``         login
    ``listTenantIdAll(SysUser)``               GET      ``/system/user/listTenantIdAll`` login
    ``listutil(SysUser)``                      GET      ``/system/user/listutil``        login
    ``listSameUtil(SysUser)``                  GET      ``/system/user/listSameUtil``    login
    ``listMy(SysUser)``                        GET      ``/system/user/listMy``          login
    ``export(SysUser)``                        GET      ``/system/user/export``          export
    ``importData(MultipartFile, boolean)``     POST     ``/system/user/importData``      import
    ``importTemplate()``                       GET      ``/system/user/importTemplate``  login
    ``getInfo(Long)``                          GET      ``/system/user/`` + ``/{userId}`` query
    ``add(SysUser)``                           POST     ``/system/user``                 add
    ``edit(SysUser)``                          PUT      ``/system/user``                 edit
    ``remove(Long[])``                         DELETE   ``/system/user/{userIds}``       remove
    ``resetPwd(SysUser)``                      PUT      ``/system/user/resetPwd``        resetPwd
    ``changeStatus(SysUser)``                  PUT      ``/system/user/changeStatus``    edit
    ``bindUky(SysUser)``                       PUT      ``/system/user/bindUky``         login
    ``getroleUser(String)``                    GET      ``/system/user/getroleUser/{x}`` login
    ``listByDept(SysUser)``                    GET      ``/system/user/list/dept``       login
    ``selectCurrentUser()``                    GET      ``/system/user/currentUser``     login
    =======================================  =======  ===============================  ==========

``export`` / ``importTemplate`` / ``importData`` 三个 Excel 端点
----------------------------------------------------------------
Phase 3.18 补齐（``app.common.utils.poi.excel_util``）。三个端点各自的行为：

=============================  ==================================================
端点                           返回 / 副作用
=============================  ==================================================
``GET /export``                 ``{"code":200,"msg":"<uuid>_用户数据.xlsx"}`` ——
                               文件名在 ``msg``，**不在** ``data``；文件落在
                               ``{ruoyi.profile}/download/``
``GET /importTemplate``         同上，但 sheet 名 ``"用户数据"``，内容是
                               **18 列的导入模板**（无数据行）；``type=IMPORT``
                               的列在这里才出现（如 ``部门编号``），而
                               ``type=EXPORT`` 的列（最后登录IP/时间、部门名称）
                               不出现
``POST /importData``           解析上传的 xlsx 后逐行导入；全成功回
                               ``success("恭喜您，...")``，有失败则抛
                               ``CustomException`` -> ``code 500`` + 明细串
=============================  ==================================================

``importData`` 的两个参数在 Java 里是 ``(MultipartFile file, boolean updateSupport)``：
``file`` 是必填的表单文件字段，``updateSupport`` 是**基本类型**（缺省即 ``false``）。
Spring 把它当"普通请求参数"绑定，所以表单字段与查询串两种写法都收；这里两份都支持。

``importData`` 不做唯一性预检：它只按 ``userName`` 查一次——存在且
``updateSupport=false`` 则计入失败，**不**调 ``checkUserNameUnique`` /
``checkPhoneUnique``。所以导入一个手机号与别人重复的新账号会直接撞库的唯一索引，
被内层 ``catch`` 计入失败。

``@Log(...)`` 注解
---------------------------
``add`` / ``edit`` / ``remove`` / ``resetPwd`` / ``changeStatus`` / ``export`` / ``importData``
带 ``@Log(title = "用户管理", businessType = ...)``，由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``：``businessType`` 依次是
``INSERT`` / ``UPDATE`` / ``DELETE`` / ``UPDATE`` / ``UPDATE`` / ``EXPORT`` / ``IMPORT``。

路由声明顺序
------------
FastAPI 按**注册顺序**匹配，Spring 的 ``AntPathMatcher`` 则优先"字面量 > 模板"。把
``/list`` / ``/list/dept`` / ``/currentUser`` 等字面量路径写在 ``/{user_id}`` **之前**，
两者结果一致；调换顺序会让 ``GET /system/user/list`` 被当成 ``userId = "list"``。

``GET /system/user`` 与 ``GET /system/user/``
--------------------------------------------
Java 的 ``@GetMapping({"/", "/{userId}"})`` 同时接受这两种写法（Spring 5.3 的
``useTrailingSlashMatch`` 默认开启）。FastAPI 默认会把前者 307 重定向到后者，为了让
"不跟随重定向"的客户端也能拿到 200，这里给同一个处理函数挂了两个路由。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.util.common_util import check_password, is_null
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.string_utils import is_empty, is_not_blank, is_not_empty
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.service.sys_post_service import SysPostService, get_post_service
from app.system.service.sys_role_service import SysRoleService, get_role_service
from app.system.service.sys_user_service import SysUserService, get_user_service
from app.common.core.domain.entity.sys_user import SysUser

logger = logging.getLogger("app.api.system.sys_user_controller")

router = APIRouter(prefix="/system/user", tags=["system-user"])

#: Java: ``com.ruoyi.web.controller.system.SysUserController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysUserController"

#: Java: ``新增用户'" + userName + "'失败，登录账号已存在``
ADD_USER_NAME_EXISTS = "新增用户'{}'失败，登录账号已存在"
#: Java: ``新增用户'" + userName + "'失败，手机号码已存在``
ADD_PHONE_EXISTS = "新增用户'{}'失败，手机号码已存在"
#: Java: ``新增用户'" + userName + "'失败，邮箱账号已存在``
ADD_EMAIL_EXISTS = "新增用户'{}'失败，邮箱账号已存在"
#: Java: ``修改用户'" + userName + "'失败，手机号码已存在``
EDIT_PHONE_EXISTS = "修改用户'{}'失败，手机号码已存在"
#: Java: ``修改用户'" + userName + "'失败，邮箱账号已存在``
EDIT_EMAIL_EXISTS = "修改用户'{}'失败，邮箱账号已存在"
#: Java: ``"对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号"``
#: 注意 ``add`` / ``resetPwd`` 的这句**没有**结尾感叹号，而 ``SysLoginController`` 里那句有。
PASSWORD_INVALID_MESSAGE = "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号"

#: Java: ``listutil`` 里 ``else { user.setUserId(-1l); }`` —— 未识别的 flag 查不到任何数据。
UNKNOWN_FLAG_USER_ID = -1

#: Spring ``StringToBooleanConverter`` 的真值集合（其余非空值抛转换异常 -> 400）。
#: 本工程只在 ``importData`` 的 ``updateSupport`` 上用到。
_TRUE_LITERALS = frozenset({"true", "on", "yes", "1"})
_FALSE_LITERALS = frozenset({"false", "off", "no", "0"})


# --------------------------------------------------------------------------- 依赖
#
# Java 三个 ``@Autowired`` 字段。Spring 默认单例，这里用模块级缓存复刻；测试替换缓存
# 对象（``_USER_SERVICE = fake``）即可注入假实现。

_USER_SERVICE: Optional[SysUserService] = None
_ROLE_SERVICE: Optional[SysRoleService] = None
_POST_SERVICE: Optional[SysPostService] = None


# Java: @Autowired private ISysUserService userService
def _user_service() -> SysUserService:
    global _USER_SERVICE
    if _USER_SERVICE is None:
        _USER_SERVICE = get_user_service()
    return _USER_SERVICE


# Java: @Autowired private ISysRoleService roleService
def _role_service() -> SysRoleService:
    global _ROLE_SERVICE
    if _ROLE_SERVICE is None:
        _ROLE_SERVICE = get_role_service()
    return _ROLE_SERVICE


# Java: @Autowired private ISysPostService postService
def _post_service() -> SysPostService:
    global _POST_SERVICE
    if _POST_SERVICE is None:
        _POST_SERVICE = get_post_service()
    return _POST_SERVICE


def reset_user_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _USER_SERVICE, _ROLE_SERVICE, _POST_SERVICE
    _USER_SERVICE = None
    _ROLE_SERVICE = None
    _POST_SERVICE = None


def _query_user(request: Request) -> SysUser:
    """Java: 形参 ``SysUser user``（**没有** ``@RequestBody``）—— 由 query string 绑定。

    规则见 :func:`app.common.core.controller.base_controller.bind_query_params`。
    """
    return bind_query_params(SysUser, request.query_params)


#: 查询条件实体（``?userName=...&status=...&params[beginTime]=...``）。
UserParam = Annotated[SysUser, Depends(_query_user)]


def _string_of(value: Any) -> str:
    """Java: ``tenantId + ""`` —— ``null`` 拼成字面量 ``"null"`` 而不是抛异常。"""
    return "null" if value is None else str(value)


def _query_bool(request: Request, name: str, default: bool) -> bool:
    """Java: 方法形参 ``boolean updateSupport`` —— 从**请求参数**绑定.

    Spring 对没有 ``@RequestParam`` 的基本类型参数走 "普通请求参数" 绑定，
    而 ``HttpServletRequest#getParameter`` 在 multipart 请求下同时覆盖**查询串**
    与**表单字段**（Servlet 3.0 的 multipart 支持）。RuoYi 前端用的是表单字段
    （``formData.append("updateSupport", ...)``），这里再兼容查询串。

    真值集合照抄 Spring 的 ``StringToBooleanConverter``；无法识别时它抛
    ``IllegalArgumentException`` -> HTTP 400，这里保持同样的语义。
    """
    raw = request.query_params.get(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in _TRUE_LITERALS:
        return True
    if lowered in _FALSE_LITERALS:
        return False
    raise ValueError(f"Failed to convert value of type 'java.lang.String' to required type 'boolean'")


def _parse_id_array(raw: str) -> List[int]:
    """Java: ``@PathVariable Long[] userIds`` —— 实现已提到 ``base_controller``。

    Spring 由 ``StringToArrayConverter`` 完成，属于“框架自动做、Python 必须手写”的那类，
    因此放在 :mod:`app.common.core.controller.base_controller`；这里保留原名字以免
    调用点/测试写串。
    """
    return parse_id_array(raw)


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
def list_users(user: UserParam) -> TableDataInfo:
    """查询本单位的机构用户：机构用户管理.

    Java: ``@GetMapping("/list") public TableDataInfo list(SysUser user)``.
    """
    start_page()
    # 查询机构用户
    user.user_type = "1"
    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


@router.get("/listAll", response_model=None)
def list_all(user: UserParam) -> TableDataInfo:
    """查询自己单位所有的用户 (包含1=机构用户2专家3供应商).

    Java: ``@GetMapping("/listAll")``.
    """
    start_page()
    user.tenant_id = SecurityUtils.get_tenant_id()
    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


@router.get("/listTenantIdAll", response_model=None)
def list_tenant_id_all(user: UserParam) -> TableDataInfo:
    """根据租户 id 查询机构用户（需要传入租户 ID）.

    Java: ``@GetMapping("/listTenantIdAll")``. ``userType`` 前台页面传入，非必填。
    租户 id 缺省时取 ``-1``，即查不到任何数据 —— 与 Java 一致（不是"查全部"）。
    """
    start_page()
    if user.tenant_id is None:
        user.tenant_id = -1
    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


@router.get("/listutil", response_model=None)
def list_util(user: UserParam) -> TableDataInfo:
    """获取用户列表 (没权限) —— 弹出页面组件.

    Java: ``@GetMapping("/listutil")``. ``flag`` 决定筛选口径；无法识别的 flag
    （包括缺省）会把 ``userId`` 置为 ``-1``，即"查不到任何人"而不是"查所有人"。
    """
    start_page()
    # 根据 flag 来查询
    flag = is_null(user.flag)
    # 查询机构用户
    if flag == "myDept":
        user.status = "0"
        user.user_type = "1"
        user.tenant_id = SecurityUtils.get_tenant_id()
    elif flag == "myDeptCg":
        user.status = "0"
        user.user_type = "1"
        user.tenant_id = SecurityUtils.get_tenant_id()
    elif flag == "sjzbDept" or flag == "sjzbDeptCg":
        # 上级有资格的招标单位
        user.data_id = _string_of(SecurityUtils.get_tenant_id())
    elif flag == "allDept":
        # Java 这里是空分支，刻意什么都不做
        pass
    else:
        user.user_id = UNKNOWN_FLAG_USER_ID

    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


@router.get("/listSameUtil", response_model=None)
def list_same_util(user: UserParam) -> TableDataInfo:
    """获取用户列表同部门 —— 弹出页面组件.

    Java: ``@GetMapping("/listSameUtil")``.
    """
    start_page()
    user.status = "0"
    user.user_type = "1"
    user.tenant_id = SecurityUtils.get_tenant_id()
    user.dept_id = SecurityUtils.get_eps_id()
    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


@router.get("/listMy", response_model=None)
def list_my(user: UserParam) -> TableDataInfo:
    """查询自己. Java: ``@GetMapping("/listMy")``."""
    start_page()
    user.user_id = SecurityUtils.get_user_id()
    rows = _user_service().select_user_list(user)
    return get_data_table(rows)


# --------------------------------------------------------------------------- Excel


@router.get("/export", response_model=None)
@pre_authorize_permi("system:user:export")
@log(title="用户管理", business_type=BusinessType.EXPORT, java_method="export")
def export(user: UserParam) -> AjaxResult:
    """导出用户数据. Java: ``@GetMapping("/export") public AjaxResult export(SysUser user)``.

    导出 **21 列**：``deptId`` 是 ``Type.IMPORT`` 被过滤掉，``dept`` 上的
    ``@Excels`` 展开成两列（部门名称 / 部门负责人）。不分页 —— Java 侧没有
    ``startPage()``。

    ``msg`` 是生成的文件名（不是文件内容）。
    """
    rows = _user_service().select_user_list(user)
    return ExcelUtil(SysUser).export_excel(rows, "用户数据")


@router.get("/importTemplate", response_model=None)
def import_template() -> AjaxResult:
    """下载用户导入模板. Java: ``@GetMapping("/importTemplate") public AjaxResult importTemplate()``.

    **没有** ``@PreAuthorize`` —— 登录即可下载。

    ``type=IMPORT`` 才会过滤出模板列：``loginIp`` / ``loginDate`` / ``dept`` 两列
    （都是 ``Type.EXPORT``）不出现，``deptId``（``Type.IMPORT``）反而出现，
    所以模板是 **18 列**，与导出的 21 列不同。
    """
    return ExcelUtil(SysUser).import_template_excel("用户数据")


@router.post("/importData", response_model=None)
@pre_authorize_permi("system:user:import")
@log(title="用户管理", business_type=BusinessType.IMPORT, java_method="importData")
def import_data(
    request: Request,
    file: Annotated[UploadFile, File()],
    update_support: Annotated[Optional[bool], Form(alias="updateSupport")] = None,
) -> AjaxResult:
    """用户导入. Java: ``@PostMapping("/importData")`` —— ``(MultipartFile file, boolean updateSupport)``.

    ``updateSupport`` 优先取**表单字段**（前端就是这么发的），其次退到**查询串**；
    见 :func:`_query_bool`。

    解析失败（不是 xlsx / 首行不是表头）会抛 ``UtilException``；
    ``importUser`` 有失败行时抛 ``CustomException``。两者都是 HTTP 200 + ``code 500``，
    但文案不同。
    """
    resolved = (
        update_support
        if update_support is not None
        else _query_bool(request, "updateSupport", False)
    )
    # Java: util.importExcel(file.getInputStream())
    user_list = ExcelUtil(SysUser).import_excel(file.file)
    # Java: LoginUser loginUser = tokenService.getLoginUser(...); operName = loginUser.getUsername();
    oper_name = SecurityUtils.get_username()
    message = _user_service().import_user(user_list, resolved, oper_name)
    # Java: AjaxResult.success(message) —— 明细串落在 msg 里
    return AjaxResult.success_message(message)


@router.get("/list/dept", response_model=None)
def list_by_dept(user: UserParam) -> TableDataInfo:
    """根据部门查询对应部门的人员信息.

    Java: ``@GetMapping("/list/dept") public TableDataInfo listByDept(SysUser user)``.
    """
    start_page()
    eps_id = SecurityUtils.get_eps_id()
    if eps_id is not None:
        user.dept_id = eps_id
    # 是否过滤掉自己
    if user.exclude_self is not None and user.exclude_self:
        user.exclude_id = SecurityUtils.get_user_id()

    # 查询机构用户
    user.user_type = "1"
    rows = _user_service().select_user_list(user)
    # 设置部门名称
    for data in rows:
        if data.dept is not None and is_not_blank(data.dept.dept_name):
            data.dept_name = data.dept.dept_name
    return get_data_table(rows)


@router.get("/getroleUser/{role_code}", response_model=None)
def getrole_user(role_code: str) -> AjaxResult:
    """根据角色名称获取人员信息.

    Java: ``@GetMapping("/getroleUser/{roleCode}")``. 没有 ``startPage()``，因此返回
    **全量**列表（不带分页信封）——这是 Java 的现状，不要"顺手"加上分页。
    """
    user = SysUser()
    user.role_code = role_code
    user.tenant_id = SecurityUtils.get_tenant_id()
    return AjaxResult.success_data(_user_service().select_user_list(user))


@router.get("/currentUser", response_model=None)
def select_current_user() -> AjaxResult:
    """获取当前用户信息（是否总公司人员 / 是否采购经理）.

    Java: ``@GetMapping("/currentUser") public AjaxResult selectCurrentUser()``.
    """
    return AjaxResult.success_data(_user_service().select_current_user())


# --------------------------------------------------------------------------- 详情


def _get_info(user_id: Optional[int]) -> AjaxResult:
    """Java: ``getInfo(Long userId)`` 的公共实现（两个路由共用）。"""
    ajax = AjaxResult.success()
    roles = _role_service().select_role_all()
    # Java: SysUser.isAdmin(userId) ? roles : roles.stream().filter(r -> !r.isAdmin())...
    # 注意判据是 **userId**（被查看的人），不是当前登录用户：查看超管时列出全部角色，
    # 查看普通人时隐藏"超级管理员"角色，防止把 admin 角色授给普通账号。
    ajax.put_chain("roles", roles if SysUser.is_admin(user_id) else [r for r in roles if not r.admin])
    ajax.put_chain("posts", _post_service().select_post_all())
    if user_id is not None:
        ajax.put_chain(AjaxResult.DATA_TAG, _user_service().select_user_by_id(user_id))
        ajax.put_chain("postIds", _post_service().select_post_list_by_user_id(user_id))
        ajax.put_chain("roleIds", _role_service().select_role_list_by_user_id(user_id))
    return ajax


# Java 的 ``@GetMapping(value = {"/", "/{userId}"})`` **只**占住 ``/system/user/`` 和
# ``/system/user/{id}``，不带尾斜杠的 ``/system/user`` 只被下面的 ``@PostMapping``
# （``add``）占着。实测 Java 对 ``GET /system/user`` 回
# ``{"code":500,"msg":"Request method 'GET' not supported"}``（HTTP 200），
# 对 ``GET /system/user/`` 回 200 —— 所以这里**不能**再挂一个 ``@router.get("")``：
# FastAPI 会同时命中，而 Java 不会。不带尾斜杠时 Starlette 找不到 GET 全匹配、
# 只剩 POST 的部分匹配 -> 405 -> 交给 :mod:`app.config.exception_handlers` 翻成
# 上面那条 JSON，与 Java 完全一致。
@router.get("/", response_model=None)
@pre_authorize_permi("system:user:query")
def get_info() -> AjaxResult:
    """根据用户编号获取详细信息（无 userId：只回下拉框数据）.

    Java: ``@GetMapping(value = {"/", "/{userId}"})`` 在 ``userId`` 缺省时的分支。
    """
    return _get_info(None)


@router.get("/{user_id}", response_model=None)
@pre_authorize_permi("system:user:query")
def get_info_by_id(user_id: int) -> AjaxResult:
    """根据用户编号获取详细信息.

    Java: ``@GetMapping(value = {"/", "/{userId}"})``.
    """
    return _get_info(user_id)


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None)
@pre_authorize_permi("system:user:add")
@log(title="用户管理", business_type=BusinessType.INSERT, java_method="add")
def add(user: SysUser) -> AjaxResult:
    """新增用户. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysUser user)``.

    ``@Validated`` 在本项目里是空转：``SysUser`` 的 ``@NotBlank`` / ``@Size`` / ``@Email``
    全部被注释掉了（见 Java 源码 375-404 行），所以参数校验只剩下面这些手写分支。
    """
    if _is_not_unique(_user_service().check_user_name_unique(user.user_name)):
        return AjaxResult.error_message(ADD_USER_NAME_EXISTS.format(user.user_name))
    elif is_not_empty(user.phonenumber) and _is_not_unique(_user_service().check_phone_unique(user)):
        return AjaxResult.error_message(ADD_PHONE_EXISTS.format(user.user_name))
    elif is_not_empty(user.email) and _is_not_unique(_user_service().check_email_unique(user)):
        return AjaxResult.error_message(ADD_EMAIL_EXISTS.format(user.user_name))

    if check_password(user.password):
        return AjaxResult.error_message(PASSWORD_INVALID_MESSAGE)

    user.create_by = SecurityUtils.get_username()
    user.password = SecurityUtils.encrypt_password(user.password)
    return to_ajax(_user_service().insert_user(user))


@router.put("", response_model=None)
@pre_authorize_permi("system:user:edit")
@log(title="用户管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(user: SysUser) -> AjaxResult:
    """修改用户. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysUser user)``.

    ``checkUserAllowed`` 会抛 ``CustomException``（"不允许操作超级管理员用户"），
    由通用处理器翻成 HTTP 200 + ``code 500``。
    """
    _user_service().check_user_allowed(user)
    if is_not_empty(user.phonenumber) and _is_not_unique(_user_service().check_phone_unique(user)):
        return AjaxResult.error_message(EDIT_PHONE_EXISTS.format(user.user_name))
    elif is_not_empty(user.email) and _is_not_unique(_user_service().check_email_unique(user)):
        return AjaxResult.error_message(EDIT_EMAIL_EXISTS.format(user.user_name))

    user.update_by = SecurityUtils.get_username()
    return to_ajax(_user_service().update_user(user))


@router.delete("/{user_ids}", response_model=None)
@pre_authorize_permi("system:user:remove")
@log(title="用户管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(user_ids: str) -> AjaxResult:
    """删除用户. Java: ``@DeleteMapping("/{userIds}") public AjaxResult remove(@PathVariable Long[] userIds)``.

    路径里的 ``1,2,3`` 被 Spring 转成 ``Long[]{1,2,3}``；这里同样按逗号切分。
    """
    return to_ajax(_user_service().delete_user_by_ids(_parse_id_array(user_ids)))


@router.put("/resetPwd", response_model=None)
@pre_authorize_permi("system:user:resetPwd")
@log(title="用户管理", business_type=BusinessType.UPDATE, java_method="resetPwd")
def reset_pwd(user: SysUser) -> AjaxResult:
    """重置密码. Java: ``@PutMapping("/resetPwd") public AjaxResult resetPwd(@RequestBody SysUser user)``.

    注意这里**没有** ``@Validated``：``password`` 为 ``null`` 时 ``CommonUtil.checkPassword``
    会 NPE（Java 侧落到 ``@ExceptionHandler(RuntimeException.class)``），Python 侧对应
    ``TypeError``，同样落到通用处理器，都是 HTTP 200 + ``code 500``。
    """
    password = user.password
    if check_password(password):
        return AjaxResult.error_message(PASSWORD_INVALID_MESSAGE)

    _user_service().check_user_allowed(user)
    user.password = SecurityUtils.encrypt_password(password)
    user.update_by = SecurityUtils.get_username()
    return to_ajax(_user_service().reset_pwd(user))


@router.put("/changeStatus", response_model=None)
@pre_authorize_permi("system:user:edit")
@log(title="用户管理", business_type=BusinessType.UPDATE, java_method="changeStatus")
def change_status(user: SysUser) -> AjaxResult:
    """状态修改. Java: ``@PutMapping("/changeStatus")``."""
    _user_service().check_user_allowed(user)
    user.update_by = SecurityUtils.get_username()
    return to_ajax(_user_service().update_user_status(user))


@router.put("/bindUky", response_model=None)
def bind_uky(user: SysUser) -> AjaxResult:
    """绑定 ukey / CA. Java: ``@PutMapping("/bindUky") public AjaxResult bindUky(@RequestBody SysUser user)``.

    "已绑定"的判断是 ``selectUserList(certEntityId)``：只要查到任意一行且它的 ``userId``
    不是自己，就拒绝。因此**同一实体标识绑到自己**是允许的（重复提交不会报错）。
    两次 ``selectUserList`` 都没有 ``startPage()``，取的是全量结果。
    """
    if user.user_id is None:
        # 获取当前用户绑定 CA
        user.user_id = SecurityUtils.get_user_id()

    if is_empty(user.cert_entity_id):
        return AjaxResult.error_message("唯一实体标识不能为空")

    if is_empty(user.cert_id):
        return AjaxResult.error_message("密码卡/USD-Key序列号不能为空")

    if is_not_empty(user.cert_entity_id):
        query_bo = SysUser()
        query_bo.cert_entity_id = user.cert_entity_id
        user_list = _user_service().select_user_list(query_bo)
        if len(user_list) > 0:
            if user_list[0].user_id != user.user_id:
                return AjaxResult.error_message("唯一实体标识已绑定，请确认！")

    if is_not_empty(user.cert_id):
        query_bo = SysUser()
        query_bo.cert_id = user.cert_id
        user_list = _user_service().select_user_list(query_bo)
        if len(user_list) > 0:
            if user_list[0].user_id != user.user_id:
                return AjaxResult.error_message("密码卡/USD-Key序列号已绑定，请确认！")

    new_user = SysUser()
    new_user.user_id = user.user_id
    new_user.cert_id = user.cert_id
    new_user.cert_entity_id = user.cert_entity_id
    new_user.update_by = SecurityUtils.get_username()

    return to_ajax(_user_service().update_user_status(new_user))


def _is_not_unique(result: str) -> bool:
    """Java: ``UserConstants.NOT_UNIQUE_OLD.equals(...)``.

    ``UserConstants.NOT_UNIQUE_OLD`` 是字面量 ``"1"``，``UNIQUE_OLD`` 是 ``"0"``
    （见 :mod:`app.common.constant.user_constants`）。Service 层返回的就是这两个字符串。
    """
    from app.common.constant.user_constants import NOT_UNIQUE_OLD

    return NOT_UNIQUE_OLD == result


__all__ = [
    "router",
    "list_users",
    "list_all",
    "list_tenant_id_all",
    "list_util",
    "list_same_util",
    "list_my",
    "export",
    "import_template",
    "import_data",
    "list_by_dept",
    "getrole_user",
    "select_current_user",
    "get_info",
    "get_info_by_id",
    "add",
    "edit",
    "remove",
    "reset_pwd",
    "change_status",
    "bind_uky",
    "reset_user_controller",
    "PASSWORD_INVALID_MESSAGE",
    "UNKNOWN_FLAG_USER_ID",
]
