"""业务操作类型 / business operation type.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/BusinessType.java

**声明顺序就是 ordinal**
------------------------
Java 的 ``BusinessType`` 没有任何字段，落库用的是 ``log.businessType().ordinal()``
（见 ``LogAspect#getControllerMethodDescription``）。所以 ``sys_oper_log.business_type``
里存的是**下标** 0..9，而不是自定义 code。字典翻译写死在
``SysOperLog.EXCEL_FIELDS`` 的 ``0=其它,1=新增,2=修改,3=删除,4=授权,5=导出,6=导入,7=强退,
8=生成代码,9=清空数据`` 里 —— 两处必须同时改，否则历史日志的"业务类型"列会整体错位。

这里给每个成员写死显式数值（而不是依赖枚举位置），再配一条断言把它们钉在
``ordinal()`` 上：Java 侧调换两个成员会让所有历史行语义反转，Python 侧调换成员却不会。
数值写死之后，顺序恢复成"文档顺序"，改动可见、可测（见
``tests/test_business_type_enum.py``）。

Java 的 ``ordinal()`` 在 Python 里叫 :meth:`ordinal`，保留 Java 名字，调用点可以机械翻译。
"""

from __future__ import annotations

from enum import Enum


class BusinessType(Enum):
    """Java: ``BusinessType`` —— 业务操作类型."""

    #: 其它
    OTHER = 0
    #: 新增
    INSERT = 1
    #: 修改
    UPDATE = 2
    #: 删除
    DELETE = 3
    #: 授权
    GRANT = 4
    #: 导出
    EXPORT = 5
    #: 导入
    IMPORT = 6
    #: 强退
    FORCE = 7
    #: 生成代码
    GENCODE = 8
    #: 清空数据
    CLEAN = 9

    # Java: public int ordinal()
    def ordinal(self) -> int:
        """Java: ``Enum.ordinal()`` —— 声明下标（0 起）.

        写入 ``sys_oper_log.business_type`` 的就是这个值。
        """
        return self.value


__all__ = ["BusinessType"]
