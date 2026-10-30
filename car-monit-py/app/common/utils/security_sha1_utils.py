"""SHA1 摘要工具类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/SecuritySHA1Utils.java

只有一个方法 ``shaEncode``：``MessageDigest.getInstance("SHA")`` + 逐字节 ``& 0xff``
后转小写十六进制。

三个照抄点
----------
1. Java 的 ``"SHA"`` 别名等价于 SHA-1，Python 侧写作 ``"sha1"``；
2. ``Integer.toHexString(val)`` **不带**前导零，所以 Java 显式补了 ``"0"``；
   ``f"{val:02x}"`` 结果一致；
3. Java 在 ``NoSuchAlgorithmException`` 时打印堆栈并返回**空串**（不抛）；
   Python 侧 ``hashlib`` 不会失败，这个分支照抄成 ``except Exception`` 后返回 ``""``。
"""

from __future__ import annotations

import hashlib


# Java: static String shaEncode(String inStr) throws Exception
def sha_encode(in_str: str) -> str:
    """对 ``inStr`` 求 SHA-1，返回 40 位小写十六进制字符串."""
    try:
        digest = hashlib.sha1(in_str.encode("utf-8")).digest()
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { ...; return ""; }
        return ""
    return "".join(f"{value:02x}" for value in digest)


__all__ = ["sha_encode"]
