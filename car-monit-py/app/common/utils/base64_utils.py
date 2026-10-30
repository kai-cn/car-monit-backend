"""Base64 工具类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/sign/Base64.java

RuoYi ships a hand-written Base64 codec (`com.ruoyi.common.utils.sign.Base64`) instead of
using ``java.util.Base64``. It implements the **standard** RFC 4648 alphabet -- ``A-Z a-z 0-9
+ /`` with ``=`` padding, no line breaks -- which is exactly what ``base64.b64encode``
produces, so the Python port is a one-line delegation.

That equivalence is the point: ``CaptchaController`` puts this string into
``AjaxResult["img"]`` and the Vue client feeds it straight into ``data:image/gif;base64,``.
A URL-safe alphabet (``-``/``_``) or wrapped lines would break every browser.

The Java class also returns ``null`` for ``null`` input and ``""`` for an empty array; both
are reproduced because callers test for ``null``.
"""

from __future__ import annotations

import base64
from typing import Optional

#: Java: ``private static final char PAD = '='`` -- kept as documentation of the alphabet.
PAD = "="


# Java: public static String encode(byte[] binaryData)
def encode(binary_data: Optional[bytes]) -> Optional[str]:
    """Standard Base64 with padding; ``None`` in, ``None`` out."""
    if binary_data is None:
        return None
    if len(binary_data) == 0:
        return ""
    return base64.b64encode(binary_data).decode("ascii")


# Java: public static byte[] decode(String encoded)
def decode(encoded: Optional[str]) -> Optional[bytes]:
    """Standard Base64; ``None`` for ``None``, for a bad length, or for stray characters.

    Java returns ``null`` (not an exception) on malformed input, and skips whitespace first.
    ``base64.b64decode(..., validate=True)`` reproduces the "reject junk" behaviour.
    """
    if encoded is None:
        return None
    compact = "".join(ch for ch in encoded if ch not in " \r\n\t")
    if len(compact) % 4 != 0:
        return None
    if len(compact) == 0:
        return b""
    try:
        return base64.b64decode(compact, validate=True)
    except Exception:  # noqa: BLE001 - Java returns null instead of throwing
        return None


__all__ = ["PAD", "encode", "decode"]
