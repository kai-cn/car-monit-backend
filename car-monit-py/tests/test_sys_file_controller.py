"""``SysFileController`` -- ``/system/file`` 的 17 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysFileController.java

这一层测什么
------------
Service 已被 ``test_sys_file_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 17 个映射全部注册（本类没有 ``export``，因此不受 ``ExcelUtil`` 缺口影响）；
* 权限点只有 **两个**：``list`` = ``base:sysflie:list``（**音近拼错**，与
  ``sys_menu.perms`` 一致）、``DELETE /{ids}`` = ``base:supplier:remove``；
* ``/list`` / ``/getNewCa`` **必须**排在单段的 ``/{ids}`` 之前，
  ``/getInfoById/{id}`` **必须**排在两段的 ``/{bucket}/{fileName}`` 之前
  （FastAPI 按注册顺序匹配，Spring 按"更具体者优先"）；
* ``getInfo`` 的 ``deleteEnd`` 只删**一个**结尾逗号，删空后换成 ``"-111111"``；
* ``uploadFileId`` 里那句 ``AjaxResult.error("主键不能为空")`` 的返回值**被丢弃**；
* ``uploadPdf`` 的 ``HttpServletResponse`` 从未被写过，所以控制器不传；
* 两条 ``void`` 下载路由成功时是 ``application/octet-stream; charset=UTF-8`` +
  原始字节，失败时是 HTTP 200 + 空 body（**不是** 404）；
* ``uploadFile``（微信小程序）只收图片、区分大小写、上限 15M，两条文案不同。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_file_controller as controller
from app.api.system.sys_file_controller import (
    CA_NOT_FOUND_MESSAGE,
    EMPTY_IDS_PLACEHOLDER,
    FILE_TOO_LARGE_MESSAGE,
    NOT_PICTURE_MESSAGE,
    edit,
    file_view,
    get_info,
    get_info_by_id,
    get_new_ca,
    list_files,
    remove,
    remove_by_id,
    update_ca_file,
    upload,
    upload_by_url,
    upload_file_enc,
    upload_file_id,
    upload_pdf,
    upload_supplier,
    upload_wechat,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.ro.upload_ro import UploadRo
from app.system.domain.sys_file import SysFile


# --------------------------------------------------------------------------- fakes


class _FakeFileService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_id_result: Optional[SysFile] = None
        self.by_ids_result: List[SysFile] = []
        self.list_result: List[SysFile] = []
        self.envelope: Dict[str, Any] = {"code": 200, "msg": "操作成功", "data": 1}
        self.upload_result: Dict[str, Any] = {
            "code": 200,
            "msg": "操作成功",
            "data": [{"bucketName": "developer", "fileName": "u.pdf", "url": "/x", "id": "7"}],
        }
        self.upload_pdf_result: Dict[str, Any] = {"code": 200, "msg": "操作成功", "data": []}
        self.file_bytes = b"payload"
        self.file_content_type: Optional[str] = (
            "application/octet-stream; charset=UTF-8"
        )
        self.page_taken: Any = None

    def select_sys_file_list(self, entity: SysFile) -> List[SysFile]:
        self.calls.append(("select_sys_file_list", entity.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_sys_file_by_id(self, entity_id: Any) -> Optional[SysFile]:
        self.calls.append(("select_sys_file_by_id", entity_id))
        return self.by_id_result

    def select_sys_file_by_ids(self, ids: Any) -> List[SysFile]:
        self.calls.append(("select_sys_file_by_ids", ids))
        return self.by_ids_result

    def upload_files(self, files: Sequence[Any]) -> Dict[str, Any]:
        self.calls.append(("upload_files", list(files)))
        return self.upload_result

    def upload_by_url(self, ro_list: Any) -> Dict[str, Any]:
        self.calls.append(("upload_by_url", ro_list))
        return self.upload_result

    def upload_supplier(self, files: Sequence[Any], buss_names: Sequence[str]) -> Dict[str, Any]:
        self.calls.append(("upload_supplier", (list(files), list(buss_names))))
        return self.upload_result

    def upload_files_pdf(self, files: Sequence[Any], response: Any = None) -> Dict[str, Any]:
        self.calls.append(("upload_files_pdf", (list(files), response)))
        return self.upload_pdf_result

    def upload_file_id(self, file_id: Any, file: Any) -> Dict[str, Any]:
        self.calls.append(("upload_file_id", (file_id, file)))
        return self.upload_result

    def upload_files_enc(self, files: Sequence[Any]) -> Dict[str, Any]:
        self.calls.append(("upload_files_enc", list(files)))
        return self.upload_result

    def update_ca_file(self, entity: SysFile) -> Dict[str, Any]:
        self.calls.append(("update_ca_file", entity.model_copy(deep=True)))
        return self.envelope

    def save_sys_file(self, entity: SysFile) -> Dict[str, Any]:
        self.calls.append(("save_sys_file", entity.model_copy(deep=True)))
        return self.envelope

    def delete_sys_file_by_id(self, entity_id: Any) -> Dict[str, Any]:
        self.calls.append(("delete_sys_file_by_id", entity_id))
        return self.envelope

    def delete_sys_file_by_ids(self, ids: Sequence[Any]) -> Dict[str, Any]:
        self.calls.append(("delete_sys_file_by_ids", list(ids)))
        return self.envelope

    def get_file(self, bucket: str, file_name: str, sink: Any) -> None:
        self.calls.append(("get_file", (bucket, file_name)))
        if self.file_content_type is not None:
            sink.set_content_type(self.file_content_type)
        sink.get_output_stream().write(self.file_bytes)

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeFileService()
    monkeypatch.setattr(controller, "_FILE_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_file_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


@pytest.fixture
def http_lenient() -> Any:
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(
                    LoginUser(user=SysUser(user_id=2, user_name="ry"), permissions={"*:*:*"}),
                    None,
                    [],
                )
            )
            return await call_next(request)

    application.include_router(controller.router)
    return application


def authenticate(permissions: Optional[set] = None) -> SysUser:
    user = SysUser(user_id=2, user_name="ry")
    login_user = LoginUser(user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _stored(file_id: int = 7) -> SysFile:
    return SysFile(id=file_id, file_name="a.pdf", bucket_name="developer", type="pdf")


def _upload(filename: str = "a.pdf", content: bytes = b"hello") -> tuple:
    return ("files", (filename, content, "application/pdf"))


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_seventeen_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/file/list", ("GET",)),
            ("/system/file/getInfoById/{id}", ("GET",)),
            ("/system/file/getNewCa", ("GET",)),
            ("/system/file/{ids}", ("GET",)),
            ("/system/file/upload", ("POST",)),
            ("/system/file/uploadByUrl", ("POST",)),
            ("/system/file/uploadSupplier", ("POST",)),
            ("/system/file/uploadPdf", ("POST",)),
            ("/system/file/uploadFileId", ("POST",)),
            ("/system/file/uploadFileEnc", ("POST",)),
            ("/system/file/updateCAFile", ("POST",)),
            ("/system/file/uploadFile", ("POST",)),
            ("/system/file/{bucket}/{file_name}", ("GET",)),
            ("/system/file/view/{bucket}/{file_name}", ("GET",)),
            ("/system/file", ("PUT",)),
            ("/system/file/del/{id}", ("DELETE",)),
            ("/system/file/{ids}", ("DELETE",)),
        }

    def test_there_is_no_export(self) -> None:
        assert not any(route.path.endswith("/export") for route in controller.router.routes)

    def test_the_literal_get_paths_come_before_the_path_variables(self) -> None:
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/file/list") < paths.index("/system/file/{ids}")
        assert paths.index("/system/file/getNewCa") < paths.index("/system/file/{ids}")
        assert paths.index("/system/file/getInfoById/{id}") < paths.index(
            "/system/file/{bucket}/{file_name}"
        )

    def test_the_router_prefix_is_the_java_one(self) -> None:
        assert controller.router.prefix == "/system/file"

    def test_list_beats_the_path_variable_over_http(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.get("/system/file/list")

        assert response.json()["msg"] == "查询成功"
        assert service.of("select_sys_file_by_ids") == []

    def test_get_new_ca_beats_the_path_variable_over_http(
        self, http: TestClient, service: Any
    ) -> None:
        service.list_result = [_stored()]

        body = http.get("/system/file/getNewCa").json()

        assert body["data"]["fileName"] == "a.pdf"
        assert service.of("select_sys_file_by_ids") == []

    def test_get_info_by_id_beats_the_two_segment_variable(
        self, http: TestClient, service: Any
    ) -> None:
        service.by_id_result = _stored(9)

        body = http.get("/system/file/getInfoById/9").json()

        assert body["data"]["id"] == "9"   # @JsonSerialize(ToStringSerializer)
        assert service.of("get_file") == []


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    def test_list_requires_the_misspelled_permission(self) -> None:
        """权限点是 ``base:sysflie:list`` —— 改成 ``sysfile`` 会让文件列表 403。"""
        with pytest.raises(AccessDeniedException):
            list_files(SysFile())

    def test_the_misspelled_permission_passes_when_granted(self) -> None:
        authenticate(permissions={"base:sysflie:list"})

        list_files(SysFile())

    def test_the_correctly_spelled_permission_does_not(self) -> None:
        authenticate(permissions={"base:sysfile:list"})

        with pytest.raises(AccessDeniedException):
            list_files(SysFile())

    def test_the_batch_delete_requires_the_supplier_permission(self) -> None:
        with pytest.raises(AccessDeniedException):
            remove("1")

    def test_the_batch_delete_passes_with_it(self) -> None:
        authenticate(permissions={"base:supplier:remove"})

        remove("1")

    def test_the_single_delete_is_login_only(self) -> None:
        """``removeById`` 没有 ``@PreAuthorize``。"""
        authenticate(permissions=set())

        assert remove_by_id(7)["code"] == 200

    @pytest.mark.parametrize(
        "call",
        [
            lambda: get_info_by_id(7),
            lambda: get_new_ca(SysFile()),
            lambda: get_info("7"),
            lambda: upload([]),
            lambda: upload_by_url(UploadRo(list=[])),
            lambda: upload_supplier([], []),
            lambda: upload_pdf([]),
            lambda: upload_file_id(SysFile(id=7, files="data:image/png;base64,aGVsbG8=")),
            lambda: upload_file_enc([]),
            lambda: update_ca_file(SysFile(id=7)),
            lambda: edit(SysFile(id=7)),
        ],
    )
    def test_the_other_endpoints_are_login_only(self, call: Any) -> None:
        authenticate(permissions=set())

        call()

    def test_an_anonymous_list_is_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.get("/system/file/list")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_an_anonymous_download_is_not_403(self, http_anonymous: TestClient) -> None:
        """下载路由没有权限点 —— 未登录也能取（靠链接保密）。"""
        response = http_anonymous.get("/system/file/developer/a.pdf")

        assert response.status_code == 200
        assert response.content == b"payload"


# --------------------------------------------------------------------------- list


class TestList:
    def test_the_page_is_started_before_the_query(self, service: Any, http: TestClient) -> None:
        http.get("/system/file/list")

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1

    def test_the_camel_case_filters_are_bound(self, http: TestClient, service: Any) -> None:
        http.get("/system/file/list", params={"fileName": "a", "bussType": "b", "bussName": "c"})

        query = service.of("select_sys_file_list")[0][1]
        assert (query.file_name, query.buss_type, query.buss_name) == ("a", "b", "c")

    def test_an_unknown_parameter_is_ignored(self, http: TestClient) -> None:
        response = http.get("/system/file/list", params={"nope": "1"})

        assert response.status_code == 200

    def test_the_rows_are_wrapped_in_a_table_envelope(self, service: Any) -> None:
        authenticate()
        service.list_result = [_stored(7), _stored(8)]

        response = list_files(SysFile())

        assert response.get_total() == 2
        assert [row.id for row in response.get_rows()] == [7, 8]


# --------------------------------------------------------------------------- getInfo


class TestGetInfo:
    def test_a_single_trailing_comma_is_removed(self, service: Any) -> None:
        authenticate()

        get_info("1,2,")

        assert service.of("select_sys_file_by_ids") == [("select_sys_file_by_ids", "1,2")]

    def test_only_one_comma_is_removed(self, service: Any) -> None:
        authenticate()

        get_info("1,2,,")

        assert service.of("select_sys_file_by_ids") == [("select_sys_file_by_ids", "1,2,")]

    def test_a_blank_ids_becomes_the_magic_number(self, service: Any) -> None:
        authenticate()

        get_info(",")

        assert service.of("select_sys_file_by_ids") == [
            ("select_sys_file_by_ids", EMPTY_IDS_PLACEHOLDER)
        ]

    def test_the_magic_number_is_minus_111111(self) -> None:
        assert EMPTY_IDS_PLACEHOLDER == "-111111"

    def test_the_by_id_lookup_passes_an_int(self, service: Any) -> None:
        authenticate()

        get_info_by_id(9)

        assert service.of("select_sys_file_by_id") == [("select_sys_file_by_id", 9)]

    def test_a_missing_row_omits_data(self, http: TestClient) -> None:
        body = http.get("/system/file/getInfoById/9").json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_the_snowflake_id_is_serialized_as_a_string(self, http: TestClient, service: Any) -> None:
        service.by_id_result = SysFile(id=1234567890123456789, file_name="a.pdf")

        body = http.get("/system/file/getInfoById/9").json()

        assert body["data"]["id"] == "1234567890123456789"

    def test_a_non_numeric_path_id_is_code_500(self, http_lenient: TestClient) -> None:
        response = http_lenient.get("/system/file/getInfoById/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- getNewCa


class TestGetNewCa:
    def test_the_first_row_of_the_page_is_returned(self, service: Any) -> None:
        authenticate()
        service.list_result = [_stored(7), _stored(8)]

        response = get_new_ca(SysFile())

        assert response["data"].id == 7

    def test_the_page_is_started(self, service: Any, http: TestClient) -> None:
        http.get("/system/file/getNewCa")

        assert service.page_taken is not None

    def test_an_empty_list_returns_the_error_message(self, http: TestClient) -> None:
        body = http.get("/system/file/getNewCa").json()

        assert body == {"code": 500, "msg": CA_NOT_FOUND_MESSAGE}
        assert CA_NOT_FOUND_MESSAGE == "未找到CA驱动程序"


# --------------------------------------------------------------------------- 上传


class TestUpload:
    def test_the_files_are_forwarded(self, http: TestClient, service: Any) -> None:
        response = http.post("/system/file/upload", files=[_upload(), _upload("b.png")])

        assert response.json()["code"] == 200
        assert len(service.of("upload_files")[0][1]) == 2
        assert service.of("upload_files")[0][1][1].filename == "b.png"

    def test_a_missing_part_is_code_500(self, http_lenient: TestClient) -> None:
        response = http_lenient.post("/system/file/upload")

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_upload_by_url_reads_the_list_property(self, service: Any) -> None:
        authenticate()

        upload_by_url(UploadRo(list=[]))

        assert service.of("upload_by_url") == [("upload_by_url", [])]

    def test_upload_by_url_without_the_key_passes_none(self, service: Any) -> None:
        """Java: ``getList()`` 为 ``null`` -> 服务层 ``for`` 循环 NPE。"""
        authenticate()

        upload_by_url(UploadRo())

        assert service.of("upload_by_url") == [("upload_by_url", None)]

    def test_upload_supplier_keeps_the_form_field_order(self, http: TestClient, service: Any) -> None:
        response = http.post(
            "/system/file/uploadSupplier",
            files=[_upload()],
            data={"bussNames": "s1"},
        )

        assert response.status_code == 200
        _files, buss_names = service.of("upload_supplier")[0][1]
        assert buss_names == ["s1"]

    def test_upload_pdf_passes_no_response(self, service: Any) -> None:
        """Java 的 ``HttpServletResponse`` 一次都没被写过，控制器不传。"""
        authenticate()

        upload_pdf([])

        _files, response = service.of("upload_files_pdf")[0][1]
        assert response is None

    def test_upload_file_enc_forwards_the_files(self, http: TestClient, service: Any) -> None:
        http.post("/system/file/uploadFileEnc", files=[_upload()])

        assert len(service.of("upload_files_enc")[0][1]) == 1

    def test_upload_file_id_decodes_the_base64(self, http: TestClient, service: Any) -> None:
        response = http.post(
            "/system/file/uploadFileId",
            json={"id": 3001, "files": "data:image/png;base64,aGVsbG8="},
        )

        assert response.status_code == 200
        file_id, file = service.of("upload_file_id")[0][1]
        assert file_id == 3001
        assert file.get_bytes() == b"hello"

    def test_upload_file_id_without_an_id_still_proceeds(self, http: TestClient, service: Any) -> None:
        """``AjaxResult.error("主键不能为空")`` 的返回值被丢弃 —— 不 return、不 throw。"""
        response = http.post(
            "/system/file/uploadFileId",
            json={"files": "data:image/png;base64,aGVsbG8="},
        )

        assert response.status_code == 200
        assert service.of("upload_file_id") != []
        file_id, _file = service.of("upload_file_id")[0][1]
        assert file_id is None

    def test_upload_file_id_without_files_is_code_500(self, http_lenient: TestClient) -> None:
        """Java: ``base64Convert(null)`` -> ``null.split(",")`` NPE -> 200 + code 500。"""
        response = http_lenient.post("/system/file/uploadFileId", json={"id": 3001})

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 微信


class TestWechatUpload:
    def test_a_picture_is_forwarded(self, service: Any) -> None:
        authenticate()

        upload_wechat(SimpleNamespace(filename="a.jpg", size=10))

        assert len(service.of("upload_files")[0][1]) == 1

    @pytest.mark.parametrize("filename", ["a.jpg", "a.jpeg", "a.png", "a.gif", "a.xjpg"])
    def test_the_four_extensions_are_accepted_by_substring(
        self, service: Any, filename: str
    ) -> None:
        authenticate()

        upload_wechat(SimpleNamespace(filename=filename, size=1))

        assert service.of("upload_files") != []

    @pytest.mark.parametrize("filename", ["a.JPG", "a.pdf", "a.docx", "noext", "", "a."])
    def test_everything_else_is_rejected(self, service: Any, filename: str) -> None:
        """``ext.indexOf(...)`` **区分大小写**，也没有 ``toLowerCase()``。"""
        result = upload_wechat(SimpleNamespace(filename=filename, size=1))

        assert result == {"code": 500, "msg": NOT_PICTURE_MESSAGE}
        assert service.of("upload_files") == []

    def test_the_picture_message_is_the_java_one(self) -> None:
        assert NOT_PICTURE_MESSAGE == "上传失败,请上传照片格式的附件！"

    def test_a_file_over_fifteen_megabytes_is_rejected(self, service: Any) -> None:
        result = upload_wechat(
            SimpleNamespace(filename="a.jpg", size=15 * 1024 * 1024 + 1)
        )

        assert result == {"code": 500, "msg": FILE_TOO_LARGE_MESSAGE}
        assert service.of("upload_files") == []

    def test_exactly_fifteen_megabytes_is_allowed(self, service: Any) -> None:
        authenticate()

        upload_wechat(SimpleNamespace(filename="a.jpg", size=15 * 1024 * 1024))

        assert service.of("upload_files") != []

    def test_the_latin1_mangled_name_is_converted_back(self, service: Any) -> None:
        """multipart 解析器按 latin-1 读出中文名，``CharsetUtil.convert`` 还原。"""
        authenticate()
        mangled = "照片.jpg".encode("utf-8").decode("iso-8859-1")
        uploaded = SimpleNamespace(filename=mangled, size=1)

        upload_wechat(uploaded)

        # Java 把**同一个** MultipartFile 交给 service，转换只影响扩展名判断
        assert service.of("upload_files")[0][1] == [uploaded]

    def test_the_form_field_must_be_named_file(self, http_lenient: TestClient) -> None:
        response = http_lenient.post(
            "/system/file/uploadFile", files=[("other", ("a.jpg", b"x", "image/jpeg"))]
        )

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 下载


class TestDownload:
    def test_the_bytes_and_content_type_come_from_the_sink(
        self, http: TestClient
    ) -> None:
        response = http.get("/system/file/developer/a.pdf")

        assert response.status_code == 200
        assert response.content == b"payload"
        assert response.headers["content-type"] == "application/octet-stream; charset=UTF-8"

    def test_the_bucket_and_name_reach_the_service(
        self, http: TestClient, service: Any
    ) -> None:
        http.get("/system/file/developer/uuid.pdf")

        assert service.of("get_file") == [("get_file", ("developer", "uuid.pdf"))]

    def test_an_error_yields_200_and_an_empty_body(self, http: TestClient, service: Any) -> None:
        """``getFile`` 把异常全吞 —— 不是 404。"""
        service.file_bytes = b""
        service.file_content_type = None

        response = http.get("/system/file/developer/missing.pdf")

        assert response.status_code == 200
        assert response.content == b""
        assert "content-type" not in response.headers

    def test_the_view_route_is_the_same_implementation(self, http: TestClient, service: Any) -> None:
        response = http.get("/system/file/view/developer/a.pdf")

        assert response.content == b"payload"
        assert service.of("get_file") == [("get_file", ("developer", "a.pdf"))]

    def test_file_view_directly(self, service: Any) -> None:
        response = file_view("developer", "a.pdf")

        assert response.body == b"payload"


# --------------------------------------------------------------------------- 增删改


class TestWrite:
    def test_edit_forwards_the_entity(self, service: Any) -> None:
        authenticate()

        edit(SysFile(id=7, file_name="a.pdf"))

        assert service.of("save_sys_file")[0][1].id == 7

    def test_edit_has_no_validation(self, http: TestClient) -> None:
        response = http.put("/system/file", json={})

        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_update_ca_file_forwards_the_entity(self, service: Any) -> None:
        authenticate()

        update_ca_file(SysFile(id=7))

        assert service.of("update_ca_file")[0][1].id == 7

    def test_remove_by_id_passes_the_int(self, service: Any) -> None:
        authenticate()

        remove_by_id(7)

        assert service.of("delete_sys_file_by_id") == [("delete_sys_file_by_id", 7)]

    def test_remove_splits_the_comma_separated_ids(self, service: Any) -> None:
        authenticate()

        remove("1,2,3")

        assert service.of("delete_sys_file_by_ids") == [
            ("delete_sys_file_by_ids", [1, 2, 3])
        ]

    def test_a_zero_count_is_still_http_200(self, http: TestClient, service: Any) -> None:
        service.envelope = {"code": 200, "msg": "操作成功", "data": 0}

        body = http.delete("/system/file/1").json()

        assert body["code"] == 200
        assert body["data"] == 0

    def test_a_non_numeric_delete_id_is_code_500(self, http_lenient: TestClient) -> None:
        response = http_lenient.delete("/system/file/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500
