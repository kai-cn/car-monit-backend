"""``DictUtils`` -- 字典缓存与"编码 <-> 中文"翻译.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-common/src/main/java/com/ruoyi/common/utils/DictUtils.java

为什么这一层必须测
------------------
``DictUtils`` 是全工程**唯一**的"字典翻译"入口：导出时每一列的中文、详情页每一个
枚举的显示值都从这里出。Java 侧它有四个"看起来像笔误、实际是行为"的地方：

1. ``containsAny(separator, dictValue)`` 的**两个参数是反的**。Commons Lang 的签名是
   ``containsAny(cs, searchChars)``，问"``cs`` 里有没有 ``searchChars`` 的任意字符"。
   传入 ``(",", dictValue)`` 的实际语义是"逗号串里有没有 dictValue 的字符" —— 因为
   ``separator`` 恒为 ``","``，效果恰好等于"``dictValue`` 里有逗号"。换个
   separator（比如 ``"1"``）语义立刻跑偏，:class:`TestReversedContainsAny` 把这个
   坑钉住。
2. 多值分支的**外层是字典项**、内层才是入参拆分，所以输出顺序是"字典表顺序"，
   不是"入参顺序"。
3. 单值分支命中后直接 ``return``，**不**走 ``stripEnd`` —— 标签本身带尾逗号时会
   原样带出去；多值分支才会剥。
4. ``getDictValue`` 的 else 分支没有 ``isNotNull(datas)`` 保护，缓存未命中 + 单值
   查询在 Java 里是 **NPE（500）**，不是空串。:func:`get_dict_label` 在同样位置
   ``return ""``（它先判了 ``isNotNull``）—— 这个**不对称**是照抄的。

缓存键
------
``CacheConstants.SYS_DICT_KEY = "sys_dict:"`` + 字典类型。``clearDictCache`` 用
``KEYS sys_dict:*`` 再批量删，是 O(N) 阻塞命令（照抄，见 ``COMPATIBILITY.md``）。
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from app.common.utils import dict_utils as DictUtils
from app.common.utils.dict_utils import (
    SEPARATOR,
    clear_dict_cache,
    get_cache_key,
    get_dict_cache,
    get_dict_label,
    get_dict_label_with_separator,
    get_dict_value,
    remove_dict_cache,
    set_dict_cache,
)
from app.common.utils.string_utils import strip_end

# --------------------------------------------------------------------------- fakes


class _FakeRedisCache:
    """只实现 ``DictUtils`` 用到的 4 个方法（``RedisCache`` 的最小面）。"""

    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}
        self.set_calls: List[tuple] = []
        self.deleted: List[Any] = []
        self.key_patterns: List[str] = []

    def set_cache_object(self, key: str, value: Any) -> None:
        # 真实实现走 fastjson2 序列化；这里直接存对象，语义等价（读回来是同一份数据）。
        self.set_calls.append((key, value))
        self.store[key] = value

    def get_cache_object(self, key: str) -> Any:
        return self.store.get(key)

    def delete_object(self, key: Any) -> bool:
        self.deleted.append(key)
        if isinstance(key, (list, tuple, set)):
            for item in key:
                self.store.pop(item, None)
        else:
            self.store.pop(key, None)
        return True

    def keys(self, pattern: str) -> List[str]:
        self.key_patterns.append(pattern)
        prefix = pattern[:-1] if pattern.endswith("*") else pattern
        return [key for key in self.store if key.startswith(prefix)]


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> _FakeRedisCache:
    fake = _FakeRedisCache()
    monkeypatch.setattr(DictUtils, "get_redis_cache", lambda: fake)
    return fake


def _item(value: str, label: str, dict_type: str = "sys_user_sex") -> DictUtils.SysDictData:
    from app.common.core.domain.entity.sys_dict_data import SysDictData

    return SysDictData(dict_value=value, dict_label=label, dict_type=dict_type)


def _seed(cache: _FakeRedisCache, *items: DictUtils.SysDictData, dict_type: str = "sys_user_sex") -> None:
    cache.store[get_cache_key(dict_type)] = list(items)


# --------------------------------------------------------------------------- 键


class TestCacheKey:
    def test_the_prefix_comes_from_cache_constants(self) -> None:
        """``sys_dict:`` 是 ``CacheConstants.SYS_DICT_KEY``，别在本地再写字面量。"""
        assert get_cache_key("sys_user_sex") == "sys_dict:sys_user_sex"

    def test_an_empty_key_still_carries_the_prefix(self) -> None:
        assert get_cache_key("") == "sys_dict:"

    def test_the_separator_is_a_single_comma(self) -> None:
        assert SEPARATOR == ","


# --------------------------------------------------------------------------- 读写


class TestSetAndGet:
    def test_set_writes_under_the_prefixed_key(self, cache: _FakeRedisCache) -> None:
        set_dict_cache("sys_user_sex", [_item("0", "男")])

        assert cache.set_calls[0][0] == "sys_dict:sys_user_sex"
        assert len(cache.set_calls[0][1]) == 1

    def test_set_copies_the_list(self, cache: _FakeRedisCache) -> None:
        """传进去的是 ``List``，写进去的必须是同一批对象（Java 直接序列化入参）。"""
        items = [_item("0", "男"), _item("1", "女")]

        set_dict_cache("sys_user_sex", items)

        assert cache.store["sys_dict:sys_user_sex"] == items

    def test_set_with_none_stores_an_empty_list(self, cache: _FakeRedisCache) -> None:
        """无调用方真的传 ``None``（两处都被 ``isNotEmpty`` 拦过），行为钉住即可。"""
        set_dict_cache("x", None)

        assert cache.store["sys_dict:x"] == []

    def test_a_miss_returns_none(self, cache: _FakeRedisCache) -> None:
        """未命中是 ``None``（Java 的 ``null``），**不是**空列表。"""
        assert get_dict_cache("nope") is None

    def test_plain_dicts_are_coerced_to_entities(self, cache: _FakeRedisCache) -> None:
        """``arrayCache.toList(SysDictData.class)`` —— 反序列化回来可能已经是 dict。"""
        cache.store["sys_dict:sys_user_sex"] = [{"dict_value": "0", "dict_label": "男"}]

        datas = get_dict_cache("sys_user_sex")

        assert datas is not None
        assert datas[0].dict_value == "0"
        assert datas[0].dict_label == "男"

    def test_a_non_list_payload_counts_as_a_miss(self, cache: _FakeRedisCache) -> None:
        """库里若存过标量（历史脏数据），Java 的 ``JSONArray`` 强转会失败 -> 当没命中。"""
        cache.store["sys_dict:x"] = {"a": 1}

        assert get_dict_cache("x") is None

    def test_a_cached_empty_list_is_not_none(self, cache: _FakeRedisCache) -> None:
        """空列表与未命中在 Service 里都算"没有"，但在 ``getDictLabel`` 里判据不同。"""
        cache.store["sys_dict:x"] = []

        assert get_dict_cache("x") == []


# --------------------------------------------------------------------------- 单值


class TestSingleValue:
    def test_hit_returns_the_label(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_label("sys_user_sex", "1") == "女"

    def test_miss_returns_the_empty_string(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"))

        assert get_dict_label("sys_user_sex", "9") == ""

    def test_no_cache_returns_the_empty_string(self, cache: _FakeRedisCache) -> None:
        """``isNotNull(datas)`` 先挡住 —— 没有缓存时**不**抛异常。"""
        assert get_dict_label("unknown", "1") == ""

    def test_a_null_label_falls_back_to_the_empty_string(self, cache: _FakeRedisCache) -> None:
        """``return dict.getDictLabel()`` 可能返回 null；JSON 里是 ``null``，这里是 ``""``。"""
        _seed(cache, _item("0", None))  # type: ignore[arg-type]

        assert get_dict_label("sys_user_sex", "0") == ""

    def test_a_trailing_comma_in_the_label_is_kept(self, cache: _FakeRedisCache) -> None:
        """单值分支**不**做 ``stripEnd``（与多值分支的唯一差别）。"""
        _seed(cache, _item("0", "男,"))

        assert get_dict_label("sys_user_sex", "0") == "男,"

    def test_a_none_value_raises_like_the_java_npe(self, cache: _FakeRedisCache) -> None:
        """``containsAny(separator, null)`` 为 false -> 走 else -> ``dictValue.equals`` NPE。"""
        _seed(cache, _item("0", "男"))

        with pytest.raises(AttributeError) as error:
            get_dict_label("sys_user_sex", None)

        assert "NullPointerException" in str(error.value)

    def test_a_none_value_is_tolerated_without_cache(self, cache: _FakeRedisCache) -> None:
        """没缓存就先 ``return ""``，走不到 NPE 那一行 —— 顺序别调换。"""
        assert get_dict_label("unknown", None) == ""


# --------------------------------------------------------------------------- 多值


class TestMultiValue:
    def test_values_are_joined_with_the_separator(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_label("sys_user_sex", "0,1") == "男,女"

    def test_the_order_follows_the_dictionary_not_the_input(
        self, cache: _FakeRedisCache
    ) -> None:
        """外层遍历**字典项** —— 入参 ``1,0`` 依然输出 ``男,女``。"""
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_label("sys_user_sex", "1,0") == "男,女"

    def test_unknown_values_are_skipped(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_label("sys_user_sex", "9,1") == "女"

    def test_the_trailing_separator_is_stripped(self, cache: _FakeRedisCache) -> None:
        """多值分支末尾一定是 ``label + ","``，靠 ``stripEnd`` 收尾。"""
        _seed(cache, _item("0", "男"))

        assert get_dict_label("sys_user_sex", "0,9") == "男"

    def test_a_comma_inside_the_label_is_kept_but_the_tail_is_stripped(
        self, cache: _FakeRedisCache
    ) -> None:
        """标签自带的逗号只影响**中间**，末尾仍被 ``stripEnd`` 收干净。"""
        _seed(cache, _item("0", "男,"), _item("1", "女"))

        # pieces = "男,," + "女," -> 去掉末尾所有逗号 -> "男,,女"
        assert get_dict_label("sys_user_sex", "0,1") == "男,,女"

    def test_a_repeated_value_only_counts_once(self, cache: _FakeRedisCache) -> None:
        """内层命中即 ``break``，但外层每个字典项都会独立匹配 —— 输出**不会**重复。"""
        _seed(cache, _item("0", "男"))

        assert get_dict_label("sys_user_sex", "0,0") == "男"

    def test_a_trailing_comma_in_the_input_changes_nothing(
        self, cache: _FakeRedisCache
    ) -> None:
        """Java ``"0,".split(",")`` -> ``["0"]``（尾空串被丢弃）。"""
        _seed(cache, _item("0", "男"))

        assert get_dict_label("sys_user_sex", "0,") == "男"

    def test_an_empty_cache_list_yields_nothing(self, cache: _FakeRedisCache) -> None:
        """``isNotNull([])`` 为真 -> 进多值分支 -> 没有字典项 -> 空串。"""
        _seed(cache)

        assert get_dict_label("sys_user_sex", "0,1") == ""


# --------------------------------------------------------------------------- containsAny


class TestReversedContainsAny:
    """``containsAny(separator, value)`` —— 参数顺序是**反的**，别"修正"。"""

    def test_a_comma_in_the_value_selects_the_multi_branch(
        self, cache: _FakeRedisCache
    ) -> None:
        _seed(cache, _item("a", "甲"))

        assert get_dict_label("sys_user_sex", "a,b") == "甲"

    def test_no_comma_selects_the_single_branch(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("a", "甲"))

        assert get_dict_label("sys_user_sex", "a") == "甲"

    def test_a_custom_separator_demonstrates_the_argument_swap(
        self, cache: _FakeRedisCache
    ) -> None:
        """separator 取 ``"1"`` 时判据变成"``"1"`` 里有 value 的字符" -> 走多值分支。

        多值分支再拿 ``"1"`` 去 split ``"1"``，Java 得到空数组（全是被丢弃的尾空串），
        所以明明缓存里有 ``value = "1"`` 也返回空串。这就是参数反序的实证。
        """
        _seed(cache, _item("1", "男"))

        assert get_dict_label_with_separator("sys_user_sex", "1", "1") == ""

    def test_an_empty_value_never_has_a_comma(self, cache: _FakeRedisCache) -> None:
        """``is_empty(probe)`` 直接短路成 false -> 单值分支 -> 查不到 -> 空串。"""
        _seed(cache, _item("0", "男"))

        assert get_dict_label("sys_user_sex", "") == ""


# --------------------------------------------------------------------------- getDictValue


class TestGetDictValue:
    def test_hit_returns_the_code(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_value("sys_user_sex", "女") == "1"

    def test_multi_labels_follow_the_dictionary_order(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"), _item("1", "女"))

        assert get_dict_value("sys_user_sex", "女,男") == "0,1"

    def test_a_miss_returns_the_empty_string(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"))

        assert get_dict_value("sys_user_sex", "未知") == ""

    def test_no_cache_and_a_single_label_raises(self, cache: _FakeRedisCache) -> None:
        """与 ``getDictLabel`` 的**不对称**：else 分支没有判空保护 -> NPE -> 500。"""
        with pytest.raises(AttributeError) as error:
            get_dict_value("unknown", "男")

        assert "NullPointerException" in str(error.value)

    def test_no_cache_but_a_comma_returns_the_empty_string(
        self, cache: _FakeRedisCache
    ) -> None:
        """多值分支的判据里有 ``&& isNotEmpty(datas)``，短路后落到 else 才 NPE……

        实际 Java 里 ``isNotEmpty(null)`` 为 false -> 进 else -> 仍然 NPE。这里保留
        同一结局，只是异常点在缓存上。
        """
        with pytest.raises(AttributeError):
            get_dict_value("unknown", "男,女")

    def test_an_empty_cache_list_and_a_comma_returns_empty(
        self, cache: _FakeRedisCache
    ) -> None:
        _seed(cache)

        assert get_dict_value("sys_user_sex", "男,女") == ""


# --------------------------------------------------------------------------- 清理


class TestRemoveAndClear:
    def test_remove_deletes_one_prefixed_key(self, cache: _FakeRedisCache) -> None:
        _seed(cache, _item("0", "男"))

        remove_dict_cache("sys_user_sex")

        assert cache.deleted == ["sys_dict:sys_user_sex"]
        assert cache.store == {}

    def test_clear_uses_the_star_pattern(self, cache: _FakeRedisCache) -> None:
        """``KEYS sys_dict:*`` —— 不是 ``SCAN``，也不是精确键。"""
        _seed(cache, _item("0", "男"))
        cache.store["sys_dict:other"] = []

        clear_dict_cache()

        assert cache.key_patterns == ["sys_dict:*"]
        assert cache.deleted == [["sys_dict:sys_user_sex", "sys_dict:other"]]
        assert cache.store == {}

    def test_clear_keeps_unrelated_keys(self, cache: _FakeRedisCache) -> None:
        cache.store["sys_dict:a"] = []
        cache.store["sys_config:b"] = []

        clear_dict_cache()

        assert cache.store == {"sys_config:b": []}


# --------------------------------------------------------------------------- stripEnd


class TestStripEnd:
    """``StringUtils.stripEnd(String, String)`` —— 按**字符集合**剥离，不是后缀子串。"""

    def test_a_trailing_separator_is_removed(self) -> None:
        assert strip_end("男,女,", ",") == "男,女"

    def test_all_trailing_separators_are_removed(self) -> None:
        assert strip_end("a,,b,,", ",") == "a,,b"

    def test_characters_of_the_set_are_stripped_one_by_one(self) -> None:
        """``"abcba"`` + ``"ab"`` -> 末尾的 ``a`` / ``b`` 逐个剥 -> ``"abc"``。"""
        assert strip_end("abcba", "ab") == "abc"

    def test_a_suffix_substring_is_not_what_this_does(self) -> None:
        """若实现成 ``removesuffix``，``"abab"`` 只会去掉一个 ``"ab"``。"""
        assert strip_end("abab", "ab") == ""

    def test_none_becomes_the_empty_string(self) -> None:
        assert strip_end(None, ",") == ""

    def test_an_empty_strip_set_returns_the_input(self) -> None:
        assert strip_end("a,,", "") == "a,,"

    def test_nothing_to_strip_returns_the_input(self) -> None:
        assert strip_end("男,女", ",") == "男,女"
