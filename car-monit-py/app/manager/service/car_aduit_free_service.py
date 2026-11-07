"""补缴处理 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarAduitFreeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarAduitFreeServiceImpl.java

三条必须照抄的地方
------------------
1. ``saveCarAduitFree`` 是纯模板（``isNotBlank(id)`` -> ``updateById``，
   否则 ``insert``），**没有**任何业务校验 —— 与 ``CarConfimFreeService`` 不同；
2. ``deleteCarAduitFreeByConfirmId`` 走 XML 的 ``<delete>``，是**物理删除**
   （按 ``confirm_id`` 整批删），而且 ``fkId`` 为空时直接返回 ``count = 0``；
3. ``getPCIncomeStatics`` / ``incomeDetailList`` 的返回类型分别是
   ``PCIncomeStaticsVO`` 与 ``CarConfimFree``（**不是** ``CarAduitFree``）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.common_util import is_not_blank
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.bigscreen.income_statistic_param import IncomeStatisticVO
from app.manager.domain.vo.pc_income_statics_vo import PCIncomeStaticsVO
from app.manager.mapper.car_aduit_free_mapper import CarAduitFreeMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.config.database import transactional


class CarAduitFreeService(ManagerCrudService):
    """Java: ``class CarAduitFreeServiceImpl extends ServiceImpl<CarAduitFreeMapper, CarAduitFree>``."""

    mapper_cls = CarAduitFreeMapper

    # ---------------------------------------------------------------- 查询

    # Java: List<CarAduitFree> selectCarAduitFreeList(CarAduitFree carAduitFree)
    def select_list(self, query: Any) -> List[Any]:
        return self._mapper.select_list(query)

    # Java: CarAduitFree selectCarAduitFreeById(String id)
    def select_by_id(self, entity_id: str) -> Optional[Any]:
        return self._mapper.select_by_id(entity_id)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarAduitFree(CarAduitFree carAduitFree)
    @transactional
    def save(self, entity: Any) -> AjaxResult:
        if is_not_blank(entity.id):
            # 修改
            self._mapper.update_by_id(entity)
        else:
            # 新增 主键
            self._mapper.insert(entity)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteCarAduitFreeByIds(String[] ids)
    @transactional
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        count = self._mapper.delete_by_ids(entity_ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarAduitFreeById(String id)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarAduitFreeByConfirmId(String fkId)
    @transactional
    def delete_by_confirm_id(self, fk_id: Optional[str]) -> AjaxResult:
        """按补缴单删除明细 —— **物理删除**，``fkId`` 为空白时不执行。"""
        count = 0
        if is_not_blank(fk_id):
            count = self._mapper.delete_by_confirm_id(fk_id)
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 大屏统计

    # Java: CarStatisticsVO getCarAudit(IncomeStatisticParam param)
    def get_car_audit(self, param: Any) -> Optional[CarStatisticsVO]:
        return self._mapper.get_car_audit(param)

    # Java: List<incomeStatisticVO> incomeStatistic(IncomeStatisticParam param)
    def income_statistic(self, param: Any) -> List[IncomeStatisticVO]:
        return self._mapper.income_statistic(param)

    # Java: Integer selectAuditCount(IncomeStatisticParam param)
    def select_audit_count(self, param: Any) -> int:
        return self._mapper.select_audit_count(param)

    # Java: ``carAduitFreeService.lambdaQuery().eq(CarAduitFree::getCarId, x).count()``
    def count_by_car_id(self, car_id: Optional[str]) -> int:
        """大屏 ``/exceptRecordList`` 逐行判断是否已有补缴记录（> 0 → 补缴状态置 ``1``）。"""
        return self._mapper.count_by_car_id(car_id)

    def count_by_car_ids(self, car_ids: Sequence[Optional[str]]) -> Dict[str, int]:
        """大屏批量版：一次 ``group by`` 取回本页所有车辆的补缴条数。"""
        return self._mapper.count_by_car_ids(car_ids)

    # ---------------------------------------------------------------- PC 堵漏增收

    # Java: List<PCIncomeStaticsVO> getPCIncomeStatics(CarConfimFreeQueryRo queryRo)
    def get_pc_income_statics(self, query_ro: Any) -> List[PCIncomeStaticsVO]:
        return self._mapper.pc_income_statics(query_ro)

    # Java: List<CarConfimFree> incomeDetailList(CarConfimFree confimFree)
    def income_detail_list(self, confim_free: Any) -> List[CarConfimFree]:
        return self._mapper.income_detail_list(confim_free)


_SERVICE: Optional[CarAduitFreeService] = None


def get_car_aduit_free_service() -> CarAduitFreeService:
    """Java: ``@Autowired ICarAduitFreeService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarAduitFreeService()
    return _SERVICE


def reset_car_aduit_free_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarAduitFreeService",
    "get_car_aduit_free_service",
    "reset_car_aduit_free_service",
]
