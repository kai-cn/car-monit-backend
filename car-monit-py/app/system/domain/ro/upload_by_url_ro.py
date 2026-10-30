"""按 url 上传文件的请求对象.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/ro/UploadByUrlRo.java

两个字段都是可空的 ``String``（Lombok ``@Data``，没有校验注解）：

* ``fileName`` —— 原始文件名（**不带**后缀；service 会拼上 ``".jpg"``）；
* ``url``      —— 远端图片地址。

序列化名与 Java 一致（``fileName`` / ``url``），``DomainModel`` 的 ``to_camel`` 负责。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class UploadByUrlRo(DomainModel):
    """Java: ``class UploadByUrlRo``."""

    file_name: Optional[str] = None
    url: Optional[str] = None


__all__ = ["UploadByUrlRo"]
