"""字典类型 service（含字典缓存）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDictTypeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictTypeServiceImpl.java

``ISysDictTypeService`` 共 11 个方法，本模块**全部迁移**。它是整个字典体系的入口：
读缓存（:mod:`app.common.utils.dict_utils`）、写完后清缓存、改类型名时同步子表。

两个 mapper 依赖
----------------
``dictTypeMapper`` + ``dictDataMapper`` —— 后者用于
``countDictDataByType``（删类型前判"是否已分配"）和
``updateDictDataType``（改类型名时同步子项）。

三个必须照抄的行为
------------------

``updateDictType`` 是"先改子表，再改主表"
    顺序不能换。它也是 Java 里唯一带 ``@Transactional`` 的方法 —— 两条 update
    必须原子。**Python 侧目前没有事务包装**（``COMPATIBILITY.md`` §28.3），
    所以第二步失败时子表已经被改了。这是已知缺口，不在本切片修复。

``deleteDictTypeByIds`` **没有** ``@Transactional``
    逐个校验、遇到已分配就抛 ``CustomException``。注意它**不是**
    "先全查完再删"：Java 是"边查边删都不删"（先全查，再一次性删）。顺序：
    ``for`` 里只做校验，循环结束后才真正 ``deleteDictTypeByIds``。

``checkDictTypeUnique`` 返回字符串
    ``"1"`` = 已存在（``NOT_UNIQUE_OLD``），``"0"`` = 可用（``UNIQUE_OLD``）。
    ``-1L`` 那一步把"新增"统一成"和自己比"。

``init()`` 与 ``@PostConstruct``
--------------------------------
Java 在容器启动后遍历所有字典类型，把每个类型的 ``status='0'`` 子项预热进 Redis
（见 :meth:`init`）。Python 侧**保留方法但不自动调用**：本工程的数据源是惰性创建的
（``app.main`` 的说明），启动期连库会让"没有数据库也能起来做健康检查"这条能力失效。

语义上没有损失：``select_dict_data_by_type`` 在缓存未命中时会回源查库并写回，
与 ``init()`` 写进去的内容来自**同一条 SQL**，所以"启动预热"只是性能优化，
不是行为差异。见 ``COMPATIBILITY.md`` §32。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.common.constant import user_constants as UserConstants
from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.exception.exceptions import CustomException
from app.common.utils import dict_utils as DictUtils
from app.common.utils.string_utils import is_empty, is_not_empty
from app.system.mapper.sys_dict_data_mapper import SysDictDataMapper
from app.system.mapper.sys_dict_type_mapper import SysDictTypeMapper


class SysDictTypeService:
    """Java: ``ISysDictTypeService`` (impl: ``SysDictTypeServiceImpl``)."""

    def __init__(
        self,
        dict_type_mapper: Optional[SysDictTypeMapper] = None,
        dict_data_mapper: Optional[SysDictDataMapper] = None,
    ) -> None:
        self._dict_type_mapper = dict_type_mapper or SysDictTypeMapper()
        self._dict_data_mapper = dict_data_mapper or SysDictDataMapper()

    @property
    def dict_type_mapper(self) -> SysDictTypeMapper:
        return self._dict_type_mapper

    @property
    def dict_data_mapper(self) -> SysDictDataMapper:
        return self._dict_data_mapper

    # Java: @PostConstruct public void init()
    def init(self) -> None:
        """项目启动时把字典预热进缓存（Java 由 ``@PostConstruct`` 触发）。

        Python 侧不自动调用，理由见模块 docstring。手动作法::

            from app.system.service.sys_dict_type_service import get_dict_type_service
            get_dict_type_service().init()
        """
        for dict_type in self._dict_type_mapper.select_dict_type_all():
            dict_datas = self._dict_data_mapper.select_dict_data_by_type(dict_type.dict_type)
            DictUtils.set_dict_cache(dict_type.dict_type, dict_datas)

    # Java: List<SysDictType> selectDictTypeList(SysDictType dictType)
    def select_dict_type_list(self, dict_type: SysDictType) -> List[SysDictType]:
        """分页由调用方的 ``startPage()`` + mapper 的 ``take_page`` 完成。"""
        return self._dict_type_mapper.select_dict_type_list(dict_type)

    # Java: List<SysDictType> selectDictTypeAll()
    def select_dict_type_all(self) -> List[SysDictType]:
        return self._dict_type_mapper.select_dict_type_all()

    # Java: List<SysDictData> selectDictDataByType(String dictType)
    def select_dict_data_by_type(self, dict_type: Optional[str]) -> Optional[List[SysDictData]]:
        """先查缓存，未命中回源查库并写回；库里也没有就返回 ``None``。

        注意返回的是 ``None`` 而不是空列表 —— 上层
        :class:`~app.api.system.sys_dict_data_controller` 会用
        ``StringUtils.isNull(data)`` 判断并换成空数组，那一步必须在控制器里做。
        """
        dict_datas = DictUtils.get_dict_cache(dict_type)
        if is_not_empty(dict_datas):
            return dict_datas
        dict_datas = self._dict_data_mapper.select_dict_data_by_type(dict_type)
        if is_not_empty(dict_datas):
            DictUtils.set_dict_cache(dict_type, dict_datas)
            return dict_datas
        return None

    # Java: List<SysDictData> selectDictDataByTypeMore(String dictType)
    def select_dict_data_by_type_more(self, dict_type: Optional[str]) -> Optional[List[SysDictData]]:
        """多类型查询（``"a,b"``），缓存键就是**原始入参**。

        三段照抄，其中有两处是"看起来像 bug 的原文"：

        1. 入参为空 -> 兜底成 ``"-dadadadas"``（一个永远查不到的类型名）。
           两句 ``isEmpty`` 判空是**重复**的：中间那段不可能把它变空，第二句是死代码。
        2. ``endsWith(",")`` 之后调的 ``substring(0, dictType.length())``
           **等于原样返回** —— 尾逗号根本没被去掉。于是缓存键里带着尾逗号
           （``"a,b,"``），与 :meth:`select_dict_data_by_type` 的 ``"a,b"`` 是两个键。

        这两处都照抄。真要清理，得先确认库里的历史缓存键，否则会把不同键的
        缓存内容混在一起。
        """
        if is_empty(dict_type):
            dict_type = "-dadadadas"
        else:
            assert dict_type is not None
            if dict_type.endswith(","):
                # Java: dictType = dictType.substring(0, dictType.length());  <- 空操作
                dict_type = dict_type[0 : len(dict_type)]
        # Java 里这里还有一次 isEmpty 判断 —— 死代码，照留
        if is_empty(dict_type):
            dict_type = "-dadadadas"

        dict_datas = DictUtils.get_dict_cache(dict_type)
        if is_not_empty(dict_datas):
            return dict_datas
        dict_datas = self._dict_data_mapper.select_dict_data_by_type_more(dict_type)
        if is_not_empty(dict_datas):
            DictUtils.set_dict_cache(dict_type, dict_datas)
            return dict_datas
        return None

    # Java: SysDictType selectDictTypeById(Long dictId)
    def select_dict_type_by_id(self, dict_id: int) -> Optional[SysDictType]:
        return self._dict_type_mapper.select_dict_type_by_id(dict_id)

    # Java: SysDictType selectDictTypeByType(String dictType)
    def select_dict_type_by_type(self, dict_type: Optional[str]) -> Optional[SysDictType]:
        return self._dict_type_mapper.select_dict_type_by_type(dict_type)

    # Java: int deleteDictTypeByIds(Long[] dictIds)
    def delete_dict_type_by_ids(self, dict_ids: Sequence[int]) -> int:
        """先逐个体检"这个类型下面还有没有字典数据"，有就整批拒绝。

        Java 先 ``selectDictTypeById`` 再 ``countDictDataByType``，且异常文案里用的是
        ``dictType.getDictName()``。类型不存在时 Java 会在 ``getDictType()`` 处 NPE
        （同样是 500，只是文案变成 NPE 描述），这里用 ``AttributeError`` 等价复刻。
        """
        for dict_id in dict_ids:
            dict_type = self.select_dict_type_by_id(dict_id)
            if self._dict_data_mapper.count_dict_data_by_type(_none_guard(dict_type).dict_type) > 0:
                # Java: throw new CustomException(String.format("%1$s已分配,不能删除", dictType.getDictName()))
                raise CustomException(f"{dict_type.dict_name}已分配,不能删除")
        count = self._dict_type_mapper.delete_dict_type_by_ids(dict_ids)
        if count > 0:
            DictUtils.clear_dict_cache()
        return count

    # Java: void clearCache()
    def clear_cache(self) -> None:
        """``DELETE /system/dict/type/clearCache`` -> 只清缓存，不动库。"""
        DictUtils.clear_dict_cache()

    # Java: int insertDictType(SysDictType dictType)
    def insert_dict_type(self, dict_type: SysDictType) -> int:
        row = self._dict_type_mapper.insert_dict_type(dict_type)
        if row > 0:
            DictUtils.clear_dict_cache()
        return row

    # Java: @Transactional int updateDictType(SysDictType dictType)
    def update_dict_type(self, dict_type: SysDictType) -> int:
        """先按 id 查出**旧**类型名，用它把子表数据一起改名，再改主表。

        Java 带 ``@Transactional``；本工程没有事务包装，两步之间没有回滚能力
        （``COMPATIBILITY.md`` §28.3 / §32）。
        """
        old_dict = self._dict_type_mapper.select_dict_type_by_id(_none_guard(dict_type).dict_id)
        self._dict_data_mapper.update_dict_data_type(
            _none_guard(old_dict).dict_type, dict_type.dict_type
        )
        row = self._dict_type_mapper.update_dict_type(dict_type)
        if row > 0:
            DictUtils.clear_dict_cache()
        return row

    # Java: String checkDictTypeUnique(SysDictType dict)
    def check_dict_type_unique(self, dict_type: SysDictType) -> str:
        """``"1"`` = 已存在，``"0"`` = 可用（``NOT_UNIQUE_OLD`` / ``UNIQUE_OLD``）。"""
        dict_id = -1 if dict_type.dict_id is None else dict_type.dict_id
        info = self._dict_type_mapper.check_dict_type_unique(dict_type.dict_type)
        if info is not None and info.dict_id != dict_id:
            return UserConstants.NOT_UNIQUE_OLD
        return UserConstants.UNIQUE_OLD


def _none_guard(value):
    """Java 在这些位置没有判空，直接解引用 -> NPE（500）。这里让同样的 500 出现。"""
    if value is None:
        raise AttributeError("java.lang.NullPointerException: value is null")
    return value


_SERVICE: Optional[SysDictTypeService] = None


def get_dict_type_service() -> SysDictTypeService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysDictTypeService()
    return _SERVICE


def reset_dict_type_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysDictTypeService",
    "get_dict_type_service",
    "reset_dict_type_service",
]
