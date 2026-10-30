"""操作状态 / operation status.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/BusinessStatus.java

落库同样是 ``ordinal()``：``sys_oper_log.status`` 的 ``0=正常,1=异常``。

**注意**：这里的 "FAIL" 指的是**抛出异常**，不是"业务失败"。控制器 ``return
AjaxResult.error(...)`` 走的是 ``@AfterReturning``，状态仍然是 ``SUCCESS(0)``。
已用真实请求在 Java 侧验证过（新增同名岗位 -> ``{"code":500}``，而
``sys_oper_log.status`` 仍是 0、``error_msg`` 为 null）。不要"顺手修正"成按
``AjaxResult.code`` 判定。
"""

from __future__ import annotations

from enum import Enum


class BusinessStatus(Enum):
    """Java: ``BusinessStatus`` —— 操作状态."""

    #: 成功
    SUCCESS = 0
    #: 失败
    FAIL = 1

    # Java: public int ordinal()
    def ordinal(self) -> int:
        """Java: ``Enum.ordinal()`` —— 声明下标（0 起）."""
        return self.value


__all__ = ["BusinessStatus"]
