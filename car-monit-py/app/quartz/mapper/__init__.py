"""``com.ruoyi.quartz.mapper`` 包 —— sys_job / sys_job_log 的 SQL 访问层."""

from __future__ import annotations

from app.quartz.mapper.sys_job_log_mapper import SysJobLogMapper
from app.quartz.mapper.sys_job_mapper import SysJobMapper

__all__ = ["SysJobMapper", "SysJobLogMapper"]
