"""车辆信息 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java

Redis 无缓存列表（大屏地图描点用）
----------------------------------
* ``Constants.car_list`` —— 全量 ``CarInfo``（``selectCarInfoList`` 空条件）；
* ``Constants.car_list_jc`` —— 同长度的简表 ``CarVO{carId, carNo}``。

``updateRedisCarList`` 之后整份覆盖两个键；``getRedisCarList`` 命中就直接用，
未命中回源一次并回写（**不**写 ``car_list_jc``，与 Java 一致）。

三处照抄的 Java 既成事实
------------------------
1. ``saveCarInfo`` 先做车牌查重（``isExitsCar``），命中就返回错误、什么都不写；
2. ``deleteCarInfoByIds`` **不**刷新缓存，只有 ``deleteCarInfoById`` 刷新；
3. ``carLocation`` 完全走 Redis（``carMapper.getCarLocation`` 那一段已被注释掉），
   过滤顺序是：状态 -> 门架编码串（路线/路段/收费站/门架/服务区**都**拿
   ``gantry_code`` 比）-> 逃费类型 -> 车牌号。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, List, Optional, Sequence

from app.base.domain.car_vo import CarVO
from app.base.domain.trail_info import TrailInfo
from app.common.constant.constants import car_list, car_list_jc
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import is_exits_str, is_not_blank, is_null
from app.common.utils.date_utils import get_timestamp
from app.manager.domain.car_info import CarInfo
from app.manager.domain.vo.bigscreen.car_info_vo import CarInfoVO
from app.manager.domain.vo.bigscreen.car_location_param import CarLocationParam
from app.manager.domain.vo.bigscreen.car_location_vo import CarLocationVO
from app.manager.mapper.car_info_mapper import CarInfoMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.config.database import transactional

#: Java: ``AjaxResult.error("车牌号存在重复，请确定！")``
DUPLICATE_CAR_NO_MESSAGE = "车牌号存在重复，请确定！"


class CarInfoService(ManagerCrudService):
    """Java: ``class CarInfoServiceImpl extends ServiceImpl<CarInfoMapper, CarInfo>``."""

    mapper_cls = CarInfoMapper

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

    @property
    def car_track_info_service(self) -> Any:
        """Java: ``@Autowired private ICarTrackInfoService carTrackInfoService``."""
        from app.manager.service.car_track_info_service import (
            get_car_track_info_service,
        )

        return get_car_track_info_service()

    # ---------------------------------------------------------------- 查询

    # Java: CarInfo selectCarInfoById(String id)
    def select_by_id(self, entity_id: str) -> Optional[CarInfo]:
        car = self._mapper.select_by_id(entity_id)
        if car is not None:
            # ---------------查询实时轨迹
            trail_info = TrailInfo()

            car_trail_list: List[Any] = []
            raod_trail_list: List[Any] = []
            if is_null(car.status) == "1":
                track_josn = car.track_josn
                if is_not_blank(track_josn):
                    trail_info = TrailInfo.model_validate_json(track_josn)
                    # 轨迹值还原
                    tracks = trail_info.tracks
                    car_trail_list = list(trail_info.trail_list or [])
                    if car_trail_list:
                        raod_trail_list = (
                            self.car_track_info_service.get_car_geometry_by_plan_new(
                                tracks, car_trail_list
                            )
                        )

                    trail_info.trail_uuid = car.car_no
                    trail_info.trail_list = car_trail_list  # type: ignore[assignment]
                    trail_info.raod_trail_list = raod_trail_list  # type: ignore[assignment]
                    trail_info.trail_dev_count_bo = (
                        self.car_track_info_service.get_trail_dev_bo(
                            trail_info.tracks, car_trail_list
                        )
                    )

            car.trail_list = [trail_info]
        return car

    # Java: List<CarInfo> selectCarInfoList(CarInfo carInfo)
    def select_list(self, query: Any) -> List[Any]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarInfo(CarInfo carInfo)
    @transactional
    def save(self, entity: Any) -> AjaxResult:
        user_id = _current_user_id()
        entity.car_no = is_null(entity.car_no)  # 去掉空格
        # 判断车牌号是否重复
        count_num = self._mapper.is_exits_car(entity)
        if count_num > 0:
            return AjaxResult.error(DUPLICATE_CAR_NO_MESSAGE)

        if is_not_blank(entity.id):
            entity.update_by = user_id  # 更新人
            entity.update_time = get_timestamp()  # 更新时间
            # 修改
            self._mapper.update_by_id(entity)
        else:
            # 逃费金额
            if entity.escaped_amount is None:
                entity.escaped_amount = Decimal("0")
            entity.id = _uuid()  # 主键
            entity.del_flag = "0"
            entity.create_by = user_id  # 创建人
            entity.eps_id = _current_eps_id()
            entity.create_time = get_timestamp()  # 创建时间
            entity.update_by = user_id  # 更新人
            entity.update_time = get_timestamp()  # 更新时间
            # 新增 主键
            self._mapper.insert(entity)
        self.update_redis_car_list()
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # Java: AjaxResult saveCarInfo(CarInfo carInfo)
    def save_car_info(self, entity: Any) -> AjaxResult:
        """Java 的方法名是 ``saveCarInfo``（不是模板的 ``saveXxx``），转发到 :meth:`save`."""
        return self.save(entity)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteCarInfoByIds(String[] ids) —— **不**刷新缓存
    @transactional
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        count = self._mapper.delete_by_ids(entity_ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarInfoById(String id) —— 刷新缓存
    @transactional
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        self.update_redis_car_list()
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 导入

    # Java: AjaxResult doImport(List<CarInfo> list)
    def do_import(self, entity_list: List[Any]) -> AjaxResult:
        if entity_list:
            user_id = _current_user_id()
            addlist: List[Any] = []
            updatalist: List[Any] = []
            for car_info in entity_list:
                if is_not_blank(car_info.id):
                    car_info.update_by = user_id
                    car_info.update_time = get_timestamp()
                    updatalist.append(car_info)
                else:
                    if car_info.escaped_amount is None:
                        car_info.escaped_amount = Decimal("0")
                    car_info.id = _uuid()
                    car_info.del_flag = "0"
                    car_info.create_by = user_id
                    car_info.eps_id = _current_eps_id()
                    car_info.create_time = get_timestamp()
                    car_info.update_by = user_id
                    car_info.update_time = get_timestamp()
                    addlist.append(car_info)

            # 新增
            if addlist:
                for addbo in addlist:
                    # 创建时间**再取一次**（Java 原文如此）
                    addbo.create_time = get_timestamp()
                    self._mapper.insert(addbo)
            # 修改
            if updatalist:
                self._mapper_batch_update(updatalist)
        self.update_redis_car_list()
        return AjaxResult.success()

    # ---------------------------------------------------------------- 大屏

    # Java: List<CarLocationVO> carLocation(CarLocationParam param)
    def car_location(self, param: CarLocationParam) -> List[CarLocationVO]:
        car_location: List[CarLocationVO] = []
        for rtn in self.get_redis_car_list():
            if is_null(rtn.status) != "1":
                continue
            dev_codes = is_null(rtn.gantry_code)

            # 所属路线编码 / 路段 / 收费站 / 门架 / 服务区 —— 全部拿 gantry_code 比
            if not is_exits_str(dev_codes, param.road_code):
                continue
            if not is_exits_str(dev_codes, param.section_code):
                continue
            if not is_exits_str(dev_codes, param.toll_code):
                continue
            if not is_exits_str(dev_codes, param.gantry_code):
                continue
            if not is_exits_str(dev_codes, param.fwqbm):
                continue
            # 逃费类型
            if not is_exits_str(rtn.escaped_type, param.escaped_type):
                continue
            # 车牌号
            if not is_exits_str(rtn.car_no, param.car_no_query):
                continue

            addvo = CarLocationVO()
            addvo.id = rtn.id
            addvo.car_no = rtn.car_no
            addvo.car_type = rtn.car_type
            addvo.lon_str = rtn.last_pass_longitude
            addvo.lat_str = rtn.last_pass_latitude
            addvo.last_pass_type = rtn.last_pass_type
            if is_not_blank(addvo.lon_str):
                addvo.lon = float(Decimal(addvo.lon_str))
            if is_not_blank(addvo.lat_str):
                addvo.lat = float(Decimal(addvo.lat_str))
            addvo.status = rtn.status
            car_location.append(addvo)
        return car_location

    # Java: List<CarInfoVO> selectCarVoList()
    def select_car_vo_list(self) -> List[CarInfoVO]:
        return self._mapper.select_car_vo_list()

    # ---------------------------------------------------------------- 缓存

    # Java: public void updateRedisCarList()
    def update_redis_car_list(self) -> None:
        rows = self._mapper.select_list(CarInfo())
        car_vo_list: List[CarVO] = []
        for rtn in rows:
            temp_vo = CarVO()
            temp_vo.car_id = rtn.id
            temp_vo.car_no = rtn.car_no
            car_vo_list.append(temp_vo)
        self.redis_cache.set_cache_object(car_list_jc, car_vo_list)
        self.redis_cache.set_cache_object(car_list, list(rows))

    # Java: public List<CarInfo> getRedisCarList()
    def get_redis_car_list(self) -> List[Any]:
        cached = self.redis_cache.get_cache_object(car_list)
        if cached is not None:
            return list(cached)
        rows = list(self._mapper.select_list(CarInfo()))
        self.redis_cache.set_cache_object(car_list, rows)
        return rows

    def _mapper_batch_update(self, entity_list: List[Any]) -> None:
        for entity in entity_list:
            self._mapper.update_by_id(entity)


def _current_user_id() -> Any:
    """Java: ``SecurityUtils.getUserId()``."""
    from app.common.utils.security_utils import get_user_id

    return get_user_id()


def _current_eps_id() -> Any:
    """Java: ``SecurityUtils.getEpsId()``."""
    from app.common.utils.security_utils import get_eps_id

    return get_eps_id()


def _uuid() -> str:
    """Java: ``StringUtils.getUUID()``."""
    from app.common.utils.string_utils import get_uuid

    return get_uuid()


_SERVICE: Optional[CarInfoService] = None


def get_car_info_service() -> CarInfoService:
    """Java: ``@Autowired ICarInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarInfoService()
    return _SERVICE


def reset_car_info_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarInfoService",
    "DUPLICATE_CAR_NO_MESSAGE",
    "get_car_info_service",
    "reset_car_info_service",
]
