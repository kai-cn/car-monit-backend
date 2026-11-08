"""线程池配置.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ThreadPoolConfig.java

Java 原文
---------
``ThreadPoolConfig`` 是一个 ``@Configuration``，注册两个 ``@Bean``：

.. code-block:: java

    @Bean(name = "threadPoolTaskExecutor")
    public ThreadPoolTaskExecutor threadPoolTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setMaxPoolSize(200);          // maxPoolSize
        executor.setCorePoolSize(50);          // corePoolSize
        executor.setQueueCapacity(1000);       // queueCapacity
        executor.setKeepAliveSeconds(300);     // keepAliveSeconds
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        return executor;
    }

    @Bean(name = "scheduledExecutorService")   // -> app/framework/manager/async_manager.py
    protected ScheduledExecutorService scheduledExecutorService() { ... }

:class:`ThreadPoolTaskExecutor` 这里只负责**前一个** bean；后一个已由
:class:`~app.framework.manager.async_manager.AsyncManager` 承载。

Python 等价实现
---------------
``concurrent.futures.ThreadPoolExecutor(max_workers=200)``。使用方的唯一语义是
``executor.execute(runnable)`` —— **把任务丢进池子就返回**，请求线程不等待，
任务里的异常也不会回传给调用方（Java 里它流向线程的
``UncaughtExceptionHandler``，线程池继续存活）。

与 Java 的差异（都不影响可观测行为，逐条说明）
----------------------------------------------
* ``ThreadPoolTaskExecutor`` 是"核心 50 + 队列 1000 + 最大 200"的三段式。
  Python 侧用 :class:`~app.common.utils.bounded_executor.BoundedThreadPoolExecutor`：
  待执行任务超过 ``app.executor_queue_capacity``（默认 1000）时，按
  ``CallerRunsPolicy`` 由调用线程执行，不会无限积压。
* ``keepAliveSeconds = 300`` 对应 ``ThreadPoolExecutor`` 的线程回收，属实现细节。
* Java 的 ``ThreadPoolTaskExecutor`` 是**懒初始化**的（第一次 ``execute`` 时建池）；
  Python 侧在模块级单例里同样懒建，语义一致。

线程池是进程级单例，测试里用 :func:`reset_thread_pool_task_executor` 换掉。
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from app.common.utils.bounded_executor import BoundedThreadPoolExecutor, default_queue_capacity

logger = logging.getLogger("app.framework.config.thread_pool_config")


class ThreadPoolTaskExecutor:
    """Java: ``org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor``.

    只实现本项目用到的那一小撮 API（``execute`` / ``shutdown``）。
    """

    #: Java: ``private int corePoolSize = 50;``
    CORE_POOL_SIZE = 50
    #: Java: ``private int maxPoolSize = 200;``
    MAX_POOL_SIZE = 200
    #: Java: ``private int queueCapacity = 1000;`` —— Python 队列无界，见模块文档
    QUEUE_CAPACITY = 1000
    #: Java: ``private int keepAliveSeconds = 300;``
    KEEP_ALIVE_SECONDS = 300

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "task-pool",
        queue_capacity: Optional[int] = None,
    ) -> None:
        capacity = queue_capacity or default_queue_capacity() or self.QUEUE_CAPACITY
        self._executor = BoundedThreadPoolExecutor(
            max_workers=self.MAX_POOL_SIZE if max_workers is None else max_workers,
            thread_name_prefix=thread_name_prefix,
            queue_capacity=capacity,
        )

    # Java: public void execute(Runnable task)
    def execute(self, task: Callable[[], None]) -> None:
        """Java: ``execute(Runnable)`` —— 提交后**立即返回**，不抛任务内的异常."""
        self._executor.submit(self._run_safely, task)

    @staticmethod
    def _run_safely(task: Callable[[], None]) -> None:
        """Java: 池线程里的 ``Runnable.run()`` 抛异常 -> ``UncaughtExceptionHandler``.

        Java 的默认处理器打印堆栈、**不中断**线程；这里打印日志并吞掉，
        保证一个坏任务不会污染整条路线（下一轮 ``execute`` 照常工作）。
        """
        try:
            task()
        except Exception:  # noqa: BLE001 —— 对应 Java 的未捕获异常处理器
            logger.error("[线程池任务] 执行失败", exc_info=True)

    # Java: public void shutdown()
    def shutdown(self) -> None:
        """Java: ``ThreadPoolTaskExecutor#shutdown`` —— 停止接收新任务，**不等待**存量.

        Spring 的 ``waitForTasksToCompleteOnShutdown`` 默认 false，与
        ``ThreadPoolExecutor.shutdown(wait=False)`` 一致；``wait=True`` 会让
        lifespan 收尾被长任务拖住，进程退出不再有界。
        """
        self._executor.shutdown(wait=False)


_INSTANCE: Optional[ThreadPoolTaskExecutor] = None
_LOCK = threading.Lock()


def get_thread_pool_task_executor() -> ThreadPoolTaskExecutor:
    """Java: ``@Resource ThreadPoolTaskExecutor executor``（按 bean 名注入的单例）."""
    global _INSTANCE
    if _INSTANCE is None:
        with _LOCK:
            if _INSTANCE is None:
                _INSTANCE = ThreadPoolTaskExecutor()
    return _INSTANCE


def reset_thread_pool_task_executor(executor: Optional[ThreadPoolTaskExecutor] = None) -> None:
    """Test helper: shutdown / 替换进程级线程池."""
    global _INSTANCE
    if executor is None and _INSTANCE is not None:
        _INSTANCE.shutdown()
    _INSTANCE = executor


__all__ = [
    "ThreadPoolTaskExecutor",
    "get_thread_pool_task_executor",
    "reset_thread_pool_task_executor",
]
