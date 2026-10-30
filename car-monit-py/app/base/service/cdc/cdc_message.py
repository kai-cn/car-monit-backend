"""CDC 消息封装.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcMessage.java

Java 侧是 ``@Data @Builder @NoArgsConstructor @AllArgsConstructor`` 的 POJO，
``operationType`` 是内嵌枚举 ``OperationType``（``INSERT`` / ``UPDATE`` / ``DELETE``），
``timestamp`` 是 ``LocalDateTime``（Jackson 默认按 ISO-8601 输出，
Spring Boot 默认关闭 ``WRITE_DATES_AS_TIMESTAMPS``）。

JSON 序列化规则
---------------
死信队列里存的是 ``JSON.toJSONString(message)``（fastjson2）：
**null 字段不输出**，``retryCount`` 是 ``int`` 原始类型所以恒出现。
:func:`to_cdc_json` 照这个规则输出；:func:`parse_cdc_message` 负责反向解析
（解析失败返回 ``None``，供调用方降级成"跳过这条"）。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import OdsRtSzdnSnapshotFlowAddcode
from app.common.core.domain.domain_model import DomainModel


class OperationType(str, Enum):
    """Java: ``CdcMessage.OperationType``."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class CdcMessage(DomainModel):
    """Java: ``class CdcMessage``."""

    #: 操作类型
    operation_type: Optional[OperationType] = None
    #: 数据源名称
    source_name: Optional[str] = None
    #: 数据库名称
    database: Optional[str] = None
    #: 表名称
    table: Optional[str] = None
    #: 变更前的数据（DELETE 或 UPDATE 操作）
    before_data: Optional[OdsRtSzdnSnapshotFlowAddcode] = None
    #: 变更后的数据（INSERT 或 UPDATE 操作）
    after_data: Optional[OdsRtSzdnSnapshotFlowAddcode] = None
    #: 变更时间
    timestamp: Optional[datetime] = None
    #: 消息唯一标识
    message_id: Optional[str] = None
    #: 重试次数（Java ``int`` 原始类型 —— 恒出现、默认 0）
    retry_count: int = 0


def _drop_none(value: Any) -> Any:
    """递归剔除 ``None`` —— 等价于 fastjson2 ``JSON.toJSONString`` 的默认行为."""
    if isinstance(value, dict):
        return {key: _drop_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value


def to_cdc_json(message: CdcMessage) -> str:
    """Java: ``JSON.toJSONString(message)``."""
    import json

    payload: Dict[str, Any] = _drop_none(message.to_json_dict())
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_cdc_message(text: Optional[str]) -> Optional[CdcMessage]:
    """Java: ``JSON.parseObject(text, CdcMessage.class)`` —— 失败返回 ``None``."""
    import json

    if text is None:
        return None
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return CdcMessage.model_validate(payload)
    except Exception:  # noqa: BLE001 - Java 侧同样 catch 后返回 null
        return None


__all__ = ["OperationType", "CdcMessage", "to_cdc_json", "parse_cdc_message"]
