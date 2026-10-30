"""可疑车辆 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java

**15** 个映射
------------
===============================  ==================================  ==================================================================
Java                             Method / Path                       权限点
===============================  ==================================  ==================================================================
``list``                         GET ``/list``                       ``manager:suspicious:list``
``listCarNo``                    GET ``/listCarNo``                  **无**
``listFileCarNo``                GET ``/listFileCarNo``              **无**
``exportAbnormalPassage``        GET ``/exportAbnormalPassage``      **无**（easypoi **Word**）
``listAll``                      GET ``/listAll``                    **无**
``export``                       GET ``/export``                     ``manager:suspicious:export``
``getInfo``                      GET ``/{id}``                       **无**
``add``                          POST ``""``                         ``manager:suspicious:add``
``edit``                         PUT ``""``                          ``manager:suspicious:edit``
``remove``                       DELETE ``/{ids}``                   ``manager:suspicious:remove``
``check``                        PUT ``/check``                      **无**（``@PreAuthorize`` 被注释掉了）
``syncSuspiciousCarTask``        POST ``/syncSuspiciousCarTask``     **无**（改用 SHA1 签名校验）
``listHistory``                  GET ``/listHistory``                ``manager:suspicious:list``
``gethistoryInfo``               GET ``/history/{id}``               **无**
``exportHistory``                GET ``/exportHistory``              ``manager:suspicious:export``
===============================  ==================================  ==================================================================

三处必须照抄的地方
------------------
1. ``list`` / ``export`` / ``listHistory`` / ``exportHistory`` 四个接口都先做同一段
   "路段"归一化 —— ``deleteEnd(sectionCode)`` 后若**包含** ``Constants.section_all``
   （``"all"``）就把 ``sectionCode`` 清空；再把 ``code`` 复制到 ``trackNames``；
2. ``listFileCarNo`` 的 ``escapedTypeName`` 是**循环拼串**，只保留命中字典的值，
   且末尾**带着**逗号（Java 没削）；``chargeAmount`` 等三个金额是
   ``BigDecimal.toString()``，所以小数位跟着源数据走；
3. ``syncSuspiciousCarTask`` 的签名 = ``SHA1(signatureKey + timeStamp)``，
   三个入参任一为空就返回 ``"参数错误"``，签名不符返回 ``"错误，签名验证失败！"``。

路由声明顺序与 Java **不同**（Java 静态路径优先，FastAPI 按声明顺序匹配）:
``GET /{id}`` 必须排在 ``/list``、``/listAll``、``/export``、``/listHistory`` … 之后，
否则 ``/manager/suspicious/listHistory`` 会被 ``/{id}`` 抢占。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.base.domain.suspicious_car_vo import SuspiciousCarVO
from app.common.constant import constants as Constants
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.file_type_utils import get_file_type
from app.common.utils.image_utils import is_image
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.common.utils.poi.word_export import ImageEntity, WordExportUtil
from app.common.utils.security_sha1_utils import sha_encode
from app.common.utils.string_utils import split_regex
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_suspicious import CarSuspicious
from app.manager.domain.car_suspicious_check import CarSuspiciousCheck
from app.manager.service.car_suspicious_service import (
    CarSuspiciousService,
    get_car_suspicious_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service
from app.system.service.sys_file_service import get_file_service

logger = logging.getLogger("app.api.manager.car_suspicious_controller")

router = APIRouter(prefix="/manager/suspicious", tags=["manager-car-suspicious"])

#: Java: ``com.ruoyi.web.controller.manager.CarSuspiciousController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarSuspiciousController"

#: Java: ``String url = "templates/export/carSuspicious.xlsx";``
EXPORT_TEMPLATE = "templates/export/carSuspicious.xlsx"
#: Java: ``String url = "templates/export/carSuspicious.docx";``
WORD_EXPORT_TEMPLATE = "templates/export/carSuspicious.docx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"
#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: ``listCarNo`` 在车牌为空时替换成的魔数
EMPTY_CAR_NO_PLACEHOLDER = "-1"

#: ``syncSuspiciousCarTask`` 的固定 ``addFlag``
SYNC_ADD_FLAG = "task"

#: ``exportAbnormalPassage`` 的图片边长（px）—— Java: ``new ImageEntity(byteObject, 250, 250)``
IMAGE_SIZE = 250

PARAM_ERROR_MESSAGE = "参数错误"
SIGNATURE_ERROR_MESSAGE = "错误，签名验证失败！"

DICT_PLATE_COLOR = "plate_color"
DICT_CAR_TYPE = "car_type"
DICT_CAR_VEHICLE = "car_vehicle"
DICT_ESCAPED_TYPE = "escaped_type"
DICT_IS_EXCEPT = "is_except"
DICT_CHECK_STATUS = "check_status"
DICT_RUN_TYPE = "run_type"

_SERVICE: Optional[CarSuspiciousService] = None


def _service() -> CarSuspiciousService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_suspicious_service()
    return _SERVICE


def reset_car_suspicious_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarSuspicious:
    """Java: 形参 ``CarSuspicious carSuspicious``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarSuspicious, request.query_params)


CarSuspiciousParam = Annotated[CarSuspicious, Depends(_query)]


# --------------------------------------------------------------------------- 列表


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:suspicious:list")
def list_car_suspicious(query: CarSuspiciousParam) -> TableDataInfo:
    """查询可疑车辆列表：菜单列表. Java: ``@GetMapping("/list")``."""
    start_page()
    _normalize_range(query)
    return get_data_table(_service().select_list(query))


@router.get("/listCarNo", response_model=None)
def list_car_suspicious_by_car_no(query: CarSuspiciousParam) -> TableDataInfo:
    """查询可疑车辆列表：根据车牌号查询. Java: ``@GetMapping("/listCarNo")``."""
    start_page()
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    return get_data_table(_service().select_list(query))


@router.get("/listFileCarNo", response_model=None)
def list_file_car_no(query: CarSuspiciousParam) -> TableDataInfo:
    """查询可疑车辆列表：证明材料. Java: ``@GetMapping("/listFileCarNo")``.

    逐行再走一次 ``selectCarSuspiciousById``（为了拿到 ``checkList``），
    金额三兄弟用 ``BigDecimal.toString()``，``escapedTypeName`` 末尾**保留**逗号。
    """
    start_page()
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    query.is_except = "1"
    query.check_status = "1"  # 是可疑车俩并且

    rows = _service().select_list(query)
    escaped_type_map: Dict[str, str] = get_dict_data_service().select_dict_data_map(
        DICT_ESCAPED_TYPE
    )

    rtn_list: List[CarSuspicious] = []
    for item in rows:
        rtn = _service().select_by_id(item.id)
        if rtn is not None and rtn.check_list is not None:
            charge_amount = Decimal("0")
            total_amount = Decimal("0")
            dif_amount = Decimal("0")
            for check in rtn.check_list:
                charge_amount = charge_amount + check.charge_amount
                total_amount = total_amount + check.total_amount
                dif_amount = dif_amount + check.dif_amount
            rtn.charge_amount = str(charge_amount)
            rtn.total_amount = str(total_amount)
            rtn.dif_amount = str(dif_amount)

            # 需要循环 : 逃费类型
            buss_name = ""
            buss_type = delete_end(rtn.escaped_type)
            if is_not_blank(buss_type):
                for buss_type_str in split_regex(buss_type, ","):
                    if buss_type_str in escaped_type_map:
                        buss_name = buss_name + escaped_type_map[buss_type_str] + ","
                rtn.escaped_type_name = buss_name
        rtn_list.append(rtn)
    return get_data_table(rtn_list)


@router.get("/listAll", response_model=None)
def list_all_car_suspicious(query: CarSuspiciousParam) -> TableDataInfo:
    """查询可疑车辆列表：异常流水弹窗. Java: ``@GetMapping("/listAll")``."""
    start_page()
    return get_data_table(_service().select_list(query))


# --------------------------------------------------------------------------- 导出


@router.get("/exportAbnormalPassage", response_model=None)
def export_abnormal_passage(carSuspiciousId: str = "") -> Response:  # noqa: N803
    """导出通行异常（**Word**）. Java: ``@GetMapping("/exportAbnormalPassage")``.

    ``carSuspiciousId`` 是**必填的 query 参数**（Java 形参没有 ``@PathVariable``）。
    返回值是 ``void``，写完响应体就结束。
    """
    car_suspicious = _service().select_by_id(carSuspiciousId)

    query_bo = CarSuspiciousCheck()
    query_bo.car_id = carSuspiciousId
    check_list = _service().car_suspicious_check_service.select_list(query_bo)

    dict_service = get_dict_data_service()
    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_PLATE_COLOR)
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)

    data: Dict[str, Any] = {}
    data["plateColor"] = (
        ""
        if car_suspicious.plate_color is None
        else is_null(plate_color_map.get(car_suspicious.plate_color))
    )
    data["carNo"] = is_null(car_suspicious.car_no)
    data["carType"] = (
        ""
        if car_suspicious.car_type is None
        else is_null(car_type_map.get(car_suspicious.car_type))
    )
    # Java: 字典没命中时**退回原始值**（不是空串）
    if car_suspicious.car_vehicle is None:
        car_vehicle = ""
    else:
        car_vehicle = car_vehicle_map.get(car_suspicious.car_vehicle)
    data["carVehicle"] = (
        car_suspicious.car_vehicle if car_vehicle is None else car_vehicle
    )
    data["carNum"] = is_null(car_suspicious.car_num)
    data["inStation"] = is_null(car_suspicious.in_station)
    data["inTime"] = is_null(
        parse_date_to_str(YYYY_MM_DD_HH_MM_SS, car_suspicious.in_time)
    )
    data["outstation"] = is_null(car_suspicious.out_station)
    data["outTime"] = is_null(
        parse_date_to_str(YYYY_MM_DD_HH_MM_SS, car_suspicious.out_time)
    )
    data["gantrytStation"] = is_null(car_suspicious.gantryt_station)
    data["gantryTime"] = is_null(
        parse_date_to_str(YYYY_MM_DD_HH_MM_SS, car_suspicious.gantry_time)
    )
    data["outGantrytStation"] = is_null(car_suspicious.out_gantryt_station)
    data["outGantryTime"] = is_null(
        parse_date_to_str(YYYY_MM_DD_HH_MM_SS, car_suspicious.out_gantry_time)
    )

    # 需要循环 : 逃费类型
    buss_name = ""
    buss_type = delete_end(car_suspicious.escaped_type)
    if is_not_blank(buss_type):
        for buss_type_str in split_regex(buss_type, ","):
            if buss_type_str in escaped_type_map:
                buss_name = buss_name + escaped_type_map[buss_type_str] + ","
    data["escapedType"] = delete_end(buss_name)

    if check_list is None:
        data["chargeAmount"] = ""
        data["totalAmount"] = ""
        data["difAmount"] = ""
    else:
        charge_amount = Decimal("0")
        total_amount = Decimal("0")
        dif_amount = Decimal("0")
        for check in check_list:
            charge_amount = charge_amount + check.charge_amount
            total_amount = total_amount + check.total_amount
            dif_amount = dif_amount + check.dif_amount
        data["chargeAmount"] = str(charge_amount)
        data["totalAmount"] = str(total_amount)
        data["difAmount"] = str(dif_amount)

    is_except = is_null(car_suspicious.is_except)
    data["isExcept"] = (
        "无逃费" if is_except == "0" else ("确认逃费" if is_except == "1" else "")
    )
    data["exceptRemark"] = is_null(car_suspicious.except_remark)

    if is_not_blank(car_suspicious.except_file_ids):
        sys_files = get_file_service().select_sys_file_by_ids(
            car_suspicious.except_file_ids
        )
        index = 1
        for sys_file in sys_files:
            if is_image(sys_file.type):
                byte_object = get_file_service().get_byte_object(sys_file.id)
                if byte_object is None:
                    # Java: new ImageEntity(null, ...) 会让 easypoi 自己崩；这里跳过
                    continue
                image = ImageEntity(byte_object, IMAGE_SIZE, IMAGE_SIZE)
                image.set_type(ImageEntity.DATA)
                image.extension = _image_extension(sys_file.type)
                data["susImg" + str(index)] = image
                index += 1

    try:
        document = WordExportUtil.export_word07(WORD_EXPORT_TEMPLATE, data)
        content = document.to_bytes()
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出通行异常失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:suspicious:export")
@log(title="可疑车辆", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarSuspiciousParam) -> Response:
    """导出可疑车辆列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    start_page()
    _normalize_range(query)

    rows: List[CarSuspicious] = _service().select_list(query)
    dict_service = get_dict_data_service()
    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_PLATE_COLOR)
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)
    is_except_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_IS_EXCEPT)
    check_status_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CHECK_STATUS)
    # Java 取了 run_type 但 ``setPassType`` 那行是注释掉的 —— 保留这次查询，不用结果
    dict_service.select_dict_data_map(DICT_RUN_TYPE)

    for item in rows:
        _localize_for_export(
            item,
            plate_color_map,
            car_type_map,
            car_vehicle_map,
            escaped_type_map,
            is_except_map,
            check_status_map,
        )

    return _export_excel(rows)


@router.get("/exportHistory", response_model=None)
@pre_authorize_permi("manager:suspicious:export")
@log(title="可疑车辆", business_type=BusinessType.EXPORT, java_method="exportHistory")
def export_history(query: CarSuspiciousParam) -> Response:
    """导出可疑车辆历史列表. Java: ``@GetMapping("/exportHistory")``."""
    start_page()
    _normalize_range(query)

    rows: List[CarSuspicious] = _service().select_list_history(query)
    dict_service = get_dict_data_service()
    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_PLATE_COLOR)
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)
    is_except_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_IS_EXCEPT)
    check_status_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CHECK_STATUS)
    dict_service.select_dict_data_map(DICT_RUN_TYPE)

    for item in rows:
        _localize_for_export(
            item,
            plate_color_map,
            car_type_map,
            car_vehicle_map,
            escaped_type_map,
            is_except_map,
            check_status_map,
        )

    return _export_excel(rows)


# --------------------------------------------------------------------------- 历史


@router.get("/listHistory", response_model=None)
@pre_authorize_permi("manager:suspicious:list")
def list_history(query: CarSuspiciousParam) -> TableDataInfo:
    """查询可疑车辆历史列表. Java: ``@GetMapping("/listHistory")``."""
    start_page()
    _normalize_range(query)
    return get_data_table(_service().select_list_history(query))


@router.get("/history/{id}", response_model=None)
def get_history_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取可疑车辆历史详细信息. Java: ``@GetMapping(value = "/history/{id}")``."""
    return AjaxResult.success_data(_service().select_history_by_id(id))


# --------------------------------------------------------------------------- 详情 / 增删改


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002
    """获取可疑车辆详细信息. Java: ``@GetMapping(value = "/{id}")``.

    **必须**声明在所有静态 ``GET`` 路径之后（见模块 docstring）。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:suspicious:add")
@log(title="可疑车辆", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarSuspicious) -> AjaxResult:
    """新增可疑车辆. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:suspicious:edit")
@log(title="可疑车辆", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarSuspicious) -> AjaxResult:
    """修改可疑车辆. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:suspicious:remove")
@log(title="可疑车辆", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除可疑车辆. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


@router.put("/check", response_model=None)
@log(title="可疑车辆", business_type=BusinessType.UPDATE, java_method="check")
def check(entity: CarSuspicious) -> AjaxResult:
    """可疑车辆核实. Java: ``@PutMapping("/check")`` —— **没有**权限点."""
    return _service().cherk_car_suspicious(entity)


# --------------------------------------------------------------------------- 同步


@router.post("/syncSuspiciousCarTask", response_model=None)
def sync_suspicious_car_task(suspicious_car_vo: SuspiciousCarVO) -> AjaxResult:
    """同步可疑车辆（定时任务回调）. Java: ``@PostMapping("/syncSuspiciousCarTask")``.

    校验顺序照抄：三个入参任一为空 -> ``"参数错误"``；签名不符 -> ``"错误，签名验证失败！"``。
    """
    signature_key = suspicious_car_vo.signature_key
    time_stamp = suspicious_car_vo.time_stamp
    signature = suspicious_car_vo.signature
    if is_not_blank(signature_key) and is_not_blank(signature) and time_stamp is not None:
        encode = sha_encode(f"{signature_key}{time_stamp}")
        if encode != signature:
            return AjaxResult.error_message(SIGNATURE_ERROR_MESSAGE)
    else:
        return AjaxResult.error_message(PARAM_ERROR_MESSAGE)

    trail_info_list = suspicious_car_vo.trail_info_list
    if trail_info_list is not None and len(trail_info_list) > 0:
        _service().sync_suspicious_car(SYNC_ADD_FLAG, trail_info_list)
    return AjaxResult.success()


# --------------------------------------------------------------------------- 内部


def _normalize_range(query: CarSuspicious) -> None:
    """Java: ``list`` / ``export`` / ``listHistory`` / ``exportHistory`` 共用的四行.

    .. code-block:: java

        String sectionCode = CommonUtil.deleteEnd(carSuspicious.getSectionCode());
        if (CommonUtil.isNotBlank(sectionCode)){
            if (sectionCode.indexOf(Constants.section_all) > -1) {
                carSuspicious.setSectionCode("");
            }
        }
        if (CommonUtil.isNotBlank(carSuspicious.getCode())){
            carSuspicious.setTrackNames(carSuspicious.getCode());
        }
    """
    section_code = delete_end(query.section_code)
    if is_not_blank(section_code):
        if Constants.section_all in section_code:
            query.section_code = ""
    if is_not_blank(query.code):
        query.track_names = query.code


def _localize_for_export(
    item: CarSuspicious,
    plate_color_map: Dict[str, str],
    car_type_map: Dict[str, str],
    car_vehicle_map: Dict[str, str],
    escaped_type_map: Dict[str, str],
    is_except_map: Dict[str, str],
    check_status_map: Dict[str, str],
) -> None:
    """``list.stream().forEach(...)`` 的那一大段 —— 字典回填 + 拼时间/地址字符串."""
    if item.create_time is not None:
        item.create_time_str = parse_date_to_str(
            YYYY_MM_DD_HH_MM_SS, item.create_time
        )
    item.plate_color = is_null(plate_color_map.get(item.plate_color))
    item.car_type = is_null(car_type_map.get(item.car_type))
    item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))
    item.escaped_type = is_null(escaped_type_map.get(item.escaped_type))
    item.is_except = is_null(is_except_map.get(item.is_except))
    item.check_status = is_null(check_status_map.get(item.check_status))
    # Java: dp.setPassType(...) 那行是注释掉的

    tx_time = ""
    tx_address = ""
    mj_time = ""
    mj_address = ""

    if item.in_time is not None:
        tx_time += parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.in_time)
    if item.out_time is not None:
        tx_time += "至" + parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.out_time)

    if is_not_blank(item.in_station):
        tx_address += is_null(item.in_station)
    if is_not_blank(item.out_station):
        tx_address += "至" + is_null(item.out_station)

    if item.gantry_time is not None:
        mj_time += parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.gantry_time)
    if item.out_gantry_time is not None:
        mj_time += "至" + parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.out_gantry_time)

    if is_not_blank(item.gantryt_station):
        mj_address += is_null(item.gantryt_station)
    if is_not_blank(item.out_gantryt_station):
        mj_address += "至" + is_null(item.out_gantryt_station)

    item.tx_time = tx_time
    item.tx_address = tx_address
    item.mj_time = mj_time
    item.mj_address = mj_address


def _export_excel(rows: List[CarSuspicious]) -> Response:
    """``templates/export/carSuspicious.xlsx`` 模板导出（``export`` / ``exportHistory`` 共用）."""
    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出可疑车辆失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            "Content-Disposition": "attachment",
        },
    )


def _image_extension(file_type: Optional[str]) -> str:
    """``SysFile.type`` -> 图片后缀（``docx`` 的 ``media`` 文件名要用）."""
    extension = get_file_type("x." + is_null(file_type)) if is_not_blank(file_type) else ""
    return extension or "png"


__all__ = [
    "DICT_CAR_TYPE",
    "DICT_CAR_VEHICLE",
    "DICT_CHECK_STATUS",
    "DICT_ESCAPED_TYPE",
    "DICT_IS_EXCEPT",
    "DICT_PLATE_COLOR",
    "DICT_RUN_TYPE",
    "EMPTY_CAR_NO_PLACEHOLDER",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "IMAGE_SIZE",
    "OCTET_STREAM_CONTENT_TYPE",
    "PARAM_ERROR_MESSAGE",
    "SIGNATURE_ERROR_MESSAGE",
    "SYNC_ADD_FLAG",
    "WORD_EXPORT_TEMPLATE",
    "add",
    "check",
    "edit",
    "export",
    "export_abnormal_passage",
    "export_history",
    "get_history_info",
    "get_info",
    "list_all_car_suspicious",
    "list_car_suspicious",
    "list_car_suspicious_by_car_no",
    "list_file_car_no",
    "list_history",
    "remove",
    "reset_car_suspicious_controller",
    "router",
    "sync_suspicious_car_task",
]
