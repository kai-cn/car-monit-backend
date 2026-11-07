"""死信队列服务（CDC 同步失败消息的重试 / 死信存储）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/DeadLetterQueueService.java

Redis 键空间
------------
=======================  ==================================  ==========================
Java 常量                键格式                              TTL
=======================  ==================================  ==========================
``DLQ_RETRY_KEY_PREFIX`` ``cdc:retry:<messageId>``            调用方给（秒）
``DLQ_DLQ_KEY_PREFIX``   ``cdc:dead:<messageId>``             7 天
``DLQ_KEY_PREFIX``       ——                                  **从未使用**（原代码遗留）
=======================  ==================================  ==========================

值都是 ``JSON.toJSONString(message)`` 的**纯文本**（``RedisTemplate<String, String>``），
所以这里用裸 ``redis`` 客户端而不是 :class:`~app.common.core.redis.redis_cache.RedisCache`
（后者会套一层 fastjson2 的类型包装，读出来的东西 Java 侧解析不了）。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from app.base.service.cdc.cdc_message import CdcMessage, parse_cdc_message, to_cdc_json
from app.config.redis_config import get_redis_client

logger = logging.getLogger("app.base.service.cdc")

#: Java 声明了却没有任何调用点的常量 —— 保留，便于与源码逐行对照。
DLQ_KEY_PREFIX = "cdc:dlq:"
DLQ_RETRY_KEY_PREFIX = "cdc:retry:"
DLQ_DLQ_KEY_PREFIX = "cdc:dead:"

#: Java: ``Duration.ofDays(7)`` -> 604800 秒
DEAD_LETTER_TTL_SECONDS = 7 * 24 * 60 * 60


def _java_key(prefix: str, message_id: Optional[str]) -> str:
    """Java 的 ``prefix + messageId`` —— ``null`` 拼成字面量 ``null``."""
    return prefix + ("null" if message_id is None else str(message_id))


class DeadLetterQueueService:
    """Java: ``class DeadLetterQueueService``."""

    def __init__(self, client: Any = None) -> None:
        self._client = client

    @property
    def client(self) -> Any:
        """Java: ``@Autowired RedisTemplate<String, String> redisTemplate``."""
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    # Java: public void addToRetryQueue(CdcMessage message, long delaySeconds)
    def add_to_retry_queue(self, message: CdcMessage, delay_seconds: int) -> None:
        key = _java_key(DLQ_RETRY_KEY_PREFIX, message.message_id)
        self.client.set(key, to_cdc_json(message), ex=delay_seconds)
        logger.info(
            "【死信队列】消息 %s 已加入重试队列，延迟 %s 秒", message.message_id, delay_seconds
        )

    # Java: public void addToDeadLetterQueue(CdcMessage message)
    def add_to_dead_letter_queue(self, message: CdcMessage) -> None:
        key = _java_key(DLQ_DLQ_KEY_PREFIX, message.message_id)
        self.client.set(key, to_cdc_json(message), ex=DEAD_LETTER_TTL_SECONDS)
        logger.error(
            "【死信队列】消息 %s 已加入死信队列，重试次数: %s",
            message.message_id,
            message.retry_count,
        )

    # Java: public List<CdcMessage> getRetryMessages()
    def get_retry_messages(self) -> List[CdcMessage]:
        return self._collect(DLQ_RETRY_KEY_PREFIX, "重试")

    # Java: public void removeFromRetryQueue(String messageId)
    def remove_from_retry_queue(self, message_id: str) -> None:
        self.client.delete(_java_key(DLQ_RETRY_KEY_PREFIX, message_id))
        logger.debug("【死信队列】已从重试队列删除消息: %s", message_id)

    # Java: public List<CdcMessage> getDeadLetterMessages()
    def get_dead_letter_messages(self) -> List[CdcMessage]:
        return self._collect(DLQ_DLQ_KEY_PREFIX, "死信")

    # Java: public void removeFromDeadLetterQueue(String messageId)
    def remove_from_dead_letter_queue(self, message_id: str) -> None:
        self.client.delete(_java_key(DLQ_DLQ_KEY_PREFIX, message_id))
        logger.debug("【死信队列】已从死信队列删除消息: %s", message_id)

    # Java: public long getRetryQueueSize()
    def get_retry_queue_size(self) -> int:
        # ``KEYS`` -> ``SCAN``：死信队列可能很大，不能阻塞 Redis 主线程。
        return len({key for key in self.client.scan_iter(match=DLQ_RETRY_KEY_PREFIX + "*", count=1000)})

    # Java: public long getDeadLetterQueueSize()
    def get_dead_letter_queue_size(self) -> int:
        return len({key for key in self.client.scan_iter(match=DLQ_DLQ_KEY_PREFIX + "*", count=1000)})

    # ---------------------------------------------------------------- helpers

    def _collect(self, prefix: str, label: str) -> List[CdcMessage]:
        """``keys(prefix*)`` -> 逐个 ``get`` -> 解析，解析失败的那条被丢弃。

        Java 用 ``keys.stream().map(...).filter(nonNull).collect(toList())``：
        顺序取决于 Redis ``KEYS`` 的返回顺序（无序），这里保持同样的"无序"语义。
        """
        messages: List[CdcMessage] = []
        for key in self.client.scan_iter(match=prefix + "*", count=1000):
            value = self.client.get(key)
            if value is None:
                continue
            message = parse_cdc_message(value)
            if message is None:
                logger.error("【死信队列】解析%s消息失败: %s", label, key)
                continue
            messages.append(message)
        return messages


_SERVICE: Optional[DeadLetterQueueService] = None


def get_dead_letter_queue_service() -> DeadLetterQueueService:
    """Java: ``@Autowired DeadLetterQueueService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = DeadLetterQueueService()
    return _SERVICE


def reset_dead_letter_queue_service() -> None:
    """Test helper: drop the cached singleton so a fake client can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "DLQ_KEY_PREFIX",
    "DLQ_RETRY_KEY_PREFIX",
    "DLQ_DLQ_KEY_PREFIX",
    "DEAD_LETTER_TTL_SECONDS",
    "DeadLetterQueueService",
    "get_dead_letter_queue_service",
    "reset_dead_letter_queue_service",
]
