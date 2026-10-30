"""``RepeatSubmitInterceptor`` / ``SameUrlDataInterceptor`` —— 防重复提交.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java
#   ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/impl/SameUrlDataInterceptor.java
#   ruoyi-common/src/main/java/com/ruoyi/common/annotation/RepeatSubmit.java
#   ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java#add

这一层测什么
------------
Java 里拦截器挂在 ``/**``，靠 ``method.getAnnotation(RepeatSubmit.class)`` 决定是否生效；
全项目只有 ``SysConfigController#add`` 一个方法带这个注解。Python 侧改成
``dependencies=[Depends(repeat_submit())]``，可观察行为必须一致：

* 判重键 = ``REPEAT_SUBMIT_KEY + requestURI + trim(token.header)`` —— 换一个
  ``Authorization`` 就是另一条记录，互不影响；
* 判重值 = ``{requestURI: {"repeatParams": <params>, "repeatTime": <millis>}}``，
  TTL = ``annotation.interval()`` 毫秒（默认 5000）；
* ``repeatParams``：JSON 请求取**原始 body 字符串**，其它请求取
  ``JSON.toJSONString(getParameterMap())``（值是**数组**）；两者都是字符串比较；
* 时间比较是 ``(now - last) < interval``，**严格小于**且不防时钟回拨 —— 照抄；
* 被拦下时响应 HTTP 200 + ``{"code":500,"msg":"不允许重复提交，请稍候再试"}``，
  业务方法不执行、也**不写** ``sys_oper_log``（``@log`` 环绕通知不会触发）。

夹具
----
``tests/conftest.py`` 里的 autouse 夹具 ``repeat_submit_redis`` 给拦截器装内存 Redis
并清掉进程内单例；本文件直接用它，同时保留"缓存里到底写了什么"的断言能力。

本工程的测试没有装 ``pytest-asyncio``，所以 ``async`` 用例一律用 :func:`_await` 驱动。
"""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine, Dict, List, Optional, Set

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.system import sys_config_controller as controller
from app.common.annotation.repeat_submit import RepeatSubmit
from app.common.constant.cache_constants import REPEAT_SUBMIT_KEY
from app.common.core.context.request_context import clear_request, set_request
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.config.exception_handlers import register_exception_handlers
from app.framework.aspectj import log_aspect
from app.framework.interceptor import repeat_submit_interceptor as base
from app.framework.interceptor.impl import same_url_data_interceptor as implementation
from app.framework.interceptor.impl.same_url_data_interceptor import (
    REPEAT_PARAMS,
    REPEAT_TIME,
    SameUrlDataInterceptor,
)
from app.framework.interceptor.repeat_submit_interceptor import (
    RepeatSubmitException,
    get_interceptor,
    repeat_submit,
    reset_interceptor,
)
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_config import SysConfig

#: 拦截器写入 Redis 时用的 key 前缀（Java: ``CacheConstants.REPEAT_SUBMIT_KEY``）。
KEY_PREFIX = REPEAT_SUBMIT_KEY

AUTH = {"Authorization": "Bearer token-A"}
JSON = {"Content-Type": "application/json;charset=UTF-8"}

URL = "/system/config"


def _await(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """驱动一个协程（等价于 JUnit 里同步调用被测方法）."""
    return asyncio.run(coroutine)


# --------------------------------------------------------------------------- 请求替身


def make_request(
    method: str = "POST",
    path: str = URL,
    query: str = "",
    headers: Optional[Dict[str, str]] = None,
    body: bytes = b"",
) -> Request:
    """构造一个最小的 Starlette ``Request``（等价于 MockHttpServletRequest）.

    ``receive`` 是必需的：``request.body()`` / ``request.form()`` 都从它读。
    """
    raw = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    sent = False

    async def receive() -> Dict[str, Any]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": path.split("?", 1)[0],
            "raw_path": path.split("?", 1)[0].encode("latin-1"),
            "query_string": query.encode("latin-1"),
            "root_path": "",
            "headers": raw,
            "client": ("127.0.0.1", 54321),
            "server": ("127.0.0.1", 9989),
        },
        receive,
    )


@pytest.fixture
def interceptor(repeat_submit_redis: Any) -> SameUrlDataInterceptor:
    return SameUrlDataInterceptor()


def is_repeat(
    interceptor: SameUrlDataInterceptor,
    request: Request,
    annotation: Optional[RepeatSubmit] = None,
) -> bool:
    """Java: ``interceptor.isRepeatSubmit(request, annotation)``."""
    return _await(interceptor.is_repeat_submit(request, annotation or RepeatSubmit()))


def cached_params(repeat_submit_redis: Any) -> Any:
    """取最后一次写入的 ``repeatParams``."""
    return repeat_submit_redis.writes[-1][1][URL][REPEAT_PARAMS]


# --------------------------------------------------------------------------- 注解默认值


class TestRepeatSubmitAnnotation:
    def test_the_defaults_match_java(self) -> None:
        """Java: ``int interval() default 5000; String message() default "不允许重复提交，请稍候再试"``."""
        annotation = RepeatSubmit()

        assert annotation.interval == 5000
        assert annotation.message == "不允许重复提交，请稍候再试"

    def test_it_is_immutable(self) -> None:
        """注解是编译期元数据，不该被运行时修改。"""
        annotation = RepeatSubmit()

        with pytest.raises(Exception):
            annotation.interval = 1  # type: ignore[misc]


# --------------------------------------------------------------------------- 判定规则


class TestSameUrlData:
    def test_the_first_submit_is_allowed(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        request = make_request(headers={**AUTH, **JSON}, body=b'{"a":1}')

        assert is_repeat(interceptor, request) is False

        key = KEY_PREFIX + URL + "Bearer token-A"
        assert repeat_submit_redis.data[key][1] == 5000  # TTL 按毫秒写

    def test_the_cache_shape_matches_java(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """``{requestURI: {"repeatParams": <body>, "repeatTime": <millis>}}``."""
        request = make_request(headers={**AUTH, **JSON}, body=b'{"a":1}')

        is_repeat(interceptor, request)

        (key, value, ttl) = repeat_submit_redis.writes[0]
        assert key == KEY_PREFIX + URL + "Bearer token-A"
        assert ttl == 5000
        assert set(value) == {URL}
        assert value[URL][REPEAT_PARAMS] == '{"a":1}'
        assert isinstance(value[URL][REPEAT_TIME], int)

    def test_an_identical_body_within_the_interval_is_blocked(
        self, interceptor: SameUrlDataInterceptor
    ) -> None:
        annotation = RepeatSubmit()

        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=b'{"a":1}'), annotation) is False
        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=b'{"a":1}'), annotation) is True

    def test_a_different_body_is_allowed(self, interceptor: SameUrlDataInterceptor) -> None:
        annotation = RepeatSubmit()

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=b'{"a":1}'), annotation)

        assert is_repeat(
            interceptor, make_request(headers={**AUTH, **JSON}, body=b'{"a":2}'), annotation
        ) is False

    def test_the_body_is_compared_as_a_raw_string(
        self, interceptor: SameUrlDataInterceptor
    ) -> None:
        """``{"a":1}`` 与 ``{ "a":1 }`` 是两份不同的字符串 -> **不算**重复提交.

        Java 就是 ``StringUtils.equals`` 比 ``repeatParams``，不去解析 JSON。
        """
        annotation = RepeatSubmit()

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=b'{"a":1}'), annotation)

        assert is_repeat(
            interceptor, make_request(headers={**AUTH, **JSON}, body=b'{ "a":1 }'), annotation
        ) is False

    def test_a_different_token_is_a_different_submission(
        self, interceptor: SameUrlDataInterceptor
    ) -> None:
        """登出再登录（换 token）不该被上一次的提交挡住。"""
        annotation = RepeatSubmit()
        body = b'{"a":1}'

        is_repeat(interceptor, make_request(headers={"Authorization": "Bearer A", **JSON}, body=body), annotation)

        assert is_repeat(
            interceptor, make_request(headers={"Authorization": "Bearer B", **JSON}, body=body), annotation
        ) is False

    def test_a_missing_token_still_produces_a_key(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """``trimToEmpty(header(token.header))`` —— 没有消息头就当空串，键仍然成立。"""
        annotation = RepeatSubmit()
        body = b'{"a":1}'

        assert is_repeat(interceptor, make_request(headers=JSON, body=body), annotation) is False
        assert is_repeat(interceptor, make_request(headers=JSON, body=body), annotation) is True

        assert repeat_submit_redis.writes[-1][0] == KEY_PREFIX + URL

    def test_the_token_is_trimmed(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """Java: ``StringUtils.trimToEmpty(...)``."""
        is_repeat(interceptor, make_request(headers={"Authorization": "  Bearer A  ", **JSON}, body=b"{}"))

        assert repeat_submit_redis.writes[0][0] == KEY_PREFIX + URL + "Bearer A"

    def test_the_query_string_is_not_part_of_the_key(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """``getRequestURI()`` 不含 query。"""
        is_repeat(interceptor, make_request(query="?debug=1", headers={**AUTH, **JSON}, body=b"{}"))

        assert repeat_submit_redis.writes[0][0] == KEY_PREFIX + URL + "Bearer token-A"

    def test_the_interval_boundary_is_exclusive(
        self, interceptor: SameUrlDataInterceptor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``(time1 - time2) < interval`` —— 正好等于 5000ms 时**放行**."""
        annotation = RepeatSubmit()
        body = b'{"a":1}'
        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_000_000)

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation)

        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_005_000)
        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation) is False

    def test_one_millisecond_earlier_is_still_a_duplicate(
        self, interceptor: SameUrlDataInterceptor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        annotation = RepeatSubmit()
        body = b'{"a":1}'
        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_000_000)

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation)

        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_004_999)
        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation) is True

    def test_clock_skew_counts_as_a_duplicate(
        self, interceptor: SameUrlDataInterceptor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """时钟回拨时 ``time1 - time2`` 为负，Java 反而永远判"重复". 照抄这个瑕疵."""
        annotation = RepeatSubmit()
        body = b'{"a":1}'
        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_000_000)

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation)

        monkeypatch.setattr(implementation, "_now_millis", lambda: 1)
        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation) is True

    def test_a_custom_interval_extends_the_window(
        self,
        interceptor: SameUrlDataInterceptor,
        monkeypatch: pytest.MonkeyPatch,
        repeat_submit_redis: Any,
    ) -> None:
        annotation = RepeatSubmit(interval=50_000)
        body = b'{"a":1}'
        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_000_000)

        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation)

        assert repeat_submit_redis.writes[0][2] == 50_000
        monkeypatch.setattr(implementation, "_now_millis", lambda: 1_040_000)
        assert is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=body), annotation) is True

    def test_another_token_does_not_overwrite_the_previous_record(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """key 里有 token，两个用户各存各的。"""
        body = b'{"a":1}'

        is_repeat(interceptor, make_request(headers={"Authorization": "A", **JSON}, body=body))
        is_repeat(interceptor, make_request(headers={"Authorization": "B", **JSON}, body=body))

        assert len(repeat_submit_redis.data) == 2


# --------------------------------------------------------------------------- 参数表分支


class TestParameterMapBranch:
    def test_a_json_body_is_used_verbatim(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """``RepeatableFilter`` 只包装 ``application/json`` -> 直接读 body。"""
        raw = '{"configName":"皮肤"}'
        is_repeat(interceptor, make_request(headers={**AUTH, **JSON}, body=raw.encode("utf-8")))

        assert cached_params(repeat_submit_redis) == raw

    def test_a_non_json_body_falls_back_to_the_parameter_map(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """表单字段按 ``getParameterMap()`` 序列化 —— 值是**数组**。"""
        headers = {**AUTH, "Content-Type": "application/x-www-form-urlencoded"}
        is_repeat(interceptor, make_request(headers=headers, body=b"a=1&b=2"))

        assert cached_params(repeat_submit_redis) == '{"a":["1"],"b":["2"]}'

    def test_query_parameters_are_included_too(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        is_repeat(
            interceptor,
            make_request(query="a=1", headers={**AUTH, "Content-Type": "text/plain"}, body=b"x"),
        )

        assert cached_params(repeat_submit_redis) == '{"a":["1"]}'

    def test_a_repeated_query_parameter_becomes_a_two_element_array(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        is_repeat(
            interceptor,
            make_request(query="a=1&a=2", headers={**AUTH, "Content-Type": "text/plain"}, body=b"x"),
        )

        assert cached_params(repeat_submit_redis) == '{"a":["1","2"]}'

    def test_an_empty_body_and_no_parameters_is_an_empty_object(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        annotation = RepeatSubmit()

        assert is_repeat(interceptor, make_request(headers=AUTH), annotation) is False
        assert is_repeat(interceptor, make_request(headers=AUTH), annotation) is True

        assert cached_params(repeat_submit_redis) == "{}"

    def test_query_comes_before_form_for_the_same_key(
        self, interceptor: SameUrlDataInterceptor, repeat_submit_redis: Any
    ) -> None:
        """先 query 后 form，键相同时 form 追加在后面（与 ``getParameterMap`` 一致）。"""
        headers = {**AUTH, "Content-Type": "application/x-www-form-urlencoded"}
        is_repeat(interceptor, make_request(query="a=1", headers=headers, body=b"a=2"))

        assert cached_params(repeat_submit_redis) == '{"a":["1","2"]}'

    def test_a_broken_utf8_body_does_not_blow_up(
        self, interceptor: SameUrlDataInterceptor
    ) -> None:
        """Java 读字符流时坏字节会变替换字符；这里用 ``errors="replace"``，不能让请求 500。"""
        request = make_request(headers={**AUTH, **JSON}, body=b'{"a":"\xff"}')

        assert is_repeat(interceptor, request) is False


# --------------------------------------------------------------------------- 依赖工厂


class _Allows:
    def __init__(self) -> None:
        self.seen: List[Any] = []

    async def is_repeat_submit(self, request: Any, annotation: Any) -> bool:
        self.seen.append(annotation)
        return False


class _AlwaysDuplicate:
    def __init__(self) -> None:
        self.seen: List[Any] = []

    async def is_repeat_submit(self, request: Any, annotation: Any) -> bool:
        self.seen.append(annotation)
        return True


class TestRepeatSubmitFactory:
    def test_a_duplicate_raises_with_the_annotation_message(self) -> None:
        fake = _AlwaysDuplicate()
        guard = repeat_submit(RepeatSubmit(message="别点两下"), interceptor=fake)  # type: ignore[arg-type]

        with pytest.raises(RepeatSubmitException) as raised:
            _await(guard(make_request()))

        assert raised.value.message == "别点两下"
        assert fake.seen[0].message == "别点两下"

    def test_the_default_annotation_is_a_plain_repeat_submit(self) -> None:
        """``@RepeatSubmit``（无参数）就是 ``interval=5000`` + 默认文案。"""
        fake = _Allows()

        _await(repeat_submit(interceptor=fake)(make_request()))  # type: ignore[arg-type]

        assert fake.seen == [RepeatSubmit()]

    def test_a_pass_returns_none(self) -> None:
        guard = repeat_submit(interceptor=_Allows())  # type: ignore[arg-type]

        assert _await(guard(make_request())) is None

    def test_the_impl_is_a_process_wide_singleton(self) -> None:
        """Java: ``@Component`` 单例 bean。两条路由共用同一个实现（同一片 Redis 键空间）。"""
        reset_interceptor()
        try:
            first = get_interceptor()
            assert get_interceptor() is first
            assert isinstance(first, SameUrlDataInterceptor)

            reset_interceptor()
            assert get_interceptor() is not first
        finally:
            reset_interceptor()

    def test_both_modules_expose_the_same_object(self) -> None:
        """``app.framework.interceptor`` 与 ``...repeat_submit_interceptor`` 是同一批对象。"""
        assert base.get_interceptor is get_interceptor
        assert base.RepeatSubmitException is RepeatSubmitException


# --------------------------------------------------------------------------- HTTP 端到端


class _FakeConfigService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []

    def check_config_key_unique(self, config: SysConfig) -> str:
        self.calls.append(("check_config_key_unique",))
        return "0"

    def insert_config(self, config: SysConfig) -> int:
        self.calls.append(("insert_config", config.model_copy(deep=True)))
        return 1

    def update_config(self, config: SysConfig) -> int:
        self.calls.append(("update_config", config.model_copy(deep=True)))
        return 1

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _RecordingAsyncManager:
    """替掉 ``AsyncManager``：把审计任务记录下来而不进线程池."""

    rows: List[Any] = []

    @classmethod
    def me(cls) -> "_RecordingAsyncManager":
        return cls()

    def execute(self, task: Any) -> None:
        type(self).rows.append(task)


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    fake = _FakeConfigService()
    monkeypatch.setattr(controller, "_CONFIG_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_request()
    controller.reset_config_controller()


@pytest.fixture
def audit(monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    rows: List[Any] = []
    monkeypatch.setattr(log_aspect, "AsyncManager", _RecordingAsyncManager)
    _RecordingAsyncManager.rows = rows
    return rows


def _build_app(permissions: Optional[Set[str]] = None) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    granted = {"*:*:*"} if permissions is None else permissions

    @application.middleware("http")
    async def _fake_jwt(request: Any, call_next: Any) -> Any:
        user = SysUser(user_id=2, user_name="ry")
        SecurityContextHolder.get_context().set_authentication(
            UsernamePasswordAuthenticationToken(
                LoginUser(user=user, permissions=granted), None, []
            )
        )
        # 等价于 ``RequestContextMiddleware``：``log_aspect`` 靠它取 ``ServletUtils.getRequest()``。
        set_request(request)
        return await call_next(request)

    application.include_router(controller.router)
    return application


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app())


@pytest.fixture
def http_without_permission() -> Any:
    return TestClient(_build_app(permissions=set()))


VALID_BODY: Dict[str, Any] = {
    "configName": "主框架页-默认皮肤样式名称",
    "configKey": "sys.index.skinName",
    "configValue": "skin-blue",
    "configType": "Y",
}


class TestOverHttp:
    def test_a_duplicate_post_returns_code_500_with_http_200(
        self, http: TestClient, service: Any
    ) -> None:
        first = http.post(URL, json=VALID_BODY)
        second = http.post(URL, json=VALID_BODY)

        assert first.status_code == 200
        assert first.json() == {"code": 200, "msg": "操作成功"}
        assert second.status_code == 200
        assert second.json() == {"code": 500, "msg": "不允许重复提交，请稍候再试"}

    def test_the_endpoint_runs_only_once(self, http: TestClient, service: Any) -> None:
        http.post(URL, json=VALID_BODY)
        http.post(URL, json=VALID_BODY)

        assert len(service.of("insert_config")) == 1

    def test_the_rejected_call_writes_no_audit_row(
        self, http: TestClient, service: Any, audit: List[Any]
    ) -> None:
        """``@log`` 在端点函数上，依赖阶段抛异常时它根本没被调用 —— 与 Java 的环绕通知一致。"""
        http.post(URL, json=VALID_BODY)
        http.post(URL, json=VALID_BODY)

        assert len(audit) == 1

    def test_a_different_body_is_accepted(self, http: TestClient, service: Any) -> None:
        http.post(URL, json=VALID_BODY)

        response = http.post(URL, json=dict(VALID_BODY, configKey="sys.other.key"))

        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert len(service.of("insert_config")) == 2

    def test_a_duplicate_beats_validation(self, http: TestClient, service: Any) -> None:
        """拦截器在请求体校验**之前**（Spring 的 ``preHandle`` 也在反序列化之前）.

        第一次空 body 被拦在校验上，第二次同样的空 body 直接判"重复提交"。
        """
        first = http.post(URL, json={})
        second = http.post(URL, json={})

        assert first.json() == {"code": 500, "msg": "参数名称不能为空"}
        assert second.json() == {"code": 500, "msg": "不允许重复提交，请稍候再试"}
        assert service.of("insert_config") == []

    def test_a_duplicate_beats_the_permission_check(
        self, http: TestClient, http_without_permission: TestClient, service: Any
    ) -> None:
        """拦截器先于 ``@PreAuthorize``：先存一条，再用无权限身份复现同一次提交。"""
        assert http.post(URL, json=VALID_BODY).json() == {"code": 200, "msg": "操作成功"}

        response = http_without_permission.post(URL, json=VALID_BODY)

        assert response.json() == {"code": 500, "msg": "不允许重复提交，请稍候再试"}
        assert len(service.of("insert_config")) == 1

    def test_a_non_duplicate_still_hits_the_permission_check(
        self, http_without_permission: TestClient, service: Any
    ) -> None:
        """顺序断言的反面：没被拦下时，``@PreAuthorize`` 照常生效。"""
        response = http_without_permission.post(URL, json=VALID_BODY)

        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}
        assert service.of("insert_config") == []

    def test_the_cache_ttl_is_the_annotation_interval(
        self, http: TestClient, service: Any, repeat_submit_redis: Any
    ) -> None:
        http.post(URL, json=VALID_BODY)

        assert [ttl for (_, _, ttl) in repeat_submit_redis.writes] == [5000]

    def test_the_key_is_the_url_plus_the_bearer_token(
        self, http: TestClient, service: Any, repeat_submit_redis: Any
    ) -> None:
        http.post(URL, json=VALID_BODY, headers=AUTH)

        assert repeat_submit_redis.writes[0][0] == KEY_PREFIX + URL + "Bearer token-A"

    def test_other_routes_are_untouched(self, http: TestClient, service: Any) -> None:
        """只有 ``add`` 带 ``@RepeatSubmit``；``edit``（PUT）连发两次都放行。"""
        body = dict(VALID_BODY, configId=1)

        http.put(URL, json=body)
        response = http.put(URL, json=body)

        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert len(service.of("update_config")) == 2
