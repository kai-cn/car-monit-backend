"""``MultipartFileUtil`` + 一个内存版 ``MultipartFile``.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/MultipartFileUtil.java

为什么需要它
------------
``SysFileServiceImpl.uploadByUrl`` 先用 Forest 把远端图片下载成 ``byte[]``，再把它
**转成 Spring 的 ``MultipartFile``**，因为下游 ``fileLog()`` / ``ossTemplate.putObject()``
只认这个接口。Python 侧没有 Servlet，于是这里提供一个最小实现 :class:`MockMultipartFile`，
属性形状与 Spring 的 ``MultipartFile`` 对齐：

    ==========================  ==================================================
    Spring                      这里
    ==========================  ==================================================
    ``getOriginalFilename()``   ``.filename``
    ``getContentType()``        ``.content_type``
    ``getName()``               ``.name``（表单字段名，固定 ``"file"``）
    ``getSize()``               ``.size``
    ``isEmpty()``               ``is_empty()`` -> ``.size == 0``
    ``getBytes()``              ``get_bytes()``
    ``getInputStream()``        ``.file``（``BytesIO``，每次**重新**返回新流）
    ==========================  ==================================================

``.file`` 之所以是"每次新流"：本项目的 ``putObject`` 会 ``read`` 到 EOF，而 Java 每次
``getInputStream()`` 都返回一个**新的** ``ByteArrayInputStream``。用同一个流对象会让
第二次读拿到空字节 —— 真实调用链里确实会读两次（``fileLog`` 只看 ``size``，不读流，
但 ``uploadFileId`` 里 ``fileLogId`` 之后还要 ``putObject``），所以必须复刻新流语义。

``FileItem`` / ``DiskFileItemFactory`` 的落盘行为**没有**迁移
-------------------------------------------------------------
Java 用 ``DiskFileItem`` 当载体，只在超过阈值（默认 10KB）时才写临时文件。这些临时文件
在 ``CommonsMultipartFile`` 生命周期结束时并不一定会被清理，属于既有隐患；Python 侧
直接放在内存里，对外可观察的行为（文件名 / 大小 / 内容 / 类型）完全一致。
"""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO, Optional

from app.common.exception.exceptions import CustomException


class MockMultipartFile:
    """内存版 ``MultipartFile``（对应 ``CommonsMultipartFile`` + ``DiskFileItem``）。"""

    def __init__(
        self,
        name: str,
        filename: Optional[str],
        content_type: Optional[str],
        content: bytes,
    ) -> None:
        self.name = name
        self.filename = filename
        self.content_type = content_type
        self.content = content
        #: Java: ``MultipartFile#getSize()`` -> ``long``
        self.size = len(content)

    # Java: getInputStream()
    @property
    def file(self) -> BinaryIO:
        """每次访问都返回**新的** ``BytesIO``，见模块 docstring。"""
        return BytesIO(self.content)

    # Java: isEmpty()
    def is_empty(self) -> bool:
        return self.size == 0

    # Java: getBytes()
    def get_bytes(self) -> bytes:
        return self.content

    def __repr__(self) -> str:  # pragma: no cover - 只为调试可读
        return f"MockMultipartFile(name={self.name!r}, filename={self.filename!r}, size={self.size})"


def convert_byte_to_multipart_file(image_bytes: Optional[bytes], file_name: str) -> MockMultipartFile:
    """Java: ``MultipartFileUtil.convertByteToMultipartFile(byte[], String)``.

    ``contentType`` 写死 ``image/jpeg``（与原版一致，即使实际是 png —— 只有
    ``getContentType()`` 会用到它，而 ``uploadByUrl`` 全程不读这个值）。
    """
    if image_bytes is None:
        raise CustomException("输入 byte 数组为空，转换失败")
    return MockMultipartFile("file", file_name, "image/jpeg", image_bytes)


def convert_input_stream_to_multipart_file(
    input_stream: BinaryIO, file_name: str
) -> MockMultipartFile:
    """Java: ``MultipartFileUtil.convertInputStreamToMultipartFile(InputStream, String)``.

    ``contentType`` 写死 ``text/plain``（原版就是这样）。本项目没有调用者，照留。
    """
    return MockMultipartFile("file", file_name, "text/plain", input_stream.read())


__all__ = [
    "MockMultipartFile",
    "convert_byte_to_multipart_file",
    "convert_input_stream_to_multipart_file",
]
