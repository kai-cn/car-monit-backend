"""``CommonController`` -- ``/common`` 的 4 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/common/CommonController.java
#   + ruoyi-framework/.../config/SecurityConfig.java（``/common/download**``）

这一层测什么
------------
* 4 个映射全部注册，且**一个** ``@PreAuthorize`` 都没有；
* ``/common/download`` 在 ``SecurityConfig`` 里是 ``anonymous()`` —— **已登录反而 403**；
* ``/common/download/resource`` 并**没有**被 ``/common/download**`` 遮蔽，是真的
  ``authenticated()``（见 :class:`TestSecurityRules` 的解释）；
* 缺 ``fileName`` / 缺 ``delete`` 都**不是 400**，而是"异常被吞 -> 200"；
* ``delete`` 只在**下载成功之后**才判断，所以缺参时文件照下、但**不删**；
* 文件不存在是 **200 + 完整响应头 + 空 body**（不是 404）；
* ``upload`` / ``uploads`` 的返回体字段名与拼接方式。

为什么直调函数 + mini app 两条腿
--------------------------------
直调能拿到 ``Response`` 对象断言 headers 与 body；走 ASGI 才验证 FastAPI 的 query
绑定（``fileName`` 的别名、``delete`` 的可选性）。``SecurityMiddleware`` 需要 Redis /
MySQL，所以 mini app 里不装它 —— 权限规则另外用 ``resolve_access`` 直接断言。
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, Iterator, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.common import common_controller as controller
from app.api.common.common_controller import file_download, resource_download
from app.common.exception.exceptions import ServiceException
from app.config.exception_handlers import register_exception_handlers
from app.framework.config.security_config import AccessMode, resolve_access
from app.settings import get_settings, reset_settings_cache


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def profile(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """``ruoyi.profile`` 指到临时目录 —— 上传/下载都真的读写磁盘."""
    value = str(tmp_path / "uploadPath")
    monkeypatch.setenv("RUOYI__PROFILE", value)
    reset_settings_cache()
    os.makedirs(get_settings().ruoyi.download_path, exist_ok=True)
    yield value
    reset_settings_cache()


@pytest.fixture
def http() -> Any:
    """只挂本控制器 + 异常处理器的 mini app（不经 SecurityMiddleware）."""
    return TestClient(_build_app())


def _build_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(controller.router)
    return application


def _drop_file(name: str = "export_用户数据.xlsx", content: bytes = b"xlsx-bytes") -> str:
    """往 ``download_path`` 放一个可下载的文件，返回**磁盘绝对路径**."""
    path = get_settings().ruoyi.download_path + name
    with open(path, "wb") as target:
        target.write(content)
    return path


class _FakeUpload:
    """``FileUploadUtils.upload`` 的替身 —— 不落盘，只返回一个假的相对 url."""

    def __init__(self, url: str = "/profile/upload/2026/10/27/a_20261027120000A001.png") -> None:
        self.url = url
        self.calls: List[tuple] = []
        self.error: Optional[BaseException] = None

    def __call__(self, base_dir: str, file: Any) -> str:
        self.calls.append((base_dir, getattr(file, "filename", None)))
        if self.error is not None:
            raise self.error
        return self.url


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """4 个映射的路径 / 动词."""

    def test_the_four_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/common/download", ("GET",)),
            ("/common/download/resource", ("GET",)),
            ("/common/upload", ("POST",)),
            ("/common/uploads", ("POST",)),
        }

    def test_there_is_no_pre_authorize_anywhere(self) -> None:
        """Java 源码里**一个** ``@PreAuthorize`` 都没有."""
        source = controller.__file__
        assert source is not None
        with open(source, encoding="utf-8") as handle:
            body = handle.read()
        assert "@pre_authorize_permi" not in body


class TestSecurityRules:
    """``SecurityConfig`` 对 ``/common/**`` 的判定."""

    def test_download_is_anonymous_only(self) -> None:
        assert resolve_access("GET", "/common/download") is AccessMode.ANONYMOUS

    def test_download_resource_is_not_shadowed_by_the_earlier_pattern(self) -> None:
        """``/common/download**`` **不会**吃掉 ``/common/download/resource``.

        ``AntPathMatcher`` 先按 ``/`` 切段：``/common/download**`` 切成
        ``["common", "download**"]``，而 ``/common/download/resource`` 切成
        ``["common", "download", "resource"]``。第二段 ``download**`` 确实能匹配
        ``download``，但此时**路径还有剩余段、模式已经用完**，``doMatch`` 直接返回
        ``false`` —— 所以 ``.antMatchers("/common/download/resource**").authenticated()``
        真的生效。
        """
        assert resolve_access("GET", "/common/download/resource") is AccessMode.AUTHENTICATED

    def test_upload_is_login_only(self) -> None:
        assert resolve_access("POST", "/common/upload") is AccessMode.AUTHENTICATED
        assert resolve_access("POST", "/common/uploads") is AccessMode.AUTHENTICATED


# --------------------------------------------------------------------------- 下载


class TestFileDownload:
    """``fileDownload``."""

    def test_a_successful_download_writes_bytes_and_headers(self, http: Any) -> None:
        path = _drop_file()

        response = http.get(
            "/common/download", params={"fileName": "export_用户数据.xlsx", "delete": "true"}
        )

        assert response.status_code == 200
        assert response.content == b"xlsx-bytes"
        assert response.headers["content-type"] == "application/octet-stream"
        # 真实文件名 = 毫秒时间戳 + 第一个 "_" 之后的部分；那个 "_" 已被 substring 吃掉
        assert response.headers["download-filename"].endswith(
            "%E7%94%A8%E6%88%B7%E6%95%B0%E6%8D%AE.xlsx"
        )
        assert response.headers["content-disposition"].startswith("attachment; filename=")
        # delete=true -> 文件被删掉
        assert not os.path.exists(path)

    def test_delete_false_keeps_the_file(self, http: Any) -> None:
        path = _drop_file("a.png")

        http.get("/common/download", params={"fileName": "a.png", "delete": "false"})

        assert os.path.exists(path)

    def test_delete_accepts_the_spring_true_literals(self, http: Any) -> None:
        path = _drop_file("a.png")

        http.get("/common/download", params={"fileName": "a.png", "delete": "on"})

        assert not os.path.exists(path)

    def test_a_missing_delete_parameter_still_downloads_but_keeps_the_file(
        self, http: Any
    ) -> None:
        """Java: ``Boolean delete`` 缺参是 ``null`` -> ``if (delete)`` 拆箱 NPE -> 被吞.

        文件**已经写进响应**了，所以客户端拿到的是完整内容；只是磁盘上的文件没被删。
        """
        path = _drop_file("a.png")

        response = http.get("/common/download", params={"fileName": "a.png"})

        assert response.status_code == 200
        assert response.content == b"xlsx-bytes"
        assert os.path.exists(path)

    def test_an_unparseable_delete_is_code_500(self, http: Any) -> None:
        """Spring 绑定 ``Boolean delete`` 失败 -> ``MethodArgumentTypeMismatchException``.

        这里用 :class:`ServiceException` 承载同样的信息：它继承 ``RuntimeError``，被
        ``ExceptionMiddleware`` 的处理器接住；若用 ``ValueError`` 会落到
        ``ServerErrorMiddleware``，在 ``TestClient`` 下会直接重抛而不是回信封。
        """
        _drop_file("a.png")

        response = http.get(
            "/common/download", params={"fileName": "a.png", "delete": "maybe"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 500
        assert body["msg"] == (
            "请求参数类型不匹配，参数[delete]要求类型为：'java.lang.Boolean'，但输入值为：'maybe'"
        )

    def test_a_missing_file_name_is_swallowed(self, http: Any) -> None:
        """``checkAllowDownload(null)`` -> ``getFileType(null)`` NPE -> 被吞."""
        response = http.get("/common/download", params={"delete": "false"})

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def test_a_traversal_attempt_is_rejected(self, http: Any) -> None:
        response = http.get("/common/download", params={"fileName": "../etc/passwd"})

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def test_a_suffix_outside_the_whitelist_is_rejected(self, http: Any) -> None:
        response = http.get("/common/download", params={"fileName": "a.json"})

        assert response.status_code == 200
        assert response.content == b""

    def test_a_missing_file_on_disk_is_200_with_headers_and_no_body(self, http: Any) -> None:
        """``writeBytes`` 抛 ``FileNotFoundException``，但响应头**已经写出去了**."""
        response = http.get("/common/download", params={"fileName": "a.png", "delete": "false"})

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" in response.headers

    def test_the_real_file_name_keeps_the_whole_name_when_there_is_no_underscore(
        self, http: Any
    ) -> None:
        """``indexOf("_") == -1`` -> ``substring(0)`` -> 整个文件名."""
        _drop_file("a.png")
        before = int(time.time() * 1000)

        response = http.get("/common/download", params={"fileName": "a.png", "delete": "true"})

        after = int(time.time() * 1000)
        # 没有 "_" 可切，头部就是 ``<millis>a.png`` —— 用前导数字解析
        stamp = int(re.match(r"^(\d+)", response.headers["download-filename"]).group(1))
        assert before <= stamp <= after

    def test_direct_call_returns_a_response_object(self) -> None:
        _drop_file("a.png")

        result = file_download(_FakeRequest(), file_name="a.png", delete="false")

        assert result.body == b"xlsx-bytes"
        # Starlette 的 Headers 会把键名统一成小写
        assert result.headers["content-type"] == "application/octet-stream"


# --------------------------------------------------------------------------- 本地资源


class TestResourceDownload:
    """``resourceDownload`` —— 方法体整块被注释，永远 200 空 body."""

    def test_an_allowed_resource_is_still_empty(self, http: Any) -> None:
        response = http.get("/common/download/resource", params={"resource": "/profile/a.png"})

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def test_a_rejected_resource_looks_identical(self, http: Any) -> None:
        response = http.get("/common/download/resource", params={"resource": "/profile/a.json"})

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def test_a_missing_resource_parameter_is_also_swallowed(self, http: Any) -> None:
        response = http.get("/common/download/resource")

        assert response.status_code == 200
        assert response.content == b""

    def test_direct_call_returns_an_empty_response(self) -> None:
        result = resource_download(_FakeRequest(), resource="/profile/a.png")

        assert result.body == b""


# --------------------------------------------------------------------------- 上传


class TestUploadFile:
    """``uploadFile`` —— 单个上传."""

    def test_the_four_extra_keys_follow_code_and_msg(
        self, http: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _FakeUpload()
        monkeypatch.setattr(controller.FileUploadUtils, "upload", fake)

        response = http.post("/common/upload", files={"file": ("a.png", b"png", "image/png")})

        body = response.json()
        # Java: ``AjaxResult`` 是 ``HashMap``，键序是桶序而非 put 序：
        # msg(0) -> fileName(2) -> code(3) -> newFileName(9) -> url(14) -> originalFilename(14)
        assert list(body) == [
            "msg",
            "fileName",
            "code",
            "newFileName",
            "url",
            "originalFilename",
        ]
        assert body["code"] == 200
        assert body["fileName"] == fake.url
        # Java: serverConfig.getUrl() + fileName
        assert body["url"] == "http://testserver" + fake.url
        assert body["newFileName"] == "a_20261027120000A001.png"
        assert body["originalFilename"] == "a.png"
        # 上传目录是 {profile}/upload
        assert fake.calls == [(get_settings().ruoyi.upload_path, "a.png")]

    def test_business_error_keeps_its_message(
        self, http: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """校验类异常（文件名过长/后缀不允许）保留可操作提示."""
        fake = _FakeUpload()
        fake.error = ServiceException("文件名长度超出限定长度")
        monkeypatch.setattr(controller.FileUploadUtils, "upload", fake)

        response = http.post("/common/upload", files={"file": ("a.png", b"png", "image/png")})

        assert response.json() == {"code": 500, "msg": "文件名长度超出限定长度"}

    def test_io_error_is_masked(
        self, http: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """磁盘路径/空间不足/S3 错误不能原样透给客户端（COMPATIBILITY §46.3）."""
        fake = _FakeUpload()
        fake.error = OSError("[Errno 28] No space left on device: D:/secret/upload")
        monkeypatch.setattr(controller.FileUploadUtils, "upload", fake)

        response = http.post("/common/upload", files={"file": ("a.png", b"png", "image/png")})

        assert response.json() == {"code": 500, "msg": controller.UPLOAD_ERROR_MESSAGE}
        assert "No space left" not in response.text
        assert "D:/secret" not in response.text

    def test_a_missing_part_is_a_code_500(self, http: Any) -> None:
        """Java 是 ``file == null`` -> NPE -> ``error(null)``；信封同样是 code 500."""
        response = http.post("/common/upload")

        assert response.json()["code"] == 500


class TestUploadFiles:
    """``uploadFiles`` —— 多个上传，返回值是**逗号串**而不是数组."""

    def test_comma_joined_strings(self, http: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        urls = iter(
            [
                "/profile/upload/2026/10/27/a_1.png",
                "/profile/upload/2026/10/27/b_2.png",
            ]
        )

        def _fake_upload(base_dir: str, file: Any) -> str:
            return next(urls)

        monkeypatch.setattr(controller.FileUploadUtils, "upload", _fake_upload)

        response = http.post(
            "/common/uploads",
            files=[
                ("files", ("a.png", b"a", "image/png")),
                ("files", ("b.png", b"b", "image/png")),
            ],
        )

        body = response.json()
        # Java: ``HashMap`` 桶序：msg(0) -> urls(2) -> code(3) -> newFileNames(4)
        # -> fileNames(14) -> originalFilenames(14)（同桶保持 put 序）。
        assert list(body) == [
            "msg",
            "urls",
            "code",
            "newFileNames",
            "fileNames",
            "originalFilenames",
        ]
        assert body["urls"] == (
            "http://testserver/profile/upload/2026/10/27/a_1.png,"
            "http://testserver/profile/upload/2026/10/27/b_2.png"
        )
        assert body["fileNames"] == (
            "/profile/upload/2026/10/27/a_1.png,/profile/upload/2026/10/27/b_2.png"
        )
        assert body["newFileNames"] == "a_1.png,b_2.png"
        assert body["originalFilenames"] == "a.png,b.png"

    def test_one_failure_discards_the_whole_batch(
        self, http: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: List[str] = []

        def _fake_upload(base_dir: str, file: Any) -> str:
            calls.append(file.filename)
            if file.filename == "b.png":
                raise OSError("boom")
            return "/profile/upload/a_1.png"

        monkeypatch.setattr(controller.FileUploadUtils, "upload", _fake_upload)

        response = http.post(
            "/common/uploads",
            files=[
                ("files", ("a.png", b"a", "image/png")),
                ("files", ("b.png", b"b", "image/png")),
            ],
        )

        assert response.json() == {"code": 500, "msg": controller.UPLOAD_ERROR_MESSAGE}
        assert "boom" not in response.text
        # 前面的文件已经上传过了，**不会**回滚
        assert calls == ["a.png", "b.png"]


class _FakeRequest:
    """只要 ``base_url`` 能用的最小 ``Request`` 替身."""

    def __init__(self, base_url: str = "http://testserver/") -> None:
        self.base_url = base_url


__all__ = [
    "TestFileDownload",
    "TestResourceDownload",
    "TestRouteTable",
    "TestSecurityRules",
    "TestUploadFile",
    "TestUploadFiles",
]
