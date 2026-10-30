"""CDC 配置（Kafka / ES 同步 / 重试）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcConfig.java

Java 是 ``@ConfigurationProperties(prefix = "cdc")``，本工程 ``application.yml`` 里
**没有** ``cdc:`` 这一段，因此所有值都取 Java 字段的默认值。以后要改配置，需在
``application.yml``（或对应 ``.env`` / ``settings.py``）里补 ``cdc.*`` 并在
:func:`get_cdc_config` 里绑定 —— 目前**不做**未经要求的扩展。

:meth:`CdcConfig` 是 :class:`~app.common.core.domain.domain_model.DomainModel`，
所以 ``GET /base/cdc/config`` 返回的 JSON 键名与 Jackson 一致
（``kafka`` / ``esSync`` / ``retry`` / ``bootstrapServers`` / ``consumerGroupId`` …）。
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.common.core.domain.domain_model import DomainModel


class KafkaConfig(DomainModel):
    """Java: ``CdcConfig.KafkaConfig``."""

    #: Bootstrap servers
    bootstrap_servers: str = "localhost:9092"
    #: 消费者组ID
    consumer_group_id: str = "snapshot-flow-cdc-group"
    #: CDC主题名称
    topic: str = "snapshot-flow-cdc"
    #: 自动提交offset
    auto_commit: bool = True
    #: 自动提交间隔(ms)
    auto_commit_interval: int = 1000
    #: 会话超时时间(ms)
    session_timeout: int = 30000
    #: 并发消费者数量
    concurrency: int = 3


class EsSyncConfig(DomainModel):
    """Java: ``CdcConfig.EsSyncConfig``."""

    #: 是否启用ES同步
    enabled: bool = True
    #: 批量写入大小
    batch_size: int = 500
    #: 批量写入间隔(ms) —— Java 是 ``long``
    batch_interval: int = 5000
    #: 异步写入线程数
    async_threads: int = 2


class RetryConfig(DomainModel):
    """Java: ``CdcConfig.RetryConfig``."""

    #: 最大重试次数
    max_attempts: int = 3
    #: 重试间隔(ms) —— Java 是 ``long``
    interval: int = 1000
    #: 重试间隔递增倍数
    multiplier: float = 2.0
    #: 最大重试间隔(ms) —— Java 是 ``long``
    max_interval: int = 30000


class CdcConfig(DomainModel):
    """Java: ``class CdcConfig`` —— ``@ConfigurationProperties(prefix = "cdc")``."""

    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    #: Java 属性名 ``esSync``（``@Data`` 生成的 getter 是 ``getEsSync()``）
    es_sync: EsSyncConfig = Field(default_factory=EsSyncConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)


_CONFIG: Optional[CdcConfig] = None


def get_cdc_config() -> CdcConfig:
    """Java: ``@Autowired CdcConfig cdcConfig``（Spring 单例）."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = CdcConfig()
    return _CONFIG


def reset_cdc_config() -> None:
    """Test helper: drop the cached singleton."""
    global _CONFIG
    _CONFIG = None


__all__ = [
    "KafkaConfig",
    "EsSyncConfig",
    "RetryConfig",
    "CdcConfig",
    "get_cdc_config",
    "reset_cdc_config",
]
