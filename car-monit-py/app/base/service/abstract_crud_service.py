"""``base`` 包「代码生成器模板」Service 的公共骨架.

# Migrated from: (no single Java source) -- faithful re-implementation of the
#   ``ruoyi-generator`` template that produced every ``<Table>ServiceImpl`` in
#   ``com.ruoyi.base.service.impl``.

为什么有这个文件
----------------
``base`` 包里有 10 个 ServiceImpl 是**同一段模板代码**，逐字相同：

.. code-block:: java

    public AjaxResult saveXxx(Xxx x) {
        if (CommonUtil.isNotBlank(x.getId())) {   // 数值主键是 null != x.getId()
            xxxMapper.updateById(x);              // 修改
        } else {
            xxxMapper.insert(x);                  // 新增 主键
        }
        return AjaxResult.success("操作成功！", x.getId());
    }

    public AjaxResult deleteXxxByIds(String[] ids) {
        int count = xxxMapper.deleteXxxByIds(ids);
        return AjaxResult.success(count);
    }

    public void truncateTable() { xxxMapper.truncateTable(); }

把这段写在一处（等价于 Java 的 ``ServiceImpl<M, E>`` 提供的通用部分），每个
ServiceImpl 只声明"我用哪个 Mapper、主键叫什么、判空用哪一条"，20 份复制粘贴
就不会各自漂移 —— 与 Mapper 层 :class:`~app.base.mapper.ods_sql.OdsListMapper`
的处理方式一致。

两条必须照抄的差异
------------------
1. **主键判空有两种写法**：``String`` 主键用 ``CommonUtil.isNotBlank``（空串也算
   "空"，走 insert）；``Integer`` 主键（``Geometry``）用 ``null != id``（``0``
   算"有值"，走 update）。所以 ``blank_check`` 是逐模块声明的。
2. **返回值**：``AjaxResult.success(msg, data)`` 在 ``data`` 为 ``null`` 时
   **不带** ``data`` 键 —— :class:`~app.common.core.domain.ajax_result.AjaxResult`
   已经实现了这一点，这里只负责传值。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.common_util import is_not_blank
from app.common.utils.string_utils import is_not_blank as string_is_not_blank

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"


class AbstractCrudService:
    """Java: ``class XxxServiceImpl extends ServiceImpl<XxxMapper, Xxx>`` 的公共部分."""

    #: 子类必须赋值为具体的 Mapper 类。
    mapper_cls: Any = None
    #: 主键属性名（snake_case），同时是 Mapper 的 ``id_column``。
    id_attribute: str = "id"
    #: ``True`` = ``CommonUtil.isNotBlank(id)``；``False`` = ``null != id``。
    blank_check: bool = True

    def __init__(self, mapper: Any = None) -> None:
        self._mapper = mapper if mapper is not None else self.mapper_cls()

    # ---------------------------------------------------------------- 查询

    # Java: Xxx selectXxxById(<pk type> pk)
    def select_by_id(self, entity_id: Any) -> Optional[Any]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<Xxx> selectXxxList(Xxx x)
    def select_list(self, query: Any) -> List[Any]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveXxx(Xxx x)  —— 新增与修改共用一个入口
    def save(self, entity: Any) -> AjaxResult:
        """``id`` 有值 -> ``updateById``；否则 -> ``insert``。两种情况的返回体相同。"""
        current_id = getattr(entity, self.id_attribute, None)
        if self._has_primary_key(current_id):
            self._mapper.update_by_id(entity)
        else:
            self._mapper.insert(entity)
        return AjaxResult.success_message_data(
            SAVE_SUCCESS_MESSAGE, getattr(entity, self.id_attribute, None)
        )

    def _has_primary_key(self, current_id: Any) -> bool:
        if current_id is None:
            return False
        if self.blank_check:
            return string_is_not_blank(current_id) and is_not_blank(current_id)
        return True

    # Java: boolean saveBatch(Collection<T> entityList)
    def save_batch(self, entity_list: Sequence[Any]) -> bool:
        """MP 的 ``saveBatch`` —— 逐条插入。

        MP 内部走 ``ExecutorType.BATCH`` 分组提交，但每行经过的填充逻辑
        （``MetaObjectFiller``）与逐条 ``insert`` 完全一致，所以这里用循环表达，
        生成的 SQL 与结果集相同。返回值恒为 ``True``（与 MP 一致：抛异常才算失败）。

        调用点：``VehicleMonitoringTask`` 的 7 个 ``syncXxxInfo`` 都是
        ``truncateTable(); saveBatch(list);``（见 :mod:`app.quartz.task`）。
        """
        for entity in entity_list:
            self._mapper.insert(entity)
        return True

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteXxxByIds(String[] ids)
    def delete_by_ids(self, entity_ids: Sequence[Any], mapper_method: str) -> AjaxResult:
        """``mapper_method`` 是 XML 语句名转成的 snake_case 方法名（如
        ``delete_ods_szdn_section_by_ids``）—— 每个 XML 的语句 id 不同，
        不能像 MyBatis 那样按参数类型分派，所以显式传进来。
        """
        count = getattr(self._mapper, mapper_method)(entity_ids)
        return AjaxResult.success_data(count)


__all__ = ["AbstractCrudService", "SAVE_SUCCESS_MESSAGE"]
