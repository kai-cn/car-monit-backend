"""参数配置表 sys_config.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysConfig.java

放在 ``app/system/domain`` 而不是 ``app/common/core/domain/entity``
-------------------------------------------------------------------
与 ``SysDictType`` 相反：``SysConfig`` 在 Java 里声明于 ``ruoyi-system`` 的
``domain`` 包（``SysNotice`` 也在同一位置），因为 ``ruoyi-common`` 不需要引用它。
目录位置照抄。

只有 5 个自有字段
-----------------
``configId`` / ``configName`` / ``configKey`` / ``configValue`` / ``configType``。
其余（``createBy`` / ``createTime`` / ``updateBy`` / ``updateTime`` / ``remark`` /
``params``）全部来自 :class:`app.common.core.domain.base_entity.BaseEntity`。

``configType`` 的语义
--------------------
``Y`` = 系统内置，``N`` = 非内置。**只有 ``Y`` 被保护**：``deleteConfigByIds``
遇到 ``Y`` 会抛 ``CustomException``（见 service）。列表/详情接口不区分。

``CONFIG_CONSTRAINTS``
----------------------
Java 把 ``@NotBlank`` / ``@Size`` 挂在 **getter** 上，由 ``SysConfigController`` 的
``@Validated @RequestBody`` 触发（``add`` / ``edit``）。顺序与源码一致：
``getConfigName`` -> ``getConfigKey`` -> ``getConfigValue``，这个顺序决定多字段
同时违规时客户端看到的那条 ``msg``。

三条文案里的坑，全部照抄：

* ``configKey`` 的 ``@NotBlank`` 文案是 **"参数键名长度不能为空"** —— 多写了"长度"
  （对比 ``configName`` 的"参数名称不能为空"）；
* 三个 ``@Size`` 的 ``max`` 分别是 100 / 100 / 500，文案分别是
  "参数名称不能超过100个字符" / "参数键名长度不能超过100个字符" /
  "参数键值长度不能超过500个字符"；
* ``configType`` **一个约束都没有** —— 传 ``"X"`` 也能入库。
"""

from __future__ import annotations

from typing import ClassVar, Optional, Tuple

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysConfig(BaseEntity):
    """参数配置表 sys_config."""

    #: 参数主键
    config_id: Optional[int] = None
    #: 参数名称
    config_name: Optional[str] = None
    #: 参数键名（唯一，缓存键就是它）
    config_key: Optional[str] = None
    #: 参数键值
    config_value: Optional[str] = None
    #: 系统内置（Y是 N否）—— 只有 ``Y`` 受删除保护
    config_type: Optional[str] = None

    #: ``@Excel`` 注解表（五个字段的量词与 Java 逐字一致）。
    #: ``BaseEntity`` 上一句 ``@Excel`` 都没有，所以这里就是全部列。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("config_id", Excel(name="参数主键", cell_type=ColumnType.NUMERIC)),
        ("config_name", Excel(name="参数名称")),
        ("config_key", Excel(name="参数键名")),
        ("config_value", Excel(name="参数键值")),
        ("config_type", Excel(name="系统内置", read_converter_exp="Y=是,N=否")),
    )


#: ``@Validated @RequestBody SysConfig`` 的校验项，顺序与 Java 里 getter 的声明顺序一致。
CONFIG_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "参数名称不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("config_name", "参数名称不能为空"),
    Size("config_name", max=100, message="参数名称不能超过100个字符"),
    # Java: @NotBlank(message = "参数键名长度不能为空") @Size(min = 0, max = 100, ...)
    # 注意 "长度" 两个字是原文（@NotBlank 的文案里也带着）
    NotBlank("config_key", "参数键名长度不能为空"),
    Size("config_key", max=100, message="参数键名长度不能超过100个字符"),
    # Java: @NotBlank(message = "参数键值不能为空") @Size(min = 0, max = 500, ...)
    NotBlank("config_value", "参数键值不能为空"),
    Size("config_value", max=500, message="参数键值长度不能超过500个字符"),
    # configType 没有任何约束
)


__all__ = ["SysConfig", "CONFIG_CONSTRAINTS"]
