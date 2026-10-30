"""AOP 切面的等价实现（Java: ``ruoyi-framework/.../aspectj``）.

已迁移：

* ``DataScopeAspect`` -> :mod:`app.framework.aspectj.data_scope_aspect`
  （显式函数调用 ``apply_data_scope``，不是装饰器 —— 它靠写入参的 ``params`` 生效）
* ``LogAspect`` -> :mod:`app.framework.aspectj.log_aspect`
  （装饰器 ``@log(title=..., business_type=...)``，放在 ``def`` 正上方）

未迁移：``RateLimiterAspect``（限流）、``DataSourceAspect``（多数据源），
分别随限流注解 / 读写分离迁移。
"""
