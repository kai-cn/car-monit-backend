"""门架抓拍流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowAddcodeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowAddcodeServiceImpl.java

生成器模板的四段 CRUD（公共部分见
:class:`~app.base.service.abstract_crud_service.AbstractCrudService`）
＋ 大屏用的 ``getTopTen()`` 排行加工。

主键不对称（原代码如此）：``@TableId`` 是 ``big_id``，但 XML 的
``selectXxxById`` 过滤的是 ``datauuid``；删除语句过滤的是 ``big_id``。
"""

from __future__ import annotations

from typing import Any, List, Sequence

from app.base.mapper.ods_rt_szdn_snapshot_flow_addcode_mapper import (
    OdsRtSzdnSnapshotFlowAddcodeMapper,
)
from app.base.service.abstract_crud_service import AbstractCrudService
from app.common.core.domain.ajax_result import AjaxResult
from app.manager.domain.vo.bigscreen.top_ten_vo import TopTenVO
from app.config.database import transactional


def _java_string(value: Any) -> str:
    """Java 字符串拼接里 ``null`` 渲染成字面量 ``"null"``（``"a" + null`` -> ``"anull"``）."""
    return "null" if value is None else str(value)


class OdsRtSzdnSnapshotFlowAddcodeService(AbstractCrudService):
    """Java: ``class OdsRtSzdnSnapshotFlowAddcodeServiceImpl``."""

    mapper_cls = OdsRtSzdnSnapshotFlowAddcodeMapper
    #: Java: ``@TableId(value = "big_id", type = IdType.INPUT)``
    id_attribute = "big_id"

    # Java: AjaxResult deleteOdsRtSzdnSnapshotFlowAddcodeByIds(String[] bigIds)
    @transactional
    def delete_by_ids(self, ids: Sequence[str]) -> AjaxResult:  # type: ignore[override]
        return super().delete_by_ids(ids, "delete_ods_rt_szdn_snapshot_flow_addcode_by_ids")

    # Java: AjaxResult deleteOdsRtSzdnSnapshotFlowAddcodeById(String bigId)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        return AjaxResult.success_data(
            self._mapper.delete_ods_rt_szdn_snapshot_flow_addcode_by_id(entity_id)
        )

    # Java: List<TopTenVO> getTopTen()
    def get_top_ten(self) -> List[TopTenVO]:
        """把 SQL 结果加工成排行榜.

        Java 原文（逐行照抄）::

            int i = 1; Integer topOne = -1;
            for (TopTenVO vo : topTen) {
                vo.setSectionName(vo.getRoadCode() + " " + vo.getSectionName());
                if (i == 1) { vo.setRate("100"); topOne = vo.getCarNum(); }
                else if (topOne != -1) { vo.setRate((int)(Double.valueOf(vo.getCarNum()) / topOne * 100) + ""); }
                vo.setRank(i++);
            }

        三个细节：

        1. 第一名固定 ``"100"``，其余按 ``carNum / 第一名 * 100`` **截断取整**（``(int)`` 是
           向零截断，不是四舍五入）；
        2. ``topOne`` 初值 ``-1`` 是哨兵：第一名 ``carNum`` 恰为 ``-1`` 时后续都不算比率
           （原代码的边界，保留）；
        3. ``roadCode`` / ``sectionName`` 为 ``null`` 时拼接结果里是字面量 ``null``。
        """
        top_ten: List[TopTenVO] = self._mapper.get_top_ten()
        index = 1
        top_one: int = -1
        for item in top_ten:
            item.section_name = f"{_java_string(item.road_code)} {_java_string(item.section_name)}"
            if index == 1:
                item.rate = "100"
                top_one = item.car_num
            else:
                if top_one != -1:
                    # Java: (int)(Double.valueOf(carNum) / topOne * 100) —— 向零截断
                    item.rate = str(int(item.car_num / top_one * 100))
            item.rank = index
            index += 1
        return top_ten


_SERVICE: OdsRtSzdnSnapshotFlowAddcodeService | None = None


def get_ods_rt_szdn_snapshot_flow_addcode_service() -> OdsRtSzdnSnapshotFlowAddcodeService:
    """Java: ``@Autowired IOdsRtSzdnSnapshotFlowAddcodeService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = OdsRtSzdnSnapshotFlowAddcodeService()
    return _SERVICE


def reset_ods_rt_szdn_snapshot_flow_addcode_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "OdsRtSzdnSnapshotFlowAddcodeService",
    "get_ods_rt_szdn_snapshot_flow_addcode_service",
    "reset_ods_rt_szdn_snapshot_flow_addcode_service",
]
