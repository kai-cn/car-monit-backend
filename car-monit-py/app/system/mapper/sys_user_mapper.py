"""用户表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml

迁移范围：登录切片（``selectUserByUserName``）+ ``sys_user`` 管理页需要的全部语句。
尚未迁移（属于其它模块，见 ``COMPATIBILITY.md``）：``getSendUserInfosByEpsId`` /
``selectByRoleKey``（返回 ``UserRoleModel``，供招投标与消息模块使用）。

结果映射的两种形态
------------------
``selectUserVo`` 系列（``selectUserByUserName`` / ``selectUserById`` /
``selectUserByCertEntityID``）left join 了 ``sys_user_role`` / ``sys_role``，
一个用户三个角色就是**三行**，靠 ``resultMap`` 的 ``<id>`` + ``<collection>`` 合并。
Python 没有这个能力，所以 :func:`_map_user` 手工合并（见其文档）。

``selectUserList`` 不一样：它**根本 select 角色列**，所以 ``roles`` 恒为 ``[]``；
它只带 ``d.dept_name`` / ``d.leader`` 两个部门列，靠 ``<association>`` 拼出
``dept``。因此它走独立的 :func:`_map_user_list_row`，不要和 ``_map_user`` 混用。

``selectUserList`` 的列不重复，但有两列容易看漏：

* ``ifnull(d.tenant_id, -1) tenant_id`` —— 用户没有部门时租户是 ``-1``（前端用它判空）；
* ``d2.dept_name tenant_name`` —— ``d2`` 是通过 ``d.tenant_id = d2.dept_id`` 反查
  的"上级单位名称"，与 ``d.dept_name`` 是两个不同概念。

分页
----
``selectUserList`` 在 Java 里由 PageHelper 隐式改写（先 count 再 ``LIMIT``，
见 :mod:`app.common.core.page.page_helper`）。这里在方法内部调用 ``take_page()``，
Service / Controller 的调用方式与 Java 完全一致。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysUserMapper.xml -> ``<sql id="selectUserVo">``.
#: ``ifnull(u.buss_id, u.user_name)`` and ``ifnull(d.tenant_id, -1)`` are business rules, not
#: cosmetics: the frontend keys off ``bussId`` and treats ``tenantId == -1`` as "no tenant".
_SELECT_USER_VO = """
        select u.user_id,
               u.user_no,
               u.dept_id,
               u.user_name,
               u.nick_name,
               u.email,
               u.avatar,
               u.phonenumber,
               u.password,
               u.sex,
               u.status,
               u.del_flag,
               u.login_ip,
               u.login_date,
               u.create_by,
               u.create_time,
               u.remark,
               u.user_type,
               u.cert_entity_id,
               u.cert_id,
               ifnull(u.buss_id, u.user_name) buss_id,
               u.buss_name,
               u.eps_name,
               ifnull(d.tenant_id, -1)        tenant_id,
               d.sub_code,
               d.dept_id,
               d.parent_id,
               d.dept_name,
               d.order_num,
               d.leader,
               d.status as                    dept_status,
               r.role_id,
               r.role_name,
               r.role_key,
               r.role_sort,
               r.data_scope,
               r.status as                    role_status
        from sys_user u
                 left join sys_dept d on u.dept_id = d.dept_id
                 left join sys_user_role ur on u.user_id = ur.user_id
                 left join sys_role r on r.role_id = ur.role_id
"""

#: Public alias kept because later mappers (``selectUserList`` and friends) reuse the same
#: ``<sql id="selectUserVo"/>`` fragment.
SELECT_USER_VO = _SELECT_USER_VO

#: Verbatim from SysUserMapper.xml -> ``<select id="selectUserByUserName">``.
_SELECT_USER_BY_USER_NAME = SELECT_USER_VO + """
        where u.user_name = :user_name
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="selectUserByCertEntityID">``.
_SELECT_USER_BY_CERT_ENTITY_ID = SELECT_USER_VO + """
        where u.cert_entity_id = :cert_entity_id
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="selectUserById">``.
_SELECT_USER_BY_ID = SELECT_USER_VO + """
        where u.user_id = :user_id
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="selectUserList">``.
#: 动态 ``<if>`` 在 :meth:`SysUserMapper.select_user_list` 里按原顺序拼接。
_SELECT_USER_LIST = """
        select u.user_id,u.user_no, u.dept_id, u.nick_name, u.user_name, u.email, u.avatar, u.phonenumber, u.password,
        u.sex, u.status, u.del_flag, u.login_ip, u.login_date,u.create_by, u.create_time, u.remark,
        u.user_type,u.cert_entity_id, u.cert_id, u.buss_id, u.buss_name, u.eps_name,ifnull(d.tenant_id,-1)
        tenant_id,d2.dept_name tenant_name,
        d.dept_name, d.leader,u.image_id
        from sys_user u
        left join sys_dept d on u.dept_id = d.dept_id
        left join sys_dept d2 on d.tenant_id = d2.dept_id
        where u.del_flag = '0'
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="checkUserNameUnique">``.
_CHECK_USER_NAME_UNIQUE = """
        select count(1)
        from sys_user
        where user_name = :user_name
          and del_flag = '0' limit 1
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="checkPhoneUnique">``.
_CHECK_PHONE_UNIQUE = """
        select user_id, phonenumber
        from sys_user
        where phonenumber = :phonenumber
          and del_flag = '0' limit 1
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="checkEmailUnique">``.
_CHECK_EMAIL_UNIQUE = """
        select user_id, email
        from sys_user
        where email = :email
          and del_flag = '0' limit 1
"""

#: Verbatim from SysUserMapper.xml -> ``<insert id="insertUser">`` (columns / values 由
#: :meth:`SysUserMapper.insert_user` 按 ``<if>`` 规则动态拼)。
_INSERT_USER_HEAD = "insert into sys_user"

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUser">``.
_UPDATE_USER_HEAD = "update sys_user"

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUserInfoByBussId">``.
_UPDATE_USER_INFO_BY_BUSS_ID_HEAD = "update sys_user"

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUserInfoByBussIdAndUserType">``.
_UPDATE_USER_INFO_BY_BUSS_ID_AND_USER_TYPE_HEAD = "update sys_user"

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUserStatus">``.
#: 注意：**没有调用者**。``SysUserServiceImpl.updateUserStatus`` 走的是 ``updateUser``；
#: 接口里也没声明 ``updateUserStatus``，所以这条语句在 Java 里是死代码。保留以示等价。
_UPDATE_USER_STATUS = """
        update sys_user
        set status = :status
        where user_id = :user_id
"""

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUserPwd">``.
_UPDATE_USER_PWD = """
        update sys_user
        set password    = :password,
            update_time = now()
        where phonenumber = :phonenumber
          and user_name = :user_name
"""

#: Verbatim from SysUserMapper.xml -> ``<update id="updateUserAvatar">``.
_UPDATE_USER_AVATAR = """
        update sys_user
        set avatar = :avatar
        where user_name = :user_name
"""

#: Verbatim from SysUserMapper.xml -> ``<update id="resetUserPwd">``.
_RESET_USER_PWD = """
        update sys_user
        set password    = :password,
            update_time = now()
        where user_name = :user_name
"""

#: Verbatim from SysUserMapper.xml -> ``<delete id="deleteUserById">``.
_DELETE_USER_BY_ID = """
        update sys_user
        set del_flag = '1'
        where user_id = :user_id
"""

#: Verbatim from SysUserMapper.xml -> ``<delete id="deleteUserByBussId">``.
_DELETE_USER_BY_BUSS_ID = """
        update sys_user
        set del_flag = '1'
        where buss_id = :buss_id
"""

#: Verbatim from SysUserMapper.xml -> ``<select id="selectPwdJudge">``.
_SELECT_PWD_JUDGE = """
        select case
                   when TIMESTAMPDIFF(DAY,t.update_time, DATE_FORMAT(NOW(), '%Y-%m-%d')) >= 90 then 3
                   when t.update_time is NULL then 1
                   else 0 end pjFlag
        from sys_user t
        where t.user_id = :user_id
"""

#: ``selectUserList`` 的投影顺序（逐字对应 XML 里的 select 列）。
#: 无法从执行结果反推，因为 :func:`select_page` 只返回行元组。
_USER_LIST_COLUMNS: Tuple[str, ...] = (
    "user_id",
    "user_no",
    "dept_id",
    "nick_name",
    "user_name",
    "email",
    "avatar",
    "phonenumber",
    "password",
    "sex",
    "status",
    "del_flag",
    "login_ip",
    "login_date",
    "create_by",
    "create_time",
    "remark",
    "user_type",
    "cert_entity_id",
    "cert_id",
    "buss_id",
    "buss_name",
    "eps_name",
    "tenant_id",
    "tenant_name",
    "dept_name",
    "leader",
    "image_id",
)

#: ``insertUser`` 的 <if> 列清单 ``(实体属性, 列名, 是否要求非空串)``。
#: 顺序即 XML 顺序；``<trim suffixOverrides=",">`` 的逗号收尾由拼接时处理。
_INSERT_USER_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("user_no", "user_no", False),
    ("dept_id", "dept_id", False),
    ("user_name", "user_name", True),
    ("nick_name", "nick_name", True),
    ("user_type", "user_type", False),
    ("email", "email", False),
    ("phonenumber", "phonenumber", False),
    ("sex", "sex", False),
    ("avatar", "avatar", False),
    ("password", "password", False),
    ("status", "status", False),
    ("remark", "remark", False),
    ("cert_entity_id", "cert_entity_id", False),
    ("cert_id", "cert_id", False),
    ("buss_id", "buss_id", False),
    ("buss_name", "buss_name", False),
    ("eps_name", "eps_name", False),
    ("login_ip", "login_ip", False),
    ("login_date", "login_date", False),
    ("del_flag", "del_flag", False),
    ("create_by", "create_by", False),
    ("create_time", "create_time", False),
    ("update_by", "update_by", False),
    ("update_time", "update_time", False),
    ("tenant_id", "tenant_id", False),
    ("image_id", "image_id", False),
)

#: ``updateUser`` 的 <if> 列清单。与 insert 的唯一差别是 ``password`` 也要求非空串
#: （``password != null and password != ''``），避免把密码改成空串。
_UPDATE_USER_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("user_no", "user_no", False),
    ("dept_id", "dept_id", False),
    ("user_name", "user_name", True),
    ("nick_name", "nick_name", True),
    ("password", "password", True),
    ("user_type", "user_type", False),
    ("email", "email", False),
    ("phonenumber", "phonenumber", False),
    ("sex", "sex", False),
    ("avatar", "avatar", False),
    ("status", "status", False),
    ("remark", "remark", False),
    ("cert_entity_id", "cert_entity_id", False),
    ("cert_id", "cert_id", False),
    ("buss_id", "buss_id", False),
    ("buss_name", "buss_name", False),
    ("eps_name", "eps_name", False),
    ("login_ip", "login_ip", False),
    ("login_date", "login_date", False),
    ("del_flag", "del_flag", False),
    ("create_by", "create_by", False),
    ("create_time", "create_time", False),
    ("update_by", "update_by", False),
    ("update_time", "update_time", False),
    ("tenant_id", "tenant_id", False),
    ("image_id", "image_id", False),
)

#: ``updateUserInfoByBussId`` / ``updateUserInfoByBussIdAndUserType`` 共用的列清单。
#: 比 ``updateUser`` 少三列：``password``、``buss_id``（它就是 where 条件）、
#: ``image_id``（外部同步不碰用户签名图）。**这三列不能“补齐”**。
_UPDATE_BY_BUSS_ID_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("user_no", "user_no", False),
    ("dept_id", "dept_id", False),
    ("user_name", "user_name", True),
    ("nick_name", "nick_name", True),
    ("user_type", "user_type", False),
    ("email", "email", False),
    ("phonenumber", "phonenumber", False),
    ("sex", "sex", False),
    ("avatar", "avatar", False),
    ("status", "status", False),
    ("remark", "remark", False),
    ("cert_entity_id", "cert_entity_id", False),
    ("cert_id", "cert_id", False),
    ("buss_name", "buss_name", False),
    ("eps_name", "eps_name", False),
    ("login_ip", "login_ip", False),
    ("login_date", "login_date", False),
    ("del_flag", "del_flag", False),
    ("create_by", "create_by", False),
    ("create_time", "create_time", False),
    ("update_by", "update_by", False),
    ("update_time", "update_time", False),
    ("tenant_id", "tenant_id", False),
)

#: 从 where 子句里抓 ``:name`` 绑定名，用于补齐 where 参数。
_BIND_PATTERN = re.compile(r":(\w+)")


class SysUserMapper:
    """Java: ``interface SysUserMapper`` (the ``sys_user`` slice)."""

    # Java: SysUser selectUserByUserName(String userName)
    def select_user_by_user_name(self, user_name: str) -> Optional[SysUser]:
        """Return the user plus its department and roles, or ``None``.

        Java relies on ``resultMap="SysUserResult"`` doing the row collapsing; here it is
        done by :func:`_map_user`. ``selectOne`` semantics: MyBatis would throw
        ``TooManyResultsException`` if the collapse produced more than one row, which can
        only happen if two rows carry different ``user_id`` values -- i.e. if
        ``user_name`` were not unique.
        """
        with session_scope() as session:
            result = session.execute(text(_SELECT_USER_BY_USER_NAME), {"user_name": user_name})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_user(rows, keys)

    # Java: SysUser selectUserByCertEntityID(String strCertEntityID)
    def select_user_by_cert_entity_id(self, cert_entity_id: str) -> Optional[SysUser]:
        """通过 CA 实体标识查用户（绑定 UKey 时用）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_USER_BY_CERT_ENTITY_ID), {"cert_entity_id": cert_entity_id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_user(rows, keys)

    # Java: SysUser selectUserById(Long userId)
    def select_user_by_id(self, user_id: int) -> Optional[SysUser]:
        """带部门与角色的单用户查询（``GET /system/user/{userId}`` 的 ``data``）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_USER_BY_ID), {"user_id": user_id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_user(rows, keys)

    # Java: List<SysUser> selectUserList(SysUser user)
    def select_user_list(self, user: Optional[SysUser] = None) -> List[SysUser]:
        """条件分页查询。分页参数从 :func:`take_page` 隐式取得（PageHelper）。

        ``params.dataScope`` 在本项目的 XML 里是**被注释掉的**
        （``<!-- 数据范围过滤${params.dataScope} -->``），所以即使切面往里写了片段，
        也不会进入 SQL。这一点不要“补全”，否则与 Java 不一样了。
        """
        user = user or SysUser()
        data_sql, params = _build_user_list_sql(user)
        # PageHelper 的 count 策略：把原语句包成子查询再 count，对 join 放大行数是安全的。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        # 投影顺序写死在 _USER_LIST_COLUMNS 里，与 _SELECT_USER_LIST 一一对应。
        mapped = [_map_user_list_row(row, _USER_LIST_COLUMNS) for row in page_list]
        return PageList(mapped, total=page_list.total, page_num=page_list.page_num, page_size=page_list.page_size)

    # Java: int checkUserNameUnique(String userName)
    def check_user_name_unique(self, user_name: str) -> int:
        """返回命中行数（0 / 1），Service 再翻译成 ``UNIQUE_OLD`` / ``NOT_UNIQUE_OLD``。"""
        with session_scope() as session:
            return int(session.execute(text(_CHECK_USER_NAME_UNIQUE), {"user_name": user_name}).scalar() or 0)

    # Java: SysUser checkPhoneUnique(String phonenumber)
    def check_phone_unique(self, phonenumber: str) -> Optional[SysUser]:
        """只带 ``user_id`` / ``phonenumber`` 两个字段的瘦对象（``resultMap`` 的子集）。"""
        with session_scope() as session:
            result = session.execute(text(_CHECK_PHONE_UNIQUE), {"phonenumber": phonenumber})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_unique_row(rows[0], keys)

    # Java: SysUser checkEmailUnique(String email)
    def check_email_unique(self, email: str) -> Optional[SysUser]:
        with session_scope() as session:
            result = session.execute(text(_CHECK_EMAIL_UNIQUE), {"email": email})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_unique_row(rows[0], keys)

    # Java: int insertUser(SysUser user)  -- useGeneratedKeys="true" keyProperty="userId"
    def insert_user(self, user: SysUser) -> int:
        """动态列插入；回写 ``user.user_id``，因为后续 ``insertUserRole`` 依赖它。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}
        for attribute, column, require_text in _INSERT_USER_COLUMNS:
            value = getattr(user, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            columns.append(column)
            names.append(f":{attribute}")
            params[attribute] = value

        sql = f"{_INSERT_USER_HEAD} ({', '.join(columns)}) values ({', '.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            # MyBatis 的 keyProperty 回写等价物。
            user.user_id = result.lastrowid
            return result.rowcount or 0

    # Java: int updateUser(SysUser user)
    def update_user(self, user: SysUser) -> int:
        sql, params = _build_update_sql(user, _UPDATE_USER_COLUMNS, "where user_id = :user_id")
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int updateUserInfoByBussId(SysUser user)
    def update_user_info_by_buss_id(self, user: SysUser) -> int:
        sql, params = _build_update_sql(
            user, _UPDATE_BY_BUSS_ID_COLUMNS, "where buss_id = :buss_id"
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: void updateUserInfoByBussIdAndUserType(SysUser user)
    def update_user_info_by_buss_id_and_user_type(self, user: SysUser) -> int:
        sql, params = _build_update_sql(
            user,
            _UPDATE_BY_BUSS_ID_COLUMNS,
            "where buss_id = :buss_id AND user_type = :user_type",
            extra_params={"user_type": user.user_type},
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: 无（XML 里的死语句，保留以对照 ``updateUserStatus``）
    def update_user_status(self, user: SysUser) -> int:
        with session_scope() as session:
            return (
                session.execute(
                    text(_UPDATE_USER_STATUS), {"status": user.status, "user_id": user.user_id}
                ).rowcount
                or 0
            )

    # Java: int updateUserPwd(String phonenumber, String password, String userName)
    def update_user_pwd(self, phonenumber: str, password: str, user_name: str) -> int:
        with session_scope() as session:
            return (
                session.execute(
                    text(_UPDATE_USER_PWD),
                    {"phonenumber": phonenumber, "password": password, "user_name": user_name},
                ).rowcount
                or 0
            )

    # Java: int updateUserAvatar(String userName, String avatar)
    def update_user_avatar(self, user_name: str, avatar: str) -> int:
        with session_scope() as session:
            return (
                session.execute(
                    text(_UPDATE_USER_AVATAR), {"user_name": user_name, "avatar": avatar}
                ).rowcount
                or 0
            )

    # Java: int resetUserPwd(String userName, String password)
    def reset_user_pwd(self, user_name: str, password: str) -> int:
        with session_scope() as session:
            return (
                session.execute(
                    text(_RESET_USER_PWD), {"user_name": user_name, "password": password}
                ).rowcount
                or 0
            )

    # Java: int deleteUserById(Long userId)  -- 软删除: del_flag = '1'
    def delete_user_by_id(self, user_id: int) -> int:
        with session_scope() as session:
            return session.execute(text(_DELETE_USER_BY_ID), {"user_id": user_id}).rowcount or 0

    # Java: int deleteUserByIds(Long[] userIds)
    def delete_user_by_ids(self, user_ids: Sequence[int]) -> int:
        clause, params = _in_clause("user_id", user_ids, "p")
        with session_scope() as session:
            return (
                session.execute(text(f"update sys_user set del_flag = '1' where {clause}"), params).rowcount
                or 0
            )

    # Java: int deleteUserByBussId(String bussId)
    def delete_user_by_buss_id(self, buss_id: str) -> int:
        with session_scope() as session:
            return session.execute(text(_DELETE_USER_BY_BUSS_ID), {"buss_id": buss_id}).rowcount or 0

    # Java: int deleteUserByBussIds(String[] bussIds)
    def delete_user_by_buss_ids(self, buss_ids: Sequence[str]) -> int:
        clause, params = _in_clause("buss_id", buss_ids, "p")
        with session_scope() as session:
            return (
                session.execute(text(f"update sys_user set del_flag = '1' where {clause}"), params).rowcount
                or 0
            )

    # Java: int existsByBussId(SysUser user)
    def exists_by_buss_id(self, user: SysUser) -> int:
        """注意语义：统计的是“``buss_id`` **不等于**该值且 ``user_name`` 相等”的用户数。

        XML 里写的是 ``t.buss_id != #{bussId}``，不是 ``=``。Java 原样如此，
        调用方（外部同步）把 ``> 0`` 解释为“该登录名已被别的业务对象占用”。
        """
        where: List[str] = ["t.del_flag='0'"]
        params: Dict[str, Any] = {}
        if _text(user.buss_id):
            where.append("and t.buss_id != :buss_id")
            params["buss_id"] = user.buss_id
        if _text(user.user_name):
            where.append("and t.user_name = :user_name")
            params["user_name"] = user.user_name
        sql = "select count(1) from sys_user t where " + " ".join(where)
        with session_scope() as session:
            return int(session.execute(text(sql), params).scalar() or 0)

    # Java: SysUser selectPwdJudge(Long userId)
    def select_pwd_judge(self, user_id: int) -> Optional[SysUser]:
        """返回只带 ``pjFlag`` 的瘦对象：0=正常，1=从未改过密码，3=超过 90 天。"""
        with session_scope() as session:
            value = session.execute(text(_SELECT_PWD_JUDGE), {"user_id": user_id}).scalar()
        if value is None:
            return None
        return SysUser(pj_flag=int(value))


def _first_by_label(row: Any, keys: Sequence[str], label: str) -> Any:
    """Read ``label`` the way JDBC does: the **first** column carrying that label."""
    return row[keys.index(label)]


def _map_user(rows: Sequence[Any], keys: Sequence[str]) -> SysUser:
    """Collapse the joined rows into one ``SysUser`` (Java: ``resultMap="SysUserResult"``)."""
    first = rows[0]
    values: Dict[str, Any] = {label: _first_by_label(first, keys, label) for label in keys}

    dept: Optional[SysDept] = None
    if values["dept_id"] is not None:
        # Java: <association property="dept" resultMap="deptResult"/> -- six columns only.
        dept = SysDept(
            dept_id=values["dept_id"],
            parent_id=values["parent_id"],
            dept_name=values["dept_name"],
            order_num=values["order_num"],
            leader=values["leader"],
            status=values["dept_status"],
        )

    roles: List[SysRole] = []
    seen_role_ids = set()
    for row in rows:
        role_id = row[keys.index("role_id")]
        if role_id is None or role_id in seen_role_ids:
            # Java: <collection> keyed on the RoleResult <id> column -> duplicates collapse.
            continue
        seen_role_ids.add(role_id)
        roles.append(
            SysRole(
                role_id=role_id,
                role_name=row[keys.index("role_name")],
                role_key=row[keys.index("role_key")],
                role_sort=row[keys.index("role_sort")],
                data_scope=row[keys.index("data_scope")],
                status=row[keys.index("role_status")],
            )
        )

    return SysUser(
        user_id=values["user_id"],
        user_no=values["user_no"],
        dept_id=values["dept_id"],
        user_name=values["user_name"],
        nick_name=values["nick_name"],
        user_type=values["user_type"],
        email=values["email"],
        phonenumber=values["phonenumber"],
        sex=values["sex"],
        avatar=values["avatar"],
        password=values["password"],
        status=values["status"],
        del_flag=values["del_flag"],
        login_ip=values["login_ip"],
        login_date=values["login_date"],
        create_by=values["create_by"],
        create_time=values["create_time"],
        remark=values["remark"],
        cert_entity_id=values["cert_entity_id"],
        cert_id=values["cert_id"],
        buss_id=values["buss_id"],
        buss_name=values["buss_name"],
        eps_name=values["eps_name"],
        tenant_id=values["tenant_id"],
        sub_code=values["sub_code"],
        dept=dept,
        roles=roles,
    )


def _text(value: Optional[str]) -> bool:
    """Java: ``StringUtils.isNotEmpty(...)`` -- 非 ``None`` 且非空串。"""
    return value is not None and value != ""


def _build_user_list_sql(user: SysUser) -> Tuple[str, Dict[str, Any]]:
    """拼出 ``selectUserList`` 的动态部分（Java: XML 里的 ``<if>`` 序列）。

    顺序、连接词大小写、``like concat('%', ?, '%')`` 的写法全部逐字保留：
    这些 SQL 会出现在慢查询日志里，改动会让运维的既有检索习惯失效。

    末尾**没有** ``${params.dataScope}``：XML 里这一行是被注释掉的
    （``<!-- 数据范围过滤${params.dataScope} -->``），见模块文档。
    """
    where: List[str] = []
    params: Dict[str, Any] = {}
    user_params: Dict[str, Any] = user.params or {}

    def eq(attribute: str, column: str) -> None:
        """``<if test="x != null and x != ''">`` -- 数值字段实际等价于只判 ``None``。"""
        value = getattr(user, attribute, None)
        if value is None or value == "":
            return
        where.append(f"AND {column} = :{attribute}")
        params[attribute] = value

    def contains(attribute: str, column: str) -> None:
        value = getattr(user, attribute, None)
        if value is None or value == "":
            return
        where.append(f"AND {column} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    eq("user_id", "u.user_id")
    eq("user_no", "u.user_no")
    contains("user_name", "u.user_name")
    eq("status", "u.status")
    contains("phonenumber", "u.phonenumber")

    begin_time = user_params.get("beginTime")
    if _text(begin_time):
        where.append(
            "AND date_format(u.create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"
        )
        params["begin_time"] = begin_time

    end_time = user_params.get("endTime")
    if _text(end_time):
        where.append(
            "AND date_format(u.create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"
        )
        params["end_time"] = end_time

    # Java: <if test="deptId != null and deptId != 0"> -- 0 是“不限”的哨兵值。
    if user.dept_id is not None and user.dept_id != 0:
        where.append(
            "AND (u.dept_id = :dept_id OR u.dept_id IN ( SELECT t.dept_id FROM sys_dept t "
            "WHERE find_in_set(:dept_id, ancestors) ))"
        )
        params["dept_id"] = user.dept_id

    eq("user_type", "u.user_type")
    eq("cert_entity_id", "u.cert_entity_id")
    eq("cert_id", "u.cert_id")
    eq("buss_id", "u.buss_id")
    contains("buss_name", "u.buss_name")
    contains("eps_name", "u.eps_name")

    # Java: <if test="tenantId != null "> -- 这一条只判 null，空串也照拼。
    if user.tenant_id is not None:
        where.append("AND d.tenant_id = :tenant_id")
        params["tenant_id"] = user.tenant_id

    if _text(user.role_code):
        where.append(
            "AND EXISTS (select 1 from sys_user_role t1,sys_role t2 "
            "where t2.del_flag = '0' and t2.role_id = t1.role_id and t1.user_id = u.user_id "
            "and t2.role_key = :role_code )"
        )
        params["role_code"] = user.role_code

    # 上级单位：注意 XML 里 ``tb.del_flag = '0'`` 重复写了两遍（原文如此）。
    if user.flag == "sjzbDept" or user.flag == "sjzbDeptCg":
        where.append(
            "AND exists ( select 1 from sys_dept tb,sys_dept tb1 "
            "where tb.del_flag = '0' and tb.del_flag = '0' and tb1.dept_id = tb.parent_id "
            "and tb.dept_id = :data_id and tb1.dept_id = d.tenant_id )"
        )
        params["data_id"] = user.data_id

    if user.flag == "sjzbDeptCg" or user.flag == "myDeptCg":
        where.append(
            "AND EXISTS ( SELECT 1 FROM sys_user_role sr, sys_role r "
            "WHERE r.role_id = sr.role_id AND r.role_key = 'cgjl_manager' "
            "AND sr.user_id = u.user_id )"
        )

    if _text(user.query_nick_name):
        where.append("AND u.nick_name LIKE CONCAT('%', :query_nick_name, '%')")
        params["query_nick_name"] = user.query_nick_name

    if user.exclude_id is not None:
        where.append("AND u.user_id != :exclude_id")
        params["exclude_id"] = user.exclude_id

    sql = _SELECT_USER_LIST
    if where:
        sql = sql + "        " + "\n        ".join(where) + "\n"
    return sql, params


def _map_user_list_row(row: Any, keys: Sequence[str]) -> SysUser:
    """把 ``selectUserList`` 的一行映射成 ``SysUser``。

    与 :func:`_map_user` 的差别：

    * 没有角色列 -> ``roles`` 恒为 ``[]``（Java 里 ``<collection>`` 拿不到列，也是空表）；
    * 部门只有 ``dept_id`` / ``dept_name`` / ``leader`` 三列，``parent_id``/``order_num``/
      ``status`` 都是 ``null``；
    * 多出 ``d2.dept_name tenant_name`` 与 ``u.image_id``。
    """
    values: Dict[str, Any] = {label: row[index] for index, label in enumerate(keys)}

    dept: Optional[SysDept] = None
    if values.get("dept_id") is not None:
        # Java: <association property="dept" resultMap="deptResult"/> -- 三个非空列。
        dept = SysDept(
            dept_id=values["dept_id"],
            dept_name=values.get("dept_name"),
            leader=values.get("leader"),
        )

    return SysUser(
        user_id=values.get("user_id"),
        user_no=values.get("user_no"),
        dept_id=values.get("dept_id"),
        nick_name=values.get("nick_name"),
        user_name=values.get("user_name"),
        email=values.get("email"),
        avatar=values.get("avatar"),
        phonenumber=values.get("phonenumber"),
        password=values.get("password"),
        sex=values.get("sex"),
        status=values.get("status"),
        del_flag=values.get("del_flag"),
        login_ip=values.get("login_ip"),
        login_date=values.get("login_date"),
        create_by=values.get("create_by"),
        create_time=values.get("create_time"),
        remark=values.get("remark"),
        user_type=values.get("user_type"),
        cert_entity_id=values.get("cert_entity_id"),
        cert_id=values.get("cert_id"),
        buss_id=values.get("buss_id"),
        buss_name=values.get("buss_name"),
        eps_name=values.get("eps_name"),
        tenant_id=values.get("tenant_id"),
        tenant_name=values.get("tenant_name"),
        # 注意：**不**填扁平的 ``deptName``。``SysUserResult`` 里有 ``<association>``，
        # 按 MyBatis 的 ``autoMappingBehavior=PARTIAL`` 规则，存在嵌套映射时自动映射
        # 会被**整体关闭**，所以 ``dept_name`` 只进 ``dept.deptName``，扁平的
        # ``SysUser.deptName`` 实测就是 ``null``（见 /system/user/list 的 Java 原始响应）。
        image_id=values.get("image_id"),
        dept=dept,
        roles=[],
    )


def _map_unique_row(row: Any, keys: Sequence[str]) -> SysUser:
    """``checkPhoneUnique`` / ``checkEmailUnique`` 的瘦对象（两列）。"""
    values: Dict[str, Any] = {label: row[index] for index, label in enumerate(keys)}
    return SysUser(
        user_id=values.get("user_id"),
        phonenumber=values.get("phonenumber"),
        email=values.get("email"),
    )


def _build_update_sql(
    user: SysUser,
    columns: Sequence[Tuple[str, str, bool]],
    where: str,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_user set ... where ...``（Java: ``<trim prefix="SET">``）。

    一个 ``<if>`` 都不命中时，Java 会拼出 ``update sys_user  where ...`` 这种非法 SQL
    并让 MySQL 报语法错（500）。这里保持同样的产出，不做额外校验。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in columns:
        value = getattr(user, attribute, None)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    # where 里的绑定名（user_id / buss_id / user_type）不来自 set 列表，单独补。
    for name in _BIND_PATTERN.findall(where):
        if name not in params:
            params[name] = getattr(user, name, None)
    if extra_params:
        params.update(extra_params)

    sql = f"{_UPDATE_USER_HEAD} set " + ", ".join(sets) + " " + where
    return sql, params


__all__ = ["SysUserMapper", "SELECT_USER_VO"]