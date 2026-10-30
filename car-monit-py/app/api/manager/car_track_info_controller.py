"""车辆行驶轨迹 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java

**10** 个映射
-------------
============================  ==============================  ================================
Java                          Method / Path                   权限点
============================  ==============================  ================================
``list``                      GET ``/list``                   ``manager:cartrackinfo:list``
``listByCarId``               GET ``/listByCarId``            **无**
``listByCarByTime``           GET ``/listByCarByTime``        **无**
``changeTrailInfo``           PUT ``/changeTrailInfo``        **无**
``carSnapShot``               GET ``/carSnapShot``            **无**
``export``                    GET ``/export``                 ``manager:cartrackinfo:export``
``getInfo``                   GET ``/{id}``                   **无**
``add``                       POST ``""``                     ``manager:cartrackinfo:add``
``edit``                      PUT ``""``                      ``manager:cartrackinfo:edit``
``remove``                    DELETE ``/{ids}``               ``manager:cartrackinfo:remove``
============================  ==============================  ================================

``listByCarId`` 的两条分支（原样照抄）
-------------------------------------
1. **本库有轨迹**（``zdataTrailTracksService.carTrackQuery`` 命中）：只把
   ``trackJosn`` 解析成 ``TrailBo`` 列表，``raodTrailList`` / ``trailDevCountBO``
   一律给**空**（不调用几何服务）。
2. **本库没有轨迹**：调 ``HttpSysUtilApiService.carTrackQueryByCarNo``（固定
   ``pageNum=1`` / ``pageSize=20``，且**忽略**入参里的时间范围 —— 那两行在 Java 里
   被注释掉了），把结果缓存到 ``car_history_trail:<车牌>``，再 ``removeRealData`` +
   ``saveBatch`` **回写本库**，``total`` 取上游的 ``total``。

``trailDevCountBO.exceptNum`` 在两条分支里都写死 ``0``、``trailDevList`` 写死空表 ——
不是遗漏，是 Java 原文。真正的统计只在 ``changeTrailInfo`` 里算。
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.car_para_vo import CarParaVO
from app.base.domain.geometry import Geometry
from app.base.domain.trail_bo import TrailBo
from app.base.domain.trail_dev_count_bo import TrailDevCountBO
from app.base.domain.trail_info import TrailInfo
from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.service.forest.http_sys_util_api_service import HttpSysUtilApiService
from app.base.service.zdata_trail_tracks_service import get_zdata_trail_tracks_service
from app.common.constant.http_status import HttpStatus
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.core.redis.redis_cache import get_redis_cache
from app.common.enums.business_type import BusinessType
from app.common.utils.common_util import is_blank, is_not_blank, is_null
from app.common.utils.json_utils import to_json_string_without_null
from app.common.utils.poi.excel_util import ExcelUtil
from app.common.utils.string_utils import is_not_blank as string_is_not_blank
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_track_info import CarTrackInfo
from app.manager.service.car_query_log_service import get_car_query_log_service
from app.manager.service.car_track_info_service import (
    CarTrackInfoService,
    get_car_track_info_service,
)
from app.common.constant import constants as Constants

logger = logging.getLogger("app.api.manager.car_track_info_controller")

router = APIRouter(prefix="/manager/cartrackinfo", tags=["manager-car-track-info"])

#: Java: ``com.ruoyi.web.controller.manager.CarTrackInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarTrackInfoController"

#: Java: ``util.exportExcel(list, "车辆行驶轨迹数据")``
EXPORT_SHEET_NAME = "车辆行驶轨迹数据"

#: Java: ``queryLog(..., "1", "1")`` —— 模块菜单 1 轨迹单 / 功能 1 查看
QUERY_LOG_MODEL_TYPE = "1"
QUERY_LOG_MENU_POINT = "1"

_SERVICE: Optional[CarTrackInfoService] = None


def _service() -> CarTrackInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_track_info_service()
    return _SERVICE


def reset_car_track_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarTrackInfo:
    """Java: 形参 ``CarTrackInfo carTrackInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarTrackInfo, request.query_params)


def _trail_query(request: Request) -> ZdataTrailTracks:
    """Java: 形参 ``ZdataTrailTracks zdataTrailTracks``（**没有** ``@RequestBody``）."""
    return bind_query_params(ZdataTrailTracks, request.query_params)


def _trail_bo_query(request: Request) -> TrailBo:
    """Java: 形参 ``TrailBo trailBo``（**没有** ``@RequestBody``）."""
    return bind_query_params(TrailBo, request.query_params)


CarTrackInfoParam = Annotated[CarTrackInfo, Depends(_query)]
ZdataTrailTracksParam = Annotated[ZdataTrailTracks, Depends(_trail_query)]
TrailBoParam = Annotated[TrailBo, Depends(_trail_bo_query)]


def _page_total(rows: Any) -> int:
    """Java: ``new PageInfo(list).getTotal()``.

    ``list`` 是 PageHelper 的 ``Page`` 时取分页总数，否则取长度。
    """
    return int(getattr(rows, "total", len(rows) if rows is not None else 0))


def _parse_trail_bo_list(key_value: str) -> List[TrailBo]:
    """Java: ``JSON.parseArray(keyValue, TrailBo.class)``."""
    parsed = json.loads(key_value)
    if not isinstance(parsed, list):
        return []
    return [TrailBo.model_validate(item) for item in parsed]


def _empty_trail_dev_count() -> TrailDevCountBO:
    """两条分支里都写死的那份 ``TrailDevCountBO``（``exceptNum=0`` + 空表）."""
    trail_dev_count_bo = TrailDevCountBO()
    trail_dev_count_bo.except_num = 0
    trail_dev_count_bo.trail_dev_list = []
    return trail_dev_count_bo


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:cartrackinfo:list")
def list_tracks(query: CarTrackInfoParam) -> TableDataInfo:
    """查询车辆行驶轨迹列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的**。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/listByCarId", response_model=None)
def list_by_car_id(query: ZdataTrailTracksParam) -> TableDataInfo:
    """车辆历史轨迹：根据车牌号查询. Java: ``@GetMapping("/listByCarId")``."""
    # ----------------------- 查询自己表结构
    query.car_no = is_null(query.car_no)
    if is_blank(query.car_no):
        query.car_no = "-1"

    start_page()
    carlist = get_zdata_trail_tracks_service().car_track_query(query)

    # 如果查询数据为空
    total_num = _page_total(carlist)

    rtn_list: List[TrailInfo] = []
    if carlist is not None and len(carlist) > 0:
        for tracks_bo in carlist:
            key_value = tracks_bo.track_josn  # 行驶轨迹
            if is_not_blank(key_value):
                josn_list = _parse_trail_bo_list(key_value)
                tracks_bo.trail_points = ""  # 行驶轨迹
                tracks_bo.track_josn = ""
                car_no = is_null(tracks_bo.plate_key)
                trail_info = TrailInfo()
                trail_info.tracks = tracks_bo
                trail_info.trail_list = josn_list
                trail_info.trail_uuid = car_no
                # 路线
                trail_info.raod_trail_list = []
                # 集合列表
                trail_info.trail_dev_count_bo = _empty_trail_dev_count()
                rtn_list.append(trail_info)
    else:
        # ----------------------- 查询接口
        car_para_vo = CarParaVO()
        car_para_vo.car_no = query.car_no  # 车牌号
        # Java 里 applyTime1 / applyTime2 两行是**注释掉的** —— 时间条件不生效
        car_para_vo.page_num = 1
        car_para_vo.page_size = 20

        table_data_info = HttpSysUtilApiService.car_track_query_by_car_no(car_para_vo)

        if table_data_info.get_rows() is not None and len(table_data_info.get_rows()) > 0:
            # Java: JSON.toJSONString(rows) -> JSON.parseArray(...) 只是一次无损往返
            trail_list = [
                TrailInfo.model_validate(item) for item in table_data_info.get_rows()
            ]
            # 车辆的轨迹
            history_key = Constants.car_history_trail + query.car_no
            get_redis_cache().set_cache_object(history_key, trail_list)

            car_no_list: List[str] = []
            # 找到下一个位置
            addlist: List[ZdataTrailTracks] = []
            car_no_list.append(query.car_no)
            for trail_info in trail_list:
                tracks_bo = trail_info.tracks
                car_no = is_null(tracks_bo.plate_key)
                josn_list = trail_info.trail_list  # trailPoints

                tracks_bo.plate_key = car_no
                tracks_bo.point_count = 0
                if josn_list is not None:
                    tracks_bo.track_josn = json.dumps(
                        [item.to_json_dict() for item in josn_list],
                        ensure_ascii=False,
                    )
                    tracks_bo.point_count = len(josn_list)
                addlist.append(tracks_bo)

                # 路线
                trail_info.raod_trail_list = []
                # 集合列表
                trail_info.trail_dev_count_bo = _empty_trail_dev_count()
                rtn_list.append(trail_info)

            if len(car_no_list) > 0:
                get_zdata_trail_tracks_service().remove_real_data(car_no_list)
            if len(addlist) > 0:
                get_zdata_trail_tracks_service().save_batch(addlist)

            total_num = table_data_info.get_total()

    rsp_data = TableDataInfo()
    rsp_data.set_code(HttpStatus.SUCCESS)
    rsp_data.set_msg("查询成功")
    rsp_data.set_rows(rtn_list)
    rsp_data.set_total(total_num)
    return rsp_data


@router.get("/listByCarByTime", response_model=None)
def list_by_car_by_time(query: ZdataTrailTracksParam) -> TableDataInfo:
    """车辆历史轨迹：根据时间查询. Java: ``@GetMapping("/listByCarByTime")``.

    方法体上半段（走 ``carTrackQueryByTime`` 的那一版）在 Java 里整段被注释掉了，
    只剩"查自己表结构"这一条路径 —— 因此本接口**不会**回写本库，也**不会**调上游。
    """
    start_page()
    carlist = get_zdata_trail_tracks_service().car_track_query(query)
    rtn_list: List[TrailInfo] = []
    if carlist is not None and len(carlist) > 0:
        for tracks_bo in carlist:
            key_value = tracks_bo.track_josn  # 行驶轨迹
            if is_not_blank(key_value):
                josn_list = _parse_trail_bo_list(key_value)
                tracks_bo.trail_points = ""  # 行驶轨迹
                tracks_bo.track_josn = ""
                car_no = is_null(tracks_bo.plate_key)
                trail_info = TrailInfo()
                trail_info.tracks = tracks_bo
                trail_info.trail_list = josn_list
                trail_info.trail_uuid = car_no
                # 路线
                trail_info.raod_trail_list = []
                # 集合列表
                trail_info.trail_dev_count_bo = _empty_trail_dev_count()
                rtn_list.append(trail_info)

    rsp_data = TableDataInfo()
    rsp_data.set_code(HttpStatus.SUCCESS)
    rsp_data.set_msg("查询成功")
    rsp_data.set_rows(rtn_list)
    rsp_data.set_total(_page_total(carlist))
    return rsp_data


@router.put("/changeTrailInfo", response_model=None)
@log(title="车辆行驶轨迹", business_type=BusinessType.UPDATE, java_method="changeTrailInfo")
def change_trail_info(trail_info: TrailInfo) -> AjaxResult:
    """修改车辆行驶轨迹（重算路线与设备统计）. Java: ``@PutMapping("/changeTrailInfo")``.

    两处照抄点：

    1. ``queryLog`` 记录的是**请求体原样**（在几何计算之前），且方向是"1"/"1"；
    2. ``setTrailList(josnList)`` 之后再取一遍 ``getTrailList()`` —— 看着多余，
       但那是 Java 原文里的"新的数据--------"。
    """
    # 查询日志
    get_car_query_log_service().query_log(
        to_json_string_without_null(trail_info),
        QUERY_LOG_MODEL_TYPE,
        QUERY_LOG_MENU_POINT,
    )
    if trail_info is not None:
        tracks = trail_info.tracks
        josn_list = trail_info.trail_list
        if tracks is not None and josn_list is not None and len(josn_list) > 0:
            # 获取抓拍对象
            trail_info.trail_list = josn_list
            josn_list = trail_info.trail_list  # 新的数据--------------
            raod_trail_list: List[Geometry] = []
            if josn_list is not None and len(josn_list) > 0:
                raod_trail_list = _service().get_car_geometry_by_plan_new(tracks, josn_list)
            trail_info.raod_trail_list = raod_trail_list
            trail_info.trail_dev_count_bo = _service().get_trail_dev_bo(tracks, josn_list)
    return AjaxResult.success_data(trail_info)


@router.get("/carSnapShot", response_model=None)
def car_snap_shot(query: TrailBoParam) -> AjaxResult:
    """抓拍详情. Java: ``@GetMapping(value = "/carSnapShot")``.

    ``StringUtils.isNoneBlank(stateType, pointUuid)`` —— **两个都非空**才发请求；
    否则直接 ``AjaxResult.success()``（没有 ``data`` 键）。
    """
    if query is not None:
        state_type = is_null(query.state_type)
        point_uuid = query.point_uuid
        if string_is_not_blank(state_type) and string_is_not_blank(point_uuid):
            bo = HttpSysUtilApiService.get_by_trail_bo(query)
            return AjaxResult.success_data(bo)
    return AjaxResult.success()


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:cartrackinfo:export")
@log(title="车辆行驶轨迹", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarTrackInfoParam) -> AjaxResult:
    """导出车辆行驶轨迹列表. Java: ``@GetMapping("/export")``.

    走 ``ExcelUtil``（不是 easypoi 模板）：文件名放在 ``msg`` 里。
    """
    rows = _service().select_list(query)
    return ExcelUtil(CarTrackInfo).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取车辆行驶轨迹详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:cartrackinfo:add")
@log(title="车辆行驶轨迹", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarTrackInfo) -> AjaxResult:
    """新增车辆行驶轨迹. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:cartrackinfo:edit")
@log(title="车辆行驶轨迹", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarTrackInfo) -> AjaxResult:
    """修改车辆行驶轨迹. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:cartrackinfo:remove")
@log(title="车辆行驶轨迹", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除车辆行驶轨迹. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "QUERY_LOG_MENU_POINT",
    "QUERY_LOG_MODEL_TYPE",
    "add",
    "car_snap_shot",
    "change_trail_info",
    "edit",
    "export",
    "get_info",
    "list_by_car_by_time",
    "list_by_car_id",
    "list_tracks",
    "remove",
    "reset_car_track_info_controller",
]
