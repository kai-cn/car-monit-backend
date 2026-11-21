"""大屏导出编排接口（Java V3 新增）.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java

端点清单（10 个映射，全部挂在 ``/manager/bigScreen/export``）
------------------------------------------------------------
    ==================================  ======  =====================  ===================================
    Java                                Method  Path                   权限
    ==================================  ======  =====================  ===================================
    ``display``                         POST    ``/display``            manager:bigscreen:export
    ``full``                            POST    ``/full``               export + exportFull
    ``status``                          GET     ``/status/{taskId}``    登录
    ``retry``                           POST    ``/{taskId}/retry``     export
    ``resume``                          POST    ``/{taskId}/resume``     export
    ``downloadUrl``                     POST    ``/{taskId}/download-url`` 登录
    ``download``                        GET     ``/download/{taskId}``  登录 + 令牌头
    ``approvals``                       GET     ``/approvals``           exportApprove
    ``approve``                         POST    ``/approvals/{requestId}/approve``  exportApprove
    ``reject``                          POST    ``/approvals/{requestId}/reject``   exportApprove
    ==================================  ======  =====================  ===================================

【Java→Python 差异】
1) Java ``@RequestBody ExportRequest`` → Python ``body: Dict[str, Any] = Body(default={})``；
   Jackson 的未知字段忽略策略由 ``ExportRequest.from_body`` 显式实现。
2) Java ``@RequestHeader(name=..., required=false)`` → Python ``Header(default=None, alias=...)``。
   **V3 明确不再兼容 query 参数令牌**（会进浏览器历史/代理日志/Referer）。
3) Java ``void download(..., HttpServletResponse)`` 直接写流 → Python 返回
   ``FileResponse``；错误分支返回 ``JSONResponse(status_code=403/404)``，与 Java 的
   ``response.setStatus(...)`` + ``AjaxResult.error`` 一致。
4) Java ``catch (ApiClientException e) { return error(e); }`` → Python 的
   ``_error_response`` helper；错误码映射表在 ``http_status_for``（400/403/404/429/503/500）。
5) ``getUserId()`` 来自 ``BaseController`` → Python ``get_user_id()`` utility。
6) ``AccessDeniedException`` 在 Java 由 Spring Security 转 403；Python 由
   ``pre_authorize_permi`` 装饰器统一处理，Controller 内不再手写 try/catch。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from app.common.core.controller.base_controller import get_user_id
from app.common.core.domain.ajax_result import AjaxResult
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.service.bigscreen.big_screen_v3_services import (
    DOWNLOAD_TOKEN_HEADER,
    EXPORT_SERVICE,
    ApiClientException,
    ExportRequest,
    http_status_for,
)

__all__ = ["router"]

log = logging.getLogger(__name__)

router = APIRouter(prefix="/manager/bigScreen/export", tags=["manager-big-screen-export"])


def _error_response(endpoint: str, exc: ApiClientException) -> JSONResponse:
    """Java: ``private AjaxResult error(ApiClientException e)``。"""
    log.warning("[导出] endpoint=%s code=%s msg=%s", endpoint, exc.code, exc.message)
    status = http_status_for(exc.code)
    return JSONResponse(status_code=status, content=AjaxResult.error_code(status, exc.message))


@router.post("/display", response_model=None)
@pre_authorize_permi("manager:bigscreen:export")
def display(body: Dict[str, Any] = Body(default_factory=dict)) -> Any:
    """提交展示字段快速导出（ES PIT）。Java: ``@PostMapping("/display")``."""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.submit(ExportRequest.from_body(body), "display"))
    except ApiClientException as e:
        return _error_response("/display", e)


@router.post("/full", response_model=None)
@pre_authorize_permi("manager:bigscreen:export")
@pre_authorize_permi("manager:bigscreen:exportFull")
def full(body: Dict[str, Any] = Body(default_factory=dict)) -> Any:
    """提交全字段海量导出（GaussDB 游标）。Java: 双 ``@PreAuthorize``。"""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.submit(ExportRequest.from_body(body), "full"))
    except ApiClientException as e:
        return _error_response("/full", e)


@router.get("/status/{task_id}", response_model=None)
def status(task_id: str) -> Any:
    """查询导出任务状态。Java: ``@GetMapping("/status/{taskId}")``."""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.status(task_id))
    except ApiClientException as e:
        return _error_response("/status", e)


@router.post("/{task_id}/retry", response_model=None)
@pre_authorize_permi("manager:bigscreen:export")
def retry(task_id: str) -> Any:
    """失败任务重试。Java: ``retry(@PathVariable String taskId, getUserId())``."""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.retry(task_id, get_user_id()))
    except ApiClientException as e:
        return _error_response("/retry", e)


@router.post("/{task_id}/resume", response_model=None)
@pre_authorize_permi("manager:bigscreen:export")
def resume(task_id: str) -> Any:
    """伪续传：Java 明确标注 api 不支持字节级续传，按原参数重新提交并附加两个字段。"""
    try:
        result = EXPORT_SERVICE.retry(task_id, get_user_id())
        result["resume"] = True
        result["message"] = "api 不支持字节级续传，已按原参数重新提交任务"
        return AjaxResult.success_data(result)
    except ApiClientException as e:
        return _error_response("/resume", e)


@router.post("/{task_id}/download-url", response_model=None)
def download_url(task_id: str) -> Any:
    """生成 15 分钟下载签名信息。Java: ``@PostMapping("/{taskId}/download-url")``."""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.create_download_info(task_id))
    except ApiClientException as e:
        return _error_response("/download-url", e)


@router.get("/download/{task_id}", response_model=None)
def download(task_id: str, request: Request,
             x_export_download_token: Optional[str] = Header(default=None, alias=DOWNLOAD_TOKEN_HEADER)) -> Response:
    """流式下载；令牌**只走请求头**。Java: ``@GetMapping("/download/{taskId}")``."""
    try:
        info = EXPORT_SERVICE.download(task_id, x_export_download_token)
        return FileResponse(
            path=info["file"], filename=info["filename"], media_type="application/gzip")
    except ApiClientException as e:
        # Java: response.setStatus(FORBIDDEN ? 403 : 404) + AjaxResult.error(msg)
        status = 403 if e.code == 403 else 404
        return JSONResponse(status_code=status, content=AjaxResult.error_message(e.message))


@router.get("/approvals", response_model=None)
@pre_authorize_permi("manager:bigscreen:exportApprove")
def approvals() -> Any:
    """查询待审批导出列表。Java: ``@GetMapping("/approvals")``."""
    try:
        return AjaxResult.success_data(EXPORT_SERVICE.pending_approvals())
    except ApiClientException as e:
        return _error_response("/approvals", e)


@router.post("/approvals/{request_id}/approve", response_model=None)
@pre_authorize_permi("manager:bigscreen:exportApprove")
def approve(request_id: str) -> Any:
    """审批通过。Java: ``findApproval` 不存在时 ``AjaxResult.error(404, ...)``。"""
    try:
        if EXPORT_SERVICE.find_approval(request_id) is None:
            return AjaxResult.error_code(404, "审批请求不存在或已过期")
        return AjaxResult.success_data(EXPORT_SERVICE.approve(request_id, get_user_id()))
    except ApiClientException as e:
        return _error_response("/approvals/approve", e)


@router.post("/approvals/{request_id}/reject", response_model=None)
@pre_authorize_permi("manager:bigscreen:exportApprove")
def reject(request_id: str, reason: Optional[str] = None) -> Any:
    """驳回。Java: ``@RequestParam(name="reason", required=false) String reason``."""
    try:
        EXPORT_SERVICE.reject(request_id, get_user_id(), reason)
        return AjaxResult.success()
    except ApiClientException as e:
        return _error_response("/approvals/reject", e)
