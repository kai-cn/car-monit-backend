"""异常车辆流水 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java

**13** 个映射
------------
============================  ================================  ==========
Java                          Method / Path                     权限点
============================  ================================  ==========
``list``                      GET ``/list``                     **无**
``listCarNo``                 GET ``/listCarNo``                **无**
``listCarOrgId``              GET ``/listCarOrgId``             **无**
``exportOrgId``               GET ``/exportOrgId``              **无**
``listExceptId``              GET ``/listExceptId``             **无**
``exceptRecordCount``         GET ``/exceptRecordCount``        **无**
``export``                    GET ``/export``                   **无**
``getInfo``                   GET ``/{id}``                     **无**
``add``                       POST ``""``                       **无**
``edit``                      PUT ``""``                        **无**
``remove``                    DELETE ``/{ids}``                 **无**
``getConfirmId``              GET ``/getConfirmId/{id}``        **无**
``doImport``                  POST ``/import``                  **无**
============================  ================================  ==========

（这个控制器**整体没有** ``@PreAuthorize`` —— 与 ``CarSuspiciousController`` 不同，照抄。）

四处必须照抄的地方
------------------
1. ``listCarOrgId`` / ``exportOrgId`` 在 ``epsId == null`` 时**塞 -1**（查不到任何数据），
   而不是"不过滤"；
2. ``exportOrgId`` 与 ``export`` 的循环体**一字不差**，只有取数方法不同
   （``selectCarExceptRecordListNew`` vs ``selectCarExceptRecordList``）；循环里
   ``setCreateTimeStr`` 被**写了两遍**（Java 原文重复），效果一样但保留顺序；
   ``carType`` / ``carVehicle`` / ``escapedType`` 是**命中字典才替换**，
   ``status`` 是**无条件**用字典值覆盖（未命中 -> ``""``）；
3. ``getConfirmId`` 先 ``AjaxResult.success()`` 再 ``put("data", ...)`` ——
   所以响应里**一定有** ``data`` 键（值可能是 ``"-1"``）；
4. ``doImport`` 的 ``gzListThree`` 是**再一次** ``initListTwo()`` 的结果（Java 的 bug：
   本该调 ``initListThree()``，而 ``initListThree`` 是死代码）。照抄，别修。

路由声明顺序与 Java **不同**：``GET /{id}`` 必须排在所有静态 ``GET`` 之后，
否则 ``/manager/exceptrecord/listCarNo`` 会被 ``/{id}`` 抢占（FastAPI 按声明顺序匹配，
Spring 是精确路径优先）。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Request, UploadFile
from starlette.responses import Response

from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.service.ods_szdn_toll_service import get_ods_szdn_toll_service
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.common_util import is_blank, is_not_blank, is_null
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
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.car_info import CarInfo
from app.manager.service.car_except_record_service import (
    CarExceptRecordService,
    get_car_except_record_service,
)
from app.manager.service.car_info_service import get_car_info_service
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_except_record_controller")

router = APIRouter(prefix="/manager/exceptrecord", tags=["manager-car-except-record"])

#: Java: ``com.ruoyi.web.controller.manager.CarExceptRecordController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarExceptRecordController"

#: Java: ``String url = "templates/export/exportCarExcept.xlsx";``
EXPORT_TEMPLATE = "templates/export/exportCarExcept.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"
#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: ``listCarNo`` / ``exceptRecordCount`` 在车牌为空时替换成的魔数
EMPTY_CAR_NO_PLACEHOLDER = "-1"
#: ``listExceptId`` 在 ``exceptIds`` 为空时替换成的魔数
EMPTY_EXCEPT_IDS_PLACEHOLDER = "-1"
#: ``listCarOrgId`` / ``exportOrgId`` 在 ``epsId == null`` 时塞进去的值
MISSING_EPS_ID = -1

#: Java: ``private static final Integer[] strNum = {0,11,12,14,15,17,18,19,21}``
STR_NUM: Tuple[int, ...] = (0, 11, 12, 14, 15, 17, 18, 19, 21)

#: Java: ``private static final String[] strName = {"序号", ...}``
STR_NAME: Tuple[str, ...] = (
    "序号",
    "出口收费站",
    "出口时间",
    "通行PASSID",
    "车牌",
    "交易车型",
    "车种",
    "入口站",
    "入口时间",
    "一级类型",
    "二级类型",
    "省内",
    "省外",
    "小计",
    "省内",
    "省外",
    "小计",
    "省内",
    "省外",
    "小计",
    "备注",
    "",
)

#: Java: ``if (errorList.size() > 100) break;``
MAX_ERROR_ROWS = 100

TEMPLATE_INVALID_MESSAGE = "导入失败,模板不正确,请下载对应的模板！"
TEMPLATE_EMPTY_MESSAGE = "导入失败,模板excel没有数据可以导入，请确定！"
IMPORT_SUCCESS_MESSAGE = "数据导入成功"
IMPORT_FILE_TYPE_MESSAGE = "请上传Excel文件(.xlsx)"

DICT_CAR_TYPE = "car_type"
DICT_CAR_VEHICLE = "car_vehicle"
DICT_ESCAPED_TYPE = "escaped_type"
DICT_SUPPLEMENTARY_STATUS = "supplementary_status"
DICT_CAR_TYPE_CHANGE = "car_type_change"
DICT_PLATE_COLOR = "plate_color"

#: Java: 导入时 ``carTypeName`` -> ``carVehicle`` 的映射（``1-4``->1，``11-16``->2，
#: ``21-26``->3，其余一律 ``99``）。注意这里是 ``99``，不是可疑车辆那套空串。
_CAR_VEHICLE_MAP: Dict[str, str] = {
    "1": "1",
    "2": "1",
    "3": "1",
    "4": "1",
    "11": "2",
    "12": "2",
    "13": "2",
    "14": "2",
    "15": "2",
    "16": "2",
    "21": "3",
    "22": "3",
    "23": "3",
    "24": "3",
    "25": "3",
    "26": "3",
}

_SERVICE: Optional[CarExceptRecordService] = None


def _service() -> CarExceptRecordService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_except_record_service()
    return _SERVICE


def reset_car_except_record_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarExceptRecord:
    """Java: 形参 ``CarExceptRecord carExceptRecord``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarExceptRecord, request.query_params)


CarExceptRecordParam = Annotated[CarExceptRecord, Depends(_query)]


# --------------------------------------------------------------------------- 列表


@router.get("/list", response_model=None)
def list_car_except_records(query: CarExceptRecordParam) -> TableDataInfo:
    """查询异常车辆流水列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/listCarNo", response_model=None)
def list_car_except_records_by_car_no(query: CarExceptRecordParam) -> TableDataInfo:
    """根据车牌号查询. Java: ``@GetMapping("/listCarNo")``."""
    start_page()
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    return get_data_table(_service().select_list(query))


@router.get("/listCarOrgId", response_model=None)
def list_car_org_id(query: CarExceptRecordParam) -> TableDataInfo:
    """根据单位查询. Java: ``@GetMapping("/listCarOrgId")`` —— 走 ``...ListNew``."""
    start_page()
    if query.eps_id is None:
        query.eps_id = MISSING_EPS_ID
    return get_data_table(_service().select_list_new(query))


@router.get("/listExceptId", response_model=None)
def list_except_id(query: CarExceptRecordParam) -> TableDataInfo:
    """根据异常流水 id 集合查询. Java: ``@GetMapping("/listExceptId")``."""
    start_page()
    if is_blank(query.except_ids):
        query.except_ids = EMPTY_EXCEPT_IDS_PLACEHOLDER
    return get_data_table(_service().select_list(query))


@router.get("/exceptRecordCount", response_model=None)
def except_record_count(query: CarExceptRecordParam) -> AjaxResult:
    """根据车牌号查询统计. Java: ``@GetMapping(value = "/exceptRecordCount")``."""
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    return AjaxResult.success_data(_service().except_record_count(query))


# --------------------------------------------------------------------------- 导出


@router.get("/exportOrgId", response_model=None)
@log(title="异常车辆流水", business_type=BusinessType.EXPORT, java_method="exportOrgId")
def export_org_id(query: CarExceptRecordParam) -> Response:
    """根据单位导出. Java: ``@GetMapping("/exportOrgId")`` —— 写完响应后 ``return null``."""
    if query.eps_id is None:
        query.eps_id = MISSING_EPS_ID
    rows: List[CarExceptRecord] = _service().select_list_new(query)
    return _export_excel(rows)


@router.get("/export", response_model=None)
@log(title="异常车辆流水", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarExceptRecordParam) -> Response:
    """导出异常车辆流水列表. Java: ``@GetMapping("/export")``."""
    rows: List[CarExceptRecord] = _service().select_list(query)
    return _export_excel(rows)


# --------------------------------------------------------------------------- 详情 / 增删改


@router.get("/getConfirmId/{id}", response_model=None)
def get_confirm_id(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取 confirmId. Java: ``@GetMapping(value = "/getConfirmId/{id}")``.

    Java 先 ``AjaxResult.success()`` 再 ``put("data", ...)`` —— ``data`` 键一定存在。
    """
    result = AjaxResult.success()
    # Java: result.put("data", ...) —— 走 ``put_chain`` 才能按 HashMap 桶号落位
    result.put_chain(AjaxResult.DATA_TAG, _service().get_confirm_id(id))
    return result


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002
    """获取异常车辆流水详细信息. Java: ``@GetMapping(value = "/{id}")``.

    **必须**声明在所有静态 ``GET`` 路径之后（见模块 docstring）。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@log(title="异常车辆流水", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarExceptRecord) -> AjaxResult:
    """新增异常车辆流水. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@log(title="异常车辆流水", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarExceptRecord) -> AjaxResult:
    """修改异常车辆流水. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@log(title="异常车辆流水", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除异常车辆流水. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


# --------------------------------------------------------------------------- 导入


@router.post("/import", response_model=None)
@log(title="新增流水导入", business_type=BusinessType.IMPORT, java_method="doImport")
def do_import(file: UploadFile = File(...)) -> AjaxResult:
    """新增流水导入. Java: ``@PostMapping("/import")``.

    逐行照抄的五个细节：

    1. 扩展名只认 ``.xlsx``；表头允许在**第 1 行或第 2 行**（``colVdaExcel08(..., 1)``
       / ``colVdaExcel08(..., 2)``，两者都失败才报错）；
    2. 第二次表头校验复用 ``initListTwo()``（Java 的 bug，``initListThree()`` 是死代码）；
    3. ``dataRtnExcel08(sheet, strName, strNum, 3)`` 从**第 3 行**开始读，
       ``strNum`` 指定的 9 列**不取值**（保持空串）；
    4. 车牌形如 ``粤A12345_2`` 时下划线后面是**车牌颜色标签**，会被字典换成值；
       车牌不在重点车辆库里就**顺手新建**（``carMap`` + ``addCarMap`` 去重）；
    5. 校验规则里 ``1,8`` = 必填 + 时间，``1,2`` = 必填 + 小数。
    """
    file_name = file.filename or ""
    if ".xlsx" not in file_name:
        return AjaxResult.error_message(IMPORT_FILE_TYPE_MESSAGE)

    import_util = ImportSysUtil()
    sheet = import_util.get_xssf_sheet(file.file, 0)

    # 获取第二列头部
    gz_list: List[ImportEntity] = init_list_two()
    cols_name = [item.col_name for item in gz_list]

    # 获取第三列头部 —— Java 这里又调了一次 ``initListTwo()``（bug），照抄
    gz_list_three: List[ImportEntity] = init_list_two()
    cols_name_three = [item.col_name for item in gz_list_three]

    # 校验头部
    if not import_util.col_vda_excel08(sheet, cols_name, 1) and not import_util.col_vda_excel08(
        sheet, cols_name_three, 2
    ):
        return AjaxResult.error_message(TEMPLATE_INVALID_MESSAGE)

    # 校验数据
    sheet_list = import_util.data_rtn_excel08(sheet, STR_NAME, STR_NUM, 3)
    if len(sheet_list) == 0:
        return AjaxResult.error_message(TEMPLATE_EMPTY_MESSAGE)

    # 校验数据格式
    error_list: List[ImportErrorEntity] = []
    import_list: List[CarExceptRecord] = []
    for index, strs in enumerate(sheet_list):
        rtn_obj = import_excel(error_list, gz_list, index, strs, CarExceptRecord)
        if len(error_list) == 0 and rtn_obj is not None:
            import_list.append(rtn_obj)
        if len(error_list) > MAX_ERROR_ROWS:
            break

    # 新增车辆
    add_list: List[CarInfo] = []
    add_car_map: Dict[str, str] = {}

    if len(error_list) == 0:
        car_info_service = get_car_info_service()
        # 查询重点车辆
        car_list = car_info_service.select_list(CarInfo())
        car_map: Dict[str, CarInfo] = {}
        for car_rtn in car_list:
            car_map[is_null(car_rtn.car_no)] = car_rtn

        # 查询收费站
        toll_list = get_ods_szdn_toll_service().select_list_new(OdsSzdnToll())
        toll_map: Dict[str, str] = {}
        for toll_rtn in toll_list:
            toll_map[is_null(toll_rtn.toll_name)] = is_null(toll_rtn.toll_code)

        dict_service = get_dict_data_service()
        car_type_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_CAR_TYPE_CHANGE
        )
        # Java: car_vehicle 的标签字典那行是注释掉的
        escaped_type_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_ESCAPED_TYPE
        )
        plate_color_map: Dict[str, str] = dict_service.select_dict_data_lale_map(
            DICT_PLATE_COLOR
        )

        for index, add_bo in enumerate(import_list):
            # 车型
            car_type = is_null(add_bo.car_type)
            if is_not_blank(car_type):
                if car_type in car_type_map:
                    add_bo.car_type = is_null(car_type_map[car_type])

            car_type_name = is_null(add_bo.car_type)
            car_vehicle = _CAR_VEHICLE_MAP.get(car_type_name, "99")

            # 车种 —— Java: ``if (CommonUtil.isNotBlank(carVehicle))``（永远成立）
            if is_not_blank(car_vehicle):
                add_bo.car_vehicle = is_null(car_vehicle)

            # 车牌号、颜色处理
            car_no = is_null(add_bo.car_no)
            plate_color = ""
            if "_" in car_no:
                vehicle_plate_str = split_regex(car_no, "_")
                if len(vehicle_plate_str) > 1:
                    plate_color = vehicle_plate_str[1]
                car_no = vehicle_plate_str[0]
            add_bo.car_no = car_no

            # 车牌颜色
            if is_not_blank(plate_color):
                if plate_color in plate_color_map:
                    plate_color = is_null(plate_color_map[plate_color])

            if is_not_blank(car_no):
                if car_no in car_map:
                    car_info = car_map[car_no]
                    add_bo.car_id = car_info.id
                    add_bo.car_num = car_info.car_num
                else:
                    if car_no not in add_car_map:
                        add_car_info = CarInfo()
                        add_car_info.car_no = car_no
                        add_car_info.plate_color = plate_color
                        add_car_info.car_type = add_bo.car_type
                        add_car_info.car_vehicle = add_bo.car_vehicle
                        add_list.append(add_car_info)
                        add_car_map[car_no] = car_no

            # 逃费类型
            escaped_type = is_null(add_bo.escaped_type)
            if is_not_blank(escaped_type):
                if escaped_type in escaped_type_map:
                    add_bo.escaped_type = is_null(escaped_type_map[escaped_type])
                else:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1,
                            "逃费类型",
                            escaped_type + " 逃费类型不存在,请在字典菜单维护！",
                        )
                    )

            # 入口
            in_station = is_null(add_bo.in_station)
            if is_not_blank(in_station):
                if in_station in toll_map:
                    add_bo.in_station = is_null(in_station)
                    add_bo.in_station_id = is_null(toll_map[in_station])

            # 出口
            out_station = is_null(add_bo.out_station)
            if is_not_blank(out_station):
                if out_station in toll_map:
                    add_bo.out_station = is_null(out_station)
                    add_bo.out_station_id = is_null(toll_map[out_station])

            # 应缴金额 不能小于 收费金额
            if add_bo.total_amount is not None and add_bo.charge_amount is not None:
                if add_bo.total_amount < add_bo.charge_amount:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1, "缴费金额", "收费金额不能大于应缴金额"
                        )
                    )

            # 时间验证
            if add_bo.in_time is not None and add_bo.out_time is not None:
                if add_bo.in_time > add_bo.out_time:
                    error_list.append(
                        import_util.get_error_bo(
                            index + 1, "时间", "入口时间大于出口时间，请确认!"
                        )
                    )

            if len(error_list) > MAX_ERROR_ROWS:
                break

    # 插入数据库
    if len(error_list) == 0:
        car_info_service = get_car_info_service()
        # 新新增车辆
        for add_car in add_list:
            car_info_service.save_car_info(add_car)

        for add_bo in import_list:
            if add_bo.total_amount is not None and add_bo.charge_amount is not None:
                add_bo.dif_amount = add_bo.total_amount - add_bo.charge_amount
            # 根据车牌号和入口时间
            query_bo = CarExceptRecord()
            query_bo.car_no = is_null(add_bo.car_no)
            query_bo.in_time = add_bo.in_time
            query_list = _service().select_list(query_bo)
            if len(query_list) > 0:
                add_bo.id = query_list[0].id
            _service().save(add_bo)

    # 错误提示
    if len(error_list) > 0:
        return AjaxResult.error_data("error", [item.to_dict() for item in error_list])

    return AjaxResult.success_message_data(IMPORT_SUCCESS_MESSAGE, import_list)


def init_list_two() -> List[ImportEntity]:
    """初始化导入头部、属性、校验规则第二列. Java: ``public List<ImportEntity> initListTwo()``.

    校验规则 1 必填 / 2 小数 / 3 整数 / 4 日期 / 5 身份证 / 6 年月，多个逗号分隔。
    """
    bo_list: List[ImportEntity] = []
    bo_list.append(ImportEntity("序号", "", ""))
    bo_list.append(ImportEntity("出口收费站", "outStation", ""))
    bo_list.append(ImportEntity("出口时间", "outTime", "1,8"))
    bo_list.append(ImportEntity("通行PASSID", "passType", ""))
    bo_list.append(ImportEntity("车牌", "carNo", "1"))

    bo_list.append(ImportEntity("交易车型", "carType", ""))
    bo_list.append(ImportEntity("车种", "carVehicle", ""))

    bo_list.append(ImportEntity("入口站", "inStation", ""))
    bo_list.append(ImportEntity("入口时间", "inTime", "1,8"))
    bo_list.append(ImportEntity("漏交通行费类型", "backCol1", ""))
    bo_list.append(ImportEntity("", "escapedType", "1"))

    bo_list.append(ImportEntity("交易金额", "", ""))
    bo_list.append(ImportEntity("", "", ""))
    bo_list.append(ImportEntity("", "chargeAmount", "1,2"))

    bo_list.append(ImportEntity("应交金额", "", ""))
    bo_list.append(ImportEntity("", "", ""))
    bo_list.append(ImportEntity("", "totalAmount", "1,2"))

    bo_list.append(ImportEntity("实际追交金额", "", ""))
    bo_list.append(ImportEntity("", "", ""))
    bo_list.append(ImportEntity("", "", ""))

    bo_list.append(ImportEntity("备注", "remark", ""))
    return bo_list


def init_list_three() -> List[ImportEntity]:
    """初始化导入头部、属性、校验规则第三列.

    Java: ``public List<ImportEntity> initListThree()`` —— **死代码**（``doImport`` 里
    本该调用它的地方又调了一次 ``initListTwo()``）。为了可读性保留，但**不要**改进
    ``do_import`` 去用它。
    """
    bo_list: List[ImportEntity] = []
    bo_list.append(ImportEntity("", "", ""))
    bo_list.append(ImportEntity("", "outStation", ""))
    bo_list.append(ImportEntity("", "outTime", "1,8"))
    bo_list.append(ImportEntity("", "passType", ""))
    bo_list.append(ImportEntity("", "carNo", "1"))

    bo_list.append(ImportEntity("", "", ""))
    bo_list.append(ImportEntity("", "", ""))

    bo_list.append(ImportEntity("", "inStation", ""))
    bo_list.append(ImportEntity("", "inTime", "1,8"))
    bo_list.append(ImportEntity("一级类型", "backCol1", ""))
    bo_list.append(ImportEntity("二级类型", "escapedType", "1"))

    bo_list.append(ImportEntity("省内", "", ""))
    bo_list.append(ImportEntity("省外", "", ""))
    bo_list.append(ImportEntity("小计", "chargeAmount", "1,2"))

    bo_list.append(ImportEntity("省内", "", ""))
    bo_list.append(ImportEntity("省外", "", ""))
    bo_list.append(ImportEntity("小计", "totalAmount", "1,2"))

    bo_list.append(ImportEntity("省内", "", ""))
    bo_list.append(ImportEntity("省外", "", ""))
    bo_list.append(ImportEntity("小计", "", "1,2"))

    bo_list.append(ImportEntity("", "remark", ""))
    return bo_list


# --------------------------------------------------------------------------- 内部


def _export_excel(rows: List[CarExceptRecord]) -> Response:
    """``export`` / ``exportOrgId`` 共用的字典回填 + 模板导出."""
    dict_service = get_dict_data_service()
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)
    status_map: Dict[str, str] = dict_service.select_dict_data_map(
        DICT_SUPPLEMENTARY_STATUS
    )

    for index, item in enumerate(rows):
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(
                YYYY_MM_DD_HH_MM_SS, item.create_time
            )
        # Java 又把上面两行写了一遍 —— 幂等，这里保留注释说明
        # if item.create_time is not None: item.create_time_str = ...
        if item.in_time is not None:
            item.in_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.in_time)
        if item.out_time is not None:
            item.out_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.out_time)

        # 命中字典才替换（三个字段）
        if item.car_type in car_type_map:
            item.car_type = is_null(car_type_map.get(item.car_type))
        if item.car_vehicle in car_vehicle_map:
            item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))
        if item.escaped_type in escaped_type_map:
            item.escaped_type = is_null(escaped_type_map.get(item.escaped_type))
        # 状态是**无条件**覆盖
        item.status = is_null(status_map.get(item.status))
        item.sort = index + 1
        item.car_no_query = ""

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出异常车辆流水失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            "Content-Disposition": "attachment",
        },
    )


__all__ = [
    "DICT_CAR_TYPE",
    "DICT_CAR_TYPE_CHANGE",
    "DICT_CAR_VEHICLE",
    "DICT_ESCAPED_TYPE",
    "DICT_PLATE_COLOR",
    "DICT_SUPPLEMENTARY_STATUS",
    "EMPTY_CAR_NO_PLACEHOLDER",
    "EMPTY_EXCEPT_IDS_PLACEHOLDER",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "IMPORT_FILE_TYPE_MESSAGE",
    "IMPORT_SUCCESS_MESSAGE",
    "MAX_ERROR_ROWS",
    "MISSING_EPS_ID",
    "OCTET_STREAM_CONTENT_TYPE",
    "STR_NAME",
    "STR_NUM",
    "TEMPLATE_EMPTY_MESSAGE",
    "TEMPLATE_INVALID_MESSAGE",
    "add",
    "do_import",
    "edit",
    "except_record_count",
    "export",
    "export_org_id",
    "get_confirm_id",
    "get_info",
    "init_list_three",
    "init_list_two",
    "list_car_except_records",
    "list_car_except_records_by_car_no",
    "list_car_org_id",
    "list_except_id",
    "remove",
    "reset_car_except_record_controller",
    "router",
]
