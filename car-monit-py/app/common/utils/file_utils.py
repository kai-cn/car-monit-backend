"""文件处理工具类 / file helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUtils.java

Java 的 ``com.ruoyi.common.utils.file`` 包在 Python 侧拍平成 ``app.common.utils.*``
（与 ``uuid`` 包的处理一致），因此本模块叫 ``file_utils``。

**与 :mod:`app.common.utils.file_util` 不是同一个东西**：那个是 hutool 的
``cn.hutool.core.io.FileUtil``（只有 ``extName`` / ``copy`` 两个方法），本项目里被
``SysFileServiceImpl`` 用。本模块是 RuoYi 自己的 ``FileUtils``。

重载对照表（Java 有两个 ``writeBytes``）
---------------------------------------
    ==========================================  ======================================
    Java                                        Python
    ==========================================  ======================================
    ``writeBytes(String filePath, OutputStream)``  :func:`write_bytes`
    ``writeBytes(byte[] data, String uploadDir)``  :func:`write_bytes_to_dir`
    ``writeImportBytes(byte[] data)``              :func:`write_import_bytes`
    ==========================================  ======================================

``write_bytes`` 会在 ``finally`` 里 **关掉输出流**
-----------------------------------------------
Java::

    finally { IOUtils.close(os); IOUtils.close(fis); }

也就是说：文件不存在时抛 ``FileNotFoundException``，但**输出流已经被关掉**。servlet
世界里"关流 = 提交响应"，所以 ``GET /common/download`` 在文件缺失时拿到的是
**HTTP 200 + 完整的响应头 + 空 body**（不是 404）。这个语义靠
:class:`app.system.service.sys_file_service.ResponseSink` 里那个 close 宽容的流包装来保留。

``checkAllowDownload`` 是**白名单**，不是黑名单
----------------------------------------------
.. code-block:: java

    if (StringUtils.contains(resource, "..")) return false;                 // 目录上跳
    if (ArrayUtils.contains(DEFAULT_ALLOWED_EXTENSION, getFileType(resource))) return true;
    return false;

* ``".."`` 出现在**任意位置**都拒绝（不只看路径段）；
* 后缀由 :func:`app.common.utils.file_type_utils.get_file_type` 取 —— 已转小写，
  所以 ``.PNG`` 也能下（上传那边是**区分**大小写的，两处判据不同）；
* ``DEFAULT_ALLOWED_EXTENSION`` 里没有 ``"json"`` / ``"xml"`` / ``"csv"``，所以这些
  后缀**一律 403 式拒绝**（表现为"下不下来"，因为异常被兜住）。

``request.getHeader("USER-AGENT")`` 为 ``null`` 时 NPE
-----------------------------------------------------
:func:`set_file_download_header` 直接 ``agent.contains(...)``，没判空。本项目里它
**没有调用方**（``set_attachment_response_header`` 已经取代了它），按迁移原则第 4 条
照留、照抄这个缺陷。
"""

from __future__ import annotations

import locale
import logging
import os
import re
from typing import BinaryIO, Final, Optional, Pattern

from app.common.utils import file_upload_utils
from app.common.utils.date_utils import date_path
from app.common.utils.file_type_utils import get_file_type
from app.common.utils.mime_type_utils import DEFAULT_ALLOWED_EXTENSION
from app.common.utils.string_utils import contains
from app.common.utils.uuid_utils import fast_uuid
from app.settings import get_settings

logger = logging.getLogger("app.common.utils.file_utils")

#: Java: ``public static String FILENAME_PATTERN``
FILENAME_PATTERN: Final[str] = r"[a-zA-Z0-9_\-\|\.\u4e00-\u9fa5]+"

_FILENAME_RE: Final[Pattern[str]] = re.compile(FILENAME_PATTERN)

#: ``java.net.URLEncoder.encode`` 的"安全字符"集合（除字母数字外只有这 4 个）。
#: 注意它**不**包含 ``~``（会被编码成 ``%7E``），而 :func:`urllib.parse.quote` 相反。
_URL_ENCODER_SAFE: Final[frozenset] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-*_"
)


def write_bytes(file_path: str, output_stream: BinaryIO) -> None:
    """输出指定文件的字节数组. Java: ``writeBytes(String filePath, OutputStream os)``.

    文件不存在时抛 :class:`FileNotFoundError`（Java 的 ``FileNotFoundException``），
    但**无论成功失败都会先关掉输出流** —— 这是 Java ``finally`` 块的行为，也是
    ``/common/download`` 在文件缺失时仍然返回 200 空 body 的原因。
    """
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        with open(file_path, "rb") as source:
            while True:
                chunk = source.read(1024)
                if not chunk:
                    break
                output_stream.write(chunk)
    finally:
        try:
            output_stream.close()
        except Exception:  # noqa: BLE001 - Java: IOUtils.close 静默吞掉
            logger.debug("关闭输出流失败", exc_info=True)


def write_import_bytes(data: bytes) -> str:
    """写数据到导入目录. Java: ``writeImportBytes(byte[] data)``."""
    return write_bytes_to_dir(data, get_settings().ruoyi.import_path)


def write_bytes_to_dir(data: bytes, upload_dir: str) -> str:
    """写数据到指定目录并返回相对 url. Java: ``writeBytes(byte[] data, String uploadDir)``.

    文件名是 ``{yyyy/MM/dd}/{fastUUID}.{猜测的后缀}``；后缀来自
    :func:`app.common.utils.file_utils.get_file_extend_name`（**小写**）。

    本项目里**没有调用方**（``ExcelUtil#importExcel`` 那句在 Python 侧改成了直接从
    上传流读），按迁移原则第 4 条照留。
    """
    extension = get_file_extend_name(data)
    path_name = date_path() + "/" + fast_uuid() + "." + extension
    absolute = file_upload_utils.get_absolute_file(upload_dir, path_name)
    with open(absolute, "wb") as target:
        target.write(data)
    return file_upload_utils.get_path_file_name(upload_dir, path_name)


def delete_file(file_path: str) -> bool:
    """删除文件. Java: ``deleteFile(String filePath)``.

    只有"是文件且存在"才删，**目录不删**；删除失败返回 ``False``。
    """
    if os.path.isfile(file_path) and os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    return False


def is_valid_filename(filename: str) -> bool:
    """文件名称验证. Java: ``isValidFilename(String filename)``.

    Java 的 ``String.matches`` 是**整串**匹配，所以这里用 ``fullmatch``。
    ``None`` 在 Java 里抛 NPE；这里同样不兜底。
    """
    return _FILENAME_RE.fullmatch(filename) is not None


def check_allow_download(resource: Optional[str]) -> bool:
    """检查文件是否可下载. Java: ``checkAllowDownload(String resource)``.

    ``None`` 时 ``StringUtils.contains(null, "..")`` 返回 ``false``，随后
    ``getFileType(null)`` 抛 NPE —— Java 同样会 NPE，这里也不兜底。
    """
    # 禁止目录上跳级别
    if contains(resource, ".."):
        return False
    # 检查允许下载的文件规则
    return get_file_type(resource) in DEFAULT_ALLOWED_EXTENSION


def set_file_download_header(request: object, file_name: str) -> str:
    """下载文件名重新编码（旧版，**无调用方**）. Java: ``setFileDownloadHeader``.

    按 ``User-Agent`` 分三种编码：IE 走 ``URLEncoder`` 并把 ``+`` 换回空格；
    Firefox 走 ``getBytes()`` + ISO-8859-1 重解码；其余走 ``URLEncoder``。

    ``agent`` 为 ``None`` 时 Java 抛 NPE（``agent.contains``）—— 这里 ``"MSIE" in None``
    抛 ``TypeError``，落到同一个异常信封。照抄，不兜底。
    """
    agent = request.headers.get("USER-AGENT")  # type: ignore[attr-defined]
    filename = file_name
    if "MSIE" in agent:
        # IE浏览器
        filename = url_encode(filename).replace("+", " ")
    elif "Firefox" in agent:
        # 火狐浏览器 —— Java: new String(fileName.getBytes(), "ISO8859-1")
        # getBytes() 用**平台默认字符集**（中文 Windows 上是 GBK），再按 ISO-8859-1 解码。
        filename = file_name.encode(_platform_charset()).decode("iso-8859-1", errors="replace")
    else:
        # google浏览器 / 其它浏览器 —— 两个分支行为完全相同，Java 里也是分开写的
        filename = url_encode(filename)
    return filename


def set_attachment_response_header(response: object, real_file_name: str) -> None:
    """下载文件名重新编码并写响应头. Java: ``setAttachmentResponseHeader``.

    写 3 个头（顺序与 Java 一致）：

    1. ``Access-Control-Expose-Headers: Content-Disposition,download-filename``
    2. ``Content-disposition: attachment; filename=<p>;filename*=utf-8''<p>``
    3. ``download-filename: <p>``

    ``<p>`` 是 :func:`percent_encode` 的结果。注意第 2 个头里
    ``filename=`` 与百分号串之间**没有空格**，``;filename*=`` 前也没有空格 —— 照抄。
    """
    percent_encoded_filename = percent_encode(real_file_name)

    content_disposition_value = (
        "attachment; filename="
        + percent_encoded_filename
        + ";"
        + "filename*="
        + "utf-8''"
        + percent_encoded_filename
    )

    response.add_header("Access-Control-Expose-Headers", "Content-Disposition,download-filename")  # type: ignore[attr-defined]
    response.set_header("Content-disposition", content_disposition_value)  # type: ignore[attr-defined]
    response.set_header("download-filename", percent_encoded_filename)  # type: ignore[attr-defined]


def percent_encode(value: str) -> str:
    """百分号编码. Java: ``percentEncode(String s)``.

    ``URLEncoder.encode(s, "UTF-8")`` 之后把 ``+`` 换成 ``%20``。
    """
    return url_encode(value).replace("+", "%20")


def url_encode(value: str) -> str:
    """``java.net.URLEncoder.encode(String, "UTF-8")`` 的等价实现.

    保留字母数字与 ``.-*_``；空格 -> ``+``；其余按 UTF-8 逐字节 ``%XX``（**大写**十六进制）。
    """
    out = []
    for char in value:
        if char in _URL_ENCODER_SAFE:
            out.append(char)
        elif char == " ":
            out.append("+")
        else:
            for byte in char.encode("utf-8"):
                out.append("%%%02X" % byte)
    return "".join(out)


def get_file_extend_name(photo_byte: bytes) -> str:
    """获取图像后缀（**小写**）. Java: ``FileUtils.getFileExtendName(byte[])``.

    与 :func:`app.common.utils.file_type_utils.get_file_extend_name` 逐字相同，
    **只有返回值大小写不同**（这里小写、那边大写）。照抄，别合并。

    长度不足 10 时 Java 抛 ``ArrayIndexOutOfBoundsException``，这里抛 :class:`IndexError`。
    """
    if len(photo_byte) < 10:
        raise IndexError("index out of range")
    if (
        photo_byte[0] == 71
        and photo_byte[1] == 73
        and photo_byte[2] == 70
        and photo_byte[3] == 56
        and (photo_byte[4] == 55 or photo_byte[4] == 57)
        and photo_byte[5] == 97
    ):
        return "gif"
    if photo_byte[6] == 74 and photo_byte[7] == 70 and photo_byte[8] == 73 and photo_byte[9] == 70:
        return "jpg"
    if photo_byte[0] == 66 and photo_byte[1] == 77:
        return "bmp"
    if photo_byte[1] == 80 and photo_byte[2] == 78 and photo_byte[3] == 71:
        return "png"
    return "jpg"


def get_name(file_name: Optional[str]) -> Optional[str]:
    """获取文件名称. Java: ``getName(String fileName)``.

    ``/profile/upload/2022/04/16/ruoyi.png`` -> ``ruoyi.png``。
    ``/`` 与 ``\\`` 都算分隔符，取**最后一个**。
    """
    if file_name is None:
        return None
    index = max(file_name.rfind("/"), file_name.rfind("\\"))
    return file_name[index + 1 :]


def get_name_not_suffix(file_name: Optional[str]) -> Optional[str]:
    """获取不带后缀的文件名称. Java: ``getNameNotSuffix(String fileName)``.

    走 commons-io 的 ``FilenameUtils.getBaseName``，**不是**简单的 ``rsplit(".")``：

    * ``"/a/b.tar.gz"`` -> ``"b.tar"``；
    * ``"/a/b"``       -> ``"b"``；
    * ``"a/"``         -> ``""``。
    """
    if file_name is None:
        return None
    # FilenameUtils.indexOfExtension：先去掉路径，再找最后一个点
    index = max(file_name.rfind("/"), file_name.rfind("\\"))
    name = file_name[index + 1 :]
    dot = name.rfind(".")
    return name if dot < 0 else name[:dot]


def _platform_charset() -> str:
    """Java ``String.getBytes()`` 用的平台默认字符集."""
    return locale.getpreferredencoding(False) or "utf-8"


__all__ = [
    "FILENAME_PATTERN",
    "check_allow_download",
    "delete_file",
    "get_file_extend_name",
    "get_name",
    "get_name_not_suffix",
    "is_valid_filename",
    "percent_encode",
    "set_attachment_response_header",
    "set_file_download_header",
    "url_encode",
    "write_bytes",
    "write_bytes_to_dir",
    "write_import_bytes",
]
