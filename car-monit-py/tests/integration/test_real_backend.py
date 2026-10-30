"""真实 MySQL + Redis 联调（**不用 mock**）.

# Migrated from: (no Java test) -- 对应 Java 侧 ``@SpringBootTest`` 打真实库的验收用例

这个模块做什么
--------------
单元测试（``tests/test_*.py``）全部用替身：mapper 的 SQL 只被断言"拼出来长什么样"，
service 的返回值被预先摆好，Redis 是个 dict。这样快、稳，但**看不到真库的形状**。
本模块反过来：按 ``config/application.yml`` 连真实的 MySQL / Redis，用
``TestClient`` 打真实的 controller，断言真实响应。

实测已经靠它抓到三个单元测试看不见的缺陷（都已修复，这里留了回归护栏）：

* ``GET /getRouters`` -> ``pydantic ValidationError``：库里 ``sys_menu.is_frame`` /
  ``is_cache`` 是 ``int``，实体声明 ``String``，MyBatis 靠 ``ResultSet.getString()``
  隐式转换，pydantic 不会 —— 见 :class:`TestMenuFlagsRegression`。
* ``GET /manager/bigScreen/carStatistics`` -> ``ModuleNotFoundError``：函数内的惰性
  import 写错了包名，单元测试从未执行到 —— 见 :class:`TestBigScreenRegression`。
* ``GET /monitor/cache`` -> ``AttributeError: 'dict' object has no attribute
  'splitlines'``：``redis-py`` 给 ``INFO`` 注册了 response callback，返回嵌套 dict，
  而 Java 的 ``RedisCallback`` 拿的是原始文本 —— 见 :class:`TestCacheMonitorRegression`。

怎么跑
------
.. code-block:: shell

    .venv\\Scripts\\python.exe -m pytest tests/integration -v

默认的 ``pytest`` 也会收集本模块，但**服务不可达时整模块 skip**，所以离线跑单测
仍然全绿。真跑起来时，本模块会**写**真实数据库：

1. 临时把 ``admin`` / ``admin_test`` 的密码改成 :data:`TEST_PASSWORD`，用真实
   ``POST /login`` 换 token，用例结束后改回去（``finally`` + 崩溃兜底文件）。
2. 用真实 token 打各 controller，读真实的 ``sys_logininfor`` / Redis 里的
   ``login_tokens:*`` / ``captcha_codes:*``。
3. 只在 ``sys_logininfor`` 里插入本模块自己造的那几条探针记录，并在用例内删掉。

环境事实（2026-10 实测，写在这里免得后人反复查）
------------------------------------------------
* MySQL ``127.0.0.1:3307/carmonitdb``（8.0.30，84 张表），Redis ``127.0.0.1:6379/0``
  （8.10.2）。
* **本库没有 ``sys_upgrade_info`` 表** —— ``/system/upgradeInfo/list`` 必然回
  ``code 500``。这不是代码缺陷：Java 打同一个库同样 500。见
  :func:`test_upgrade_info_degrades_when_the_table_is_missing`。
* ``admin_test``（user_id 966）只有登录态、没有任何菜单权限，所以它在
  ``@PreAuthorize`` 端点上拿到 ``403 没有权限，请联系管理员授权`` —— 这是**正确**
  行为，不是 bug。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.common.constant.constants import (
    CAPTCHA_CODE_KEY,
    LOGIN_TOKEN_KEY,
    LOGIN_USER_KEY,
    TOKEN,
)
from app.common.core.redis.redis_cache import get_redis_cache, reset_redis_cache
from app.config.database import check_connection as check_database
from app.config.database import dispose_engine, get_engine
from app.config.redis_config import check_connection as check_redis
from app.framework.security.handle.logout_success_handler_impl import (
    reset_logout_success_handler,
)
from app.framework.web.service.token_service import reset_token_service
from app.logging_config import reset_logging
from app.settings import get_settings, reset_settings_cache

pytestmark = pytest.mark.integration


# --------------------------------------------------------------------------- 可达性门槛

def _unavailable_reason() -> Optional[str]:
    """返回 skip 理由；两者都通就返回 ``None``."""
    if not check_database():
        return (
            "MySQL 不可达（config/application.yml -> spring.datasource.druid.master.url），"
            "跳过真实联调用例"
        )
    if not check_redis():
        return (
            "Redis 不可达（config/application.yml -> spring.redis），"
            "跳过真实联调用例"
        )
    return None


_SKIP_REASON = _unavailable_reason()
if _SKIP_REASON is not None:  # pragma: no cover - 取决于本机是否起了服务
    pytest.skip(_SKIP_REASON, allow_module_level=True)


# --------------------------------------------------------------------------- 常量

#: 联调期间临时设的强口令。必须过 ``checkPassword``（8-20 位 + 大小写 + 数字 + 符号）。
TEST_PASSWORD = "Mig@Test123"

#: 崩溃兜底：进程被 kill 时原密码哈希留在这里，下次 import 自动还原。
_BACKUP_PATH = Path(__file__).with_name(".password_backup.json")

#: 分页探针用的用户名（不存在的账号，走失败分支，不产生 token）。
_PROBE_USER = "no_such_user_probe"

#: ``sys_user.user_type`` 等字段不影响本模块断言。
_ADMIN = "admin"
_LIMITED = "admin_test"


# --------------------------------------------------------------------------- 数据库直连

def _scalar(sql: str, **params: Any) -> Any:
    """跑一条标量 SQL（**独立连接**，不参与请求的事务）。"""
    with get_engine().connect() as conn:
        return conn.execute(text(sql), params).scalar()


def _execute(sql: str, **params: Any) -> int:
    """跑一条写 SQL 并提交。"""
    with get_engine().begin() as conn:
        return conn.execute(text(sql), params).rowcount or 0


def _table_exists(table_name: str) -> bool:
    found = _scalar(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :name",
        name=table_name,
    )
    return bool(found)


def _fetch_password(user_name: str) -> Optional[str]:
    return _scalar("SELECT password FROM sys_user WHERE user_name = :name", name=user_name)


def _store_password(user_name: str, password_hash: str) -> None:
    _execute(
        "UPDATE sys_user SET password = :pwd WHERE user_name = :name",
        pwd=password_hash,
        name=user_name,
    )


def _hash_password(password: str) -> str:
    """Java: ``SecurityUtils.encryptPassword`` -> ``BCryptPasswordEncoder``."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def _recover_from_previous_crash() -> None:
    """上一次运行被强杀时，把原密码哈希写回去（否则账号永久失联）。"""
    if not _BACKUP_PATH.exists():  # pragma: no cover - 只在异常路径命中
        return
    try:
        backup: Dict[str, str] = json.loads(_BACKUP_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # pragma: no cover - 文件损坏时不阻塞后续用例
        _BACKUP_PATH.unlink(missing_ok=True)
        return
    for user_name, password_hash in backup.items():
        _store_password(user_name, password_hash)
    _BACKUP_PATH.unlink(missing_ok=True)


def _wait_until(predicate: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1) -> bool:
    """轮询等待。``AsyncManager`` 是真实的线程池，落库是**异步**的。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


# --------------------------------------------------------------------------- 客户端

@pytest.fixture(scope="session")
def real_client() -> Iterator[TestClient]:
    """真实应用实例.

    ``raise_server_exceptions=False`` 很关键：未被捕获的 ``Exception`` 在 Starlette 里
    由 ``ServerErrorMiddleware`` 先写响应、再**重新抛出**。开着这个开关，测试里看到的是
    异常而不是"线上会返回什么"；关掉它，``code 500`` 的信封才会真实呈现。
    """
    reset_settings_cache()
    reset_logging()

    from app.main import create_app

    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client

    dispose_engine()
    # 本模块把**真实**的 RedisCache / TokenService 钉到了几个进程级单例上。不拆掉
    # 的话，后面的单元测试即使注入替身，惰性解析到的还是这条真实连接
    # （``LogoutSuccessHandlerImpl`` 就会把首次拿到的 TokenService 一直握着）。
    reset_redis_cache()
    reset_token_service()
    reset_logout_success_handler()


# --------------------------------------------------------------------------- 登录

def _captcha(client: TestClient) -> Tuple[str, str]:
    """拿一对 ``(uuid, 答案)``；答案从 Redis 里按 **Java 的序列化格式**读回来."""
    payload = client.get("/captchaImage").json()
    assert payload["code"] == 200, payload
    uuid = payload["uuid"]
    # 必须走 RedisCache.get_cache_object —— FastJson2 风格的 JSON 文本，
    # 直接 client.get() 会拿到带引号的 '"7"'，喂回 /login 就是"验证码错误"。
    answer = get_redis_cache().get_cache_object(CAPTCHA_CODE_KEY + uuid)
    assert answer is not None, "验证码没有写进 Redis"
    return uuid, str(answer)


def _login(client: TestClient, user_name: str, password: str = TEST_PASSWORD) -> Dict[str, Any]:
    """走真实 ``POST /login``（带真实验证码）."""
    uuid, answer = _captcha(client)
    response = client.post(
        "/login",
        json={"username": user_name, "password": password, "code": answer, "uuid": uuid},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def tokens(real_client: TestClient) -> Iterator[Dict[str, str]]:
    """临时改口令 -> 真实登录 -> 拿 token -> 结束**一定**改回去."""
    _recover_from_previous_crash()

    originals: Dict[str, str] = {}
    new_hash = _hash_password(TEST_PASSWORD)
    try:
        for user_name in (_ADMIN, _LIMITED):
            original = _fetch_password(user_name)
            assert original, "sys_user 里找不到账号 %s" % user_name
            originals[user_name] = original
        # 先落盘再改库：改完密码的瞬间进程被杀也不会丢原哈希。
        _BACKUP_PATH.write_text(json.dumps(originals), encoding="utf-8")
        for user_name in originals:
            _store_password(user_name, new_hash)

        issued: Dict[str, str] = {}
        for user_name in originals:
            payload = _login(real_client, user_name)
            assert payload["code"] == 200, payload
            issued[user_name] = payload[TOKEN]
        yield issued
    finally:
        for user_name, original in originals.items():
            _store_password(user_name, original)
        _BACKUP_PATH.unlink(missing_ok=True)


def _auth(token: str) -> Dict[str, str]:
    # Java: ``Constants.TOKEN_PREFIX`` = "Bearer "
    return {"Authorization": "Bearer " + token}


@pytest.fixture(scope="session")
def admin_headers(tokens: Dict[str, str]) -> Dict[str, str]:
    return _auth(tokens[_ADMIN])


@pytest.fixture(scope="session")
def limited_headers(tokens: Dict[str, str]) -> Dict[str, str]:
    return _auth(tokens[_LIMITED])


def _token_uuid(token: str) -> str:
    """JWT 里 ``login_user_key`` -> Redis 里的 ``login_tokens:<uuid>`` 后缀."""
    claims = jwt.decode(token, options={"verify_signature": False})
    return str(claims[LOGIN_USER_KEY])


# --------------------------------------------------------------------------- 健康检查

class TestHealth:
    """``GET /health`` —— 两侧依赖都得是 ``UP``."""

    def test_reports_both_components_up(self, real_client: TestClient) -> None:
        payload = real_client.get("/health").json()

        assert payload["code"] == 200
        assert payload["data"]["status"] == "UP"
        assert payload["data"]["components"] == {"db": "UP", "redis": "UP"}

    def test_reports_the_java_version_string(self, real_client: TestClient) -> None:
        data = real_client.get("/health").json()["data"]

        assert data["version"] == get_settings().ruoyi.version
        assert data["application"] == get_settings().ruoyi.name


# --------------------------------------------------------------------------- 验证码

class TestCaptcha:
    """``GET /captchaImage`` —— 必须真的在 Redis 里留下 ``captcha_codes:<uuid>``."""

    def test_returns_an_uuid_and_a_base64_jpeg(self, real_client: TestClient) -> None:
        payload = real_client.get("/captchaImage").json()

        assert payload["code"] == 200
        assert len(payload["uuid"]) == 32
        # 60 秒 / 120 分钟都见过；这里只钉住"是一串 base64"，不钉长度。
        assert isinstance(payload["img"], str) and len(payload["img"]) > 100

    def test_the_answer_is_stored_with_the_java_ttl(self, real_client: TestClient) -> None:
        """Java: ``redisCache.setCacheObject(key, code, CAPTCHA_EXPIRATION, TimeUnit.MINUTES)``."""
        uuid = real_client.get("/captchaImage").json()["uuid"]
        cache = get_redis_cache()

        assert cache.has_key(CAPTCHA_CODE_KEY + uuid) is True
        ttl = cache.get_expire(CAPTCHA_CODE_KEY + uuid)
        assert 0 < ttl <= 120

    def test_the_answer_matches_the_configured_captcha_type(self, real_client: TestClient) -> None:
        """``ruoyi.captchaType: math`` -> 答案是算术结果（数字字符串）."""
        uuid = real_client.get("/captchaImage").json()["uuid"]
        answer = get_redis_cache().get_cache_object(CAPTCHA_CODE_KEY + uuid)

        assert get_settings().ruoyi.captcha_type == "math"
        assert str(answer).lstrip("-").isdigit()


# --------------------------------------------------------------------------- 登录

class TestLogin:
    """``POST /login`` —— 三条分支：弱口令 / 密码错 / 成功."""

    def test_a_weak_password_is_rejected_before_the_captcha(
        self, real_client: TestClient
    ) -> None:
        """``checkPassword`` 排在验证码之前，所以**不消耗**验证码、**不写**登录日志."""
        uuid, answer = _captcha(real_client)
        cache = get_redis_cache()
        before = _scalar("SELECT COUNT(*) FROM sys_logininfor WHERE user_name = :n", n=_ADMIN)

        payload = real_client.post(
            "/login",
            json={"username": _ADMIN, "password": "123456", "code": answer, "uuid": uuid},
        ).json()

        assert payload["code"] == 500
        assert payload["msg"] == "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"
        # 验证码没被消耗 —— 这是顺序正确的证据。
        assert cache.has_key(CAPTCHA_CODE_KEY + uuid) is True
        assert _scalar("SELECT COUNT(*) FROM sys_logininfor WHERE user_name = :n", n=_ADMIN) == before

    def test_a_wrong_password_fails_and_consumes_the_captcha(
        self, tokens: Dict[str, str], real_client: TestClient
    ) -> None:
        uuid, answer = _captcha(real_client)
        cache = get_redis_cache()

        payload = real_client.post(
            "/login",
            json={"username": _ADMIN, "password": "Wrong@Test123", "code": answer, "uuid": uuid},
        ).json()

        assert payload["code"] == 500
        assert payload["msg"] == "用户不存在/密码错误"
        # Java 在 validateCaptcha 里就 deleteObject，无论后面成不成功。
        assert cache.has_key(CAPTCHA_CODE_KEY + uuid) is False

    def test_a_wrong_captcha_is_rejected(self, tokens: Dict[str, str], real_client: TestClient) -> None:
        uuid, _ = _captcha(real_client)

        payload = real_client.post(
            "/login",
            json={"username": _ADMIN, "password": TEST_PASSWORD, "code": "定错的答案", "uuid": uuid},
        ).json()

        assert payload["code"] == 500
        assert payload["msg"] == "验证码错误"

    def test_the_login_writes_an_audit_row(self, tokens: Dict[str, str], real_client: TestClient) -> None:
        """``AsyncManager`` 是真实线程池，落库异步 —— 必须轮询."""

        def count() -> int:
            return int(
                _scalar(
                    "SELECT COUNT(*) FROM sys_logininfor WHERE user_name = :n", n=_PROBE_USER
                )
            )

        before = count()
        try:
            uuid, answer = _captcha(real_client)
            payload = real_client.post(
                "/login",
                json={"username": _PROBE_USER, "password": TEST_PASSWORD, "code": answer, "uuid": uuid},
            ).json()
            assert payload["code"] == 500

            assert _wait_until(lambda: count() > before), "登录日志没有落库"
            row = _scalar(
                "SELECT msg FROM sys_logininfor WHERE user_name = :n ORDER BY login_time DESC LIMIT 1",
                n=_PROBE_USER,
            )
            assert row == "用户不存在/密码错误"
        finally:
            # 只删本用例自己造的那几条，别动真实审计记录。
            _execute("DELETE FROM sys_logininfor WHERE user_name = :n", n=_PROBE_USER)

    def test_a_successful_login_issues_a_token_backed_by_redis(
        self, tokens: Dict[str, str], real_client: TestClient
    ) -> None:
        token = tokens[_ADMIN]
        cache = get_redis_cache()

        assert token
        assert cache.has_key(LOGIN_TOKEN_KEY + _token_uuid(token)) is True
        # Java: createToken -> refreshToken(loginUser) -> expire(key, expireTime, MINUTES)
        ttl = cache.get_expire(LOGIN_TOKEN_KEY + _token_uuid(token))
        assert 0 < ttl <= get_settings().token.expire_time * 60


# --------------------------------------------------------------------------- 身份与路由

class TestIdentity:
    """``GET /getInfo`` —— ``admin`` 必须拿到 ``*:*:*``."""

    def test_admin_gets_the_wildcard_permission(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get("/getInfo", headers=admin_headers).json()

        assert payload["code"] == 200
        assert payload["user"]["userId"] == 1
        assert payload["user"]["userName"] == _ADMIN
        assert payload["roles"] == ["admin"]
        assert payload["permissions"] == ["*:*:*"]

    def test_the_legacy_frontend_flags_are_present(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """Java: ``ajax.put("pjFlag", 0); ajax.put("overdue", false);`` —— 前端还在读."""
        payload = real_client.get("/getInfo", headers=admin_headers).json()

        assert payload["pjFlag"] == 0
        assert payload["overdue"] is False

    def test_the_limited_account_has_no_wildcard(
        self, real_client: TestClient, limited_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get("/getInfo", headers=limited_headers).json()

        assert payload["code"] == 200
        assert payload["user"]["userName"] == _LIMITED
        assert "*:*:*" not in payload["permissions"]


class TestGetRouters:
    """``GET /getRouters`` —— bug #1 的现场."""

    def test_returns_the_menu_tree(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get("/getRouters", headers=admin_headers).json()

        assert payload["code"] == 200
        assert isinstance(payload["data"], list) and payload["data"]
        assert all("path" in node for node in payload["data"])

    def test_every_node_carries_a_boolean_hidden_and_a_meta_title(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        data = real_client.get("/getRouters", headers=admin_headers).json()["data"]

        def walk(nodes: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
            for node in nodes:
                yield node
                yield from walk(node.get("children") or [])

        nodes = list(walk(data))
        assert nodes
        for node in nodes:
            # Java: ``private boolean hidden`` —— primitive，NON_EMPTY 也不会省掉。
            assert isinstance(node["hidden"], bool)
            if node.get("meta"):
                assert isinstance(node["meta"].get("title"), str)

    def test_the_tree_is_nested_not_flat(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        data = real_client.get("/getRouters", headers=admin_headers).json()["data"]

        assert any(node.get("children") for node in data)


class TestMenuFlagsRegression:
    """bug #1 回归护栏：``int`` 列必须按 JDBC ``getString`` 转成 ``str``.

    真实库 ``sys_menu.is_frame`` / ``is_cache`` 是 ``int``，Java 实体声明 ``String``。
    MyBatis 的 ``resultMap`` 按属性类型选 ``StringTypeHandler`` -> ``rs.getString()``，
    所以拿到 ``"1"``。pydantic 不做隐式转换，最初直接 500。
    """

    def test_is_frame_and_is_cache_are_strings_from_the_database(self) -> None:
        from app.common.core.domain.entity.sys_menu import SysMenu
        from app.system.mapper.sys_menu_mapper import SysMenuMapper

        menus = SysMenuMapper().select_menu_list(SysMenu())
        assert menus, "sys_menu 为空？"

        for menu in menus:
            assert menu.is_frame is None or isinstance(menu.is_frame, str), (
                "menu_id=%s is_frame=%r（%s）—— 必须是字符串"
                % (menu.menu_id, menu.is_frame, type(menu.is_frame).__name__)
            )
            assert menu.is_cache is None or isinstance(menu.is_cache, str), (
                "menu_id=%s is_cache=%r（%s）—— 必须是字符串"
                % (menu.menu_id, menu.is_cache, type(menu.is_cache).__name__)
            )

    def test_the_raw_column_really_is_an_int(self) -> None:
        """这条断言的意义：一旦本库把列改成 ``varchar``，上面的护栏就该删掉."""
        column_type = _scalar(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'sys_menu' "
            "AND column_name = 'is_frame'"
        )
        assert column_type == "int"


# --------------------------------------------------------------------------- 分页列表

#: ``(路径, 期望 total 的 SQL)``。
#:
#: 只收录 **where 子句一眼可读** 的表 —— 把 mapper 的 SQL 抄进测试是同义反复，而一句
#: ``COUNT(*)`` 能真正校验"数据查询"和"count 查询"是同一套过滤条件。``sys_oper_log`` /
#: ``sys_logininfor`` 会随用例自己增长，所以走下面的结构断言，不钉数值。
EXACT_TOTALS: Tuple[Tuple[str, str], ...] = (
    ("/system/user/list", "SELECT COUNT(*) FROM sys_user WHERE del_flag = '0'"),
    ("/system/post/list", "SELECT COUNT(*) FROM sys_post"),
    ("/system/role/list", "SELECT COUNT(*) FROM sys_role WHERE del_flag = '0'"),
    ("/system/config/list", "SELECT COUNT(*) FROM sys_config"),
    ("/system/dict/type/list", "SELECT COUNT(*) FROM sys_dict_type"),
    ("/system/dict/data/list", "SELECT COUNT(*) FROM sys_dict_data"),
    ("/system/notice/list", "SELECT COUNT(*) FROM sys_notice"),
    ("/system/file/list", "SELECT COUNT(*) FROM sys_file"),
    ("/base/section/list", "SELECT COUNT(*) FROM ods_szdn_section"),
    ("/base/toll/list", "SELECT COUNT(*) FROM ods_szdn_toll"),
    ("/base/gantry/list", "SELECT COUNT(*) FROM ods_szdn_gantry"),
    ("/base/org/list", "SELECT COUNT(*) FROM ods_yhgl_v_base_org"),
    ("/base/location/list", "SELECT COUNT(*) FROM zdata_location_dict"),
    ("/base/fitting/list", "SELECT COUNT(*) FROM zdata_trail_fitting"),
)

#: 只做结构断言的分页端点（数据会变，或过滤条件是多表关联）。
STRUCTURAL_LISTS: Tuple[str, ...] = (
    "/system/indexmenu/list",
    "/monitor/operlog/list",
    "/monitor/logininfor/list",
    "/manager/carinfo/list",
    "/manager/exceptrecord/list",
    "/manager/suspicious/list",
    "/manager/carwarning/list",
    "/manager/aduitfree/list",
    "/manager/confimfree/list",
    "/flow/flowlist/list",
    "/flow/flowname/list",
    "/flow/applyinfo/listAll",
)


class TestPagedListsMatchTheDatabase:
    """``TableDataInfo`` 四个字段都得对，``total`` 必须等于库里的真实行数."""

    @pytest.mark.parametrize("path,sql", EXACT_TOTALS, ids=[item[0] for item in EXACT_TOTALS])
    def test_total_equals_the_row_count(
        self,
        real_client: TestClient,
        admin_headers: Dict[str, str],
        path: str,
        sql: str,
    ) -> None:
        payload = real_client.get(path, params={"pageNum": 1, "pageSize": 2}, headers=admin_headers).json()

        assert payload["code"] == 200, payload
        assert payload["msg"] == "查询成功"
        assert payload["total"] == _scalar(sql), "%s 的 total 与库里行数不一致" % path
        assert len(payload["rows"]) == min(2, payload["total"])

    @pytest.mark.parametrize("path", STRUCTURAL_LISTS)
    def test_the_envelope_is_well_formed(
        self, real_client: TestClient, admin_headers: Dict[str, str], path: str
    ) -> None:
        payload = real_client.get(path, params={"pageNum": 1, "pageSize": 2}, headers=admin_headers).json()

        assert payload["code"] == 200, payload
        assert isinstance(payload["total"], int)
        assert isinstance(payload["rows"], list)
        assert len(payload["rows"]) <= 2
        assert len(payload["rows"]) <= payload["total"]


class TestPaging:
    """第二页必须换一批主键 —— 分页真的推到了 SQL，而不是在内存里切."""

    @pytest.mark.parametrize(
        "path,id_field",
        (
            ("/system/user/list", "userId"),
            ("/base/gantry/list", "gantryCode"),
            ("/base/location/list", None),
        ),
    )
    def test_page_two_differs_from_page_one(
        self,
        real_client: TestClient,
        admin_headers: Dict[str, str],
        path: str,
        id_field: Optional[str],
    ) -> None:
        page_one = real_client.get(
            path, params={"pageNum": 1, "pageSize": 2}, headers=admin_headers
        ).json()
        page_two = real_client.get(
            path, params={"pageNum": 2, "pageSize": 2}, headers=admin_headers
        ).json()

        assert page_one["total"] == page_two["total"], "两次请求的 total 必须一致"
        assert page_one["rows"] != page_two["rows"], "第二页与第一页相同时分页没生效"
        if id_field is not None and page_one["rows"]:
            assert page_one["rows"][0][id_field] != page_two["rows"][0][id_field]

    def test_a_page_beyond_the_end_is_clamped_to_the_last_page(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """``reasonable=true`` 是 RuoYi 的**默认值**，越界页码会回退到最后一页.

        Java: ``PageDomain.reasonable = true`` -> ``PageHelper.startPage(...)
        .setReasonable(reasonable)``。所以最后一页不该是空的 —— 前端删光末页
        数据后不会看到空白页。

        ``sys_post`` 有 3 行、``pageSize=2`` -> 共 2 页，最后一页只剩 1 行；
        若页码没被回退，``LIMIT 19996, 2`` 会返回 0 行，这条断言就会失败。
        """
        total = _scalar("SELECT COUNT(*) FROM sys_post")
        assert total == 3, "这条用例依赖 sys_post 恰好 3 行，库里变了就换表"

        payload = real_client.get(
            "/system/post/list", params={"pageNum": 9999, "pageSize": 2}, headers=admin_headers
        ).json()

        assert payload["total"] == total
        assert len(payload["rows"]) == 1

    def test_without_reasonable_an_out_of_range_page_is_empty(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """显式 ``reasonable=false`` 时页码不被纠正 —— ``LIMIT`` 越过末尾，回空列表."""
        payload = real_client.get(
            "/system/post/list",
            params={"pageNum": 9999, "pageSize": 2, "reasonable": "false"},
            headers=admin_headers,
        ).json()

        assert payload["total"] == 3
        assert payload["rows"] == []

    def test_page_size_is_honoured(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        rows = real_client.get(
            "/system/dict/data/list", params={"pageNum": 1, "pageSize": 5}, headers=admin_headers
        ).json()["rows"]

        assert len(rows) == 5


class TestNonPagedLists:
    """没有 ``startPage()`` 的列表 —— ``AjaxResult`` 信封，``data`` 直接是数组."""

    @pytest.mark.parametrize(
        "path",
        (
            "/system/dept/list",
            "/system/menu/list",
            "/base/configServiceArea/listQuery",
        ),
    )
    def test_data_is_a_plain_array(
        self, real_client: TestClient, admin_headers: Dict[str, str], path: str
    ) -> None:
        payload = real_client.get(path, headers=admin_headers).json()

        assert payload["code"] == 200, payload
        assert isinstance(payload["data"], list)
        assert "rows" not in payload and "total" not in payload

    def test_the_dict_data_endpoint_returns_the_three_sex_options(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get("/system/dict/data/type/sys_user_sex", headers=admin_headers).json()

        assert payload["code"] == 200
        values = [row["dictValue"] for row in payload["data"]]
        assert values == ["0", "1", "2"]


# --------------------------------------------------------------------------- 大屏

class TestBigScreen:
    """``/manager/bigScreen/**`` —— 12 个 GET 全过一遍真实数据."""

    @pytest.mark.parametrize(
        "path",
        (
            "/manager/bigScreen/carStatistics",
            "/manager/bigScreen/sectionList",
            "/manager/bigScreen/orgList",
            "/manager/bigScreen/topTen",
            "/manager/bigScreen/carVoList",
            "/manager/bigScreen/incomeStatistic?type=1",
        ),
    )
    def test_list_payloads(self, real_client: TestClient, admin_headers: Dict[str, str], path: str) -> None:
        payload = real_client.get(path, headers=admin_headers).json()

        assert payload["code"] == 200, payload
        assert isinstance(payload["data"], list)

    def test_car_audit_returns_the_four_aggregates(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get(
            "/manager/bigScreen/carAudit", params={"type": 1}, headers=admin_headers
        ).json()

        assert payload["code"] == 200
        assert set(payload["data"]) == {
            "totalCount",
            "finishedCount",
            "totalAmount",
            "finishedAmount",
        }

    def test_except_record_list_is_paged(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get(
            "/manager/bigScreen/exceptRecordList",
            params={"pageNum": 1, "pageSize": 2},
            headers=admin_headers,
        ).json()

        assert payload["code"] == 200
        # mapper 的 where 里有 del_flag = '0'（软删除的行不计入）。
        assert payload["total"] == _scalar(
            "SELECT COUNT(*) FROM car_except_record WHERE del_flag = '0'"
        )
        assert len(payload["rows"]) == 2

    def test_section_list_is_not_shorter_than_the_base_table(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """大屏的分段列表按 ``car_info`` 去重，可能比路网表多，不能比它少."""
        data = real_client.get("/manager/bigScreen/sectionList", headers=admin_headers).json()["data"]

        assert len(data) >= 1


class TestBigScreenRegression:
    """bug #2 回归护栏：``get_car_statistics`` 里的惰性 import 包名写错过.

    原来的 ``from app.system.domain.sys_dict_data import SysDictData`` 指向一个不存在的
    模块 —— 因为它在函数体内，单元测试从没执行到，只有真打接口才会炸。
    """

    def test_the_escape_type_dictionary_resolves(self) -> None:
        from app.manager.service.car_confim_free_service import CarConfimFreeService

        rows = CarConfimFreeService().get_car_statistics(None)

        # 字典里有几种逃费类型就返回几条，SQL 没有的补 0。
        assert len(rows) == _scalar("SELECT COUNT(*) FROM sys_dict_data WHERE dict_type = 'escaped_type'")
        assert all(row.escaped_type_name for row in rows)


# --------------------------------------------------------------------------- 监控

class TestMonitor:
    """``/monitor/**`` —— 真实 Redis / 进程指标."""

    def test_online_users_reads_the_live_tokens(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        payload = real_client.get("/monitor/online/list", headers=admin_headers).json()

        assert payload["code"] == 200
        assert payload["total"] == len(get_redis_cache().keys(LOGIN_TOKEN_KEY + "*"))
        assert payload["total"] >= 1

    def test_server_reports_the_java_domain_sections(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """Java 的 ``Server`` 域对象正好这五块."""
        data = real_client.get("/monitor/server", headers=admin_headers).json()["data"]

        assert set(data) == {"cpu", "mem", "jvm", "sys", "sysFiles"}


class TestCacheMonitorRegression:
    """bug #3 回归护栏：``INFO`` 必须拿到**原始文本**再解析.

    ``redis-py`` 给 ``INFO`` 注册了 response callback，``execute_command("INFO")`` 回的是
    嵌套 dict，``parse_info`` 拿它 ``splitlines()`` 直接 ``AttributeError``。Java 的
    ``RedisCallback`` 走裸连接，拿到的是扁平 ``Properties`` 的原料。
    """

    def test_returns_the_three_sections(self, real_client: TestClient, admin_headers: Dict[str, str]) -> None:
        payload = real_client.get("/monitor/cache", headers=admin_headers).json()

        assert payload["code"] == 200, payload
        assert set(payload["data"]) == {"info", "dbSize", "commandStats"}

    def test_info_is_a_flat_map_of_strings(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """``Properties`` 是扁平的 ``key -> String``；嵌套 dict 就是 bug 复发了."""
        info = real_client.get("/monitor/cache", headers=admin_headers).json()["data"]["info"]

        assert isinstance(info, dict) and info
        assert all(isinstance(key, str) for key in info)
        assert all(isinstance(value, str) for value in info.values()), "info 出现非字符串值"
        assert "redis_version" in info
        # 段落注释行必须被丢掉，不能变成 "Server" 键。
        assert "Server" not in info and "# Server" not in info

    def test_db_size_matches_dbsize(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        data = real_client.get("/monitor/cache", headers=admin_headers).json()["data"]

        assert isinstance(data["dbSize"], int)
        assert data["dbSize"] == get_redis_cache().client.dbsize()

    def test_command_stats_is_a_pie_list_of_strings(
        self, real_client: TestClient, admin_headers: Dict[str, str]
    ) -> None:
        """``value`` 是 ``substringBetween("calls=", ",usec")`` 的结果 —— 字符串."""
        stats = real_client.get("/monitor/cache", headers=admin_headers).json()["data"]["commandStats"]

        assert isinstance(stats, list) and stats
        for item in stats:
            assert set(item) == {"name", "value"}
            assert isinstance(item["name"], str)
            assert not item["name"].startswith("cmdstat_")
            # Redis 8 的某些统计项没有 usec（例如 rejected_calls 才有的），此时 Java 也回 null。
            assert item["value"] is None or isinstance(item["value"], str)


# --------------------------------------------------------------------------- 权限

class TestAuthorization:
    """三层：匿名 401 / 无权限 403 / 有权限 200."""

    @pytest.mark.parametrize(
        "path",
        ("/system/user/list", "/getInfo", "/monitor/cache", "/manager/bigScreen/carStatistics"),
    )
    def test_anonymous_gets_the_401_envelope(self, real_client: TestClient, path: str) -> None:
        """RuoYi 的惯例：HTTP 永远是 200，业务码放在 ``code`` 里."""
        response = real_client.get(path)

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 401
        assert "认证失败" in payload["msg"]

    @pytest.mark.parametrize(
        "path",
        ("/system/dept/list", "/system/dict/type/list", "/monitor/operlog/list"),
    )
    def test_a_permissionless_account_gets_403(
        self, real_client: TestClient, limited_headers: Dict[str, str], path: str
    ) -> None:
        response = real_client.get(path, headers=limited_headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 403
        assert payload["msg"] == "没有权限，请联系管理员授权"

    @pytest.mark.parametrize(
        "path",
        ("/system/user/list", "/base/section/list", "/manager/carinfo/list"),
    )
    def test_login_only_endpoints_stay_open(
        self, real_client: TestClient, limited_headers: Dict[str, str], path: str
    ) -> None:
        """这些端点 Java 上**没有** ``@PreAuthorize`` —— 登录即可，别顺手加权限点."""
        payload = real_client.get(
            path, params={"pageNum": 1, "pageSize": 1}, headers=limited_headers
        ).json()

        assert payload["code"] == 200


# --------------------------------------------------------------------------- 登出

class TestLogout:
    """``POST /logout`` —— token 在 Redis 里必须被删掉."""

    def test_logout_deletes_the_token_key(
        self, tokens: Dict[str, str], real_client: TestClient
    ) -> None:
        # 单独登录一次，别把 session 级 token 弄失效。
        payload = _login(real_client, _ADMIN)
        token = payload[TOKEN]
        cache = get_redis_cache()
        key = LOGIN_TOKEN_KEY + _token_uuid(token)

        assert cache.has_key(key) is True

        logout = real_client.post("/logout", headers=_auth(token)).json()

        assert logout == {"code": 200, "msg": "退出成功"}
        assert cache.has_key(key) is False

    def test_the_token_stops_working_after_logout(
        self, tokens: Dict[str, str], real_client: TestClient
    ) -> None:
        token = _login(real_client, _ADMIN)[TOKEN]
        real_client.post("/logout", headers=_auth(token))

        payload = real_client.get("/getInfo", headers=_auth(token)).json()

        # token 里的 uuid 还在，但 Redis 里的 LoginUser 没了 -> 认证失败。
        assert payload["code"] == 401


# --------------------------------------------------------------------------- 环境事实

def test_upgrade_info_degrades_when_the_table_is_missing(
    real_client: TestClient, admin_headers: Dict[str, str]
) -> None:
    """本库没有 ``sys_upgrade_info`` —— 两侧都该是 HTTP 200 + ``code 500``.

    这不是迁移缺陷：Java 打同一个库会抛 ``BadSqlGrammarException``，走通用
    ``ExceptionHandler`` 得到同样的信封。表补上之后本用例自动改断言。
    """
    has_table = _table_exists("sys_upgrade_info")
    payload = real_client.get(
        "/system/upgradeInfo/list", params={"pageNum": 1, "pageSize": 2}, headers=admin_headers
    ).json()

    if has_table:
        assert payload["code"] == 200
        assert payload["total"] == _scalar("SELECT COUNT(*) FROM sys_upgrade_info")
        return

    assert payload["code"] == 500
    assert "sys_upgrade_info" in payload["msg"]
