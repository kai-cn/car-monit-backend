"""操作日志 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysOperLogService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysOperLogServiceImpl.java

实现与 ``SysOperLogMapper`` 一一对应，**没有任何业务判断** —— 五个方法都是
"转发一行"。Java 侧同样如此（``SysOperLogServiceImpl`` 全部是
``return operLogMapper.xxx(...)``），所以这里不做"顺手加个 try/except"的改动：
异常照原样冒到 ``GlobalExceptionHandler``（HTTP 200 + ``code 500``）。

``insertOperlog`` 的返回值被丢弃
-------------------------------
Java 的接口签名是 ``void insertOperlog(SysOperLog operLog)``，实现里
``operLogMapper.insertOperlog(operLog);`` 也**不**接收返回值。这里返回 ``int``
（行数）只为了方便用例断言，控制器侧没有任何调用点。

谁在写这张表
------------
``LogAspect``（``@Log`` 注解的切面）异步调用 ``insertOperlog``。本工程对应
:mod:`app.framework.aspectj.log_aspect` 与 :func:`app.framework.manager.factory.async_factory.record_oper`，
各控制器上的 ``@log(...)`` 就是指这里。见 ``COMPATIBILITY.md`` §25。
"""

from __future__ import annotations

from typing import List, Optional

from app.system.domain.sys_oper_log import SysOperLog
from app.system.mapper.sys_oper_log_mapper import SysOperLogMapper


class SysOperLogService:
    """Java: ``ISysOperLogService`` (impl: ``SysOperLogServiceImpl``)."""

    def __init__(self, mapper: Optional[SysOperLogMapper] = None) -> None:
        self._mapper = mapper or SysOperLogMapper()

    @property
    def mapper(self) -> SysOperLogMapper:
        return self._mapper

    # Java: public void insertOperlog(SysOperLog operLog)
    def insert_operlog(self, oper_log: SysOperLog) -> int:
        """新增操作日志. Java 签名是 ``void``，返回值仅为本工程便于断言的便利。"""
        return self._mapper.insert_operlog(oper_log)

    # Java: public List<SysOperLog> selectOperLogList(SysOperLog operLog)
    def select_oper_log_list(self, oper_log: SysOperLog) -> List[SysOperLog]:
        """查询系统操作日志集合（分页点在 mapper 内部，见 ``take_page()``）。"""
        return self._mapper.select_oper_log_list(oper_log)

    # Java: public int deleteOperLogByIds(Long[] operIds)
    def delete_oper_log_by_ids(self, oper_ids: List[int]) -> int:
        """批量删除系统操作日志."""
        return self._mapper.delete_oper_log_by_ids(oper_ids)

    # Java: public SysOperLog selectOperLogById(Long operId)
    def select_oper_log_by_id(self, oper_id: int) -> Optional[SysOperLog]:
        """查询操作日志详细.

        **控制器没有调用点** —— Java 的 ``SysOperlogController`` 只有
        ``list`` / ``export`` / ``remove`` / ``clean`` 四个映射，没有 ``/{operId}``
        详情接口。按原则第 4 条照搬，不删。
        """
        return self._mapper.select_oper_log_by_id(oper_id)

    # Java: public void cleanOperLog()
    def clean_oper_log(self) -> None:
        """清空操作日志（``truncate table``，DDL，不可回滚）。"""
        self._mapper.clean_oper_log()


_SERVICE: Optional[SysOperLogService] = None


def get_oper_log_service() -> SysOperLogService:
    """Java: ``@Autowired ISysOperLogService`` —— Spring 默认单例。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysOperLogService()
    return _SERVICE


def reset_oper_log_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysOperLogService", "get_oper_log_service", "reset_oper_log_service"]
