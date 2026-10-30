"""字典数据 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDictDataService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java

``ISysDictDataService`` 共 8 个方法，本模块**全部迁移**。

所有写操作都是"写库 + 清缓存"
------------------------------
``insertDictData`` / ``updateDictData`` / ``deleteDictDataByIds`` 三处都是::

    int row = mapper.xxx(...);
    if (row > 0) { DictUtils.clearDictCache(); }

注意清的是**整个**字典缓存（``sys_dict:*`` 全删），不是只删本类型 —— 因为
``updateDictData`` 可能改了 ``dictType`` 字段，Java 侧干脆全清。照抄。

``selectDictDataMap`` / ``selectDictDataLaleMap`` 是给业务模块用的
---------------------------------------------------------------
它们没有对应的控制器端点，是 ``manager`` / ``base`` 包里那些导出/详情接口的辅助方法
（例如 ``CarExceptRecordController`` 用 ``selectDictDataMap("car_type")`` 把编码翻成中文）。

两个方法的区别只有键值方向：

    selectDictDataMap      {dictValue: dictLabel}   -> 编码查中文
    selectDictDataLaleMap  {dictLabel: dictValue}   -> 中文查编码（方法名里 Lale 是 Label 的笔误）

**没有走缓存**：它们直接 ``selectDictDataList`` 查库（``status`` 不过滤，停用项也在
映射表里）。这与 ``DictUtils.getDictLabel`` 走缓存是两条路，别合并。

``Collectors.toMap`` 遇到重复键会抛异常
---------------------------------------
Java 的 ``stream().collect(Collectors.toMap(...))`` 在**重复键**时抛
``IllegalStateException: Duplicate key ...``（HTTP 500）。Python 的字典推导会静默
后者覆盖前者 —— 那会让"同一类型下两条相同 dictValue"的数据质量错误变成"看不出来"。
所以这里显式检测并抛 ``AttributeError``（消息里带 ``IllegalStateException``），
与 :mod:`app.system.mapper.sys_dict_data_mapper` 处理 ``TooManyResultsException``
的方式一致。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.utils import dict_utils as DictUtils
from app.system.mapper.sys_dict_data_mapper import SysDictDataMapper


class SysDictDataService:
    """Java: ``ISysDictDataService`` (impl: ``SysDictDataServiceImpl``)."""

    def __init__(self, mapper: Optional[SysDictDataMapper] = None) -> None:
        self._mapper = mapper or SysDictDataMapper()

    @property
    def mapper(self) -> SysDictDataMapper:
        return self._mapper

    # Java: List<SysDictData> selectDictDataList(SysDictData dictData)
    def select_dict_data_list(self, dict_data: SysDictData) -> List[SysDictData]:
        """分页与否取决于调用方有没有 ``startPage()``（见 mapper 的说明）。"""
        return self._mapper.select_dict_data_list(dict_data)

    # Java: String selectDictLabel(String dictType, String dictValue)
    def select_dict_label(self, dict_type: Optional[str], dict_value: Optional[str]) -> Optional[str]:
        """**直接查库**，不读缓存；相同 ``(type, value)`` 多于一行时抛异常。"""
        return self._mapper.select_dict_label(dict_type, dict_value)

    # Java: SysDictData selectDictDataById(Long dictCode)
    def select_dict_data_by_id(self, dict_code: int) -> Optional[SysDictData]:
        return self._mapper.select_dict_data_by_id(dict_code)

    # Java: int deleteDictDataByIds(Long[] dictCodes)
    def delete_dict_data_by_ids(self, dict_codes: Sequence[int]) -> int:
        row = self._mapper.delete_dict_data_by_ids(dict_codes)
        if row > 0:
            DictUtils.clear_dict_cache()
        return row

    # Java: int insertDictData(SysDictData dictData)
    def insert_dict_data(self, dict_data: SysDictData) -> int:
        row = self._mapper.insert_dict_data(dict_data)
        if row > 0:
            DictUtils.clear_dict_cache()
        return row

    # Java: int updateDictData(SysDictData dictData)
    def update_dict_data(self, dict_data: SysDictData) -> int:
        row = self._mapper.update_dict_data(dict_data)
        if row > 0:
            DictUtils.clear_dict_cache()
        return row

    # Java: public Map<String,String> selectDictDataMap(String dictValue)
    def select_dict_data_map(self, dict_value: Optional[str]) -> Dict[str, str]:
        """``{dictValue: dictLabel}``；``dictValue`` 在这里是**字典类型**（命名照抄）。"""
        query = SysDictData()
        query.dict_type = dict_value
        dict_list = self._mapper.select_dict_data_list(query)
        result: Dict[str, str] = {}
        for item in dict_list:
            _put_unique(result, item.dict_value, item.dict_label)
        return result

    # Java: public Map<String,String> selectDictDataLaleMap(String dictValue)
    def select_dict_data_lale_map(self, dict_value: Optional[str]) -> Dict[str, str]:
        """``{dictLabel: dictValue}``；方法名里的 ``Lale`` 是 ``Label`` 的笔误，照抄。"""
        query = SysDictData()
        query.dict_type = dict_value
        dict_list = self._mapper.select_dict_data_list(query)
        result: Dict[str, str] = {}
        for item in dict_list:
            _put_unique(result, item.dict_label, item.dict_value)
        return result


def _put_unique(target: Dict[str, str], key: Optional[str], value: Optional[str]) -> None:
    """Java: ``Collectors.toMap`` —— 重复键抛 ``IllegalStateException``。

    注意 Python 里 ``dict`` 的键不能是 ``None`` 之外的问题都没关系，但 Java 的
    ``toMap`` 允许 ``null`` 值、不允许 ``null`` 键（``HashMap`` 允许，``toMap`` 的
    合并器也不会拒绝）—— 所以这里只拦"重复"，不拦 ``None``。
    实际列上 ``dict_value`` / ``dict_label`` 都可能为 ``null``，历史数据里存在，
    保持与 Java 同样的宽容度。
    """
    if key in target:
        raise AttributeError(
            "java.lang.IllegalStateException: Duplicate key "
            f"{key} (attempted merging values {target[key]} and {value})"
        )
    target[key] = value  # type: ignore[assignment]


_SERVICE: Optional[SysDictDataService] = None


def get_dict_data_service() -> SysDictDataService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysDictDataService()
    return _SERVICE


def reset_dict_data_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysDictDataService",
    "get_dict_data_service",
    "reset_dict_data_service",
]
