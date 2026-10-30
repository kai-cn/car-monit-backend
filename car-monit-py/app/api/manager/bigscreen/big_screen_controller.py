"""大屏接口 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java

**12** 个映射，**一个 ``@PreAuthorize`` 都没有**
------------------------------------------------
==========================  ==================================  ==========================
Java                        Method / Path                       权限点
==========================  ==================================  ==========================
``getCarStatistics``        GET ``/carStatistics``              **无**
``getCarLocation``          GET ``/carLocation``                **无**
``getSectionList``          GET ``/sectionList``                **无**
``getTollList``             GET ``/tollGantryFwqList``          **无**
``carVoList``               GET ``/carVoList``                  **无**
``getCarAudit``             GET ``/carAudit``                   **无**
``getCarWarning``           GET ``/carWarning``                 **无**
``getExceptionCar``         GET ``/exceptionCar``               **无**
``topTen``                  GET ``/topTen``                     **无**
``getOrgList``              GET ``/orgList``                    **无**
``incomeStatistic``         GET ``/incomeStatistic``            **无**
``list``                    GET ``/exceptRecordList``           **无**
==========================  ==================================  ==========================

类上只有 ``@RequestMapping("/manager/bigScreen")`` —— **路径里的 ``bigScreen`` 是驼峰**
（与包里其它控制器的全小写路径不同），照抄，不要"顺手"改成 ``bigscreen``。

``@CrossOrigin(origins = "*")`` 由全局 ``CORSMiddleware`` 承担（Java 侧本来就是
``SecurityConfig`` + 这个方法注解二者叠加），这里不另挂。

三个必须照抄的业务细节
----------------------
1. ``carLocation`` / ``carWarning`` 共用同一段入参规整：``sectionCode`` 含 ``"all"``
   子串时清空；``type`` 非空时按 ``1``/``2``/``3`` 把 ``code`` 塞进
   ``tollCode`` / ``gantryCode`` / ``fwqbm``，``code`` 为空则塞
   ``StationCapture`` / ``GantryCapture`` / ``ServiceAreaCapture``（**魔法值**，
   不是 ``null``）;
2. ``tollGantryFwqList``：``sectionCode`` 空白直接回**空数组**（不是全量）；
   否则先 ``deleteEnd`` 削掉**一个**尾逗号，再按 ``,`` 切分；切分后整串里只要还含
   ``"all"`` 就把列表**清空**（``in`` 列表为空 → SQL 里那段 ``<if>`` 不生效）；
3. ``exceptRecordList`` 在分页结果里**逐行**补两个字段：``orgId`` 来自
   ``carConfimFreeService.selectOrgId``，``supplementaryStatus`` 在
   ``car_aduit_free`` 里按 ``carId`` 数到 > 0 条时置 ``"1"``（默认 ``"0"``）——
   这是 N+1 查询，Java 原样，不要"优化"成一条 join。
"""

from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.base.domain.dwd_lczt_fwqjcxx import DwdLcztFwqjcxx
from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.service.dwd_lczt_fwqjcxx_service import (
    DwdLcztFwqjcxxService,
    get_dwd_lczt_fwqjcxx_service,
)
from app.base.service.ods_rt_szdn_snapshot_flow_addcode_service import (
    OdsRtSzdnSnapshotFlowAddcodeService,
    get_ods_rt_szdn_snapshot_flow_addcode_service,
)
from app.base.service.ods_szdn_gantry_service import OdsSzdnGantryService, get_ods_szdn_gantry_service
from app.base.service.ods_szdn_section_service import (
    OdsSzdnSectionService,
    get_ods_szdn_section_service,
)
from app.base.service.ods_szdn_toll_service import OdsSzdnTollService, get_ods_szdn_toll_service
from app.base.service.ods_yhgl_v_base_org_service import (
    OdsYhglVBaseOrgService,
    get_ods_yhgl_v_base_org_service,
)
from app.common.constant.constants import (
    GANTRY_CAPTURE,
    SERVICE_AREA_CAPTURE,
    STATION_CAPTURE,
    section_all,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.exception.exceptions import ServiceException
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.string_utils import split_regex
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.vo.bigscreen.car_audit_vo import CarAuditVO
from app.manager.domain.vo.bigscreen.car_location_param import CarLocationParam
from app.manager.domain.vo.bigscreen.income_statistic_param import IncomeStatisticParam
from app.manager.domain.vo.bigscreen.org_vo import OrgVO
from app.manager.domain.vo.bigscreen.section_vo import SectionVO
from app.manager.domain.vo.bigscreen.toll_gantry_fwq_vo import TollGantryFwqVO
from app.manager.service.car_aduit_free_service import (
    CarAduitFreeService,
    get_car_aduit_free_service,
)
from app.manager.service.car_confim_free_service import (
    CarConfimFreeService,
    get_car_confim_free_service,
)
from app.manager.service.car_except_record_service import (
    CarExceptRecordService,
    get_car_except_record_service,
)
from app.manager.service.car_info_service import CarInfoService, get_car_info_service
from app.manager.service.car_suspicious_service import (
    CarSuspiciousService,
    get_car_suspicious_service,
)
from app.manager.service.car_warning_info_service import (
    CarWarningInfoService,
    get_car_warning_info_service,
)

#: ``@RequestMapping("/manager/bigScreen")`` —— 注意 ``bigScreen`` 的驼峰。
router = APIRouter(prefix="/manager/bigScreen", tags=["manager-big-screen"])

#: 路段"全部"的文案（``getSectionList`` 手工插在首条）。
SECTION_ALL_NAME = "全部"

#: ``@RequestParam String type`` 是**必填**：缺失时 Spring 抛
#: ``MissingServletRequestParameterException``，被 ``GlobalExceptionHandler`` 的
#: ``Exception`` 分支接住 → ``code 500`` 回信封。
MISSING_TYPE_MESSAGE = (
    "Required request parameter 'type' for method parameter type String is not present"
)


# --------------------------------------------------------------------------- 协作者

_CAR_INFO: Optional[CarInfoService] = None
_CAR_CONFIM_FREE: Optional[CarConfimFreeService] = None
_CAR_ADUIT_FREE: Optional[CarAduitFreeService] = None
_SECTION: Optional[OdsSzdnSectionService] = None
_TOLL: Optional[OdsSzdnTollService] = None
_GANTRY: Optional[OdsSzdnGantryService] = None
_FWQJCXX: Optional[DwdLcztFwqjcxxService] = None
_CAR_WARNING_INFO: Optional[CarWarningInfoService] = None
_SNAPSHOT_FLOW: Optional[OdsRtSzdnSnapshotFlowAddcodeService] = None
_CAR_SUSPICIOUS: Optional[CarSuspiciousService] = None
_BASE_ORG: Optional[OdsYhglVBaseOrgService] = None
_CAR_EXCEPT_RECORD: Optional[CarExceptRecordService] = None


def _car_info() -> CarInfoService:
    global _CAR_INFO
    if _CAR_INFO is None:
        _CAR_INFO = get_car_info_service()
    return _CAR_INFO


def _car_confim_free() -> CarConfimFreeService:
    global _CAR_CONFIM_FREE
    if _CAR_CONFIM_FREE is None:
        _CAR_CONFIM_FREE = get_car_confim_free_service()
    return _CAR_CONFIM_FREE


def _car_aduit_free() -> CarAduitFreeService:
    global _CAR_ADUIT_FREE
    if _CAR_ADUIT_FREE is None:
        _CAR_ADUIT_FREE = get_car_aduit_free_service()
    return _CAR_ADUIT_FREE


def _section() -> OdsSzdnSectionService:
    global _SECTION
    if _SECTION is None:
        _SECTION = get_ods_szdn_section_service()
    return _SECTION


def _toll() -> OdsSzdnTollService:
    global _TOLL
    if _TOLL is None:
        _TOLL = get_ods_szdn_toll_service()
    return _TOLL


def _gantry() -> OdsSzdnGantryService:
    global _GANTRY
    if _GANTRY is None:
        _GANTRY = get_ods_szdn_gantry_service()
    return _GANTRY


def _fwqjcxx() -> DwdLcztFwqjcxxService:
    global _FWQJCXX
    if _FWQJCXX is None:
        _FWQJCXX = get_dwd_lczt_fwqjcxx_service()
    return _FWQJCXX


def _car_warning_info() -> CarWarningInfoService:
    global _CAR_WARNING_INFO
    if _CAR_WARNING_INFO is None:
        _CAR_WARNING_INFO = get_car_warning_info_service()
    return _CAR_WARNING_INFO


def _snapshot_flow() -> OdsRtSzdnSnapshotFlowAddcodeService:
    global _SNAPSHOT_FLOW
    if _SNAPSHOT_FLOW is None:
        _SNAPSHOT_FLOW = get_ods_rt_szdn_snapshot_flow_addcode_service()
    return _SNAPSHOT_FLOW


def _car_suspicious() -> CarSuspiciousService:
    global _CAR_SUSPICIOUS
    if _CAR_SUSPICIOUS is None:
        _CAR_SUSPICIOUS = get_car_suspicious_service()
    return _CAR_SUSPICIOUS


def _base_org() -> OdsYhglVBaseOrgService:
    global _BASE_ORG
    if _BASE_ORG is None:
        _BASE_ORG = get_ods_yhgl_v_base_org_service()
    return _BASE_ORG


def _car_except_record() -> CarExceptRecordService:
    global _CAR_EXCEPT_RECORD
    if _CAR_EXCEPT_RECORD is None:
        _CAR_EXCEPT_RECORD = get_car_except_record_service()
    return _CAR_EXCEPT_RECORD


def reset_big_screen_controller() -> None:
    """Test helper: drop every cached collaborator so fakes can be injected."""
    global _CAR_INFO, _CAR_CONFIM_FREE, _CAR_ADUIT_FREE, _SECTION, _TOLL, _GANTRY
    global _FWQJCXX, _CAR_WARNING_INFO, _SNAPSHOT_FLOW, _CAR_SUSPICIOUS, _BASE_ORG
    global _CAR_EXCEPT_RECORD
    _CAR_INFO = None
    _CAR_CONFIM_FREE = None
    _CAR_ADUIT_FREE = None
    _SECTION = None
    _TOLL = None
    _GANTRY = None
    _FWQJCXX = None
    _CAR_WARNING_INFO = None
    _SNAPSHOT_FLOW = None
    _CAR_SUSPICIOUS = None
    _BASE_ORG = None
    _CAR_EXCEPT_RECORD = None


# --------------------------------------------------------------------------- 入参绑定

def _income_param(request: Request) -> IncomeStatisticParam:
    """Java: 形参 ``IncomeStatisticParam param``（**没有** ``@RequestBody``）。"""
    return bind_query_params(IncomeStatisticParam, request.query_params)


def _location_param(request: Request) -> CarLocationParam:
    """Java: 形参 ``CarLocationParam param``."""
    return bind_query_params(CarLocationParam, request.query_params)


def _except_param(request: Request) -> CarExceptRecord:
    """Java: 形参 ``CarExceptRecord carExceptRecord``."""
    return bind_query_params(CarExceptRecord, request.query_params)


IncomeParam = Annotated[IncomeStatisticParam, Depends(_income_param)]
LocationParam = Annotated[CarLocationParam, Depends(_location_param)]
ExceptParam = Annotated[CarExceptRecord, Depends(_except_param)]


def _normalise_location_param(param: CarLocationParam) -> None:
    """Java: ``getCarLocation`` / ``getCarWarning`` 里那段逐字相同的规整。

    ``sectionCode`` 含 ``"all"`` 子串（不是相等）就清空 —— 前端可能发
    ``"all,SD01"`` 这种拼串。``type`` 为空时**什么都不做**（``code`` 也不生效）。
    """
    if section_all in is_null(param.section_code):
        param.section_code = ""
    code = is_null(param.code)
    if not is_not_blank(param.type):
        return
    if param.type == "1":
        param.toll_code = code if is_not_blank(code) else STATION_CAPTURE
    elif param.type == "2":
        param.gantry_code = code if is_not_blank(code) else GANTRY_CAPTURE
    elif param.type == "3":
        param.fwqbm = code if is_not_blank(code) else SERVICE_AREA_CAPTURE


# --------------------------------------------------------------------------- 统计

@router.get("/carStatistics", response_model=None)
def get_car_statistics(param: IncomeParam) -> AjaxResult:
    """重点关注的车辆统计. Java: ``@GetMapping(value = "/carStatistics")``."""
    return AjaxResult.success_data(_car_confim_free().get_car_statistics(param))


@router.get("/carLocation", response_model=None)
def get_car_location(param: LocationParam) -> AjaxResult:
    """地图（车辆位置描点）. Java: ``@GetMapping(value = "/carLocation")``."""
    _normalise_location_param(param)
    return AjaxResult.success_data(_car_info().car_location(param))


@router.get("/sectionList", response_model=None)
def get_section_list() -> AjaxResult:
    """路段列表. Java: ``@GetMapping(value = "/sectionList")``.

    数据源是 ``selectOdsSzdnSectionListNew(new OdsSzdnSection())``（空条件 = 全量），
    返回前**手工插**一条 ``{"sectionCode": "all", "sectionName": "全部"}`` 在最前面。
    """
    rows: List[SectionVO] = [
        SectionVO(section_code=item.section_code, section_name=item.section_name)
        for item in _section().select_list_new(OdsSzdnSection())
    ]
    return AjaxResult.success_data(
        [SectionVO(section_code=section_all, section_name=SECTION_ALL_NAME), *rows]
    )


@router.get("/tollGantryFwqList", response_model=None)
def get_toll_list(
    type_: Annotated[Optional[str], Query(alias="type")] = None,
    section_code: Annotated[Optional[str], Query(alias="sectionCode")] = None,
) -> AjaxResult:
    """收费站 / 门架 / 服务区列表. Java: ``@GetMapping(value = "/tollGantryFwqList")``."""
    if type_ is None:
        # Java: ``@RequestParam String type`` 必填 → code 500 回信封
        raise ServiceException(MISSING_TYPE_MESSAGE)
    if is_blank(section_code):
        # Java: ``return AjaxResult.success(new ArrayList<>())`` —— 空数组，不是全量
        return AjaxResult.success_data([])

    stripped = delete_end(section_code)
    section_code_list: List[str] = [] if section_all in stripped else split_regex(stripped, ",")

    collect: List[TollGantryFwqVO] = []
    if type_ == "1":
        query = OdsSzdnToll()
        query.section_code_list = section_code_list
        collect = [
            TollGantryFwqVO(type="1", code=item.toll_code, name=item.toll_name)
            for item in _toll().select_list_new(query)
        ]
    elif type_ == "2":
        query = OdsSzdnGantry()
        query.section_code_list = section_code_list
        collect = [
            TollGantryFwqVO(type="2", code=item.gantry_code, name=item.gantry_name)
            for item in _gantry().select_list_new(query)
        ]
    elif type_ == "3":
        fwq = DwdLcztFwqjcxx()
        fwq.section_code_list = section_code_list
        collect = [
            TollGantryFwqVO(type="3", code=item.fwqbm, name=item.fwqmc)
            for item in _fwqjcxx().select_list_new(fwq)
        ]
    return AjaxResult.success_data(collect)


@router.get("/carVoList", response_model=None)
def car_vo_list() -> AjaxResult:
    """重点车辆库统计. Java: ``@GetMapping(value = "/carVoList")``."""
    return AjaxResult.success_data(_car_info().select_car_vo_list())


@router.get("/carAudit", response_model=None)
def get_car_audit(param: IncomeParam) -> AjaxResult:
    """追缴统计. Java: ``@GetMapping(value = "/carAudit")``.

    两个来源各自可能回 ``null``；为 ``null`` 时保留 ``CarAuditVO`` 的**零初值**
    （不是 ``null``）。顺序固定：先查异常流水，再查确认追缴。
    """
    vo = CarAuditVO()

    escaped = _car_aduit_free().get_car_audit(param)
    if escaped is not None:
        vo.total_amount = escaped.escaped_amount
        vo.total_count = escaped.number

    finished = _car_confim_free().get_car_confirm(param)
    if finished is not None:
        vo.finished_amount = finished.escaped_amount
        vo.finished_count = finished.number

    return AjaxResult.success_data(vo)


@router.get("/carWarning", response_model=None)
def get_car_warning(param: LocationParam) -> AjaxResult:
    """车辆预警. Java: ``@GetMapping(value = "/carWarning")``."""
    _normalise_location_param(param)
    return AjaxResult.success_data(_car_warning_info().select_car_warning_info_list_limit100(param))


@router.get("/exceptionCar", response_model=None)
def get_exception_car() -> AjaxResult:
    """异常数据（最近 10 条）. Java: ``@GetMapping(value = "/exceptionCar")``."""
    return AjaxResult.success_data(_car_suspicious().select_list_limit10())


@router.get("/topTen", response_model=None)
def top_ten() -> AjaxResult:
    """重点车辆通行前 10. Java: ``@GetMapping(value = "/topTen")``."""
    return AjaxResult.success_data(_snapshot_flow().get_top_ten())


@router.get("/orgList", response_model=None)
def get_org_list() -> AjaxResult:
    """机构列表. Java: ``@GetMapping(value = "/orgList")``.

    Java 走 MyBatis-Plus 的 ``lambdaQuery().select(orgCode, orgName).list()`` ——
    只查两列；再逐条拷进 ``OrgVO``（所以响应体只有 ``orgCode`` / ``orgName``）。
    """
    return AjaxResult.success_data(
        [
            OrgVO(org_code=item.org_code, org_name=item.org_name)
            for item in _base_org().select_org_list()
        ]
    )


@router.get("/incomeStatistic", response_model=None)
def income_statistic(param: IncomeParam) -> AjaxResult:
    """堵漏增收统计. Java: ``@GetMapping(value = "/incomeStatistic")``.

    ``queryDateType`` 为空时**默认为 ``"suo"``**（查所），这个默认值在控制器里盖，
    不在 SQL 里 —— 所以传 ``zhan`` 才能查到"按站"的粒度。
    """
    if is_blank(param.query_date_type):
        param.query_date_type = "suo"
    return AjaxResult.success_data(_car_aduit_free().income_statistic(param))


@router.get("/exceptRecordList", response_model=None)
def list(param: ExceptParam) -> TableDataInfo:
    """异常流水分页列表（带补缴状态）. Java: ``@GetMapping("/exceptRecordList")``."""
    start_page()
    data_table = get_data_table(_car_except_record().select_list(param))
    for row in data_table.get_rows() or []:
        row.org_id = _car_confim_free().select_org_id(row.car_id, row.id)
        if _car_aduit_free().count_by_car_id(row.car_id) > 0:
            row.supplementary_status = "1"
    return data_table


__all__ = [
    "router",
    "MISSING_TYPE_MESSAGE",
    "SECTION_ALL_NAME",
    "car_vo_list",
    "get_car_audit",
    "get_car_location",
    "get_car_statistics",
    "get_car_warning",
    "get_exception_car",
    "get_org_list",
    "get_section_list",
    "get_toll_list",
    "income_statistic",
    "list",
    "reset_big_screen_controller",
    "top_ten",
]
