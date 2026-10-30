"""批量按 url 上传的请求体.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/ro/UploadRo.java

Java 只有一个 ``List<UploadByUrlRo> list`` 字段，请求体形如::

    {"list": [{"fileName": "abc", "url": "http://..."}, ...]}

``list`` 是 Python 内建名，但在这里作为 pydantic 字段没问题（属性访问
``upload_ro.list`` 只在实例上生效）。**默认值是 ``None`` 而不是 ``[]``**：
Java 侧没传这个键时 ``getList()`` 返回 ``null``，随后 ``for`` 循环 NPE ->
HTTP 200 + ``code 500``；用 ``[]`` 会静默返回空数组，那是另一种行为。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel
from app.system.domain.ro.upload_by_url_ro import UploadByUrlRo


class UploadRo(DomainModel):
    """Java: ``class UploadRo``."""

    list: Optional[List[UploadByUrlRo]] = None


__all__ = ["UploadRo"]
