# -*- coding: utf-8 -*-
"""Java V3 对齐回归测试（backend 侧，16 个新增端点 + 核心契约）。

运行::

    .venv\\Scripts\\python.exe -m pytest tests/test_v3_alignment.py -q

【Java→Python 差异】Java 侧对应 JUnit ``bigscreen/ExportPolicyTest`` /
``ExportApprovalStateMachineTest``；Python 侧用 pytest 驱动 Service + TestClient，
避免启动 MySQL/Redis/Kafka 等中间件。
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_NEW_ROUTES = {
    ("POST", "/manager/bigScreen/export/display"),
    ("POST", "/manager/bigScreen/export/full"),
    ("GET", "/manager/bigScreen/export/status/{task_id}"),
    ("POST", "/manager/bigScreen/export/{task_id}/retry"),
    ("POST", "/manager/bigScreen/export/{task_id}/resume"),
    ("POST", "/manager/bigScreen/export/{task_id}/download-url"),
    ("GET", "/manager/bigScreen/export/download/{task_id}"),
    ("GET", "/manager/bigScreen/export/approvals"),
    ("POST", "/manager/bigScreen/export/approvals/{request_id}/approve"),
    ("POST", "/manager/bigScreen/export/approvals/{request_id}/reject"),
    ("GET", "/monitor/bigscreen/metrics"),
    ("GET", "/monitor/bigscreen/switches"),
    ("POST", "/monitor/bigscreen/gray/{name}"),
    ("DELETE", "/monitor/bigscreen/gray/{name}"),
    ("POST", "/monitor/bigscreen/switches/{name}"),
    ("DELETE", "/monitor/bigscreen/switches/{name}"),
}


def _strong_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """settings 有密钥强度门禁；测试用高熵占位值（monkeypatch 保证不污染其它测试）。"""
    monkeypatch.setenv("TOKEN__SECRET", "Kx9pLm2Qv8Rt5Yw7Nc4Jb6Hs3Fa1Zd0E!@#$%^&*()")
    monkeypatch.setenv("SPRING__DATASOURCE__DRUID__MASTER__PASSWORD", "DbPwd9!xQ2vLm7#kR4t")
    monkeypatch.setenv("HENGDA__SECRET", "Hd8sK2mQ5vR7yT1wP9zB3nL6xC4aF0j~`!@#$%^&*()-_=+")


def test_v3_routes_registered(monkeypatch: pytest.MonkeyPatch):
    """16 个 Java V3 新端点全部注册；路径变量使用 Python 的 ``{task_id}`` 命名。"""
    _strong_env(monkeypatch)
    from app.main import create_app

    app = create_app()
    actual = {(next(iter(r.methods)) if getattr(r, "methods", None) else "", r.path)
              for r in app.routes if getattr(r, "methods", None)}
    # FastAPI 的 APIRoute.methods 是 set（GET 路由同时含 HEAD），统一取第一个并规范化
    normalized = {(m if m not in ("HEAD",) else "GET", p) for m, p in actual}
    missing = {("POST" if m == "POST" else m, p.replace("{taskId}", "{task_id}").replace("{requestId}", "{request_id}"))
               for m, p in EXPECTED_NEW_ROUTES} - normalized
    assert not missing, f"缺失 V3 端点: {sorted(missing)}"


def test_export_service_submit_status_retry():
    from app.manager.service.bigscreen.big_screen_v3_services import (
        ExportRequest,
        BigScreenExportService,
    )

    service = BigScreenExportService()
    task = service.submit(ExportRequest.from_body({"table": "snapshot"}), "display")
    assert "filePath" not in task, "filePath 是服务端绝对路径，不得暴露"
    assert task["mode"] == "display"

    assert service.status(task["taskId"])["taskId"] == task["taskId"]
    with pytest.raises(Exception):
        service.status("not-exist")

    retried = service.retry(task["taskId"], 42)
    assert retried["taskId"] != task["taskId"]
    assert retried["owner"] == 42


def test_download_token_header_only():
    from app.manager.service.bigscreen.big_screen_v3_services import (
        DOWNLOAD_TOKEN_HEADER,
        ExportRequest,
        BigScreenExportService,
    )

    assert DOWNLOAD_TOKEN_HEADER == "X-Export-Download-Token"
    service = BigScreenExportService()
    task = service.submit(ExportRequest.from_body({"table": "fee"}), "display")
    info = service.create_download_info(task["taskId"])
    assert info["header"] == DOWNLOAD_TOKEN_HEADER
    assert service.verify_download_token(task["taskId"], info["token"]) is True
    assert service.verify_download_token(task["taskId"], "wrong") is False
    with pytest.raises(Exception):
        service.download(task["taskId"], None)


def test_approval_state_machine():
    from app.manager.service.bigscreen.big_screen_v3_services import (
        ExportRequest,
        BigScreenExportService,
    )

    service = BigScreenExportService()
    task = service.submit(ExportRequest.from_body({"table": "fee"}), "full")
    approvals = service.pending_approvals()
    assert len(approvals) == 1
    request_id = approvals[0]["requestId"]
    assert service.find_approval(request_id) is not None
    approved = service.approve(request_id, 7)
    assert approved["status"] == "APPROVED"
    assert service.pending_approvals() == []


def test_feature_switch_security_guard():
    from app.manager.service.bigscreen.big_screen_v3_services import (
        FeatureSwitchService,
    )

    switches = FeatureSwitchService()
    assert switches.snapshot()[FeatureSwitchService.EXPORT_APPROVAL] is True
    switches.override(FeatureSwitchService.EXPORT_APPROVAL, False)
    assert switches.enabled(FeatureSwitchService.EXPORT_APPROVAL) is False
    switches.clearOverride(FeatureSwitchService.EXPORT_APPROVAL)
    assert switches.enabled(FeatureSwitchService.EXPORT_APPROVAL) is True

    switches.overrideGray(FeatureSwitchService.EXPORT_APPROVAL, 150, "tenant-a")
    gray = switches.graySnapshot()[FeatureSwitchService.EXPORT_APPROVAL]
    assert gray["percent"] == 100, "Java V3 clamp percent 到 0-100"
    assert gray["tenants"] == "tenant-a"


def test_metrics_ratio_rounding():
    from app.common.core.metrics import metrics_registry

    metrics_registry.reset()
    metrics_registry.increment("api.request")
    metrics_registry.increment("api.timeout")
    metrics_registry.set_gauge("export.active", 3)
    assert metrics_registry.counter("api.timeout") == 1
    assert list(metrics_registry.counters()) == ["api.request", "api.timeout"]
    assert metrics_registry.gauge("export.active") == 3
    metrics_registry.reset()
