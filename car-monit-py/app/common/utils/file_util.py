"""hutool ``FileUtil`` / ``IoUtil`` 的最小迁移.

# Migrated from: cn.hutool.core.io.FileUtil#extName(String)
# Migrated from: cn.hutool.core.io.IoUtil#copy(InputStream, OutputStream)

只搬 ``SysFileServiceImpl`` / ``SysFileController`` 实际调用的两个方法。hutool 的其余
成员（``readBytes`` / ``writeBytes`` / ``del`` …）随各自的调用方迁移。

``ext_name`` 与 :func:`app.common.utils.file_upload_utils.get_extension` 的关系
-----------------------------------------------------------------------------
一个是 hutool 的 ``FileUtil.extName``，一个是 commons-io 的
``FilenameUtils.getExtension``。**本项目里两者结果一致**，都遵守同一条规则：

* ``"a/b.png"`` -> ``"png"``；
* ``"a.b.png"`` -> ``"png"``（取最后一个点）;
* ``"a.b/c"``   -> ``""``（点在目录上，不算后缀）；
* ``"a."``      -> ``""``；
* ``".bashrc"`` -> ``"bashrc"``；
* ``"a"``       -> ``""``；
* ``None``      -> ``None``（hutool 返回 ``null``；``getExtension`` 也是 ``null``）。
"""

from __future__ import annotations

from typing import BinaryIO, Optional

#: Java: ``StrUtil.DOT``
DOT: str = "."


def ext_name(filename: Optional[str]) -> Optional[str]:
    """扩展名（**不带**点）. Java: ``FileUtil.extName(String``.

    调用点对它做了 ``null != ext && !ext.equals("")`` 的双重判空，所以返回 ``None``
    （而不是 ``""``）与 Java 一致。
    """
    if filename is None:
        return None
    extension_pos = filename.rfind(DOT)
    last_separator = max(filename.rfind("/"), filename.rfind("\\"))
    # Java: 点在目录名上 -> 没有扩展名（``a.b/c`` 的 ``.`` 属于目录 ``a.b``）
    if extension_pos == -1 or last_separator > extension_pos:
        return ""
    return filename[extension_pos + 1 :]


def io_copy(input_stream: BinaryIO, output_stream: BinaryIO, buffer_size: int = 8192) -> int:
    """把输入流整个拷到输出流. Java: ``IoUtil.copy(InputStream, OutputStream)``.

    返回写入的字节数（Java 版本返回 ``long``，调用点都没用返回值）。
    """
    total = 0
    while True:
        chunk = input_stream.read(buffer_size)
        if not chunk:
            break
        output_stream.write(chunk)
        total += len(chunk)
    return total


__all__ = ["DOT", "ext_name", "io_copy"]
