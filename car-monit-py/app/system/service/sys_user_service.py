"""用户 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUserService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java

Java splits this into an interface (``ISysUserService``) and an implementation
(``SysUserServiceImpl``). Python has no interfaces, so one class keeps the implementation
bodies and the module docstring names both types -- see ``app/system/service/__init__.py``.

Spring 依赖 -> 构造参数
-----------------------
Java 有 10 个 ``@Autowired`` 字段。Python 版本把它们全部做成**可选构造参数**，默认各自
``new`` 一个：既保留"单例、可替换"的语义（:func:`get_user_service` 缓存一个实例），也方便
测试注入假实现。

未迁移的方法
------------
无。``importUser`` 已在 Phase 3.18 随 ``ExcelUtil`` 一起迁入（见 :meth:`SysUserService.import_user`），
它依赖的两个子系统现在都已存在：

* ``ISysConfigService.selectConfigByKey("sys.user.initPassword")`` —— :mod:`app.system.service.sys_config_service`；
* 唯一调用方 ``SysUserController#importData`` 的 xlsx 解析 —— :class:`app.common.utils.poi.excel_util.ExcelUtil`。

事务语义（与 Java 的差异，已记录）
----------------------------------
Java 的 ``@Transactional`` 让同一个方法内的多次 Mapper 调用共用一个连接、一个事务。
本项目的 Mapper 每个方法各自 ``with session_scope()``，所以 ``insertUser`` /
``updateUser`` / ``deleteUserByIds`` 里的"先删关联再写主表"**不是原子的**。这是既有
Python 数据访问层的统一约定（见 :mod:`app.config.database`），不是本模块新引入的偏差。
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, List, Optional, Sequence

from app.common.constant.constants import PROCUREMENT_MANAGER_ROLE_KEY
from app.common.constant.user_constants import DEFAULT_PWD, NOT_UNIQUE_OLD, UNIQUE_OLD
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.exception.exceptions import CustomException
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.string_utils import is_empty
from app.framework.aspectj.data_scope_aspect import apply_data_scope
from app.system.domain.sys_user_post import SysUserPost
from app.system.domain.sys_user_role import SysUserRole
from app.system.mapper.sys_dept_mapper import SysDeptMapper
from app.system.mapper.sys_post_mapper import SysPostMapper
from app.system.mapper.sys_role_mapper import SysRoleMapper
from app.system.mapper.sys_user_mapper import SysUserMapper
from app.system.mapper.sys_user_post_mapper import SysUserPostMapper
from app.system.mapper.sys_user_role_mapper import SysUserRoleMapper
from app.system.service.sys_config_service import SysConfigService, get_config_service
from app.system.service.sys_dept_service import SysDeptService, get_dept_service
from app.system.service.sys_role_service import SysRoleService, get_role_service
from app.config.database import transactional

logger = logging.getLogger("app.system.service.sys_user_service")

#: Java: ``new CustomException("不允许操作超级管理员用户")``
CHECK_USER_ALLOWED_MESSAGE = "不允许操作超级管理员用户"

#: ``updateUserPwd`` / ``forgotPassword`` 的验证码错误提示（两处字面量相同）。
VCODE_INVALID_MESSAGE = "验证码错误或过期！"
#: ``updateUserPwd`` / ``forgotPassword`` 的账号+手机号组合不唯一提示。
ACCOUNT_INVALID_MESSAGE = "账号或手机号有误！"
#: ``updateUserPwd`` 的重置失败提示（注意是**全角**感叹号）。
RESET_PWD_FAILED_MESSAGE = "找回密码失败！"
#: ``forgotPassword`` 的重置失败提示（注意是**半角**感叹号 + 尾随空格）。
FORGOT_PWD_FAILED_MESSAGE = "找回密码失败! "

#: Java: ``new CustomException("导入用户数据不能为空！")``
IMPORT_USER_EMPTY_MESSAGE = "导入用户数据不能为空！"
#: ``importUser`` 全量失败时的前缀（注意是**全角**感叹号）。
IMPORT_FAILURE_PREFIX = "很抱歉，导入失败！共 {} 条数据格式不正确，错误如下："
#: ``importUser`` 全量成功时的前缀（注意是**全角**感叹号）。
IMPORT_SUCCESS_PREFIX = "恭喜您，数据已全部导入成功！共 {} 条，数据如下："
#: Java: ``configService.selectConfigByKey("sys.user.initPassword")`` 的键名。
IMPORT_INIT_PASSWORD_KEY = "sys.user.initPassword"


class SysUserService:
    """Java: ``ISysUserService`` (impl: ``SysUserServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysUserMapper] = None,
        role_mapper: Optional[SysRoleMapper] = None,
        post_mapper: Optional[SysPostMapper] = None,
        user_role_mapper: Optional[SysUserRoleMapper] = None,
        user_post_mapper: Optional[SysUserPostMapper] = None,
        dept_mapper: Optional[SysDeptMapper] = None,
        redis_cache: Optional[RedisCache] = None,
        dept_service: Optional[SysDeptService] = None,
        role_service: Optional[SysRoleService] = None,
        config_service: Optional[SysConfigService] = None,
    ) -> None:
        self._mapper = mapper or SysUserMapper()
        self._role_mapper = role_mapper or SysRoleMapper()
        self._post_mapper = post_mapper or SysPostMapper()
        self._user_role_mapper = user_role_mapper or SysUserRoleMapper()
        self._user_post_mapper = user_post_mapper or SysUserPostMapper()
        self._dept_mapper = dept_mapper or SysDeptMapper()
        self._redis_cache = redis_cache
        self._dept_service = dept_service
        self._role_service = role_service
        self._config_service = config_service

    # ---- Java 的 @Autowired 字段：Python 里按需惰性构造（避免构造期连 Redis） ----

    @property
    def mapper(self) -> SysUserMapper:
        return self._mapper

    @property
    def role_mapper(self) -> SysRoleMapper:
        return self._role_mapper

    @property
    def post_mapper(self) -> SysPostMapper:
        return self._post_mapper

    @property
    def user_role_mapper(self) -> SysUserRoleMapper:
        return self._user_role_mapper

    @property
    def user_post_mapper(self) -> SysUserPostMapper:
        return self._user_post_mapper

    @property
    def dept_mapper(self) -> SysDeptMapper:
        return self._dept_mapper

    @property
    def redis_cache(self) -> RedisCache:
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    @property
    def dept_service(self) -> SysDeptService:
        if self._dept_service is None:
            self._dept_service = get_dept_service()
        return self._dept_service

    @property
    def role_service(self) -> SysRoleService:
        if self._role_service is None:
            self._role_service = get_role_service()
        return self._role_service

    @property
    def config_service(self) -> SysConfigService:
        """Java: ``@Autowired private ISysConfigService configService``.

        只有 :meth:`import_user` 用它（取 ``sys.user.initPassword``），所以惰性构造。
        """
        if self._config_service is None:
            self._config_service = get_config_service()
        return self._config_service

    # Java: List<SysUser> selectUserList(SysUser user)
    def select_user_list(self, user: SysUser) -> List[SysUser]:
        """根据条件分页查询用户列表.

        Java: ``@DataScope(deptAlias = "d", userAlias = "u")``。切面在方法体之前写入
        ``user.params["dataScope"]``，这里改成显式调用。**注意**：本项目的
        ``SysUserMapper.xml#selectUserList`` 把 ``${params.dataScope}`` 注释掉了，
        所以这个片段实际不会进 SQL —— 保留调用是为了和 Java 的调用链一致。

        调用方若先 ``start_page()``，分页由 Mapper 内部的 ``take_page()`` 消费。
        """
        apply_data_scope(user, "d", "u")
        return self._mapper.select_user_list(user)

    # Java: SysUser selectUserByUserName(String userName)
    def select_user_by_user_name(self, user_name: str) -> Optional[SysUser]:
        """Delegates straight to the mapper -- no trimming, no caching, no null checks.

        ``where u.user_name = #{userName}`` compares with MySQL's default collation, which is
        case-insensitive for ``utf8mb4_general_ci``: ``"Admin"`` finds ``"admin"``. That is a
        database property, so it is preserved by *not* normalising the parameter in Python.
        """
        return self._mapper.select_user_by_user_name(user_name)

    # Java: SysUser selectUserByCertEntityID(String strCertEntityID)
    def select_user_by_cert_entity_id(self, cert_entity_id: str) -> Optional[SysUser]:
        return self._mapper.select_user_by_cert_entity_id(cert_entity_id)

    # Java: SysUser selectUserById(Long userId)
    def select_user_by_id(self, user_id: int) -> Optional[SysUser]:
        return self._mapper.select_user_by_id(user_id)

    # Java: String selectUserRoleGroup(String userName)
    def select_user_role_group(self, user_name: str) -> str:
        """用户所属角色组，逗号分隔的角色**名称**（不是 key，也不是 id）。"""
        roles = self._role_mapper.select_roles_by_user_name(user_name)
        # Java 逐个 append(name + ",")，最后 substring 掉末尾逗号 -> 等价于 join。
        return _join_names(role.role_name for role in roles)

    # Java: String selectUserPostGroup(String userName)
    def select_user_post_group(self, user_name: str) -> str:
        posts = self._post_mapper.select_posts_by_user_name(user_name)
        return _join_names(post.post_name for post in posts)

    # Java: String checkUserNameUnique(String userName)
    def check_user_name_unique(self, user_name: str) -> str:
        if self._mapper.check_user_name_unique(user_name) > 0:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # Java: String checkPhoneUnique(SysUser user)
    def check_phone_unique(self, user: SysUser) -> str:
        user_id = -1 if user.user_id is None else user.user_id
        info = self._mapper.check_phone_unique(user.phonenumber)
        # Java: info.getUserId().longValue() -- the column is NOT NULL, so no null check.
        if info is not None and info.user_id != user_id:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # Java: String checkEmailUnique(SysUser user)
    def check_email_unique(self, user: SysUser) -> str:
        user_id = -1 if user.user_id is None else user.user_id
        info = self._mapper.check_email_unique(user.email)
        if info is not None and info.user_id != user_id:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # Java: void checkUserAllowed(SysUser user)
    def check_user_allowed(self, user: SysUser) -> None:
        if user.user_id is not None and user.admin:
            raise CustomException(CHECK_USER_ALLOWED_MESSAGE)

    # Java: int insertUser(SysUser user)
    @transactional
    def insert_user(self, user: SysUser) -> int:
        if user.dept_id is not None:
            sys_dept = self._dept_mapper.select_dept_by_id(user.dept_id)
            # Java: sysDept.getDeptName() -- NPE when the部门不存在, mirrored by AttributeError.
            user.buss_name = sys_dept.dept_name
            user.tenant_id = sys_dept.tenant_id

        # 新增用户信息
        rows = self._mapper.insert_user(user)
        # 新增用户岗位关联
        self.insert_user_post(user)
        # 新增用户与角色管理
        self.insert_user_role(user)
        return rows

    # Java: int updateUser(SysUser user)
    @transactional
    def update_user(self, user: SysUser) -> int:
        user_id = user.user_id
        # 删除用户与角色关联
        self._user_role_mapper.delete_user_role_by_user_id(user_id)
        # 新增用户与角色管理
        self.insert_user_role(user)
        # 删除用户与岗位关联
        self._user_post_mapper.delete_user_post_by_user_id(user_id)
        # 新增用户与岗位管理
        self.insert_user_post(user)

        if user.dept_id is not None:
            sys_dept = self._dept_mapper.select_dept_by_id(user.dept_id)
            user.buss_name = sys_dept.dept_name
            user.tenant_id = sys_dept.tenant_id

        return self._mapper.update_user(user)

    # Java: int updateUserInfoByBussId(SysUser user)
    def update_user_info_by_buss_id(self, user: SysUser) -> int:
        return self._mapper.update_user_info_by_buss_id(user)

    # Java: int updateUserStatus(SysUser user)
    def update_user_status(self, user: SysUser) -> int:
        """状态修改走的是 **updateUser**（整行动态更新），不是 ``updateUserStatus``。

        ``SysUserMapper.xml`` 里那条 ``updateUserStatus`` 在 Java 里没有任何调用者，
        属于死语句，Mapper 里保留着，但这里不要改用它。
        """
        return self._mapper.update_user(user)

    # Java: int updateUserProfile(SysUser user)
    def update_user_profile(self, user: SysUser) -> int:
        return self._mapper.update_user(user)

    # Java: boolean updateUserAvatar(String userName, String avatar)
    def update_user_avatar(self, user_name: str, avatar: str) -> bool:
        return self._mapper.update_user_avatar(user_name, avatar) > 0

    # Java: int resetPwd(SysUser user)
    def reset_pwd(self, user: SysUser) -> int:
        return self._mapper.update_user(user)

    # Java: int resetUserPwd(String userName, String password)
    def reset_user_pwd(self, user_name: str, password: str) -> int:
        return self._mapper.reset_user_pwd(user_name, password)

    # Java: public void insertUserRole(SysUser user)
    def insert_user_role(self, user: SysUser) -> None:
        """Java 里没有 ``private`` 修饰符，所以是公开方法；保持公开。"""
        role_ids = user.role_ids
        if role_ids is not None:
            rows = [SysUserRole(user_id=user.user_id, role_id=role_id) for role_id in role_ids]
            if rows:
                self._user_role_mapper.batch_user_role(rows)

    # Java: public void insertUserPost(SysUser user)
    def insert_user_post(self, user: SysUser) -> None:
        post_ids = user.post_ids
        if post_ids is not None:
            rows = [SysUserPost(user_id=user.user_id, post_id=post_id) for post_id in post_ids]
            if rows:
                self._user_post_mapper.batch_user_post(rows)

    # Java: int deleteUserById(Long userId)
    @transactional
    def delete_user_by_id(self, user_id: int) -> int:
        # 删除用户与角色关联
        self._user_role_mapper.delete_user_role_by_user_id(user_id)
        # 删除用户与岗位表
        self._user_post_mapper.delete_user_post_by_user_id(user_id)
        return self._mapper.delete_user_by_id(user_id)

    # Java: int deleteUserByIds(Long[] userIds)
    @transactional
    def delete_user_by_ids(self, user_ids: Sequence[int]) -> int:
        for user_id in user_ids:
            # Java: checkUserAllowed(new SysUser(userId))
            self.check_user_allowed(SysUser(user_id=user_id))
        # 删除用户与角色关联
        self._user_role_mapper.delete_user_role(list(user_ids))
        # 删除用户与岗位关联
        self._user_post_mapper.delete_user_post(list(user_ids))
        return self._mapper.delete_user_by_ids(user_ids)

    # Java: AjaxResult updateUserPwd(SysUser sysUser)
    @transactional
    def update_user_pwd(self, sys_user: SysUser) -> AjaxResult:
        """通过手机号找回密码 —— 重置为**默认密码** ``UserConstants.DEFAULT_PWD``。"""
        try:
            # Java: redisCache.getCacheObject(phone).toString() -- null.toString() 会 NPE，
            # 被同一个 catch 吞掉，所以这里让 _to_string(None) 抛异常，落在同一个分支。
            vcode = _to_string(self.redis_cache.get_cache_object(sys_user.phonenumber))
        except Exception:  # noqa: BLE001 - Java catches Exception and printStackTrace()s it
            logger.exception("读取短信验证码失败")
            return AjaxResult.error_message(VCODE_INVALID_MESSAGE)

        if is_empty(sys_user.remark) or sys_user.remark != vcode:
            return AjaxResult.error_message(VCODE_INVALID_MESSAGE)

        # 根据账号查询用户
        sys_users = self._mapper.select_user_list(sys_user)
        if len(sys_users) == 0 or len(sys_users) > 1:
            return AjaxResult.error_message(ACCOUNT_INVALID_MESSAGE)

        user = SysUser()
        user.phonenumber = sys_user.phonenumber
        user.user_name = sys_user.user_name
        user.password = SecurityUtils.encrypt_password(DEFAULT_PWD)
        rows = self._mapper.update_user_pwd(user.phonenumber, user.password, user.user_name)
        # 说明更新成功
        if rows == 1:
            return AjaxResult.success_message_data("密码已重置为", DEFAULT_PWD)
        return AjaxResult.error_message(RESET_PWD_FAILED_MESSAGE)

    # Java: SysUser selectCurrentUser()
    def select_current_user(self) -> SysUser:
        """当前用户 + 两个派生标识（是否总公司人员 / 是否采购经理）。

        返回的是一个**新的瘦对象**，只带 ``userId`` / ``deptId`` / ``headOffice`` /
        ``procurementManager`` 四个字段；其余字段都是默认值（``null`` / ``false``），
        与 Java 的 JSON 完全一致。
        """
        user = SecurityUtils.get_login_user().user
        dept_id = SecurityUtils.get_eps_id()
        current_user = SysUser()
        current_user.user_id = user.user_id
        current_user.dept_id = dept_id
        # 设置默认的总公司标识
        current_user.head_office = False
        # 设置默认的采购经理角色标识
        current_user.procurement_manager = False

        # 获取总公司列表
        dept_set = self.dept_service.select_head_office()
        if dept_set:
            dept_id_set = {dept.dept_id for dept in dept_set}
            if dept_id in dept_id_set:
                current_user.head_office = True

        # 查询采购经理角色信息
        role_query_bo = SysRole(role_key=PROCUREMENT_MANAGER_ROLE_KEY)
        role_list = self.role_service.select_role_list(role_query_bo)
        if role_list:
            role = role_list[0]
            user_role_list = self._role_mapper.select_roles_by_user_name(user.user_name)
            if user_role_list:
                role_set = {user_role.role_id for user_role in user_role_list}
                if role.role_id in role_set:
                    current_user.procurement_manager = True

        return current_user

    # Java: void updateUserInfoByBussIdAndUserType(SysUser user)
    def update_user_info_by_buss_id_and_user_type(self, user: SysUser) -> None:
        """Java 声明为 ``void``，Mapper 的返回值被丢弃。这里照样返回 ``None``。"""
        self._mapper.update_user_info_by_buss_id_and_user_type(user)

    # Java: SysUser selectPwdJudge(Long userId)
    def select_pwd_judge(self, user_id: int) -> Optional[SysUser]:
        return self._mapper.select_pwd_judge(user_id)

    # Java: String importUser(List<SysUser> userList, Boolean isUpdateSupport, String operName)
    def import_user(
        self,
        user_list: Optional[Sequence[SysUser]],
        is_update_support: bool,
        oper_name: str,
    ) -> str:
        """导入用户数据.

        逐行处理，**每行独立 try/catch** —— 单行失败不中断整批。全部成功时返回
        ``"恭喜您，..."`` 前缀的明细串（每行以 ``<br/>`` 分隔）；有任一行失败则抛
        :class:`~app.common.exception.exceptions.CustomException`，由通用处理器翻成
        HTTP 200 + ``code 500`` + 同一个明细串。

        三点容易弄错的地方：

        1. ``isUpdateSupport`` 在 Java 是**基本类型** ``boolean``（Spring 绑定永远不会给
           ``null``），所以这里不需要空值判断。
        2. ``selectUserByUserName`` 用的是**库里的**大小写不敏感比较，所以导入 ``Admin``
           会更新/撞上已有的 ``admin``。
        3. ``insertUser`` / ``updateUser`` 是 ``this.`` 自调用，**不走代理** —— 导入不开启
           单个用户级别的事务回滚。这里同样是直接调用自己。
        """
        # Java: StringUtils.isNull(userList) || userList.size() == 0
        if user_list is None or len(user_list) == 0:
            raise CustomException(IMPORT_USER_EMPTY_MESSAGE)

        success_num = 0
        failure_num = 0
        success_msg: List[str] = []
        failure_msg: List[str] = []
        password = self.config_service.select_config_by_key(IMPORT_INIT_PASSWORD_KEY)

        for user in user_list:
            try:
                # 验证是否存在这个用户
                existing = self._mapper.select_user_by_user_name(user.user_name)
                if existing is None:
                    user.password = SecurityUtils.encrypt_password(password)
                    user.create_by = oper_name
                    self.insert_user(user)
                    success_num += 1
                    success_msg.append(f"<br/>{success_num}、账号 {_text(user.user_name)} 导入成功")
                elif is_update_support:
                    user.update_by = oper_name
                    self.update_user(user)
                    success_num += 1
                    success_msg.append(f"<br/>{success_num}、账号 {_text(user.user_name)} 更新成功")
                else:
                    failure_num += 1
                    failure_msg.append(f"<br/>{failure_num}、账号 {_text(user.user_name)} 已存在")
            except Exception as exc:  # noqa: BLE001 —— Java 这里也是 catch (Exception e)
                failure_num += 1
                msg = f"<br/>{failure_num}、账号 {_text(user.user_name)} 导入失败："
                failure_msg.append(msg + str(exc))
                logger.error("%s", msg, exc_info=exc)

        if failure_num > 0:
            # Java: failureMsg.insert(0, "很抱歉，...")
            raise CustomException(IMPORT_FAILURE_PREFIX.format(failure_num) + "".join(failure_msg))

        # Java: successMsg.insert(0, "恭喜您，...")
        return IMPORT_SUCCESS_PREFIX.format(success_num) + "".join(success_msg)

    # Java: AjaxResult forgotPassword(SysUser sysUser)
    @transactional
    def forgot_password(self, sys_user: SysUser) -> AjaxResult:
        """忘记密码 —— 重置为**请求里带来的新密码**（不是默认密码）。

        与 :meth:`update_user_pwd` 的差别只有三处，全部保留：

        * 验证码比较用 ``equalsIgnoreCase``（大小写不敏感）；
        * 账号查询结果用 ``CollectionUtils.isEmpty``（空表即报错）；
        * 成功时把**明文**新密码回显在 ``data`` 里，提示语是 ``"密码已重置为: "``。
        """
        try:
            vcode = _to_string(self.redis_cache.get_cache_object(sys_user.phonenumber))
        except Exception:  # noqa: BLE001
            logger.exception("读取短信验证码失败")
            return AjaxResult.error_message(VCODE_INVALID_MESSAGE)

        # Java: StringUtils.isEmpty(remark) || !remark.equalsIgnoreCase(vcode)
        if is_empty(sys_user.remark) or sys_user.remark is None or sys_user.remark.lower() != vcode.lower():
            return AjaxResult.error_message(VCODE_INVALID_MESSAGE)

        # 根据账号查询用户
        sys_users = self._mapper.select_user_list(sys_user)
        if not sys_users or len(sys_users) > 1:
            return AjaxResult.error_message(ACCOUNT_INVALID_MESSAGE)

        user = SysUser()
        user.phonenumber = sys_user.phonenumber
        user.user_name = sys_user.user_name
        user.password = SecurityUtils.encrypt_password(sys_user.password)
        rows = self._mapper.update_user_pwd(user.phonenumber, user.password, user.user_name)
        # 说明更新成功
        if rows == 1:
            return AjaxResult.success_message_data("密码已重置为: ", sys_user.password)

        return AjaxResult.error_message(FORGOT_PWD_FAILED_MESSAGE)


def _join_names(names: Iterable[Optional[str]]) -> str:
    """Java: ``StringBuffer.append(name).append(",")`` + ``substring(0, len-1)``.

    ``StringBuffer.append(null)`` 会拼出字面量 ``"null"``，而不是抛异常；
    角色名 / 岗位名在库里都是 ``NOT NULL``，这里照样保留该语义。
    """
    parts = ["null" if name is None else str(name) for name in names]
    if not parts:
        return ""
    return ",".join(parts)


def _to_string(value: Any) -> str:
    """Java: ``value.toString()`` —— ``null`` 会 NPE，这里抛 ``TypeError``。"""
    if value is None:
        raise TypeError("'NoneType' object has no attribute 'toString'")
    return str(value)


def _text(value: Optional[str]) -> str:
    """Java 字符串拼接：``"..." + null`` 得到字面量 ``"null"``，不抛异常。"""
    return "null" if value is None else value


_SERVICE: Optional[SysUserService] = None


def get_user_service() -> SysUserService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysUserService()
    return _SERVICE


def reset_user_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysUserService",
    "get_user_service",
    "reset_user_service",
    "CHECK_USER_ALLOWED_MESSAGE",
    "VCODE_INVALID_MESSAGE",
    "ACCOUNT_INVALID_MESSAGE",
    "RESET_PWD_FAILED_MESSAGE",
    "FORGOT_PWD_FAILED_MESSAGE",
    "IMPORT_USER_EMPTY_MESSAGE",
    "IMPORT_INIT_PASSWORD_KEY",
    "IMPORT_FAILURE_PREFIX",
    "IMPORT_SUCCESS_PREFIX",
]
