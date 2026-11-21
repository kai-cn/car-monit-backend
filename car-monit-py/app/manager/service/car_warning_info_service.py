"""预警车辆 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningInfoServiceImpl.java

与「纯模板」模块的两处差别
--------------------------
1. ``saveCarWarningInfo`` 的 ``userId`` **硬编码为 1L**（不是 ``SecurityUtils``）；
   新增时补 ``delFlag = "0"`` 与四个审计字段，修改时只补 ``updateBy`` / ``updateTime``。
2. 多了 4 个给大屏用的方法：``selectCarWarningInfoById`` 的轨迹补充、
   按 ``trackId``（= 当天 ``yyyyMMdd``）取「在线车辆」预警并写 Redis、
   ``selectCarWarningInfoListLimit100`` 的「是否需要告警」标记。

三处照抄的 Java 既成事实
------------------------
1. ``selectCarWarningInfoListLimit100`` 只看 ``trailFwqList`` 来源的 ``devCodes``
   （``trackNames``），而 ``escapedType`` 在实体上恒为 ``null`` —— 所以一旦前端
   传了 ``escapedType``，结果必然为空。
2. ``needToWarnStr`` 先把**候选项**全部置 ``"0"``，再按 Redis 里的门架规则
   与 ``sys_config:warning_trigger_timespan``（分钟）回填 ``"1"``。
3. ``updateRedisWarningList`` 里的 ``carWhiteInfo`` 局部变量创建后从未使用，
   照抄保留（不影响行为）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from app.base.domain.trail_bo import TrailBo
from app.common.constant.constants import (
    CAR_WARNING_RULE,
    SERVICE_AREA_CAPTURE,
    STATION_CAPTURE,
    car_history_trail,
    car_warning_list,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import is_exits_str, is_not_blank, is_null
from app.common.utils.date_utils import get_timestamp
from app.settings import get_settings
from app.manager.domain.car_warning_info import CarWarningInfo
from app.manager.domain.vo.bigscreen.car_location_param import CarLocationParam
from app.manager.mapper.car_warning_info_mapper import CarWarningInfoMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.config.database import transactional

#: Java: ``String formattedDate = sdf.format(new Date());`` 的格式。
DATE_PATTERN = "%Y%m%d"


class CarWarningInfoService(ManagerCrudService):
    """Java: ``class CarWarningInfoServiceImpl extends ServiceImpl<CarWarningInfoMapper, CarWarningInfo>``."""

    mapper_cls = CarWarningInfoMapper

    def __init__(
        self, mapper: Any = None, redis_cache: Optional[RedisCache] = None
    ) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    # ---------------------------------------------------------------- 查询

    # Java: CarWarningInfo selectCarWarningInfoById(String id)
    def select_by_id(self, entity_id: str) -> Optional[CarWarningInfo]:
        rtn = self._mapper.select_by_id(entity_id)
        if rtn is not None:
            car_no = is_null(rtn.car_no)
            next_key = car_history_trail + car_no
            # 当前进入门架的时间
            gantry_station_id = is_null(rtn.gantry_station_id)

            trail_info_list = self.redis_cache.get_cache_object(next_key)
            trail_fwq_list: List[Any] = []
            if trail_info_list:
                cylylist: List[List[Any]] = []
                # 找到下一个位置
                for trail_info in trail_info_list:
                    trail_list = trail_info.trail_list
                    # 循环轨迹
                    if trail_list:
                        for trail_bo in trail_list:
                            if gantry_station_id == is_null(trail_bo.dev_code):
                                cylylist.append(trail_list)

                # 循环 cylylist
                name_map: dict = {}
                for trail_list in cylylist:
                    index_type = SERVICE_AREA_CAPTURE
                    if is_null(get_settings().is_localhost) == "local":
                        index_type = STATION_CAPTURE
                    # 需要去掉重复的数据
                    for trail_bo in trail_list:
                        if index_type == is_null(trail_bo.state_type):
                            dev_name = is_null(trail_bo.dev_name)
                            if dev_name != "":
                                if dev_name in name_map:
                                    pass
                                else:
                                    trail_fwq_list.append(trail_bo)
                                    name_map[dev_name] = dev_name
            rtn.trail_fwq_list = trail_fwq_list  # type: ignore[assignment]
        return rtn

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarWarningInfo(CarWarningInfo carWarningInfo)
    @transactional
    def save(self, entity: Any) -> AjaxResult:
        # Java: Long userId = 1L;  —— 硬编码，不是当前登录用户
        user_id = 1
        if is_not_blank(getattr(entity, "id", None)):
            entity.update_by = user_id
            entity.update_time = get_timestamp()
            self._mapper.update_by_id(entity)
        else:
            entity.del_flag = "0"
            entity.create_by = user_id
            entity.create_time = get_timestamp()
            entity.update_by = user_id
            entity.update_time = get_timestamp()
            self._mapper.insert(entity)
        return AjaxResult.success_message_data(
            SAVE_SUCCESS_MESSAGE, getattr(entity, "id", None)
        )

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteCarWarningInfoByUUid(List<String> idList)
    def delete_car_warning_info_by_uuid(self, id_list: Any) -> AjaxResult:
        if id_list:
            self._mapper.delete_car_warning_info_by_uuid(id_list)
        return AjaxResult.success()

    # ---------------------------------------------------------------- 缓存

    # Java: public void updateRedisWarningList()
    def update_redis_warning_list(self) -> None:
        formatted_date = datetime.now().strftime(DATE_PATTERN)
        query = CarWarningInfo()
        query.track_id = formatted_date
        rows = self._mapper.select_car_warning_info_list_limit100(query)
        self.redis_cache.set_cache_object(car_warning_list, list(rows))

    # Java: public List<CarWarningInfo> getRedisCarWarningList()
    def get_redis_car_warning_list(self) -> List[Any]:
        cached = self.redis_cache.get_cache_object(car_warning_list)
        if cached is not None:
            return list(cached)
        # 查询在线的
        formatted_date = datetime.now().strftime(DATE_PATTERN)
        query = CarWarningInfo()
        query.track_id = formatted_date
        rows = self._mapper.select_car_warning_info_list_limit100(query)
        self.redis_cache.set_cache_object(car_warning_list, list(rows))
        return list(rows)

    # Java: List<CarWarningInfo> selectCarWarningInfoListLimit100(CarLocationParam param)
    def select_car_warning_info_list_limit100(
        self, param: CarLocationParam
    ) -> List[Any]:
        rtnlist: List[Any] = []

        rows = self.get_redis_car_warning_list()
        for rtn in rows:
            dev_codes = is_null(rtn.track_names)
            # 所属路线编码
            if not is_exits_str(dev_codes, param.road_code):
                continue
            # 所属路段编码
            if not is_exits_str(dev_codes, param.section_code):
                continue
            # 所属收费站编码
            if not is_exits_str(dev_codes, param.toll_code):
                continue
            # 门架编号
            if not is_exits_str(dev_codes, param.gantry_code):
                continue
            # 服务区编码
            if not is_exits_str(dev_codes, param.fwqbm):
                continue
            # 逃费类型（实体上恒为 null —— 传了就全部过滤掉）
            if not is_exits_str(rtn.escaped_type, param.escaped_type):
                continue
            # 车牌号
            if not is_exits_str(rtn.car_no, param.car_no_query):
                continue
            rtn.need_to_warn_str = "0"  # 不需要告警标志
            rtnlist.append(rtn)

        if rtnlist:
            cache_object_num = 10  # 提醒时间默认 10 分钟
            user_id = get_current_user_id()
            # 声音提醒
            notice_type = "1"
            redis_key = f"{CAR_WARNING_RULE}{user_id}type{notice_type}"
            old_object = self.redis_cache.get_cache_object(redis_key)
            rule_list_value: List[Any] = list(old_object) if old_object is not None else []
            if rule_list_value:
                cache_object = self.redis_cache.get_cache_object(
                    "sys_config:warning_trigger_timespan"
                )
                if is_not_blank(cache_object):
                    cache_object_num = int(cache_object)

                minutes_in_millis = cache_object_num * 60 * 1000
                current_date = datetime.now()
                for warning_info in rtnlist:
                    gantry_time = warning_info.gantry_time
                    if gantry_time is not None:
                        # 经过时间在指定的分钟内告警
                        diff = abs(
                            int(current_date.timestamp() * 1000)
                            - int(gantry_time.timestamp() * 1000)
                        )
                        if diff <= minutes_in_millis:
                            gantry_station_id = is_null(warning_info.gantry_station_id)
                            if gantry_station_id in rule_list_value:
                                warning_info.need_to_warn_str = "1"  # 需要告警标志

        return rtnlist


def get_current_user_id() -> Any:
    """Java: ``SecurityUtils.getUserId()`` —— 延迟导入避免循环依赖。"""
    from app.common.utils.security_utils import get_user_id

    return get_user_id()


_SERVICE: Optional[CarWarningInfoService] = None


def get_car_warning_info_service() -> CarWarningInfoService:
    """Java: ``@Autowired ICarWarningInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarWarningInfoService()
    return _SERVICE


def reset_car_warning_info_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarWarningInfoService",
    "get_car_warning_info_service",
    "reset_car_warning_info_service",
]
