"""``SysDictDataService`` -- 写库即清缓存，以及两个"翻译表".

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java

三个要点
--------
1. 三个写方法都是"``row > 0`` 才 ``clearDictCache()``"；清的是**整个**字典缓存
   （``sys_dict:*``），因为 ``updateDictData`` 可能改了 ``dictType``。
2. ``selectDictDataMap`` / ``selectDictDataLaleMap`` **不走缓存**，直接查库，且
   **不过滤** ``status``（停用项也在映射表里）。它们没有控制器端点，是导出/详情接口的
   辅助方法。
3. ``Collectors.toMap`` 遇到重复键抛 ``IllegalStateException``（500）。Python 的字典
   推导会静默覆盖，所以这里显式抛，行为与 Java 一致；而 ``null`` **键**在 Java 里
   同样会抛（``toMap`` 用 ``HashMap.merge``，null 键 NPE），``null`` 值则允许。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.system.service import sys_dict_data_service as service_module
from app.system.service.sys_dict_data_service import (
    SysDictDataService,
    get_dict_data_service,
    reset_dict_data_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysDictData] = []
        self.by_id_result: Optional[SysDictData] = None
        self.label_result: Optional[str] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1

    def select_dict_data_list(self, query: SysDictData) -> List[SysDictData]:
        self.calls.append(("select_dict_data_list", query.model_copy(deep=True)))
        return list(self.list_result)

    def select_dict_label(self, dict_type: Optional[str], dict_value: Optional[str]) -> Optional[str]:
        self.calls.append(("select_dict_label", dict_type, dict_value))
        return self.label_result

    def select_dict_data_by_id(self, dict_code: int) -> Optional[SysDictData]:
        self.calls.append(("select_dict_data_by_id", dict_code))
        return self.by_id_result

    def delete_dict_data_by_ids(self, dict_codes: Sequence[int]) -> int:
        self.calls.append(("delete_dict_data_by_ids", list(dict_codes)))
        return self.delete_result

    def insert_dict_data(self, entity: SysDictData) -> int:
        self.calls.append(("insert_dict_data", entity.model_copy(deep=True)))
        return self.insert_result

    def update_dict_data(self, entity: SysDictData) -> int:
        self.calls.append(("update_dict_data", entity.model_copy(deep=True)))
        return self.update_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _CacheRecorder:
    def __init__(self) -> None:
        self.clears = 0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(service_module.DictUtils, "clear_dict_cache", self.clear)
        # 两个 Map 方法**不该**读缓存；真被调用就炸。
        monkeypatch.setattr(
            service_module.DictUtils,
            "get_dict_cache",
            lambda key: (_ for _ in ()).throw(AssertionError("cache must not be read")),
        )

    def clear(self) -> None:
        self.clears += 1


@pytest.fixture
def mapper() -> _FakeMapper:
    return _FakeMapper()


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> _CacheRecorder:
    recorder = _CacheRecorder()
    recorder.install(monkeypatch)
    return recorder


@pytest.fixture
def service(mapper: _FakeMapper, cache: _CacheRecorder) -> SysDictDataService:
    return SysDictDataService(mapper)


def _item(value: str, label: str, dict_type: str = "sys_user_sex") -> SysDictData:
    return SysDictData(dict_value=value, dict_label=label, dict_type=dict_type)


# --------------------------------------------------------------------------- 写方法


class TestWritesClearTheCache:
    def test_insert_clears_on_success(self, service: SysDictDataService, cache: _CacheRecorder) -> None:
        assert service.insert_dict_data(_item("0", "男")) == 1
        assert cache.clears == 1

    def test_insert_leaves_the_cache_alone_on_failure(
        self, service: SysDictDataService, mapper: _FakeMapper, cache: _CacheRecorder
    ) -> None:
        mapper.insert_result = 0

        assert service.insert_dict_data(_item("0", "男")) == 0
        assert cache.clears == 0

    def test_update_clears_on_success(self, service: SysDictDataService, cache: _CacheRecorder) -> None:
        assert service.update_dict_data(SysDictData(dict_code=1)) == 1
        assert cache.clears == 1

    def test_update_leaves_the_cache_alone_on_failure(
        self, service: SysDictDataService, mapper: _FakeMapper, cache: _CacheRecorder
    ) -> None:
        mapper.update_result = 0

        assert service.update_dict_data(SysDictData(dict_code=1)) == 0
        assert cache.clears == 0

    def test_delete_clears_on_success(self, service: SysDictDataService, cache: _CacheRecorder) -> None:
        assert service.delete_dict_data_by_ids([1, 2]) == 1
        assert cache.clears == 1

    def test_delete_leaves_the_cache_alone_on_failure(
        self, service: SysDictDataService, mapper: _FakeMapper, cache: _CacheRecorder
    ) -> None:
        mapper.delete_result = 0

        assert service.delete_dict_data_by_ids([1]) == 0
        assert cache.clears == 0

    def test_the_delete_is_a_single_statement(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        """物理删除、批量一条 SQL，没有"先查再删"。"""
        service.delete_dict_data_by_ids([3, 4])

        assert mapper.calls == [("delete_dict_data_by_ids", [3, 4])]


# --------------------------------------------------------------------------- 读方法


class TestReads:
    def test_select_list_delegates(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        mapper.list_result = [_item("0", "男")]

        rows = service.select_dict_data_list(SysDictData(dict_type="sys_user_sex"))

        assert [row.dict_label for row in rows] == ["男"]
        assert mapper.of("select_dict_data_list")[0][1].dict_type == "sys_user_sex"

    def test_select_label_goes_straight_to_the_database(
        self, service: SysDictDataService, mapper: _FakeMapper, cache: _CacheRecorder
    ) -> None:
        """**不走缓存** —— 与 ``DictUtils.getDictLabel`` 是两条路。"""
        mapper.label_result = "男"

        assert service.select_dict_label("sys_user_sex", "0") == "男"
        assert mapper.of("select_dict_label") == [("select_dict_label", "sys_user_sex", "0")]

    def test_select_label_passes_none_through(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        assert service.select_dict_label(None, None) is None
        assert mapper.of("select_dict_label") == [("select_dict_label", None, None)]

    def test_select_by_id_delegates(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        mapper.by_id_result = _item("0", "男")

        entity = service.select_dict_data_by_id(5)

        assert entity is not None
        assert mapper.of("select_dict_data_by_id") == [("select_dict_data_by_id", 5)]


# --------------------------------------------------------------------------- selectDictDataMap


class TestSelectDictDataMap:
    def test_value_maps_to_label(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        mapper.list_result = [_item("0", "男"), _item("1", "女")]

        result = service.select_dict_data_map("sys_user_sex")

        assert result == {"0": "男", "1": "女"}

    def test_the_argument_is_really_the_dict_type(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        """形参叫 ``dictValue``，实际传的是**字典类型** —— 命名照抄 Java。"""
        service.select_dict_data_map("car_type")

        query = mapper.of("select_dict_data_list")[0][1]
        assert query.dict_type == "car_type"
        assert query.dict_value is None

    def test_the_status_is_not_filtered(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        """停用项也在映射表里（Java 只按 ``dictType`` 查）。"""
        service.select_dict_data_map("sys_user_sex")

        assert mapper.of("select_dict_data_list")[0][1].status is None

    def test_an_empty_result_is_an_empty_dict(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        assert service.select_dict_data_map("unknown") == {}

    def test_a_duplicate_value_raises(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        """``Collectors.toMap`` 的重复键 -> ``IllegalStateException`` -> 500。"""
        mapper.list_result = [_item("0", "男"), _item("0", "男性")]

        with pytest.raises(AttributeError) as error:
            service.select_dict_data_map("sys_user_sex")

        assert "IllegalStateException" in str(error.value)
        assert "Duplicate key 0" in str(error.value)

    def test_two_null_values_collide(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        """历史脏数据里 ``dict_value`` 可能是 null；两条 null 就是重复键。"""
        mapper.list_result = [SysDictData(dict_value=None, dict_label="甲"), SysDictData(dict_value=None, dict_label="乙")]

        with pytest.raises(AttributeError):
            service.select_dict_data_map("broken")

    def test_a_null_label_is_allowed(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        """``toMap`` 不拒绝 null 值（HashMap 允许）。"""
        mapper.list_result = [SysDictData(dict_value="0", dict_label=None)]

        assert service.select_dict_data_map("sys_user_sex") == {"0": None}


# --------------------------------------------------------------------------- selectDictDataLaleMap


class TestSelectDictDataLaleMap:
    def test_label_maps_to_value(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        mapper.list_result = [_item("0", "男"), _item("1", "女")]

        result = service.select_dict_data_lale_map("sys_user_sex")

        assert result == {"男": "0", "女": "1"}

    def test_the_direction_is_the_opposite_of_the_sibling(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        mapper.list_result = [_item("0", "男")]

        forward = service.select_dict_data_map("sys_user_sex")
        backward = service.select_dict_data_lale_map("sys_user_sex")

        assert forward == {"0": "男"}
        assert backward == {"男": "0"}

    def test_a_duplicate_label_raises(self, service: SysDictDataService, mapper: _FakeMapper) -> None:
        mapper.list_result = [_item("0", "男"), _item("1", "男")]

        with pytest.raises(AttributeError) as error:
            service.select_dict_data_lale_map("sys_user_sex")

        assert "Duplicate key 男" in str(error.value)

    def test_an_empty_result_is_an_empty_dict(
        self, service: SysDictDataService, mapper: _FakeMapper
    ) -> None:
        assert service.select_dict_data_lale_map("unknown") == {}


# --------------------------------------------------------------------------- 单例


def test_get_service_is_a_singleton() -> None:
    reset_dict_data_service()
    try:
        assert get_dict_data_service() is get_dict_data_service()
    finally:
        reset_dict_data_service()


def test_the_mapper_is_exposed() -> None:
    mapper = _FakeMapper()
    assert SysDictDataService(mapper).mapper is mapper
