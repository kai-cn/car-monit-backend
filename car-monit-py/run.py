"""One-command launcher.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java (main)

Java 原实现
-----------
``RuoYiApplication.main`` 调用 ``SpringApplication.run``，端口来自
``server.port``（默认 9989）。启动失败时捕获 ``Throwable`` 并打印堆栈。

Python 等价实现
---------------
``uvicorn`` 接管 socket，所以端口/主机必须显式传给它。本文件的作用就是
把 ``application.yml`` 里的 ``server.port`` 交给 uvicorn，让 Java 开发者
继续用「一条命令启动」的心智模型：

    python run.py

等价的显式写法（不需要本文件）::

    uvicorn app.main:app --host 0.0.0.0 --port 9989

``--reload`` 对应 ``spring.devtools.restart.enabled: true``，但只在开发时使用；
生产脚本不开启（Java 的 devtools 在生产 jar 中同样不生效）。
"""

from __future__ import annotations

import sys
import traceback

import uvicorn

from app.settings import get_settings


def main() -> int:
    """Start uvicorn on ``server.port``; return a process exit code."""
    settings = get_settings()
    host = "0.0.0.0"  # Java: Tomcat 默认绑定 0.0.0.0
    port = settings.server.port

    reload_enabled = "--reload" in sys.argv

    print(f"[启动] {settings.ruoyi.name} v{settings.ruoyi.version}")
    print(f"[启动] 监听 http://{host}:{port}  (context-path: {settings.context_path or '/'})")
    if not reload_enabled:
        print("[启动] 热重载未开启；开发时可执行: python run.py --reload")

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload_enabled,
            # access_log 由 uvicorn 输出；Java 侧等价的访问日志来自 Tomcat accesslog。
            access_log=True,
            log_config=None,  # 日志由 app.logging_config 统一配置（镜像 logback.xml）
        )
    except KeyboardInterrupt:
        print("\n[关闭] 收到 Ctrl+C, 已停止")
        return 0
    except Exception:  # Java: catch (Throwable e) { e.printStackTrace(); }
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
