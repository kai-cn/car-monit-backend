"""``SysConfigService`` -- 缓存契约与内置参数保护.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysConfigServiceImpl.java

被钉住的五个点
--------------
1. **逐键维护 vs 全清**：``insert`` / ``update`` 只写自己那个键；``delete`` /
   ``clearCache`` 才 ``keys("sys_config:*")`` 全清。写成"增改也全清"不会报错，
   但会让别的键多一次回源（性能差异，行为看不出来）。
2. ``selectConfigByKey`` 的"空即未命中"用的是 RuoYi 会 **trim** 的 ``isNotEmpty``，
   所以缓存里存了 ``"  "`` 也会回源。
3. ``deleteConfigByIds`` 只拦 ``config_type == "Y"``，且文案**末尾有一个空格**。
4. 删除/清缓存都是 ``KEYS`` 全表扫描（O(N) 阻塞），照抄不改成 ``SCAN``。
5. ``getCacheKey(null)`` 得到 ``"sys_config:null"`` —— Java 的字符串拼接把
   ``null`` 变成 ``"null"``，Python 的 ``+`` 会抛错，必须显式复刻。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from app.common.exception.exceptions import CustomException
from app.system.domain.sys_config import SysConfig
from app.system.service import sys_config_service as service_module
from app.system.service.sys_config_service import (
    SysConfigService,
    get_config_service,
    reset_config_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeConfigMapper:
    def __init__(self) -> None:
        self.by_id: Dict[int, SysConfig] = {}
        self.by_key: Dict[str, SysConfig] = {}
        self.rows: List[SysConfig] = []
        self.check_result: Optional[SysConfig] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.calls: List[str] = []
        self.check_keys: List[Optional[str]] = []
        self.list_arguments: List[SysConfig] = []

    def select_config(self, config: SysConfig) -> Optional[SysConfig]:
        self.calls.append("select_config")
        if config.config_id is not None:
            return self.by_id.get(config.config_id)
        if config.config_key is not None:
            return self.by_key.get(config.config_key)
        return None

    def select_config_list(self, config: SysConfig) -> List[SysConfig]:
        self.calls.append("select_config_list")
        self.list_arguments.append(config)
        return list(self.rows)

    def check_config_key_unique(self, config_key: Optional[str]) -> Optional[SysConfig]:
        self.calls.append("check_config_key_unique")
        self.check_keys.append(config_key)
        return self.check_result

    def insert_config(self, config: SysConfig) -> int:
        self.calls.append("insert_config")
        return self.insert_result

    def update_config(self, config: SysConfig) -> int:
        self.calls.append("update_config")
        return self.update_result

    def delete_config_by_ids(self, config_ids: Any) -> int:
        self.calls.append("delete_config_by_ids")
        return self.delete_result

    def of(self, name: str) -> int:
        return self.calls.count(name)


class _FakeRedisCache:
    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}
        self.set_calls: List[Any] = []
        self.keys_patterns: List[str] = []
        self.delete_calls: List[Any] = []

    def get_cache_object(self, key: str) -> Any:
        return self.store.get(key)

    def set_cache_object(self, key: str, value: Any) -> None:
        self.set_calls.append((key, value))
        self.store[key] = value

    def keys(self, pattern: str) -> List[str]:
        self.keys_patterns.append(pattern)
        prefix = pattern[:-1]
        return [key for key in self.store if key.startswith(prefix)]

    def delete_object(self, key: Any) -> bool:
        self.delete_calls.append(key)
        if isinstance(key, list):
            for item in key:
                self.store.pop(item, None)
        else:
            self.store.pop(key, None)
        return True


@pytest.fixture
def mapper() -> _FakeConfigMapper:
    return _FakeConfigMapper()


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> _FakeRedisCache:
    fake = _FakeRedisCache()
    monkeypatch.setattr(service_module, "get_redis_cache", lambda: fake)
    return fake


@pytest.fixture
def service(mapper: _FakeConfigMapper, cache: _FakeRedisCache) -> SysConfigService:
    return SysConfigService(config_mapper=mapper)


def _config(**kwargs: Any) -> SysConfig:
    values: Dict[str, Any] = {"config_id": 1, "config_name": "皮肤", "config_key": "k"}
    values.update(kwargs)
    return SysConfig(**values)


# --------------------------------------------------------------------------- init


class TestInit:
    def test_the_constructor_does_not_touch_the_database(self, mapper: _FakeConfigMapper) -> None:
        SysConfigService(config_mapper=mapper)
        assert mapper.calls == []

    def test_every_row_lands_in_its_own_key(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.rows = [
            _config(config_key="a", config_value="1"),
            _config(config_key="b", config_value="2"),
        ]

        service.init()

        assert cache.set_calls == [("sys_config:a", "1"), ("sys_config:b", "2")]

    def test_the_warm_up_reads_through_select_config_list(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        """Java 用的是 ``selectConfigList(new SysConfig())``，不是单独的 statement。"""
        service.init()

        assert mapper.of("select_config_list") == 1
        assert mapper.list_arguments[0].config_id is None
        assert mapper.list_arguments[0].config_key is None


# --------------------------------------------------------------------------- selectConfigByKey


class TestSelectConfigByKey:
    def test_a_cache_hit_short_circuits_the_database(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        cache.store["sys_config:k"] = "v"

        assert service.select_config_by_key("k") == "v"
        assert mapper.of("select_config") == 0

    def test_a_number_in_the_cache_is_converted_by_to_str(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        """``Convert.toStr`` 走 ``toString()``：``123`` -> ``"123"``。"""
        cache.store["sys_config:k"] = 123

        assert service.select_config_by_key("k") == "123"
        assert mapper.of("select_config") == 0

    @pytest.mark.parametrize("cached", ["", " ", "   "])
    def test_a_blank_cache_value_is_a_miss(
        self,
        service: SysConfigService,
        mapper: _FakeConfigMapper,
        cache: _FakeRedisCache,
        cached: str,
    ) -> None:
        """RuoYi 的 ``StringUtils.isNotEmpty`` 会 trim —— 空格也算空。"""
        cache.store["sys_config:k"] = cached
        mapper.by_key["k"] = _config(config_value="from-db")

        assert service.select_config_by_key("k") == "from-db"
        assert mapper.of("select_config") == 1

    def test_a_missing_cache_key_is_a_miss(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.by_key["k"] = _config(config_value="from-db")

        assert service.select_config_by_key("k") == "from-db"

    def test_a_database_hit_is_written_back(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.by_key["k"] = _config(config_value="from-db")

        service.select_config_by_key("k")

        assert cache.set_calls == [("sys_config:k", "from-db")]

    def test_a_database_miss_returns_the_empty_string(
        self, service: SysConfigService, cache: _FakeRedisCache
    ) -> None:
        """Java 最后一行的 ``return StringUtils.EMPTY`` —— 空串，不是 ``None``。"""
        assert service.select_config_by_key("nope") == ""
        assert cache.set_calls == []

    def test_the_row_value_is_returned_raw(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        """库里是 ``NULL`` 时返回 ``None``（不是空串）—— Java 同样返回 null。"""
        mapper.by_key["k"] = _config(config_value=None)

        assert service.select_config_by_key("k") is None

    def test_the_query_is_by_key_not_by_id(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.by_key["k"] = _config(config_value="v")

        service.select_config_by_key("k")

        assert mapper.by_key["k"].config_key == "k"


# --------------------------------------------------------------------------- cache key


class TestCacheKey:
    def test_the_prefix_is_sys_config(self, service: SysConfigService) -> None:
        assert service.get_cache_key("k") == "sys_config:k"

    def test_a_null_key_becomes_the_literal_null(self, service: SysConfigService) -> None:
        """Java ``"sys_config:" + null`` -> ``"sys_config:null"``。"""
        assert service.get_cache_key(None) == "sys_config:null"


# --------------------------------------------------------------------------- insert / update


class TestInsertConfig:
    def test_a_successful_insert_writes_the_single_key(
        self, service: SysConfigService, cache: _FakeRedisCache
    ) -> None:
        assert service.insert_config(_config(config_value="v")) == 1
        assert cache.set_calls == [("sys_config:k", "v")]

    def test_a_failed_insert_does_not_touch_the_cache(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.insert_result = 0

        assert service.insert_config(_config(config_value="v")) == 0
        assert cache.set_calls == []

    def test_the_insert_does_not_clear_the_whole_cache(
        self, service: SysConfigService, cache: _FakeRedisCache
    ) -> None:
        """与字典相反：增改是**写键**，不是全清。"""
        service.insert_config(_config(config_value="v"))

        assert cache.keys_patterns == []
        assert cache.delete_calls == []


class TestUpdateConfig:
    def test_a_successful_update_writes_the_single_key(
        self, service: SysConfigService, cache: _FakeRedisCache
    ) -> None:
        assert service.update_config(_config(config_value="v2")) == 1
        assert cache.set_calls == [("sys_config:k", "v2")]

    def test_a_failed_update_does_not_touch_the_cache(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.update_result = 0

        assert service.update_config(_config(config_value="v2")) == 0
        assert cache.set_calls == []


# --------------------------------------------------------------------------- delete


class TestDeleteConfigByIds:
    def test_a_built_in_parameter_is_rejected_with_the_trailing_space(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        """Java 文案 ``"内置参数【%1$s】不能删除 "`` —— 末尾那个空格照抄。"""
        mapper.by_id[1] = _config(config_id=1, config_key="sys.index.skinName", config_type="Y")

        with pytest.raises(CustomException) as caught:
            service.delete_config_by_ids([1])

        assert str(caught.value) == "内置参数【sys.index.skinName】不能删除 "

    def test_one_bad_id_blocks_the_whole_batch(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.by_id[1] = _config(config_id=1, config_type="N")
        mapper.by_id[2] = _config(config_id=2, config_type="Y", config_key="built-in")

        with pytest.raises(CustomException):
            service.delete_config_by_ids([1, 2])

        assert mapper.of("delete_config_by_ids") == 0

    @pytest.mark.parametrize("config_type", ["N", "", None])
    def test_only_uppercase_y_is_protected(
        self, service: SysConfigService, mapper: _FakeConfigMapper, config_type: Optional[str]
    ) -> None:
        """``StringUtils.equals("Y", configType)`` —— 其它值全部放行。"""
        mapper.by_id[1] = _config(config_id=1, config_type=config_type)

        assert service.delete_config_by_ids([1]) == 1

    def test_a_missing_row_raises_like_the_java_npe(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        """Java 没判空，直接在 ``config.getConfigType()`` 处 NPE -> 500。"""
        with pytest.raises(AttributeError):
            service.delete_config_by_ids([99])

        assert mapper.of("delete_config_by_ids") == 0

    def test_a_non_zero_count_clears_every_key(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.by_id[1] = _config(config_id=1, config_type="N")
        cache.store["sys_config:a"] = "1"
        cache.store["sys_config:b"] = "2"

        assert service.delete_config_by_ids([1]) == 1

        assert cache.keys_patterns == ["sys_config:*"]
        assert cache.delete_calls == [["sys_config:a", "sys_config:b"]]
        assert cache.store == {}

    def test_a_zero_count_leaves_the_cache_alone(
        self, service: SysConfigService, mapper: _FakeConfigMapper, cache: _FakeRedisCache
    ) -> None:
        mapper.by_id[1] = _config(config_id=1, config_type="N")
        mapper.delete_result = 0

        assert service.delete_config_by_ids([1]) == 0
        assert cache.keys_patterns == []


class TestClearCache:
    def test_clear_cache_deletes_every_sys_config_key(
        self, service: SysConfigService, cache: _FakeRedisCache
    ) -> None:
        cache.store["sys_config:a"] = "1"
        cache.store["sys_dict:x"] = "keep"

        service.clear_cache()

        assert cache.keys_patterns == ["sys_config:*"]
        assert cache.store == {"sys_dict:x": "keep"}


# --------------------------------------------------------------------------- checkConfigKeyUnique


class TestCheckConfigKeyUnique:
    def test_an_existing_other_row_is_not_unique(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.check_result = _config(config_id=2)

        assert service.check_config_key_unique(_config(config_id=1)) == "1"

    def test_the_same_row_is_unique(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.check_result = _config(config_id=1)

        assert service.check_config_key_unique(_config(config_id=1)) == "0"

    def test_a_miss_is_unique(self, service: SysConfigService, mapper: _FakeConfigMapper) -> None:
        assert service.check_config_key_unique(_config(config_id=None)) == "0"

    def test_a_null_id_is_treated_as_minus_one(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        """新增时 ``configId`` 是 null -> ``-1``，与任何真实 id 都不相等。"""
        mapper.check_result = _config(config_id=1)

        assert service.check_config_key_unique(_config(config_id=None)) == "1"

    def test_the_mapper_receives_the_key_not_the_entity(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        service.check_config_key_unique(_config(config_key="sys.index.skinName"))

        assert mapper.check_keys == ["sys.index.skinName"]

    def test_the_entity_is_not_mutated(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.check_result = _config(config_id=2)
        config = _config(config_id=None)

        service.check_config_key_unique(config)

        assert config.config_id is None


# --------------------------------------------------------------------------- delegation / singleton


class TestDelegation:
    def test_select_config_list_is_a_passthrough(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.rows = [_config()]

        assert service.select_config_list(SysConfig(config_type="Y")) == mapper.rows
        assert mapper.of("select_config_list") == 1

    def test_select_config_by_id_builds_a_minimal_entity(
        self, service: SysConfigService, mapper: _FakeConfigMapper
    ) -> None:
        mapper.by_id[5] = _config(config_id=5)

        assert service.select_config_by_id(5) is mapper.by_id[5]

    def test_select_config_by_id_returns_none_on_a_miss(
        self, service: SysConfigService
    ) -> None:
        assert service.select_config_by_id(404) is None


class TestSingleton:
    def test_get_config_service_returns_the_same_instance(self) -> None:
        reset_config_service()
        try:
            assert get_config_service() is get_config_service()
        finally:
            reset_config_service()

    def test_reset_drops_the_instance(self) -> None:
        reset_config_service()
        first = get_config_service()
        reset_config_service()

        assert get_config_service() is not first
        reset_config_service()
