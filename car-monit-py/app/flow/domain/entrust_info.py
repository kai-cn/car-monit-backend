"""流程委派信息 EntrustInfo.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/EntrustInfo.java

这不是一张表，也不会被 MyBatis 读取/写入；它的**唯一用途**是序列化成 JSON 字符串，
塞进 ``flow_apply_info.entrust_info`` 列（见
``FlowCurrentNodeServiceImpl#submitEntrustFlow``）：

    String entrustJson = JSON.toJSONString(Collections.singletonList(entrustInfo));

时间格式两处注解并存
--------------------
    @JSONField(format = "yyyy-MM-dd HH:mm:ss.SS")   <- fastjson2，真正生效
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")    <- Jackson，只有在 Controller
                                                       直接返回 EntrustInfo 时才生效

本工程里 ``EntrustInfo`` 从不进 Controller 返回值，序列化一律由 fastjson2 完成，
所以这里只实现 **fastjson2** 那一份：``"yyyy-MM-dd HH:mm:ss.SS"``。

``SS`` 的位数（实测 ``java.text.SimpleDateFormat``）
--------------------------------------------------
    .123 -> ".123"      .005 -> ".05"       .000 -> ".00"

即最少 2 位、最多 3 位（去掉末尾的 0，但至少保留 2 位）。这不是 ``%f`` 能直接给出的，
所以 :func:`format_operation_time` 手写补零。

时区：``operationTime`` 是 ``LocalDateTime``（无时区），fastjson2 对 LocalDateTime
不会做任何时区换算，序列化 = 原样输出墙上时间。因此这里**不**走
:func:`app.common.utils.json_utils.format_date_time`（那个会把 naive 时间当成
GMT+8 再转 UTC，是 ``@JsonFormat`` 的 Jackson 行为）。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import field_serializer, field_validator

from app.common.core.domain.domain_model import DomainModel
from app.common.utils.json_utils import parse_date_time

#: Java: ``@JSONField(format = "yyyy-MM-dd HH:mm:ss.SS")``
ENTRUST_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss.SS"


def format_operation_time(value: Optional[datetime]) -> Optional[str]:
    """Render a ``LocalDateTime`` the way fastjson2 does for ``yyyy-MM-dd HH:mm:ss.SS``.

    ``None`` stays ``None`` (fastjson2 omits the property entirely on the wire, which is
    :func:`dump_entrust_list`'s job -- here ``None`` only means "no value").
    """
    if value is None:
        return None
    millis = value.microsecond // 1000
    # 最少 2 位、最多 3 位：123 -> "123"，5 -> "05"，0 -> "00"
    fraction = f"{millis:03d}"
    if fraction.endswith("0"):
        fraction = fraction[:2]
    return value.strftime("%Y-%m-%d %H:%M:%S.") + fraction


class EntrustInfo(DomainModel):
    """Java: ``com.ruoyi.flow.domain.EntrustInfo``."""

    #: 操作人id
    operator_user_id: Optional[str] = None
    #: 操作人名称
    operator_user_name: Optional[str] = None
    #: 委托人id
    entrust_user_id: Optional[str] = None
    #: 委托人名称
    entrust_user_name: Optional[str] = None
    #: 流程id, flow_name 表的 id 字段
    flow_id: Optional[str] = None
    #: 流程键, flow_name 表中的 flow_key 字段
    flow_key: Optional[str] = None
    #: 流程模板id, flow_template 表的 id 字段
    flow_template_id: Optional[str] = None
    #: 操作时间
    operation_time: Optional[datetime] = None

    # Java: @JSONField(format = "yyyy-MM-dd HH:mm:ss.SS")
    @field_serializer("operation_time")
    def _serialize_operation_time(
        self, value: Optional[datetime], _info: Any
    ) -> Optional[str]:
        return format_operation_time(value)

    @field_validator("operation_time", mode="before")
    @classmethod
    def _parse_operation_time(cls, value: Any) -> Optional[datetime]:
        """接受 fastjson2 写出的 ``"yyyy-MM-dd HH:mm:ss.SS"``（也兼容 3 位毫秒）。

        fastjson2 的 ``parseArray`` 遇到 ``.SS`` 只解析 2 位毫秒；这里用
        :func:`parse_date_time` 宽松解析后**保留墙上时间**（``LocalDateTime`` 语义），
        不经历任何时区换算。
        """
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        parsed = parse_date_time(value)
        return parsed


def dump_entrust_list(infos: List[EntrustInfo]) -> str:
    """Java: ``JSON.toJSONString(Collections.singletonList(entrustInfo))``.

    fastjson2 默认**不输出** ``null`` 属性（未开启 ``WriteMapNullValue``），
    且输出紧凑格式（``,`` / ``:`` 后无空格、中文不转义）。
    :func:`app.common.utils.json_utils.to_json_string` 走的是 ``model_dump``（保留 null），
    所以这里单独逐项剔除 ``None``。
    """
    payload: List[Dict[str, Any]] = []
    for info in infos:
        row = info.model_dump(by_alias=True, mode="json")
        payload.append({key: item for key, item in row.items() if item is not None})
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


__all__ = ["EntrustInfo", "ENTRUST_TIME_PATTERN", "format_operation_time", "dump_entrust_list"]
