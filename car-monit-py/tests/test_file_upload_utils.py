"""``FileUploadUtils`` / ``MimeTypeUtils`` / ``Seq`` 的行为对齐测试.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-common/.../utils/file/FileUploadUtils.java
#   ruoyi-common/.../utils/file/MimeTypeUtils.java
#   ruoyi-common/.../utils/uuid/Seq.java
#   org.apache.commons.io.FilenameUtils (只搬了 getBaseName / getExtension)

这一层测什么
------------
三个工具类都没有依赖注入，所以直接调函数断言"输出长什么样"：

* ``Seq``：序列的**形状**（14 位时间 + 机器标识 + 3 位序号）与**循环边界**
  （1..999，+1 之后才判断重置 —— 写成"value >= max 就归零"会错一位）；
* ``MimeTypeUtils``：只认 5 种图片 ``Content-Type``，其余回空串；
* ``FileUploadUtils``：文件名拼装、``profile`` 前缀切片、大小/后缀/文件名长度三道校验，
  以及 2 参 ``upload`` 只把**真正的 I/O 故障**包成 ``OSError``（Java 的 ``IOException``），
  校验类错误（文件名/大小/后缀）保留为业务异常的事实。

时间与序列号都是"现在"，所以断言用正则或用 ``monkeypatch`` 把
``date_path`` / ``get_id`` 固定下来 —— 不去 mock 时钟，避免测到 mock 自己。
"""

from __future__ import annotations

import io
import os
import re
from typing import Any, Optional

import pytest
from starlette.datastructures import Headers, UploadFile

from app.common.exception.exceptions import ServiceException
from app.common.exception.file import (
    FileException,
    FileNameLengthLimitExceededException,
    FileSizeLimitExceededException,
    InvalidExtensionException,
    InvalidImageExtensionException,
)
from app.common.utils import file_upload_utils as fu
from app.common.utils import mime_type_utils as mime
from app.common.utils import seq
from app.settings import get_settings, reset_settings_cache

#: Java: ``messages.properties`` 里 ``upload.exceed.maxSize`` 的原文
SIZE_EXCEEDED_MESSAGE = "上传的文件大小超出限制的文件大小！<br/>允许的文件最大大小是：50MB！"
#: Java: ``messages.properties`` 里 ``upload.filename.exceed.length`` 的原文
NAME_LENGTH_MESSAGE = "上传的文件名最长100个字符"


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def _reset_seq() -> Any:
    """``Seq`` 的计数器是**进程级**的，用例之间必须归位，否则序号断言会互相干扰。"""
    seq.reset_seq()
    yield
    seq.reset_seq()


@pytest.fixture
def profile_dir(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> str:
    """把 ``ruoyi.profile`` 指到一个临时目录（等价于 Spring 里换 ``RuoYiConfig``）。"""
    target = (tmp_path / "uploadPath").as_posix()
    monkeypatch.setenv("RUOYI__PROFILE", target)
    reset_settings_cache()
    yield target
    monkeypatch.delenv("RUOYI__PROFILE", raising=False)
    reset_settings_cache()


def _upload_file(
    data: bytes = b"hello",
    filename: Optional[str] = "avatar.png",
    content_type: Optional[str] = "image/png",
    size: Optional[int] = None,
) -> UploadFile:
    """构造一个与 multipart 解析结果同形的 ``UploadFile``。"""
    headers = Headers({"content-type": content_type}) if content_type is not None else None
    return UploadFile(
        file=io.BytesIO(data),
        size=len(data) if size is None else size,
        filename=filename,
        headers=headers,
    )


# --------------------------------------------------------------------------- Seq


class TestSeq:
    """``Seq`` -- ``yyyyMMddHHmmss`` + ``"A"`` + 3 位循环序号。"""

    def test_the_shape_is_fourteen_digits_machine_code_and_three_digits(self) -> None:
        value = seq.get_id()

        # Java 注释写"16位 / yyMMddHHmmss"，但代码用的是 dateTimeNow() 的 14 位格式，
        # 总长 18。这里按代码断言（见模块 docstring）。
        assert re.fullmatch(r"\d{14}A\d{3}", value) is not None
        assert len(value) == 18

    def test_the_first_value_is_001(self) -> None:
        assert seq.get_id().endswith("A001")

    def test_the_counter_increments_per_call(self) -> None:
        endings = [seq.get_id()[-6:] for _ in range(3)]

        # A001 / A002 / A003 —— 序号部分是最后 3 位，机器标识是它前面那一位
        assert [ending[-3:] for ending in endings] == ["001", "002", "003"]

    def test_the_upload_counter_is_independent_from_the_common_one(self) -> None:
        assert seq.get_id(seq.UPLOAD_SEQ_TYPE).endswith("A001")
        # 通用序列没有被上传序列"蹭"掉一个号
        assert seq.get_id().endswith("A001")
        assert seq.get_id(seq.UPLOAD_SEQ_TYPE).endswith("A002")

    def test_the_sequence_wraps_after_nine_for_length_one(self) -> None:
        """``length = 1`` 时上界是 10：``+1 之后`` 才判断重置，所以只输出 1..9。"""
        values = [seq.get_id(length=1)[-1] for _ in range(10)]

        assert values == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "1"]

    def test_reset_puts_both_counters_back_to_one(self) -> None:
        seq.get_id()
        seq.get_id(seq.UPLOAD_SEQ_TYPE)

        seq.reset_seq()

        assert seq.get_id().endswith("A001")
        assert seq.get_id(seq.UPLOAD_SEQ_TYPE).endswith("A001")


# --------------------------------------------------------------------------- MimeType


class TestMimeTypeUtils:
    """``MimeTypeUtils`` -- 5 种图片类型 + 白名单常量。"""

    @pytest.mark.parametrize(
        ("content_type", "expected"),
        [
            ("image/png", "png"),
            ("image/jpg", "jpg"),
            ("image/jpeg", "jpeg"),
            ("image/bmp", "bmp"),
            ("image/gif", "gif"),
        ],
    )
    def test_the_five_image_prefixes(self, content_type: str, expected: str) -> None:
        assert mime.get_extension(content_type) == expected

    def test_an_unknown_prefix_yields_an_empty_string(self) -> None:
        # image/webp 不在 switch 里 -> ""，随后被后缀白名单拦下
        assert mime.get_extension("image/webp") == ""

    def test_the_default_whitelist_keeps_the_java_order(self) -> None:
        # 顺序会原样出现在 InvalidExtensionException 的文案里，所以顺序也是行为
        assert mime.DEFAULT_ALLOWED_EXTENSION[:5] == ("bmp", "gif", "jpg", "jpeg", "png")
        assert mime.DEFAULT_ALLOWED_EXTENSION[-1] == "pdf"
        assert len(mime.DEFAULT_ALLOWED_EXTENSION) == 22

    def test_the_image_extension_constant_is_the_identity_used_by_assert_allowed(self) -> None:
        # FileUploadUtils 用 ``==``（引用比较）区分四种专用异常，见下一个测试类
        assert mime.IMAGE_EXTENSION is mime.IMAGE_EXTENSION
        assert mime.IMAGE_EXTENSION == ("bmp", "gif", "jpg", "jpeg", "png")


# --------------------------------------------------------------------------- 后缀 / 文件名


class TestFilenameHelpers:
    """``FilenameUtils`` 的三个方法 + ``extractFilename`` / ``getPathFileName``。"""

    def test_the_extension_comes_from_the_original_filename(self) -> None:
        assert fu.get_extension(_upload_file(filename="a.PNG")) == "PNG"

    def test_the_extension_falls_back_to_the_content_type(self) -> None:
        # 没有后缀 -> Content-Type 反推
        assert fu.get_extension(_upload_file(filename="avatar", content_type="image/png")) == "png"

    def test_a_dot_inside_a_directory_name_is_not_an_extension(self) -> None:
        # a.b/c：点在目录上，Commons-IO 的 indexOfExtension 返回 -1
        assert fu.get_extension(_upload_file(filename="a.b/c", content_type="image/gif")) == "gif"

    def test_a_null_content_type_without_an_extension_raises(self) -> None:
        # Java: Objects.requireNonNull(file.getContentType()) -> NPE
        with pytest.raises(TypeError):
            fu.get_extension(_upload_file(filename="avatar", content_type=None))

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("a/b.png", "b"),
            ("a.b.png", "a.b"),
            (".bashrc", ""),
            ("plain", "plain"),
            ("dir/plain", "plain"),
        ],
    )
    def test_the_base_name_matches_commons_io(self, filename: str, expected: str) -> None:
        assert fu._get_base_name(filename) == expected

    def test_extract_filename_is_date_path_slash_base_name_underscore_seq(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(fu, "date_path", lambda: "2026/10/26")
        monkeypatch.setattr(fu, "get_id", lambda *_args, **_kwargs: "20261026120000A007")

        name = fu.extract_filename(_upload_file(filename="my.avatar.png"))

        # 原名只保留 baseName（my.avatar），后缀单独拼
        assert name == "2026/10/26/my.avatar_20261026120000A007.png"

    def test_get_path_file_name_strips_the_profile_prefix(self, profile_dir: str) -> None:
        upload_dir = get_settings().ruoyi.avatar_path

        url = fu.get_path_file_name(upload_dir, "2026/10/26/a.png")

        # profile 之前的盘符与目录全部切掉，换成 Constants.RESOURCE_PREFIX
        assert url == "/profile/avatar/2026/10/26/a.png"

    def test_get_path_file_name_truncates_a_directory_outside_the_profile(self) -> None:
        # 不在 profile 之下时"从头截错位置" —— Java 没有校验，这里也不加
        url = fu.get_path_file_name("D:/other/avatar", "a.png")

        assert url.startswith("/profile/")
        assert url.endswith("/a.png")


# --------------------------------------------------------------------------- 校验


class TestAssertAllowed:
    """``assertAllowed`` -- 大小 / 后缀两道闸。"""

    def test_a_file_over_fifty_megabytes_is_refused(self) -> None:
        too_big = _upload_file(size=fu.DEFAULT_MAX_SIZE + 1)

        with pytest.raises(FileSizeLimitExceededException) as raised:
            fu.assert_allowed(too_big, mime.DEFAULT_ALLOWED_EXTENSION)

        assert str(raised.value) == SIZE_EXCEEDED_MESSAGE

    def test_exactly_fifty_megabytes_is_allowed(self) -> None:
        at_limit = _upload_file(size=fu.DEFAULT_MAX_SIZE)

        fu.assert_allowed(at_limit, mime.DEFAULT_ALLOWED_EXTENSION)

    def test_a_disallowed_extension_lists_the_whole_whitelist(self) -> None:
        exe = _upload_file(filename="a.exe", content_type="application/x-msdownload")

        with pytest.raises(InvalidExtensionException) as raised:
            fu.assert_allowed(exe, mime.DEFAULT_ALLOWED_EXTENSION)

        assert str(raised.value) == (
            "文件[a.exe]后缀[exe]不正确，请上传"
            "[bmp, gif, jpg, jpeg, png, doc, docx, xls, xlsx, ppt, pptx, html, htm, txt, "
            "rar, zip, gz, bz2, mp4, avi, rmvb, pdf]格式"
        )

    def test_the_image_constant_raises_the_image_subtype(self) -> None:
        # Java: allowedExtension == MimeTypeUtils.IMAGE_EXTENSION（引用比较）
        svg = _upload_file(filename="a.svg", content_type="image/svg+xml")

        with pytest.raises(InvalidImageExtensionException):
            fu.assert_allowed(svg, mime.IMAGE_EXTENSION)

    def test_an_equal_but_distinct_tuple_raises_the_generic_type(self) -> None:
        """内容相同、对象不同 -> 走最后一个分支（Java 的 ``==`` 也是这个结果）。"""
        svg = _upload_file(filename="a.svg", content_type="image/svg+xml")

        with pytest.raises(InvalidExtensionException) as raised:
            fu.assert_allowed(svg, list(mime.IMAGE_EXTENSION))

        assert not isinstance(raised.value, InvalidImageExtensionException)
        assert str(raised.value) == "文件[a.svg]后缀[svg]不正确，请上传[bmp, gif, jpg, jpeg, png]格式"

    def test_the_extension_match_ignores_case(self) -> None:
        assert fu.is_allowed_extension("PNG", mime.DEFAULT_ALLOWED_EXTENSION) is True
        assert fu.is_allowed_extension("exe", mime.DEFAULT_ALLOWED_EXTENSION) is False

    def test_a_null_whitelist_skips_the_check(self) -> None:
        # Java: allowedExtension != null && ...
        fu.assert_allowed(_upload_file(filename="a.exe", content_type=None, data=b"x"), None)


# --------------------------------------------------------------------------- 落盘


class TestUpload:
    """``upload`` -- 文件名长度闸、目录创建、内容写入、异常包装。"""

    def test_it_writes_the_bytes_and_creates_the_date_directories(self, profile_dir: str) -> None:
        avatar_dir = get_settings().ruoyi.avatar_path

        url = fu.upload(avatar_dir, _upload_file(data=b"hello"))

        assert re.fullmatch(
            r"/profile/avatar/\d{4}/\d{2}/\d{2}/avatar_\d{14}A\d{3}\.png", url
        ) is not None
        written = avatar_dir + os.sep + url[len("/profile/avatar/") :]
        assert os.path.isfile(written)
        with open(written, "rb") as handle:
            assert handle.read() == b"hello"

    def test_a_name_longer_than_one_hundred_characters_is_refused(self, profile_dir: str) -> None:
        long_name = "a" * 101 + ".png"

        with pytest.raises(FileException) as raised:
            fu.upload(get_settings().ruoyi.avatar_path, _upload_file(filename=long_name))

        # P2-6 后续：校验类错误保留为业务异常，客户端仍能看到可操作的 i18n 文案。
        assert str(raised.value) == NAME_LENGTH_MESSAGE

    def test_the_three_argument_form_keeps_the_original_exception_type(
        self, profile_dir: str
    ) -> None:
        # 3 参重载不包装：Java 直接 throw FileNameLengthLimitExceededException
        with pytest.raises(FileNameLengthLimitExceededException):
            fu.upload_with_extensions(
                get_settings().ruoyi.avatar_path,
                _upload_file(filename="a" * 101 + ".png"),
                mime.DEFAULT_ALLOWED_EXTENSION,
            )

    def test_a_refused_extension_leaves_nothing_on_disk(self, profile_dir: str) -> None:
        avatar_dir = get_settings().ruoyi.avatar_path

        with pytest.raises(ServiceException):
            fu.upload(avatar_dir, _upload_file(filename="a.exe", content_type="application/zip"))

        # 校验在 extract/transfer 之前，所以连日期目录都不会被创建
        assert not os.path.exists(avatar_dir) or os.listdir(avatar_dir) == []

    def test_a_zero_byte_file_is_accepted_here(self, profile_dir: str) -> None:
        """``isEmpty()`` 是**控制器**的判断，工具类不看内容长度。"""
        url = fu.upload(get_settings().ruoyi.avatar_path, _upload_file(data=b""))

        assert url.endswith(".png")

    def test_the_default_base_dir_follows_the_profile_until_it_is_overridden(
        self, profile_dir: str
    ) -> None:
        assert fu.get_default_base_dir() == profile_dir

        fu.set_default_base_dir("/tmp/fixed")
        try:
            assert fu.get_default_base_dir() == "/tmp/fixed"
        finally:
            fu.reset_default_base_dir()

        assert fu.get_default_base_dir() == profile_dir
