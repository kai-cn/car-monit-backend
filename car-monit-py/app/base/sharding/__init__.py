"""分表工具包.

# Migrated from: com/ruoyi/base/sharding/

对应 Java 的三个类：

============================  ==================================================
Java                          Python
============================  ==================================================
``ShardingConfig``            :mod:`app.base.sharding.sharding_config`
``ShardingTableUtil``         :mod:`app.base.sharding.sharding_table_util`
``ShardingStrategy``          :class:`~app.base.sharding.sharding_config.ShardingStrategy`
============================  ==================================================
"""

from app.base.sharding.sharding_config import (
    ShardingConfig,
    ShardingStrategy,
    TableShardingConfig,
)
from app.base.sharding.sharding_table_util import ShardingTableUtil

__all__ = [
    "ShardingConfig",
    "ShardingStrategy",
    "ShardingTableUtil",
    "TableShardingConfig",
]
