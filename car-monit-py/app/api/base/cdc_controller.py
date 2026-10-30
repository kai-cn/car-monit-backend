"""CDC 同步管理控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java

8 个映射，全部迁移
------------------
=================================  ===================================  ====================
Java                                Method / Path                        权限点
=================================  ===================================  ====================
``getQueueStatus``                 GET ``/status``                      **无**（登录即可）
``getDeadLetterMessages``          GET ``/dead-letters``                **无**
``getRetryMessages``               GET ``/retry-messages``              **无**
``retryMessage``                   POST ``/retry/{messageId}``          **无**
``retryAllDeadMessages``           POST ``/retry-all``                  **无**
``deleteDeadLetterMessage``        DELETE ``/dead-letters/{messageId}`` **无**
``clearDeadLetterQueue``           DELETE ``/dead-letters/clear``       **无**
``getConfig``                      GET ``/config``                      **无**
=================================  ===================================  ====================

**路由顺序**：``DELETE /dead-letters/clear`` 必须注册在
``DELETE /dead-letters/{messageId}`` **之前**。Spring 的 ``AntPathMatcher`` 让字面量
段天然优先（与声明顺序无关），FastAPI 只按注册顺序匹配；照抄 Java 的声明顺序会把
``clear`` 当成 ``messageId="clear"`` 处理。

**两个 500**：``retryMessage`` 失败走 ``AjaxResult.error(...)``；
``retry-all`` 永远返回成功文案（条数拼在消息里）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.base.service.cdc.cdc_config import CdcConfig, get_cdc_config
from app.base.service.cdc.cdc_sync_service import CdcSyncService, get_cdc_sync_service
from app.base.service.cdc.dead_letter_queue_service import (
    DeadLetterQueueService,
    get_dead_letter_queue_service,
)
from app.common.core.domain.ajax_result import AjaxResult

router = APIRouter(prefix="/base/cdc", tags=["base-cdc"])

_DEAD_LETTER_SERVICE: Optional[DeadLetterQueueService] = None
_SYNC_SERVICE: Optional[CdcSyncService] = None
_CONFIG: Optional[CdcConfig] = None


def _dead_letter_service() -> DeadLetterQueueService:
    global _DEAD_LETTER_SERVICE
    if _DEAD_LETTER_SERVICE is None:
        _DEAD_LETTER_SERVICE = get_dead_letter_queue_service()
    return _DEAD_LETTER_SERVICE


def _sync_service() -> CdcSyncService:
    global _SYNC_SERVICE
    if _SYNC_SERVICE is None:
        _SYNC_SERVICE = get_cdc_sync_service()
    return _SYNC_SERVICE


def _config() -> CdcConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = get_cdc_config()
    return _CONFIG


def reset_cdc_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _DEAD_LETTER_SERVICE, _SYNC_SERVICE, _CONFIG
    _DEAD_LETTER_SERVICE = None
    _SYNC_SERVICE = None
    _CONFIG = None


@router.get("/status", response_model=None)
def get_queue_status() -> AjaxResult:
    """获取CDC队列状态. Java: ``@GetMapping("/status")``.

    Java 用 ``HashMap`` 装这 5 个键，**顺序不确定**（取决于 hash 与扩容）；
    这里按源码 ``put`` 的顺序输出，键集合与值完全一致。
    """
    status: Dict[str, Any] = {
        "retryQueueSize": _dead_letter_service().get_retry_queue_size(),
        "deadLetterQueueSize": _dead_letter_service().get_dead_letter_queue_size(),
        "kafkaTopic": _config().kafka.topic,
        "consumerGroupId": _config().kafka.consumer_group_id,
        "maxRetryAttempts": _config().retry.max_attempts,
    }
    return AjaxResult.success_data(status)


@router.get("/dead-letters", response_model=None)
def get_dead_letter_messages() -> AjaxResult:
    """获取死信队列消息列表. Java: ``@GetMapping("/dead-letters")``."""
    return AjaxResult.success_data(_dead_letter_service().get_dead_letter_messages())


@router.get("/retry-messages", response_model=None)
def get_retry_messages() -> AjaxResult:
    """获取重试队列消息列表. Java: ``@GetMapping("/retry-messages")``."""
    return AjaxResult.success_data(_dead_letter_service().get_retry_messages())


@router.post("/retry/{message_id}", response_model=None)
def retry_message(message_id: str) -> AjaxResult:
    """手动重试指定死信消息. Java: ``@PostMapping("/retry/{messageId}")``."""
    success = _sync_service().retry_message(message_id)
    if success:
        return AjaxResult.success_message("重试成功")
    return AjaxResult.error_message("重试失败，消息不存在或处理失败")


@router.post("/retry-all", response_model=None)
def retry_all_dead_messages() -> AjaxResult:
    """批量重试所有死信消息. Java: ``@PostMapping("/retry-all")``."""
    success_count = _sync_service().retry_all_dead_messages()
    return AjaxResult.success_message(f"批量重试完成，成功 {success_count} 条")


# 注意：必须排在 ``/dead-letters/{message_id}`` 之前（见模块文档的"路由顺序"）。
@router.delete("/dead-letters/clear", response_model=None)
def clear_dead_letter_queue() -> AjaxResult:
    """清空死信队列. Java: ``@DeleteMapping("/dead-letters/clear")``.

    逐条删除（不是 ``DEL cdc:dead:*``）：``getDeadLetterMessages`` 解析失败的那条
    拿不到 ``messageId``，因此**会被漏下** —— Java 同样漏，照抄。
    """
    messages = _dead_letter_service().get_dead_letter_messages()
    for message in messages:
        _dead_letter_service().remove_from_dead_letter_queue(message.message_id)
    return AjaxResult.success_message("已清空死信队列")


@router.delete("/dead-letters/{message_id}", response_model=None)
def delete_dead_letter_message(message_id: str) -> AjaxResult:
    """删除指定死信消息. Java: ``@DeleteMapping("/dead-letters/{messageId}")``."""
    _dead_letter_service().remove_from_dead_letter_queue(message_id)
    return AjaxResult.success_message("删除成功")


@router.get("/config", response_model=None)
def get_config() -> AjaxResult:
    """获取CDC配置信息. Java: ``@GetMapping("/config")``."""
    return AjaxResult.success_data(_config())


__all__ = [
    "router",
    "get_queue_status",
    "get_dead_letter_messages",
    "get_retry_messages",
    "retry_message",
    "retry_all_dead_messages",
    "clear_dead_letter_queue",
    "delete_dead_letter_message",
    "get_config",
    "reset_cdc_controller",
]
