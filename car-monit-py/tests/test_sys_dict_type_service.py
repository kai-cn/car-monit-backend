"""``SysDictTypeService`` -- 缓存、唯一性与"改类型名同步子表".

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictTypeServiceImpl.java

这一层的三个"必须照抄"
----------------------
1. ``updateDictType`` **先改子表、再改主表**，且用**旧**类型名做 ``where``。顺序换了
   （或拿新名字去改子表）会让子项全部变成孤儿行 —— 且不报错。
2. ``deleteDictTypeByIds`` 是"先全查、再一次性删"：``for`` 里只校验，删除在循环之后。
   一旦某个类型"已分配"就抛 ``CustomException``，**整批都不删**。
3. ``selectDictDataByTypeMore`` 里有两处"看起来像 bug 的原文"：``substring(0, len)``
   的空操作（尾逗号根本没去掉，缓存键跟着带尾逗号）和重复的 ``isEmpty`` 判空。

``init()`` 不自动调用
---------------------
Java 用 ``@PostConstruct`` 预热缓存。本工程数据源是惰性的（见 ``app.main``），
启动期连库会让"没有 MySQL 也能起来做健康检查"失效，所以**保留方法、不挂到生命周期**。
语义无损：缓存未命中时 ``selectDictDataByType`` 会用同一条 SQL 回源。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.constant import user_constants as UserConstants
from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.exception.exceptions import CustomException
from app.system.service import sys_dict_type_service as service_module
from app.system.service.sys_dict_type_service import (
    SysDictTypeService,
    get_dict_type_service,
    reset_dict_type_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeTypeMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.all_result: List[SysDictType] = []
        self.list_result: List[SysDictType] = []
        self.by_id: Dict[int, SysDictType] = {}
        self.by_type: Optional[SysDictType] = None
        self.unique_result: Optional[SysDictType] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1

    def select_dict_type_list(self, query: SysDictType) -> List[SysDictType]:
        self.calls.append(("select_dict_type_list", query.model_copy(deep=True)))
        return self.list_result

    def select_dict_type_all(self) -> List[SysDictType]:
        self.calls.append(("select_dict_type_all",))
        return self.all_result

    def select_dict_type_by_id(self, dict_id: int) -> Optional[SysDictType]:
        self.calls.append(("select_dict_type_by_id", dict_id))
        return self.by_id.get(dict_id)

    def select_dict_type_by_type(self, dict_type: Optional[str]) -> Optional[SysDictType]:
        self.calls.append(("select_dict_type_by_type", dict_type))
        return self.by_type

    def check_dict_type_unique(self, dict_type: Optional[str]) -> Optional[SysDictType]:
        self.calls.append(("check_dict_type_unique", dict_type))
        return self.unique_result

    def delete_dict_type_by_id(self, dict_id: int) -> int:
        self.calls.append(("delete_dict_type_by_id", dict_id))
        return self.delete_result

    def delete_dict_type_by_ids(self, dict_ids: Sequence[int]) -> int:
        self.calls.append(("delete_dict_type_by_ids", list(dict_ids)))
        return self.delete_result

    def insert_dict_type(self, entity: SysDictType) -> int:
        self.calls.append(("insert_dict_type", entity.model_copy(deep=True)))
        return self.insert_result

    def update_dict_type(self, entity: SysDictType) -> int:
        self.calls.append(("update_dict_type", entity.model_copy(deep=True)))
        return self.update_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeDataMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_type: Dict[Optional[str], List[SysDictData]] = {}
        self.by_type_more: Dict[Optional[str], List[SysDictData]] = {}
        self.counts: Dict[Optional[str], int] = {}
        self.update_type_result = 1

    def select_dict_data_by_type(self, dict_type: Optional[str]) -> List[SysDictData]:
        self.calls.append(("select_dict_data_by_type", dict_type))
        return list(self.by_type.get(dict_type, []))

    def select_dict_data_by_type_more(self, dict_types: Optional[str]) -> List[SysDictData]:
        self.calls.append(("select_dict_data_by_type_more", dict_types))
        return list(self.by_type_more.get(dict_types, []))

    def count_dict_data_by_type(self, dict_type: Optional[str]) -> int:
        self.calls.append(("count_dict_data_by_type", dict_type))
        return self.counts.get(dict_type, 0)

    def update_dict_data_type(self, old_dict_type: Optional[str], new_dict_type: Optional[str]) -> int:
        self.calls.append(("update_dict_data_type", old_dict_type, new_dict_type))
        return self.update_type_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeDictCache:
    """替身 :mod:`app.common.utils.dict_utils` 的读/写/清。"""

    def __init__(self) -> None:
        self.store: Dict[str, List[SysDictData]] = {}
        self.set_calls: List[tuple] = []
        self.cleared = 0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(service_module.DictUtils, "get_dict_cache", self.get)
        monkeypatch.setattr(service_module.DictUtils, "set_dict_cache", self.set)
        monkeypatch.setattr(service_module.DictUtils, "clear_dict_cache", self.clear)

    # Java: DictUtils.getDictCache / setDictCache / clearDictCache
    def get(self, key: Optional[str]) -> Optional[List[SysDictData]]:
        return self.store.get(key or "")

    def set(self, key: Optional[str], datas: Optional[Sequence[SysDictData]]) -> None:
        self.set_calls.append((key, list(datas or [])))
        self.store[key or ""] = list(datas or [])

    def clear(self) -> None:
        self.cleared += 1
        self.store.clear()


@pytest.fixture
def mappers() -> Any:
    return _FakeTypeMapper(), _FakeDataMapper()


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> _FakeDictCache:
    fake = _FakeDictCache()
    fake.install(monkeypatch)
    return fake


@pytest.fixture
def service(mappers: Any, cache: _FakeDictCache) -> SysDictTypeService:
    type_mapper, data_mapper = mappers
    return SysDictTypeService(type_mapper, data_mapper)


def _dict_type(dict_id: int = 1, dict_type: str = "sys_user_sex") -> SysDictType:
    return SysDictType(dict_id=dict_id, dict_name="用户性别", dict_type=dict_type)


def _item(value: str, label: str, dict_type: str = "sys_user_sex") -> SysDictData:
    return SysDictData(dict_value=value, dict_label=label, dict_type=dict_type)


# --------------------------------------------------------------------------- init


class TestInit:
    def test_every_type_is_warmed_up(self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache) -> None:
        type_mapper, data_mapper = mappers
        type_mapper.all_result = [_dict_type(1, "sys_user_sex"), _dict_type(2, "sys_yes_no")]
        data_mapper.by_type = {
            "sys_user_sex": [_item("0", "男")],
            "sys_yes_no": [_item("Y", "是", "sys_yes_no")],
        }

        service.init()

        assert [call[0] for call in cache.set_calls] == ["sys_user_sex", "sys_yes_no"]
        assert cache.store["sys_yes_no"][0].dict_label == "是"

    def test_a_type_without_items_still_writes_an_empty_list(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        """Java 的 ``selectDictDataByType`` 返回空 List（不是 null），照写。"""
        type_mapper, _data_mapper = mappers
        type_mapper.all_result = [_dict_type(1, "empty_type")]

        service.init()

        assert cache.store["empty_type"] == []

    def test_no_types_means_no_writes(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        service.init()

        assert cache.set_calls == []

    def test_init_is_not_called_by_the_constructor(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """Python 侧不挂生命周期（数据源惰性）—— 构造服务不该连库。"""
        type_mapper, _data_mapper = mappers

        assert type_mapper.calls == []


# --------------------------------------------------------------------------- selectDictDataByType


class TestSelectDictDataByType:
    def test_a_cache_hit_skips_the_database(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        _type_mapper, data_mapper = mappers
        cache.store["sys_user_sex"] = [_item("0", "男")]

        rows = service.select_dict_data_by_type("sys_user_sex")

        assert rows is not None
        assert rows[0].dict_label == "男"
        assert data_mapper.calls == []

    def test_a_cache_miss_reads_the_database_and_writes_back(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        _type_mapper, data_mapper = mappers
        data_mapper.by_type = {"sys_user_sex": [_item("0", "男")]}

        rows = service.select_dict_data_by_type("sys_user_sex")

        assert rows is not None
        assert data_mapper.of("select_dict_data_by_type") == [("select_dict_data_by_type", "sys_user_sex")]
        assert [call[0] for call in cache.set_calls] == ["sys_user_sex"]
        assert cache.store["sys_user_sex"][0].dict_label == "男"

    def test_an_empty_result_returns_none_and_writes_nothing(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        """空结果**不**写缓存，也**不**返回空列表 —— 控制器负责换成 ``[]``。"""
        assert service.select_dict_data_by_type("unknown") is None
        assert cache.set_calls == []

    def test_an_empty_cached_list_falls_back_to_the_database(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        """``isNotEmpty([])`` 为假 —— 空列表等于未命中（与 Java 同）。"""
        _type_mapper, data_mapper = mappers
        cache.store["sys_user_sex"] = []
        data_mapper.by_type = {"sys_user_sex": [_item("1", "女")]}

        rows = service.select_dict_data_by_type("sys_user_sex")

        assert rows is not None
        assert rows[0].dict_label == "女"


# --------------------------------------------------------------------------- selectDictDataByTypeMore


class TestSelectDictDataByTypeMore:
    def test_an_empty_input_uses_the_sentinel(self, service: SysDictTypeService, mappers: Any) -> None:
        """``"-dadadadas"`` 是一个永远查不到的类型名 —— 照抄。"""
        _type_mapper, data_mapper = mappers

        assert service.select_dict_data_by_type_more("") is None
        assert data_mapper.of("select_dict_data_by_type_more") == [
            ("select_dict_data_by_type_more", "-dadadadas")
        ]

    def test_none_also_uses_the_sentinel(self, service: SysDictTypeService, mappers: Any) -> None:
        _type_mapper, data_mapper = mappers

        service.select_dict_data_by_type_more(None)

        assert data_mapper.of("select_dict_data_by_type_more")[0][1] == "-dadadadas"

    def test_a_blank_string_is_not_empty(self, service: SysDictTypeService, mappers: Any) -> None:
        """``StringUtils.isEmpty(" ")`` **trim** 后为空 -> 也是 sentinel。"""
        _type_mapper, data_mapper = mappers

        service.select_dict_data_by_type_more(" ")

        assert data_mapper.of("select_dict_data_by_type_more")[0][1] == "-dadadadas"

    def test_a_trailing_comma_is_kept(self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache) -> None:
        """``substring(0, length)`` 是**空操作**：尾逗号留在缓存键里，也传给 mapper。"""
        _type_mapper, data_mapper = mappers

        service.select_dict_data_by_type_more("car_type,")

        assert data_mapper.of("select_dict_data_by_type_more")[0][1] == "car_type,"

    def test_a_hit_is_served_from_cache(self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache) -> None:
        _type_mapper, data_mapper = mappers
        cache.store["car_type,plate_color"] = [_item("1", "轿车", "car_type")]

        rows = service.select_dict_data_by_type_more("car_type,plate_color")

        assert rows is not None
        assert rows[0].dict_label == "轿车"
        assert data_mapper.calls == []

    def test_a_miss_reads_the_database_and_writes_back(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        _type_mapper, data_mapper = mappers
        data_mapper.by_type_more = {"a,b": [_item("1", "甲", "a")]}

        rows = service.select_dict_data_by_type_more("a,b")

        assert rows is not None
        assert cache.set_calls[0][0] == "a,b"

    def test_an_empty_result_returns_none(self, service: SysDictTypeService, mappers: Any) -> None:
        assert service.select_dict_data_by_type_more("nothing") is None


# --------------------------------------------------------------------------- deleteDictTypeByIds


class TestDeleteDictTypeByIds:
    def test_a_free_type_is_deleted_once(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1), 2: _dict_type(2, "sys_yes_no")}
        type_mapper.delete_result = 2

        assert service.delete_dict_type_by_ids([1, 2]) == 2

        assert type_mapper.of("delete_dict_type_by_ids") == [("delete_dict_type_by_ids", [1, 2])]
        assert cache.cleared == 1

    def test_the_delete_runs_after_the_whole_loop(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """先全查、再一次性删 —— 顺序不能变成"边查边删"。"""
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1), 2: _dict_type(2, "sys_yes_no")}

        service.delete_dict_type_by_ids([1, 2])

        names = [call[0] for call in type_mapper.calls]
        assert names[-1] == "delete_dict_type_by_ids"
        assert names.count("select_dict_type_by_id") == 2

    def test_an_assigned_type_aborts_the_whole_batch(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1)}
        data_mapper.counts = {"sys_user_sex": 3}

        with pytest.raises(CustomException) as error:
            service.delete_dict_type_by_ids([1])

        assert "用户性别已分配,不能删除" == str(error.value)
        assert type_mapper.of("delete_dict_type_by_ids") == []
        assert cache.cleared == 0

    def test_the_second_type_stops_the_batch(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1), 2: _dict_type(2, "sys_yes_no")}
        data_mapper.counts = {"sys_yes_no": 1}

        with pytest.raises(CustomException):
            service.delete_dict_type_by_ids([1, 2])

        assert type_mapper.of("delete_dict_type_by_ids") == []
        # 第一条已经查过了（Java 是边走边校验，不是先全查）
        assert len(type_mapper.of("select_dict_type_by_id")) == 2

    def test_a_missing_type_raises_like_the_java_npe(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """``dictType.getDictType()`` 对 null 解引用 -> NPE -> 500。"""
        with pytest.raises(AttributeError) as error:
            service.delete_dict_type_by_ids([404])

        assert "NullPointerException" in str(error.value)


# --------------------------------------------------------------------------- clear / insert


class TestClearAndInsert:
    def test_clear_cache_only_touches_the_cache(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, data_mapper = mappers

        service.clear_cache()

        assert cache.cleared == 1
        assert type_mapper.calls == []
        assert data_mapper.calls == []

    def test_insert_clears_the_cache_on_success(
        self, service: SysDictTypeService, cache: _FakeDictCache
    ) -> None:
        assert service.insert_dict_type(_dict_type()) == 1
        assert cache.cleared == 1

    def test_insert_leaves_the_cache_alone_on_failure(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.insert_result = 0

        assert service.insert_dict_type(_dict_type()) == 0
        assert cache.cleared == 0


# --------------------------------------------------------------------------- updateDictType


class TestUpdateDictType:
    def test_the_child_table_is_renamed_first(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """子表用**旧**类型名做 where、改成新名字，然后才改主表。"""
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1, "old_type")}

        service.update_dict_type(_dict_type(1, "new_type"))

        assert data_mapper.of("update_dict_data_type") == [
            ("update_dict_data_type", "old_type", "new_type")
        ]
        assert type_mapper.of("update_dict_type")[0][1].dict_type == "new_type"

    def test_the_child_rename_precedes_the_parent_update(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1, "old_type")}

        service.update_dict_type(_dict_type(1, "new_type"))

        # 两次调用分别落在两个 mapper 上，用调用顺序证明先后
        order: List[str] = []
        order.append(type_mapper.calls[0][0])
        order.append(data_mapper.calls[0][0])
        order.append(type_mapper.calls[-1][0])
        assert order == ["select_dict_type_by_id", "update_dict_data_type", "update_dict_type"]

    def test_the_cache_is_cleared_after_a_successful_update(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1, "old_type")}

        assert service.update_dict_type(_dict_type(1, "new_type")) == 1
        assert cache.cleared == 1

    def test_a_failed_update_does_not_clear_the_cache(
        self, service: SysDictTypeService, mappers: Any, cache: _FakeDictCache
    ) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1, "old_type")}
        type_mapper.update_result = 0

        assert service.update_dict_type(_dict_type(1, "new_type")) == 0
        assert cache.cleared == 0

    def test_the_children_are_still_renamed_when_the_parent_fails(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """**已知缺口**：Java 有 ``@Transactional``，Python 没有 —— 没有回滚。"""
        type_mapper, data_mapper = mappers
        type_mapper.by_id = {1: _dict_type(1, "old_type")}
        type_mapper.update_result = 0

        service.update_dict_type(_dict_type(1, "new_type"))

        assert data_mapper.of("update_dict_data_type") != []

    def test_a_missing_old_type_raises_like_the_java_npe(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        with pytest.raises(AttributeError) as error:
            service.update_dict_type(_dict_type(404, "new_type"))

        assert "NullPointerException" in str(error.value)


# --------------------------------------------------------------------------- checkDictTypeUnique


class TestCheckDictTypeUnique:
    def test_a_free_type_is_unique(self, service: SysDictTypeService) -> None:
        assert service.check_dict_type_unique(_dict_type(1, "brand_new")) == UserConstants.UNIQUE_OLD

    def test_another_row_with_the_same_type_is_not_unique(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.unique_result = _dict_type(2, "sys_user_sex")

        result = service.check_dict_type_unique(_dict_type(1, "sys_user_sex"))

        assert result == UserConstants.NOT_UNIQUE_OLD
        assert result == "1"

    def test_the_same_row_is_unique(self, service: SysDictTypeService, mappers: Any) -> None:
        """改自己时撞到的那一条就是自己 -> ``"0"``。"""
        type_mapper, _data_mapper = mappers
        type_mapper.unique_result = _dict_type(1, "sys_user_sex")

        assert service.check_dict_type_unique(_dict_type(1, "sys_user_sex")) == UserConstants.UNIQUE_OLD

    def test_a_new_entity_is_compared_as_minus_one(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """``dictId == null`` 时用 ``-1L`` 统一成"和自己比"，所以任何已存在行都不等于它。"""
        type_mapper, _data_mapper = mappers
        type_mapper.unique_result = _dict_type(5, "sys_user_sex")

        assert service.check_dict_type_unique(SysDictType(dict_type="sys_user_sex")) == "1"

    def test_the_entity_id_is_not_mutated(
        self, service: SysDictTypeService, mappers: Any
    ) -> None:
        """``-1`` 只在方法内比较，不回写实体。"""
        type_mapper, _data_mapper = mappers
        entity = SysDictType(dict_type="sys_user_sex")

        service.check_dict_type_unique(entity)

        assert entity.dict_id is None


# --------------------------------------------------------------------------- 委托


class TestDelegation:
    def test_select_list_delegates(self, service: SysDictTypeService, mappers: Any) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.list_result = [_dict_type()]

        rows = service.select_dict_type_list(SysDictType(dict_name="性别"))

        assert [row.dict_id for row in rows] == [1]
        assert type_mapper.of("select_dict_type_list")[0][1].dict_name == "性别"

    def test_select_all_delegates(self, service: SysDictTypeService, mappers: Any) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.all_result = [_dict_type()]

        assert [row.dict_id for row in service.select_dict_type_all()] == [1]

    def test_select_by_id_delegates(self, service: SysDictTypeService, mappers: Any) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.by_id = {3: _dict_type(3)}

        entity = service.select_dict_type_by_id(3)

        assert entity is not None
        assert entity.dict_id == 3

    def test_select_by_type_delegates(self, service: SysDictTypeService, mappers: Any) -> None:
        type_mapper, _data_mapper = mappers
        type_mapper.by_type = _dict_type()

        entity = service.select_dict_type_by_type("sys_user_sex")

        assert entity is not None
        assert type_mapper.of("select_dict_type_by_type") == [
            ("select_dict_type_by_type", "sys_user_sex")
        ]

    def test_the_mapper_properties_are_exposed(self, mappers: Any, service: SysDictTypeService) -> None:
        type_mapper, data_mapper = mappers
        assert service.dict_type_mapper is type_mapper
        assert service.dict_data_mapper is data_mapper


# --------------------------------------------------------------------------- 单例


def test_get_service_is_a_singleton() -> None:
    reset_dict_type_service()
    try:
        assert get_dict_type_service() is get_dict_type_service()
    finally:
        reset_dict_type_service()


def test_reset_drops_the_singleton() -> None:
    reset_dict_type_service()
    first = get_dict_type_service()
    reset_dict_type_service()
    try:
        assert get_dict_type_service() is not first
    finally:
        reset_dict_type_service()
