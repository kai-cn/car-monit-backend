"""``SysFileService`` -- 上传 / 下载 / 登记的全部约定.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java
#   ruoyi-system/src/main/java/com/ruoyi/system/service/ISysFileService.java

本模块测什么
------------
不连数据库、不连 OSS：注入假 mapper / 假 OSS 客户端 / 假 Forest，只锁 **Java 的行为**：

1. ``uploadFile`` **先** putObject **再** 登记；``uploadFiles`` / ``uploadSupplier`` /
   ``uploadByUrl`` / ``uploadFileId`` 反过来或另有讲究（见各自用例）；
2. 扩展名白名单走 ``indexOf > -1`` 的**子串**匹配，且先 ``toLowerCase()``；
3. ``uploadFiles`` 在 ``fileLog`` 返回 ``-1`` 时**跳过**上传，但结果里仍保留该条；
4. ``uploadFilesUser`` 不写 ``del_flag``（绕过 ``saveSysFile``）；
5. ``uploadSupplier`` 没有长度校验 —— ``bussNames`` 短了直接越界；
6. ``uploadFilesPdf`` 的非 pdf 分支只往本地写文件，结果里**没有** ``id``；
7. ``uploadFilesEnc`` / ``getFileUrl`` / ``uploadBase64Picture(richText)`` /
   ``uploadFile(InputStream, SysFile)`` 的方法体**都被注释**，返回值是死的；
8. ``uploadBase64Picture`` 走的是 ``AjaxResult.success(String)`` -> 值落在 **msg**；
9. ``getFile`` 把异常**全吞**（客户端拿到空 body + 200）；
10. ``updateCAFile`` 先物理删 3001，再把主键改成 3001，返回**原** id。

``_message_of`` 与 Java 的差异
------------------------------
``catch (Exception e) { return error(e.getMessage()); }`` 在 Java 里 NPE 的
``getMessage()`` 是 ``null``；Python 的 ``AttributeError`` 有文案，所以 ``msg`` 变成
``"'NoneType' object has no attribute 'file_name'"``。两者 ``code`` 都是 500，前端只看
``code``，文案差异在 ``COMPATIBILITY.md`` 里登记。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.multipart_file_util import MockMultipartFile
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.system.domain.ro.upload_by_url_ro import UploadByUrlRo
from app.system.domain.sys_file import SysFile
from app.system.service import sys_file_service as svc_module
from app.system.service.sys_file_service import (
    FILE_URL_TEMPLATE,
    ResponseSink,
    SysFileService,
)

BUCKET = "developer"


# --------------------------------------------------------------------------- fakes


class _FakeFileMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_id: Optional[SysFile] = None
        self.by_ids: List[SysFile] = []
        self.list_result: List[SysFile] = []
        self.inserted: List[SysFile] = []
        self.updated: List[SysFile] = []
        self.deleted_by_id: List[Any] = []
        self.deleted_by_ids: List[Sequence[Any]] = []
        self.hard_deleted: List[Any] = []
        self.ca_updated: List[SysFile] = []

    def select_sys_file_by_ids(self, ids: Sequence[Any]) -> List[SysFile]:
        self.calls.append(("select_sys_file_by_ids", list(ids)))
        return self.by_ids

    def select_sys_file_by_id(self, id: Any) -> Optional[SysFile]:
        self.calls.append(("select_sys_file_by_id", id))
        return self.by_id

    def select_sys_file_list(self, entity: SysFile) -> List[SysFile]:
        self.calls.append(("select_sys_file_list", entity.model_copy(deep=True)))
        return self.list_result

    def insert_sys_file(self, entity: SysFile) -> int:
        self.calls.append(("insert_sys_file", entity))
        self.inserted.append(entity)
        return 1

    def update_sys_file(self, entity: SysFile) -> int:
        self.calls.append(("update_sys_file", entity))
        self.updated.append(entity)
        return 1

    def delete_sys_file_by_id(self, id: Any) -> int:
        self.calls.append(("delete_sys_file_by_id", id))
        self.deleted_by_id.append(id)
        return 1

    def delete_sys_file_by_ids(self, ids: Sequence[Any]) -> int:
        self.calls.append(("delete_sys_file_by_ids", list(ids)))
        self.deleted_by_ids.append(list(ids))
        return len(ids)

    def delete_sys_file_by_id_new(self, id: Any) -> int:
        self.calls.append(("delete_sys_file_by_id_new", id))
        self.hard_deleted.append(id)
        return 1

    def update_ca_file(self, entity: SysFile) -> int:
        self.calls.append(("update_ca_file", entity))
        self.ca_updated.append(entity)
        return 1

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _OssRecorder:
    """记录静态调用 ``OssTemplate.putObject`` / ``removeObject``。"""

    def __init__(self) -> None:
        self.put: List[tuple] = []
        self.removed: List[tuple] = []
        self.fail_put: Optional[BaseException] = None
        self.fail_remove: Optional[BaseException] = None

    def put_object(
        self, bucket_name: str, object_name: str, stream: Any,
        size: Any = None, content_type: Any = None,
    ) -> Any:
        if self.fail_put is not None:
            raise self.fail_put
        payload = stream.read() if hasattr(stream, "read") else stream
        self.put.append((bucket_name, object_name, payload))

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        if self.fail_remove is not None:
            raise self.fail_remove
        self.removed.append((bucket_name, object_name))


class _S3ObjectStub:
    def __init__(self, content: bytes) -> None:
        self._content = content
        self.closed = False

    def get_object_content(self) -> Any:
        from io import BytesIO

        return BytesIO(self._content)

    def close(self) -> None:
        self.closed = True


class _FakeOssTemplate:
    """替身：只实现 service 用到的 ``get_object`` / ``get_object_info``。"""

    def __init__(self) -> None:
        self.objects: Dict[tuple, bytes] = {}
        self.info_calls: List[tuple] = []
        self.fail_get: Optional[BaseException] = None

    def get_object(self, bucket_name: str, object_name: str) -> _S3ObjectStub:
        if self.fail_get is not None:
            raise self.fail_get
        return _S3ObjectStub(self.objects[(bucket_name, object_name)])

    def get_object_info(self, bucket_name: str, object_name: str) -> _S3ObjectStub:
        self.info_calls.append((bucket_name, object_name))
        if self.fail_get is not None:
            raise self.fail_get
        return _S3ObjectStub(self.objects[(bucket_name, object_name)])


class _FakeFileApi:
    def __init__(self) -> None:
        self.downloads: List[str] = []
        self.payload = b"\xff\xd8image"
        self.fail: Optional[BaseException] = None

    def download_image_to_byte_array(self, url: str) -> bytes:
        self.downloads.append(url)
        if self.fail is not None:
            raise self.fail
        return self.payload


class _FakeIdWorker:
    def __init__(self, start: int = 1000) -> None:
        self.value = start
        self.calls = 0

    def next_id(self) -> int:
        self.calls += 1
        self.value += 1
        return self.value


def authenticate(user_id: int = 2) -> SysUser:
    user = SysUser(user_id=user_id, user_name="ry")
    login_user = LoginUser(user=user, permissions={"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Any:
    """把 OSS / 设置 / 雪花 / uuid 全部钉住，让断言可以写死。

    默认**已登录**：本类里除了 ``upload_files`` 的“被拒扩展名”分支，几乎所有路径都会
    走到 ``saveSysFile`` 里的 ``SecurityUtils.getUserId()``。
    """
    SecurityContextHolder.clear_context()
    authenticate()
    oss = _OssRecorder()
    monkeypatch.setattr(svc_module.OssTemplate, "put_object", staticmethod(oss.put_object))
    monkeypatch.setattr(svc_module.OssTemplate, "remove_object", staticmethod(oss.remove_object))

    settings = SimpleNamespace(
        oss=SimpleNamespace(bucket_name=BUCKET),
        ruoyi=SimpleNamespace(upload_path=str(tmp_path / "upload")),
    )
    monkeypatch.setattr(svc_module, "get_settings", lambda: settings)
    monkeypatch.setattr(svc_module, "simple_uuid", lambda: "uuid-fixed")

    id_worker = _FakeIdWorker()
    monkeypatch.setattr(svc_module, "get_id_worker", lambda: id_worker)

    yield SimpleNamespace(
        oss=oss,
        settings=settings,
        id_worker=id_worker,
        tmp_path=tmp_path,
        upload_path=tmp_path / "upload",
    )
    SecurityContextHolder.clear_context()


def _service(
    mapper: Optional[_FakeFileMapper] = None,
    oss_template: Any = None,
    file_api: Any = None,
) -> SysFileService:
    return SysFileService(
        file_mapper=mapper or _FakeFileMapper(),
        oss_template=oss_template or _FakeOssTemplate(),
        file_api=file_api,
    )


def _file(filename: str = "a.pdf", content: bytes = b"hello") -> MockMultipartFile:
    return MockMultipartFile("file", filename, "application/pdf", content)


def _stored(file_id: int = 7, file_name: str = "a.pdf") -> SysFile:
    return SysFile(id=file_id, file_name=file_name, bucket_name=BUCKET, type="pdf")


# --------------------------------------------------------------------------- 查询


class TestQueries:
    def test_the_ids_are_split_on_comma_without_trimming(self) -> None:
        """``ids.split(",")`` —— **不 trim**、不过滤空串。"""
        mapper = _FakeFileMapper()

        _service(mapper).select_sys_file_by_ids("1,,2")

        assert mapper.of("select_sys_file_by_ids") == [
            ("select_sys_file_by_ids", ["1", "", "2"])
        ]

    def test_a_numeric_argument_is_stringified_first(self) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).select_sys_file_by_ids(3001)

        assert mapper.of("select_sys_file_by_ids") == [
            ("select_sys_file_by_ids", ["3001"])
        ]

    def test_the_by_id_lookup_is_passed_through(self) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()

        assert _service(mapper).select_sys_file_by_id(7).id == 7

    def test_the_list_query_is_passed_through(self) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).select_sys_file_list(SysFile(file_name="a"))

        assert mapper.of("select_sys_file_list")[0][1].file_name == "a"


# --------------------------------------------------------------------------- save


class TestSave:
    def test_an_id_means_update(self, env: Any) -> None:
        authenticate(user_id=2)
        mapper = _FakeFileMapper()

        _service(mapper).save_sys_file(SysFile(id=7, file_name="a.pdf"))

        assert mapper.of("update_sys_file")
        assert mapper.inserted == []

    def test_the_update_stamps_the_audit_columns_as_strings(self, env: Any) -> None:
        authenticate(user_id=2)
        mapper = _FakeFileMapper()

        _service(mapper).save_sys_file(SysFile(id=7))

        stored = mapper.updated[0]
        assert stored.update_user == "2"
        assert stored.update_time is not None
        assert stored.create_user is None

    def test_no_id_means_insert_with_a_snowflake_id(self, env: Any) -> None:
        authenticate(user_id=2)
        mapper = _FakeFileMapper()

        result = _service(mapper).save_sys_file(SysFile(file_name="a.pdf"))

        stored = mapper.inserted[0]
        assert stored.id == env.id_worker.value
        assert stored.del_flag == "0"
        assert (stored.create_user, stored.update_user) == ("2", "2")
        assert result == {"code": 200, "msg": "操作成功！", "data": stored.id}

    def test_the_success_message_keeps_the_full_width_bang(self, env: Any) -> None:
        authenticate()

        result = _service().save_sys_file(SysFile(file_name="a.pdf"))

        assert result["msg"] == "操作成功！"

    def test_an_unauthenticated_call_raises(self, env: Any) -> None:
        """Java: ``SecurityUtils.getUserId()`` -> ``CustomException("获取用户账户异常")``。"""
        SecurityContextHolder.clear_context()

        with pytest.raises(Exception):  # noqa: B017 - CustomException
            _service().save_sys_file(SysFile(id=7))


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_the_object_is_removed_before_the_soft_delete(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()

        result = _service(mapper).delete_sys_file_by_id(7)

        assert env.oss.removed == [(BUCKET, "a.pdf")]
        assert mapper.deleted_by_id == [7]
        assert result == {"code": 200, "msg": "操作成功", "data": 1}

    def test_the_batch_removes_every_object_then_deletes_once(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()

        result = _service(mapper).delete_sys_file_by_ids([1, 2])

        assert len(env.oss.removed) == 2
        assert mapper.deleted_by_ids == [[1, 2]]
        assert result["code"] == 200

    def test_a_zero_count_is_still_success(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()

        def _zero(ids: Sequence[Any]) -> int:
            return 0

        mapper.delete_sys_file_by_ids = _zero  # type: ignore[assignment]

        assert _service(mapper).delete_sys_file_by_ids([1])["code"] == 200

    def test_an_oss_failure_becomes_an_error_envelope(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()
        env.oss.fail_remove = RuntimeError("oss down")

        result = _service(mapper).delete_sys_file_by_id(7)

        assert result == {"code": 500, "msg": "oss down"}
        assert mapper.deleted_by_id == []

    def test_a_missing_row_fails_with_code_500(self, env: Any) -> None:
        """Java NPE -> ``error(null)``；Python 的 ``AttributeError`` 有文案，code 相同。"""
        mapper = _FakeFileMapper()
        mapper.by_id = None

        result = _service(mapper).delete_sys_file_by_id(7)

        assert result["code"] == 500
        assert mapper.deleted_by_id == []


# --------------------------------------------------------------------------- 名单


class TestWhitelist:
    @pytest.mark.parametrize(
        "filename",
        [
            "a.doc", "a.docx", "a.pdf", "a.xls", "a.xlsx", "a.pptx", "a.txt",
            "a.zip", "a.rar", "a.jpg", "a.jpeg", "a.png", "a.gif", "a.mp3",
            "a.mp4", "a.flv", "a.3gp",
        ],
    )
    def test_the_seventeen_extensions_are_accepted(
        self, env: Any, filename: str
    ) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).upload_files([_file(filename)])

        assert mapper.inserted, filename
        assert mapper.inserted[0].type == filename.rsplit(".", 1)[1]

    def test_the_extension_is_lower_cased_first(self, env: Any) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).upload_files([_file("A.PDF")])

        assert mapper.inserted[0].type == "pdf"

    def test_the_match_is_a_substring_not_an_equality(self, env: Any) -> None:
        """``ext.indexOf("pdf") > -1`` —— ``pdfdoc`` 也算命中。"""
        mapper = _FakeFileMapper()

        _service(mapper).upload_files([_file("a.pdfdoc")])

        assert mapper.inserted[0].type == "pdfdoc"

    @pytest.mark.parametrize("filename", ["a.exe", "a.ppt", "a", "a.", ""])
    def test_everything_else_is_rejected(self, env: Any, filename: str) -> None:
        """``ppt`` 不在名单里（只有 ``pptx``），``.ppt`` 那条死条目也救不了它。"""
        mapper = _FakeFileMapper()

        result = _service(mapper).upload_files([_file(filename)])

        assert mapper.inserted == []
        assert result["data"][0]["id"] == "-1"

    def test_a_rejected_file_is_still_reported(self, env: Any) -> None:
        result = _service().upload_files([_file("a.exe")])

        assert result["code"] == 200
        assert len(result["data"]) == 1
        assert env.oss.put == []


# --------------------------------------------------------------------------- uploadFile


class TestUploadFile:
    def test_the_object_is_put_before_the_row_is_written(self, env: Any) -> None:
        """与 ``uploadFiles`` **相反**：先 putObject，再 ``fileLog``。"""
        mapper = _FakeFileMapper()
        order: List[str] = []

        def _put(*_args: Any, **_kwargs: Any) -> None:
            order.append("put")

        mapper.insert_sys_file = lambda entity: order.append("insert") or 1  # type: ignore[assignment]
        env.oss.put_object = _put
        svc_module.OssTemplate.put_object = staticmethod(_put)  # type: ignore[assignment]
        try:
            _service(mapper).upload_file(_file())
        finally:
            pass

        assert order == ["put", "insert"]

    def test_the_result_map_has_the_four_keys(self, env: Any) -> None:
        result = _service().upload_file(_file("a.pdf"))

        row = result["data"]
        assert set(row) == {"bucketName", "fileName", "url", "id"}
        assert row["bucketName"] == BUCKET
        assert row["fileName"] == "uuid-fixed.pdf"
        assert row["url"] == FILE_URL_TEMPLATE.format(BUCKET, "uuid-fixed.pdf")

    def test_the_id_is_a_string(self, env: Any) -> None:
        result = _service().upload_file(_file())

        assert isinstance(result["data"]["id"], str)

    def test_a_put_failure_becomes_an_error(self, env: Any) -> None:
        env.oss.fail_put = RuntimeError("oss down")

        result = _service().upload_file(_file())

        assert result == {"code": 500, "msg": "oss down"}

    def test_an_empty_extension_leaves_a_trailing_dot(self, env: Any) -> None:
        """``extName("noext")`` 回 ``""``（不是 ``null``）—— 结果是 ``"uuid-fixed."``。"""
        result = _service().upload_file(_file("noext"))

        assert result["data"]["fileName"] == "uuid-fixed."

    def test_a_null_filename_becomes_the_literal_null(self, env: Any) -> None:
        """``simpleUUID + "." + getType()`` —— ``null`` 拼成字面量 ``"null"``。"""
        result = _service().upload_file(_file(None))

        assert result["data"]["fileName"] == "uuid-fixed.null"
        assert result["data"]["id"] == "-1"


# --------------------------------------------------------------------------- uploadFiles


class TestUploadFiles:
    def test_the_row_is_written_before_the_put(self, env: Any) -> None:
        order: List[str] = []
        mapper = _FakeFileMapper()

        def _insert(entity: SysFile) -> int:
            order.append("insert")
            return 1

        def _put(*_args: Any, **_kwargs: Any) -> None:
            order.append("put")

        mapper.insert_sys_file = _insert  # type: ignore[assignment]
        svc_module.OssTemplate.put_object = staticmethod(_put)  # type: ignore[assignment]

        _service(mapper).upload_files([_file()])

        assert order == ["insert", "put"]

    def test_a_rejected_file_skips_the_put(self, env: Any) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).upload_files([_file("a.exe")])

        assert env.oss.put == []

    def test_several_files_produce_several_rows(self, env: Any) -> None:
        result = _service().upload_files([_file("a.pdf"), _file("b.png")])

        assert len(result["data"]) == 2
        assert [row["fileName"] for row in result["data"]] == [
            "uuid-fixed.pdf",
            "uuid-fixed.png",
        ]

    def test_an_empty_array_is_an_empty_data_array(self, env: Any) -> None:
        result = _service().upload_files([])

        assert result["data"] == []


# --------------------------------------------------------------------------- uploadByUrl


class TestUploadByUrl:
    def test_a_missing_file_name_becomes_dot_jpg(self, env: Any) -> None:
        """``ro.setFileName(CommonUtil.isNull(ro.getFileName()) + ".jpg")``。"""
        file_api = _FakeFileApi()
        env_oss_put: List[tuple] = []
        svc_module.OssTemplate.put_object = staticmethod(
            lambda bucket, name, stream, *a: env_oss_put.append((bucket, name))
        )

        result = _service(file_api=file_api).upload_by_url([UploadByUrlRo(url="http://x/1")])

        assert file_api.downloads == ["http://x/1"]
        assert result["data"][0]["fileName"] == "uuid-fixed.jpg"

    def test_an_explicit_file_name_is_overwritten_by_dot_jpg(self, env: Any) -> None:
        file_api = _FakeFileApi()
        svc_module.OssTemplate.put_object = staticmethod(lambda *a, **k: None)

        result = _service(file_api=file_api).upload_by_url(
            [UploadByUrlRo(url="http://x/1", file_name="named")]
        )

        assert result["data"][0]["fileName"] == "uuid-fixed.jpg"

    def test_a_blank_url_is_skipped(self, env: Any) -> None:
        file_api = _FakeFileApi()

        result = _service(file_api=file_api).upload_by_url([UploadByUrlRo(url="")])

        assert file_api.downloads == []
        assert result["data"] == []

    def test_a_failing_download_does_not_abort_the_batch(self, env: Any) -> None:
        file_api = _FakeFileApi()
        file_api.fail = RuntimeError("network")
        svc_module.OssTemplate.put_object = staticmethod(lambda *a, **k: None)

        result = _service(file_api=file_api).upload_by_url(
            [UploadByUrlRo(url="http://x/1"), UploadByUrlRo(url="http://x/2")]
        )

        assert result["code"] == 200
        assert result["data"] == []


# --------------------------------------------------------------------------- uploadSupplier


class TestUploadSupplier:
    def test_buss_names_are_matched_by_position(self, env: Any) -> None:
        mapper = _FakeFileMapper()

        _service(mapper).upload_supplier([_file("a.pdf"), _file("b.pdf")], ["s1", "s2"])

        assert [row.buss_name for row in mapper.inserted] == ["s1", "s2"]

    def test_a_short_buss_names_array_raises(self, env: Any) -> None:
        """Java ``AIOOBE`` / Python ``IndexError`` -> HTTP 200 + code 500。"""
        with pytest.raises(IndexError):
            _service().upload_supplier([_file()], [])


# --------------------------------------------------------------------------- uploadFilesUser


class TestUploadFilesUser:
    def test_del_flag_is_not_written(self, env: Any) -> None:
        """绕过 ``saveSysFile`` —— 插入的行 ``del_flag`` 为 NULL，列表里查不到。"""
        mapper = _FakeFileMapper()

        _service(mapper).upload_files_user([_file()], "42")

        stored = mapper.inserted[0]
        assert stored.del_flag is None
        assert stored.create_user == "42"
        assert stored.id is not None

    def test_the_named_user_wins_over_the_login(self, env: Any) -> None:
        authenticate(user_id=2)
        mapper = _FakeFileMapper()

        _service(mapper).upload_files_user([_file()], "42")

        assert mapper.inserted[0].create_user == "42"


# --------------------------------------------------------------------------- uploadFileId


class TestUploadFileId:
    def test_the_old_row_is_hard_deleted_first(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored(3001, "old.pdf")

        _service(mapper).upload_file_id(3001, _file())

        assert mapper.hard_deleted == [3001]
        assert env.oss.removed == [(BUCKET, "old.pdf")]
        assert mapper.inserted[0].id == 3001

    def test_the_explicit_id_is_kept_in_the_result(self, env: Any) -> None:
        result = _service().upload_file_id(3001, _file())

        assert result["data"][0]["id"] == "3001"

    def test_none_still_reaches_the_deletion(self, env: Any) -> None:
        """``uploadFileId`` 控制器把 ``error()`` 丢了，所以 ``id == null`` 也会走到这里。"""
        mapper = _FakeFileMapper()

        result = _service(mapper).upload_file_id(None, _file())

        assert mapper.inserted[0].id is None
        assert result["data"][0]["id"] == "null"


# --------------------------------------------------------------------------- uploadPdf


class TestUploadPdf:
    def test_a_pdf_is_uploaded(self, env: Any) -> None:
        result = _service().upload_files_pdf([_file("a.pdf")])

        assert result["data"][0]["id"]
        assert env.oss.put[0][1] == "uuid-fixed.pdf"

    def test_a_non_pdf_only_lands_on_disk(self, env: Any) -> None:
        result = _service().upload_files_pdf([_file("a.docx")])

        written = list(env.upload_path.glob("*/*"))
        assert [path.name for path in written] == ["uuid-fixed.docx"]
        assert written[0].read_bytes() == b"hello"
        assert "id" not in result["data"][0]
        assert env.oss.put == []

    def test_the_response_sink_is_never_written(self, env: Any) -> None:
        sink = ResponseSink()

        _service().upload_files_pdf([_file("a.docx")], sink)

        assert sink.body == b""
        assert sink.content_type is None


# --------------------------------------------------------------------------- 死代码


class TestDeadCode:
    def test_upload_files_enc_always_returns_an_empty_array(self, env: Any) -> None:
        result = _service().upload_files_enc([_file()])

        assert result == {"code": 200, "msg": "操作成功", "data": []}

    def test_get_file_url_always_returns_none(self, env: Any) -> None:
        assert _service().get_file_url(7) is None

    def test_the_rich_text_overload_returns_the_input_when_blank(self, env: Any) -> None:
        service = _service()

        assert service.upload_base64_picture_rich_text(None) is None
        assert service.upload_base64_picture_rich_text("") == ""
        assert service.upload_base64_picture_rich_text("   ") == "   "

    def test_the_rich_text_overload_drops_everything_else(self, env: Any) -> None:
        assert _service().upload_base64_picture_rich_text("<p>hi</p>") == ""

    def test_upload_file_from_stream_only_mints_an_id(self, env: Any) -> None:
        from io import BytesIO

        mapper = _FakeFileMapper()

        file_id = _service(mapper).upload_file_from_stream(BytesIO(b"x"), SysFile())

        assert file_id == env.id_worker.value
        assert mapper.calls == []
        assert env.oss.put == []


# --------------------------------------------------------------------------- 读取


class TestRead:
    def test_get_file_copies_the_bytes_and_sets_the_content_type(self, env: Any) -> None:
        template = _FakeOssTemplate()
        template.objects[(BUCKET, "a.pdf")] = b"payload"
        sink = ResponseSink()

        _service(oss_template=template).get_file(BUCKET, "a.pdf", sink)

        assert sink.body == b"payload"
        assert sink.content_type == "application/octet-stream; charset=UTF-8"

    def test_get_file_swallows_every_error(self, env: Any) -> None:
        """客户端拿到 HTTP 200 + 空 body（不是 404）。"""
        template = _FakeOssTemplate()
        template.fail_get = RuntimeError("missing")
        sink = ResponseSink()

        _service(oss_template=template).get_file(BUCKET, "a.pdf", sink)

        assert sink.body == b""
        assert sink.content_type is None

    def test_get_file_to_output_stream_does_not_set_a_content_type(self, env: Any) -> None:
        from io import BytesIO

        template = _FakeOssTemplate()
        template.objects[(BUCKET, "a.pdf")] = b"payload"
        buffer = BytesIO()

        _service(oss_template=template).get_file_to_output_stream(BUCKET, "a.pdf", buffer)

        assert buffer.getvalue() == b"payload"

    def test_get_file_to_url_writes_a_local_file(self, env: Any) -> None:
        template = _FakeOssTemplate()
        template.objects[(BUCKET, "a.pdf")] = b"payload"
        target = env.tmp_path / "download"
        target.mkdir()

        _service(oss_template=template).get_file_to_url(BUCKET, "a.pdf", str(target))

        assert (target / "a.pdf").read_bytes() == b"payload"

    def test_get_file_object_uses_the_stored_bucket_and_name(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()
        template = _FakeOssTemplate()
        template.objects[(BUCKET, "a.pdf")] = b"payload"

        obj = _service(mapper, template).get_file_object(7)

        assert obj is not None
        assert template.info_calls == [(BUCKET, "a.pdf")]

    def test_get_file_object_is_none_when_the_row_is_missing(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = None

        assert _service(mapper).get_file_object(7) is None

    def test_get_byte_object_returns_the_bytes(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()
        template = _FakeOssTemplate()
        template.objects[(BUCKET, "a.pdf")] = b"payload"

        assert _service(mapper, template).get_byte_object(7) == b"payload"

    def test_get_byte_object_is_none_on_an_oss_error(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored()
        template = _FakeOssTemplate()
        template.fail_get = RuntimeError("boom")

        assert _service(mapper, template).get_byte_object(7) is None


# --------------------------------------------------------------------------- CA


class TestCa:
    def test_update_ca_file_hard_deletes_3001_first(self, env: Any) -> None:
        mapper = _FakeFileMapper()
        mapper.by_id = _stored(3001, "old.pdf")

        _service(mapper).update_ca_file(SysFile(id=7))

        assert mapper.hard_deleted == [3001]
        assert mapper.ca_updated[0].id == 7

    def test_update_ca_file_returns_the_original_id(self, env: Any) -> None:
        authenticate()

        result = _service().update_ca_file(SysFile(id=7))

        assert result == {"code": 200, "msg": "操作成功！", "data": 7}

    def test_the_audit_columns_are_stamped_before_the_delete(self, env: Any) -> None:
        authenticate(user_id=2)
        mapper = _FakeFileMapper()
        entity = SysFile(id=7)

        _service(mapper).update_ca_file(entity)

        assert entity.update_user == "2"
        assert entity.update_time is not None


# --------------------------------------------------------------------------- base64


class TestBase64Picture:
    def test_a_valid_picture_is_stored_and_uploaded(self, env: Any) -> None:
        result = _service().upload_base64_picture("aGVsbG8=", SysFile(type="png"))

        assert env.oss.put[0][1] == "uuid-fixed.png"
        assert result["code"] == 200

    def test_the_file_id_lands_in_msg_not_in_data(self, env: Any) -> None:
        """``AjaxResult.success(String)`` 重载 —— 只有 ``code`` / ``msg``。"""
        result = _service().upload_base64_picture("aGVsbG8=", SysFile(type="png"))

        assert "data" not in result
        assert result["msg"] != "操作成功"

    def test_a_malformed_base64_falls_into_the_error_branch(self, env: Any) -> None:
        """``Base64.decode`` 返回 ``null`` -> ``ByteArrayInputStream(null)`` NPE。"""
        result = _service().upload_base64_picture("!!!", SysFile(type="png"))

        assert result == {"code": 500, "msg": "操作失败"}

    def test_the_entity_file_name_comes_from_the_type(self, env: Any) -> None:
        entity = SysFile(type="jpg")

        _service().upload_base64_picture("aGVsbG8=", entity)

        assert entity.file_name == "uuid-fixed.jpg"

    def test_a_null_type_yields_the_literal_null_suffix(self, env: Any) -> None:
        entity = SysFile()

        _service().upload_base64_picture("aGVsbG8=", entity)

        assert entity.file_name == "uuid-fixed.null"
