"""交易流水 Service 业务层处理（门架计费融合流水）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeGantryFusion01Service.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeGantryFusion01ServiceImpl.java

生成器模板的四段 CRUD，公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`。

**注意主键不对称**（原代码如此）：本实体没有 ``@TableId``，MyBatis-Plus 按字段名
自动把 ``id`` 当作主键（``ASSIGN_ID`` 雪花号），但 XML 的 ``selectXxxById`` /
``deleteXxxById`` 用的是业务键 ``big_id``。所以：

======================  ==========================
Java 调用               实际 WHERE 列
======================  ==========================
``saveXxx``（新增）      ``insert ... (id, ...)``
``saveXxx``（修改）      ``where id = ?``
``deleteXxxById``       ``where big_id = ?``
``selectXxxById``       ``where big_id = ?``
======================  ==========================
"""

from __future__ import annotations

from typing import Sequence

from app.base.mapper.ods_lwzxsfsj_fee_gantry_fusion01_mapper import (
    OdsLwzxsfsjFeeGantryFusion01Mapper,
)
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult
from app.config.database import transactional


class OdsLwzxsfsjFeeGantryFusion01Service(AbstractCrudService):
    """Java: ``class OdsLwzxsfsjFeeGantryFusion01ServiceImpl``."""

    mapper_cls = OdsLwzxsfsjFeeGantryFusion01Mapper
    #: Java: ``CommonUtil.isNotBlank(x.getId())`` —— 判的是 ``id`` 而不是 ``bigId``
    id_attribute = "id"

    # Java: AjaxResult deleteOdsLwzxsfsjFeeGantryFusion01ByIds(String[] bigIds)
    @transactional
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_lwzxsfsj_fee_gantry_fusion01_by_ids")


_SERVICE: OdsLwzxsfsjFeeGantryFusion01Service | None = None


def get_ods_lwzxsfsj_fee_gantry_fusion01_service() -> OdsLwzxsfsjFeeGantryFusion01Service:
    """Java: ``@Autowired IOdsLwzxsfsjFeeGantryFusion01Service``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsLwzxsfsjFeeGantryFusion01Service()
    return _SERVICE


def reset_ods_lwzxsfsj_fee_gantry_fusion01_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsLwzxsfsjFeeGantryFusion01Service",
    "get_ods_lwzxsfsj_fee_gantry_fusion01_service",
    "reset_ods_lwzxsfsj_fee_gantry_fusion01_service",
]
