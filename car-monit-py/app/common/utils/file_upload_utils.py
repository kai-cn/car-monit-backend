"""文件上传工具类 / file upload helper.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java
# Migrated from: org.apache.commons.io.FilenameUtils (只搬了用到的 3 个方法)

Java 包 ``com.ruoyi.common.utils.file`` 在 Python 侧拍平成 ``app.common.utils.*``
（同 ``uuid`` 包的处理），所以本模块叫 ``file_upload_utils``。

重载对照表（Java 三个 ``upload`` 重载 -> 三个名字）
--------------------------------------------------
    ======================================================  ===================================
    Java                                                     Python
    ======================================================  ===================================
    ``upload(MultipartFile)``                                 :func:`upload_default`
    ``upload(String baseDir, MultipartFile)``                  :func:`upload`
    ``upload(String baseDir, MultipartFile, String[])``        :func:`upload_with_extensions`
    ======================================================  ===================================

**只有 2 参重载会被业务代码调用**（``SysProfileController`` 与 ``CommonController``），
所以"最常用"的那个占用 ``upload`` 这个名字；3 参重载叫 ``upload_with_extensions``；
1 参重载本项目没有调用者，按"不删看似无用的 Java 代码"的原则一起迁过来。

异常包装（1/2 参重载）
----------------------
Java 的 1 参、2 参重载都是::

    try { return upload(baseDir, file, DEFAULT_ALLOWED_EXTENSION); }
    catch (Exception e) { throw new IOException(e.getMessage(), e); }

也就是说**连 ``FileSizeLimitExceededException`` 这种受检异常也会被包成
``IOException``**。Python 侧用 ``OSError`` 对应 ``java.io.IOException``，
消息原样透传 —— 客户端看到的 ``code 500`` + 文案与 Java 完全一致。

生成的文件名
------------
``extractFilename`` 拼的是 ``{datePath}/{原文件名去后缀}_{序列号}.{后缀}``::

    2026/10/26/avatar_20261026143001A001.png

* ``datePath()`` 是 ``yyyy/MM/dd``（带斜杠，直接当子目录用）；
* 序列号来自 :func:`app.common.utils.seq.get_id`（``yyyyMMddHHmmss`` + ``A`` + 3 位）；
* 后缀取 ``FilenameUtils.getExtension(originalFilename)``，空则回退到 ``Content-Type``。

返回给客户端的 url 由 ``getPathFileName`` 生成：把 ``profile`` 前缀（含紧跟的一个
分隔符）切掉，换成 ``Constants.RESOURCE_PREFIX``（``/profile``），所以最终是
``/profile/avatar/2026/10/26/avatar_20261026143001A001.png``。**数据库里存的就是这个
相对 url**，不是磁盘路径。
"""

from __future__ import annotations

import logging
import os
from typing import Final, Optional, Sequence

from app.common.constant.constants import RESOURCE_PREFIX
from app.common.exception.file import (
    FileNameLengthLimitExceededException,
    FileSizeLimitExceededException,
    InvalidExtensionException,
)
from app.common.utils.date_utils import date_path
from app.common.utils.mime_type_utils import (
    DEFAULT_ALLOWED_EXTENSION,
    FLASH_EXTENSION,
    IMAGE_EXTENSION,
    MEDIA_EXTENSION,
    VIDEO_EXTENSION,
)
from app.common.utils.mime_type_utils import get_extension as get_mime_extension
from app.common.utils.seq import UPLOAD_SEQ_TYPE, get_id
from app.common.utils.string_utils import format as java_format
from app.common.utils.string_utils import is_empty, substring
from app.settings import get_settings

logger = logging.getLogger("app.common.utils.file_upload_utils")

#: 默认大小 50M
DEFAULT_MAX_SIZE: Final[int] = 50 * 1024 * 1024

#: 默认的文件名最大长度 100
DEFAULT_FILE_NAME_LENGTH: Final[int] = 100

#: Java: ``private static String defaultBaseDir = RuoYiConfig.getProfile();``
#: ``None`` 表示"还没被 ``set_default_base_dir`` 改过"，此时读配置里的 ``profile``。
_DEFAULT_BASE_DIR: Optional[str] = None


def set_default_base_dir(default_base_dir: str) -> None:
    """Java: ``setDefaultBaseDir(String)``."""
    global _DEFAULT_BASE_DIR
    _DEFAULT_BASE_DIR = default_base_dir


def get_default_base_dir() -> str:
    """Java: ``getDefaultBaseDir()``.

    Java 在类加载时就把 ``RuoYiConfig.getProfile()`` 存进静态字段；Python 侧默认值
    改为"用时再读配置"，这样 :func:`app.settings.reset_settings_cache` 之后不需要
    额外重置本模块 —— 只有在显式调用 ``set_default_base_dir`` 之后才与 Java 一致。
    """
    if _DEFAULT_BASE_DIR is not None:
        return _DEFAULT_BASE_DIR
    return get_settings().ruoyi.profile


def reset_default_base_dir() -> None:
    """Test helper: 撤销 ``set_default_base_dir`` 的设置。"""
    global _DEFAULT_BASE_DIR
    _DEFAULT_BASE_DIR = None


def upload_default(file: object) -> str:
    """以默认配置进行文件上传. Java: ``upload(MultipartFile file)``.

    本项目没有调用者（Java 侧同样没有），保留以对齐源码。
    """
    try:
        return upload_with_extensions(get_default_base_dir(), file, DEFAULT_ALLOWED_EXTENSION)
    except Exception as exc:  # noqa: BLE001 - Java: catch (Exception e) -> IOException
        raise OSError(_message_of(exc)) from exc


def upload(base_dir: str, file: object) -> str:
    """根据文件路径上传. Java: ``upload(String baseDir, MultipartFile file)``.

    唯一的业务入口：``SysProfileController.avatar`` 传 ``RuoYiConfig.getAvatarPath()``。
    """
    try:
        return upload_with_extensions(base_dir, file, DEFAULT_ALLOWED_EXTENSION)
    except Exception as exc:  # noqa: BLE001 - Java: catch (Exception e) -> IOException
        raise OSError(_message_of(exc)) from exc


def upload_with_extensions(
    base_dir: str, file: object, allowed_extension: Optional[Sequence[str]]
) -> str:
    """文件上传. Java: ``upload(String baseDir, MultipartFile file, String[] allowedExtension)``.

    顺序与原版一致：**先**校验文件名长度、**再**校验大小/后缀、**最后**才落盘。
    超长文件名与非法后缀都不会在磁盘上留下任何东西。
    """
    # Java: int fileNamelength = Objects.requireNonNull(file.getOriginalFilename()).length();
    # 文件名为 null 时 Java 抛 NPE；这里 ``len(None)`` 抛 TypeError，落到同一个处理器。
    file_name_length = len(file.filename)  # type: ignore[attr-defined]
    if file_name_length > DEFAULT_FILE_NAME_LENGTH:
        raise FileNameLengthLimitExceededException(DEFAULT_FILE_NAME_LENGTH)

    assert_allowed(file, allowed_extension)

    file_name = extract_filename(file)

    abs_path = get_absolute_file(base_dir, file_name)
    _transfer_to(file, abs_path)
    return get_path_file_name(base_dir, file_name)


def extract_filename(file: object) -> str:
    """编码文件名. Java: ``extractFilename(MultipartFile file)``.

    形如 ``2026/10/26/avatar_20261026143001A001.png`` —— **带子目录**，不是纯文件名。
    """
    original_filename = file.filename  # type: ignore[attr-defined]
    return java_format(
        "{}/{}_{}.{}",
        date_path(),
        _get_base_name(original_filename),
        get_id(UPLOAD_SEQ_TYPE),
        get_extension(file),
    )


def get_absolute_file(upload_dir: str, file_name: str) -> str:
    """Java: ``getAbsoluteFile(String uploadDir, String fileName)`` -> 绝对磁盘路径.

    目录不存在时逐级创建（Java 的 ``mkdirs()``）。注意 ``file_name`` 里带 ``/``，
    所以最后一级 ``file_name`` 的父目录是 ``.../yyyy/MM/dd``。
    """
    desc = upload_dir + os.sep + file_name

    if not os.path.exists(desc):
        parent = os.path.dirname(desc)
        if not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
    return os.path.abspath(desc)


def get_path_file_name(upload_dir: str, file_name: str) -> str:
    """Java: ``getPathFileName(String uploadDir, String fileName)`` -> 对外 url.

    ``profile`` 前缀连同后面那一个分隔符一起切掉，换成 ``/profile``::

        D:/ruoyi/uploadPath/avatar + 2026/10/26/a_b.png
        -> /profile/avatar/2026/10/26/a_b.png

    切分点用的是**配置里的 profile 长度**，不是 ``upload_dir`` 的长度 —— 所以传一个
    不在 ``profile`` 之下的目录时，结果会是"从头截错位置"的怪字符串（Java 行为一致，
    没有校验）。``StringUtils.substring`` 对越界做钳位，不会抛异常。
    """
    dir_last_index = len(get_settings().ruoyi.profile) + 1
    current_dir = substring(upload_dir, dir_last_index)
    return RESOURCE_PREFIX + "/" + current_dir + "/" + file_name


def assert_allowed(file: object, allowed_extension: Optional[Sequence[str]]) -> None:
    """文件大小 / 后缀校验. Java: ``assertAllowed(MultipartFile, String[])``.

    两个细节：

    * 大小上限用的是 **字节**（``DEFAULT_MAX_SIZE``），但报错文案里传的是
      ``DEFAULT_MAX_SIZE / 1024 / 1024`` = 50，即"MB 数"；
    * ``allowed_extension == MimeTypeUtils.IMAGE_EXTENSION`` 是**引用比较**，
      Python 用 ``is`` 保留（见 :mod:`app.common.utils.mime_type_utils`）。
    """
    size = size_of(file)
    if size > DEFAULT_MAX_SIZE:
        raise FileSizeLimitExceededException(DEFAULT_MAX_SIZE // 1024 // 1024)

    file_name = file.filename  # type: ignore[attr-defined]
    extension = get_extension(file)
    if allowed_extension is not None and not is_allowed_extension(extension, allowed_extension):
        if allowed_extension is IMAGE_EXTENSION:
            raise InvalidExtensionException.InvalidImageExtensionException(
                allowed_extension, extension, file_name
            )
        if allowed_extension is FLASH_EXTENSION:
            raise InvalidExtensionException.InvalidFlashExtensionException(
                allowed_extension, extension, file_name
            )
        if allowed_extension is MEDIA_EXTENSION:
            raise InvalidExtensionException.InvalidMediaExtensionException(
                allowed_extension, extension, file_name
            )
        if allowed_extension is VIDEO_EXTENSION:
            raise InvalidExtensionException.InvalidVideoExtensionException(
                allowed_extension, extension, file_name
            )
        raise InvalidExtensionException(allowed_extension, extension, file_name)


def is_allowed_extension(extension: Optional[str], allowed_extension: Sequence[str]) -> bool:
    """判断后缀是否在白名单里. Java: ``isAllowedExtension(String, String[])``.

    ``equalsIgnoreCase``：``.PNG`` 与 ``png`` 等价。
    """
    return any(
        allowed is not None and extension is not None and allowed.lower() == extension.lower()
        for allowed in allowed_extension
    )


def get_extension(file: object) -> str:
    """获取文件名的后缀. Java: ``getExtension(MultipartFile file)``.

    优先取原文件名的后缀；取不到时（无后缀、或 ``.bashrc`` 这种）回退到
    ``MimeTypeUtils.getExtension(contentType)``，而后者只认 5 种图片类型，
    其余返回空串。``contentType`` 为 ``null`` 时 Java ``Objects.requireNonNull`` NPE，
    这里抛 TypeError。
    """
    extension = _get_extension_of(file.filename)  # type: ignore[attr-defined]
    if is_empty(extension):
        content_type = file.content_type  # type: ignore[attr-defined]
        if content_type is None:
            # Java: Objects.requireNonNull(file.getContentType())
            raise TypeError("file.getContentType() 为 null, 无法推断后缀")
        extension = get_mime_extension(content_type)
    return extension or ""


# --------------------------------------------------------------------------- 内部


def _message_of(exc: BaseException) -> str:
    """Java: ``new IOException(e.getMessage(), e)`` —— 只取 message，可能为 ``null``。

    Java 的 ``IOException(null)`` 的 message 就是 ``null``，客户端会看到
    ``{"code":500,"msg":null}``。这里返回空串或 ``str(exc)``：``OSError("")`` 的
    ``str`` 也是空串，行为一致。
    """
    message = exc.message if isinstance(getattr(exc, "message", None), str) else None
    if message is not None:
        return message
    return str(exc)


def size_of(file: object) -> int:
    """Java: ``MultipartFile#getSize()`` —— 上传内容的**字节数**.

    Starlette 的 ``UploadFile.size`` 由 multipart 解析器填好；手工构造时可能是
    ``None``，此时退回到"读一遍底层文件的长度"，等价于 Java 的真实字节数。

    公开导出是因为 ``SysProfileController.avatar`` 要复刻 ``file.isEmpty()``
    （即 ``getSize() == 0``），不该重复实现一遍尺寸计算。
    """
    size = getattr(file, "size", None)
    if isinstance(size, int):
        return size
    stream = file.file  # type: ignore[attr-defined]
    position = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(position)
    return int(size)


def _transfer_to(file: object, abs_path: str) -> None:
    """Java: ``file.transferTo(Paths.get(absPath))``.

    Spring 的 ``transferTo`` 语义是"把整个上传内容写到目标文件"（必要时把临时文件
    移动过去）。这里整段读出再写入 —— 头像最大 50M，内存里过一遍无妨，且不依赖
    ``SpooledTemporaryFile`` 的名字（那个临时文件随时可能已经被清理）。
    """
    stream = file.file  # type: ignore[attr-defined]
    stream.seek(0)
    data = stream.read()
    with open(abs_path, "wb") as handle:
        handle.write(data)


def _get_base_name(filename: Optional[str]) -> Optional[str]:
    """Java: ``FilenameUtils.getBaseName(String)`` -> 去掉目录与最后一段后缀.

    ``a/b.png`` -> ``b``；``a.b.png`` -> ``a.b``；``.bashrc`` -> ``""``（后缀就是
    整个名字）；``None`` -> ``None``。
    """
    name = _get_name(filename)
    if name is None:
        return None
    index = _index_of_extension(name)
    if index == -1:
        return name
    return name[:index]


def _get_name(filename: Optional[str]) -> Optional[str]:
    """Java: ``FilenameUtils.getName(String)`` -> 最后一个分隔符之后的部分."""
    if filename is None:
        return None
    return filename[_index_of_last_separator(filename) + 1 :]


def _get_extension_of(filename: Optional[str]) -> Optional[str]:
    """Java: ``FilenameUtils.getExtension(String)`` -> 最后一段后缀（不含点）."""
    if filename is None:
        return None
    index = _index_of_extension(filename)
    if index == -1:
        return ""
    return filename[index + 1 :]


def _index_of_last_separator(filename: str) -> int:
    """Java: ``FilenameUtils.indexOfLastSeparator(String)`` -- ``/`` 与 ``\\`` 都算."""
    return max(filename.rfind("/"), filename.rfind("\\"))


def _index_of_extension(filename: str) -> int:
    """Java: ``FilenameUtils.indexOfExtension(String)``.

    关键在 ``lastSeparator > extensionPos`` 这一句：``a.b/c`` 里的点在目录名上，
    不算后缀，返回 ``-1``。
    """
    extension_pos = filename.rfind(".")
    last_separator = _index_of_last_separator(filename)
    return -1 if last_separator > extension_pos else extension_pos


__all__ = [
    "DEFAULT_MAX_SIZE",
    "DEFAULT_FILE_NAME_LENGTH",
    "set_default_base_dir",
    "get_default_base_dir",
    "reset_default_base_dir",
    "upload_default",
    "upload",
    "upload_with_extensions",
    "extract_filename",
    "get_absolute_file",
    "get_path_file_name",
    "assert_allowed",
    "is_allowed_extension",
    "get_extension",
    "size_of",
]
