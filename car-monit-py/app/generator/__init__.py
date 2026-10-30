"""代码生成模块.

# Migrated from: ruoyi-generator（com.ruoyi.generator 整包）

Python 侧把 Java 的
``com.ruoyi.generator.{domain,config,mapper,service,util}`` 一对一放在
``app.generator`` 下，控制器放在 ``app.api.tool.gen_controller``（对应 Java 的
``com.ruoyi.generator.controller.GenController``，包名与其它模块保持一致：
控制器统一在 ``app/api`` 下）。

**为什么这个模块必须迁**：``ruoyi-admin/pom.xml`` 依赖 ``ruoyi-generator``，根
``pom.xml`` 也把它列为 ``<module>``，所以 ``/tool/gen/**`` 这 15 个端点在 Java 侧是
**活着**的（前端"系统工具 -> 代码生成"直接用）。早期版本的端点审计脚本只扫了
``ruoyi-admin`` 与 ``ruoyi-quartz`` 的 controller 目录，漏掉了这个模块。
"""

from __future__ import annotations

__all__: list[str] = []
