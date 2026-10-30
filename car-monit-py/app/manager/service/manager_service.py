"""``manager`` 包「代码生成器模板」Service 的公共骨架.

# Migrated from: (no single Java source) -- faithful re-implementation of the
#   ``ruoyi-generator`` template that produced every ``<Table>ServiceImpl`` in
#   ``com.ruoyi.manager.service.impl``.

模板原文（``CarWarningRuleServiceImpl`` 等 8 份逐字相同）
-------------------------------------------------------

.. code-block:: java

    public AjaxResult saveXxx(Xxx x) {
        if (CommonUtil.isNotBlank(x.getId())) {   // 修改
            xxxMapper.updateById(x);
        } else {                                  // 新增 主键
            xxxMapper.insert(x);
        }
        cacheXxx();                               // 有的模块有，有的没有
        return AjaxResult.success("操作成功！", x.getId());
    }

    public AjaxResult deleteXxxByIds(String[] ids) {
        int count = xxxMapper.deleteXxxByIds(ids);
        return AjaxResult.success(count);
    }

与 ``base`` 包的 ``AbstractCrudService`` 的差异
-----------------------------------------------
1. 主键判空**统一**是 ``CommonUtil.isNotBlank(id)``（``String`` 主键；没有数值主键）；
2. 保存 / 删除之后可能刷新缓存 —— 用 :meth:`after_change` 钩子表达，
   默认空实现，有缓存的模块覆盖它（``CarWarningRule`` / ``CarWhiteInfo`` …）；
3. ``createBy`` / ``createTime`` / ``epsId`` 由 MP 的 ``MetaObjectFiller`` 填充，
   Python 侧对应 :class:`~app.base.mapper.plus_mapper.MetaObjectFiller`，
   Service 里**不**手写这四个字段。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.common_util import is_not_blank

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"


class ManagerCrudService:
    """Java: ``class XxxServiceImpl extends ServiceImpl<XxxMapper, Xxx>`` 的公共部分."""

    #: 子类必须赋值为具体的 Mapper 类。
    mapper_cls: Any = None

    def __init__(self, mapper: Any = None) -> None:
        self._mapper = mapper if mapper is not None else self.mapper_cls()

    # ---------------------------------------------------------------- 查询

    # Java: Xxx selectXxxById(String id)
    def select_by_id(self, entity_id: str) -> Optional[Any]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<Xxx> selectXxxList(Xxx x)
    def select_list(self, query: Any) -> List[Any]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveXxx(Xxx x)  —— 新增与修改共用一个入口
    def save(self, entity: Any) -> AjaxResult:
        if not is_not_blank(getattr(entity, "id", None)):
            self._mapper.insert(entity)
        else:
            self._mapper.update_by_id(entity)
        self.after_change()
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, getattr(entity, "id", None))

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteXxxByIds(String[] ids)
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        count = self._mapper.delete_by_ids(entity_ids)
        self.after_change()
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteXxxById(String id)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        self.after_change()
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 批量

    # Java: boolean saveBatch(Collection<T> entityList)
    def save_batch(self, entity_list: Sequence[Any]) -> bool:
        """MP 的 ``saveBatch`` —— 逐条插入。

        MP 内部走 ``ExecutorType.BATCH`` 分组提交，但每行经过的填充逻辑（
        ``MetaObjectFiller``）与逐条 ``insert`` 完全一致，所以这里用循环表达，
        生成的 SQL 与结果集相同。返回值恒为 ``True``（与 MP 一致：抛异常才算失败）。
        """
        for entity in entity_list:
            self._mapper.insert(entity)
        return True

    # Java: boolean updateBatchById(Collection<T> entityList)
    def update_batch_by_id(self, entity_list: Sequence[Any]) -> bool:
        """MP 的 ``updateBatchById`` —— 逐条 ``updateById``。"""
        for entity in entity_list:
            self._mapper.update_by_id(entity)
        return True

    # ---------------------------------------------------------------- 钩子

    def after_change(self) -> None:
        """保存 / 删除之后的缓存刷新（Java 里的 ``cacheXxx()``）。默认无操作。"""


__all__ = ["ManagerCrudService", "SAVE_SUCCESS_MESSAGE"]
