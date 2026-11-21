"""车辆行驶轨迹 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarTrackInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java

``manager`` 包里最大的一份 Service。四块职责：

1. **模板 CRUD**（``selectCarTrackInfoById`` / ``selectCarTrackInfoList`` /
   ``save`` / ``delete``）—— 列表回填 ``longitudeDec`` / ``latitudeDec``；
2. **实时轨迹同步** ``syncCurrentTrack`` —— 读 Redis 里的
   ``car_curent_trail:<车牌>``，改写 ``car_info`` 的在线状态与轨迹 JSON，
   并在门架停留超时后补一个「服务区抓拍」虚拟点；
3. **历史轨迹落库** ``syncHistoryTrack`` / ``syncHistoryTrackNoCar``；
4. **轨迹几何** ``getCarGeometry`` / ``getTrailDevBO`` / ``getCarGeometryByPlan`` /
   ``getCarGeometryByPlanNew`` —— 给 ``CarInfoService.selectCarInfoById`` 与
   大屏用。

照抄的 Java 既成事实（容易被"顺手修掉"）
------------------------------------------
1. ``syncCurrentTrack`` 的 ``userId`` 硬编码 ``1L``；
   ``isLocalhost == "local"`` 时**只**让 ``isZxFlag`` 参与"是否把车置为离线"的判断，
   早退逻辑本身仍会跑完整流程。
2. ``syncCurrentTrack`` 里 ``lastBo`` 与 ``lastMjBo`` 的赋值条件**完全相同** ——
   两个变量恒等，但历史轨迹补点逻辑依赖这个写法，照抄。
3. 补点的 ``captureTime`` 用当前时间；若 ``sys_config:sync_current_time``
   （小时）内还有抓拍，则 ``isExitFlag = false``（视为"还在路上"）。
4. ``saveTrailTracksHistory`` 先 ``removeRealData(carNoList)`` 再 ``saveBatch``；
   同一车牌在 Redis 里有多条 ``TrailInfo`` 就插多条。
5. ``getTrailDevBO`` 的 ``tracks`` 为 ``null`` 时新建一个空对象（不写回调用方）。

Redis 键
--------
``car_curent_trail:<carNo>``（实时，单对象）与 ``car_history_trail:<carNo>``
（历史，列表）都是 ``TrailInfo``；``sys_config:*`` 是运行期可调的整数配置。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

from app.base.domain.geometry import Geometry
from app.base.domain.trail_bo import TrailBo
from app.base.domain.trail_dev_bo import TrailDevBO
from app.base.domain.trail_dev_count_bo import TrailDevCountBO
from app.base.domain.trail_info import TrailInfo
from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.util.gps_util import gps84_to_gcj02
from app.base.util.lon_lat_paths_utils import LonLatPathsUtils
from app.common.constant import constants as Constants
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.domain_model import to_camel
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.date_utils import get_timestamp
from app.common.utils.string_utils import get_uuid
from app.manager.domain.car_info import CarInfo
from app.manager.domain.car_warning_info import CarWarningInfo
from app.manager.mapper.car_track_info_mapper import CarTrackInfoMapper
from app.manager.service.manager_service import SAVE_SUCCESS_MESSAGE, ManagerCrudService
from app.settings import get_settings
from app.config.database import transactional

logger = logging.getLogger("app.manager.service.car_track_info_service")

#: Java: ``new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")``
DATE_TIME_PATTERN = "%Y-%m-%d %H:%M:%S"
#: Java: ``new SimpleDateFormat("yyyyMMdd")``
DATE_PATTERN = "%Y%m%d"
#: Java: ``nextTrailBo.setCaptureTime("2000-10-10 10:00:00")``
DEFAULT_CAPTURE_TIME = "2000-10-10 10:00:00"
#: Java: ``int syncCurrentTime = 12;`` —— 默认 12 小时
DEFAULT_SYNC_CURRENT_TIME = 12
#: Java: ``long threeMinutesInMillis = 3 * 60 * 1000;``
THREE_MINUTES_IN_MILLIS = 3 * 60 * 1000
#: Java: ``int cacheObjectnum = 10;`` —— 预警提醒默认 10 分钟
DEFAULT_WARNING_TIMESPAN = 10
#: Java: ``setScale(4, RoundingMode.HALF_UP)`` 用的小数位
FOUR_PLACES = Decimal("0.0001")


def _parse_date_time(value: str) -> Optional[datetime]:
    """Java: ``SimpleDateFormat("yyyy-MM-dd HH:mm:ss").parse(...)``（失败返回 ``None``）。"""
    try:
        return datetime.strptime(value, DATE_TIME_PATTERN)
    except (TypeError, ValueError):
        return None


def _to_model_list(cached: Any, model_cls: Any) -> List[Any]:
    """Redis 反序列化出来的 ``dict`` 列表 -> 实体列表（Java 的 autotype 等价物）。"""
    if not cached:
        return []
    result: List[Any] = []
    for item in cached:
        result.append(item if isinstance(item, model_cls) else model_cls.model_validate(item))
    return result


def _to_model(cached: Any, model_cls: Any) -> Optional[Any]:
    if cached is None:
        return None
    return cached if isinstance(cached, model_cls) else model_cls.model_validate(cached)


def _to_decimal(value: Any) -> Decimal:
    """``float`` / ``Decimal`` -> ``Decimal``（Java 侧统一是 ``BigDecimal``）。"""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _plain_string(value: Any) -> str:
    """Java: ``BigDecimal.toPlainString()`` —— 不用科学计数法。"""
    return format(_to_decimal(value), "f")


def _field_of(item: Any, name: str) -> Any:
    """从 ``Geometry`` 实体或 Redis 反序列化出来的 ``dict`` 里读字段。"""
    if isinstance(item, dict):
        alias = to_camel(name)
        if alias in item:
            return item[alias]
        return item.get(name)
    return getattr(item, name, None)


class CarTrackInfoService(ManagerCrudService):
    """Java: ``class CarTrackInfoServiceImpl extends ServiceImpl<CarTrackInfoMapper, CarTrackInfo>``."""

    mapper_cls = CarTrackInfoMapper

    def __init__(
        self,
        mapper: Any = None,
        redis_cache: Optional[RedisCache] = None,
        lon_lat_paths_utils: Optional[LonLatPathsUtils] = None,
    ) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache
        self._lon_lat_paths_utils = lon_lat_paths_utils

    # ---------------------------------------------------------- 依赖（延迟取）

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    @property
    def car_info_service(self) -> Any:
        """Java: ``@Autowired private ICarInfoService carInfoService``."""
        from app.manager.service.car_info_service import get_car_info_service

        return get_car_info_service()

    @property
    def car_warning_info_service(self) -> Any:
        """Java: ``@Autowired private ICarWarningInfoService carWarningInfoService``."""
        from app.manager.service.car_warning_info_service import (
            get_car_warning_info_service,
        )

        return get_car_warning_info_service()

    @property
    def geometry_service(self) -> Any:
        """Java: ``@Autowired private IGeometryService geometryService``."""
        from app.base.service.geometry_service import get_geometry_service

        return get_geometry_service()

    @property
    def trail_tracks_service(self) -> Any:
        """Java: ``@Autowired private IZdataTrailTracksService trailTracksService``."""
        from app.base.service.zdata_trail_tracks_service import (
            get_zdata_trail_tracks_service,
        )

        return get_zdata_trail_tracks_service()

    @property
    def car_warning_config_service(self) -> Any:
        """Java: ``@Autowired private ICarWarningConfigService carWarningConfigService``."""
        from app.base.service.car_warning_config_service import (
            get_car_warning_config_service,
        )

        return get_car_warning_config_service()

    @property
    def lon_lat_paths_utils(self) -> LonLatPathsUtils:
        """Java: ``@Resource private LonLatPathsUtils lonLatPathsUtils``."""
        if self._lon_lat_paths_utils is None:
            self._lon_lat_paths_utils = LonLatPathsUtils()
        return self._lon_lat_paths_utils

    @property
    def road_path_service(self) -> Any:
        """Java: ``@Autowired private IRoadPathService roadPathService``."""
        from app.base.service.road_path_service import get_road_path_service

        return get_road_path_service()

    # ---------------------------------------------------------------- 查询

    # Java: CarTrackInfo selectCarTrackInfoById(String id)
    def select_by_id(self, entity_id: str) -> Optional[Any]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<CarTrackInfo> selectCarTrackInfoList(CarTrackInfo carTrackInfo)
    def select_list(self, query: Any) -> List[Any]:
        rows = self._mapper.select_list(query)
        if rows:
            for rtn in rows:
                if is_not_blank(rtn.longitude):
                    rtn.longitude_dec = float(Decimal(rtn.longitude))
                if is_not_blank(rtn.latitude):
                    rtn.latitude_dec = float(Decimal(rtn.latitude))
        return rows

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveCarTrackInfo(CarTrackInfo carTrackInfo)
    @transactional
    def save(self, entity: Any) -> AjaxResult:
        # 注意：这里**不**补审计字段（模板与其它模块不同）
        if is_not_blank(getattr(entity, "id", None)):
            self._mapper.update_by_id(entity)
        else:
            self._mapper.insert(entity)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, entity.id)

    # ---------------------------------------------------------------- 同步

    # Java: AjaxResult syncCurrentTrack()
    @transactional
    def sync_current_track(self) -> AjaxResult:
        """轨迹同步：实时（改写车辆在线状态 + 生成/清理预警）。"""
        # 查询所有的车俩
        car_list = self.car_info_service.get_redis_car_list()

        updatalist: List[Any] = []
        # 新增的预警
        add_car_warning_info_list: List[CarWarningInfo] = []
        # 删除的预警
        del_car_warning_info_list: List[str] = []

        user_id = 1

        # 是否执行
        is_zx_flag = True
        if is_null(get_settings().is_localhost) == "local":
            is_zx_flag = False  # 本地不执行

        # ---------- 服务器停留配置
        fwq_tl_list = self.car_warning_config_service.get_redis_car_warning_config()
        fwq_tl_map: Dict[str, Any] = {}
        for fwq_tl_vo in fwq_tl_list:
            fwq_tl_map[is_null(fwq_tl_vo.gantry_code_in)] = fwq_tl_vo

        for vo in car_list:
            car_no = is_null(vo.car_no)
            key = Constants.car_curent_trail + car_no
            trail_info = _to_model(self.redis_cache.get_cache_object(key), TrailInfo)

            car = CarInfo()
            car.id = vo.id
            # 跟新车俩 ---------- 车的状态修改 status 0
            car.status = "0"
            car.track_josn = None

            if trail_info is not None:
                tracks_bo = trail_info.tracks
                # 当前轨迹点：车辆+时间 carNo +"@@"+ formattedDate
                point_uuid = is_null(getattr(tracks_bo, "uuid", None))
                josn_list = list(trail_info.trail_list or [])
                if josn_list:
                    station_list: List[TrailBo] = []  # 收费站
                    first_station = TrailBo()  # 第一个收费站或者门架

                    trail_exits = False  # 轨迹点是否存在
                    # 在线增加判断是否有出的话 true=进入，false=驶出 directionIn
                    frist_count_num = 0
                    capture_time_last = ""  # 最后抓拍时间
                    is_exit_flag = True  # 是否离开
                    for trail_bo in josn_list:
                        if trail_bo.lon is not None and trail_bo.lat is not None:
                            trail_exits = True

                        capture_time = is_null(trail_bo.capture_time)
                        if is_not_blank(capture_time):
                            capture_time_last = capture_time
                        state_type = is_null(trail_bo.state_type)
                        if state_type == Constants.BORDER_WEIGHING_CAPTURE:
                            # 省界称重
                            if frist_count_num == 0:
                                first_station = trail_bo
                                frist_count_num += 1
                        elif state_type == Constants.GANTRY_CAPTURE:
                            # 门架抓拍
                            pass
                        elif state_type == Constants.PROV_CAPTURE:
                            # 省界抓拍
                            if frist_count_num == 0:
                                first_station = trail_bo
                                frist_count_num += 1
                        elif state_type == Constants.SERVICE_AREA_CAPTURE:
                            # 服务区抓拍
                            pass
                        elif state_type == Constants.STATION_CAPTURE:
                            # 收费站抓拍
                            if frist_count_num == 0:
                                first_station = trail_bo
                                frist_count_num += 1
                            station_list.append(trail_bo)

                    # 判断在线最后一个节点时间
                    try:
                        # ---------12 个小时
                        sync_current_time = DEFAULT_SYNC_CURRENT_TIME
                        cache_object = self.redis_cache.get_cache_object(
                            "sys_config:sync_current_time"
                        )
                        if is_not_blank(cache_object):
                            sync_current_time = int(cache_object)

                        millis = sync_current_time * 60 * 60 * 1000
                        if is_not_blank(capture_time_last):
                            capture_time_date = _parse_date_time(capture_time_last)
                            if capture_time_date is not None:
                                diff = abs(
                                    int(datetime.now().timestamp() * 1000)
                                    - int(capture_time_date.timestamp() * 1000)
                                )
                                if diff < millis:
                                    is_exit_flag = False
                    except Exception:  # noqa: BLE001 - Java 原文 catch (Exception e)
                        logger.warning(
                            "[轨迹同步] 计算抓拍时间差失败, carNo=%s",
                            getattr(car, "car_no", None),
                            exc_info=True,
                        )

                    if is_exit_flag and is_zx_flag:
                        # 跟新车俩 ---------- 车的状态修改 status 0
                        car.status = "0"
                        car.track_josn = None
                    else:
                        if trail_exits:
                            # -------- 获取最后一个节点：判断服务器停留配置
                            cur_js_last_bo = josn_list[-1]
                            cur_js_dev_code = is_null(cur_js_last_bo.dev_code)
                            cur_js_capture_time = is_null(cur_js_last_bo.capture_time)
                            if (
                                is_not_blank(cur_js_dev_code)
                                and is_not_blank(cur_js_capture_time)
                                and cur_js_dev_code in fwq_tl_map
                            ):
                                warning_config = fwq_tl_map[cur_js_dev_code]
                                # 判断在线最后一个节点时间
                                try:
                                    cur_js_current_time = (
                                        warning_config.time_span or 0
                                    )
                                    cur_js_millis = cur_js_current_time * 60 * 1000

                                    if is_not_blank(cur_js_capture_time):
                                        capture_time_date = _parse_date_time(
                                            cur_js_capture_time
                                        )
                                        cur_date = datetime.now()
                                        if capture_time_date is not None:
                                            # 注意：这里**不是** abs
                                            diff = int(
                                                cur_date.timestamp() * 1000
                                            ) - int(capture_time_date.timestamp() * 1000)
                                            if diff > cur_js_millis:
                                                area_trail_bo = TrailBo()
                                                area_trail_bo.point_uuid = get_uuid()
                                                area_trail_bo.state_type = (
                                                    Constants.SERVICE_AREA_CAPTURE
                                                )
                                                area_trail_bo.capture_time = (
                                                    cur_date.strftime(
                                                        DATE_TIME_PATTERN
                                                    )
                                                )
                                                area_trail_bo.location_code = ""
                                                area_trail_bo.road_code = (
                                                    warning_config.road_code
                                                )
                                                area_trail_bo.section_code = (
                                                    warning_config.section_code
                                                )
                                                area_trail_bo.dev_code = (
                                                    warning_config.fwqbm
                                                )
                                                area_trail_bo.dev_name = (
                                                    warning_config.fwqmc
                                                )
                                                area_trail_bo.pileno = (
                                                    warning_config.pile_no
                                                )
                                                if is_not_blank(
                                                    warning_config.lon
                                                ):
                                                    area_trail_bo.lon = float(
                                                        Decimal(warning_config.lon)
                                                    )
                                                if is_not_blank(
                                                    warning_config.lat
                                                ):
                                                    area_trail_bo.lat = float(
                                                        Decimal(warning_config.lat)
                                                    )
                                                josn_list.append(area_trail_bo)
                                except Exception:  # noqa: BLE001
                                    pass

                            last_bo = None
                            last_mj_bo = None
                            dev_codes = ""  # 设备所有的集合
                            for trail_bo in josn_list:
                                if (
                                    trail_bo.lon is not None
                                    and trail_bo.lat is not None
                                    and is_not_blank(trail_bo.dev_code)
                                ):
                                    last_bo = trail_bo

                                # Java 原文两个判断条件完全一样，照抄
                                if (
                                    trail_bo.lon is not None
                                    and trail_bo.lat is not None
                                    and is_not_blank(trail_bo.dev_code)
                                ):
                                    last_mj_bo = trail_bo

                            # 车辆实时位置
                            if last_bo is not None:
                                state_type = is_null(last_bo.state_type)

                                # 抓拍设备
                                if is_not_blank(last_bo.dev_code):
                                    dev_codes += (
                                        state_type + ":" + last_bo.dev_code + ","
                                    )
                                # 路线
                                if is_not_blank(last_bo.road_code):
                                    road_key = "roadCode:" + last_bo.road_code
                                    if dev_codes.find(road_key) == -1:
                                        dev_codes += road_key + ","
                                # 路段
                                if is_not_blank(last_bo.section_code):
                                    section_key = "sectionCode:" + last_bo.section_code
                                    if dev_codes.find(section_key) == -1:
                                        dev_codes += section_key + ","

                                car.status = "1"
                                if last_bo.lon is not None:
                                    car.last_pass_longitude = is_null(last_bo.lon)
                                if last_bo.lat is not None:
                                    car.last_pass_latitude = is_null(last_bo.lat)
                                car.last_pass_type = last_bo.state_type  # 业务类型
                                car.track_josn = json.dumps(
                                    trail_info.to_json_dict(), ensure_ascii=False
                                )
                                car.gantry_code = delete_end(dev_codes)

                            # 最后一个经过门架
                            if last_mj_bo is not None:
                                # 预警信息
                                car_warning_info = CarWarningInfo()
                                car_warning_info.car_id = vo.id
                                car_warning_info.car_no = vo.car_no
                                car_warning_info.car_type = vo.car_type
                                car_warning_info.car_vehicle = vo.car_vehicle
                                car_warning_info.car_num = vo.car_num

                                car_warning_info.track_id = point_uuid
                                car_warning_info.track_josn = json.dumps(
                                    last_mj_bo.to_json_dict(), ensure_ascii=False
                                )
                                car_warning_info.track_names = delete_end(dev_codes)

                                # 入站
                                car_warning_info.in_station_id = is_null(
                                    first_station.dev_code
                                )
                                car_warning_info.in_station = is_null(
                                    first_station.dev_name
                                )
                                if is_not_blank(first_station.capture_time):
                                    car_warning_info.in_time = _parse_date_time(
                                        first_station.capture_time
                                    )

                                # 抓拍设备
                                if is_not_blank(last_mj_bo.dev_code):
                                    car_warning_info.gantry_station_id = (
                                        last_mj_bo.dev_code
                                    )
                                    car_warning_info.gantryt_station = (
                                        last_mj_bo.dev_name
                                    )
                                    if is_not_blank(last_mj_bo.capture_time):
                                        car_warning_info.gantry_time = _parse_date_time(
                                            last_mj_bo.capture_time
                                        )
                                    car_warning_info.file_ids = is_null(
                                        last_mj_bo.images_arry
                                    )

                                    car_warning_info.del_flag = "0"
                                    car_warning_info.create_by = user_id
                                    car_warning_info.create_time = get_timestamp()
                                    car_warning_info.update_by = user_id
                                    car_warning_info.update_time = get_timestamp()
                                    car_warning_info.road_code = last_mj_bo.road_code
                                    car_warning_info.section_code = (
                                        last_mj_bo.section_code
                                    )

                                    if is_not_blank(point_uuid):
                                        del_car_warning_info_list.append(point_uuid)

                                    formatted_date = datetime.now().strftime(
                                        DATE_PATTERN
                                    )
                                    car_warning_info.back_col1 = formatted_date
                                    if point_uuid.find("@@") > -1:
                                        point_uuid_str = point_uuid.split("@@")
                                        if len(point_uuid_str) > 1:
                                            car_warning_info.back_col1 = (
                                                point_uuid_str[1]
                                            )

                                    add_car_warning_info_list.append(car_warning_info)

            updatalist.append(car)

        # 修改
        if updatalist:
            self.car_info_service.update_batch_by_id(updatalist)
            # 更新缓存
            self.car_info_service.update_redis_car_list()

        # 生成车俩预警信息
        if del_car_warning_info_list:
            self.car_warning_info_service.delete_car_warning_info_by_uuid(
                del_car_warning_info_list
            )

        if add_car_warning_info_list:
            # 去掉重合的
            for addbo in add_car_warning_info_list:
                car_no = is_null(addbo.car_no)
                next_key = Constants.car_history_trail + car_no
                # 当前进入门架的时间
                gantry_station_id = is_null(addbo.gantry_station_id)
                gantry_time = addbo.gantry_time

                trail_info_list = _to_model_list(
                    self.redis_cache.get_cache_object(next_key), TrailInfo
                )
                next_bo_list: List[TrailBo] = []
                for trail_info in trail_info_list:
                    trail_list_new = list(trail_info.trail_list or [])
                    # 循环轨迹
                    if trail_list_new:
                        trail_list: List[TrailBo] = []

                        distinct_map: Dict[str, str] = {}
                        for trail_bo_new in trail_list_new:
                            state_type = is_null(trail_bo_new.state_type)
                            capture_time = is_null(trail_bo_new.capture_time)
                            cur_dev_code = is_null(trail_bo_new.dev_code)
                            if state_type in (
                                Constants.BORDER_WEIGHING_CAPTURE,
                                Constants.GANTRY_CAPTURE,
                                Constants.PROV_CAPTURE,
                                Constants.SERVICE_AREA_CAPTURE,
                                Constants.STATION_CAPTURE,
                            ):
                                if is_not_blank(capture_time):
                                    if cur_dev_code in distinct_map:
                                        try:
                                            # 判断时间是否超过 3 分钟
                                            date1 = _parse_date_time(capture_time)
                                            date2 = _parse_date_time(
                                                distinct_map[cur_dev_code]
                                            )
                                            if date1 is not None and date2 is not None:
                                                diff = abs(
                                                    int(date2.timestamp() * 1000)
                                                    - int(date1.timestamp() * 1000)
                                                )
                                                if diff > THREE_MINUTES_IN_MILLIS:
                                                    trail_list.append(trail_bo_new)
                                        except Exception:  # noqa: BLE001
                                            pass
                                    else:
                                        distinct_map[cur_dev_code] = capture_time
                                        trail_list.append(trail_bo_new)

                        next_count_num = 0
                        for yy in range(len(trail_list)):
                            if next_count_num == 0:
                                trail_bo = trail_list[yy]
                                cur_dev_code = is_null(trail_bo.dev_code)
                                cur_capture_time = trail_bo.capture_time
                                if gantry_station_id == cur_dev_code:
                                    # 判断有下一个：不是最后一个
                                    if yy != len(trail_list) - 1:
                                        # 循环他后面的数量
                                        for next_index in range(
                                            yy + 1, len(trail_list)
                                        ):
                                            if next_count_num == 0:
                                                next_trail_bo = trail_list[next_index]
                                                if gantry_station_id != is_null(
                                                    next_trail_bo.dev_code
                                                ):
                                                    next_trail_bo.pre_capture_time = (
                                                        cur_capture_time
                                                    )
                                                    if is_blank(
                                                        next_trail_bo.capture_time
                                                    ):
                                                        next_trail_bo.capture_time = (
                                                            DEFAULT_CAPTURE_TIME
                                                        )
                                                    next_bo_list.append(next_trail_bo)
                                                    next_count_num += 1

                if next_bo_list:
                    # 找到最后一条记录
                    count_map: Dict[str, int] = {}
                    for nextbo in next_bo_list:
                        cur_dev_code = is_null(nextbo.dev_code)
                        count_map[cur_dev_code] = count_map.get(cur_dev_code, 0) + 1

                    for nextbo in next_bo_list:
                        cur_dev_code = is_null(nextbo.dev_code)
                        if cur_dev_code in count_map:
                            nextbo.count_num = count_map[cur_dev_code]
                        else:
                            nextbo.count_num = 0

                    # 按照先 countNum 排序 然后按照抓拍时间
                    # Java: comparing(countNum).reversed().thenComparing(captureTime).reversed()
                    #   == countNum 升序 + captureTime 降序
                    next_bo_list = sorted(
                        next_bo_list, key=lambda b: b.capture_time or "", reverse=True
                    )
                    next_bo_list = sorted(next_bo_list, key=lambda b: b.count_num or 0)

                    last_trail_bo = next_bo_list[0]

                    addbo.next_pass_address = last_trail_bo.dev_name

                    cur_capture_time = last_trail_bo.capture_time
                    pre_capture_time = last_trail_bo.pre_capture_time

                    if (
                        gantry_time is not None
                        and is_not_blank(cur_capture_time)
                        and is_not_blank(pre_capture_time)
                    ):
                        date1 = _parse_date_time(cur_capture_time)
                        date2 = _parse_date_time(pre_capture_time)
                        if date1 is not None and date2 is not None:
                            dif_time = (
                                int(gantry_time.timestamp() * 1000)
                                + int(date1.timestamp() * 1000)
                                - int(date2.timestamp() * 1000)
                            )
                            addbo.next_pass_time = datetime.fromtimestamp(
                                dif_time / 1000
                            )

            self.car_warning_info_service.save_batch(add_car_warning_info_list)

        # 更新缓存
        self.car_warning_info_service.update_redis_warning_list()

        return AjaxResult.success()

    # Java: AjaxResult syncHistoryTrack()
    @transactional
    def sync_history_track(self) -> AjaxResult:
        car_list = self.car_info_service.get_redis_car_list()
        self.save_trail_tracks_history(car_list)
        return AjaxResult.success()

    # Java: AjaxResult syncHistoryTrackNoCar()
    @transactional
    def sync_history_track_no_car(self) -> AjaxResult:
        query = CarInfo()
        query.flag = "noTrack"
        car_list = self.car_info_service.select_list(query)
        self.save_trail_tracks_history(car_list)
        return AjaxResult.success()

    # Java: private void saveTrailTracksHistory(List<CarInfo> carList)
    def save_trail_tracks_history(self, car_list: List[Any]) -> None:
        car_no_list: List[str] = []
        # 找到下一个位置
        addlist: List[ZdataTrailTracks] = []
        for vo in car_list:
            car_no = is_null(vo.car_no)
            key = Constants.car_history_trail + car_no
            trail_info_list = _to_model_list(
                self.redis_cache.get_cache_object(key), TrailInfo
            )
            for trail_info in trail_info_list:
                tracks_bo = trail_info.tracks
                trail_list = trail_info.trail_list  # trailPoints
                tracks_bo.plate_key = car_no
                tracks_bo.point_count = 0
                if trail_list is not None:
                    tracks_bo.track_josn = json.dumps(
                        [item.to_json_dict() for item in trail_list],
                        ensure_ascii=False,
                    )
                    tracks_bo.point_count = len(trail_list)
                car_no_list.append(car_no)
                addlist.append(tracks_bo)
        if car_no_list:
            self.trail_tracks_service.remove_real_data(car_no_list)
        if addlist:
            self.trail_tracks_service.save_batch(addlist)

    # ---------------------------------------------------------------- 轨迹几何

    # Java: List<Geometry> getCarGeometry(ZdataTrailTracks tracksBo, List<TrailBo> josnList)
    def get_car_geometry(
        self, tracks_bo: Optional[ZdataTrailTracks], josn_list: List[TrailBo]
    ) -> List[Geometry]:
        """按桩号把 Redis 里缓存的 ``Geometry.paths`` 拼成一段连续轨迹。"""
        if tracks_bo is None:
            tracks_bo = ZdataTrailTracks()

        raod_trail_list: List[Geometry] = []
        # 去掉重复的桩号 —— Java 用 ``LinkedHashMap`` 保序，这里用 dict（3.7+ 同样保序）
        road_group: Dict[str, List[TrailBo]] = {}

        for trail_bo in josn_list:
            road_code = is_null(trail_bo.road_code)  # 路线编号
            pileno = is_null(trail_bo.pileno)  # 桩号
            if is_not_blank(road_code) and is_not_blank(pileno):
                # Java 的 replace 顺序不能换：先 ZK/YK 再 K，否则 "ZK123" 会剩 "Z123"
                chang_pileno = (
                    pileno.replace("+", ".")
                    .replace("ZK", "")
                    .replace("YK", "")
                    .replace("K", "")
                )
                # Java: new BigDecimal(changPileno) —— 非法数值抛 NumberFormatException -> 500
                trail_bo.pileno_dec = Decimal(chang_pileno)
                road_group.setdefault(road_code, []).append(trail_bo)

        road_map = self.geometry_service.get_redis_list()

        for road_code, trail_bo_list in road_group.items():
            reserver = 0
            if trail_bo_list and len(trail_bo_list) > 0:
                # 首点桩号 > 末点桩号 => 这段轨迹是反向采到的
                if _to_decimal(trail_bo_list[0].pileno_dec) > _to_decimal(
                    trail_bo_list[-1].pileno_dec
                ):
                    reserver = 1

                # 按照桩号排序
                trail_bo_list = sorted(
                    trail_bo_list, key=lambda item: _to_decimal(item.pileno_dec)
                )

                # -------------- 起点桩号
                first_dec = _to_decimal(trail_bo_list[0].pileno_dec)
                # Java: setScale(4, HALF_UP).intValue() —— intValue() 是截断，不是四舍五入
                sq = int(first_dec.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP))
                sz = 0
                if len(trail_bo_list) > 1:
                    # ------------ 终点桩号
                    end_dec = _to_decimal(trail_bo_list[-1].pileno_dec)
                    sz = (
                        int(end_dec.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)) + 1
                    )
                else:
                    sz = sq

                # 四种区间重叠情况（见 Java 注释），命中任一即算覆盖，可重复计数
                add_list: List[Any] = []
                filt_list = road_map.get(road_code)
                if filt_list and len(filt_list) > 0:
                    for filt_bo in filt_list:
                        qd = _field_of(filt_bo, "qdzh")
                        zd = _field_of(filt_bo, "zdzh")
                        qd = 0 if qd is None else qd
                        zd = 0 if zd is None else zd

                        count_num = 0
                        if qd <= sq and zd >= sz:
                            count_num += 1
                        if qd > sq and qd < sz:
                            count_num += 1
                        if zd > sq and zd < sz:
                            count_num += 1
                        if qd >= sq and zd <= sz:
                            count_num += 1

                        if count_num > 0:
                            add_list.append(filt_bo)

                if add_list and len(add_list) > 0:
                    # 把路线所有的轨迹点拼接出来
                    rtn_geometry = Geometry()
                    rtn_geometry.lxbh = road_code
                    paths_array: List[Any] = []
                    for query_geometry in add_list:
                        paths = _field_of(query_geometry, "paths")
                        if is_not_blank(paths):
                            # Java: JSONUtil.parseArray(paths) 后 addAll 展平一层
                            paths_array.extend(json.loads(paths))
                    if reserver == 1:
                        # Java: Collections.reverse(pathsJSONArray) —— 原地反转
                        paths_array.reverse()
                    # Java: JSONArray.toString() —— fastjson 紧凑输出（无空格）
                    rtn_geometry.paths = json.dumps(
                        paths_array, ensure_ascii=False, separators=(",", ":")
                    )
                    raod_trail_list.append(rtn_geometry)
        return raod_trail_list

    # Java: TrailDevCountBO getTrailDevBO(ZdataTrailTracks tracks, List<TrailBo> josnList)
    def get_trail_dev_bo(
        self, tracks: Optional[ZdataTrailTracks], josn_list: List[TrailBo]
    ) -> TrailDevCountBO:
        """按设备归并轨迹点，并统计「有门架抓拍但无门架流水」的异常数。"""
        if tracks is None:
            tracks = ZdataTrailTracks()

        trail_dev_count_bo = TrailDevCountBO()
        except_num = 0
        trail_dev_list: List[TrailDevBO] = []
        except_msg = ""

        dev_map: Dict[str, List[TrailBo]] = {}
        rtn_list: List[TrailBo] = []

        for trail_bo in josn_list:
            state_type = is_null(trail_bo.state_type)
            dev_name = is_null(trail_bo.dev_name)
            if (
                state_type == Constants.GANTRY_CAPTURE
                or state_type == Constants.FeeRecord
            ):
                # 门架抓拍 / 门架流水
                if is_not_blank(dev_name):
                    temp_list: List[TrailBo] = []
                    if dev_name in dev_map:
                        temp_list = dev_map[dev_name]  # 重复的对象合并
                    else:
                        rtn_list.append(trail_bo)  # 去掉重复的
                    temp_list.append(trail_bo)
                    dev_map[dev_name] = temp_list
                else:
                    rtn_list.append(trail_bo)
            else:
                rtn_list.append(trail_bo)

        for trail_bo in rtn_list:
            trail_dev_bo = TrailDevBO()
            state_type = is_null(trail_bo.state_type)
            dev_name = is_null(trail_bo.dev_name)
            trail_dev_bo.status = "0"  # 默认为正常
            trail_list: List[TrailBo] = []

            if (
                state_type == Constants.GANTRY_CAPTURE
                or state_type == Constants.FeeRecord
            ):
                if dev_name in dev_map:
                    trail_list = dev_map[dev_name]
                    # 判断异常数量
                    count_gantry_capture = 0
                    count_fee_record = 0
                    for rtn_trail_bo in trail_list:
                        state_type_dif = is_null(rtn_trail_bo.state_type)
                        if state_type_dif == Constants.GANTRY_CAPTURE:
                            # 门架抓拍
                            count_gantry_capture += 1
                        elif state_type_dif == Constants.FeeRecord:
                            # 卡口流水
                            count_fee_record += 1
                    if count_gantry_capture > 0 and count_fee_record == 0:
                        trail_dev_bo.status = "1"  # 异常数据
                        except_num += 1
                else:
                    trail_list.append(trail_bo)
            else:
                trail_list.append(trail_bo)
            trail_dev_bo.dev_name = dev_name
            trail_dev_bo.trail_list = trail_list
            trail_dev_list.append(trail_dev_bo)

        trail_dev_count_bo.except_num = except_num
        trail_dev_count_bo.trail_dev_list = trail_dev_list
        trail_dev_count_bo.trail_list = josn_list

        tips = ""
        if tracks.start_lon_dec is None or tracks.strat_lat_dec is None:
            tips = "起始位置"
        if tracks.end_lon_dec is None or tracks.end_lat_dec is None:
            if tips == "":
                tips = "终点位置"
            else:
                tips = tips + "和终点位置"
        if is_not_blank(tips):
            except_msg = (
                "由于无法获取轨迹"
                + tips
                + "，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。"
            )
        trail_dev_count_bo.except_msg = except_msg

        return trail_dev_count_bo

    # Java: List<Geometry> getCarGeometryByPlan(ZdataTrailTracks tracksBo, List<TrailBo> josnList)
    def get_car_geometry_by_plan(
        self, tracks_bo: Optional[ZdataTrailTracks], josn_list: List[TrailBo]
    ) -> List[Geometry]:
        """起终点齐全时走腾讯地图 API（``LonLatPathsUtils``）规划路线，带 Redis 缓存。"""
        if tracks_bo is None:
            tracks_bo = ZdataTrailTracks()

        if (
            tracks_bo.start_lon_dec is None
            or tracks_bo.strat_lat_dec is None
            or tracks_bo.end_lon_dec is None
            or tracks_bo.end_lat_dec is None
        ):
            # Java: log.info("起始和终点位置不存在-----------");
            return self.get_car_geometry(tracks_bo, josn_list)

        key = (
            Constants.car_lxgh
            + is_null(tracks_bo.plate_key)
            + is_null(tracks_bo.start_lon_dec)
            + is_null(tracks_bo.strat_lat_dec)
            + is_null(tracks_bo.end_lon_dec)
            + is_null(tracks_bo.end_lat_dec)
            + str(len(josn_list))
        )

        lxbh = ""
        way_points: List[str] = []
        for trail_bo in josn_list:
            if trail_bo.lon is not None and trail_bo.lat is not None:
                lon = float(trail_bo.lon)
                lat = float(trail_bo.lat)
                road_code = trail_bo.road_code
                # Java: "".equals(lxbh) && !"".equals(roadCode) —— roadCode 为 null 时
                # 反而不等于 ""，会把 lxbh 写成 null 并就此定型。照抄。
                if lxbh == "" and road_code != "":
                    lxbh = road_code

                doubles = gps84_to_gcj02(lat, lon)
                way_points.append(str(doubles[0]) + "," + str(doubles[1]))

        paths: Optional[str]
        cached = self.redis_cache.get_cache_object(key)
        if cached is not None:
            # Java: CommonUtil.isNull(obj) —— 命中缓存时返回值不会为 null
            paths = is_null(cached)
        else:
            paths = self.lon_lat_paths_utils.calc_lon_and_lat_paths(
                _plain_string(tracks_bo.start_lon_dec),
                _plain_string(tracks_bo.strat_lat_dec),
                _plain_string(tracks_bo.end_lon_dec),
                _plain_string(tracks_bo.end_lat_dec),
                "",
                ";".join(way_points),
            )
            if paths is not None:
                self.redis_cache.set_cache_object(key, paths)

        if paths is None:
            # Java: log.info("调用腾讯地图API找不到位置不存在-----------");
            return self.get_car_geometry(tracks_bo, josn_list)

        rtn_geometry = Geometry()
        rtn_geometry.lxbh = lxbh
        rtn_geometry.paths = paths
        return [rtn_geometry]

    # Java: List<Geometry> getCarGeometryByPlanNew(ZdataTrailTracks tracksBo, List<TrailBo> josnList)
    def get_car_geometry_by_plan_new(
        self, tracks_bo: Optional[ZdataTrailTracks], josn_list: List[TrailBo]
    ) -> List[Geometry]:
        """起终点收费站齐全时走本地路网 API（``RoadPathService``），否则退到腾讯地图。"""
        api_map = "1"
        cache_object = self.redis_cache.get_cache_object("sys_config:api_map")
        if is_not_blank(cache_object):
            api_map = is_null(cache_object)

        if is_null(api_map) == "0":
            return self.get_car_geometry_by_plan(tracks_bo, josn_list)

        if tracks_bo is None:
            tracks_bo = ZdataTrailTracks()

        node_ids: List[str] = []

        if is_not_blank(tracks_bo.entollstationid) and is_not_blank(
            tracks_bo.extollstationid
        ):
            node_ids.append(tracks_bo.entollstationid)  # 起点

            key = (
                Constants.car_lxgh
                + is_null(tracks_bo.plate_key)
                + is_null(tracks_bo.entollstationid)
                + is_null(tracks_bo.extollstationid)
                + str(len(josn_list))
            )

            lxbh = ""
            for trail_bo in josn_list:
                road_code = trail_bo.road_code
                # 同 getCarGeometryByPlan：null 会把 lxbh 写成 null
                if lxbh == "" and road_code != "":
                    lxbh = road_code
                if is_not_blank(trail_bo.dev_code):
                    node_ids.append(trail_bo.dev_code)  # 中间的轨迹点
            node_ids.append(tracks_bo.extollstationid)  # 终点

            paths: Optional[str]
            cached = self.redis_cache.get_cache_object(key)
            if cached is not None:
                paths = is_null(cached)
            else:
                paths = self.road_path_service.get_shortest_road_path(node_ids)
                if paths is not None:
                    # Java: log.info("调用本地API获取path-----------");
                    self.redis_cache.set_cache_object(key, paths)

            if paths is None:
                # Java: log.info("调用本地API找不到位置不存在-----------");
                return self.get_car_geometry_by_plan(tracks_bo, josn_list)

            rtn_geometry = Geometry()
            rtn_geometry.lxbh = lxbh
            rtn_geometry.paths = paths
            return [rtn_geometry]

        # Java: log.info("起始和终点位置不存在-----------");
        return self.get_car_geometry_by_plan(tracks_bo, josn_list)


_SERVICE: Optional[CarTrackInfoService] = None


def get_car_track_info_service() -> CarTrackInfoService:
    """Java: ``@Autowired ICarTrackInfoService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarTrackInfoService()
    return _SERVICE


def reset_car_track_info_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarTrackInfoService",
    "get_car_track_info_service",
    "reset_car_track_info_service",
    "DATE_TIME_PATTERN",
    "DATE_PATTERN",
    "DEFAULT_CAPTURE_TIME",
    "DEFAULT_SYNC_CURRENT_TIME",
    "THREE_MINUTES_IN_MILLIS",
    "DEFAULT_WARNING_TIMESPAN",
    "FOUR_PLACES",
]
