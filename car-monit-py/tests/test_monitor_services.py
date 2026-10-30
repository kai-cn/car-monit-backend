"""monitor 包三个 service 的装配层 —— 纯转发 + 单例定位.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/.../service/impl/{SysOperLogServiceImpl,SysLogininforServiceImpl,
#                                 SysUserOnlineServiceImpl}.java

三个 service 在 Java 里都**没有业务逻辑**
-----------------------------------------
``SysOperLogServiceImpl`` 与 ``SysLogininforServiceImpl`` 的每个方法都是
``return xxxMapper.yyy(...);`` 一行；``SysUserOnlineServiceImpl`` 的三段 ``if`` 已经有
``tests/test_sys_user_online_controller.py`` 覆盖。所以这里只钉三件容易在重构中被
"顺手改掉"的事：

1. **参数与返回值原样穿透** —— 包括 ``insertOperlog`` 的 Java 签名是 ``void``，
   本工程为了断言把它写成 ``-> int``（见 ``sys_oper_log_service`` 的模块 docstring）；
2. **不吞异常** —— Java 没有 ``try/catch``，异常直接冒到 ``GlobalExceptionHandler``；
3. **单例与重置** —— ``@Autowired`` 的 Spring 默认单例语义，对应
   ``get_*_service()`` / ``reset_*_service()`` 这对函数。
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

import pytest

from app.common.core.redis.redis_cache import RedisCache
from app.system.domain.sys_logininfor import SysLogininfor
from app.system.domain.sys_oper_log import SysOperLog
from app.system.service import sys_logininfor_service as logininfor_module
from app.system.service import sys_oper_log_service as oper_log_module
from app.system.service import sys_user_online_service as user_online_module
from app.system.service.sys_logininfor_service import (
    SysLogininforService,
    get_logininfor_service,
    reset_logininfor_service,
)
from app.system.service.sys_oper_log_service import (
    SysOperLogService,
    get_oper_log_service,
    reset_oper_log_service,
)
from app.system.service.sys_user_online_service import (
    SysUserOnlineService,
    get_user_online_service,
    reset_user_online_service,
)


# --------------------------------------------------------------------------- fakes


class _RecordingMapper:
    """记录调用并回放预设结果；``raises`` 非空时抛它."""

    def __init__(self, result: Any = 1, raises: Optional[BaseException] = None) -> None:
        self.calls: List[Tuple[str, Tuple[Any, ...]]] = []
        self.result = result
        self.raises = raises

    def _record(self, name: str, *args: Any) -> Any:
        self.calls.append((name, args))
        if self.raises is not None:
            raise self.raises
        return self.result

    # --- SysOperLogMapper
    def insert_operlog(self, oper_log: SysOperLog) -> int:
        return self._record("insert_operlog", oper_log)

    def select_oper_log_list(self, oper_log: SysOperLog) -> List[SysOperLog]:
        return self._record("select_oper_log_list", oper_log)

    def delete_oper_log_by_ids(self, oper_ids: List[int]) -> int:
        return self._record("delete_oper_log_by_ids", oper_ids)

    def select_oper_log_by_id(self, oper_id: int) -> Optional[SysOperLog]:
        return self._record("select_oper_log_by_id", oper_id)

    def clean_oper_log(self) -> None:
        self._record("clean_oper_log")

    # --- SysLogininforMapper
    def insert_logininfor(self, logininfor: SysLogininfor) -> int:
        return self._record("insert_logininfor", logininfor)

    def select_logininfor_list(self, logininfor: SysLogininfor) -> List[SysLogininfor]:
        return self._record("select_logininfor_list", logininfor)

    def delete_logininfor_by_ids(self, info_ids: List[int]) -> int:
        return self._record("delete_logininfor_by_ids", info_ids)

    def clean_logininfor(self) -> None:
        self._record("clean_logininfor")


@pytest.fixture(autouse=True)
def _reset_locators() -> Any:
    """每个用例都从"没有单例"开始，避免互相污染."""
    reset_oper_log_service()
    reset_logininfor_service()
    reset_user_online_service()
    yield
    reset_oper_log_service()
    reset_logininfor_service()
    reset_user_online_service()


# --------------------------------------------------------------------------- operlog


class TestOperLogService:
    def test_insert_forwards_and_returns_the_row_count(self) -> None:
        mapper = _RecordingMapper(result=1)
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]
        oper_log = SysOperLog(title="用户管理")

        assert service.insert_operlog(oper_log) == 1
        assert mapper.calls == [("insert_operlog", (oper_log,))]

    def test_insert_returns_what_the_mapper_returns(self) -> None:
        """Java 签名是 ``void``；保留返回值只是本工程便于断言的便利，不能改成常量."""
        mapper = _RecordingMapper(result=7)
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]
        assert service.insert_operlog(SysOperLog()) == 7

    def test_list_forwards_the_same_entity_instance(self) -> None:
        mapper = _RecordingMapper(result=[])
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]
        oper_log = SysOperLog(title="登录")

        assert service.select_oper_log_list(oper_log) == []
        assert mapper.calls[0][1][0] is oper_log

    def test_delete_forwards_the_id_list_untouched(self) -> None:
        mapper = _RecordingMapper(result=2)
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]

        assert service.delete_oper_log_by_ids([3, 4]) == 2
        assert mapper.calls == [("delete_oper_log_by_ids", ([3, 4],))]

    def test_select_by_id_is_kept_even_without_a_call_site(self) -> None:
        """``SysOperlogController`` 没有 ``/{operId}`` 详情接口 —— 死代码照搬（原则 4）."""
        mapper = _RecordingMapper(result=None)
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]

        assert service.select_oper_log_by_id(9) is None
        assert mapper.calls == [("select_oper_log_by_id", (9,))]

    def test_clean_calls_the_mapper_once_and_returns_none(self) -> None:
        """``truncate`` 没有影响行数可看 —— Java 的 ``void cleanOperLog()`` 同理."""
        mapper = _RecordingMapper(result=None)
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]

        assert service.clean_oper_log() is None
        assert mapper.calls == [("clean_oper_log", ())]

    def test_an_exception_is_not_swallowed(self) -> None:
        mapper = _RecordingMapper(raises=RuntimeError("db down"))
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError):
            service.select_oper_log_list(SysOperLog())

    def test_the_mapper_is_exposed_read_only(self) -> None:
        mapper = _RecordingMapper()
        service = SysOperLogService(mapper=mapper)  # type: ignore[arg-type]
        assert service.mapper is mapper


class TestOperLogLocator:
    def test_the_default_service_builds_a_real_mapper(self) -> None:
        assert isinstance(get_oper_log_service().mapper, oper_log_module.SysOperLogMapper)

    def test_the_locator_is_a_singleton(self) -> None:
        """Java: ``@Autowired ISysOperLogService`` -> Spring 默认单例."""
        assert get_oper_log_service() is get_oper_log_service()

    def test_reset_drops_the_cached_instance(self) -> None:
        first = get_oper_log_service()
        reset_oper_log_service()

        assert get_oper_log_service() is not first


# --------------------------------------------------------------------------- logininfor


class TestLogininforService:
    def test_insert_forwards_and_returns_the_row_count(self) -> None:
        mapper = _RecordingMapper(result=1)
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]
        info = SysLogininfor(user_name="admin", status="0")

        assert service.insert_logininfor(info) == 1
        assert mapper.calls == [("insert_logininfor", (info,))]

    def test_list_forwards_the_same_entity_instance(self) -> None:
        mapper = _RecordingMapper(result=[])
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]
        info = SysLogininfor(ipaddr="127.0.0.1")

        assert service.select_logininfor_list(info) == []
        assert mapper.calls[0][1][0] is info

    def test_delete_forwards_the_id_list_untouched(self) -> None:
        mapper = _RecordingMapper(result=2)
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]

        assert service.delete_logininfor_by_ids([8, 9]) == 2
        assert mapper.calls == [("delete_logininfor_by_ids", ([8, 9],))]

    def test_clean_calls_the_mapper_once_and_returns_none(self) -> None:
        mapper = _RecordingMapper(result=None)
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]

        assert service.clean_logininfor() is None
        assert mapper.calls == [("clean_logininfor", ())]

    def test_an_exception_is_not_swallowed(self) -> None:
        mapper = _RecordingMapper(raises=RuntimeError("truncate denied"))
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError):
            service.clean_logininfor()

    def test_the_mapper_is_exposed_read_only(self) -> None:
        mapper = _RecordingMapper()
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]
        assert service.mapper is mapper

    def test_there_is_no_transaction_wrapper(self) -> None:
        """Java 的 ``SysLogininforServiceImpl`` 也**没有** ``@Transactional``."""
        mapper = _RecordingMapper(result=1)
        service = SysLogininforService(mapper=mapper)  # type: ignore[arg-type]

        service.insert_logininfor(SysLogininfor())
        service.clean_logininfor()

        # 两次调用各自独立穿透，中间没有任何 begin/commit 痕迹
        assert [name for name, _ in mapper.calls] == ["insert_logininfor", "clean_logininfor"]


class TestLogininforLocator:
    def test_the_default_service_builds_a_real_mapper(self) -> None:
        assert isinstance(
            get_logininfor_service().mapper, logininfor_module.SysLogininforMapper
        )

    def test_the_locator_is_a_singleton(self) -> None:
        assert get_logininfor_service() is get_logininfor_service()

    def test_reset_drops_the_cached_instance(self) -> None:
        first = get_logininfor_service()
        reset_logininfor_service()

        assert get_logininfor_service() is not first


# --------------------------------------------------------------------------- online


class TestUserOnlineServiceWiring:
    def test_an_injected_cache_is_used_as_is(self) -> None:
        cache = _RecordingMapper()  # 结构无关，只要是同一个对象
        service = SysUserOnlineService(redis_cache=cache)  # type: ignore[arg-type]
        assert service.redis_cache is cache

    def test_the_cache_is_resolved_lazily(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java: ``@Autowired private RedisCache redisCache``；这里是惰性取单例."""
        sentinel = RedisCache(client=object())  # 不会连接（只塞一个假 client）
        monkeypatch.setattr(user_online_module, "get_redis_cache", lambda: sentinel)

        service = SysUserOnlineService()
        assert service.redis_cache is sentinel

    def test_the_locator_is_a_singleton(self) -> None:
        assert get_user_online_service() is get_user_online_service()

    def test_reset_drops_the_cached_instance(self) -> None:
        first = get_user_online_service()
        reset_user_online_service()

        assert get_user_online_service() is not first

    def test_the_locator_does_not_connect_to_redis_at_import_time(self) -> None:
        """单例创建时不能连 Redis —— 本工程允许"没有 Redis 也能启动"."""
        service = get_user_online_service()
        assert service._redis_cache is None  # noqa: SLF001 - 故意检查内部状态


# --------------------------------------------------------------------------- 模块导出


class TestModuleExports:
    """三个模块各自声明 ``__all__``（包 ``__init__`` 刻意不聚合，见其 docstring）."""

    def test_oper_log_module_exports_the_pair(self) -> None:
        assert set(oper_log_module.__all__) == {
            "SysOperLogService",
            "get_oper_log_service",
            "reset_oper_log_service",
        }

    def test_logininfor_module_exports_the_pair(self) -> None:
        assert set(logininfor_module.__all__) == {
            "SysLogininforService",
            "get_logininfor_service",
            "reset_logininfor_service",
        }

    def test_user_online_module_exports_the_pair(self) -> None:
        assert set(user_online_module.__all__) == {
            "SysUserOnlineService",
            "get_user_online_service",
            "reset_user_online_service",
        }
