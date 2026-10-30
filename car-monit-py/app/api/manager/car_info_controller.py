"""车辆信息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java

**8** 个映射
------------
========================  ============================  ==============================
Java                      Method / Path                 权限点
========================  ============================  ==============================
``list``                  GET ``/list``                 ``manager:carinfo:list``
``listAll``               GET ``/listAll``              **无**（弹窗选择用）
``export``                GET ``/export``               ``manager:carinfo:export``
``getInfo``               GET ``/{id}``                 **无**
``add``                   POST ``""``                   **无**（``@PostMapping`` 上没有 ``@PreAuthorize``）
``edit``                  PUT ``""``                    ``manager:carinfo:edit``
``remove``                DELETE ``/{ids}``             ``manager:carinfo:remove``
``doImport``              POST ``/import``              **无**
========================  ============================  ==============================

``add`` 没有权限点是一个既成事实（历史遗留），照抄 —— 不要"顺手补上"。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile
from starlette.responses import Response

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.common_util import delete_end, is_not_blank, is_null
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.import_util import (
    ImportEntity,
    ImportErrorEntity,
    ImportSysUtil,
    import_excel,
)
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.common.utils.string_utils import split_regex
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_info import CarInfo
from app.manager.service.car_info_service import CarInfoService, get_car_info_service
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_info_controller")

router = APIRouter(prefix="/manager/carinfo", tags=["manager-car-info"])

#: Java: ``com.ruoyi.web.controller.manager.CarInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarInfoController"

#: Java: ``String url = "templates/export/carInfo.xlsx";``
EXPORT_TEMPLATE = "templates/export/carInfo.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: 导出用字典类型
DICT_PLATE_COLOR = "plate_color"
DICT_CAR_TYPE = "car_type"
DICT_CAR_VEHICLE = "car_vehicle"
DICT_ESCAPED_TYPE = "escaped_type"
DICT_CAR_RUN_STATUS = "car_run_status"

#: 导入错误上限 —— Java: ``if (errorList.size() > 100) break;``
MAX_ERROR_ROWS = 100

_SERVICE: Optional[CarInfoService] = None


def _service() -> CarInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_info_service()
    return _SERVICE


def reset_car_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarInfo:
    """Java: 形参 ``CarInfo carInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarInfo, request.query_params)


CarInfoParam = Annotated[CarInfo, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:carinfo:list")
def list_car_infos(query: CarInfoParam) -> TableDataInfo:
    """查询车辆信息列表：菜单. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 跨租户可见。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/listAll", response_model=None)
def list_all_car_infos(query: CarInfoParam) -> TableDataInfo:
    """查询车辆信息列表：弹出窗口选择. Java: ``@GetMapping("/listAll")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:carinfo:export")
@log(title="车辆信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarInfoParam) -> Response:
    """导出车辆信息列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarInfo] = _service().select_list(query)
    dict_service = get_dict_data_service()

    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_PLATE_COLOR)
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)
    status_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_RUN_STATUS)

    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(
                YYYY_MM_DD_HH_MM_SS, item.create_time
            )
        item.plate_color = is_null(plate_color_map.get(item.plate_color))
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))
        item.status = is_null(status_map.get(item.status))

        # 需要循环：逃费类型（多值）—— 结果写回 escapedType，未命中字典的值被丢掉
        buss_name = ""
        buss_type = delete_end(item.escaped_type)
        if is_not_blank(buss_type):
            for buss_type_str in split_regex(buss_type, ","):
                if buss_type_str in escaped_type_map:
                    buss_name = buss_name + escaped_type_map[buss_type_str] + ","
        item.escaped_type = delete_end(buss_name)

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出车辆信息失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取车辆信息详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@log(title="车辆信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarInfo) -> AjaxResult:
    """新增车辆信息. Java: ``@PostMapping`` —— 注意这里**没有** ``@PreAuthorize``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:carinfo:edit")
@log(title="车辆信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarInfo) -> AjaxResult:
    """修改车辆信息. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:carinfo:remove")
@log(title="车辆信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除车辆信息. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


@router.post("/import", response_model=None)
@log(title="车辆信息", business_type=BusinessType.IMPORT, java_method="doImport")
def do_import(file: UploadFile = File(...)) -> AjaxResult:
    """导入车辆信息. Java: ``@PostMapping("/import")``.

    逐行照抄的四个细节：

    1. 扩展名只认 ``.xlsx``（``fileName.lastIndexOf(".xlsx") == -1``）；
    2. 字典校验用的是 ``selectDictDataLaleMap``（**标签 -> 值**），
       即表里填中文、库里存数字；
    3. ``errorList`` 超过 100 条就 ``break``（外层、内层各有一处）；
    4. 导入前按车牌号回查已有记录，命中就把 ``id`` 填进去 —— 于是 ``doImport``
       走的是更新而不是插入，但 ``createTime`` 会被重写（见 ``CarInfoService.do_import``）。
    """
    file_name = file.filename or ""
    if ".xlsx" not in file_name:
        return AjaxResult.error_message("请上传Excel文件(.xlsx)")

    import_util = ImportSysUtil()
    # Java: importUtil.getXSSFSheet(file.getInputStream(), 0)
    sheet = import_util.get_xssf_sheet(file.file, 0)
    gz_list: List[ImportEntity] = init_list()

    # 获取头部
    cols_name = [item.col_name for item in gz_list]
    # 校验头部
    if not import_util.col_vda_excel07(sheet, cols_name):
        return AjaxResult.error_message("导入失败,模板不正确,请下载对应的模板！")
    # 校验数据
    sheet_list = import_util.data_rtn_excel07(sheet, cols_name)
    if len(sheet_list) == 0:
        return AjaxResult.error_message("导入失败,模板excel没有数据可以导入，请确定！")

    # 校验数据格式
    error_list: List[ImportErrorEntity] = []
    import_list: List[CarInfo] = []
    for index, strs in enumerate(sheet_list):
        rtn_obj = import_excel(error_list, gz_list, index, strs, CarInfo)
        if len(error_list) == 0 and rtn_obj is not None:
            import_list.append(rtn_obj)
        if len(error_list) > MAX_ERROR_ROWS:
            break

    # 校验数据
    if len(error_list) == 0:
        dict_service = get_dict_data_service()
        plate_color_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_PLATE_COLOR
        )
        car_type_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_CAR_TYPE
        )
        car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_CAR_VEHICLE
        )
        escaped_type_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_ESCAPED_TYPE
        )

        for index, add_bo in enumerate(import_list):
            # 车牌颜色
            plate_color = is_null(add_bo.plate_color)
            if is_not_blank(plate_color):
                if plate_color in plate_color_map:
                    add_bo.plate_color = is_null(plate_color_map[plate_color])
                else:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1,
                            "车牌颜色",
                            plate_color + " 车牌颜色不存在,请在字典菜单维护！",
                        )
                    )

            # 车型
            car_type = is_null(add_bo.car_type)
            if is_not_blank(car_type):
                if car_type in car_type_map:
                    add_bo.car_type = is_null(car_type_map[car_type])
                else:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1,
                            "车型",
                            car_type + " 车型不存在,请在字典菜单维护！",
                        )
                    )

            # 车种
            car_vehicle = is_null(add_bo.car_vehicle)
            if is_not_blank(car_vehicle):
                if car_vehicle in car_vehicle_map:
                    add_bo.car_vehicle = is_null(car_vehicle_map[car_vehicle])
                else:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1,
                            "车种",
                            car_vehicle + " 车种不存在,请在字典菜单维护！",
                        )
                    )

            # 逃费类型（先削尾逗号，再把全角逗号换成半角）
            escaped_type = delete_end(add_bo.escaped_type)
            escaped_type = escaped_type.replace("，", ",")
            escaped_type_value = ""
            if escaped_type != "":
                for buss_type_str in split_regex(escaped_type, ","):
                    if buss_type_str in escaped_type_map:
                        escaped_type_value = (
                            escaped_type_value + is_null(escaped_type_map[buss_type_str]) + ","
                        )
                    else:
                        error_list.append(
                            import_util.get_error_bo(
                                index + 1,
                                "逃费类型",
                                buss_type_str + " 逃费类型不存在,请在字典菜单维护！",
                            )
                        )
            add_bo.escaped_type = delete_end(escaped_type_value)

            if len(error_list) > MAX_ERROR_ROWS:
                break

    # 插入数据库
    if len(error_list) == 0:
        for add_bo in import_list:
            add_bo.car_no = is_null(add_bo.car_no)  # 去掉空格
            # 根据车牌号
            query_bo = CarInfo()
            query_bo.car_no = is_null(add_bo.car_no)
            query_list = _service().select_list(query_bo)
            if len(query_list) > 0:
                add_bo.id = query_list[0].id
        _service().do_import(import_list)

    # 错误提示
    if len(error_list) > 0:
        return AjaxResult.error_data("error", [item.to_dict() for item in error_list])

    return AjaxResult.success_message_data("数据导入成功", import_list)


def init_list() -> List[ImportEntity]:
    """初始化导入头部、属性、校验规则.

    Java: ``public List<ImportEntity> initList()`` ——
    校验规则 1 必填 / 2 小数 / 3 整数 / 4 日期 / 5 身份证 / 6 年月。
    """
    bo_list: List[ImportEntity] = []
    bo_list.append(ImportEntity("车牌颜色", "plateColor", "1"))
    bo_list.append(ImportEntity("车牌号", "carNo", "1"))
    bo_list.append(ImportEntity("车型", "carType", "1"))
    bo_list.append(ImportEntity("车种", "carVehicle", ""))
    bo_list.append(ImportEntity("轴数", "carNum", "3"))
    bo_list.append(ImportEntity("逃费类型", "escapedType", "1"))
    bo_list.append(ImportEntity("逃费金额（元）", "escapedAmount", "2"))
    bo_list.append(ImportEntity("备注", "remark", ""))
    return bo_list


__all__ = [
    "router",
    "DICT_CAR_RUN_STATUS",
    "DICT_CAR_TYPE",
    "DICT_CAR_VEHICLE",
    "DICT_ESCAPED_TYPE",
    "DICT_PLATE_COLOR",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "MAX_ERROR_ROWS",
    "OCTET_STREAM_CONTENT_TYPE",
    "add",
    "do_import",
    "edit",
    "export",
    "get_info",
    "init_list",
    "list_all_car_infos",
    "list_car_infos",
    "remove",
    "reset_car_info_controller",
]
