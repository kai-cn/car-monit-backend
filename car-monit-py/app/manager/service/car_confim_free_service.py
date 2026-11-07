"""确认补缴 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarConfimFreeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java

六个必须照抄的地方
------------------
1. ``saveCarConfimFree`` 是**新增/修改共用一个入口**：``id`` 非空即修改（走
   ``updateById``），否则先查重（``selectCarConfimFreeByIds`` 那套
   ``selectCarConfimFreeByExceptIds``），再插入；
2. 金额校验**只对内部补缴生效**：``comfimFreeType`` 不等于 ``"waibu"`` 时要求
   ``amount + aduitAmount`` 四舍五入到 2 位后**恰好等于**逃费合计，否则直接报错；
3. ``difAmount`` 只在**不等于 0** 时做 ``setScale(2, HALF_UP)`` —— 为 0 时保持
   ``BigDecimal.ZERO``（``0`` 而不是 ``0.00``，JSON 里两者都是 ``0``）；
4. ``escapedTypes`` 是把明细的 ``escapedType`` 用逗号拼起来（``Collectors.joining``），
   明细为空时**不赋值**（保持 ``null``），而不是空串；
5. 外部补缴（``waibu``）会把异常流水与可疑车辆的状态都改成 ``1``；内部补缴只有在
   ``carAduitFreeList`` 非空时才做同样的事 —— 也就是说传空明细的内部补缴**不会**
   改状态，照抄；
6. ``getCarStatistics`` 用 ``Collectors.toMap`` 建索引（**重复 key 会抛
   IllegalStateException**，即 HTTP 500）；Python 侧同样显式抛 ``ValueError``，
   不用"后者覆盖前者"。

``selectCarConfimFreeByExceptIds``（选择异常查询）的默认比例
-----------------------------------------------------------
``backCol1 = "0.3"``，``amount = difAmount * 0.3`` 再 ``setScale(2, HALF_UP)``。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.date_utils import get_timestamp
from app.manager.domain.car_aduit_free import CarAduitFree
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.car_suspicious import CarSuspicious
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.pc_car_statistics_vo import PCCarStatisticsVO
from app.manager.mapper.car_confim_free_mapper import CarConfimFreeMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.config.database import transactional

#: Java: ``AjaxResult.error("请选择车辆异常流水！")``
NO_EXCEPT_IDS_MESSAGE = "请选择车辆异常流水！"
#: Java: ``AjaxResult.error("车辆补缴单已追缴，请勿重复补缴！")``
ALREADY_PAID_MESSAGE = "车辆补缴单已追缴，请勿重复补缴！"
#: Java: ``AjaxResult.error("异常车辆流水不存在！")``
NO_EXCEPT_RECORD_MESSAGE = "异常车辆流水不存在！"
#: Java: ``AjaxResult.error("请勿选择多辆车！")``
MULTI_CAR_MESSAGE = "请勿选择多辆车！"
#: Java: ``AjaxResult.error("选择的异常流水存在多个录入单位，请确认！")``
MULTI_ORG_MESSAGE = "选择的异常流水存在多个录入单位，请确认！"
#: Java: ``AjaxResult.error("录入信息的拆分金额和处理信息的拆分金额合计不等于逃费金额！")``
AMOUNT_MISMATCH_MESSAGE = "录入信息的拆分金额和处理信息的拆分金额合计不等于逃费金额！"

#: Java: ``new BigDecimal("0.3")`` —— 选择异常流水时的默认拆分比例
DEFAULT_RATE = Decimal("0.3")
#: Java: ``setScale(2, RoundingMode.HALF_UP)``
TWO_PLACES = Decimal("0.01")
#: Java: ``"waibu".equals(comfimFreeType)`` —— 外部补缴
TYPE_EXTERNAL = "waibu"
#: Java: ``"escaped_type"``
DICT_ESCAPED_TYPE = "escaped_type"


def _half_up(value: Decimal) -> Decimal:
    """Java: ``value.setScale(2, RoundingMode.HALF_UP)``."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _sum_dif_amount(record_list: Sequence[Any]) -> Decimal:
    """Java: 循环累加非 null 的 ``difAmount``，非 0 时 ``setScale(2, HALF_UP)``。"""
    dif_amount = Decimal("0")
    for record in record_list:
        if record.dif_amount is not None:
            dif_amount = dif_amount + record.dif_amount
    if dif_amount != 0:
        dif_amount = _half_up(dif_amount)
    return dif_amount


class CarConfimFreeService(ManagerCrudService):
    """Java: ``class CarConfimFreeServiceImpl extends ServiceImpl<CarConfimFreeMapper, CarConfimFree>``."""

    mapper_cls = CarConfimFreeMapper

    # ---------------------------------------------------------------- 协作者

    @property
    def car_except_record_service(self) -> Any:
        from app.manager.service.car_except_record_service import (
            get_car_except_record_service,
        )

        return get_car_except_record_service()

    @property
    def car_aduit_free_service(self) -> Any:
        from app.manager.service.car_aduit_free_service import get_car_aduit_free_service

        return get_car_aduit_free_service()

    @property
    def car_suspicious_mapper(self) -> Any:
        from app.manager.mapper.car_suspicious_mapper import CarSuspiciousMapper

        return CarSuspiciousMapper()

    @property
    def dict_data_service(self) -> Any:
        from app.system.service.sys_dict_data_service import get_dict_data_service

        return get_dict_data_service()

    # ---------------------------------------------------------------- 查询

    # Java: CarConfimFree selectCarConfimFreeById(String id)
    def select_by_id(self, entity_id: str) -> Optional[CarConfimFree]:
        """详情 —— 顺带把异常流水明细、处理明细、逃费合计一起带出来。"""
        entity = self._mapper.select_by_id(entity_id)
        if entity is None or not is_not_blank(entity.id):
            return entity

        # 通过异常IDS查询异常列表
        except_ids = delete_end(entity.except_ids)
        if is_not_blank(except_ids):
            query = CarExceptRecord()
            query.except_ids = except_ids
            record_list = self.car_except_record_service.select_list(query)
            entity.car_except_record_list = record_list
            entity.dif_amount = _sum_dif_amount(record_list)

        # 处理明细
        aduit_query = CarAduitFree()
        aduit_query.confirm_id = entity_id
        entity.car_aduit_free_list = self.car_aduit_free_service.select_list(
            aduit_query
        )
        return entity

    # Java: List<CarConfimFree> selectCarConfimFreeList(CarConfimFree carConfimFree)
    def select_list(self, query: Any) -> List[Any]:
        return self._mapper.select_list(query)

    # Java: CarConfimFree listCount(CarConfimFree carConfimFree)
    def list_count(self, query: Any) -> Optional[CarConfimFree]:
        return self._mapper.list_count(query)

    # Java: List<CarConfimFree> selectConcernedList(CarConfimFree carConfimFree)
    def select_concerned_list(self, query: Any) -> List[Any]:
        return self._mapper.select_concerned_list(query)

    # Java: String selectOrgId(String carId, String id)
    def select_org_id(self, car_id: str, entity_id: str) -> Optional[str]:
        return self._mapper.select_org_id(car_id, entity_id)

    # 大屏批量版：一次查询补全本页的 ``orgId``（逐行调用是 N+1）。
    def select_org_ids(self, pairs: Sequence[Tuple[str, str]]) -> Dict[Tuple[str, str], Optional[str]]:
        return self._mapper.select_org_ids(pairs)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarConfimFree(CarConfimFree carConfimFree)
    @transactional
    def save(self, entity: CarConfimFree) -> AjaxResult:
        except_ids = delete_end(entity.except_ids)
        if is_blank(except_ids):
            return AjaxResult.error_message(NO_EXCEPT_IDS_MESSAGE)
        except_id_list = except_ids.split(",")

        if is_blank(entity.id):
            exists = self._mapper.select_by_except_ids(except_id_list)
            if exists is not None and len(exists) > 0:
                return AjaxResult.error_message(ALREADY_PAID_MESSAGE)

        # 修改异常车辆核实状态（实际只是取明细）
        query = CarExceptRecord()
        query.except_ids = except_ids
        record_list = self.car_except_record_service.select_list(query)
        dif_amount = _sum_dif_amount(record_list)

        # 修改明细
        aduit_free_list = entity.car_aduit_free_list
        if aduit_free_list is not None and len(aduit_free_list) > 0:
            # 将处理金额进行累加
            processing_amount = Decimal("0")
            for item in aduit_free_list:
                if item.amount is not None:
                    processing_amount = processing_amount + item.amount
            entity.aduit_amount = processing_amount
            entity.escaped_types = ",".join(
                is_null(record.escaped_type) for record in record_list
            )

        # 判断金额是否一致
        amount = entity.amount if entity.amount is not None else Decimal("0")
        aduit_amount = (
            entity.aduit_amount if entity.aduit_amount is not None else Decimal("0")
        )
        comfim_free_type = is_null(entity.comfim_free_type)
        if comfim_free_type != TYPE_EXTERNAL:
            yz_num = _half_up(amount + aduit_amount)
            if yz_num != dif_amount:
                return AjaxResult.error_message(AMOUNT_MISMATCH_MESSAGE)

        if is_not_blank(entity.id):
            # 修改
            self._mapper.update_by_id(entity)
        else:
            entity.status = "0"
            if comfim_free_type == TYPE_EXTERNAL:
                entity.status = "1"
            # 新增 主键
            self._mapper.insert(entity)

        if comfim_free_type == TYPE_EXTERNAL:
            # 外部补缴 —— 无论明细是否为空都要改状态
            self.car_except_record_service.update_status_by_except_id(
                except_id_list, "1"
            )
            self._mark_suspicious(record_list)
        else:
            # 内部补缴 —— 明细为空时**什么都不做**（照抄 Java）
            if aduit_free_list is not None and len(aduit_free_list) > 0:
                # 先删除
                self.car_aduit_free_service.delete_by_confirm_id(entity.id)
                # 后新增
                for item in aduit_free_list:
                    item.confirm_id = entity.id
                    item.car_id = entity.car_no  # Java 这里把 carNo 塞进 carId
                    item.car_type = entity.car_type
                    item.car_vehicle = entity.car_vehicle
                    item.car_no = entity.car_no
                    item.del_flag = "0"
                    item.create_time = get_timestamp()
                    item.update_time = get_timestamp()
                self.car_aduit_free_service.save_batch(aduit_free_list)

                # 修改异常流水状态
                self.car_except_record_service.update_status_by_except_id(
                    except_id_list, "1"
                )
                self._mark_suspicious(record_list)

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    def _mark_suspicious(self, record_list: Sequence[Any]) -> None:
        """把明细关联的可疑车辆状态改成 ``1``（``carId`` 为空则跳过）。"""
        for record in record_list:
            if is_not_blank(record.car_id):
                update_bo = CarSuspicious()
                update_bo.id = record.car_id
                update_bo.status = "1"
                self.car_suspicious_mapper.update_by_id(update_bo)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteCarConfimFreeByIds(String[] ids)
    @transactional
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        count = 0
        if entity_ids is not None and len(entity_ids) > 0:
            except_ids = ""
            for entity_id in entity_ids:
                entity = self._mapper.select_by_id(entity_id)
                if entity is not None and is_not_blank(entity.except_ids):
                    except_ids += delete_end(entity.except_ids) + ","
                # 删除明细（物理删除）
                self.car_aduit_free_service.delete_by_confirm_id(entity_id)

            except_ids = delete_end(except_ids)
            if is_not_blank(except_ids):
                # 修改异常流水状态回 0
                self.car_except_record_service.update_status_by_except_id(
                    except_ids.split(","), "0"
                )
            # 删除流水
            count = self._mapper.delete_by_ids(entity_ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarConfimFreeById(String id)
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 大屏统计

    # Java: List<CarStatisticsVO> getCarStatistics(IncomeStatisticParam param)
    def get_car_statistics(self, param: Any) -> List[CarStatisticsVO]:
        """按**字典顺序**输出逃费类型，SQL 没有的类型补 ``0``。"""
        from app.common.core.domain.entity.sys_dict_data import SysDictData

        dict_query = SysDictData()
        dict_query.dict_type = DICT_ESCAPED_TYPE
        dict_data_list = self.dict_data_service.select_dict_data_list(dict_query)

        row_list = self._mapper.get_car_statistics(param)
        # Java: Collectors.toMap(...) —— 重复 key 直接抛异常（HTTP 500）
        vo_map: Dict[Optional[str], CarStatisticsVO] = {}
        for row in row_list:
            if row.escaped_type in vo_map:
                raise ValueError(
                    f"Duplicate key {row.escaped_type!r} "
                    "(java.lang.IllegalStateException: Duplicate key)"
                )
            vo_map[row.escaped_type] = row

        result: List[CarStatisticsVO] = []
        for item in dict_data_list:
            vo = CarStatisticsVO()
            result.append(vo)
            vo.escaped_type = item.dict_value
            vo.escaped_type_name = item.dict_label
            found = vo_map.get(vo.escaped_type)
            if found is not None:
                vo.number = found.number
                vo.escaped_amount = found.escaped_amount
        return result

    # Java: CarStatisticsVO getCarConfirm(IncomeStatisticParam param)
    def get_car_confirm(self, param: Any) -> Optional[CarStatisticsVO]:
        return self._mapper.get_car_confirm(param)

    # ---------------------------------------------------------------- 选择异常查询

    # Java: AjaxResult selectCarConfimFreeByExceptIds(String exceptIds)
    def select_by_except_ids(self, except_ids: Optional[str]) -> AjaxResult:
        """选择异常流水后回显补缴单（**大部分字段是算出来的**，不落库）。"""
        entity = CarConfimFree()

        except_ids = delete_end(except_ids)
        if is_blank(except_ids):
            return AjaxResult.error_message(NO_EXCEPT_IDS_MESSAGE)

        query = CarExceptRecord()
        query.except_ids = except_ids
        record_list = self.car_except_record_service.select_list(query)
        entity.car_except_record_list = record_list
        if record_list is None or len(record_list) == 0:
            return AjaxResult.error_message(NO_EXCEPT_RECORD_MESSAGE)

        car_no_list = _distinct(record.car_no for record in record_list)
        if len(car_no_list) > 1:
            return AjaxResult.error_message(MULTI_CAR_MESSAGE)

        eps_list = _distinct(record.eps_id for record in record_list)
        if len(eps_list) > 1:
            return AjaxResult.error_message(MULTI_ORG_MESSAGE)
        if len(eps_list) > 0:
            # Java: epsList.get(0) + "" —— null 会拼成字符串 "null"
            entity.org_id = "null" if eps_list[0] is None else str(eps_list[0])

        except_id_list = except_ids.split(",")
        exists = self._mapper.select_by_except_ids(except_id_list)
        if exists is not None and len(exists) > 0:
            return AjaxResult.error_message(ALREADY_PAID_MESSAGE)

        first = record_list[0]
        entity.car_id = first.car_id
        entity.car_no = first.car_no
        entity.car_type = first.car_type
        entity.car_vehicle = first.car_vehicle
        entity.except_ids = except_ids

        # -------------- 应交金额
        dif_amount = Decimal("0")
        for record in record_list:
            if record.dif_amount is not None:
                dif_amount = dif_amount + record.dif_amount
        temp_cf_amount = dif_amount * DEFAULT_RATE
        if dif_amount != 0:
            dif_amount = _half_up(dif_amount)
        entity.dif_amount = dif_amount
        entity.back_col1 = str(DEFAULT_RATE)
        entity.amount = _half_up(temp_cf_amount)
        return AjaxResult.success_data(entity)

    # ---------------------------------------------------------------- PC 统计

    # Java: List<PCCarStatisticsVO> getPCCarStatistics(CarConfimFreeQueryRo queryRo)
    def get_pc_car_statistics(self, query_ro: Any) -> List[PCCarStatisticsVO]:
        """按单位汇总 6 种逃费类型的数量 / 金额。

        只有 ``10``~``60`` 六个类型参与汇总，其余值（如 ``1``/``2``）被丢弃；
        ``totalAmount`` 是这六个金额之和，即使一个都没命中也会写入
        ``0.00``（``setScale(2)`` 无条件执行）。
        """
        row_list = self._mapper.get_pc_car_statistics(query_ro)

        dept_list: List[str] = []
        dept_map: Dict[str, str] = {}
        except_map: Dict[str, Any] = {}
        for row in row_list:
            eps_id = is_null(row.eps_id)
            org_name = is_null(row.org_name)
            escaped_type = is_null(row.escaped_type)
            if is_not_blank(eps_id):
                if eps_id not in dept_map:
                    dept_list.append(eps_id)
                    dept_map[eps_id] = org_name
                except_map[eps_id + escaped_type] = row

        result: List[PCCarStatisticsVO] = []
        for org in dept_list:
            vo = PCCarStatisticsVO()
            vo.org_id = org
            vo.org_name = dept_map.get(org)

            total_num = 0
            total_amount = Decimal("0")

            for escaped_type in ("10", "20", "30", "40", "50", "60"):
                found = except_map.get(org + escaped_type)
                if found is None:
                    continue
                setattr(vo, f"escaped_type{escaped_type}_num", found.number)
                setattr(vo, f"escaped_type{escaped_type}_amount", found.escaped_amount)
                total_num = total_num + found.number
                total_amount = total_amount + found.escaped_amount

            # 合计
            vo.total_num = total_num
            vo.total_amount = _half_up(total_amount)
            result.append(vo)
        return result


def _distinct(values: Any) -> List[Any]:
    """Java: ``stream().map(...).distinct().collect(toList())`` —— 保序去重。"""
    seen: List[Any] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


_SERVICE: Optional[CarConfimFreeService] = None


def get_car_confim_free_service() -> CarConfimFreeService:
    """Java: ``@Autowired ICarConfimFreeService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarConfimFreeService()
    return _SERVICE


def reset_car_confim_free_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarConfimFreeService",
    "get_car_confim_free_service",
    "reset_car_confim_free_service",
]
