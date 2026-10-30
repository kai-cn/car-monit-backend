"""关联表字段类型枚举.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/util/enumeration/LinkTableFiledTypeEnum.java

Java 是 ``enum``，两个成员各带 ``code`` / ``info`` 两个字段::

    TABLE("10", "表中的字段")
    CUSTOM_FIELD("20", "自定义字段")

``info`` 在 Java 侧只被日志/前端用到，模板没用；``code`` 被
``GenTableServiceImpl#initLinkTableInfo`` 用来把 ``fieldMapString`` 里的条目
分成"表字段 / 自定义字段"两组。所以这两个值必须逐字照抄。

名字里的 ``Filed`` 是 Java 原文的笔误（应为 ``Field``），类名照抄以便追溯。
"""

from __future__ import annotations

from typing import Final


class LinkTableFiledTypeEnum:
    """Java: ``enum LinkTableFiledTypeEnum``."""

    #: 表中的字段
    TABLE: Final[str] = "10"
    #: 自定义字段
    CUSTOM_FIELD: Final[str] = "20"

    #: Java: ``TABLE.getInfo()``
    TABLE_INFO: Final[str] = "表中的字段"
    #: Java: ``CUSTOM_FIELD.getInfo()``
    CUSTOM_FIELD_INFO: Final[str] = "自定义字段"

    @classmethod
    def get_code(cls, member: str) -> str:
        """Java: ``LinkTableFiledTypeEnum.valueOf(name).getCode()`` 的等价便捷方法."""
        return getattr(cls, member)

    @classmethod
    def get_info(cls, member: str) -> str:
        """Java: ``LinkTableFiledTypeEnum.valueOf(name).getInfo()``."""
        return getattr(cls, f"{member}_INFO")


__all__ = ["LinkTableFiledTypeEnum"]
