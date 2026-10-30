"""操作人类别 / operator category.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/OperatorType.java

与 :mod:`app.common.enums.business_type` 同理：落库的是 ``ordinal()``
（``sys_oper_log.operator_type``，字典 ``0=其它,1=后台用户,2=手机端用户``）。
本工程没有任何 ``@Log(operatorType = ...)`` 用法 —— 218 处注解全部取默认值
``MANAGE``，所以这一列永远是 ``1``；枚举照搬是为了让注解默认值有出处。
"""

from __future__ import annotations

from enum import Enum


class OperatorType(Enum):
    """Java: ``OperatorType`` —— 操作人类别."""

    #: 其它
    OTHER = 0
    #: 后台用户
    MANAGE = 1
    #: 手机端用户
    MOBILE = 2

    # Java: public int ordinal()
    def ordinal(self) -> int:
        """Java: ``Enum.ordinal()`` —— 声明下标（0 起）."""
        return self.value


__all__ = ["OperatorType"]
