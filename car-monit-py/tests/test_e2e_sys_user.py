"""端到端验证：``POST /login`` -> JWT -> ``/system/user`` 增删改查 -> ``POST /logout``.

# Migrated from: (no Java test) -- the whole chain of
#   SysLoginController + SysLoginService + DaoAuthenticationProvider
#   + JwtAuthenticationTokenFilter + SecurityMiddleware
#   + SysUserController + SysUserServiceImpl + SysUserMapper

为什么要有这一层
----------------
前三层（mapper / service / controller）都是**注入假协作者**的，各自证明"自己这段对"。
但漏掉了一种失败：某个对象图在装配时接到了**另一个**实例 —— 例如控制器缓存了旧的
Service、过滤器缓存了旧的 TokenService、或者 ``LoginUser`` 缓存进 Redis 时丢了
``permissions``。这类问题只有真的走一遍 HTTP 才会暴露。

因此本文件**不替换任何业务对象**：真实的 FastAPI 应用、真实的 SecurityMiddleware、
真实的 JWT 过滤器、真实的 ProviderManager、真实的 Controller/Service/Mapper。
只替换两样外围设施：

==============  ==========================================================
MySQL           各 mapper 模块里的 ``session_scope`` 换成按 SQL 文本分派的假库
Redis           ``TokenService`` / ``SysLoginService`` 里的 ``get_redis_cache()``
==============  ==========================================================

假库只认 ``sys_user`` 切片涉及的语句（见 :meth:`_FakeDb.execute`），命中不了就抛
``AssertionError`` —— 这样"某个用例意外多查了一张表"会直接失败，而不是悄悄返回空。

覆盖的链路
----------
========================================  ====================================
Java 串联点                                本文件中的用例
========================================  ====================================
``SysLoginController#login``              ``TestLogin``
``DaoAuthenticationProvider`` + bcrypt    ``TestLogin``（错密码 -> 500 信封）
``AsyncFactory.recordLogininfor``         ``test_the_audit_row_is_written``（异步）
``JwtAuthenticationTokenFilter``          ``TestTokenAuthority``
``FilterSecurityInterceptor``             ``test_a_request_without_a_token_...``
``SysUserController#list`` + PageHelper    ``TestList``
``SysUserController#getInfo``             ``TestDetail``
``SysUserController#add`` / ``edit``      ``TestWrite``
``SysUserController#remove``              ``TestWrite``
``SysUserController#resetPwd``            ``TestWrite``
``LogoutSuccessHandlerImpl``              ``TestLogout``
========================================  ====================================

没有被覆盖的部分（见 ``COMPATIBILITY.md`` §25）
----------------------------------------------
``/system/user/export``、``/system/user/importData``、``@Log`` 写的 ``sys_oper_log``、
``GET /getRouters``（菜单树属于菜单模块）、``SysUserController#currentUser`` 里的
"总公司人员/采购经理"判定（依赖 ``sys_role`` 与 ``PROCUREMENT_MANAGER_ROLE_KEY``，已在
``test_sys_user_service.py`` 里逐分支覆盖）。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api.system.sys_login_controller import reset_login_controller
from app.api.system.sys_user_controller import ADD_USER_NAME_EXISTS, reset_user_controller
from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.common.utils.security_utils import encrypt_password, matches_password
from app.framework.manager.async_manager import reset_async_manager
from app.framework.security.authentication.provider_manager import reset_authentication_manager
from app.framework.security.context.security_context import SecurityContextHolder
from app.framework.security.filter.jwt_authentication_token_filter import (
    reset_jwt_authentication_token_filter,
)
from app.framework.security.handle.logout_success_handler_impl import (
    reset_logout_success_handler,
)
from app.framework.web.service import sys_login_service as login_service_module
from app.framework.web.service import token_service as token_service_module
from app.framework.web.service.permission_service import reset_permission_service
from app.framework.web.service.sys_login_service import reset_login_service
from app.framework.web.service.sys_permission_service import (
    reset_permission_service as reset_menu_permission_service,
)
from app.framework.web.service.token_service import reset_token_service
from app.framework.web.service.user_details_service_impl import reset_user_details_service
from app.system.mapper import (
    sys_dept_mapper,
    sys_logininfor_mapper,
    sys_menu_mapper,
    sys_post_mapper,
    sys_role_mapper,
    sys_user_mapper,
    sys_user_post_mapper,
    sys_user_role_mapper,
)
from app.system.mapper.sys_dept_mapper import _DEPT_COLUMNS
from app.system.mapper.sys_user_mapper import _USER_LIST_COLUMNS
from app.system.service.sys_dept_service import reset_dept_service
from app.system.service.sys_menu_service import reset_menu_service
from app.system.service.sys_post_service import reset_post_service
from app.system.service.sys_role_service import reset_role_service
from app.system.service.sys_user_service import reset_user_service

#: 密码强度校验（``CommonUtil.checkPassword``）要求的形状，见 ``sys_login_controller``。
PASSWORD = "Abc12345!"

#: 登录用户 id（``admin`` 是 1；这里刻意用普通人，才能走到"隐藏 admin 角色"的分支）。
LOGIN_USER_ID = 2
#: 被查看/被操作的普通用户 id。
TARGET_USER_ID = 100
#: ``insertUser`` 的 ``useGeneratedKeys`` 回填值。
NEW_USER_ID = 101

#: ``sys_menu`` 授予的权限串（逗号会被 ``SysMenuService`` 拆开）。
MENU_PERMS = [
    "system:user:list",
    "system:user:query,system:user:add",
    "system:user:edit",
    "system:user:remove",
    "system:user:resetPwd",
]
#: ``GET /getInfo`` 之后控制器能通过的权限集合。
EXPECTED_PERMISSIONS = {
    "system:user:list",
    "system:user:query",
    "system:user:add",
    "system:user:edit",
    "system:user:remove",
    "system:user:resetPwd",
}


# --------------------------------------------------------------------------- 假库
#
# 假库的分派键是 **SQL 文本**，不是"第几次调用"。这样用例之间没有隐藏的调用顺序耦合，
# 而且某个用例多查/少查一张表会立刻暴露。


class _Result:
    """``CursorResult`` 的最小替身：mapper 只用到 ``keys/all/scalar/rowcount/lastrowid``。"""

    def __init__(
        self,
        rows: Optional[Sequence[Any]] = None,
        keys: Optional[Sequence[str]] = None,
        scalar: Any = None,
        rowcount: int = 0,
        lastrowid: Optional[int] = None,
    ) -> None:
        self._rows: List[Any] = list(rows or ())
        self._keys: List[str] = list(keys or ())
        self._scalar = scalar
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def keys(self) -> List[str]:
        return list(self._keys)

    def all(self) -> List[Any]:
        return list(self._rows)

    def scalar(self) -> Any:
        return self._scalar


#: ``selectUserVo`` 投影的列标签。与 ``SysUserMapper.xml`` 的 ``<sql id="selectUserVo">``
#: 一一对应，但**不含** SQLAlchemy 为重复 ``dept_id`` 生成的 ``dept_id_1`` ——
#: ``_map_user`` 只按标签名取第一个，足够。
_USER_VO_KEYS: Tuple[str, ...] = (
    "user_id",
    "user_no",
    "dept_id",
    "user_name",
    "nick_name",
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
    "sub_code",
    "parent_id",
    "dept_name",
    "order_num",
    "leader",
    "dept_status",
    "role_id",
    "role_name",
    "role_key",
    "role_sort",
    "data_scope",
    "role_status",
)

#: ``selectRoleVo`` 的 11 列（``_map_role`` 全都要）。
_ROLE_KEYS: Tuple[str, ...] = (
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

#: ``selectPostVo`` 的 8 列。
_POST_KEYS: Tuple[str, ...] = (
    "post_id",
    "post_code",
    "post_name",
    "post_sort",
    "status",
    "create_by",
    "create_time",
    "remark",
)


class _FakeSession:
    """``Session`` 的最小替身；只转发 ``execute``（mapper 不用别的）。"""

    def __init__(self, db: "_FakeDb") -> None:
        self._db = db

    def execute(self, statement: Any, params: Any = None) -> _Result:
        return self._db.execute(str(statement), params)


class _FakeDb:
    """按 SQL 分派的假库（见模块 docstring）。线程安全：审计写入发生在异步线程。"""

    def __init__(self) -> None:
        #: ``sys_user`` 全字段行（``selectUserVo`` 系列的数据源）。
        self.users: List[Dict[str, Any]] = []
        #: ``selectUserList`` 的数据源（只带 28 列）。
        self.user_list: List[Dict[str, Any]] = []
        #: ``selectRoleAll`` / ``selectRolePermissionByUserId`` 共用。
        self.roles: List[Dict[str, Any]] = []
        #: ``selectRoleListByUserId`` 的回显。
        self.role_ids_by_user: Dict[int, List[int]] = {}
        #: ``selectPostAll``。
        self.posts: List[Tuple[Any, ...]] = []
        #: ``selectPostListByUserId`` 的回显。
        self.post_ids_by_user: Dict[int, List[int]] = {}
        #: ``selectMenuPermsByUserId``。
        self.menu_perms: List[str] = []
        #: ``selectDeptById`` 的返回（``None`` 表示部门不存在）。
        self.dept: Optional[Dict[str, Any]] = None
        #: 已执行的语句：(规范化 SQL, 绑定参数, executemany 行数)
        self.statements: List[Tuple[str, Dict[str, Any], int]] = []
        #: ``sys_logininfor`` 的审计行。
        self.audit: List[Dict[str, Any]] = []
        self.next_user_id = NEW_USER_ID
        self._lock = threading.Lock()

    # ---- session_scope 替身 -------------------------------------------------
    def session_scope(self) -> Any:
        """``with session_scope() as session`` —— 事务语义在这里无关紧要。"""

        db = self

        class _Scope:
            def __enter__(self) -> _FakeSession:
                return _FakeSession(db)

            def __exit__(self, *exc_info: Any) -> bool:
                return False

        return _Scope()

    # ---- 执行 ---------------------------------------------------------------
    def execute(self, sql: str, params: Any = None) -> _Result:
        normalized = " ".join(sql.split()).lower()
        batch = params if isinstance(params, list) else None
        bound: Dict[str, Any] = dict(params) if isinstance(params, dict) else {}
        with self._lock:
            self.statements.append((normalized, bound, 0 if batch is None else len(batch)))

        # 1) PageHelper 的 count：把原语句包成子查询
        if normalized.startswith("select count(0) from ("):
            return _Result(scalar=len(self._select_user_list(bound)))

        # 2) 登录审计（异步线程）
        if normalized.startswith("insert into sys_logininfor"):
            with self._lock:
                self.audit.append(dict(bound))
            return _Result(rowcount=1)

        # 3) selectUserVo 系列（selectUserByUserName / ById / ByCertEntityID）
        if "from sys_user u" in normalized and "left join sys_user_role ur" in normalized:
            return self._select_user_vo(normalized, bound)

        # 4) selectUserList（多一个 d2 自连接）
        if "left join sys_dept d2" in normalized:
            rows = self._select_user_list(bound)
            return _Result(rows=[self._list_row(row) for row in rows], keys=_USER_LIST_COLUMNS)

        # 5) 唯一性校验
        if normalized.startswith("select count(1) from sys_user where user_name"):
            exists = any(user["user_name"] == bound.get("user_name") for user in self.users)
            return _Result(scalar=1 if exists else 0)
        if normalized.startswith("select user_id, phonenumber from sys_user"):
            return _Result(rows=[], keys=["user_id", "phonenumber"])
        if normalized.startswith("select user_id, email from sys_user"):
            return _Result(rows=[], keys=["user_id", "email"])

        # 6) 角色
        if "select distinct r.role_id" in normalized:
            rows = [tuple(role[key] for key in _ROLE_KEYS) for role in self.roles]
            return _Result(rows=rows, keys=_ROLE_KEYS)
        if normalized.startswith("select r.role_id from sys_role r"):
            ids = self.role_ids_by_user.get(bound.get("user_id"), [])
            return _Result(rows=[(role_id,) for role_id in ids])

        # 7) 菜单权限
        if normalized.startswith("select distinct m.perms"):
            return _Result(rows=[(perm,) for perm in self.menu_perms])

        # 8) 岗位
        if normalized.startswith("select post_id, post_code, post_name"):
            return _Result(rows=list(self.posts), keys=_POST_KEYS)
        if normalized.startswith("select p.post_id from sys_post p"):
            ids = self.post_ids_by_user.get(bound.get("user_id"), [])
            return _Result(rows=[(post_id,) for post_id in ids])

        # 9) 部门
        if normalized.startswith("select d.dept_id, d.parent_id"):
            rows = [] if self.dept is None else [tuple(self.dept[key] for key in _DEPT_COLUMNS)]
            return _Result(rows=rows, keys=_DEPT_COLUMNS)

        # 10) 写语句
        if normalized.startswith("insert into sys_user ("):
            # MyBatis: useGeneratedKeys -> keyProperty="userId"
            return _Result(rowcount=1, lastrowid=self.next_user_id)
        if normalized.startswith(("insert into sys_user_role", "insert into sys_user_post")):
            return _Result(rowcount=len(batch or ()))
        if normalized.startswith(("delete from sys_user_role", "delete from sys_user_post")):
            return _Result(rowcount=len(bound))
        if normalized.startswith("update sys_user set"):
            return _Result(rowcount=1)

        raise AssertionError(f"假库不认识这条 SQL: {normalized}")

    # ---- 查询实现 -----------------------------------------------------------
    def _select_user_vo(self, normalized: str, bound: Dict[str, Any]) -> _Result:
        if "u.user_name = :user_name" in normalized:
            matched = [u for u in self.users if u["user_name"] == bound.get("user_name")]
        elif "u.user_id = :user_id" in normalized:
            matched = [u for u in self.users if u["user_id"] == bound.get("user_id")]
        elif "u.cert_entity_id = :cert_entity_id" in normalized:
            matched = [
                u for u in self.users if u.get("cert_entity_id") == bound.get("cert_entity_id")
            ]
        else:
            raise AssertionError(f"假库不认识这条 selectUserVo: {normalized}")
        rows: List[Tuple[Any, ...]] = []
        for user in matched:
            rows.extend(_vo_rows(user))
        return _Result(rows=rows, keys=_USER_VO_KEYS)

    def _select_user_list(self, bound: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按绑定参数过滤 —— 等价于 XML 里的 ``<if>``，不做别的加工。"""
        rows: List[Dict[str, Any]] = []
        for row in self.user_list:
            if "user_id" in bound and row["user_id"] != bound["user_id"]:
                continue
            if "user_name" in bound:
                # XML: ``like concat('%', ?, '%')``
                if str(bound["user_name"]).lower() not in (row.get("user_name") or "").lower():
                    continue
            if "user_type" in bound and row.get("user_type") != bound["user_type"]:
                continue
            if "status" in bound and row.get("status") != bound["status"]:
                continue
            if "dept_id" in bound and row.get("dept_id") != bound["dept_id"]:
                continue
            if "tenant_id" in bound and row.get("tenant_id") != bound["tenant_id"]:
                continue
            if "exclude_id" in bound and row["user_id"] == bound["exclude_id"]:
                continue
            rows.append(row)
        return rows

    @staticmethod
    def _list_row(user: Dict[str, Any]) -> Tuple[Any, ...]:
        dept = user.get("dept") or {}
        values: Dict[str, Any] = {key: user.get(key) for key in _USER_LIST_COLUMNS}
        values.update(
            tenant_name=user.get("tenant_name"),
            dept_name=dept.get("dept_name"),
            leader=dept.get("leader"),
        )
        return tuple(values.get(key) for key in _USER_LIST_COLUMNS)


def _vo_rows(user: Dict[str, Any]) -> List[Tuple[Any, ...]]:
    """一行 ``sys_user`` -> 若干行 ``selectUserVo``（一个角色一行，Java 再合并）。"""
    dept = user.get("dept") or {}
    roles: List[Dict[str, Any]] = user.get("roles") or [{}]
    rows: List[Tuple[Any, ...]] = []
    for role in roles:
        values: Dict[str, Any] = {key: user.get(key) for key in _USER_VO_KEYS}
        values.update(
            dept_id=dept.get("dept_id"),
            parent_id=dept.get("parent_id"),
            dept_name=dept.get("dept_name"),
            order_num=dept.get("order_num"),
            leader=dept.get("leader"),
            dept_status=dept.get("status"),
            role_id=role.get("role_id"),
            role_name=role.get("role_name"),
            role_key=role.get("role_key"),
            role_sort=role.get("role_sort"),
            data_scope=role.get("data_scope"),
            role_status=role.get("status"),
        )
        rows.append(tuple(values[key] for key in _USER_VO_KEYS))
    return rows


class _FakeCache:
    """``RedisCache`` 替身：只实现令牌服务用到的四个方法，值按**对象**存。"""

    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}

    def get_cache_object(self, key: str) -> Any:
        return self.store.get(key)

    def set_cache_object(self, key: str, value: Any) -> None:
        self.store[key] = value

    def set_cache_object_with_timeout(
        self, key: str, value: Any, timeout: int, unit: Any
    ) -> None:
        self.store[key] = value

    def delete_object(self, key: str) -> bool:
        return self.store.pop(key, None) is not None

    def has_key(self, key: str) -> bool:
        return key in self.store


# --------------------------------------------------------------------------- 夹具


class _E2E:
    """一个用例可用的全部句柄。"""

    def __init__(self, client: TestClient, db: _FakeDb, cache: _FakeCache) -> None:
        self.client = client
        self.db = db
        self.cache = cache

    # ---- 登录 ---------------------------------------------------------------
    def login(self, user_name: str = "test01", password: str = PASSWORD) -> Any:
        return self.client.post("/login", json={"username": user_name, "password": password})

    def token(self, user_name: str = "test01", password: str = PASSWORD) -> str:
        body = self.login(user_name, password).json()
        assert body["code"] == 200, body
        return body["token"]

    def auth(self, user_name: str = "test01") -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token(user_name)}"}

    # ---- 断言辅助 -----------------------------------------------------------
    def statements(self, marker: str) -> List[Tuple[str, Dict[str, Any], int]]:
        return [row for row in self.db.statements if marker in row[0]]

    def data_statements(self, marker: str) -> List[Tuple[str, Dict[str, Any], int]]:
        """只要**取数**那条，排除 PageHelper 包出来的 count 语句。

        ``select count(0) from ( <原语句> ) table_count`` 里含着原语句的全部文本，
        按 ``marker`` 直接匹配会把 count 和数据查询一起捞出来。
        """
        return [row for row in self.statements(marker) if not row[0].startswith("select count(0) from (")]


@pytest.fixture
def e2e(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> Iterator[_E2E]:
    """重建整条对象图 + 换掉 MySQL/Redis 两处外围设施。

    为什么每个用例都要 ``reset_*``：这些单例会把"第一次构造时拿到的依赖"记住（正是
    Java 的 singleton 语义）。上一个用例的 ``RedisCache`` 是假对象，如果不丢弃，
    本用例的 ``TokenService`` 会继续用它 —— 那就不再是"每个用例一套新容器"了。
    """
    db = _FakeDb()
    for module in (
        sys_user_mapper,
        sys_user_role_mapper,
        sys_user_post_mapper,
        sys_dept_mapper,
        sys_menu_mapper,
        sys_role_mapper,
        sys_post_mapper,
        sys_logininfor_mapper,
    ):
        monkeypatch.setattr(module, "session_scope", db.session_scope)

    cache = _FakeCache()
    # TokenService / SysLoginService 都是**惰性**取 RedisCache（见各自模块的 property），
    # 所以替换模块级 ``get_redis_cache`` 就够了，不需要碰实例字段。
    monkeypatch.setattr(token_service_module, "get_redis_cache", lambda: cache)
    monkeypatch.setattr(login_service_module, "get_redis_cache", lambda: cache)

    _reset_object_graph()
    try:
        yield _E2E(client=client, db=db, cache=cache)
    finally:
        # 先把异步审计任务排空（此时假的 session_scope 还在），再让 monkeypatch 撤 patch。
        reset_async_manager()
        _reset_object_graph()


def _reset_object_graph() -> None:
    reset_jwt_authentication_token_filter()
    reset_token_service()
    # ``LogoutSuccessHandlerImpl`` 也是个进程级单例，而它把首次解析到的
    # ``TokenService``（以及后者缓存的 ``RedisCache``）一直握着 —— 不重置就会沿用
    # 上一个用例的 Redis 替身，登出删的是一把已经不存在的钥匙。
    reset_logout_success_handler()
    reset_login_service()
    reset_authentication_manager()
    reset_user_details_service()
    reset_menu_permission_service()
    reset_permission_service()
    reset_user_service()
    reset_role_service()
    reset_menu_service()
    reset_post_service()
    reset_dept_service()
    reset_user_controller()
    reset_login_controller()
    SecurityContextHolder.clear_context()
    clear_page()


def _seed_user(
    db: _FakeDb,
    *,
    user_id: int = LOGIN_USER_ID,
    user_name: str = "test01",
    password: Optional[str] = PASSWORD,
    roles: Optional[List[Dict[str, Any]]] = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """往假库里放一个可登录、可查询的机构用户。"""
    # ``selectDeptById`` 投影 26 列，``_map_dept`` 按列名逐个取，缺一个就 KeyError；
    # 先铺满 None，再覆盖用得上的那几列。
    dept: Dict[str, Any] = {column: None for column in _DEPT_COLUMNS}
    dept.update(
        dept_id=105,
        parent_id=100,
        ancestors="0,100",
        dept_name="研发部门",
        order_num="1",
        leader="admin",
        status="0",
        del_flag="0",
        sub_code="D105",
        tenant_id=100,
    )
    user: Dict[str, Any] = {
        "user_id": user_id,
        "user_no": user_id,
        "dept_id": dept["dept_id"],
        "user_name": user_name,
        "nick_name": "测试用户",
        "email": f"{user_name}@example.com",
        "avatar": "",
        "phonenumber": "13800000001",
        "password": encrypt_password(password) if password is not None else None,
        "sex": "0",
        "status": "0",
        "del_flag": "0",
        "user_type": "1",
        "cert_entity_id": None,
        "cert_id": None,
        "buss_id": user_name,
        "buss_name": dept["dept_name"],
        "eps_name": dept["dept_name"],
        "tenant_id": 100,
        "sub_code": "D105",
        "dept": dept,
        "roles": roles
        if roles is not None
        else [
            {
                "role_id": 2,
                "role_name": "普通角色",
                "role_key": "common",
                "role_sort": "2",
                "data_scope": "1",  # 全部数据权限 -> DataScope 不写片段
                "status": "0",
            }
        ],
    }
    user.update(overrides)
    db.users.append(user)
    db.user_list.append(user)
    db.dept = dict(dept)
    db.menu_perms = list(MENU_PERMS)
    return user


def _seed_catalogs(db: _FakeDb, target_user_id: int = TARGET_USER_ID) -> None:
    """下拉框与回显数据：角色列表、岗位列表、角色/岗位 id。"""
    db.roles = [
        {
            "role_id": 1,
            "role_name": "超级管理员",
            "role_key": "admin",
            "role_sort": "1",
            "data_scope": "1",
            "menu_check_strictly": True,
            "dept_check_strictly": True,
            "status": "0",
            "del_flag": "0",
            "create_time": None,
            "remark": "超级管理员",
        },
        {
            "role_id": 2,
            "role_name": "普通角色",
            "role_key": "common",
            "role_sort": "2",
            "data_scope": "1",
            "menu_check_strictly": True,
            "dept_check_strictly": True,
            "status": "0",
            "del_flag": "0",
            "create_time": None,
            "remark": "普通角色",
        },
    ]
    db.role_ids_by_user[target_user_id] = [2]
    # ``sys_post.post_sort`` 是 varchar，MyBatis 映射成 String —— 传 int 会被 pydantic 拒掉。
    db.posts = [
        (1, "ceo", "董事长", "1", "0", "admin", None, None),
        (2, "se", "项目经理", "2", "0", "admin", None, None),
    ]
    db.post_ids_by_user[target_user_id] = [2]


# --------------------------------------------------------------------------- 登录


class TestLogin:
    def test_the_token_is_issued_and_the_principal_is_cached(self, e2e: _E2E) -> None:
        """Java: ``tokenService.createToken(loginUser)`` -> JWT + ``login_tokens:<uuid>``。"""
        _seed_user(e2e.db)

        body = e2e.login().json()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        token = body["token"]
        # 令牌里只有 login_user_key（Java 的 setClaims 不写 sub/iat/exp）
        claims = jwt.decode(token, options={"verify_signature": False})
        assert list(claims) == ["login_user_key"]
        user_key = claims["login_user_key"]
        assert user_key

        cached = e2e.cache.store[f"{LOGIN_TOKEN_KEY}{user_key}"]
        assert isinstance(cached, LoginUser)
        assert cached.user is not None and cached.user.user_name == "test01"
        assert cached.token == user_key
        # permissions 在登录时就固化进缓存（之后改角色不影响已签发的令牌）
        assert cached.permissions == EXPECTED_PERMISSIONS
        # setUserAgent 的三个字段来自请求
        assert cached.ipaddr is not None
        assert cached.browser is not None
        assert cached.expire_time is not None

    def test_the_audit_row_is_written(self, e2e: _E2E) -> None:
        """Java: ``AsyncManager.me().execute(AsyncFactory.recordLogininfor(...))``。"""
        _seed_user(e2e.db)

        e2e.login()

        _wait_until(lambda: bool(e2e.db.audit))
        assert e2e.db.audit[0]["user_name"] == "test01"
        assert e2e.db.audit[0]["status"] == "0"  # Constants.SUCCESS
        assert e2e.db.audit[0]["msg"] == "登录成功"

    def test_a_wrong_password_is_a_500_envelope_with_http_200(self, e2e: _E2E) -> None:
        """``BadCredentialsException`` -> ``user.password.not.match``，HTTP 仍是 200。"""
        _seed_user(e2e.db)

        response = e2e.login(password="Wrong123!")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "用户不存在/密码错误"}
        assert e2e.cache.store == {}

    def test_an_unknown_account_is_indistinguishable_from_a_wrong_password(
        self, e2e: _E2E
    ) -> None:
        """``hideUserNotFoundExceptions`` 把"用户不存在"也改写成密码错误。"""
        response = e2e.login(user_name="nobody")

        assert response.json() == {"code": 500, "msg": "用户不存在/密码错误"}

    def test_a_weak_password_never_reaches_the_database(self, e2e: _E2E) -> None:
        """``checkPassword`` 在控制器里，先于验证码与凭证校验。"""
        _seed_user(e2e.db)

        response = e2e.login(password="abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500
        assert response.json()["msg"].startswith("对不起，密码长度8-20位")
        assert e2e.db.statements == []  # 一次 SQL 都没发
        assert e2e.db.audit == []


# --------------------------------------------------------------------------- 令牌


class TestTokenAuthority:
    def test_a_request_without_a_token_is_refused(self, e2e: _E2E) -> None:
        """``FilterSecurityInterceptor`` -> ``AuthenticationEntryPoint``：HTTP 200 + 401.

        ``AuthenticationEntryPointImpl`` 把请求路径拼进了消息里。
        """
        response = e2e.client.get("/system/user/list")

        assert response.status_code == 200
        assert response.json() == {
            "code": 401,
            "msg": "请求访问：/system/user/list，认证失败，无法访问系统资源",
        }

    def test_an_unknown_bearer_token_is_refused(self, e2e: _E2E) -> None:
        """JWT 签名有效但 Redis 里没有会话 —— 登出后的令牌就是这种状态。"""
        _seed_user(e2e.db)
        headers = e2e.auth()
        e2e.cache.store.clear()

        response = e2e.client.get("/system/user/list", headers=headers)

        assert response.json()["code"] == 401

    def test_a_permission_is_enforced_after_the_login(self, e2e: _E2E) -> None:
        """``@PreAuthorize("@ss.hasPermi('system:user:query')")`` -> 缺权限回 code 403。"""
        _seed_user(e2e.db)
        # 登录时只给 list，不给 query
        e2e.db.menu_perms = ["system:user:list"]

        response = e2e.client.get(f"/system/user/{TARGET_USER_ID}", headers=e2e.auth())

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- 查询


class TestList:
    def test_the_list_endpoint_returns_the_paged_envelope(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)

        response = e2e.client.get("/system/user/list?pageNum=1&pageSize=10", headers=e2e.auth())

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert body["total"] == 1
        assert [row["userName"] for row in body["rows"]] == ["test01"]
        assert body["rows"][0]["dept"]["deptName"] == "研发部门"
        assert "password" not in body["rows"][0]  # @JsonIgnore

    def test_the_list_goes_through_pagehelper(self, e2e: _E2E) -> None:
        """先 count 再 ``LIMIT 0, 10`` —— ``startPage()`` 的效果。"""
        _seed_user(e2e.db)

        e2e.client.get("/system/user/list?pageNum=1&pageSize=10", headers=e2e.auth())

        counts = e2e.statements("select count(0) from (")
        assert len(counts) == 1
        data = e2e.data_statements("left join sys_dept d2")
        assert len(data) == 1
        assert data[0][0].endswith("limit 0, 10")

    def test_the_controller_forces_the_institution_user_type(self, e2e: _E2E) -> None:
        """``list`` 里 ``user.setUserType("1")`` —— 传 2 也覆盖成 1。"""
        _seed_user(e2e.db)

        e2e.client.get("/system/user/list?userType=2", headers=e2e.auth())

        data = e2e.data_statements("left join sys_dept d2")
        assert data[0][1]["user_type"] == "1"

    def test_a_name_filter_reaches_the_sql(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)

        body = e2e.client.get(
            "/system/user/list?userName=nomatch", headers=e2e.auth()
        ).json()

        assert body["total"] == 0
        assert body["rows"] == []
        # PageHelper 在 count 为 0 时**根本不执行** data 语句（``select_page`` 里那条
        # ``if total <= 0: return PageList([])``，对应 ``PageInterceptor#intercept``），
        # 所以这个筛选条件只能从 COUNT 语句的参数上验证。
        assert e2e.data_statements("left join sys_dept d2") == []
        counts = e2e.statements("select count(0) from (")
        assert len(counts) == 1
        assert counts[0][1]["user_name"] == "nomatch"

    def test_list_my_queries_only_the_current_user(self, e2e: _E2E) -> None:
        """``listMy`` -> ``user.setUserId(SecurityUtils.getUserId())``。"""
        _seed_user(e2e.db)

        body = e2e.client.get("/system/user/listMy", headers=e2e.auth()).json()

        assert body["total"] == 1
        assert e2e.data_statements("left join sys_dept d2")[0][1]["user_id"] == LOGIN_USER_ID


class TestDetail:
    def test_the_detail_returns_the_user_with_its_dropdowns(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        _seed_user(e2e.db, user_id=TARGET_USER_ID, user_name="target")
        _seed_catalogs(e2e.db)

        body = e2e.client.get(
            f"/system/user/{TARGET_USER_ID}", headers=e2e.auth()
        ).json()

        assert body["code"] == 200
        assert body["data"]["userId"] == TARGET_USER_ID
        assert body["data"]["userName"] == "target"
        assert body["postIds"] == [2]
        assert body["roleIds"] == [2]

    def test_the_admin_role_is_hidden_when_the_target_is_not_admin(self, e2e: _E2E) -> None:
        """Java: ``SysUser.isAdmin(userId) ? roles : roles.stream().filter(r -> !r.isAdmin())``."""
        _seed_user(e2e.db)
        _seed_catalogs(e2e.db)

        body = e2e.client.get(
            f"/system/user/{TARGET_USER_ID}", headers=e2e.auth()
        ).json()

        assert [role["roleKey"] for role in body["roles"]] == ["common"]

    def test_the_admin_role_is_visible_for_the_admin_target(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        _seed_catalogs(e2e.db)

        body = e2e.client.get("/system/user/1", headers=e2e.auth()).json()

        assert [role["roleKey"] for role in body["roles"]] == ["admin", "common"]
        assert body["data"] is None  # 查不到这个用户，但键存在（HashMap.put）

    def test_the_bare_route_is_only_reachable_with_a_trailing_slash(self, e2e: _E2E) -> None:
        """``@GetMapping(value = {"/", ...})`` 只占住 ``/system/user/``。

        不带尾斜杠时路径上只剩 ``@PostMapping``（``add``），Spring 回 405，再被
        ``GlobalExceptionHandler`` 翻成 ``code 500`` —— 实测 Java 就是这样。Python 侧
        绝不能为了“顺手”多挂一个 ``@router.get("")``（以前挂过，这个用例曾断言裸路径
        返回下拉数据，属于与 Java 不符的多余行为）。
        """
        _seed_user(e2e.db)
        _seed_catalogs(e2e.db)

        bare = e2e.client.get("/system/user", headers=e2e.auth()).json()
        assert bare["code"] == 500
        assert bare["msg"] == "Request method 'GET' not supported"

        body = e2e.client.get("/system/user/", headers=e2e.auth()).json()
        assert body["code"] == 200
        assert "data" not in body
        assert body["posts"]
        assert [role["roleKey"] for role in body["roles"]] == ["common"]


# --------------------------------------------------------------------------- 写


class TestWrite:
    def test_add_persists_the_user_then_the_post_and_role_links(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        _seed_catalogs(e2e.db)

        body = e2e.client.post(
            "/system/user",
            headers=e2e.auth(),
            json={
                "userName": "newbie",
                "nickName": "新同事",
                "password": PASSWORD,
                "deptId": 105,
                "phonenumber": "13900000002",
                "email": "newbie@example.com",
                "sex": "0",
                "status": "0",
                "postIds": [1, 2],
                "roleIds": [2],
            },
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}

        # ``sys_logininfor`` 是登录时异步写的审计行，与本次写入无关，必须排除；
        # 否则它的先后位置会让断言随机失败。
        inserts = [
            row
            for row in e2e.db.statements
            if row[0].startswith("insert into") and "sys_logininfor" not in row[0]
        ]
        assert [statement_label(sql) for sql, _, _ in inserts] == [
            "insert into sys_user",
            "insert into sys_user_post",
            "insert into sys_user_role",
        ]
        user_params = inserts[0][1]
        assert user_params["user_name"] == "newbie"
        assert user_params["create_by"] == "test01"  # SecurityUtils.getUsername()
        assert user_params["buss_name"] == "研发部门"  # 由 deptId 反查
        assert user_params["tenant_id"] == 100
        assert matches_password(PASSWORD, user_params["password"])  # 落库前加密
        assert inserts[1][2] == 2  # executemany 两行岗位
        assert inserts[2][2] == 1  # 一行角色

    def test_add_rejects_a_duplicate_login_name(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)

        body = e2e.client.post(
            "/system/user",
            headers=e2e.auth(),
            json={"userName": "test01", "nickName": "重名", "password": PASSWORD},
        ).json()

        assert body == {"code": 500, "msg": ADD_USER_NAME_EXISTS.format("test01")}
        assert e2e.statements("insert into sys_user (") == []

    def test_add_rejects_a_weak_password_before_inserting(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)

        body = e2e.client.post(
            "/system/user",
            headers=e2e.auth(),
            json={"userName": "newbie", "nickName": "新同事", "password": "abc"},
        ).json()

        assert body["code"] == 500
        assert e2e.statements("insert into sys_user (") == []

    def test_edit_rewrites_links_before_the_row(self, e2e: _E2E) -> None:
        """Java 的顺序：删角色 -> 加角色 -> 删岗位 -> 加岗位 -> 更新主表。"""
        _seed_user(e2e.db)  # 登录/操作人
        _seed_user(e2e.db, user_id=TARGET_USER_ID, user_name="target")
        _seed_catalogs(e2e.db)

        body = e2e.client.put(
            "/system/user",
            headers=e2e.auth(),
            json={
                "userId": TARGET_USER_ID,
                "userName": "target",
                "nickName": "改名",
                "password": PASSWORD,
                "deptId": 105,
                "postIds": [1],
                "roleIds": [2],
            },
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        order = [
            statement_label(sql)
            for sql, _, _ in e2e.db.statements
            if sql.startswith(
                (
                    "delete from sys_user_role",
                    "insert into sys_user_role",
                    "delete from sys_user_post",
                    "insert into sys_user_post",
                    "update sys_user set",
                )
            )
        ]
        assert order == [
            "delete from sys_user_role",
            "insert into sys_user_role",
            "delete from sys_user_post",
            "insert into sys_user_post",
            "update sys_user",
        ]
        update = e2e.statements("update sys_user set")[0][1]
        assert update["user_id"] == TARGET_USER_ID
        assert update["update_by"] == "test01"
        assert update["nick_name"] == "改名"
        assert update["buss_name"] == "研发部门"

    def test_edit_refuses_the_super_admin(self, e2e: _E2E) -> None:
        """``checkUserAllowed`` -> ``CustomException`` -> HTTP 200 + code 500。"""
        _seed_user(e2e.db)

        body = e2e.client.put(
            "/system/user",
            headers=e2e.auth(),
            json={"userId": 1, "userName": "admin"},
        ).json()

        assert body == {"code": 500, "msg": "不允许操作超级管理员用户"}
        assert e2e.statements("update sys_user set") == []

    def test_remove_soft_deletes_with_an_in_clause(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)

        body = e2e.client.delete(
            f"/system/user/{TARGET_USER_ID},{TARGET_USER_ID + 1}", headers=e2e.auth()
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        soft_delete = e2e.statements("update sys_user set del_flag")
        assert len(soft_delete) == 1
        assert soft_delete[0][1] == {"p0": TARGET_USER_ID, "p1": TARGET_USER_ID + 1}
        assert soft_delete[0][0].endswith("user_id in (:p0, :p1)")
        # 关联表先删
        assert e2e.statements("delete from sys_user_role")[0][1] == {
            "p0": TARGET_USER_ID,
            "p1": TARGET_USER_ID + 1,
        }

    def test_reset_pwd_stores_a_bcrypt_hash(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        _seed_user(e2e.db, user_id=TARGET_USER_ID, user_name="target")

        body = e2e.client.put(
            "/system/user/resetPwd",
            headers=e2e.auth(),
            json={"userId": TARGET_USER_ID, "password": PASSWORD},
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        params = e2e.statements("update sys_user set")[0][1]
        assert params["user_id"] == TARGET_USER_ID
        assert matches_password(PASSWORD, params["password"])

    def test_reset_pwd_rejects_a_weak_password(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        _seed_user(e2e.db, user_id=TARGET_USER_ID, user_name="target")

        body = e2e.client.put(
            "/system/user/resetPwd",
            headers=e2e.auth(),
            json={"userId": TARGET_USER_ID, "password": "abc"},
        ).json()

        assert body["code"] == 500
        assert e2e.statements("update sys_user set") == []

    def test_change_status_writes_through_update_user(self, e2e: _E2E) -> None:
        """走 ``updateUser``（XML 里那条 ``updateUserStatus`` 是死语句）。"""
        _seed_user(e2e.db)
        _seed_user(e2e.db, user_id=TARGET_USER_ID, user_name="target")

        body = e2e.client.put(
            "/system/user/changeStatus",
            headers=e2e.auth(),
            json={"userId": TARGET_USER_ID, "status": "1"},
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        updates = e2e.statements("update sys_user set")
        assert len(updates) == 1
        assert "status = :status" in updates[0][0]
        assert updates[0][1]["status"] == "1"


# --------------------------------------------------------------------------- 登出


class TestLogout:
    def test_logout_deletes_the_session_and_answers_success(self, e2e: _E2E) -> None:
        _seed_user(e2e.db)
        headers = e2e.auth()
        assert len(e2e.cache.store) == 1  # 会话在 Redis: login_tokens:<uuid>

        body = e2e.client.post("/logout", headers=headers).json()

        assert body == {"code": 200, "msg": "退出成功"}
        assert e2e.cache.store == {}
        # 令牌本身仍然有效（JWT 无状态），只是解不出会话了
        assert e2e.client.get("/system/user/list", headers=headers).json()["code"] == 401

    def test_logout_without_a_token_still_answers_success(self, e2e: _E2E) -> None:
        """``LogoutFilter`` 在认证之前，所以无令牌也是 200，且不写审计行。"""
        assert e2e.client.post("/logout").json() == {"code": 200, "msg": "退出成功"}
        # 没有 loginUser 就没有 ``AsyncFactory.recordLogininfor``，不存在异步竞态。
        assert e2e.db.audit == []


# --------------------------------------------------------------------------- 工具


def statement_label(sql: str) -> str:
    """把一条语句归成“动作 + 表”。

    ``insert into sys_user (user_id, ...) values (...)`` -> ``insert into sys_user``
    ``delete from sys_user_role where user_id=:user_id`` -> ``delete from sys_user_role``
    ``update sys_user set nick_name=:nick_name, ...``      -> ``update sys_user``

    直接对字符串做 ``split``/``replace`` 会被 ``where`` / ``set`` / 括号干扰，
    按前缀切第一个标识符才不会误判。
    """
    for prefix in ("delete from", "insert into", "update"):
        if sql.startswith(prefix):
            rest = sql[len(prefix):].strip()
            # 注意 ``insert into sys_user_role(user_id, role_id) values ...`` 这里
            # 表名后**没有**空格，直接 ``split()[0]`` 会连列名一起带出来。
            return f"{prefix} {rest.split()[0].split('(')[0]}" if rest else prefix
    return sql


def _wait_until(predicate: Callable[[], bool], timeout: float = 5.0) -> None:
    """轮询等待异步审计线程（``AsyncManager`` 的任务不保证在响应前完成）。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate(), "等待异步任务超时"


__all__ = ["e2e"]
