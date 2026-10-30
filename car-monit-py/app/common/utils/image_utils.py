"""图片工具类 / image helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/ImageUtils.java

只迁了本工程实际用到的两个成员：

* :data:`IMAGE_EXTENSION` —— 7 个图片后缀（**小写**）；
* :func:`is_image` —— ``equalsIgnoreCase`` 比较，所以 ``"JPG"`` / ``"jpg"`` 都算图片。

``getImage(String imagePath)`` / ``getImageBytes`` / ``getImageBase64`` 依赖
``classpath:`` 路径与 Tomcat 的临时目录，本工程没有任何调用点，故未迁移 ——
如果后续需要，再按 Java 原文补齐，**不要**先写个"差不多能用"的近似实现。
"""

from __future__ import annotations

from typing import Final, Optional, Tuple

#: Java: ``public static final String[] IMAGE_EXTENSION = {"bmp","gif","jpg","jpeg","png","webp","svg"}``
IMAGE_EXTENSION: Final[Tuple[str, ...]] = (
    "bmp",
    "gif",
    "jpg",
    "jpeg",
    "png",
    "webp",
    "svg",
)

#: 后缀 -> ``docx`` 图片所需的 MIME（``svg`` 在 Word 里不被支持，退化成 png 声明）。
_CONTENT_TYPES = {
    "bmp": "image/bmp",
    "gif": "image/gif",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}


# Java: static boolean isImage(String extension)
def is_image(extension: Optional[str]) -> bool:
    """``extension`` 是否是图片后缀（忽略大小写）.

    Java 的 ``str.equalsIgnoreCase(extension)`` 在 ``extension == null`` 时返回
    ``false``（不会 NPE），这里保持一致。
    """
    if extension is None:
        return False
    return extension.lower() in IMAGE_EXTENSION


def content_type_of(extension: Optional[str]) -> str:
    """后缀 -> MIME；未知后缀退化成 ``image/png``."""
    if extension is None:
        return "image/png"
    return _CONTENT_TYPES.get(extension.lower(), "image/png")


__all__ = ["IMAGE_EXTENSION", "content_type_of", "is_image"]
