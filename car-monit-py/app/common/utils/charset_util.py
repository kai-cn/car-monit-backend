"""``CharsetUtil`` 的最小迁移.

# Migrated from: cn.hutool.core.util.CharsetUtil

``SysFileController.uploadFile``（微信小程序上传）用它把 **ISO-8859-1** 的文件名还原成
UTF-8：multipart 解析器按 RFC 7578 把文件名当 latin-1 读，中文名到手上就是乱码，
所以先 ``getBytes(ISO_8859_1)`` 再 ``new String(UTF_8)`` 转回来。

``convert`` 的三处细节
----------------------
1. ``null`` 的 charset 参数分别回退到 ISO-8859-1 / UTF-8（Java 方法体里那两个 if）；
2. ``StrUtil.isBlank(source)`` 为真时**原样返回**（``null`` -> ``null``，``""`` -> ``""``，
   全空白串 -> 原串）；
3. 两个 charset 相同则也是原样返回。

第 3 点意味着"本来就是 UTF-8 的名字"不会被二次解码 —— 这正是 Java 的行为，别优化掉。
"""

from __future__ import annotations

from typing import Optional

#: Java: ``CharsetUtil.CHARSET_ISO_8859_1`` / ``CharsetUtil.CHARSET_UTF_8``
ISO_8859_1: str = "iso-8859-1"
UTF_8: str = "utf-8"


def convert(
    source: Optional[str],
    src_charset: Optional[str] = None,
    dest_charset: Optional[str] = None,
) -> Optional[str]:
    """Java: ``CharsetUtil.convert(String source, Charset srcCharset, Charset destCharset)``.

    ``new String(source.getBytes(src), dest)``：先按源编码取字节，再按目标编码解释。
    Java 对无法映射的字节填 ``U+FFFD``，所以这里用 ``errors="replace"``。
    """
    from app.common.utils.string_utils import is_blank

    if src_charset is None:
        src_charset = ISO_8859_1
    if dest_charset is None:
        dest_charset = UTF_8

    if is_blank(source):
        return source
    if src_charset.lower() == dest_charset.lower():
        return source
    assert source is not None  # is_blank 只对 None / 空白串放行，上面已返回
    return source.encode(_python_codec(src_charset), errors="replace").decode(
        _python_codec(dest_charset), errors="replace"
    )


def _python_codec(java_charset: str) -> str:
    """Java charset 名 -> Python codec 名（本项目只用到这两个）。"""
    normalized = java_charset.strip().lower().replace("_", "-")
    if normalized in ("iso-8859-1", "iso8859-1", "latin-1", "latin1"):
        return "iso-8859-1"
    if normalized in ("utf-8", "utf8"):
        return "utf-8"
    # Java 抛 UnsupportedEncodingException；Python 的 LookupError 落到同一个处理器。
    return normalized


__all__ = ["ISO_8859_1", "UTF_8", "convert"]
