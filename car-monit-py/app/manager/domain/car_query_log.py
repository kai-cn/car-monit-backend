"""查询日志对象 car_query_log.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarQueryLog.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``apply_time1`` / ``apply_time2`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarQueryLog(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarQueryLog``."""

    #: 用户ID
    user_id: Optional[str] = None
    #: 用户名称
    user_name: Optional[str] = None
    #: 用户IP
    user_ip: Optional[str] = None
    #: 模块菜单(1轨迹单2门架拍识3门架交易流水)
    model_type: Optional[str] = None
    #: 模块功能(1查看2导出)
    menu_point: Optional[str] = None
    #: 查询条件
    query_condition: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 时间查询 :入口时间
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None


__all__ = ["CarQueryLog"]
