"""``com.ruoyi.common.annotation`` 包 —— 注解的 Python 等价物（类变量 + 数据类）.

Java 的注解是编译期元数据；Python 没有注解，本包把每个注解落成一个
``frozen dataclass``，由各实体类以 ``ClassVar`` 的形式声明，读取方（mapper /
``ExcelUtil`` / 校验器）按名字取值。一一对应关系：

    com.ruoyi.common.annotation.Excel    -> app.common.annotation.excel.Excel
    com.ruoyi.common.annotation.Excels   -> app.common.annotation.excel.Excels（Tuple 别名）
    com.ruoyi.common.annotation.Log      -> app.common.annotation.log.Log
                                            （装饰器见 app.framework.aspectj.log_aspect）
    com.ruoyi.common.annotation.RepeatSubmit
                                         -> app.common.annotation.repeat_submit.RepeatSubmit
                                            （拦截器见 app.framework.interceptor）
    com.ruoyi.common.annotation.DataScope / DataSource / RateLimiter / Sensitive / Anonymous
                                         -> 未迁移（对应切面 / 拦截器尚未迁移）
                                            ``DataScope`` 的语义已由
                                            ``app.framework.aspectj.data_scope_aspect`` 承担，
                                            但它没有注解实体（显式函数调用），故不在此处。
"""

from __future__ import annotations

from app.common.annotation.excel import (
    BLACK,
    GREY_50_PERCENT,
    WHITE,
    ColumnType,
    Excel,
    ExcelField,
    ExcelFields,
    ExcelHandlerAdapter,
    Excels,
    HorizontalAlignment,
    IndexedColor,
    Type,
)
from app.common.annotation.log import Log
from app.common.annotation.repeat_submit import RepeatSubmit

__all__ = [
    "BLACK",
    "ColumnType",
    "Excel",
    "ExcelField",
    "ExcelFields",
    "ExcelHandlerAdapter",
    "Excels",
    "GREY_50_PERCENT",
    "HorizontalAlignment",
    "IndexedColor",
    "Log",
    "RepeatSubmit",
    "Type",
    "WHITE",
]
