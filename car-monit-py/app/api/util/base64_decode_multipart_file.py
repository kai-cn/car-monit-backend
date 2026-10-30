"""base64 -> ``MultipartFile`` 的适配器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/Base64DecodeMultipartFile.java

调用点只有一处：``SysFileController.uploadFileId``，它把前端传的 ``data:image/png;base64,xxx``
串转成 ``MultipartFile`` 再走 ``sysFileService.uploadFileId``。

``base64Convert`` 的三处必须照抄的地方
------------------------------------
1. **按第一个逗号切分**：``base64.split(",")`` 取 ``[0]`` 当 header、``[1]`` 当正文。
   没有逗号 -> ``ArrayIndexOutOfBoundsException`` -> HTTP 200 + ``code 500``
   （Python 侧 ``split(",")[1]`` 抛 ``IndexError``，同一个处理器）；
2. **用的是 ``sun.misc.BASE64Decoder``**，也就是 MIME 解码器：**跳过**所有非法字符、
   允许缺失 ``=`` 补齐。``base64.b64decode(validate=False)`` 跳过非法字符，
   这里再手工补 ``=``，两者行为一致；
3. 解析失败时 Java ``catch (IOException) { printStackTrace(); }`` —— 也就是说
   **吞掉异常**，``b`` 保持空数组，随后 ``isEmpty() == true``、``getSize() == 0``。
   结果是一个 0 字节的文件被正常写库。

``getOriginalFilename()`` 里的 ``(int) Math.random() * 10000`` 是**既有 bug**
----------------------------------------------------------------------------
Java 写的是 ``(int) Math.random() * 10000``（强转在乘之前），``(int) Math.random()``
恒为 ``0``，所以文件名永远是 ``<毫秒时间戳>0.<后缀>``。**不要**改成
``(int) (Math.random() * 10000)`` —— 改了就是改了行为（何况客户端只从中取后缀）。
"""

from __future__ import annotations

import base64
import binascii
import time
from io import BytesIO
from typing import BinaryIO, List, Optional


class Base64DecodeMultipartFile:
    """Java: ``class Base64DecodeMultipartFile implements MultipartFile``."""

    def __init__(self, img_content: Optional[bytes], header: str) -> None:
        self._img_content = img_content
        # Java: this.header = header.split(";")[0];
        self.header = header.split(";")[0]

    # Java: getName()
    def get_name(self) -> str:
        """``System.currentTimeMillis() + Math.random() + "." + ext`` —— 注意是**字符串拼接**。"""
        return f"{_current_time_millis()}{_random()}.{self._header_extension()}"

    # Java: getOriginalFilename()
    @property
    def filename(self) -> str:
        # Java: System.currentTimeMillis() + (int) Math.random() * 10000 + "." + ext
        return f"{_current_time_millis()}0.{self._header_extension()}"

    # Java: getContentType()
    @property
    def content_type(self) -> str:
        # Java: header.split(":")[1]
        return self.header.split(":")[1]

    # Java: isEmpty()
    def is_empty(self) -> bool:
        return self._img_content is None or len(self._img_content) == 0

    # Java: getSize()
    @property
    def size(self) -> int:
        return len(self._img_content or b"")

    # Java: getBytes()
    def get_bytes(self) -> Optional[bytes]:
        return self._img_content

    # Java: getInputStream()
    @property
    def file(self) -> BinaryIO:
        """每次访问返回**新的** ``BytesIO``（Java 每次 new 一个 ``ByteArrayInputStream``）。"""
        return BytesIO(self._img_content or b"")

    # Java: transferTo(File dest)
    def transfer_to(self, dest: str) -> None:
        with open(dest, "wb") as handle:
            handle.write(self._img_content or b"")

    def _header_extension(self) -> str:
        """Java: ``header.split("/")[1]``."""
        return self.header.split("/")[1]

    def __repr__(self) -> str:  # pragma: no cover - 只为调试可读
        return f"Base64DecodeMultipartFile(header={self.header!r}, size={self.size})"


def base64_convert(base64_text: str) -> Base64DecodeMultipartFile:
    """Java: ``Base64DecodeMultipartFile.base64Convert(String base64)``."""
    base_strs: List[str] = base64_text.split(",")

    decode_error: Optional[Exception] = None
    decoded = b""
    try:
        decoded = _decode_buffer(base_strs[1])
    except (binascii.Error, ValueError) as exc:
        # Java: catch (IOException e) { e.printStackTrace(); } —— 吞掉，b 保持空数组
        decode_error = exc

    if decode_error is not None:
        decoded = b""

    return Base64DecodeMultipartFile(decoded, base_strs[0])


def _decode_buffer(payload: str) -> bytes:
    """``sun.misc.BASE64Decoder#decodeBuffer`` —— MIME 宽松解码（跳非法字符、补 ``=``）。"""
    # 换行 / 空格 / 其它非字母表字符由 validate=False 跳过；这里只负责补足 padding。
    padded = payload + "=" * (-len(payload.replace("\r", "").replace("\n", "")) % 4)
    return base64.b64decode(padded, validate=False)


def _current_time_millis() -> int:
    """Java: ``System.currentTimeMillis()``."""
    return int(time.time() * 1000)


def _random() -> float:
    """Java: ``Math.random()``."""
    import random

    return random.random()


__all__ = ["Base64DecodeMultipartFile", "base64_convert"]
