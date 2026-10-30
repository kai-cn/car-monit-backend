"""flow 分组（审批流）的 HTTP 契约测试.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/flow/{FlowApplyInfo,FlowCurrentNode,FlowList,
#   FlowMessageDispose,FlowMessageInfo,FlowName,FlowTemplate}Controller.java

覆盖的重点（Mapper / Service 由各自文件覆盖）：

* 7 张路由表都完整（共 **55** 个映射），且每个路由里的 ``GET /{id}`` 都**排在所有
  静态 GET 之后** —— ``FlowMessageInfoController`` 在 Java 里把 ``exportShrz`` 写在
  ``getInfo`` 之后，靠 Spring "精确路径优先"才没被吞掉，FastAPI 必须手动调整；
* 权限点：``FlowNameController`` 逐个方法都挂 ``@PreAuthorize``（``/listQuery`` 例外），
  ``FlowApplyInfoController`` 只有 ``/listAll`` 挂，其余 5 个控制器**一个都没有**；
* ``/listnew`` 在审核历史末尾补的"待审批 / 流程结束"两条虚拟记录；
* ``/flowlist`` 头部那条不入库的"申请人提交"虚拟节点；
* ``/getInfoByBillId/{billOid}`` 查不到时回显查询对象（不是 ``null``）；
* ``exportShrz`` 的模板占位符与 ``sort`` 从 1 开始；渲染失败时回**空 body**。
"""

from __future__ import annotations

import importlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.domain.flow_current_node import FlowCurrentNode
from app.flow.domain.flow_list import FlowList
from app.flow.domain.flow_message_info import FlowMessageInfo
from app.flow.domain.flow_template import FlowTemplate

FLOW_PACKAGE = "app.api.flow"

#: ``模块名 -> {(path, (method, ...))}`` —— 逐条抄自 7 个 Java 控制器的映射表。
ROUTE_TABLES: Dict[str, Set[Tuple[str, Tuple[str, ...]]]] = {
    "flow_apply_info_controller": {
        ("/flow/applyinfo/list", ("GET",)),
        ("/flow/applyinfo/listAll", ("GET",)),
        ("/flow/applyinfo/export", ("GET",)),
        ("/flow/applyinfo/{id}", ("GET",)),
        ("/flow/applyinfo", ("POST",)),
        ("/flow/applyinfo", ("PUT",)),
        ("/flow/applyinfo/{ids}", ("DELETE",)),
    },
    "flow_current_node_controller": {
        ("/flow/currentnode/list", ("GET",)),
        ("/flow/currentnode/export", ("GET",)),
        ("/flow/currentnode/getInfoByBillId/{billOid}", ("GET",)),
        ("/flow/currentnode/{id}", ("GET",)),
        ("/flow/currentnode", ("POST",)),
        ("/flow/currentnode", ("PUT",)),
        ("/flow/currentnode/{ids}", ("DELETE",)),
        ("/flow/currentnode/saveFlowAuit", ("PUT",)),
        ("/flow/currentnode/submitReturn", ("POST",)),
        ("/flow/currentnode/submitEntrustFlow", ("POST",)),
    },
    "flow_list_controller": {
        ("/flow/flowlist/list", ("GET",)),
        ("/flow/flowlist/listnew", ("GET",)),
        ("/flow/flowlist/export", ("GET",)),
        ("/flow/flowlist/{id}", ("GET",)),
        ("/flow/flowlist", ("POST",)),
        ("/flow/flowlist", ("PUT",)),
        ("/flow/flowlist/{ids}", ("DELETE",)),
    },
    "flow_message_dispose_controller": {
        ("/flow/messagedispose/list", ("GET",)),
        ("/flow/messagedispose/export", ("GET",)),
        ("/flow/messagedispose/{id}", ("GET",)),
        ("/flow/messagedispose", ("POST",)),
        ("/flow/messagedispose", ("PUT",)),
        ("/flow/messagedispose/{ids}", ("DELETE",)),
        ("/flow/messagedispose/delmes/{mid}", ("DELETE",)),
        ("/flow/messagedispose/szzdmes/{mid}", ("DELETE",)),
    },
    # Java 的 POST/PUT 在块注释里 -> **不注册**（8 个映射，不是 10 个）
    "flow_message_info_controller": {
        ("/flow/messageinfo/list", ("GET",)),
        ("/flow/messageinfo/listyb", ("GET",)),
        ("/flow/messageinfo/listyj", ("GET",)),
        ("/flow/messageinfo/listxx", ("GET",)),
        ("/flow/messageinfo/export", ("GET",)),
        ("/flow/messageinfo/exportShrz", ("GET",)),
        ("/flow/messageinfo/{id}", ("GET",)),
        ("/flow/messageinfo/{ids}", ("DELETE",)),
    },
    "flow_name_controller": {
        ("/flow/flowname/list", ("GET",)),
        ("/flow/flowname/listQuery", ("GET",)),
        ("/flow/flowname/export", ("GET",)),
        ("/flow/flowname/{id}", ("GET",)),
        ("/flow/flowname", ("POST",)),
        ("/flow/flowname", ("PUT",)),
        ("/flow/flowname/{ids}", ("DELETE",)),
        ("/flow/flowname/tbFlow", ("POST",)),
    },
    "flow_template_controller": {
        ("/flow/flowtemplate/list", ("GET",)),
        ("/flow/flowtemplate/flowlist", ("GET",)),
        ("/flow/flowtemplate/export", ("GET",)),
        ("/flow/flowtemplate/{id}", ("GET",)),
        ("/flow/flowtemplate", ("POST",)),
        ("/flow/flowtemplate", ("PUT",)),
        ("/flow/flowtemplate/{ids}", ("DELETE",)),
    },
}


def _module(name: str) -> Any:
    return importlib.import_module(f"{FLOW_PACKAGE}.{name}")


def _build_app(
    router: Any,
    permissions: Optional[Set[str]] = None,
    tenant_id: int = 100,
) -> FastAPI:
    """带假 JWT 的应用：中间件直接把登录用户塞进 ``SecurityContextHolder``."""
    application = FastAPI()
    register_exception_handlers(application)

    @application.middleware("http")
    async def _fake_jwt(request: Any, call_next: Any) -> Any:
        SecurityContextHolder.get_context().set_authentication(
            UsernamePasswordAuthenticationToken(
                LoginUser(
                    user=SysUser(user_id=2, user_name="ry", tenant_id=tenant_id),
                    permissions={"*:*:*"} if permissions is None else permissions,
                ),
                None,
                [],
            )
        )
        return await call_next(request)

    application.include_router(router)
    return application


@pytest.fixture(autouse=True)
def _clean_context() -> Any:
    SecurityContextHolder.clear_context()
    clear_page()


class _FakeService:
    """7 个 flow service 的公共替身：只记录调用，返回可预期的空结果."""

    def __init__(self, rows: Optional[List[Any]] = None, by_id: Any = None) -> None:
        self.rows = rows if rows is not None else []
        self.by_id = by_id
        self.calls: List[Tuple[str, Any]] = []

    # ---- 通用 CRUD
    def select_flow_apply_info_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_apply_info_list", query))
        return list(self.rows)

    def select_flow_apply_info_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_apply_info_by_id", entity_id))
        return self.by_id

    def save_flow_apply_info(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_apply_info", entity))
        return AjaxResult.success()

    def delete_flow_apply_info_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_apply_info_by_ids", ids))
        return AjaxResult.success()

    def select_flow_current_node_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_current_node_list", query))
        return list(self.rows)

    def select_flow_current_node_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_current_node_by_id", entity_id))
        return self.by_id

    def save_flow_current_node(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_current_node", entity))
        return AjaxResult.success()

    def save_flow_auit(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_auit", entity))
        return AjaxResult.success()

    def submit_return(self, entity: Any) -> AjaxResult:
        self.calls.append(("submit_return", entity))
        return AjaxResult.success()

    def submit_entrust_flow(self, entity: Any) -> AjaxResult:
        self.calls.append(("submit_entrust_flow", entity))
        return AjaxResult.success()

    def delete_flow_current_node_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_current_node_by_ids", ids))
        return AjaxResult.success()

    def select_flow_list_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_list_list", query))
        return list(self.rows)

    def select_flow_list_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_list_by_id", entity_id))
        return self.by_id

    def save_flow_list(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_list", entity))
        return AjaxResult.success()

    def delete_flow_list_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_list_by_ids", ids))
        return AjaxResult.success()

    def select_flow_message_dispose_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_message_dispose_list", query))
        return list(self.rows)

    def select_flow_message_dispose_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_message_dispose_by_id", entity_id))
        return self.by_id

    def save_flow_message_dispose(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_message_dispose", entity))
        return AjaxResult.success()

    def delete_flow_message_dispose_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_message_dispose_by_ids", ids))
        return AjaxResult.success()

    def remove_flow_message(self, mid: Any, buss_id: Any) -> AjaxResult:
        self.calls.append(("remove_flow_message", (mid, buss_id)))
        return AjaxResult.success()

    def save_szzd_flow_message(self, mid: Any, buss_id: Any) -> AjaxResult:
        self.calls.append(("save_szzd_flow_message", (mid, buss_id)))
        return AjaxResult.success()

    def select_flow_message_info_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_message_info_list", query))
        return list(self.rows)

    def select_flow_message_info_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_message_info_by_id", entity_id))
        return self.by_id

    def delete_flow_message_info_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_message_info_by_ids", ids))
        return AjaxResult.success()

    def select_flow_name_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_name_list", query))
        return list(self.rows)

    def select_flow_name_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_name_by_id", entity_id))
        return self.by_id

    def save_flow_name(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_name", entity))
        return AjaxResult.success()

    def delete_flow_name_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_name_by_ids", ids))
        return AjaxResult.success()

    def tb_flow(self, entity: Any) -> AjaxResult:
        self.calls.append(("tb_flow", entity))
        return AjaxResult.success()

    def select_flow_template_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_flow_template_list", query))
        return list(self.rows)

    def select_flow_template_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_flow_template_by_id", entity_id))
        return self.by_id

    def save_flow_template(self, entity: Any) -> AjaxResult:
        self.calls.append(("save_flow_template", entity))
        return AjaxResult.success()

    def delete_flow_template_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_flow_template_by_ids", ids))
        return AjaxResult.success()


def _inject(monkeypatch: Any, module: Any, service: Any, name: str = "_SERVICE") -> None:
    """跳过单例，直接把替身挂到模块级缓存上."""

    def _fake() -> Any:
        return service

    getter = "_apply_service" if name == "_APPLY_SERVICE" else (
        "_flow_list_service" if name == "_FLOW_LIST_SERVICE" else "_service"
    )
    monkeypatch.setattr(module, name, service)
    monkeypatch.setattr(module, getter, _fake)


def _boom(*_args: Any, **_kwargs: Any) -> Any:
    raise RuntimeError("template exploded")


# --------------------------------------------------------------------------- 路由表


@pytest.mark.parametrize("module_name", sorted(ROUTE_TABLES))
def test_the_route_table_matches_the_java_mappings(module_name: str) -> None:
    router = _module(module_name).router

    registered = {(route.path, tuple(sorted(route.methods))) for route in router.routes}

    assert registered == ROUTE_TABLES[module_name]


def test_the_whole_flow_package_has_55_mappings() -> None:
    """7+10+7+8+8+8+7 = 55 —— 与 Java 的映射总数一致."""
    total = sum(len(table) for table in ROUTE_TABLES.values())

    assert total == 55


@pytest.mark.parametrize("module_name", sorted(ROUTE_TABLES))
def test_the_single_segment_path_variable_is_declared_last(module_name: str) -> None:
    """``GET /{id}`` 必须排在所有静态 GET 之后，否则 ``/export`` 会被当成主键."""
    router = _module(module_name).router
    paths = [route.path for route in router.routes]
    catch_all = f"{router.prefix}/{{id}}"

    if catch_all not in paths:
        pytest.skip(f"{module_name} 没有单段路径变量")

    position = paths.index(catch_all)
    getters = [
        index
        for index, route in enumerate(router.routes)
        if "GET" in route.methods and route.path != catch_all
    ]

    assert all(index < position for index in getters), paths


# --------------------------------------------------------------------------- 权限点


def test_apply_info_only_guards_list_all(monkeypatch: Any) -> None:
    """``/listAll`` 是唯一挂 ``@PreAuthorize`` 的方法；``/list`` 登录即可."""
    module = _module("flow_apply_info_controller")
    _inject(monkeypatch, module, _FakeService())
    client = TestClient(_build_app(module.router, permissions=set()))

    assert client.get("/flow/applyinfo/list").json()["code"] == 200
    assert client.get("/flow/applyinfo/listAll").json()["code"] == 403
    assert client.get("/flow/applyinfo/export").json()["code"] == 200
    assert client.post("/flow/applyinfo", json={}).json()["code"] == 200
    assert client.delete("/flow/applyinfo/a,b").json()["code"] == 200


def test_apply_info_list_all_passes_with_the_permission(monkeypatch: Any) -> None:
    module = _module("flow_apply_info_controller")
    _inject(monkeypatch, module, _FakeService())
    client = TestClient(
        _build_app(module.router, permissions={"flow:applyinfo:list"})
    )

    assert client.get("/flow/applyinfo/listAll").json()["code"] == 200


def test_flow_name_guards_every_method_except_list_query(monkeypatch: Any) -> None:
    """``FlowNameController`` 是本组唯一逐个方法都挂 ``@PreAuthorize`` 的."""
    module = _module("flow_name_controller")
    _inject(monkeypatch, module, _FakeService())
    client = TestClient(_build_app(module.router, permissions=set()))

    guarded = [
        client.get("/flow/flowname/list"),
        client.get("/flow/flowname/export"),
        client.get("/flow/flowname/1"),
        client.post("/flow/flowname", json={}),
        client.put("/flow/flowname", json={}),
        client.delete("/flow/flowname/a,b"),
        client.post("/flow/flowname/tbFlow", json={}),
    ]

    assert [response.json()["code"] for response in guarded] == [403] * 7
    # /listQuery 没有权限点 -> 登录即可
    assert client.get("/flow/flowname/listQuery").json()["code"] == 200


@pytest.mark.parametrize(
    ("module_name", "path", "method"),
    [
        ("flow_current_node_controller", "/flow/currentnode/list", "get"),
        ("flow_current_node_controller", "/flow/currentnode/saveFlowAuit", "put"),
        ("flow_current_node_controller", "/flow/currentnode/submitReturn", "post"),
        ("flow_current_node_controller", "/flow/currentnode/submitEntrustFlow", "post"),
        ("flow_list_controller", "/flow/flowlist/list", "get"),
        ("flow_message_dispose_controller", "/flow/messagedispose/list", "get"),
        ("flow_message_info_controller", "/flow/messageinfo/list", "get"),
        ("flow_template_controller", "/flow/flowtemplate/list", "get"),
    ],
)
def test_the_other_five_controllers_need_login_only(
    monkeypatch: Any, module_name: str, path: str, method: str
) -> None:
    """这 5 个控制器在 Java 里的 ``@PreAuthorize`` 全是注释行 —— 空权限集也应 200."""
    module = _module(module_name)
    _inject(monkeypatch, module, _FakeService())
    client = TestClient(_build_app(module.router, permissions=set()))

    response = getattr(client, method)(path, **({"json": {}} if method != "get" else {}))

    assert response.json()["code"] == 200


# --------------------------------------------------------------------------- 我的申请


def test_apply_info_list_forces_create_by_to_the_current_user(monkeypatch: Any) -> None:
    """``/list`` 里那句 ``setCreateBy(getUserId())`` —— 只能看到自己的."""
    module = _module("flow_apply_info_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/flow/applyinfo/list")

    assert service.calls[-1][1].create_by == 2


def test_apply_info_list_all_keeps_create_by_empty(monkeypatch: Any) -> None:
    """``/listAll`` 没有那句 ``setCreateBy`` —— 条件保持 ``None``."""
    module = _module("flow_apply_info_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/flow/applyinfo/listAll")

    assert service.calls[-1][1].create_by is None


def test_apply_info_export_goes_through_excel_util(monkeypatch: Any) -> None:
    """``export`` 走 ``ExcelUtil<FlowApplyInfo>``：返回体只有 ``msg``、没有 ``data``."""
    module = _module("flow_apply_info_controller")
    _inject(monkeypatch, module, _FakeService(rows=[FlowApplyInfo(id="a-1")]))

    client = TestClient(_build_app(module.router))
    body = client.get("/flow/applyinfo/export").json()

    assert body["code"] == 200
    assert "data" not in body
    assert body["msg"].endswith("_我的申请数据.xlsx")


# --------------------------------------------------------------------------- 当前节点


def test_get_info_by_bill_id_echoes_the_probe_when_nothing_matches(
    monkeypatch: Any,
) -> None:
    """查不到时返回**查询对象本身**（带 ``billOid``），不是 ``null``."""
    module = _module("flow_current_node_controller")
    _inject(monkeypatch, module, _FakeService(rows=[]))

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/currentnode/getInfoByBillId/B-9").json()["data"]

    assert data["billOid"] == "B-9"
    assert data["id"] is None


def test_get_info_by_bill_id_returns_the_first_row(monkeypatch: Any) -> None:
    module = _module("flow_current_node_controller")
    rows = [FlowCurrentNode(id="n-1", bill_oid="B-9"), FlowCurrentNode(id="n-2")]
    _inject(monkeypatch, module, _FakeService(rows=rows))

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/currentnode/getInfoByBillId/B-9").json()["data"]

    assert data["id"] == "n-1"


def test_save_flow_auit_is_a_put_and_reaches_the_service(monkeypatch: Any) -> None:
    module = _module("flow_current_node_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    body = client.put(
        "/flow/currentnode/saveFlowAuit",
        json={"billOid": "B-1", "auitEmpOid": "9", "shValue": "1"},
    ).json()

    assert body["code"] == 200
    assert service.calls[-1][0] == "save_flow_auit"
    assert service.calls[-1][1].sh_value == "1"


# --------------------------------------------------------------------------- 审核历史


def test_listnew_rewrites_a_blank_bill_oid_to_minus_one(monkeypatch: Any) -> None:
    """``billOid`` 为空（``null`` 或空串）-> ``"-1"``，于是查不到任何历史."""
    module = _module("flow_list_controller")
    list_service = _FakeService()
    apply_service = _FakeService()
    _inject(monkeypatch, module, list_service)
    _inject(monkeypatch, module, apply_service, name="_APPLY_SERVICE")

    client = TestClient(_build_app(module.router))
    body = client.get("/flow/flowlist/listnew").json()

    assert body["data"] == []
    assert list_service.calls[-1][1].bill_oid == "-1"
    assert apply_service.calls[-1][1].bill_oid == "-1"


def test_listnew_appends_the_current_auditor_while_approving(monkeypatch: Any) -> None:
    """``flow_status == "2"`` 且 ``BACK_COL1`` 非空 -> 补一条"待审批"."""
    module = _module("flow_list_controller")
    history = [FlowList(id="h-1", sh_value="提交")]
    _inject(monkeypatch, module, _FakeService(rows=history))
    _inject(
        monkeypatch,
        module,
        _FakeService(rows=[FlowApplyInfo(flow_status="2", back_col1="张三")]),
        name="_APPLY_SERVICE",
    )

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/flowlist/listnew", params={"billOid": "B-1"}).json()["data"]

    assert len(data) == 2
    assert data[0]["id"] == "h-1"
    assert data[1]["shUser"] == "张三"
    assert data[1]["shValue"] == "待审批"
    assert data[1]["id"] is None


def test_listnew_skips_the_extra_row_when_the_auditor_is_blank(
    monkeypatch: Any,
) -> None:
    module = _module("flow_list_controller")
    _inject(monkeypatch, module, _FakeService(rows=[FlowList(id="h-1")]))
    _inject(
        monkeypatch,
        module,
        _FakeService(rows=[FlowApplyInfo(flow_status="2", back_col1="  ")]),
        name="_APPLY_SERVICE",
    )

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/flowlist/listnew", params={"billOid": "B-1"}).json()["data"]

    assert len(data) == 1


def test_listnew_appends_the_end_marker_when_approved(monkeypatch: Any) -> None:
    """``flow_status == "3"`` -> 补一条"流程结束"（不看 ``BACK_COL1``）."""
    module = _module("flow_list_controller")
    _inject(monkeypatch, module, _FakeService(rows=[FlowList(id="h-1")]))
    _inject(
        monkeypatch,
        module,
        _FakeService(rows=[FlowApplyInfo(flow_status="3")]),
        name="_APPLY_SERVICE",
    )

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/flowlist/listnew", params={"billOid": "B-1"}).json()["data"]

    assert len(data) == 2
    assert data[1]["shValue"] == "流程结束"
    assert data[1]["shUser"] is None


@pytest.mark.parametrize("status", ["1", "4", "5", None])
def test_listnew_appends_nothing_for_the_other_statuses(
    monkeypatch: Any, status: Optional[str]
) -> None:
    """起草中 / 退回 / 拒绝（以及 ``flow_status`` 为空）都不补行."""
    module = _module("flow_list_controller")
    _inject(monkeypatch, module, _FakeService(rows=[FlowList(id="h-1")]))
    _inject(
        monkeypatch,
        module,
        _FakeService(rows=[FlowApplyInfo(flow_status=status, back_col1="张三")]),
        name="_APPLY_SERVICE",
    )

    client = TestClient(_build_app(module.router))
    data = client.get("/flow/flowlist/listnew", params={"billOid": "B-1"}).json()["data"]

    assert len(data) == 1


# --------------------------------------------------------------------------- 消息处理人


def test_delmes_and_szzdmes_pass_the_current_user_as_a_string(monkeypatch: Any) -> None:
    """``SecurityUtils.getUserId() + ""`` —— ``Long`` 拼成 ``String``."""
    module = _module("flow_message_dispose_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.delete("/flow/messagedispose/delmes/M-1")
    client.delete("/flow/messagedispose/szzdmes/M-1")

    assert service.calls[-2] == ("remove_flow_message", ("M-1", "2"))
    assert service.calls[-1] == ("save_szzd_flow_message", ("M-1", "2"))


# --------------------------------------------------------------------------- 内部消息


@pytest.mark.parametrize(
    ("path", "flag"),
    [
        ("/flow/messageinfo/list", "mydb"),
        ("/flow/messageinfo/listyb", "myyb"),
        ("/flow/messageinfo/listyj", "myyj"),
        ("/flow/messageinfo/listxx", "myxx"),
    ],
)
def test_each_message_list_sets_its_flag_and_the_user(
    monkeypatch: Any, path: str, flag: str
) -> None:
    module = _module("flow_message_info_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    assert client.get(path).json()["code"] == 200

    query = service.calls[-1][1]
    assert query.flag == flag
    assert query.user_id == 2


def test_message_export_sets_neither_flag_nor_user(monkeypatch: Any) -> None:
    """``export`` 是"按查询条件全量"，控制器不设 ``flag`` / ``userId``."""
    module = _module("flow_message_info_controller")
    service = _FakeService(rows=[FlowMessageInfo(id="m-1")])
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    body = client.get("/flow/messageinfo/export").json()

    assert body["msg"].endswith("_系统内部消息数据.xlsx")
    query = service.calls[-1][1]
    assert query.flag is None
    assert query.user_id is None


def test_export_shrz_fills_the_template_placeholders(monkeypatch: Any) -> None:
    """模板占位符：``applyName`` / ``createTime``(``yyyy-MM-dd``) / ``msgTitle`` / ``entitylist``."""
    module = _module("flow_message_info_controller")
    message = FlowMessageInfo(
        id="m-1",
        bill_oid="B-1",
        apply_name="李四",
        msg_title="公车申请",
        create_time=datetime(2021, 5, 7, 15, 30, 45),
    )
    _inject(monkeypatch, module, _FakeService(by_id=message))
    _inject(
        monkeypatch,
        module,
        _FakeService(rows=[FlowList(id="h-1"), FlowList(id="h-2"), FlowList(id="h-3")]),
        name="_FLOW_LIST_SERVICE",
    )

    captured: Dict[str, Any] = {}

    class _FakeParams:
        def __init__(self, template: str) -> None:
            captured["template"] = template

    class _FakeExportUtil:
        @staticmethod
        def export_excel(params: Any, data: Dict[str, Any]) -> Any:
            captured["data"] = data
            return object()

    monkeypatch.setattr(module, "TemplateExportParams", _FakeParams)
    monkeypatch.setattr(module, "ExcelExportUtil", _FakeExportUtil)
    monkeypatch.setattr(module, "workbook_to_bytes", lambda _wb: b"xlsx-bytes")

    client = TestClient(_build_app(module.router))
    response = client.get("/flow/messageinfo/exportShrz", params={"id": "m-1"})

    assert response.content == b"xlsx-bytes"
    assert response.headers["content-disposition"] == "attachment"
    assert captured["template"] == "templates/export/exportShrz.xlsx"
    data = captured["data"]
    assert data["applyName"] == "李四"
    assert data["createTime"] == "2021-05-07"
    assert data["msgTitle"] == "公车申请"
    assert [row.sort for row in data["entitylist"]] == [1, 2, 3]


def test_export_shrz_returns_an_empty_body_when_rendering_fails(
    monkeypatch: Any,
) -> None:
    """Java 的 ``catch (Exception e) { e.printStackTrace(); }`` —— 空 body、无响应头."""
    module = _module("flow_message_info_controller")
    _inject(
        monkeypatch,
        module,
        _FakeService(by_id=FlowMessageInfo(id="m-1", bill_oid="B-1")),
    )
    _inject(monkeypatch, module, _FakeService(rows=[]), name="_FLOW_LIST_SERVICE")
    monkeypatch.setattr(module, "TemplateExportParams", _boom)

    client = TestClient(_build_app(module.router))
    response = client.get("/flow/messageinfo/exportShrz", params={"id": "m-1"})

    assert response.content == b""
    assert "content-disposition" not in response.headers


# --------------------------------------------------------------------------- 流程名称


def test_flow_name_list_query_filters_by_the_login_tenant(monkeypatch: Any) -> None:
    """``/listQuery`` 是单位视角：控制器强制 ``setTenantId(getTenantId())``."""
    module = _module("flow_name_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router, tenant_id=100))
    client.get("/flow/flowname/listQuery")

    assert service.calls[-1][1].tenant_id == 100


def test_flow_name_list_does_not_filter_by_tenant(monkeypatch: Any) -> None:
    """``/list`` 不过滤租户（即便请求里带了 ``tenantId`` 也照收）."""
    module = _module("flow_name_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router, tenant_id=100))
    client.get("/flow/flowname/list")

    assert service.calls[-1][1].tenant_id is None


def test_tb_flow_reuses_the_edit_permission(monkeypatch: Any) -> None:
    """``/tbFlow`` 的权限点是 ``flow:flowname:edit``（不是 ``:add``）."""
    module = _module("flow_name_controller")
    _inject(monkeypatch, module, _FakeService())

    without = TestClient(_build_app(module.router, permissions={"flow:flowname:add"}))
    assert without.post("/flow/flowname/tbFlow", json={}).json()["code"] == 403

    with_edit = TestClient(
        _build_app(module.router, permissions={"flow:flowname:edit"})
    )
    assert with_edit.post("/flow/flowname/tbFlow", json={}).json()["code"] == 200


# --------------------------------------------------------------------------- 流程节点


def test_flowlist_returns_an_empty_array_when_flow_oid_is_blank(
    monkeypatch: Any,
) -> None:
    """``flowOid`` 为空时连库都不查，直接回空数组."""
    module = _module("flow_template_controller")
    service = _FakeService(rows=[FlowTemplate(id="t-1")])
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    body = client.get("/flow/flowtemplate/flowlist").json()

    assert body["data"] == []
    assert service.calls == []


def test_flowlist_prepends_the_virtual_submit_node(monkeypatch: Any) -> None:
    """头部虚拟节点：``id="-1"`` / ``nodeOrder=-1`` / ``nodeKey="tj"`` / ``nodeName="申请人提交"``."""
    module = _module("flow_template_controller")
    _inject(monkeypatch, module, _FakeService(rows=[FlowTemplate(id="t-1", node_order=1)]))

    client = TestClient(_build_app(module.router))
    data = client.get(
        "/flow/flowtemplate/flowlist", params={"flowOid": "F-1"}
    ).json()["data"]

    assert [row["id"] for row in data] == ["-1", "t-1"]
    assert data[0]["nodeOrder"] == -1
    assert data[0]["nodeKey"] == "tj"
    assert data[0]["nodeName"] == "申请人提交"
    assert data[0]["flowOid"] is None


def test_flowlist_treats_a_whitespace_only_oid_as_blank(monkeypatch: Any) -> None:
    """``CommonUtil.isNotBlank`` 会 ``trim`` —— 全空白等于空."""
    module = _module("flow_template_controller")
    service = _FakeService(rows=[])
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    body = client.get("/flow/flowtemplate/flowlist", params={"flowOid": "   "}).json()

    assert body["data"] == []
    assert service.calls == []


def test_the_template_export_path_is_not_swallowed_by_the_id_route(
    monkeypatch: Any,
) -> None:
    """``/flowlist`` 是静态段，不能被 ``/{id}`` 抢先匹配."""
    module = _module("flow_template_controller")
    service = _FakeService(rows=[])
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/flow/flowtemplate/flowlist", params={"flowOid": "F-1"})

    called = [name for name, _ in service.calls]
    assert "select_flow_template_list" in called
    assert "select_flow_template_by_id" not in called
