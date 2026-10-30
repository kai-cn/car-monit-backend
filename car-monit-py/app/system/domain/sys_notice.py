"""通知公告表 sys_notice.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysNotice.java

``SysNotice`` 在 Java 里 ``extends BaseEntity``，所以 JSON 里同样携带
``createBy`` / ``createTime`` / ``updateBy`` / ``updateTime`` / ``remark``，
以及 ``@JsonInclude(NON_EMPTY)`` 的 ``params``（为空时不输出）。

**没有校验注解**
--------------
Java 的 ``SysNoticeController`` 在 ``add`` / ``edit`` 上写了 ``@Validated``，但实体
**一个约束注解都没有**（没有 ``@NotBlank`` / ``@Size``），所以 ``@Validated`` 实际什么都不做。
Python 侧因此没有 ``NOTICE_CONSTRAINTS`` —— 不要凭空加一堆"公告标题不能为空"，
那会让空标题从"能入库"变成 `code 500`。

``noticeContent`` 是 ``longtext``
-------------------------------
XML 的 ``selectNoticeVo`` 用 ``cast(t.notice_content as char) as notice_content`` 取这一列
（见 :mod:`app.system.mapper.sys_notice_mapper`）；实体这边只是普通字符串。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.base_entity import BaseEntity


class SysNotice(BaseEntity):
    """通知公告表 sys_notice."""

    #: 公告ID
    notice_id: Optional[int] = None
    #: 公告标题
    notice_title: Optional[str] = None
    #: 公告类型（1通知 2公告）—— 服务层**强制**写成 ``"1"``，见 service
    notice_type: Optional[str] = None
    #: 公告内容（longtext）
    notice_content: Optional[str] = None
    #: 公告状态（0正常 1关闭）
    status: Optional[str] = None
    #: 业务id
    buss_id: Optional[str] = None
    #: 业务名称
    buss_name: Optional[str] = None
    #: 租户id（列表 SQL 里会额外放行 ``100``，见 mapper）
    tenant_id: Optional[int] = None


__all__ = ["SysNotice"]
