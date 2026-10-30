"""服务区基础信息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztFwqjcxxController.java

6 个映射，全部迁移
------------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``export``                GET ``/export``             ``base:fwqjcxx:export``
``getInfo``               GET ``/{agentPk}``          **无**
``add``                   POST ``""``                 ``base:fwqjcxx:add``
``edit``                  PUT ``""``                  ``base:fwqjcxx:edit``
``remove``                DELETE ``/{agentPks}``      ``base:fwqjcxx:remove``
========================  ==========================  ==============================

三个与 Java 一致的坑
--------------------
1. ``/{agentPk}`` 是 **String** 路径变量，会吃掉所有单段 GET 路径，所以
   ``/list`` / ``/export`` 必须**先注册**（Spring 靠字面量优先，FastAPI 靠顺序）。
2. ``export`` 返回的是**文件名**（在 ``msg`` 里），文件落到
   ``{ruoyi.profile}/download/``，前端再 ``GET /common/download`` 取。
3. ``add`` / ``edit`` 调的是**同一个** Service 方法：``agentPk`` 非空即更新。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.dwd_lczt_fwqjcxx import DwdLcztFwqjcxx
from app.base.service.dwd_lczt_fwqjcxx_service import (
    DwdLcztFwqjcxxService,
    get_dwd_lczt_fwqjcxx_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/base/fwqjcxx", tags=["base-fwqjcxx"])

#: Java: ``com.ruoyi.web.controller.base.DwdLcztFwqjcxxController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.DwdLcztFwqjcxxController"

#: Java: ``util.exportExcel(list, "服务区基础信息数据")`` —— sheet 名与文件名前缀。
EXPORT_SHEET_NAME = "服务区基础信息数据"

_SERVICE: Optional[DwdLcztFwqjcxxService] = None


def _service() -> DwdLcztFwqjcxxService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_dwd_lczt_fwqjcxx_service()
    return _SERVICE


def reset_fwqjcxx_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> DwdLcztFwqjcxx:
    """Java: 形参 ``DwdLcztFwqjcxx x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(DwdLcztFwqjcxx, request.query_params)


#: 查询条件实体。
FwqjcxxParam = Annotated[DwdLcztFwqjcxx, Depends(_query)]


@router.get("/list", response_model=None)
def list_fwqjcxx(query: FwqjcxxParam) -> TableDataInfo:
    """查询服务区基础信息列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:fwqjcxx:export")
@log(title="服务区基础信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: FwqjcxxParam) -> AjaxResult:
    """导出服务区基础信息列表. Java: ``@GetMapping("/export")``.

    **不受分页影响**（Java 没有 ``startPage()``），返回体只有 ``code`` / ``msg``。
    """
    rows = _service().select_list(query)
    return ExcelUtil(DwdLcztFwqjcxx).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{agent_pk}", response_model=None)
def get_info(agent_pk: str) -> AjaxResult:
    """获取服务区基础信息详细信息. Java: ``@GetMapping(value = "/{agentPk}")``."""
    return AjaxResult.success_data(_service().select_by_id(agent_pk))


@router.post("", response_model=None)
@pre_authorize_permi("base:fwqjcxx:add")
@log(title="服务区基础信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: DwdLcztFwqjcxx) -> AjaxResult:
    """新增服务区基础信息. Java: ``@PostMapping public AjaxResult add(@RequestBody ...)``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:fwqjcxx:edit")
@log(title="服务区基础信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: DwdLcztFwqjcxx) -> AjaxResult:
    """修改服务区基础信息. Java: ``@PutMapping public AjaxResult edit(@RequestBody ...)``."""
    return _service().save(entity)


@router.delete("/{agent_pks}", response_model=None)
@pre_authorize_permi("base:fwqjcxx:remove")
@log(title="服务区基础信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(agent_pks: str) -> AjaxResult:
    """删除服务区基础信息. Java: ``@DeleteMapping("/{agentPks}")``（``String[]`` 路径变量）."""
    return _service().delete_by_ids(parse_str_array(agent_pks))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "FwqjcxxParam",
    "list_fwqjcxx",
    "export",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_fwqjcxx_controller",
]
