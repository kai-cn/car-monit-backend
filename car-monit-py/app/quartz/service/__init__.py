"""定时任务 service 包（Java: ``com.ruoyi.quartz.service`` + ``com.ruoyi.quartz.service.impl``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/

Java 每个 service 都是"接口 + ``Impl``"两个文件。Python 没有接口，接口与实现折成
**一个类**（保留 ``Impl`` 的方法体），每个模块的 docstring 会同时标注两个 Java 类型名：

    ===================================  ===================================================
    模块                                  对应的 Java 类型
    ===================================  ===================================================
    ``sys_job_service``                  ``ISysJobService`` / ``SysJobServiceImpl``
    ``sys_job_log_service``              ``ISysJobLogService`` / ``SysJobLogServiceImpl``
    ===================================  ===================================================

本 ``__init__.py`` **不做任何 eager import**
--------------------------------------------
与 :mod:`app.system.service` 一致，只放说明文字。这里额外说清两件事，因为 quartz
的两个 service 都参与 Spring 的"按名字/按类型取 Bean"机制：

1. ``get_job_service()`` / ``get_job_log_service()`` 是 ``@Autowired`` 的等价物
   （Spring 默认 ``singleton``）。控制器、调度线程都只拿这一个实例。
2. ``ISysJobLogService`` **必须**在 :mod:`app.common.utils.spring_utils` 的注册表里
   有名字 —— ``AbstractQuartzJob#after`` 走 ``SpringUtils.getBean(ISysJobLogService.class)``
   （**按类型**）。这个注册发生在 ``get_job_log_service()`` 首次调用时（见
   :mod:`app.quartz.service.sys_job_log_service` 的 ``BEAN_NAME``）。

所以 ``app.quartz.service`` 的导入顺序**不能**被测试随意打乱：先调用
``get_job_log_service()`` 把 Bean 注册进去，再让调度器首次触发任务，否则
``AbstractQuartzJob`` 会抛 ``NoSuchBeanDefinitionException``。Java 侧不存在这个
问题（容器先就绪），Python 侧由 :mod:`app.main` 的 ``lifespan`` 保证 ——
它在启动时先 ``import app.quartz.service.sys_job_log_service`` 并取一次单例。
"""

from __future__ import annotations

__all__: list[str] = []
