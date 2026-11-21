"""转义和反转义工具类 / the subset of Java ``EscapeUtil`` used by this project.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/html/EscapeUtil.java

Java 的 ``EscapeUtil`` 有三个入口：

* ``escape`` / ``unescape`` —— ``%xx`` / ``%uxxxx`` 形式的编码与解码；
* ``clean`` —— ``new HTMLFilter().filter(content)``，``XssFilter`` 用的就是它。

本项目只迁 ``clean``：另外两个在 Python 侧没有调用点，迁过来只会变成未测试的死代码。
``clean`` 的行为完全由 :mod:`app.common.utils.html_filter` 负责，每次调用新建一个
``HTMLFilter``（与 Java ``EscapeUtil.clean`` 的 ``new HTMLFilter()`` 一致，保证
``vTagCounts`` 不跨调用残留）。
"""

from __future__ import annotations

from app.common.utils.html_filter import HTMLFilter


def clean(content: str) -> str:
    """清除 HTML 标签并保留白名单标签. Java: ``EscapeUtil.clean(String)``."""
    return HTMLFilter().filter(content)


__all__ = ["clean"]
