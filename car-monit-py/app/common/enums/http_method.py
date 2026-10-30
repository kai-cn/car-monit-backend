"""请求方式 / HTTP verb.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/HttpMethod.java

Java 的 ``HttpMethod`` 是一个带静态 ``mappings`` 表（名字 -> 常量）的枚举，
``resolve(name)`` / ``matches(name)`` 都做**名字的精确比较**（``HEAD`` 不匹配 ``GET``）。

Python 的 ``enum.Enum`` 已经有 ``.name``，所以 ``HttpMethod.PUT.name`` 直接就是
``"PUT"`` —— ``LogAspect#setRequestValue`` 里那句
``HttpMethod.PUT.name().equals(requestMethod)`` 可以逐字搬成
``HttpMethod.PUT.name == request_method``。

本工程的实际调用点只有两处，都在日志切面里：
``LogAspect#setRequestValue``（判断要不要序列化入参）。``security_config`` 里的
``antMatchers(HttpMethod.GET, ...)`` 用的是字符串，不动。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional


class HttpMethod(Enum):
    """Java: ``HttpMethod`` —— 请求方式."""

    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"

    # Java: @Nullable public static HttpMethod resolve(@Nullable String method)
    @classmethod
    def resolve(cls, method: Optional[str]) -> Optional["HttpMethod"]:
        """Java: ``HttpMethod.resolve(String)`` —— 名字精确匹配，未知名返回 ``None``."""
        if method is None:
            return None
        return _MAPPINGS.get(method)

    # Java: public boolean matches(String method)
    def matches(self, method: Optional[str]) -> bool:
        """Java: ``HttpMethod.matches(String)``."""
        return self is HttpMethod.resolve(method)


#: Java: ``private static final Map<String, HttpMethod> mappings``
_MAPPINGS: Dict[str, HttpMethod] = {member.name: member for member in HttpMethod}


__all__ = ["HttpMethod"]
