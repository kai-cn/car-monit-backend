"""CDC 同步服务（Kafka 消费 → ES 同步 → 失败重试 / 死信）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcSyncService.java

**重要：ES 同步在 Java 源码里是注释掉的**
------------------------------------------
``handleInsert`` / ``handleUpdate`` / ``handleDelete`` 三个方法里，
``elasticsearchService.*`` 那行都是 ``//`` 注释状态，方法体实际只打 ``debug`` 日志并
``return true``。也就是说 CDC 消费在本工程里**没有任何外部可观察副作用**。

因此：

* 三个 ``handle*`` 方法逐行照抄（保留注释掉的 ES 调用）；
* Kafka ``@KafkaListener`` **没有**接入驱动（否则要凭空引入 kafka 客户端并决定
  offset 语义）。消费器一旦接入，消息处理链路不需要改 —— 见 ``COMPATIBILITY.md``；
* HTTP 管理端点（``/base/cdc/**``）完整可用，死信队列读的是 Redis 里的既有数据。

引用语义
--------
Java 传的是**对象引用**：``cdcMessage.setRetryCount(...)`` 会改到调用方持有的那个
对象；``retryMessage`` 里 ``message.setRetryCount(0)`` 同样。Python 里
:class:`~app.base.service.cdc.cdc_message.CdcMessage` 是 pydantic 模型（可变），
``message.retry_count = 0`` 效果一致。
"""

from __future__ import annotations

import logging
import math
from typing import Any, List, Optional

from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import OdsRtSzdnSnapshotFlowAddcode
from app.base.service.cdc.cdc_config import CdcConfig, get_cdc_config
from app.base.service.cdc.cdc_message import CdcMessage, OperationType, parse_cdc_message
from app.base.service.cdc.dead_letter_queue_service import (
    DeadLetterQueueService,
    get_dead_letter_queue_service,
)

logger = logging.getLogger("app.base.service.cdc")


class Acknowledgment:
    """Java: ``org.springframework.kafka.support.Acknowledgment`` 的最小替身.

    Java 侧 ``consumeCdcMessage`` 只在三处调用 ``acknowledge()``；Kafka 驱动未接入时
    这份实现什么也不做（offset 由谁提交见 ``COMPATIBILITY.md``）。
    """

    def acknowledge(self) -> None:  # noqa: D401 - 与 Java 同名
        """Java: ``acknowledgment.acknowledge()``."""
        return None


class CdcSyncService:
    """Java: ``class CdcSyncService``."""

    def __init__(
        self,
        dead_letter_queue_service: Optional[DeadLetterQueueService] = None,
        cdc_config: Optional[CdcConfig] = None,
    ) -> None:
        self._dead_letter_queue_service = dead_letter_queue_service
        self._cdc_config = cdc_config

    @property
    def dead_letter_queue_service(self) -> DeadLetterQueueService:
        """Java: ``@Autowired DeadLetterQueueService``."""
        if self._dead_letter_queue_service is None:
            self._dead_letter_queue_service = get_dead_letter_queue_service()
        return self._dead_letter_queue_service

    @property
    def cdc_config(self) -> CdcConfig:
        """Java: ``@Autowired CdcConfig``."""
        if self._cdc_config is None:
            self._cdc_config = get_cdc_config()
        return self._cdc_config

    # Java: @KafkaListener(...) public void consumeCdcMessage(String message, Acknowledgment ack)
    def consume_cdc_message(self, message: str, acknowledgment: Any) -> None:
        """Kafka 消费入口 —— 驱动未接入，方法体与 Java 保持一致以备启用."""
        logger.debug("【CDC消费】收到消息: %s", message)
        try:
            cdc_message = self.parse_cdc_message(message)
            if cdc_message is None:
                logger.warning("【CDC消费】消息解析失败，跳过: %s", message)
                acknowledgment.acknowledge()
                return
            success = self.process_cdc_message(cdc_message)
            if success:
                acknowledgment.acknowledge()
                logger.info("【CDC消费】消息 %s 处理成功", cdc_message.message_id)
            else:
                self.handle_failure(cdc_message)
                acknowledgment.acknowledge()
        except Exception:  # noqa: BLE001 - Java: catch (Exception e) 后照样 ack
            logger.exception("【CDC消费】处理消息异常")
            acknowledgment.acknowledge()

    # Java: private CdcMessage parseCdcMessage(String message)
    def parse_cdc_message(self, message: str) -> Optional[CdcMessage]:
        parsed = parse_cdc_message(message)
        if parsed is None:
            logger.error("【CDC解析】解析消息失败: %s", message)
        return parsed

    # Java: private boolean processCdcMessage(CdcMessage cdcMessage)
    def process_cdc_message(self, cdc_message: CdcMessage) -> bool:
        try:
            operation_type = cdc_message.operation_type
            data = cdc_message.after_data
            if operation_type is OperationType.INSERT:
                return self.handle_insert(data)
            if operation_type is OperationType.UPDATE:
                return self.handle_update(data)
            if operation_type is OperationType.DELETE:
                return self.handle_delete(cdc_message.before_data)
            if operation_type is None:
                # Java: switch(null) -> NullPointerException -> 被 catch 吞掉 -> false
                logger.error("【CDC处理】操作类型为空")
                return False
            logger.warning("【CDC处理】未知操作类型: %s", operation_type)
            return True
        except Exception:  # noqa: BLE001 - Java: catch (Exception e) { return false; }
            logger.exception("【CDC处理】处理消息失败")
            return False

    # Java: private boolean handleInsert(OdsRtSzdnSnapshotFlowAddcode data)
    def handle_insert(self, data: Optional[OdsRtSzdnSnapshotFlowAddcode]) -> bool:
        if data is None:
            logger.warning("【CDC插入】数据为空")
            return True
        try:
            # Java 源码里这行是注释掉的： elasticsearchService.saveOrUpdate(data);
            logger.debug("【CDC插入】成功索引数据: %s", data.big_id)
            return True
        except Exception:  # noqa: BLE001
            logger.exception("【CDC插入】索引失败")
            return False

    # Java: private boolean handleUpdate(OdsRtSzdnSnapshotFlowAddcode data)
    def handle_update(self, data: Optional[OdsRtSzdnSnapshotFlowAddcode]) -> bool:
        if data is None:
            logger.warning("【CDC更新】数据为空")
            return True
        try:
            # Java 源码里这行是注释掉的： elasticsearchService.update(data);
            logger.debug("【CDC更新】成功更新数据: %s", data.big_id)
            return True
        except Exception:  # noqa: BLE001
            logger.exception("【CDC更新】更新失败")
            return False

    # Java: private boolean handleDelete(OdsRtSzdnSnapshotFlowAddcode data)
    def handle_delete(self, data: Optional[OdsRtSzdnSnapshotFlowAddcode]) -> bool:
        if data is None:
            logger.warning("【CDC删除】数据为空")
            return True
        try:
            # Java 源码里这行是注释掉的： elasticsearchService.delete(data.getBigId());
            logger.debug("【CDC删除】成功删除数据: %s", data.big_id)
            return True
        except Exception:  # noqa: BLE001
            logger.exception("【CDC删除】删除失败")
            return False

    # Java: private void handleFailure(CdcMessage cdcMessage)
    def handle_failure(self, cdc_message: CdcMessage) -> None:
        max_attempts = self.cdc_config.retry.max_attempts
        current_attempt = cdc_message.retry_count + 1
        if current_attempt < max_attempts:
            delay = self.calculate_retry_delay(current_attempt)
            cdc_message.retry_count = current_attempt
            self.dead_letter_queue_service.add_to_retry_queue(cdc_message, delay)
            logger.warning(
                "【CDC重试】消息 %s 重试次数 %s，延迟 %s 秒",
                cdc_message.message_id,
                current_attempt,
                delay,
            )
        else:
            cdc_message.retry_count = current_attempt
            self.dead_letter_queue_service.add_to_dead_letter_queue(cdc_message)
            logger.error(
                "【CDC失败】消息 %s 超过最大重试次数 %s，已加入死信队列",
                cdc_message.message_id,
                max_attempts,
            )

    # Java: private long calculateRetryDelay(int attempt)
    def calculate_retry_delay(self, attempt: int) -> int:
        """指数退避：``interval/1000 * multiplier^(attempt-1)``，向下取整并封顶.

        Java 的 ``getInterval() / 1000`` 是**整数除法**（毫秒转秒），
        ```(long)`` 强转是**截断**，两者都不能写成浮点。
        """
        base_interval = self.cdc_config.retry.interval // 1000
        multiplier = self.cdc_config.retry.multiplier
        max_interval = self.cdc_config.retry.max_interval // 1000
        delay = int(base_interval * math.pow(multiplier, attempt - 1))
        return min(delay, max_interval)

    # Java: public boolean retryMessage(String messageId)
    def retry_message(self, message_id: str) -> bool:
        dead_messages: List[CdcMessage] = self.dead_letter_queue_service.get_dead_letter_messages()
        message = next((item for item in dead_messages if item.message_id == message_id), None)
        if message is None:
            logger.warning("【CDC重试】未找到死信消息: %s", message_id)
            return False
        message.retry_count = 0
        success = self.process_cdc_message(message)
        if success:
            self.dead_letter_queue_service.remove_from_dead_letter_queue(message_id)
            logger.info("【CDC重试】死信消息 %s 重试成功", message_id)
            return True
        logger.error("【CDC重试】死信消息 %s 重试失败", message_id)
        return False

    # Java: public int retryAllDeadMessages()
    def retry_all_dead_messages(self) -> int:
        dead_messages: List[CdcMessage] = self.dead_letter_queue_service.get_dead_letter_messages()
        success_count = 0
        for message in dead_messages:
            message.retry_count = 0
            if self.process_cdc_message(message):
                self.dead_letter_queue_service.remove_from_dead_letter_queue(message.message_id)
                success_count += 1
        logger.info(
            "【CDC重试】批量重试完成，成功 %s 条，失败 %s 条",
            success_count,
            len(dead_messages) - success_count,
        )
        return success_count


_SERVICE: Optional[CdcSyncService] = None


def get_cdc_sync_service() -> CdcSyncService:
    """Java: ``@Autowired CdcSyncService``（Spring 单例）."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CdcSyncService()
    return _SERVICE


def reset_cdc_sync_service() -> None:
    """Test helper: drop the cached singleton so fakes can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "Acknowledgment",
    "CdcSyncService",
    "get_cdc_sync_service",
    "reset_cdc_sync_service",
]
