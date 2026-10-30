"""路网路径查询入参（``PathQueryRo``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/PathQueryRo.java

Java 里 ``limit`` / ``page`` / ``pageSize`` 已被注释掉，这里不保留。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel


class PathQueryRo(DomainModel):
    """Java: ``com.ruoyi.base.domain.PathQueryRo``."""

    #: 节点编码序列（起点 … 终点）
    node_ids: Optional[List[str]] = None
    #: 路径策略，固定为 ``SHORTEST``
    path_type: Optional[str] = None
    #: 是否返回坐标，固定为 ``TRUE``
    include_coordinates: Optional[str] = None
    #: 查询模式，固定为 ``LENIENT``
    query_mode: Optional[str] = None


__all__ = ["PathQueryRo"]
