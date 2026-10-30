"""可疑车辆 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java

五个必须照抄的既成事实
----------------------
1. ``saveCarSuspicious`` 的新增分支把 ``createBy`` / ``updateBy`` 写死成 ``1L``
   （不是当前登录用户）；
2. ``cherkCarSuspicious`` 里 ``for (CarSuspiciousCheck check : checkList)`` 在
   ``isExcept != "1"`` 且 ``checkList == null`` 时会抛 NPE —— 照抄（``TypeError``
   冒泡成 500），**不要**加空判；
3. ``cherkCarSuspicious`` 里"确认逃费"分支查询 ``CarInfo`` 时，命中已有记录则
   **什么都不做**（``addCarInfo`` 那行被注释掉了）；
4. ``syncSuspiciousCar`` 用 ``Constants.car_uspicious + yyyyMMdd + "*"`` 扫 Redis，
   但紧接着就把 ``trailInfoList`` **无条件覆盖**成入参 ``paraTrailInfoList`` ——
   Redis 分支的结果被丢弃（照抄）；
5. ``changeCarSuspicious`` 是先 ``insert ... select *`` 再 ``delete``（物理删除）。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence

from app.base.domain.geometry import Geometry
from app.base.domain.trail_bo import TrailBo
from app.base.domain.trail_info import TrailInfo
from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.common.constant import constants as Constants
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.date_utils import (
    YYYY_MM_DD_HH_MM_SS,
    date_time_parse,
    get_timestamp,
    get_timestamp_new,
    get_timestamp_new2,
)
from app.common.utils.json_utils import to_json_string
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.car_info import CarInfo
from app.manager.domain.car_suspicious import CarSuspicious
from app.manager.domain.car_suspicious_check import CarSuspiciousCheck
from app.manager.mapper.car_except_record_mapper import CarExceptRecordMapper
from app.manager.mapper.car_suspicious_mapper import CarSuspiciousMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService

#: Java: ``AjaxResult.error("可疑车俩不存在！")``
SUSPICIOUS_NOT_FOUND_MESSAGE = "可疑车俩不存在！"
#: Java: ``AjaxResult.error("可疑车俩异常流水已追缴！")``
SUSPICIOUS_PAID_MESSAGE = "可疑车俩异常流水已追缴！"
#: Java: ``AjaxResult.error("车辆逃费类型列表不能为空！")``
CHECK_LIST_EMPTY_MESSAGE = "车辆逃费类型列表不能为空！"
#: Java: ``AjaxResult.success("可疑车辆迁移：保留一个月的数据！")``
CHANGE_SUCCESS_MESSAGE = "可疑车辆迁移：保留一个月的数据！"

#: Java: ``Long userId = 1L;``（写死的系统用户）
SYSTEM_USER_ID = 1

#: Java: ``Calendar.add(Calendar.DAY_OF_MONTH, -30)``
KEEP_DAYS = 30

#: Java: ``SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd")``
REDIS_DATE_PATTERN = "%Y%m%d"

#: Java: ``SimpleDateFormat sdf1 = new SimpleDateFormat("yyyy-MM-dd")``
QUERY_DATE_PATTERN = "%Y-%m-%d"


class CarSuspiciousService(ManagerCrudService):
    """Java: ``class CarSuspiciousServiceImpl extends ServiceImpl<CarSuspiciousMapper, CarSuspicious>``."""

    mapper_cls = CarSuspiciousMapper

    def __init__(
        self,
        mapper: Any = None,
        redis_cache: Optional[RedisCache] = None,
        car_except_record_mapper: Any = None,
    ) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache
        self._car_except_record_mapper = car_except_record_mapper

    # ---------------------------------------------------------------- 协作者

    @property
    def redis_cache(self) -> RedisCache:
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    @property
    def car_suspicious_check_service(self) -> Any:
        from app.manager.service.car_suspicious_check_service import (
            get_car_suspicious_check_service,
        )

        return get_car_suspicious_check_service()

    @property
    def car_except_record_service(self) -> Any:
        from app.manager.service.car_except_record_service import (
            get_car_except_record_service,
        )

        return get_car_except_record_service()

    @property
    def car_confim_free_service(self) -> Any:
        from app.manager.service.car_confim_free_service import (
            get_car_confim_free_service,
        )

        return get_car_confim_free_service()

    @property
    def car_white_info_service(self) -> Any:
        from app.manager.service.car_white_info_service import (
            get_car_white_info_service,
        )

        return get_car_white_info_service()

    @property
    def car_info_service(self) -> Any:
        from app.manager.service.car_info_service import get_car_info_service

        return get_car_info_service()

    @property
    def car_track_info_service(self) -> Any:
        from app.manager.service.car_track_info_service import (
            get_car_track_info_service,
        )

        return get_car_track_info_service()

    @property
    def car_except_record_mapper(self) -> Any:
        if self._car_except_record_mapper is None:
            self._car_except_record_mapper = CarExceptRecordMapper()
        return self._car_except_record_mapper

    # ---------------------------------------------------------------- 查询

    # Java: CarSuspicious selectCarSuspiciousById(String id)
    def select_by_id(self, entity_id: str) -> Optional[CarSuspicious]:
        car = self._mapper.select_by_id(entity_id)
        if car is None:
            return None

        query_bo = CarSuspiciousCheck()
        query_bo.car_id = entity_id
        car.check_list = self.car_suspicious_check_service.select_list(query_bo)

        # --------------- 查询实时轨迹
        trail_info = TrailInfo()
        car_trail_list: List[Any] = []
        raod_trail_list: List[Geometry] = []
        track_josn = car.track_josn
        if is_not_blank(track_josn):
            trail_info = TrailInfo.model_validate_json(track_josn)
            tracks: Optional[ZdataTrailTracks] = trail_info.tracks
            car_trail_list = list(trail_info.trail_list or [])
            if car_trail_list:
                raod_trail_list = self.car_track_info_service.get_car_geometry_by_plan_new(
                    tracks, car_trail_list
                )

            trail_info.trail_uuid = car.car_no
            trail_info.trail_list = car_trail_list  # type: ignore[assignment]
            trail_info.raod_trail_list = raod_trail_list  # type: ignore[assignment]
            trail_info.trail_dev_count_bo = self.car_track_info_service.get_trail_dev_bo(
                trail_info.tracks, car_trail_list
            )

        car.trail_list = [trail_info]
        return car

    # Java: List<CarSuspicious> selectCarSuspiciousList(CarSuspicious x)
    def select_list(self, query: Any) -> List[Any]:
        return self._mapper.select_list(query)

    # Java: List<CarSuspicious> selectCarSuspiciousListHistroy(CarSuspicious x)
    def select_list_history(self, query: Any) -> List[Any]:
        return self._mapper.select_list_history(query)

    # Java: CarSuspicious selectCarSuspiciousHistoryById(String id)
    def select_history_by_id(self, entity_id: str) -> Optional[CarSuspicious]:
        car = self._mapper.select_history_by_id(entity_id)
        if car is None:
            return None

        query_bo = CarSuspiciousCheck()
        query_bo.car_id = entity_id
        car.check_list = self.car_suspicious_check_service.select_list(query_bo)

        trail_info = TrailInfo()
        car_trail_list: List[Any] = []
        raod_trail_list: List[Geometry] = []
        track_josn = car.track_josn
        if is_not_blank(track_josn):
            trail_info = TrailInfo.model_validate_json(track_josn)
            tracks: Optional[ZdataTrailTracks] = trail_info.tracks
            car_trail_list = list(trail_info.trail_list or [])
            if car_trail_list:
                raod_trail_list = self.car_track_info_service.get_car_geometry_by_plan_new(
                    tracks, car_trail_list
                )

            trail_info.trail_uuid = car.car_no
            trail_info.trail_list = car_trail_list  # type: ignore[assignment]
            trail_info.raod_trail_list = raod_trail_list  # type: ignore[assignment]
            trail_info.trail_dev_count_bo = self.car_track_info_service.get_trail_dev_bo(
                trail_info.tracks, car_trail_list
            )

        car.trail_list = [trail_info]
        return car

    # Java: List<CarSuspicious> selectCarSuspiciousListLimit10()
    def select_list_limit10(self) -> List[Any]:
        return self._mapper.select_list_limit10()

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarSuspicious(CarSuspicious x)
    def save(self, entity: Any) -> AjaxResult:
        entity.car_no = is_null(entity.car_no)

        user_id = SYSTEM_USER_ID
        if is_not_blank(entity.id):
            entity.update_by = user_id  # 更新人
            entity.update_time = get_timestamp_new()  # 更新时间
            # 修改
            self._mapper.update_by_id(entity)
        else:
            entity.create_by = user_id  # 创建人
            entity.create_time = get_timestamp_new()  # 创建时间
            entity.update_by = user_id  # 更新人
            entity.update_time = get_timestamp_new()  # 更新时间
            entity.is_except = "1"  # 默认是可疑车俩
            entity.status = "0"  # 是否可以核实标识
            # 新增 主键
            self._mapper.insert(entity)

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # Java: AjaxResult deleteCarSuspiciousByIds(String[] ids)
    def delete_by_ids(self, entity_ids: Sequence[str]) -> AjaxResult:
        count = self._mapper.delete_by_ids(entity_ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteCarSuspiciousById(String id)
    def delete_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 核实

    # Java: AjaxResult cherkCarSuspicious(CarSuspicious x)
    def cherk_car_suspicious(self, entity: Any) -> AjaxResult:
        car_id = is_null(entity.id)
        if is_blank(car_id):
            return AjaxResult.error_message(SUSPICIOUS_NOT_FOUND_MESSAGE)

        # 查询可疑车俩
        rtn_vo: Optional[CarSuspicious] = self._mapper.select_by_id(car_id)
        if not (rtn_vo is not None and is_not_blank(rtn_vo.id)):
            return AjaxResult.error_message(SUSPICIOUS_NOT_FOUND_MESSAGE)

        if is_null(rtn_vo.status) == "1":
            return AjaxResult.error_message(SUSPICIOUS_PAID_MESSAGE)

        # 车辆信息：根据车牌号查询
        car_no = is_null(entity.car_no)
        check_list: Optional[List[CarSuspiciousCheck]] = entity.check_list
        if is_null(entity.is_except) == "1":
            if not check_list:
                return AjaxResult.error_message(CHECK_LIST_EMPTY_MESSAGE)

        # 删除人工核验详情
        self.car_suspicious_check_service.delete_by_suspicious_id(car_id)
        # 删除异常车辆信息
        self.car_except_record_service.delete_by_car_id(car_id)

        # 逃费类型 —— Java 在 checkList 为 null 时抛 NPE，照抄
        escaped_type = ""
        escaped_amount = Decimal("0")
        for check in check_list:  # type: ignore[union-attr]
            add_check_type = is_null(check.escaped_type)
            if add_check_type in escaped_type:
                pass
            else:
                escaped_type += add_check_type + ","
            if check.dif_amount is not None:
                escaped_amount = escaped_amount + check.dif_amount
        escaped_type = delete_end(escaped_type)

        # 确认逃费
        if is_null(entity.is_except) == "1":
            # 查询车俩
            query_bo = CarInfo()
            query_bo.car_no = car_no
            car_info_list = self.car_info_service.select_list(query_bo)

            # 有值 —— 什么都不做（Java 里那一行是注释掉的）
            if not car_info_list:
                add_car_info = CarInfo()
                eps_id, user_id = _current_eps_and_user()
                add_car_info.id = _uuid()  # 主键
                add_car_info.del_flag = "0"
                add_car_info.eps_id = eps_id
                add_car_info.create_by = user_id  # 创建人
                add_car_info.create_time = get_timestamp()  # 创建时间
                add_car_info.update_by = user_id  # 更新人
                add_car_info.update_time = get_timestamp()  # 更新时间

                add_car_info.car_no = car_no
                add_car_info.car_type = entity.car_type
                add_car_info.car_num = entity.car_num
                add_car_info.car_vehicle = entity.car_vehicle
                add_car_info.plate_color = entity.plate_color
                add_car_info.escaped_type = entity.escaped_type
                add_car_info.escaped_amount = escaped_amount

                self.car_info_service._mapper.insert(add_car_info)  # noqa: SLF001

            except_record_list: List[CarExceptRecord] = []
            # 人工核实详情
            for check in check_list:  # type: ignore[union-attr]
                check.car_id = car_id
                check.car_no = car_no
                check.suspicous_flag = entity.is_except

                # -------------- 异常流水
                except_record = CarExceptRecord()
                except_record.car_id = car_id
                except_record.car_no = car_no
                except_record.car_type = entity.car_type
                except_record.car_vehicle = entity.car_vehicle
                except_record.car_num = entity.car_num

                except_record.pass_type = rtn_vo.pass_type
                except_record.in_station_id = rtn_vo.in_station_id
                except_record.in_station = rtn_vo.in_station
                except_record.in_time = rtn_vo.in_time
                except_record.out_station_id = rtn_vo.gantry_station_id
                except_record.out_station = rtn_vo.gantryt_station
                except_record.out_time = rtn_vo.gantry_time
                except_record.status = "0"

                except_record.total_amount = check.total_amount
                except_record.charge_amount = check.charge_amount
                except_record.dif_amount = check.dif_amount
                except_record.escaped_type = check.escaped_type
                except_record_list.append(except_record)

            if check_list:
                self.car_suspicious_check_service.save_batch(check_list)  # 插入核实
                self.car_except_record_service.save_batch(except_record_list)  # 插入异常流水

        # 修改状态已核实
        update_bo = CarSuspicious()
        update_bo.id = car_id
        update_bo.check_status = "1"
        update_bo.is_except = entity.is_except
        update_bo.except_remark = entity.except_remark
        update_bo.except_file_ids = entity.except_file_ids
        update_bo.pass_type = entity.pass_type

        update_bo.plate_color = entity.plate_color
        update_bo.car_no = car_no
        update_bo.car_type = entity.car_type
        update_bo.car_vehicle = entity.car_vehicle
        update_bo.car_num = entity.car_num
        update_bo.escaped_type = entity.escaped_type
        update_bo.remark = entity.remark

        # 车辆相关信息
        if is_null(entity.is_except) == "0":
            update_bo.except_file_ids = ""
        self._mapper.update_by_id(update_bo)

        # 更新重点车俩库
        self.car_info_service.update_redis_car_list()

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # ---------------------------------------------------------------- 同步

    # Java: AjaxResult syncSuspiciousCar(String addFlag, List<TrailInfo> paraTrailInfoList)
    def sync_suspicious_car(
        self, add_flag: str, para_trail_info_list: List[TrailInfo]
    ) -> AjaxResult:
        from app.system.service.sys_dict_data_service import get_dict_data_service

        user_id = SYSTEM_USER_ID
        # Java: ``CarParaVO carParaVO = new CarParaVO();`` —— 构造后从未使用（接口调用那行是注释掉的）

        # ------------------- 白名单的不生成相关数据 -------------
        car_white_info_map: Dict[str, Any] = {}
        for car_white_info in self.car_white_info_service.get_redis_car_white_list():
            car_white_info_map[is_null(car_white_info.car_no)] = car_white_info

        # 从 redis 拿（结果随后被入参覆盖 —— 照抄）
        trail_info_list: List[TrailInfo] = []
        formatted_date = datetime.now().strftime(REDIS_DATE_PATTERN)
        keys = self.redis_cache.keys(Constants.car_uspicious + formatted_date + "*")
        if is_null(add_flag) == "redis":
            if keys:
                for key in keys:
                    trail_info_list.append(self.redis_cache.get_cache_object(key))
        else:
            pass

        trail_info_list = list(para_trail_info_list)

        # 查询所有的车俩
        car_info_map: Dict[str, Any] = {}
        for vo in self.car_info_service.get_redis_car_list():
            car_info_map[is_null(vo.car_no)] = vo

        # 轨迹新增或者修改
        car_suspicious_list_add: List[CarSuspicious] = []
        car_suspicious_list_update: List[CarSuspicious] = []

        # 车牌颜色（标签 -> 值）
        plate_color_map: Dict[str, str] = get_dict_data_service().select_dict_data_lale_map(
            "plate_color"
        )

        for trail_info in trail_info_list:
            tracks_bo: ZdataTrailTracks = trail_info.tracks
            car_no = is_null(None if tracks_bo is None else tracks_bo.plate_key)  # 车牌号
            trail_uuid = is_null(None if tracks_bo is None else tracks_bo.uuid)  # 轨迹单
            if not (is_not_blank(car_no) and is_not_blank(trail_uuid)):
                continue
            if car_no in car_white_info_map:
                continue

            josn_list: List[TrailBo] = list(trail_info.trail_list or [])
            if not josn_list:
                continue

            dev_codes = ""  # 设备所有的集合
            # 生成可疑车辆
            car_suspicious = CarSuspicious()

            query_bo = CarSuspicious()
            query_bo.car_no = car_no
            query_bo.track_id = trail_uuid
            query_list = self._mapper.select_list(query_bo)

            check_status = "0"
            if query_list:
                car_suspicious.id = query_list[0].id
                check_status = is_null(query_list[0].check_status)

            car_suspicious.track_id = trail_uuid
            car_suspicious.track_josn = to_json_string(trail_info)
            car_suspicious.back_col1 = tracks_bo.escaped_tfcj

            if check_status == "1":
                # 已核实 —— 不写库
                continue

            car_suspicious.car_no = car_no
            car_suspicious.plate_color = is_null(plate_color_map.get(tracks_bo.plate_color))

            # ------------------ 标记需要转换
            if car_no in car_info_map:
                car_info = car_info_map[car_no]
                car_suspicious.plate_color = is_null(car_info.plate_color)
                car_suspicious.car_type = is_null(car_info.car_type)
                car_suspicious.car_vehicle = is_null(car_info.car_vehicle)
            else:
                # 车型
                if is_not_blank(tracks_bo.envehicletype):
                    car_vehicle = _car_vehicle_of(tracks_bo.envehicletype)
                    # 车型和车的种
                    if car_vehicle != "":
                        car_suspicious.car_type = tracks_bo.envehicletype
                        car_suspicious.car_vehicle = car_vehicle

            # 入口车轴数
            if tracks_bo.enaxlecount is not None:
                car_suspicious.car_num = int(str(tracks_bo.enaxlecount))
            else:
                car_suspicious.car_num = tracks_bo.car_num  # 轴数
            car_suspicious.pass_type = tracks_bo.pass_type  # 通行标识

            # -------------- 设置默认值
            if is_blank(car_suspicious.plate_color):
                car_suspicious.plate_color = "9"
            if is_blank(car_suspicious.car_type):
                car_suspicious.car_type = "99"
            if is_blank(car_suspicious.car_vehicle):
                car_suspicious.car_vehicle = "99"

            gantry_list: List[TrailBo] = []  # 门架
            station_list: List[TrailBo] = []  # 收费站

            for trail_bo in josn_list:
                state_type = is_null(trail_bo.state_type)
                # 抓拍设备
                if is_not_blank(trail_bo.dev_code):
                    dev_codes += state_type + ":" + trail_bo.dev_code + ","  # type: ignore[operator]
                # 路线
                if is_not_blank(trail_bo.road_code):
                    road_key = "roadCode:" + trail_bo.road_code  # type: ignore[operator]
                    if road_key not in dev_codes:
                        dev_codes += road_key + ","
                # 路段
                if is_not_blank(trail_bo.section_code):
                    section_key = "sectionCode:" + trail_bo.section_code  # type: ignore[operator]
                    if section_key not in dev_codes:
                        dev_codes += section_key + ","

                if state_type == Constants.BORDER_WEIGHING_CAPTURE:
                    pass  # 省界称重
                elif state_type == Constants.GANTRY_CAPTURE:
                    gantry_list.append(trail_bo)  # 门架抓拍
                elif state_type == Constants.PROV_CAPTURE:
                    pass
                elif state_type == Constants.SERVICE_AREA_CAPTURE:
                    pass  # 服务区抓拍
                elif state_type == Constants.STATION_CAPTURE:
                    station_list.append(trail_bo)  # 收费站抓拍

            # 收费站 ----------------
            for index, trail_bo in enumerate(station_list):
                if index == 0:
                    # 第一个收费站
                    car_suspicious.in_station_id = trail_bo.dev_code
                    car_suspicious.in_station = trail_bo.dev_name
                    if is_not_blank(trail_bo.capture_time):
                        car_suspicious.in_time = date_time_parse(
                            YYYY_MM_DD_HH_MM_SS, trail_bo.capture_time  # type: ignore[arg-type]
                        )
                elif index == len(station_list) - 1:
                    # 最后一个收费站
                    car_suspicious.out_station_id = trail_bo.dev_code
                    car_suspicious.out_station = trail_bo.dev_name
                    if is_not_blank(trail_bo.capture_time):
                        car_suspicious.out_time = date_time_parse(
                            YYYY_MM_DD_HH_MM_SS, trail_bo.capture_time  # type: ignore[arg-type]
                        )

            # 入口收费站编号
            if is_not_blank(tracks_bo.entollstationid):
                car_suspicious.in_station_id = tracks_bo.entollstationid
                car_suspicious.in_station = tracks_bo.entollstationname
                if tracks_bo.enter_time is not None:
                    car_suspicious.in_time = _as_datetime(tracks_bo.enter_time)

            # 出口收费站
            if is_not_blank(tracks_bo.extollstationid):
                car_suspicious.out_station_id = tracks_bo.extollstationid
                car_suspicious.out_station = tracks_bo.extollstationname
                if tracks_bo.exit_time is not None:
                    car_suspicious.out_time = _as_datetime(tracks_bo.exit_time)

            # 门架 ---------------
            for index, trail_bo in enumerate(gantry_list):
                if index == 0:
                    # 第一个门架
                    car_suspicious.gantry_station_id = trail_bo.dev_code
                    car_suspicious.gantryt_station = trail_bo.dev_name
                    if is_not_blank(trail_bo.capture_time):
                        car_suspicious.gantry_time = date_time_parse(
                            YYYY_MM_DD_HH_MM_SS, trail_bo.capture_time  # type: ignore[arg-type]
                        )
                elif index == len(gantry_list) - 1:
                    # 最后一个门架
                    car_suspicious.out_gantry_station_id = trail_bo.dev_code
                    car_suspicious.out_gantryt_station = trail_bo.dev_name
                    if is_not_blank(trail_bo.capture_time):
                        car_suspicious.out_gantry_time = date_time_parse(
                            YYYY_MM_DD_HH_MM_SS, trail_bo.capture_time  # type: ignore[arg-type]
                        )

            car_suspicious.create_by = user_id  # 创建人
            car_suspicious.create_time = get_timestamp_new2()  # 创建时间（now - 2 天）
            car_suspicious.update_by = user_id  # 更新人
            car_suspicious.update_time = get_timestamp_new2()  # 更新时间
            car_suspicious.is_except = "1"  # 默认是可疑车俩
            car_suspicious.status = "0"  # 是否可以核实标识

            car_suspicious.track_names = delete_end(dev_codes)
            if is_blank(car_suspicious.id):
                # 新增 -----------
                car_suspicious.escaped_type = tracks_bo.escaped_type  # 屏蔽
                car_suspicious.remark = tracks_bo.escaped_type_remark
                car_suspicious_list_add.append(car_suspicious)
            else:
                # 没有核实
                car_suspicious.remark = tracks_bo.escaped_type_remark
                car_suspicious_list_update.append(car_suspicious)

        if car_suspicious_list_add:
            self.save_batch(car_suspicious_list_add)
        if car_suspicious_list_update:
            self.update_batch_by_id(car_suspicious_list_update)

        return AjaxResult.success()

    # ---------------------------------------------------------------- 迁移

    # Java: AjaxResult changeCarSuspicious()
    def change_car_suspicious(self) -> AjaxResult:
        current_date = datetime.now()
        keep_date = current_date - timedelta(days=KEEP_DAYS)
        query_date = keep_date.strftime(QUERY_DATE_PATTERN)
        query_start_time = query_date + " 00:00:00"

        print(f"可疑车辆迁移时间------------：{query_start_time}")
        if is_not_blank(query_start_time):
            # 先转移 -----
            self._mapper.change_car_suspicious(query_start_time)
            # 然后再删除
            self._mapper.delete_change_car_suspicious(query_start_time)
        return AjaxResult.success_message(CHANGE_SUCCESS_MESSAGE)


# --------------------------------------------------------------------------- 工具


def _uuid() -> str:
    """Java: ``StringUtils.getUUID()``."""
    from app.common.utils.string_utils import get_uuid

    return get_uuid()


def _current_eps_and_user() -> tuple[Any, Any]:
    """Java: ``SecurityUtils.getEpsId()`` / ``SecurityUtils.getUserId()``."""
    from app.common.utils.security_utils import get_eps_id, get_user_id

    return get_eps_id(), get_user_id()


def _as_datetime(value: Any) -> Any:
    """``enter_time`` / ``exit_time`` 是 ``OdsDateTime``（可能已是 ``datetime``）."""
    if isinstance(value, datetime):
        return value
    return date_time_parse(YYYY_MM_DD_HH_MM_SS, str(value))


def _car_vehicle_of(car_type_name: str) -> str:
    """Java: 入口车种 ``envehicletype`` -> 车种（1/2/3，未命中返回空串）."""
    if car_type_name in ("1", "2", "3", "4"):
        return "1"
    if car_type_name in ("11", "12", "13", "14", "15", "16"):
        return "2"
    if car_type_name in ("21", "22", "23", "24", "25", "26"):
        return "3"
    return ""


_SERVICE: Optional[CarSuspiciousService] = None


def get_car_suspicious_service() -> CarSuspiciousService:
    """Java: ``@Autowired ICarSuspiciousService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarSuspiciousService()
    return _SERVICE


def reset_car_suspicious_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarSuspiciousService",
    "CHECK_LIST_EMPTY_MESSAGE",
    "CHANGE_SUCCESS_MESSAGE",
    "KEEP_DAYS",
    "SUSPICIOUS_NOT_FOUND_MESSAGE",
    "SUSPICIOUS_PAID_MESSAGE",
    "SYSTEM_USER_ID",
    "get_car_suspicious_service",
    "reset_car_suspicious_service",
]
