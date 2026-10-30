"""媒体类型工具类 / MIME-type helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/MimeTypeUtils.java

Java 的 ``com.ruoyi.common.utils.file`` 包在 Python 侧拍平成
``app.common.utils.*``（与 ``uuid`` 包的处理一致），因此本模块叫
``mime_type_utils`` 而不是 ``file/mime_type_utils``。

类型选择（为什么是 tuple 而不是 list）
--------------------------------------
Java 的常量是 ``String[]``。``FileUploadUtils.assertAllowed`` 里有一段

    if (allowedExtension == MimeTypeUtils.IMAGE_EXTENSION)

这是**引用比较**（数组的 ``==`` 比较的是引用），不是内容比较。也就是说：调用方传
``new String[]{"png"}`` 这种"内容相同但对象不同"的数组时，走的是最后一个通用分支，
客户端看到的错误文案里不会出现 ``InvalidImageExtensionException`` 的差别（两者文案
其实一样，只有类型不同）。Python 侧用 **tuple + ``is`` 比较**保留这个语义：只要传的是
本模块的常量对象，就是 ``is`` 成立。

``getExtension`` 只认 5 种图片前缀，其余一律返回空串 —— 上传 ``.txt`` 且请求头
``Content-Type`` 不是图片时，后缀就是 ``""``，然后被白名单拦下。
"""

from __future__ import annotations

from typing import Final, Tuple

#: image/png
IMAGE_PNG: Final[str] = "image/png"
#: image/jpg
IMAGE_JPG: Final[str] = "image/jpg"
#: image/jpeg
IMAGE_JPEG: Final[str] = "image/jpeg"
#: image/bmp
IMAGE_BMP: Final[str] = "image/bmp"
#: image/gif
IMAGE_GIF: Final[str] = "image/gif"

#: 图片后缀（Java: ``String[] IMAGE_EXTENSION``）
IMAGE_EXTENSION: Final[Tuple[str, ...]] = ("bmp", "gif", "jpg", "jpeg", "png")
#: flash 后缀
FLASH_EXTENSION: Final[Tuple[str, ...]] = ("swf", "flv")
#: 媒体后缀
MEDIA_EXTENSION: Final[Tuple[str, ...]] = (
    "swf",
    "flv",
    "mp3",
    "wav",
    "wma",
    "wmv",
    "mid",
    "avi",
    "mpg",
    "asf",
    "rm",
    "rmvb",
)
#: 视频后缀
VIDEO_EXTENSION: Final[Tuple[str, ...]] = ("mp4", "avi", "rmvb")
#: 默认允许上传的文件后缀（顺序与 Java 一致，会出现在错误文案里）
DEFAULT_ALLOWED_EXTENSION: Final[Tuple[str, ...]] = (
    # 图片
    "bmp",
    "gif",
    "jpg",
    "jpeg",
    "png",
    # word excel powerpoint
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "html",
    "htm",
    "txt",
    # 压缩文件
    "rar",
    "zip",
    "gz",
    "bz2",
    # 视频格式
    "mp4",
    "avi",
    "rmvb",
    # pdf
    "pdf",
)


def get_extension(prefix: str) -> str:
    """根据 ``Content-Type`` 反推后缀. Java: ``MimeTypeUtils.getExtension(String prefix)``.

    只覆盖 5 种图片类型，其它（含 ``image/webp``）返回空串。Java 用 ``switch``，对
    ``null`` 会 NPE —— 这里同样不兜底（调用方 ``FileUploadUtils.getExtension`` 已经
    ``requireNonNull`` 过）。
    """
    if prefix == IMAGE_PNG:
        return "png"
    if prefix == IMAGE_JPG:
        return "jpg"
    if prefix == IMAGE_JPEG:
        return "jpeg"
    if prefix == IMAGE_BMP:
        return "bmp"
    if prefix == IMAGE_GIF:
        return "gif"
    return ""


__all__ = [
    "IMAGE_PNG",
    "IMAGE_JPG",
    "IMAGE_JPEG",
    "IMAGE_BMP",
    "IMAGE_GIF",
    "IMAGE_EXTENSION",
    "FLASH_EXTENSION",
    "MEDIA_EXTENSION",
    "VIDEO_EXTENSION",
    "DEFAULT_ALLOWED_EXTENSION",
    "get_extension",
]
