"""``DownTemplateController`` -- ``GET /downTemplate/{type}``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/common/DownTemplateController.java
#   + ruoyi-framework/.../config/SecurityConfig.java（无规则 -> anyRequest()）

这一层测什么
------------
* 只有 **1** 个映射，且没有 ``@PreAuthorize``；
* ``SecurityConfig`` 没有 ``/downTemplate/**`` 规则 —— 落到 ``anyRequest()``，
  所以是 ``authenticated()``（登录即可，不查权限点）；
* 7 个 ``type`` 各自对应固定模板，回的是**模板原始字节**；
* 成功时 ``Content-Type: application/octet-stream;charset=UTF-8`` 且
  ``Content-Disposition: attachment`` —— **没有 filename**（Java 就写死了 ``"attachment"``）；
* 未知 ``type`` **不是 404**：``url`` 保持初值 ``"templates/down"``（一个目录），
  读失败 -> ``catch`` -> ``return null`` -> **200 + 空 body + 无响应头**。

为什么断言"原始字节"
--------------------
Java 走 easypoi ``TemplateExportParams(url, true)`` + 空 ``HashMap`` 渲染后写流。
这 7 个模板里**没有任何** ``${...}`` 占位符（已逐格核对），所以"渲染"等于"原样输出"。
Python 侧直接返回文件字节 —— 因此断言 ``response.content == 磁盘上的字节``
既钉住了实现，也钉住了"内容与 Java 一致"这个更强的性质。

模板在哪
--------
Java 是 classpath ``templates/down/``；Python 的 ``config/`` 是 classpath 的镜像，
所以落在 ``config/templates/down/``（见 :data:`app.settings.CONFIG_DIR`）。
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.common import down_template_controller as controller
from app.config.exception_handlers import register_exception_handlers
from app.framework.config.security_config import AccessMode, resolve_access
from app.settings import CONFIG_DIR

#: Java if/else 链里的 7 个分支（``type -> 文件名``）。
EXPECTED_TEMPLATES: Dict[str, str] = {
    "goodsFkApplyDetail": "importGoodsFkApplyDetail.xlsx",
    "goodsRkApplyDetail": "importGoodsRkApplyDetail.xlsx",
    "planListDetail": "importPlanListDetail.xlsx",
    "importPsbz": "importPsbz.xlsx",
    "importSupplierAnnualScore": "importSupplierAnnualScore.xlsx",
    "carinfo": "importCar.xlsx",
    "carExcept": "importCarExcept.xlsx",
}

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
EXPECTED_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"


# --------------------------------------------------------------------------- 装配


@pytest.fixture
def http() -> Any:
    """只挂本控制器 + 异常处理器的 mini app（避开 SecurityMiddleware 的 Redis/MySQL）."""
    return TestClient(_build_app())


def _build_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(controller.router)
    return application


def _template_bytes(file_name: str) -> bytes:
    """读磁盘上的模板 —— 用来断言"响应体 == 模板原始字节"."""
    path = os.path.join(str(CONFIG_DIR), "templates", "down", file_name)
    with open(path, "rb") as handle:
        return handle.read()


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """1 个映射的路径 / 动词."""

    def test_the_only_path_is_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {("/downTemplate/{type}", ("GET",))}

    def test_there_is_no_pre_authorize_anywhere(self) -> None:
        """Java 源码里**一个** ``@PreAuthorize`` 都没有."""
        source = controller.__file__
        assert source is not None
        with open(source, encoding="utf-8") as handle:
            body = handle.read()
        assert "@pre_authorize_permi" not in body


class TestSecurityRules:
    """``SecurityConfig`` 对 ``/downTemplate/**`` 的判定."""

    def test_it_falls_through_to_any_request(self) -> None:
        """没有专门规则 -> ``anyRequest().authenticated()``：登录即可，不查权限点."""
        assert resolve_access("GET", "/downTemplate/carinfo") is AccessMode.AUTHENTICATED
        assert resolve_access("GET", "/downTemplate/whatever") is AccessMode.AUTHENTICATED


# --------------------------------------------------------------------------- 白名单


class TestTemplateMapping:
    """``type`` -> 模板文件的 7 个分支."""

    def test_the_mapping_matches_the_java_if_else_chain(self) -> None:
        assert controller.TEMPLATE_BY_TYPE == EXPECTED_TEMPLATES

    def test_every_template_file_exists_on_disk(self) -> None:
        """classpath 镜像：``config/templates/down/`` 下应该 7 个都在."""
        for type_, file_name in EXPECTED_TEMPLATES.items():
            path = os.path.join(str(CONFIG_DIR), "templates", "down", file_name)
            assert os.path.isfile(path), f"{type_} -> 缺模板 {path}"

    @pytest.mark.parametrize(("type_", "file_name"), list(EXPECTED_TEMPLATES.items()))
    def test_resolve_template_path_points_at_the_file(self, type_: str, file_name: str) -> None:
        assert controller.resolve_template_path(type_) == os.path.join(
            str(CONFIG_DIR), "templates", "down", file_name
        )

    @pytest.mark.parametrize("type_", ["", "unknown", "CarInfo", "carinfo/"])
    def test_an_unknown_type_resolves_to_the_directory(self, type_: str) -> None:
        """Java: ``url`` 停在初值 ``"templates/down"`` —— 那是个**目录**，读不到."""
        resolved = controller.resolve_template_path(type_)

        assert resolved == os.path.join(str(CONFIG_DIR), "templates", "down")
        assert os.path.isdir(resolved)


# --------------------------------------------------------------------------- 下载


class TestDownExcel:
    """``downExcel``."""

    @pytest.mark.parametrize(("type_", "file_name"), list(EXPECTED_TEMPLATES.items()))
    def test_the_seven_types_stream_the_raw_template(
        self, http: Any, type_: str, file_name: str
    ) -> None:
        response = http.get(f"/downTemplate/{type_}")

        assert response.status_code == 200
        assert response.content == _template_bytes(file_name)
        assert response.headers["content-type"] == EXPECTED_CONTENT_TYPE

    def test_the_disposition_has_no_filename(self, http: Any) -> None:
        """Java 只写 ``setHeader("Content-Disposition", "attachment")``."""
        response = http.get("/downTemplate/carinfo")

        assert response.headers["content-disposition"] == "attachment"
        assert "filename" not in response.headers["content-disposition"]

    @pytest.mark.parametrize("type_", ["unknown", "CarInfo", "car"])
    def test_an_unknown_type_is_200_with_an_empty_body(self, http: Any, type_: str) -> None:
        """``catch`` -> ``return null`` -> 200 空 body，**且没有**响应头."""
        response = http.get(f"/downTemplate/{type_}")

        assert response.status_code == 200
        assert response.content == b""
        # setContentType / setHeader 都在 try 里、在异常点之后 -> 一个都没写到
        assert "content-disposition" not in response.headers
        # Java 那边也没有 Content-Type（setContentType 同样被跳过）
        assert "content-type" not in response.headers

    def test_a_missing_template_file_degrades_the_same_way(
        self, http: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """白名单里有、但磁盘上被删了 —— 同样是 200 空 body（不是 500）."""
        monkeypatch.setattr(
            controller,
            "resolve_template_path",
            lambda type_: os.path.join(str(CONFIG_DIR), "templates", "down", "缺失.xlsx"),
        )

        response = http.get("/downTemplate/carinfo")

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def test_direct_call_returns_a_response_object(self) -> None:
        result = controller.down_excel("carExcept")

        assert result.body == _template_bytes("importCarExcept.xlsx")
        assert dict(result.headers)["content-type"] == EXPECTED_CONTENT_TYPE

    def test_direct_call_for_an_unknown_type_returns_an_empty_body(self) -> None:
        result = controller.down_excel("nope")

        assert result.body == b""
        assert "content-disposition" not in result.headers


__all__ = [
    "TestDownExcel",
    "TestRouteTable",
    "TestSecurityRules",
    "TestTemplateMapping",
]
