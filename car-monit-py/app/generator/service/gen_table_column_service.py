"""业务字段服务层.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableColumnService.java
# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableColumnServiceImpl.java

两个 ``...ByTableColumnIds`` 变体在**空列表时返回 ``None``**（不是空列表）
-------------------------------------------------------------------------
这是 Java 原实现，而且 ``None`` 会一路传到
``GenTableColumn#setDialogSearchColumnList(null)``，最终 JSON 里那个键是 ``null``
而不是 ``[]``。看着像笔误，但改成空列表会改变 ``/tool/gen/{id}`` 的响应体，
所以照抄，见 :meth:`GenTableColumnService.select_gen_table_column_list_by_table_column_ids`。

``selectGenTableColumnListByTableColumnIds`` 的入参是**逗号拼接的字符串**
-----------------------------------------------------------------------
``StringUtils.stringToList(tableColumnIds)`` 之后才交给 mapper。``None`` /
``""`` 都得到空列表 -> 返回 ``None``。注意 ``string_to_list`` 对 ``None`` 也是空列表，
所以 ``dialogSearchColumnIds`` 为空时不会落到 mapper（mapper 那条会拼 ``in ()``）。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.common.core.text.convert import to_long_array
from app.common.utils.string_utils import string_to_list
from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.mapper.gen_table_column_mapper import GenTableColumnMapper


class GenTableColumnService:
    """Java: ``IGenTableColumnService`` (impl: ``GenTableColumnServiceImpl``)."""

    def __init__(self, column_mapper: Optional[GenTableColumnMapper] = None) -> None:
        self._column_mapper = column_mapper or GenTableColumnMapper()

    @property
    def column_mapper(self) -> GenTableColumnMapper:
        return self._column_mapper

    # Java: List<GenTableColumn> selectGenTableColumnListByTableId(Long tableId)
    def select_gen_table_column_list_by_table_id(
        self, table_id: Optional[int]
    ) -> List[GenTableColumn]:
        """查询业务字段列表（``/tool/gen/column/{talbleId}`` 的唯一数据源）。"""
        return self._column_mapper.select_gen_table_column_list_by_table_id(table_id)

    # Java: List<GenTableColumn> selectGenTableColumnListByTableColumnIds(String tableColumnIds)
    def select_gen_table_column_list_by_table_column_ids(
        self, table_column_ids: Optional[str]
    ) -> Optional[List[GenTableColumn]]:
        """按逗号拼接的 id 串查字段；**空 -> ``None``**（Java 的
        ``CollectionUtils.isEmpty(idList)`` 就直接 ``return null``）。"""
        id_list = string_to_list(table_column_ids)
        if not id_list:
            return None
        return self._column_mapper.select_gen_table_column_list_by_table_column_ids(id_list)

    # Java: List<GenTableColumn> selectGenTableColumnListByTableColumnIdList(List<Long> tableColumnIdList)
    def select_gen_table_column_list_by_table_column_id_list(
        self, table_column_id_list: Optional[Sequence[Optional[int]]]
    ) -> Optional[List[GenTableColumn]]:
        """按 id 列表查字段；**空 -> ``None``**。元素先 ``String.valueOf`` 再交给 mapper。"""
        if not table_column_id_list:
            return None
        # Java: tableColumnIdList.stream().map(String::valueOf)
        # ``String.valueOf(null)`` 是字符串 "null"，MyBatis 会把它当普通文本参数
        column_id_string_list = ["null" if item is None else str(item) for item in table_column_id_list]
        return self._column_mapper.select_gen_table_column_list_by_table_column_ids(
            column_id_string_list
        )

    # Java: List<GenTableColumn> selectGenTableColumnList(GenTableColumn genTableColumn)
    def select_gen_table_column_list(
        self, gen_table_column: GenTableColumn
    ) -> List[GenTableColumn]:
        return self._column_mapper.select_gen_table_column_list(gen_table_column)

    # Java: int insertGenTableColumn(GenTableColumn genTableColumn)
    def insert_gen_table_column(self, gen_table_column: GenTableColumn) -> int:
        return self._column_mapper.insert_gen_table_column(gen_table_column)

    # Java: int updateGenTableColumn(GenTableColumn genTableColumn)
    def update_gen_table_column(self, gen_table_column: GenTableColumn) -> int:
        return self._column_mapper.update_gen_table_column(gen_table_column)

    # Java: int deleteGenTableColumnByIds(String ids)
    def delete_gen_table_column_by_ids(self, ids: Optional[str]) -> int:
        """``Convert.toLongArray(ids)`` —— ``None`` / ``""`` 得到空数组，
        随后 ``<foreach>`` 拼出 ``in ()`` 让 MySQL 报语法错（Java 同样如此）。"""
        return self._column_mapper.delete_gen_table_column_by_ids(to_long_array(ids))


#: Controller 侧的默认单例（Java: ``@Autowired`` 注入同一个 bean）。
_GEN_TABLE_COLUMN_SERVICE = GenTableColumnService()


def get_gen_table_column_service() -> GenTableColumnService:
    """取共享的 service 实例（测试可 ``reset`` 后换成带 mock mapper 的实例）."""
    return _GEN_TABLE_COLUMN_SERVICE


def reset_gen_table_column_service(service: Optional[GenTableColumnService] = None) -> None:
    """测试钩子：替换 / 还原模块级单例."""
    global _GEN_TABLE_COLUMN_SERVICE
    _GEN_TABLE_COLUMN_SERVICE = service or GenTableColumnService()


__all__ = [
    "GenTableColumnService",
    "get_gen_table_column_service",
    "reset_gen_table_column_service",
]
