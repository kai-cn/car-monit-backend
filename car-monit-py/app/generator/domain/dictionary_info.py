"""字典信息.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/DictionaryInfo.java

Java 用 ``@Data + @Accessors(chain = true)``，setter 返回 ``this`` 以便链式调用::

    dictionaryInfo.setDictionaryKey(...).setDictionaryKeyCamelCase(...);

Python 没有链式 setter，``GenTableServiceImpl#dictionaryKeyToCamelCase`` 里的那行
改成两次赋值，语义相同。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class DictionaryInfo(DomainModel):
    """Java: ``com.ruoyi.generator.domain.DictionaryInfo``."""

    #: 字典键名称
    dictionary_key: Optional[str] = None
    #: 字典键名称-驼峰形式
    dictionary_key_camel_case: Optional[str] = None


__all__ = ["DictionaryInfo"]
