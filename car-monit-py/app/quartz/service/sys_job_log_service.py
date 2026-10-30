"""定时任务调度日志信息 service.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/ISysJobLogService.java
# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobLogServiceImpl.java

六个方法全部迁移，**没有任何业务判断** —— 实现全是
``return jobLogMapper.xxx(...)``。唯一多一层的是 :meth:`SysJobLogService.add_job_log`：

``addJobLog`` 由调度线程调用
---------------------------
``AbstractQuartzJob#after`` -> ``SpringUtils.getBean(ISysJobLogService.class).addJobLog(...)``。
Java 签名是 ``void``（返回值被丢弃）；这里返回行数只为便于用例断言，调度侧不看。

因为这个 Bean 是由 :mod:`app.quartz.util.abstract_quartz_job` 在**运行时**按类型取出来的，
:func:`get_job_log_service` 在创建单例时会把它注册进
:mod:`app.common.utils.spring_utils` 的注册表（名字 ``ISysJobLogService``），
对应 Spring 容器里那个 Bean 名。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.utils import spring_utils as SpringUtils
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.mapper.sys_job_log_mapper import SysJobLogMapper


class SysJobLogService:
    """Java: ``ISysJobLogService`` (impl: ``SysJobLogServiceImpl``)."""

    def __init__(self, mapper: Optional[SysJobLogMapper] = None) -> None:
        self._mapper = mapper or SysJobLogMapper()

    @property
    def mapper(self) -> SysJobLogMapper:
        return self._mapper

    # Java: public List<SysJobLog> selectJobLogList(SysJobLog jobLog)
    def select_job_log_list(self, job_log: SysJobLog) -> List[SysJobLog]:
        """获取调度器日志（分页点在 mapper 内部）。"""
        return self._mapper.select_job_log_list(job_log)

    # Java: public SysJobLog selectJobLogById(Long jobLogId)
    def select_job_log_by_id(self, job_log_id: int) -> Optional[SysJobLog]:
        """通过日志 ID 查询调度信息.

        控制器侧**永远走不到**：``SysJobLogController`` 的 ``@GetMapping("/{configId}")``
        与 ``@PathVariable Long jobLogId`` 名字不匹配，Spring 会先抛
        ``MissingPathVariableException``。方法本身照搬。
        """
        return self._mapper.select_job_log_by_id(job_log_id)

    # Java: public void addJobLog(SysJobLog jobLog)
    def add_job_log(self, job_log: SysJobLog) -> int:
        """新增任务日志. Java 签名是 ``void``，返回值仅为本工程便于断言的便利。"""
        return self._mapper.insert_job_log(job_log)

    # Java: public int deleteJobLogByIds(Long[] logIds)
    def delete_job_log_by_ids(self, log_ids: List[int]) -> int:
        """批量删除调度日志."""
        return self._mapper.delete_job_log_by_ids(log_ids)

    # Java: public int deleteJobLogById(Long jobId)
    def delete_job_log_by_id(self, job_id: int) -> int:
        """删除任务日志（参数名叫 ``jobId``，Java 原文如此；**控制器没有调用点**）."""
        return self._mapper.delete_job_log_by_id(job_id)

    # Java: public void cleanJobLog()
    def clean_job_log(self) -> None:
        """清空任务日志（``truncate table``，DDL，不可回滚）."""
        self._mapper.clean_job_log()


_SERVICE: Optional[SysJobLogService] = None

#: Java 的 Bean 名（``ISysJobLogService`` 是接口简单名，``AnnotationBeanNameGenerator`` 的产物）。
BEAN_NAME = "ISysJobLogService"


def get_job_log_service() -> SysJobLogService:
    """Java: ``@Autowired ISysJobLogService`` / ``SpringUtils.getBean(ISysJobLogService.class)``."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysJobLogService()
        SpringUtils.register_named(BEAN_NAME, _SERVICE)
    return _SERVICE


def reset_job_log_service() -> None:
    """Test helper: drop the cached service so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    SpringUtils.unregister_bean(BEAN_NAME)


__all__ = [
    "SysJobLogService",
    "BEAN_NAME",
    "get_job_log_service",
    "reset_job_log_service",
]
