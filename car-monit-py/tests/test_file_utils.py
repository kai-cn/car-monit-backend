"""``FileUtils`` / ``FileTypeUtils`` -- 文件工具类.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-common/.../utils/file/FileUtils.java
#   ruoyi-common/.../utils/file/FileTypeUtils.java

这一层测什么
------------
纯函数，没有协作者，所以直接调。重点在**判据的不对称**：

* ``get_file_type`` 会 ``toLowerCase()`` —— 所以下载白名单**不区分大小写**；
* ``MimeTypeUtils.get_extension``（上传那半边）**区分**大小写 —— 两处不能互相参照；
* ``FileTypeUtils.get_file_extend_name`` 返回**大写**，``FileUtils.get_file_extend_name``
  返回**小写**，实现逐字相同；
* ``write_bytes`` 在 ``finally`` 里关流 —— 文件不存在时**流也已经关了**，
  这是 ``/common/download`` 回 200 空 body 的根因；
* ``percent_encode`` 用的是 ``URLEncoder`` 的安全字符集（``.-*_``），
  与 :func:`urllib.parse.quote` 的 ``_.-~`` **不同**（``~`` 与 ``*`` 会差）。
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import pytest

from app.common.utils import file_type_utils
from app.common.utils import file_utils
from app.settings import reset_settings_cache
from app.system.service.sys_file_service import ResponseSink

#: GIF87a / GIF89a 头
GIF_BYTES = b"GIF89a" + b"\x00" * 10
#: JFIF：下标 6..9 是 'J','F','I','F'
JPG_BYTES = b"\x00\x00\x00\x00\x00\x00JFIF" + b"\x00" * 10
#: BMP
BMP_BYTES = b"BM" + b"\x00" * 12
#: PNG：下标 1..3 是 'P','N','G'
PNG_BYTES = b"\x00PNG" + b"\x00" * 10


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def profile(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """把 ``ruoyi.profile`` 指到临时目录 —— ``write_bytes_to_dir`` 会真的落盘."""
    value = str(tmp_path / "uploadPath")
    monkeypatch.setenv("RUOYI__PROFILE", value)
    reset_settings_cache()
    yield value
    reset_settings_cache()


# --------------------------------------------------------------------------- FileTypeUtils


class TestGetFileType:
    """``FileTypeUtils.getFileType(String)``."""

    @pytest.mark.parametrize(
        ("file_name", "expected"),
        [
            ("ruoyi.txt", "txt"),
            ("ruoyi.tar.gz", "gz"),
            ("/a/b/c.PNG", "png"),
            ("a", ""),
            ("a.", ""),
            (".bashrc", "bashrc"),
        ],
    )
    def test_the_suffix_is_lower_cased(self, file_name: str, expected: str) -> None:
        assert file_type_utils.get_file_type(file_name) == expected

    def test_a_dot_in_a_directory_name_is_not_special_cased(self) -> None:
        """与 ``FileUploadUtils.getExtension`` 不同：这里只看最后一个点，不做目录判断."""
        assert file_type_utils.get_file_type("a.b/c") == "b/c"

    def test_none_raises(self) -> None:
        with pytest.raises(AttributeError):
            file_type_utils.get_file_type(None)

    def test_the_file_overload_reads_name(self) -> None:
        class _File:
            name = "/x/ruoyi.XLSX"

        assert file_type_utils.get_file_type_of_file(_File()) == "xlsx"

    def test_the_file_overload_returns_empty_string_for_none(self) -> None:
        assert file_type_utils.get_file_type_of_file(None) == ""


class TestFileTypeUtilsExtendName:
    """``FileTypeUtils.getFileExtendName(byte[])`` —— 返回**大写**."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (GIF_BYTES, "GIF"),
            (JPG_BYTES, "JPG"),
            (BMP_BYTES, "BMP"),
            (PNG_BYTES, "PNG"),
            (b"\x00" * 16, "JPG"),
        ],
    )
    def test_magic_numbers(self, data: bytes, expected: str) -> None:
        assert file_type_utils.get_file_extend_name(data) == expected

    def test_a_short_array_raises(self) -> None:
        with pytest.raises(IndexError):
            file_type_utils.get_file_extend_name(b"BM")


# --------------------------------------------------------------------------- FileUtils


class TestFilenamePattern:
    """``FileUtils.isValidFilename``."""

    @pytest.mark.parametrize(
        "file_name",
        ["ruoyi.png", "a-b_c|d.txt", "中文.png", "a.b.c"],
    )
    def test_legal_names(self, file_name: str) -> None:
        assert file_utils.is_valid_filename(file_name) is True

    @pytest.mark.parametrize("file_name", ["a/b.png", "a b.png", "a@b.png", ""])
    def test_illegal_names(self, file_name: str) -> None:
        assert file_utils.is_valid_filename(file_name) is False

    def test_the_pattern_is_the_java_literal(self) -> None:
        assert file_utils.FILENAME_PATTERN == r"[a-zA-Z0-9_\-\|\.\u4e00-\u9fa5]+"


class TestCheckAllowDownload:
    """``FileUtils.checkAllowDownload`` —— **白名单**."""

    def test_dotdot_anywhere_is_rejected(self) -> None:
        assert file_utils.check_allow_download("../etc/passwd") is False
        assert file_utils.check_allow_download("a..png") is False

    def test_an_allowed_suffix_passes(self) -> None:
        assert file_utils.check_allow_download("export_用户数据.xlsx") is True
        assert file_utils.check_allow_download("a.pdf") is True

    def test_the_suffix_is_lower_cased_so_upper_case_passes(self) -> None:
        """``getFileType`` 会 ``toLowerCase()`` —— 与上传那边的**区分**大小写相反."""
        assert file_utils.check_allow_download("A.PNG") is True

    @pytest.mark.parametrize("name", ["a.json", "a.xml", "a.csv", "a", "a."])
    def test_suffixes_outside_the_whitelist_are_rejected(self, name: str) -> None:
        assert file_utils.check_allow_download(name) is False

    def test_no_suffix_is_rejected(self) -> None:
        """``getFileType("export")`` 是空串，不在白名单里."""
        assert file_utils.check_allow_download("export") is False


class TestEncoding:
    """``URLEncoder`` 的等价实现与 ``percentEncode``."""

    def test_space_becomes_plus_in_url_encode(self) -> None:
        assert file_utils.url_encode("a b") == "a+b"

    def test_percent_encode_turns_plus_into_percent_20(self) -> None:
        assert file_utils.percent_encode("a b.png") == "a%20b.png"

    def test_chinese_is_utf8_percent_encoded(self) -> None:
        assert file_utils.percent_encode("中文.png") == "%E4%B8%AD%E6%96%87.png"

    def test_tilde_is_encoded_but_star_is_not(self) -> None:
        """``URLEncoder`` 的安全集是 ``.-*_``；``urllib.parse.quote`` 是 ``_.-~``."""
        assert file_utils.url_encode("a~b*c.png") == "a%7Eb*c.png"

    def test_set_attachment_response_header_writes_three_headers(self) -> None:
        sink = ResponseSink()

        file_utils.set_attachment_response_header(sink, "1699999999999_用户数据.xlsx")

        headers = sink.headers
        assert (
            headers["Access-Control-Expose-Headers"]
            == "Content-Disposition,download-filename"
        )
        encoded = "1699999999999_%E7%94%A8%E6%88%B7%E6%95%B0%E6%8D%AE.xlsx"
        assert headers["Content-disposition"] == (
            "attachment; filename=" + encoded + ";filename*=utf-8''" + encoded
        )
        assert headers["download-filename"] == encoded

    def test_set_header_replaces_and_add_header_appends(self) -> None:
        sink = ResponseSink()
        sink.set_header("X-A", "1")
        sink.set_header("x-a", "2")
        sink.add_header("X-B", "3")

        assert sink.headers == {"x-a": "2", "X-B": "3"}


class TestNames:
    """``getName`` / ``getNameNotSuffix``."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("/profile/upload/2022/04/16/ruoyi.png", "ruoyi.png"),
            ("/profile/upload/2022/04/16/ruoyi", "ruoyi"),
            ("a\\b.png", "b.png"),
            ("abc", "abc"),
            ("", ""),
            (None, None),
        ],
    )
    def test_get_name(self, value: Any, expected: Any) -> None:
        assert file_utils.get_name(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("/a/b.tar.gz", "b.tar"),
            ("/a/b", "b"),
            ("a.png", "a"),
            (None, None),
        ],
    )
    def test_get_name_not_suffix(self, value: Any, expected: Any) -> None:
        assert file_utils.get_name_not_suffix(value) == expected


class TestExtendName:
    """``FileUtils.getFileExtendName`` —— 返回**小写**（与 ``FileTypeUtils`` 相反）."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (GIF_BYTES, "gif"),
            (JPG_BYTES, "jpg"),
            (BMP_BYTES, "bmp"),
            (PNG_BYTES, "png"),
            (b"\x00" * 16, "jpg"),
        ],
    )
    def test_magic_numbers(self, data: bytes, expected: str) -> None:
        assert file_utils.get_file_extend_name(data) == expected

    def test_a_short_array_raises(self) -> None:
        with pytest.raises(IndexError):
            file_utils.get_file_extend_name(b"BM")


class TestWriteBytes:
    """``FileUtils.writeBytes(String, OutputStream)`` —— 关流语义."""

    def test_copies_the_file_and_closes_the_stream(self, tmp_path: Any) -> None:
        source = tmp_path / "a.txt"
        source.write_bytes(b"hello")
        sink = ResponseSink()

        file_utils.write_bytes(str(source), sink.get_output_stream())

        assert sink.body == b"hello"
        # 关流之后再写就报错（与真实流一致）
        with pytest.raises(ValueError):
            sink.get_output_stream().write(b"x")

    def test_a_missing_file_still_closes_the_stream(self, tmp_path: Any) -> None:
        """这是 ``/common/download`` 回 200 空 body 的根因（``finally`` 里关流）."""
        sink = ResponseSink()
        stream = sink.get_output_stream()

        with pytest.raises(FileNotFoundError):
            file_utils.write_bytes(str(tmp_path / "missing.txt"), stream)

        with pytest.raises(ValueError):
            stream.write(b"x")
        assert sink.body == b""

    def test_a_directory_is_not_a_file(self, tmp_path: Any) -> None:
        with pytest.raises(FileNotFoundError):
            file_utils.write_bytes(str(tmp_path), ResponseSink().get_output_stream())


class TestDeleteFile:
    """``FileUtils.deleteFile`` —— 目录不删."""

    def test_a_file_is_removed(self, tmp_path: Any) -> None:
        target = tmp_path / "a.txt"
        target.write_bytes(b"x")

        assert file_utils.delete_file(str(target)) is True
        assert not target.exists()

    def test_a_missing_path_returns_false(self, tmp_path: Any) -> None:
        assert file_utils.delete_file(str(tmp_path / "nope.txt")) is False

    def test_a_directory_returns_false(self, tmp_path: Any) -> None:
        """Java: ``file.isFile()`` 是 false -> 不删."""
        assert file_utils.delete_file(str(tmp_path)) is False
        assert tmp_path.exists()


class TestWriteData:
    """``writeBytes(byte[], String)`` / ``writeImportBytes(byte[])``."""

    def test_write_bytes_to_dir_returns_a_profile_url(self, profile: str) -> None:
        url = file_utils.write_bytes_to_dir(PNG_BYTES, profile + "/import")

        assert url.startswith("/profile/import/")
        assert url.endswith(".png")
        # 真的落盘了
        absolute = profile + url[len("/profile") :]
        assert os.path.isfile(absolute)

    def test_write_import_bytes_uses_the_import_path(self, profile: str) -> None:
        url = file_utils.write_import_bytes(PNG_BYTES)

        assert url.startswith("/profile/import/")


class TestSetFileDownloadHeader:
    """``FileUtils.setFileDownloadHeader`` —— **无调用方**，照搬."""

    class _Request:
        def __init__(self, agent: Any) -> None:
            self.headers = {} if agent is None else {"USER-AGENT": agent}

    def test_ie_percent_encodes_and_restores_spaces(self) -> None:
        request = self._Request("Mozilla/4.0 (compatible; MSIE 8.0)")

        assert file_utils.set_file_download_header(request, "a b.png") == "a b.png"

    def test_chrome_percent_encodes_with_plus(self) -> None:
        request = self._Request("Mozilla/5.0 Chrome/120")

        assert file_utils.set_file_download_header(request, "a b.png") == "a+b.png"

    def test_firefox_re_decodes_as_iso_8859_1(self) -> None:
        request = self._Request("Mozilla/5.0 Firefox/120")

        result = file_utils.set_file_download_header(request, "abc.png")

        assert result == "abc.png"

    def test_a_missing_user_agent_raises(self) -> None:
        """Java: ``agent.contains(...)`` -> NPE；这里 ``"MSIE" in None`` -> ``TypeError``."""
        with pytest.raises(TypeError):
            file_utils.set_file_download_header(self._Request(None), "a.png")
