"""分表配置类.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingConfig.java

``@ConfigurationProperties(prefix = "sharding")`` —— 但 ``application.yml`` 里
**没有** ``sharding:`` 块（只有 ``snapshot.flow.sharding``），所以 Spring 绑定出来的
``tables`` 是空 ``HashMap``，:meth:`getTableConfig` 永远返回
:meth:`create_default_config` 的默认值。

本模块照抄这个事实：``tables`` 默认为空字典，:meth:`get_table_config` 的兜底分支
与 Java 逐字段一致。**不要**把它接到 ``snapshot.flow.sharding`` 上 ——
:class:`~app.base.sharding.sharding_table_util.ShardingTableUtil` 完全不读这个
配置（Java 侧同样不读，它硬编码了 ``MONTHLY`` 前缀 ``ods_rt_szdn_snapshot_flow``）。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional


class ShardingStrategy(str, Enum):
    """Java: ``ShardingConfig.ShardingStrategy``."""

    #: 按月分表
    MONTHLY = "MONTHLY"
    #: 按日分表
    DAILY = "DAILY"
    #: 按季度分表
    QUARTERLY = "QUARTERLY"
    #: 按年分表
    YEARLY = "YEARLY"


class TableShardingConfig:
    """Java: ``ShardingConfig.TableShardingConfig``."""

    def __init__(
        self,
        strategy: ShardingStrategy = ShardingStrategy.MONTHLY,
        sharding_field: str = "snapshottime",
        field_type: str = "DATE",
        table_separator: str = "_",
        auto_create_table: bool = True,
        sync_enabled: bool = True,
        sync_batch_size: int = 1000,
        pre_create_periods: int = 4,
        source_service_bean: Optional[str] = None,
        target_mapper_bean: Optional[str] = None,
    ) -> None:
        self.strategy = strategy
        self.sharding_field = sharding_field
        self.field_type = field_type
        self.table_separator = table_separator
        self.auto_create_table = auto_create_table
        self.sync_enabled = sync_enabled
        self.sync_batch_size = sync_batch_size
        self.pre_create_periods = pre_create_periods
        self.source_service_bean = source_service_bean
        self.target_mapper_bean = target_mapper_bean


class ShardingConfig:
    """Java: ``@Configuration @ConfigurationProperties(prefix = "sharding") ShardingConfig``."""

    def __init__(self, tables: Optional[Dict[str, TableShardingConfig]] = None) -> None:
        #: Java: ``private Map<String, TableShardingConfig> tables = new HashMap<>();``
        self.tables: Dict[str, TableShardingConfig] = tables if tables is not None else {}

    # Java: public TableShardingConfig getTableConfig(String tablePrefix)
    def get_table_config(self, table_prefix: str) -> TableShardingConfig:
        """``tables.getOrDefault(tablePrefix, createDefaultConfig())`` —— 注意 Java 的
        ``getOrDefault`` 是**每次调用都新建**一个默认对象，这里同样不复用实例。
        """
        existing = self.tables.get(table_prefix)
        if existing is not None:
            return existing
        return self.create_default_config()

    # Java: private TableShardingConfig createDefaultConfig()
    def create_default_config(self) -> TableShardingConfig:
        config = TableShardingConfig()
        config.strategy = ShardingStrategy.MONTHLY
        config.sharding_field = "snapshottime"
        config.field_type = "DATE"
        config.table_separator = "_"
        config.auto_create_table = True
        config.sync_enabled = True
        config.sync_batch_size = 1000
        config.pre_create_periods = 4
        return config


__all__ = ["ShardingConfig", "ShardingStrategy", "TableShardingConfig"]
