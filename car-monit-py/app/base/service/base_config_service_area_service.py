"""服务区 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IBaseConfigServiceAreaService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/BaseConfigServiceAreaServiceImpl.java

Java 是 ``ServiceImpl<Mapper, Entity>`` —— 除了 XML 语句，还能用 ``BaseMapper`` 的
``insert`` / ``updateById``。这里把两者组合起来，逻辑逐行照抄：

* ``saveBaseConfigServiceArea``：``id`` 非空 -> ``updateById``，否则 ``insert``；
  两种情况的返回体**完全一样** —— ``AjaxResult.success("操作成功！", id)``。
* ``deleteBaseConfigServiceAreaByIds``：物理删除，返回 ``AjaxResult.success(count)``。

``@Transactional(rollbackFor = Exception.class)`` 未复刻（与其它切片一致，见
``COMPATIBILITY.md`` §28.3）：单语句方法本身没有原子性问题，多语句方法才有。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.base.domain.base_config_service_area import BaseConfigServiceArea
from app.base.mapper.base_config_service_area_mapper import BaseConfigServiceAreaMapper
from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.string_utils import is_not_blank

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"


class BaseConfigServiceAreaService:
    """Java: ``class BaseConfigServiceAreaServiceImpl``."""

    def __init__(self, mapper: Optional[BaseConfigServiceAreaMapper] = None) -> None:
        self._mapper = mapper or BaseConfigServiceAreaMapper()

    # Java: selectBaseConfigServiceAreaById(String fwqbm)
    def select_by_id(self, fwqbm: str) -> Optional[BaseConfigServiceArea]:
        return self._mapper.select_by_fwqbm(fwqbm)

    # Java: selectBaseConfigServiceAreaList(BaseConfigServiceArea x)
    def select_list(self, query: BaseConfigServiceArea) -> List[BaseConfigServiceArea]:
        """返回 ``PageList``（``List`` 子类），供 ``get_data_table`` 取分页元数据。"""
        return self._mapper.select_list(query)

    # Java: AjaxResult saveBaseConfigServiceArea(BaseConfigServiceArea x)
    def save(self, entity: BaseConfigServiceArea) -> AjaxResult:
        """新增或修改 —— 判据是 ``CommonUtil.isNotBlank(id)``，空串也算"空"。"""
        if is_not_blank(entity.id):
            self._mapper.update_by_id(entity)
        else:
            self._mapper.insert(entity)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # Java: AjaxResult deleteBaseConfigServiceAreaByIds(String[] fwqbms)
    def delete_by_ids(self, fwqbms: Sequence[str]) -> AjaxResult:
        return AjaxResult.success_data(self._mapper.delete_by_fwqbms(fwqbms))

    # Java: AjaxResult deleteBaseConfigServiceAreaById(String fwqbm)（无控制器调用方）
    def delete_by_id(self, fwqbm: str) -> AjaxResult:
        """按原则第 4 条照留：XML 有、控制器没调，但方法存在。"""
        return AjaxResult.success_data(self._mapper.delete_by_fwqbm(fwqbm))


_SERVICE: Optional[BaseConfigServiceAreaService] = None


def get_base_config_service_area_service() -> BaseConfigServiceAreaService:
    """Java: ``@Autowired IBaseConfigServiceAreaService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = BaseConfigServiceAreaService()
    return _SERVICE


def reset_base_config_service_area_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "BaseConfigServiceAreaService",
    "SAVE_SUCCESS_MESSAGE",
    "get_base_config_service_area_service",
    "reset_base_config_service_area_service",
]
