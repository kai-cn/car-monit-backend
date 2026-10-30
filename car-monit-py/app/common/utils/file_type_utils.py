"""文件类型工具类 / file-type helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileTypeUtils.java

Java 的 ``com.ruoyi.common.utils.file`` 包在 Python 侧拍平成 ``app.common.utils.*``
（与 ``uuid`` 包的处理一致），因此本模块叫 ``file_type_utils``。

与 :mod:`app.common.utils.mime_type_utils` 的分工
------------------------------------------------
两个类名字很像，不要混用：

* ``MimeTypeUtils``（:mod:`mime_type_utils`）—— 由 ``Content-Type`` **反推**后缀，
  只有 5 个图片分支；
* ``FileTypeUtils``（本模块）—— 由**文件名**取后缀，**会 ``toLowerCase()``**。

``check_allow_download`` 用的是后者，所以下载白名单实际上**不区分大小写**
（``DEFAULT_ALLOWED_EXTENSION`` 全是小写，而 ``get_file_type`` 已经转小写）。
文件上传走的是前者，**区分大小写** —— 两处判据不同，是 Java 原样。

``getFileExtendName(byte[])`` 的大小写与 ``FileUtils`` 里的同名方法**相反**
------------------------------------------------------------------------
``FileTypeUtils.getFileExtendName`` 返回**大写**（``"JPG"`` / ``"GIF"`` …），
``FileUtils.getFileExtendName`` 返回**小写**（``"jpg"`` / ``"gif"`` …）。
两个方法名一样、实现逐字一样、返回值大小写不同，属于历史遗留。照抄，别统一。
"""

from __future__ import annotations

from typing import Final, Optional

#: Java: ``FileTypeUtils.getFileExtendName`` 的默认值（**大写**）
DEFAULT_EXTEND_NAME: Final[str] = "JPG"


def get_file_type(file_name: Optional[str]) -> str:
    """按文件名取后缀（不含点，已转小写）. Java: ``getFileType(String fileName)``.

    ``fileName`` 为 ``None`` 时 Java 会在 ``lastIndexOf`` 上抛 NPE；这里同样不兜底
    （``AttributeError`` 落到 ``Exception`` 处理器，信封一致）。

    注意 ``"a.b/c"`` 这类"点在目录上"的输入**不特殊处理** —— 只看最后一个 ``.``，
    所以结果是 ``"b/c"``。这与 ``FileUploadUtils.getExtension`` 的行为不同，是 Java 原样。
    """
    separator_index = file_name.rfind(".")  # type: ignore[union-attr]
    if separator_index < 0:
        return ""
    return file_name[separator_index + 1 :].lower()  # type: ignore[index]


def get_file_type_of_file(file: object) -> str:
    """``getFileType(File)`` 重载 —— ``file.getName()`` 再走上面那个.

    ``file`` 为 ``None`` 时返回空串（Java 有 ``if (null == file) return StringUtils.EMPTY``）。
    本项目没有 ``java.io.File``，所以 ``file`` 只需要有 ``name`` 属性。
    """
    if file is None:
        return ""
    return get_file_type(getattr(file, "name"))


def get_file_extend_name(photo_byte: bytes) -> str:
    """按魔数猜测图片后缀（**大写**）. Java: ``FileTypeUtils.getFileExtendName(byte[])``.

    Java 直接按下标读 ``photoByte[6]`` … ``photoByte[9]``，长度不足 10 会抛
    ``ArrayIndexOutOfBoundsException``。这里显式抛 :class:`IndexError` —— 与
    ``RuntimeException`` 一样落到 ``code 500`` 的信封里。

    :returns: ``"JPG"`` / ``"GIF"`` / ``"BMP"`` / ``"PNG"``
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
        return "GIF"
    if photo_byte[6] == 74 and photo_byte[7] == 70 and photo_byte[8] == 73 and photo_byte[9] == 70:
        return "JPG"
    if photo_byte[0] == 66 and photo_byte[1] == 77:
        return "BMP"
    if photo_byte[1] == 80 and photo_byte[2] == 78 and photo_byte[3] == 71:
        return "PNG"
    return DEFAULT_EXTEND_NAME


__all__ = [
    "DEFAULT_EXTEND_NAME",
    "get_file_type",
    "get_file_type_of_file",
    "get_file_extend_name",
]
