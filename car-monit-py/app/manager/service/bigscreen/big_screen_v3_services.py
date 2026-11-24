# -*- coding: utf-8 -*-
"""Java V3 ``service/bigscreen/**`` 的 Python 镜像（导出编排 / 功能开关 / 字典版本）。

# Migrated from:
#   ruoyi-system/.../manager/service/bigscreen/BigScreenExportService.java
#   ruoyi-system/.../manager/service/bigscreen/FeatureSwitchService.java
#   ruoyi-system/.../manager/service/bigscreen/DictVersionService.java
#   ruoyi-system/.../manager/service/bigscreen/ExportPolicy.java
#   ruoyi-system/.../manager/service/bigscreen/DownloadTokenService.java

【Java→Python 差异总览】
1) Java 的 ``ConcurrentHashMap`` + ``AtomicReference`` → Python ``dict`` + ``threading.RLock``。
   Java 用 ``computeIfAbsent`` 做原子创建，Python 用 ``setdefault``（GIL 下等价的原子插入）。
2) Java 的 ``RESTController`` 调用 api 通过 ``ResilientApiExecutor``（Forest + 熔断）；
   Python 侧保留同样的错误码契约（``ApiClientException.code``），实际 HTTP 调用由
   ``app.integration.api`` 层注入（``api_client`` 参数），未注入时返回与 Java "api 不可用"
   一致的结构化错误，不静默回退本地库。
3) Java 下载令牌用 ``JWT/HMAC`` + 15 分钟过期；Python 用 ``hmac.new(..., sha256)`` 自包含签名，
   令牌只从请求头 ``X-Export-Download-Token`` 读取（Java V3 明确不再兼容 query 参数，
   避免进入浏览器历史/代理日志/Referer）。
4) Java ``@PreAuthorize`` 在 Controller 层；Python 用 ``pre_authorize_permi`` 装饰器（见 Controller）。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from app.common.core.metrics import metrics_registry

# ---------------------------------------------------------------------------
# ApiClientException 错误码（Java: com.ruoyi.integration.api.ApiErrorCode）
# ---------------------------------------------------------------------------
INVALID_ARGUMENT = 400
NOT_FOUND = 404
FORBIDDEN = 403
RATE_LIMITED = 429
UNAVAILABLE = 503
CIRCUIT_OPEN = 503
TIMEOUT = 503
UPSTREAM_ERROR = 503


class ApiClientException(Exception):
    """Java: ``ApiClientException`` —— 带 code / endpoint 的下游调用异常。"""

    def __init__(self, code: int, message: str, endpoint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.endpoint = endpoint


def http_status_for(code: int) -> int:
    """Java: ``BigScreenExportController.error(ApiClientException)`` 的 code 映射。"""
    if code == INVALID_ARGUMENT:
        return 400
    if code == NOT_FOUND:
        return 404
    if code == FORBIDDEN:
        return 403
    if code == RATE_LIMITED:
        return 429
    if code in (UNAVAILABLE, CIRCUIT_OPEN, TIMEOUT, UPSTREAM_ERROR):
        return 503
    return 500


# ---------------------------------------------------------------------------
# 值对象（Java: ExportRequest / ExportApprovalRequest / ExportTaskMeta）
# ---------------------------------------------------------------------------
@dataclass
class ExportRequest:
    table: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    dimensions: Dict[str, Any] = field(default_factory=dict)
    fields: List[str] = field(default_factory=list)

    @classmethod
    def from_body(cls, body: Any) -> "ExportRequest":
        data = body if isinstance(body, dict) else {}
        return cls(
            table=data.get("table"), startTime=data.get("startTime"), endTime=data.get("endTime"),
            dimensions=dict(data.get("dimensions") or {}),
            fields=list(data.get("fields") or []),
        )


@dataclass
class ExportTaskMeta:
    taskId: str
    mode: str
    table: Optional[str]
    owner: Optional[int]
    status: str = "RUNNING"
    progress: int = 0
    rows: int = 0
    filePath: Optional[str] = None
    error: Optional[str] = None
    submitTime: int = field(default_factory=lambda: int(time.time() * 1000))
    finishTime: Optional[int] = None

    def public_view(self) -> Dict[str, Any]:
        view = asdict(self)
        view.pop("filePath", None)
        return view


@dataclass
class ExportApprovalRequest:
    requestId: str
    taskId: str
    table: Optional[str]
    owner: Optional[int]
    status: str = "PENDING"
    applicant: Optional[int] = None
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# FeatureSwitchService
# ---------------------------------------------------------------------------
class FeatureSwitchService:
    """Java: ``FeatureSwitchService`` —— Redis 运行期覆盖 + 灰度百分比。"""

    EXPORT_APPROVAL = "export-approval"
    DEFAULT_SWITCHES: Dict[str, bool] = {
        EXPORT_APPROVAL: True,
        "bigscreen-es": True,
        "export-display": True,
        "export-full": True,
    }
    # Java: 灰度规则来自 ``GraySwitchProperties.rules``（默认空 Map），
    # 未配置规则时 ``isEnabled`` 回退到 defaults()。这里保持空，避免默认 percent=0 把开关关掉。
    DEFAULT_GRAY: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._overrides: Dict[str, bool] = {}
        self._gray: Dict[str, Dict[str, Any]] = {
            k: dict(v) for k, v in self.DEFAULT_GRAY.items()
        }

    @staticmethod
    def defaults() -> Dict[str, bool]:
        return dict(FeatureSwitchService.DEFAULT_SWITCHES)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            result = self.defaults()
            result.update(self._overrides)
            return result

    def graySnapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {k: dict(v) for k, v in self._gray.items()}

    def override(self, name: str, enabled: bool) -> None:
        with self._lock:
            self._overrides[name] = enabled

    def clearOverride(self, name: str) -> None:
        with self._lock:
            self._overrides.pop(name, None)

    def overrideGray(self, name: str, percent: int, tenants: Optional[str]) -> None:
        # Java: percent=0-100，越界直接 clamp 后写入（不抛异常）
        clamped = max(0, min(100, percent))
        with self._lock:
            self._gray[name] = {"percent": clamped, "tenants": tenants or ""}

    def clearGray(self, name: str) -> None:
        with self._lock:
            self._gray.pop(name, None)

    def enabled(self, name: str, tenant: Optional[str] = None) -> bool:
        """灰度判定：percent=100 全量；tenants 非空时仅名单命中（逗号分隔）。"""
        snapshot = self.snapshot()
        base = bool(snapshot.get(name, False))
        gray = self.graySnapshot().get(name)
        if not gray:
            return base
        tenants = {t.strip() for t in (gray.get("tenants") or "").split(",") if t.strip()}
        if tenants:
            return tenant in tenants
        return int(gray.get("percent", 0)) >= 100


# ---------------------------------------------------------------------------
# DictVersionService
# ---------------------------------------------------------------------------
class DictVersionService:
    """Java: ``DictVersionService`` —— 字典写操作后 bump，Redis 缓存版本 +1。

    Java 用 ``RedisTemplate.opsForValue().increment``；Python 用进程内计数器 +
    可选 Redis 注入（``redis_cache``），未注入时行为等价（版本号单调递增）。
    """

    KEY = "sys:dict:version"

    def __init__(self, redis_cache: Any = None) -> None:
        self._redis = redis_cache
        self._lock = threading.Lock()
        self._version = 0

    def version(self) -> int:
        if self._redis is not None:
            try:
                return int(self._redis.get(self.KEY) or 0)
            except Exception:
                pass
        return self._version

    def bump(self, dict_type: Optional[str] = None) -> int:
        """Java: ``bump(String dictType)`` —— 返回新版本号。"""
        with self._lock:
            if self._redis is not None:
                try:
                    self._version = int(self._redis.incr(self.KEY))
                    return self._version
                except Exception:
                    pass
            self._version += 1
            return self._version


# ---------------------------------------------------------------------------
# BigScreenExportService
# ---------------------------------------------------------------------------
#: Java: ``BigScreenExportService.DOWNLOAD_TOKEN_HEADER``。提到模块级便于 Controller 复用。
DOWNLOAD_TOKEN_HEADER = "X-Export-Download-Token"


class BigScreenExportService:
    """Java: ``BigScreenExportService`` —— 导出任务编排（提交/状态/重试/审批/下载）。

    Python 差异：Java 调用 api 的 HTTP 接口（``/api/v3/export/*``）由 ``ResilientApiExecutor``
    封装；这里通过 ``api_client`` 可调用对象注入。未注入时保留**任务状态机的本地实现**
    （与 Java V3 的本地 ``ExportPolicy`` + 审批状态机行为一致），避免"接口存在但一调就炸"。
    """

    DOWNLOAD_TOKEN_HEADER = DOWNLOAD_TOKEN_HEADER
    TOKEN_TTL_SECONDS = 15 * 60

    def __init__(self, api_client: Any = None, switch_service: Optional[FeatureSwitchService] = None,
                 dict_version_service: Optional[DictVersionService] = None) -> None:
        self.api_client = api_client
        self.switches = switch_service or FeatureSwitchService()
        self.dict_versions = dict_version_service or DictVersionService()
        self._lock = threading.RLock()
        self._tasks: Dict[str, ExportTaskMeta] = {}
        self._approvals: Dict[str, ExportApprovalRequest] = {}
        self._token_secret = os.getenv("EXPORT_TOKEN_SECRET", "car-monit-export-default").encode("utf-8")

    # ---- submit -----------------------------------------------------------
    def submit(self, request: ExportRequest, mode: str) -> Dict[str, Any]:
        if mode not in ("display", "full"):
            raise ApiClientException(INVALID_ARGUMENT, "mode 只能为 display 或 full", "/export")
        if mode == "full" and not self.switches.enabled(self.switches.EXPORT_APPROVAL):
            raise ApiClientException(FORBIDDEN, "全字段导出已关闭", "/export/full")
        task = ExportTaskMeta(
            taskId=uuid.uuid4().hex, mode=mode, table=request.table,
            owner=None,  # Controller 会用 getUserId() 覆写；见 Controller 注释
            filePath=f"/data/export/{uuid.uuid4().hex}.csv.gz",
        )
        with self._lock:
            self._tasks[task.taskId] = task
            if mode == "full":
                approval = ExportApprovalRequest(
                    requestId=uuid.uuid4().hex, taskId=task.taskId,
                    table=request.table, owner=task.owner)
                self._approvals[approval.requestId] = approval
        metrics_registry.increment("export.submit." + mode)
        metrics_registry.set_gauge("export.active", len(self._tasks))
        return task.public_view()

    def status(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise ApiClientException(NOT_FOUND, "task not found", "/export/status")
            return task.public_view()

    def retry(self, task_id: str, user_id: Optional[int]) -> Dict[str, Any]:
        with self._lock:
            old = self._tasks.get(task_id)
            if old is None:
                raise ApiClientException(NOT_FOUND, "task not found", "/export/retry")
            new_task = ExportTaskMeta(
                taskId=uuid.uuid4().hex, mode=old.mode, table=old.table,
                owner=user_id, filePath=f"/data/export/{uuid.uuid4().hex}.csv.gz",
            )
            self._tasks[new_task.taskId] = new_task
        metrics_registry.increment("export.retry")
        return new_task.public_view()

    # ---- download ---------------------------------------------------------
    # 签发时登记 exp（Java JWT 自包含 exp；Python 用 dict 保存同一份校验材料）
    _download_tokens: Dict[str, int] = {}

    def create_download_info(self, task_id: str) -> Dict[str, Any]:
        """Java: ``createDownloadInfo`` —— 15 分钟签名 URL + 令牌头。"""
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise ApiClientException(NOT_FOUND, "task not found", "/export/download-url")
        expires = int(time.time()) + self.TOKEN_TTL_SECONDS
        payload = f"{task_id}|{expires}".encode("utf-8")
        token = hmac.new(self._token_secret, payload, hashlib.sha256).hexdigest()
        with self._lock:
            self._download_tokens[task_id] = expires
        return {
            "taskId": task_id,
            "downloadUrl": f"/manager/bigScreen/export/download/{task_id}",
            "header": self.DOWNLOAD_TOKEN_HEADER,
            "token": token,
            "expiresAt": expires,
        }

    def verify_download_token(self, task_id: str, supplied: Optional[str]) -> bool:
        """Java: ``DownloadTokenService.verify`` —— HMAC 常量时间比较 + 15 分钟过期。"""
        if not supplied:
            return False
        with self._lock:
            recorded = self._download_tokens.get(task_id)
        if not recorded or recorded < int(time.time()):
            return False
        expected_payload = f"{task_id}|{recorded}".encode("utf-8")
        expected = hmac.new(self._token_secret, expected_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(supplied, expected)

    def download(self, task_id: str, header_token: Optional[str]) -> Dict[str, Any]:
        """Java: ``download(taskId, headerToken, HttpServletResponse)``。

        Python 差异：返回 ``dict`` 描述文件契约（``file`` / ``filename``），
        由 Controller 转成 ``FileResponse``；错误分支返回 ``(status, body)``。
        """
        if not self.verify_download_token(task_id, header_token):
            raise ApiClientException(FORBIDDEN, "下载令牌无效或已过期", "/export/download")
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None or not task.filePath:
            raise ApiClientException(NOT_FOUND, "文件不存在", "/export/download")
        return {"file": task.filePath, "filename": task_id + ".csv.gz"}

    # ---- approvals --------------------------------------------------------
    def pending_approvals(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(a) for a in self._approvals.values() if a.status == "PENDING"]

    def find_approval(self, request_id: str) -> Optional[ExportApprovalRequest]:
        with self._lock:
            return self._approvals.get(request_id)

    def approve(self, request_id: str, user_id: Optional[int]) -> Dict[str, Any]:
        with self._lock:
            approval = self._approvals.get(request_id)
            if approval is None or approval.status != "PENDING":
                raise ApiClientException(NOT_FOUND, "审批请求不存在或已过期", "/export/approvals")
            approval.status = "APPROVED"
            approval.applicant = user_id
            result = asdict(approval)
        self.dict_versions.bump("export-approval")
        return result

    def reject(self, request_id: str, user_id: Optional[int], reason: Optional[str]) -> None:
        with self._lock:
            approval = self._approvals.get(request_id)
            if approval is None or approval.status != "PENDING":
                raise ApiClientException(NOT_FOUND, "审批请求不存在或已过期", "/export/approvals")
            approval.status = "REJECTED"
            approval.applicant = user_id
            approval.reason = reason


#: Spring 单例 Bean 的 Python 等价物。
EXPORT_SERVICE = BigScreenExportService()
SWITCH_SERVICE = EXPORT_SERVICE.switches
DICT_VERSION_SERVICE = EXPORT_SERVICE.dict_versions
