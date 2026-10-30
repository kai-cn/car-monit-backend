"""车辆信息（几何对象）控制器 —— 桩号批量转经纬度 + 生成器模板 CRUD.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java

**9** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``getHenDa``              GET ``/getHenDa``           ``base:geometry:list``
``syncAllGeometry``       GET ``/syncAllGeometry``    **无**（登录即可）
``syncAllGeometry1``      GET ``/syncAllGeometry1``   **无**
``list``                  GET ``/list``               ``base:geometry:list``
``export``                GET ``/export``             ``base:geometry:export``
``getInfo``               GET ``/{ID}``               **无**
``add``                   POST ``""``                 ``base:geometry:add``
``edit``                  PUT ``""``                  ``base:geometry:edit``
``remove``                DELETE ``/{IDs}``           ``base:geometry:remove``
========================  ==========================  ==============================

注意表名/文案：Java 注释里通篇写的是"车辆信息"，但实体是 ``Geometry``（路线几何点），
``ExcelUtil`` 的表单名也是 ``"车辆信息数据"`` —— 照抄，不改。

``syncAllGeometry`` / ``syncAllGeometry1`` 是 **fire-and-forget**
--------------------------------------------------------------
``syncGeometry(list)`` 里对每条几何数据 ``executor.execute(...)``（Spring 的
``threadPoolTaskExecutor``，核心 50 / 最大 200 / 队列 1000），**提交完立刻返回**：

* 接口响应 ``{"code":200,"msg":"操作成功"}`` 时，真正的补齐线程可能还没开始跑；
* 任务里的任何异常都不会回传（在线程池的未捕获异常处理器里打印堆栈），
  所以 ``/syncAllGeometry`` **永远不会**因为恒达接口超时而返回 500。
* 幂等性由人工保证，Java 原注释：

  .. code-block:: text

      第一次请求先清空 geometry 表数据，后续重复请求不需要清空
      跑到一半 hengda 接口批量超时，重启项目重新请求继续跑
      G4521 一条数据都查不到，沿用老数据
      同一个路线编号、方向、起点桩号不要重复请求，否则会插入一模一样的数据

  代码里**没有**清表、没有去重 —— 照抄。

``syncGeometry`` 的"泵"（逐段补齐 10 个桩号）
---------------------------------------------
对每条几何数据：

1. ``qdzh``（起点桩号）、``count = 10``、``i = 0``、``doubleList = []``；
2. ``while count >= 7``：``i < 10`` 时查 ``"{qdzh}.{i}"``，``i == 10`` 时查
   ``"{qdzh+1}"``（整桩号）；
3. 恒达返回非空就收集 ``[longitude, latitude]``；
4. ``i == 10`` 时结算：``count = len(doubleList)``，**凑够 5 个才入库**
   （``path = Arrays.deepToString``），随后 ``doubleList = []``、``qdzh += 1``、``i = 0``；
   否则 ``i += 1``；
5. ``count < 7`` —— 这一段的经纬度太稀疏，整条路线停止。

即"10 个桩号里至少 7 个能查到经纬度，才继续跑下一段"。

照抄的两颗地雷
--------------
* ``qdzh`` 为 ``null`` 时，第一次拼桩号是 ``"null.0"``（Java 字符串拼接不 NPE，
  所以不会立刻报错），但跑到 ``i == 10`` 的 ``String.valueOf(qdzh + 1)`` 会
  **拆箱 NPE** —— 整个任务失败（只是被线程池吞掉，接口仍返回成功）。
  ``new Geometry(..., qdzh, qdzh + 1, ...)`` 也是同一个拆箱点。
* ``getDoubleValue`` 对非数字串抛 ``NumberFormatException``；对缺失键返回 ``0.0``
  （fastjson2 的行为），所以恒达少返回一个字段不会报错，只会插进一个 ``0.0``。
"""

from __future__ import annotations

import logging
import math
from typing import Annotated, Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.geometry import Geometry
from app.base.service.geometry_service import GeometryService, get_geometry_service
from app.base.service.hen_da_service import HenDaService, get_hen_da_service
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.config.thread_pool_config import (
    ThreadPoolTaskExecutor,
    get_thread_pool_task_executor,
)
from app.framework.web.service.permission_service import pre_authorize_permi

logger = logging.getLogger("app.api.base.geometry_controller")

router = APIRouter(prefix="/base/geometry", tags=["base-geometry"])

#: Java: ``com.ruoyi.web.controller.base.GeometryController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.GeometryController"

#: Java: ``util.exportExcel(list, "车辆信息数据")``
EXPORT_SHEET_NAME = "车辆信息数据"

#: Java: ``int count = 10;`` —— 每段先试探 10 个桩号
POSE_COUNT = 10
#: Java: ``while (count >= 7)`` —— 10 个桩号里至少 7 个有经纬度才继续下一段
MIN_POSE_COUNT = 7
#: Java: ``if (doubleList.size() >= 5)`` —— 至少 5 个点才入库
MIN_SAVE_COUNT = 5

_NULL_POINTER = "java.lang.NullPointerException"

_COLLABORATORS: Optional[Dict[str, Any]] = None


def _collaborators() -> Dict[str, Any]:
    """Java 的三个注入项：``IGeometryService`` / ``IHenDaService`` / ``ThreadPoolTaskExecutor``."""
    global _COLLABORATORS
    if _COLLABORATORS is None:
        _COLLABORATORS = {
            "geometry_service": get_geometry_service(),
            "hen_da_service": get_hen_da_service(),
            "executor": get_thread_pool_task_executor(),
        }
    return _COLLABORATORS


def reset_geometry_controller(
    geometry_service: Optional[GeometryService] = None,
    hen_da_service: Optional[HenDaService] = None,
    executor: Optional[ThreadPoolTaskExecutor] = None,
) -> None:
    """Test helper: drop / inject the cached collaborators.

    单测里建议注入一个**同步执行**的假 executor（:class:`_InlineExecutor`），
    否则 ``/syncAllGeometry`` 的断言只能验证"接口已返回"。
    """
    global _COLLABORATORS
    if geometry_service is None and hen_da_service is None and executor is None:
        _COLLABORATORS = None
        return
    current = dict(_collaborators())
    if geometry_service is not None:
        current["geometry_service"] = geometry_service
    if hen_da_service is not None:
        current["hen_da_service"] = hen_da_service
    if executor is not None:
        current["executor"] = executor
    _COLLABORATORS = current


class _InlineExecutor:
    """Test double：``execute`` 里**同步**跑任务，让异步流程可断言。

    只用于 pytest，不参与运行时装配（Java 侧没有对应物）。
    """

    def execute(self, task) -> None:  # noqa: ANN001 —— 形参名照抄 Java 的 Runnable
        task()

    def shutdown(self) -> None:  # pragma: no cover - 对齐 ThreadPoolTaskExecutor 的接口
        return None


def _query(request: Request) -> Geometry:
    """Java: 形参 ``Geometry geometry``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(Geometry, request.query_params)


GeometryParam = Annotated[Geometry, Depends(_query)]


def _java_string(value: Optional[str]) -> str:
    """Java 字符串拼接时 ``null`` 渲染成字面量 ``"null"``."""
    return "null" if value is None else value


def _get_double_value(json_object: Any, key: str) -> float:
    """Java: ``JSONObject#getDoubleValue(String)``.

    * 键不存在 / 值为 ``null`` -> ``0.0``（fastjson2 不抛异常）；
    * 值是非数字串 -> ``NumberFormatException``。
    """
    value = json_object.get(key) if isinstance(json_object, dict) else None
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"java.lang.NumberFormatException: {value!r}") from exc


def _decimal_to_scientific(text: str) -> str:
    """把定点十进制串（``repr`` 的另一种写法）转成 Java 的 ``1.0E7`` 形式."""
    sign = ""
    if text.startswith("-"):
        sign, text = "-", text[1:]
    int_part, _, frac_part = text.partition(".")
    stripped_int = int_part.lstrip("0")
    if stripped_int:
        exponent = len(stripped_int) - 1
        digits = (stripped_int + frac_part).rstrip("0")
    else:
        # ``0.0001`` 这类：数前导零定出指数
        exponent = -(len(frac_part) - len(frac_part.lstrip("0")) + 1)
        digits = frac_part.lstrip("0").rstrip("0")
    return f"{sign}{digits[0]}.{digits[1:] or '0'}E{exponent}"


def _java_double_to_string(value: float) -> str:
    """Java: ``Double#toString(double)``.

    两种实现都输出"能唯一还原该 double 的最短十进制串"，所以 ``[1e-3, 1e7)``
    区间内与 Python 的 ``repr`` 逐字符一致（比如 ``116.12345678901234``）。
    区间外的切换阈值不同（Java 1e-3/1e7，Python 1e-4/1e16），这里按 Java 的
    阈值把 ``repr`` 改写成 ``E`` 形式；经纬度恒落在十进制区间，该分支实际不可达。
    """
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    magnitude = abs(value)
    if magnitude == 0.0 or 1e-3 <= magnitude < 1e7:
        return repr(value)
    text = repr(value)
    if "e" not in text:
        return _decimal_to_scientific(text)
    mantissa, _, exponent = text.partition("e")
    if "." not in mantissa:
        mantissa += ".0"
    return f"{mantissa}E{int(exponent)}"


def _deep_to_string(rows: List[List[float]]) -> str:
    """Java: ``Arrays.deepToString(double[][])`` -> ``[[116.1, 39.1], [116.2, 39.2]]``."""
    return "[" + ", ".join("[" + ", ".join(_java_double_to_string(v) for v in row) + "]" for row in rows) + "]"


def _sync_one(geometry: Geometry) -> None:
    """``syncGeometry`` 里那个 ``Runnable`` 的任务体（单条几何数据）."""
    collaborators = _collaborators()
    hen_da_service: HenDaService = collaborators["hen_da_service"]
    geometry_service: GeometryService = collaborators["geometry_service"]

    # Java: Integer qdzh = geometry.getQdzh();
    qdzh: Optional[int] = geometry.qdzh
    double_list: List[List[float]] = []
    count = POSE_COUNT
    i = 0

    # Java: // 10个桩号有7个以上经纬度就继续跑下一截
    while count >= MIN_POSE_COUNT:
        zh: str
        if i < POSE_COUNT:
            # Java: zh = qdzh + "." + i;  —— qdzh 为 null 时是 "null.0"（不 NPE）
            zh = f"{_java_string(None if qdzh is None else str(qdzh))}.{i}"
        else:
            # Java: zh = String.valueOf(qdzh + 1);  —— 拆箱，qdzh 为 null 时 NPE
            if qdzh is None:
                raise TypeError(_NULL_POINTER)
            zh = str(qdzh + 1)

        json_object = hen_da_service.get_pile_to_lon_lat(geometry.lxbh, zh, geometry.lxfx)
        if json_object is not None:
            double_list.append(
                [
                    _get_double_value(json_object, "longitude"),
                    _get_double_value(json_object, "latitude"),
                ]
            )

        if i == POSE_COUNT:
            count = len(double_list)
            # Java: // 10个桩号有5个以上经纬度才入库
            if len(double_list) >= MIN_SAVE_COUNT:
                if qdzh is None:
                    # Java: new Geometry(..., qdzh, qdzh + 1, ...) 的拆箱 NPE
                    raise TypeError(_NULL_POINTER)
                entity = Geometry(
                    lxbh=geometry.lxbh,
                    lxfx=geometry.lxfx,
                    qdzh=qdzh,
                    zdzh=qdzh + 1,
                    paths=_deep_to_string(double_list),
                )
                geometry_service.save(entity)
            double_list = []
            # Java: qdzh ++;  —— 同样是拆箱；上一行的 zh 计算已保证 qdzh 非 null
            qdzh = qdzh + 1
            i = 0
        else:
            i += 1


def sync_geometry(geometries: Iterable[Geometry]) -> None:
    """Java: ``public void syncGeometry(List<Geometry> list)`` —— 逐条丢进线程池.

    ``lambda`` 用默认参数绑定当轮的 ``geometry``，避免 Python 的闭包晚绑定
    （Java 的增强 for 循环里每个迭代变量的捕获语义等价于此）。
    """
    executor = _collaborators()["executor"]
    for geometry in geometries:
        executor.execute(lambda geometry=geometry: _sync_one(geometry))


@router.get("/getHenDa", response_model=None)
@pre_authorize_permi("base:geometry:list")
def get_hen_da(query: GeometryParam) -> AjaxResult:
    """henDa 查询路线经纬度. Java: ``@GetMapping("/getHenDa")``.

    直接把恒达返回的 ``{"longitude": "...", "latitude": "..."}`` 塞进 ``data``；
    查不到时是 ``data = null`` —— 而 ``AjaxResult`` 会省略 ``data`` 键。
    """
    result = _collaborators()["hen_da_service"].get_pile_to_lon_lat(
        query.lxbh, query.zh_str, query.lxfx
    )
    return AjaxResult.success_data(result)


@router.get("/syncAllGeometry", response_model=None)
def sync_all_geometry() -> AjaxResult:
    """同步所有路线经纬度. Java: ``@GetMapping("/syncAllGeometry")``.

    没有任何权限注解、也没有 ``@Log``（Java 原样如此）；接口在任务**提交后**
    立即返回成功。
    """
    geometries = _collaborators()["geometry_service"].sync_all_geometry()
    sync_geometry(geometries)
    return AjaxResult.success()


@router.get("/syncAllGeometry1", response_model=None)
def sync_all_geometry_1(query: GeometryParam) -> AjaxResult:
    """手动补齐路线经纬度. Java: ``@GetMapping("/syncAllGeometry1")``.

    只处理请求参数里的那**一条**几何数据（从传入的 ``qdzh`` 向上补）。
    """
    sync_geometry([query])
    return AjaxResult.success()


@router.get("/list", response_model=None)
@pre_authorize_permi("base:geometry:list")
def list_geometries(query: GeometryParam) -> TableDataInfo:
    """查询车辆信息列表. Java: ``@GetMapping("/list")``."""
    start_page()
    # Java: // geometry.setTenantId(SecurityUtils.getTenantId()); —— 注释掉的租户过滤
    return get_data_table(_collaborators()["geometry_service"].select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:geometry:export")
@log(title="车辆信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: GeometryParam) -> AjaxResult:
    """导出车辆信息列表. Java: ``@GetMapping("/export")``.

    走 ``ExcelUtil``（不是 easypoi 模板）：文件名放在 ``msg`` 里，
    客户端再走 ``GET /common/download?fileName=...`` 取内容。
    """
    rows = _collaborators()["geometry_service"].select_list(query)
    return ExcelUtil(Geometry).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{ID}", response_model=None)
def get_info(ID: int) -> AjaxResult:  # noqa: N803 —— 形参名照抄 Java 的 ``Integer ID``
    """获取车辆信息详细信息. Java: ``@GetMapping(value = "/{ID}")``."""
    return AjaxResult.success_data(_collaborators()["geometry_service"].select_by_id(ID))


@router.post("", response_model=None)
@pre_authorize_permi("base:geometry:add")
@log(title="车辆信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: Geometry) -> AjaxResult:
    """新增车辆信息. Java: ``@PostMapping`` —— 主键由调用方给（``IdType.INPUT``）."""
    return _collaborators()["geometry_service"].save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:geometry:edit")
@log(title="车辆信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: Geometry) -> AjaxResult:
    """修改车辆信息. Java: ``@PutMapping``."""
    return _collaborators()["geometry_service"].save(entity)


@router.delete("/{IDs}", response_model=None)
@pre_authorize_permi("base:geometry:remove")
@log(title="车辆信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(IDs: str) -> AjaxResult:  # noqa: N803 —— 形参名照抄 Java 的 ``Integer[] IDs``
    """删除车辆信息. Java: ``@DeleteMapping("/{IDs}")`` —— ``Integer[]``（逗号分隔）."""
    return _collaborators()["geometry_service"].delete_by_ids(parse_id_array(IDs))


__all__ = [
    "EXPORT_SHEET_NAME",
    "GeometryParam",
    "MIN_POSE_COUNT",
    "MIN_SAVE_COUNT",
    "POSE_COUNT",
    "add",
    "edit",
    "export",
    "get_hen_da",
    "get_info",
    "list_geometries",
    "remove",
    "reset_geometry_controller",
    "router",
    "sync_all_geometry",
    "sync_all_geometry_1",
    "sync_geometry",
]
