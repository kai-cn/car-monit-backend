"""系统访问记录 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysLogininforService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysLogininforServiceImpl.java

Java resolves this bean from *inside a background task* with
``SpringUtils.getBean(ISysLogininforService.class)`` because ``AsyncFactory`` is a plain
utility class with no injection point. :func:`get_logininfor_service` is the same
service-locator pattern; the difference is that Python makes it explicit.

**Not transactional.** ``insertLogininfor`` is a single statement, so Java's
``@Transactional`` on the impl adds nothing; the audit row must survive even if the caller's
transaction rolled back, which is another reason it runs on a separate connection.

四个方法的来源
--------------
``insert_logininfor`` 的调用方是登录/登出/注册三条异步链路（``AsyncFactory``）；
另外三个（``select_logininfor_list`` / ``delete_logininfor_by_ids`` /
``clean_logininfor``）只有 ``/monitor/logininfor`` 控制器在用。

**本类不加** ``@Transactional``
------------------------------
Java 的 ``SysLogininforServiceImpl`` 也**没有** ``@Transactional``（与``SysOperLogServiceImpl``
相同）。``cleanLogininfor`` 是 ``truncate``（DDL），MySQL 下隐式提交，事务包不包都一样。
"""

from __future__ import annotations

from typing import List, Optional

from app.system.domain.sys_logininfor import SysLogininfor
from app.system.mapper.sys_logininfor_mapper import SysLogininforMapper


class SysLogininforService:
    """Java: ``ISysLogininforService`` (impl: ``SysLogininforServiceImpl``)."""

    def __init__(self, mapper: Optional[SysLogininforMapper] = None) -> None:
        self._mapper = mapper or SysLogininforMapper()

    @property
    def mapper(self) -> SysLogininforMapper:
        return self._mapper

    # Java: public int insertLogininfor(SysLogininfor logininfor)
    def insert_logininfor(self, logininfor: SysLogininfor) -> int:
        return self._mapper.insert_logininfor(logininfor)

    # Java: public List<SysLogininfor> selectLogininforList(SysLogininfor logininfor)
    def select_logininfor_list(self, logininfor: SysLogininfor) -> List[SysLogininfor]:
        """查询系统登录日志集合（分页点在 mapper 内部，见 ``take_page()``）。"""
        return self._mapper.select_logininfor_list(logininfor)

    # Java: public int deleteLogininforByIds(Long[] infoIds)
    def delete_logininfor_by_ids(self, info_ids: List[int]) -> int:
        """批量删除系统登录日志."""
        return self._mapper.delete_logininfor_by_ids(info_ids)

    # Java: public void cleanLogininfor()
    def clean_logininfor(self) -> None:
        """清空系统登录日志（``truncate table``，DDL，不可回滚）。"""
        self._mapper.clean_logininfor()


_SERVICE: Optional[SysLogininforService] = None


def get_logininfor_service() -> SysLogininforService:
    """Java: ``SpringUtils.getBean(ISysLogininforService.class)``."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysLogininforService()
    return _SERVICE


def reset_logininfor_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysLogininforService", "get_logininfor_service", "reset_logininfor_service"]
