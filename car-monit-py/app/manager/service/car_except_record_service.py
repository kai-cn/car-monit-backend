"""异常车辆流水 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarExceptRecordService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarExceptRecordServiceImpl.java

五个必须照抄的既成事实
----------------------
1. ``saveCarExceptRecord`` 先做**区间重复**校验（``isExitsTime``），命中直接返回
   ``"录入区间时间重复！"``；随后新增/修改，最后再按车牌重算 ``CarInfo`` 的
   逃费类型与金额；
2. ``deleteCarExceptRecordByIds`` 先查补缴记录，有补缴则拒绝删除；
3. ``buildPCCarStatisticsVO`` 只认 ``10``/``20``/``30``/``40``/``50`` 五个逃费类型，
   ``60`` 的字段永远是初值 0（SQL 可能返回但方法没读）；
4. ``getConfirmId`` 没查到补缴时返回 ``"-1"``（不是 ``null``）；
5. ``saveCarExcept`` 只在 ``car_info`` 里**已存在**同一车牌时回写，不会新建。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.common_util import is_not_blank, is_null
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.car_info import CarInfo
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.pc_car_statistics_vo import PCCarStatisticsDetailVO, PCCarStatisticsVO
from app.manager.mapper.car_except_record_mapper import CarExceptRecordMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.config.database import transactional

logger = logging.getLogger("app.manager.service.car_except_record_service")

#: Java: ``AjaxResult.error("录入区间时间重复！")``
TIME_DUPLICATED_MESSAGE = "录入区间时间重复！"
#: Java: ``AjaxResult.error("删除失败，车辆异常流水已补缴！")``
ALREADY_PAID_MESSAGE = "删除失败，车辆异常流水已补缴！"
#: Java: ``return "-1";``
NO_CONFIRM_ID = "-1"


class CarExceptRecordService(ManagerCrudService):
    """Java: ``class CarExceptRecordServiceImpl extends ServiceImpl<CarExceptRecordMapper, CarExceptRecord>``."""

    mapper_cls = CarExceptRecordMapper

    # ---------------------------------------------------------------- 协作者

    @property
    def car_confim_free_mapper(self) -> Any:
        from app.manager.mapper.car_confim_free_mapper import CarConfimFreeMapper

        return CarConfimFreeMapper()

    @property
    def car_info_service(self) -> Any:
        from app.manager.service.car_info_service import get_car_info_service

        return get_car_info_service()

    # ---------------------------------------------------------------- 查询

    # Java: List<CarExceptRecord> selectCarExceptRecordListNew(CarExceptRecord x)
    def select_list_new(self, query: Any) -> List[Any]:
        return self._mapper.select_list_new(query)

    # Java: CarExceptRecord exceptRecordCount(CarExceptRecord x)
    def except_record_count(self, query: Any) -> Optional[CarExceptRecord]:
        return self._mapper.except_record_count(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarExceptRecord(CarExceptRecord x)
    @transactional
    def save(self, entity: Any) -> AjaxResult:
        # 判断区间是否重复
        if entity.in_time is not None and entity.out_time is not None:
            count_time_num = self._mapper.is_exists_time(entity)
            if count_time_num > 0:
                return AjaxResult.error_message(TIME_DUPLICATED_MESSAGE)

        if is_not_blank(entity.id):
            # 修改
            self._mapper.update_by_id(entity)
        else:
            entity.status = "0"
            # 新增 主键
            self._mapper.insert(entity)

        # --------- 根据车辆逃费类型和金额
        if is_not_blank(entity.car_no):
            query_car_except_record = CarExceptRecord()
            query_car_except_record.car_no = entity.car_no
            self.save_car_except(query_car_except_record)

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteCarExceptRecordByIds(String[] ids)
    @transactional
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        # 判断是否有补缴记录 ----------------
        count = 0
        if entity_ids:
            car_confim_free_list = self.car_confim_free_mapper.select_by_except_ids(
                list(entity_ids)
            )
            if car_confim_free_list:
                return AjaxResult.error_message(ALREADY_PAID_MESSAGE)
            count = self._mapper.delete_by_ids(entity_ids)

        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarExceptRecordById(String id)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarExceptRecordByCarId(String fkId) —— **物理删除**
    def delete_by_car_id(self, fk_id: str) -> AjaxResult:
        count = self._mapper.delete_by_car_id(fk_id)
        return AjaxResult.success_data(count)

    # Java: void updateStatusByExceptId(List<String> exceptIdList, String status)
    def update_status_by_except_id(
        self, except_id_list: Sequence[str], status: str
    ) -> None:
        self._mapper.update_status_by_except_id(except_id_list, status)

    # ---------------------------------------------------------------- 统计

    # Java: PCCarStatisticsVO buildPCCarStatisticsVO(List<String> ids, String escapedType)
    def build_pc_car_statistics_vo(
        self, ids: Optional[Sequence[str]], escaped_type: Optional[str]
    ) -> PCCarStatisticsVO:
        vo = PCCarStatisticsVO()
        rows: List[CarStatisticsVO] = self._mapper.build_pc_car_statistics_vo(
            ids, escaped_type
        )
        # Java: Collectors.toMap(CarStatisticsVO::getEscapedType, v -> v)
        vo_map: Dict[str, CarStatisticsVO] = {}
        for item in rows:
            vo_map[is_null(item.escaped_type)] = item

        total_num = 0
        total_amount = Decimal("0")
        for key, suffix in (
            ("10", "escaped_type10"),
            ("20", "escaped_type20"),
            ("30", "escaped_type30"),
            ("40", "escaped_type40"),
            ("50", "escaped_type50"),
        ):
            item = vo_map.get(key)
            if item is None:
                continue
            if item.number is not None:
                total_num += item.number
                setattr(vo, f"{suffix}_num", item.number)
            if item.escaped_amount is not None:
                total_amount = total_amount + item.escaped_amount
                setattr(vo, f"{suffix}_amount", item.escaped_amount)
        # 注意：escapedType60* 在 Java 里**没有**被读取，保持初值 0
        vo.total_num = total_num
        vo.total_amount = total_amount
        return vo

    # Java: List<PCCarStatisticsDetailVO> buildPCCarStatisticsVODetail(ids, escapedType)
    def build_pc_car_statistics_vo_detail(
        self, ids: Optional[Sequence[str]], escaped_type: Optional[str]
    ) -> List[PCCarStatisticsDetailVO]:
        return self._mapper.build_pc_car_statistics_vo_detail(ids, escaped_type)

    # Java: String getConfirmId(String id)
    def get_confirm_id(self, entity_id: str) -> str:
        car_confim_free_list = self.car_confim_free_mapper.select_by_except_ids(
            [entity_id]
        )
        if car_confim_free_list:
            return car_confim_free_list[0].id
        return NO_CONFIRM_ID

    # ---------------------------------------------------------------- 回写重点车辆

    # Java: void saveCarExcept(CarExceptRecord x)
    def save_car_except(self, query: Any) -> None:
        """按车牌重算逃费类型 / 金额，回写到 ``car_info``（只更新已存在的车牌）。"""
        car_query_no = is_null(query.car_no)
        rows: List[CarExceptRecord] = self._mapper.except_record_list(query)
        update_list: List[CarInfo] = []

        car_info_query = CarInfo()
        car_info_query.car_no = car_query_no
        car_list = self.car_info_service.select_list(car_info_query)
        car_map: Dict[str, CarInfo] = {}
        for car_rtn in car_list:
            car_map[is_null(car_rtn.car_no)] = car_rtn

        for record in rows:
            car_no = is_null(record.car_no)
            if not is_not_blank(car_no):
                continue
            if car_no not in car_map:
                continue
            car_info = car_map[car_no]
            upt_car_info = CarInfo()
            upt_car_info.id = car_info.id
            upt_car_info.escaped_type = record.escaped_type
            upt_car_info.escaped_amount = record.except_amount
            update_list.append(upt_car_info)

        if update_list:
            for item in update_list:
                self.car_info_service._mapper.update_by_id(item)  # noqa: SLF001


_SERVICE: Optional[CarExceptRecordService] = None


def get_car_except_record_service() -> CarExceptRecordService:
    """Java: ``@Autowired ICarExceptRecordService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarExceptRecordService()
    return _SERVICE


def reset_car_except_record_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "ALREADY_PAID_MESSAGE",
    "CarExceptRecordService",
    "NO_CONFIRM_ID",
    "TIME_DUPLICATED_MESSAGE",
    "get_car_except_record_service",
    "reset_car_except_record_service",
]
