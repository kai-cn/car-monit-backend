"""读取代码生成相关配置.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/config/GenConfig.java
# Migrated from: ruoyi-generator/src/main/resources/generator.yml

Java 用 ``@PropertySource("classpath:generator.yml")`` + ``@Value("${author}")`` 把
``generator.yml`` 里的四个键注入到 **静态字段**（注意是 ``public static String author``），
``GenUtils#initTable`` 直接读静态 getter。这里保持"全局可变单例"的语义：

    ``GenConfig.AUTHOR`` / ``PACKAGE_NAME`` / ``AUTO_REMOVE_PRE`` / ``TABLE_PREFIX``

为什么不用 :mod:`app.settings`
-----------------------------
``generator.yml`` 在 Java 里是 ``ruoyi-generator`` 模块**自带**的资源，不属于
``application.yml``；而且它是"生成器自己的偏好"，改它不该影响任何别的配置。
放进 ``settings.py`` 会让"配置文件与类一一对应"这条约定失效，所以单独一个模块。

一个照抄点
----------
Java 里的键是 ``author`` / ``packageName`` / ``autoRemovePre`` / ``tablePrefix``
（**没有** ``gen.`` 前缀 —— ``@ConfigurationProperties(prefix = "gen")`` 与
``@Value`` 同时存在，实际生效的是 ``@Value`` 的顶层键）。所以这里读的是
``generator.yml`` 顶层，而不是 ``gen`` 子节点。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.settings import CONFIG_DIR

#: Java: ``@PropertySource(value = {"classpath:generator.yml"})``
GENERATOR_YML: Path = CONFIG_DIR / "generator.yml"

#: 配置文件的兜底值 —— 与 ``generator.yml`` 当前内容一致。
#: 文件缺失时 Java 会因 ``@Value`` 解析失败而**启动失败**；这里选择用兜底值启动，
#: 差异记录在 COMPATIBILITY.md（生成器不是核心链路，不该拖垮整个服务）。
_DEFAULTS: Dict[str, Any] = {
    "author": "ruoyi",
    "packageName": "com.ruoyi.manager",
    "autoRemovePre": False,
    "tablePrefix": "sys_",
}


def _load() -> Dict[str, Any]:
    """读 ``generator.yml``；与 Java ``@PropertySource`` 一样只取顶层键."""
    values = dict(_DEFAULTS)
    if not GENERATOR_YML.exists():
        return values
    with GENERATOR_YML.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        return values
    for key in _DEFAULTS:
        if key in loaded and loaded[key] is not None:
            values[key] = loaded[key]
    return values


class GenConfig:
    """Java: ``com.ruoyi.generator.config.GenConfig`` —— 四个静态字段."""

    #: 作者
    AUTHOR: str = str(_DEFAULTS["author"])
    #: 生成包路径
    PACKAGE_NAME: str = str(_DEFAULTS["packageName"])
    #: 自动去除表前缀，默认是false
    AUTO_REMOVE_PRE: bool = bool(_DEFAULTS["autoRemovePre"])
    #: 表前缀(类名不会包含表前缀)
    TABLE_PREFIX: str = str(_DEFAULTS["tablePrefix"])

    @classmethod
    def reload(cls) -> None:
        """重新读配置文件（Java 只在启动时注入一次，这里供测试用）."""
        values = _load()
        cls.AUTHOR = str(values["author"])
        cls.PACKAGE_NAME = str(values["packageName"])
        cls.AUTO_REMOVE_PRE = bool(values["autoRemovePre"])
        cls.TABLE_PREFIX = str(values["tablePrefix"])

    # Java 的静态 getter
    @classmethod
    def get_author(cls) -> str:
        """Java: ``static String getAuthor()``."""
        return cls.AUTHOR

    @classmethod
    def get_package_name(cls) -> str:
        """Java: ``static String getPackageName()``."""
        return cls.PACKAGE_NAME

    @classmethod
    def get_auto_remove_pre(cls) -> bool:
        """Java: ``static boolean getAutoRemovePre()``."""
        return cls.AUTO_REMOVE_PRE

    @classmethod
    def get_table_prefix(cls) -> Optional[str]:
        """Java: ``static String getTablePrefix()``."""
        return cls.TABLE_PREFIX


GenConfig.reload()

__all__ = ["GenConfig", "GENERATOR_YML"]
