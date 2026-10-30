"""公告 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysNoticeService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysNoticeServiceImpl.java

``ISysNoticeService`` 共 7 个方法，本模块**全部迁移**。

7 个方法里有 4 个是一行转发，真正有行为的是下面三处 —— 它们都是
"服务层**覆盖**控制器刚写好的字段"：

``insertNotice``
    ::

        notice.setNoticeType("1");
        notice.setCreateBy(SecurityUtils.getUserId() + "");   // 注意：覆盖
        notice.setTenantId(SecurityUtils.getTenantId());

    控制器 ``add`` 里刚写过 ``notice.setCreateBy(getUsername())``，紧接着就在这里
    被改写成 **userId 的字符串**。所以 ``sys_notice.create_by`` 里存的是 ``"1"``
    而不是 ``"admin"`` —— 与其它模块（存 userName）**不一致**，是 Java 原样。
    另外 ``noticeType`` 被强制成 ``"1"``，前端传 ``"2"``（公告）也会变成通知。

``updateNotice``
    ``updateBy`` 同样被覆盖成 userId 字符串。方法体里原本还有一段
    "处理富文本中的图片信息"（``fileService.uploadBase64Picture(...)``），
    在 Java 源码里已经**整段注释掉**，所以这里也不做任何处理
    （:class:`app.system.service.sys_file_service` 的对应能力与本切片无关）。

``addDeliveryTimeAbnormal``
    "内容相同的不重复新增"：先按入参当条件查一遍列表，
    查不到才插入，查到就把已有那条的 id 返回。
    **这个方法在 Java 里没有任何调用方**（没有控制器映射、没有定时任务引用），
    按迁移原则第 4 条照搬，并在 ``COMPATIBILITY.md`` 里标记为"死代码"。

    两点细节：

    1. 它直接调 ``noticeMapper.insertNotice``，**不经过** :meth:`insert_notice`
       —— 少了一次 ``noticeType`` 以外的覆盖，但这里手工补齐了
       ``createBy`` / ``tenantId`` / ``noticeType`` / ``status``，结果一致。
    2. ``selectNoticeList(notice)`` 是**分页点**（mapper 里 ``take_page()``）。
       在 Java 里这条路径没有 ``startPage()``，PageHelper 的 thread-local 为
       ``null`` 所以不分页；Python 侧 ``take_page()`` 取到 ``None`` 也不分页，
       行为一致。但如果将来有调用方先 ``start_page()`` 再调这里，
       分页会被这条 select 吃掉（PageHelper 的语义就是这样）。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.common.utils import security_utils as SecurityUtils
from app.system.domain.sys_notice import SysNotice
from app.system.mapper.sys_notice_mapper import SysNoticeMapper


class SysNoticeService:
    """Java: ``ISysNoticeService`` (impl: ``SysNoticeServiceImpl``)."""

    def __init__(self, mapper: Optional[SysNoticeMapper] = None) -> None:
        self._mapper = mapper or SysNoticeMapper()

    @property
    def mapper(self) -> SysNoticeMapper:
        return self._mapper

    # Java: SysNotice selectNoticeById(Long noticeId)
    def select_notice_by_id(self, notice_id: int) -> Optional[SysNotice]:
        # Java 里中间变量 sysNotice 只是为了可读，直接返回。
        return self._mapper.select_notice_by_id(notice_id)

    # Java: List<SysNotice> selectNoticeList(SysNotice notice)
    def select_notice_list(self, notice: SysNotice) -> List[SysNotice]:
        """分页由调用方的 ``start_page()`` + mapper 的 ``take_page`` 完成。"""
        return self._mapper.select_notice_list(notice)

    # Java: int insertNotice(SysNotice notice)
    def insert_notice(self, notice: SysNotice) -> int:
        """强制 ``noticeType = "1"``，并**覆盖** ``createBy`` / ``tenantId``。"""
        notice.notice_type = "1"
        # Java: notice.setCreateBy(SecurityUtils.getUserId() + "")
        notice.create_by = f"{SecurityUtils.get_user_id()}"
        notice.tenant_id = SecurityUtils.get_tenant_id()
        return self._mapper.insert_notice(notice)

    # Java: int updateNotice(SysNotice notice)
    def update_notice(self, notice: SysNotice) -> int:
        """**覆盖** ``updateBy``；富文本图片处理在 Java 里已被注释掉。"""
        # Java: notice.setUpdateBy(SecurityUtils.getUserId() + "")
        notice.update_by = f"{SecurityUtils.get_user_id()}"
        return self._mapper.update_notice(notice)

    # Java: int deleteNoticeById(Long noticeId)
    def delete_notice_by_id(self, notice_id: int) -> int:
        """Java 侧**无调用方**（控制器只走批量删除），照搬。"""
        return self._mapper.delete_notice_by_id(notice_id)

    # Java: int deleteNoticeByIds(Long[] noticeIds)
    def delete_notice_by_ids(self, notice_ids: Sequence[int]) -> int:
        return self._mapper.delete_notice_by_ids(notice_ids)

    # Java: Long addDeliveryTimeAbnormal(SysNotice notice)
    def add_delivery_time_abnormal(self, notice: SysNotice) -> Optional[int]:
        """内容相同的不重复新增，返回公告 id（已存在时返回已有那条的 id）。

        Java 里 ``notice = sysNoticeList.get(0)`` 是**重新赋值局部变量**，
        所以"插入"与"命中已有"两条路径返回的都是 ``notice.getNoticeId()``。
        命中已有那条时，入参上的字段改动**全部被丢弃**（不写库）。
        """
        existing = self._mapper.select_notice_list(notice)
        if len(existing) == 0:
            notice.create_by = f"{SecurityUtils.get_user_id()}"
            notice.tenant_id = SecurityUtils.get_tenant_id()
            notice.notice_type = "1"
            notice.status = "0"
            self._mapper.insert_notice(notice)
        else:
            # Java: notice = sysNoticeList.get(0);
            notice = existing[0]
        return notice.notice_id


_SERVICE: Optional[SysNoticeService] = None


def get_notice_service() -> SysNoticeService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysNoticeService()
    return _SERVICE


def reset_notice_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysNoticeService", "get_notice_service", "reset_notice_service"]
