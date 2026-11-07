"""Application entrypoint.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java (CORS part)
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ResourcesConfig.java (CORS part)

Start with one command::

    uvicorn app.main:app --host 0.0.0.0 --port 9989

``server.port`` is 9989 in application.yml; pass ``--port`` to match. The ``port`` value in
:class:`app.settings.ServerSection` is informational for uvicorn (uvicorn owns the socket),
and ``run.py`` reads it for convenience.

Java ``@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)`` has no Python
analogue: there is no auto-configuration to exclude. The engine is created lazily by
:mod:`app.config.database`, which is the equivalent of "the datasource bean is not
instantiated at startup".
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import anyio.to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.base.base_config_service_area_controller import router as base_config_service_area_router
from app.api.base.car_warning_config_controller import router as base_car_warning_config_router
from app.api.base.cdc_controller import router as base_cdc_router
from app.api.base.dwd_lczt_fwqjcxx_controller import router as base_fwqjcxx_router
from app.api.base.dwd_lczt_sfsjcxx_controller import router as base_sfsjcxx_router
from app.api.base.dwd_lczt_sfzjcxx_controller import router as base_sfzjcxx_router
from app.api.base.geometry_controller import router as base_geometry_router
from app.api.base.ods_cxzt_fwqclls_controller import router as manager_fwqclls_router
from app.api.base.ods_lwzxsfsj_fee_gantry_fusion01_controller import (
    router as base_fee_gantry_router,
)
from app.api.base.ods_lwzxsfsj_fee_records01_controller import router as base_fee_records_router
from app.api.base.ods_lwzxsfsj_fee_station_enter01_controller import (
    router as base_fee_station_enter_router,
)
from app.api.base.ods_lwzxsfsj_fee_station_exit01_controller import (
    router as base_fee_station_exit_router,
)
from app.api.base.ods_rt_szdn_snapshot_flow_addcode_controller import (
    router as base_snapshot_flow_router,
)
from app.api.base.ods_rt_szdn_snapshot_flow_provcapture_addcode_controller import (
    router as base_prov_capture_router,
)
from app.api.base.ods_rt_szdn_snapshot_flow_stationcapture_addcode_controller import (
    router as base_station_capture_router,
)
from app.api.base.ods_szdn_gantry_controller import router as base_gantry_router
from app.api.base.ods_szdn_gantry_ip_controller import router as base_gantry_ip_router
from app.api.base.ods_szdn_province_border_vehicle_weight_newstructure_controller import (
    router as base_vehicle_weight_router,
)
from app.api.base.ods_szdn_section_controller import router as base_section_router
from app.api.base.ods_szdn_toll_controller import router as base_toll_router
from app.api.base.ods_szdn_toll_station_ip_controller import router as base_toll_station_ip_router
from app.api.base.ods_yhgl_v_base_org_controller import router as base_org_router
from app.api.base.zdata_location_dict_controller import router as base_location_router
from app.api.base.zdata_trail_fitting_controller import router as base_fitting_router
from app.api.base.zdata_trail_tracks_controller import router as base_trail_tracks_router
from app.api.common.captcha_controller import router as captcha_router
from app.api.common.common_controller import router as common_router
from app.api.common.down_template_controller import router as down_template_router
from app.api.flow.flow_apply_info_controller import router as flow_apply_info_router
from app.api.flow.flow_current_node_controller import router as flow_current_node_router
from app.api.flow.flow_list_controller import router as flow_list_router
from app.api.flow.flow_message_dispose_controller import router as flow_message_dispose_router
from app.api.flow.flow_message_info_controller import router as flow_message_info_router
from app.api.flow.flow_name_controller import router as flow_name_router
from app.api.flow.flow_template_controller import router as flow_template_router
from app.api.health_controller import router as health_router
from app.api.manager.buss_test_controller import router as manager_buss_test_router
from app.api.manager.bigscreen.big_screen_controller import router as manager_big_screen_router
from app.api.manager.car_aduit_free_controller import (
    router as manager_car_aduit_free_router,
)
from app.api.manager.car_confim_free_controller import (
    router as manager_car_confim_free_router,
)
from app.api.manager.car_except_record_controller import (
    router as manager_car_except_record_router,
)
from app.api.manager.car_fee_record_controller import router as manager_fee_record_router
from app.api.manager.car_info_controller import router as manager_car_info_router
from app.api.manager.car_query_log_controller import router as manager_query_log_router
from app.api.manager.car_route_detail_controller import router as manager_route_detail_router
from app.api.manager.car_route_info_controller import router as manager_route_info_router
from app.api.manager.car_split_record_controller import router as manager_split_record_router
from app.api.manager.car_suspicious_controller import router as manager_suspicious_router
from app.api.manager.car_suspicious_back_controller import router as manager_suspicious_back_router
from app.api.manager.car_suspicious_check_controller import (
    router as manager_suspicious_check_router,
)
from app.api.manager.car_track_info_controller import (
    router as manager_car_track_info_router,
)
from app.api.manager.car_warning_info_controller import router as manager_warning_info_router
from app.api.manager.car_warning_rule_controller import router as manager_warning_rule_router
from app.api.manager.car_white_info_controller import router as manager_white_info_router
from app.api.manager.gantry_car_controller import router as manager_gantry_car_router
from app.api.manager.gantry_trade_info_controller import router as manager_gantry_trade_router
from app.api.monitor.cache_controller import router as monitor_cache_router
from app.api.monitor.server_controller import router as monitor_server_router
from app.api.monitor.sys_job_controller import router as monitor_job_router
from app.api.monitor.sys_job_log_controller import router as monitor_job_log_router
from app.api.monitor.sys_logininfor_controller import router as monitor_logininfor_router
from app.api.monitor.sys_operlog_controller import router as monitor_operlog_router
from app.api.monitor.sys_user_online_controller import router as monitor_online_router
from app.api.system.sys_config_controller import router as sys_config_router
from app.api.system.sys_dept_controller import router as sys_dept_router
from app.api.system.sys_dict_data_controller import router as sys_dict_data_router
from app.api.system.sys_dict_type_controller import router as sys_dict_type_router
from app.api.system.sys_file_controller import router as sys_file_router
from app.api.system.sys_index_controller import router as sys_index_router
from app.api.system.sys_index_menu_controller import router as sys_index_menu_router
from app.api.system.sys_login_controller import router as sys_login_router
from app.api.system.sys_menu_controller import router as sys_menu_router
from app.api.system.sys_notice_controller import router as sys_notice_router
from app.api.system.sys_post_controller import router as sys_post_router
from app.api.system.sys_profile_controller import router as sys_profile_router
from app.api.system.sys_role_controller import router as sys_role_router
from app.api.system.sys_upgrade_info_controller import router as sys_upgrade_info_router
from app.api.system.sys_user_controller import router as sys_user_router
from app.api.tool.gen_controller import router as tool_gen_router
from app.api.tool.test_controller import router as tool_test_router
from app.config.database import dispose_engine
from app.config.exception_handlers import register_exception_handlers
from app.config.redis_config import close_redis
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.trace_id import TraceIdMiddleware
from app.middleware.xss import XssMiddleware
from app.settings import AppSettings, get_settings

# Java: ``@ComponentScan`` 扫到 ``com.ruoyi.quartz.task`` 的六个业务 bean。
# 导入本包就会把它们注册进 :mod:`app.common.utils.spring_utils` 的注册表 ——
# ``JobInvokeUtil.invokeMethod`` 是靠 ``SpringUtils.getBean(beanName)`` 找任务的，
# 少了这一行，``sys_job`` 里每一条都能触发却全部报 ``No bean named 'trackTask' available``。
# 放在这里（模块导入期）而不是 ``lifespan`` 里，是因为 ``create_app()`` 的调用方
# （含测试）必须看到同一份注册表。
import app.quartz.task  # noqa: F401  —— 导入副作用：注册 6 个任务 bean

logger = logging.getLogger("app.main")

#: Copied from ``kafka``/``elasticsearch``/``oss`` config so startup can warn loudly.
_STARTUP_BANNER = "(♥◠‿◠)ﾉﾞ  {name}启动成功   ლ(´ڡ`ლ)ﾞ"

#: Java: ``RuoYiApplication.main`` prints this after ``SpringApplication.run`` returns.
_STARTUP_MESSAGE = "(♥◠‿◠)ﾉﾞ  吉安东管理中心重点车辆监测平台启动成功   ლ(´ڡ`ლ)ﾞ"


def _relax_stdio_encoding() -> None:
    """Relax stdout/stderr to ``errors="replace"`` (do NOT change the encoding).

    Java 原语义
        ``System.out`` / ``System.err`` 使用**平台默认字符集**，无法映射的字符被替换成
        ``?``，**永远不会抛异常**。中文 Windows 上就是 GBK。

    Python 的坑
        stdout 被重定向（管道、文件、IDE 捕获、systemd）时用的是 locale 编码，
        中文 Windows 上是 GBK。打印启动横幅里的 ``♥`` / ``ლ`` 会抛
        ``UnicodeEncodeError`` ⇒ 进程直接启动失败。这属于环境差异，不是业务逻辑，
        但后果是“服务起不来”，所以必须在启动前修掉。

    为什么**不改** encoding
        改成 UTF-8 会让 GBK 控制台看到乱码，而 Java 在同样的控制台上是可读的。
        保留平台编码 + ``errors="replace"`` 才能与 ``PrintStream`` 行为完全一致
        （不可编码字符 → ``?``）。
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:  # 被替换成非 TextIOWrapper（如 pytest 捕获器）
            continue
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):  # pragma: no cover - 极少数只写流
            logger.debug("无法调整 %s 的编码错误策略，保持默认", stream_name)


_relax_stdio_encoding()


def _log_startup_state(settings: AppSettings) -> None:
    """Report the components that are switched off, mirroring the Java log on boot."""
    logger.info(_STARTUP_MESSAGE)
    logger.info(
        "[启动参数] port=%s, context-path=%s, profile=%s, captchaType=%s",
        settings.server.port,
        settings.context_path or "/",
        settings.ruoyi.profile,
        settings.ruoyi.captcha_type,
    )
    if not settings.app.kafka_enabled:
        logger.warning("[启动警告] Kafka 已禁用 (app.kafka_enabled=false); 4 个 consumer 不会启动")
    if not settings.app.oss_enabled:
        logger.warning("[启动警告] MinIO/OSS 已禁用 (app.oss_enabled=false); 文件上传/下载将不可用")
    if not settings.app.scheduled_annotations_enabled:
        logger.warning("[启动警告] @Scheduled 已禁用, 与 Java 运行时一致 (Java 缺少 @EnableScheduling)")
    if not settings.app.scheduler_enabled:
        logger.warning("[启动警告] Quartz 调度器已禁用 (app.scheduler_enabled=false); sys_job 中的任务不会调度")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Java: the Spring context ``refresh`` + graceful shutdown hooks."""
    settings = get_settings()
    if settings.app.banner_enabled:
        print(_STARTUP_BANNER.format(name=settings.ruoyi.name))
    _log_startup_state(settings)
    _apply_tomcat_thread_parity(settings)
    _init_quartz(settings)
    try:
        yield
    finally:
        # Java: ``ShutdownManager`` + Druid ``destroy``
        _shutdown_quartz(settings)
        # Java: Spring 销毁 ``threadPoolTaskExecutor`` / ``scheduledExecutorService`` 两个
        # bean 时调用各自的 ``shutdown()``。Python 侧这两个池是进程级单例（模块级变量），
        # 容器销毁不会自动触发；漏掉这一步，解释器退出时会留下 50 + 200 个 worker 线程，
        # 进程无法干净退出（uvicorn 重载/测试反复 create_app 时还会累积线程）。
        _shutdown_thread_pools()
        _close_http_client()
        dispose_engine()
        close_redis()
        logger.info("[应用] 已优雅关闭")


def _init_quartz(settings: AppSettings) -> None:
    """Java: ``SysJobServiceImpl`` 的 ``@PostConstruct public void init()``.

    Spring 创建 ``ISysJobLogService`` / ``ISysJobService`` 这两个单例时就完成了：

    1. ``@Autowired Scheduler`` —— 拿到 ``SchedulerFactoryBean`` 里那个调度器，等价的
       Python 实现是 :func:`app.quartz.util.scheduler.get_scheduler`（首次调用即建好并
       ``start()``）。**线程池在 Java 里也是启动期就起**，不是等到第一个任务。
    2. ``scheduler.clear()`` + 逐条 ``createScheduleJob`` —— 把 ``sys_job`` 整表重建进
       JobStore（RAMJobStore，重启即丢，所以每次启动都得重建）。
    3. ``ISysJobLogService`` 进容器 —— ``AbstractQuartzJob#after`` 按**类型**取它，
       所以必须先建出来放进 :mod:`app.common.utils.spring_utils` 的注册表。

    顺序不能换：先注册日志服务，再 ``init()``。``init()`` 会按 ``status`` 把任务
    ``pause_job``，一条也不会真的跑（``sys_job`` 的种子数据全是 ``status='1'`` 暂停）。

    ``app.scheduler_enabled=false`` 时整段跳过 —— 这是本工程**独有**的开关
    （Java 没有"关掉 Quartz"的配置），用于没有 MySQL 的环境起服务。
    """
    if not settings.app.scheduler_enabled:
        return
    from app.quartz.service.sys_job_log_service import get_job_log_service
    from app.quartz.service.sys_job_service import get_job_service

    # Java: 容器先建 Bean，再调 @PostConstruct
    get_job_log_service()
    try:
        get_job_service().init()
    except Exception:  # noqa: BLE001 - 启动期 DB 不可用时只记日志
        # Java 这里是 BeanCreationException -> 启动失败。本工程保留进程可用性：
        # 调度器继续空转，未注册的任务在 ``PUT /monitor/job/run`` 时会回
        # ``The job (...) referenced by the trigger does not exist.``（与 Java 一致）。
        logger.error("[启动警告] Quartz 任务初始化失败, sys_job 中的任务不会调度", exc_info=True)


def _shutdown_quartz(settings: AppSettings) -> None:
    """Java: ``SchedulerFactoryBean#destroy()`` + ``ExecutorService`` 回收."""
    if not settings.app.scheduler_enabled:
        return
    from app.quartz.service.sys_job_log_service import reset_job_log_service
    from app.quartz.util.scheduler import shutdown_scheduler

    shutdown_scheduler()
    reset_job_log_service()


def _shutdown_thread_pools() -> None:
    """Java: ``ThreadPoolConfig`` 两个 bean 的 ``destroyMethod``.

    Java 里 ``ThreadPoolTaskExecutor`` 与 ``scheduledExecutorService`` 都是 Spring bean，
    容器关闭时由 ``DisposableBean#destroy()`` 依次 ``shutdown()``。本工程把它们落成
    进程级单例（:mod:`app.framework.config.thread_pool_config` /
    :mod:`app.framework.manager.async_manager`），必须在 lifespan 收尾时显式回收，
    否则遗留的非 daemon worker 线程会让进程卡在退出阶段。
    """
    from app.framework.config.thread_pool_config import reset_thread_pool_task_executor
    from app.framework.manager.async_manager import reset_async_manager

    reset_async_manager()
    reset_thread_pool_task_executor()


def _close_http_client() -> None:
    """关闭 Forest 等外部 HTTP 调用共用的进程级 ``httpx.Client``。"""
    from app.base.service.forest.forest_client import close_http_client

    close_http_client()


def _apply_tomcat_thread_parity(settings: AppSettings) -> None:
    """Reconcile the request thread budget with anyio's thread pool.

    Java 原语义
        ``server.tomcat.threads.max: 800`` -- Tomcat keeps up to 800 request worker
        threads, so 800 blocking requests can run concurrently.

    Python 等价实现
        All endpoints are declared as sync ``def`` (chosen for behavioural parity with
        JDBC/ThreadLocal), so Starlette dispatches every request onto anyio's default
        thread pool. That pool is capped at **40 tokens** by default, which would
        silently throttle the service.

    与 Java 的偏差（有意为之）
        800 个请求线程里最多只有 ``spring.datasource.druid.max-active``（200）个
        能拿到 DB 连接，其余 600 个只是在连接池上排队。默认改用
        ``app.request_thread_limit``（200），与连接池对齐；需要复刻 Tomcat 原值
        时设 ``APP__REQUEST_THREAD_LIMIT=800``。
    """
    max_threads = settings.app.request_thread_limit
    try:
        anyio.to_thread.current_default_thread_limiter().total_tokens = max(1, max_threads)
    except Exception:  # pragma: no cover - defensive, anyio API is stable
        logger.warning("[启动警告] 无法调整 anyio 线程池上限, 并发请求可能被限制在 40")
        return
    logger.debug("[启动参数] anyio 线程池上限 = %s (app.request_thread_limit)", max_threads)


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Application factory. Tests call this to build an isolated instance."""
    settings = settings or get_settings()
    configure_logging(settings)

    # Java: springfox is disabled (``swagger.enabled: false``) and SecurityConfig denies
    # ``/swagger-ui.html`` -> do not expose docs unless explicitly enabled.
    docs_enabled = settings.swagger.enabled

    application = FastAPI(
        title=f"{settings.ruoyi.name} API",
        version=settings.ruoyi.version,
        default_response_class=ORJSONResponse,
        docs_url="/swagger-ui.html" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/v3/api-docs" if docs_enabled else None,
        lifespan=lifespan,
    )

    # ---- Filters: order mirrors the Java filter chain ----------------------
    # Java registers CorsFilter before JwtAuthenticationTokenFilter; TraceIdFilter is a
    # plain servlet filter, so it sits outermost. ``add_middleware`` **prepends**, therefore
    # this list is written innermost-first and executes in the opposite order:
    #
    #     TraceIdFilter -> CorsFilter -> RequestContextFilter -> Spring Security
    #     TraceIdMiddleware -> CORSMiddleware -> RequestContextMiddleware -> SecurityMiddleware
    #
    # SecurityMiddleware must be registered **before** CORSMiddleware so that CORS ends up
    # outside it: ``CorsFilter`` answers a preflight OPTIONS and returns without calling the
    # chain, so a preflight never needs a token. Swapping these two lines would answer every
    # browser preflight with 401. RequestContextMiddleware must stay outside SecurityMiddleware
    # because the logout handler runs ``AsyncFactory.recordLogininfor``, which resolves the
    # current request through ``ServletUtils.getRequest()``.
    application.add_middleware(SecurityMiddleware)
    application.add_middleware(RequestContextMiddleware)

    # Java: config.addAllowedOriginPattern("*") -- NOT addAllowedOrigin("*").
    # ``allow_credentials=true`` with "*" is spec-invalid, so a permissive regex is the
    # correct equivalent of Spring's allowedOriginPatterns. Production should whitelist
    # through ``app.cors.allowed_origins``; when the list is empty only local installs
    # keep the permissive Java behaviour (see CorsSection).
    allowed_origins = [origin.strip() for origin in settings.app.cors.allowed_origins if origin.strip()]
    cors_options: dict = {
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Trace-Id"],
        "max_age": 1800,  # Java: config.setMaxAge(1800L)
    }
    if allowed_origins:
        cors_options["allow_origins"] = allowed_origins
        logger.info("[启动参数] CORS 白名单已启用: %s", allowed_origins)
    elif (settings.is_localhost or "").strip().lower() == "local":
        cors_options["allow_origin_regex"] = ".*"
    else:
        logger.warning(
            "[启动警告] app.cors.allowed_origins 未配置, 非 local 环境将拒绝所有跨域请求"
        )
    application.add_middleware(CORSMiddleware, **cors_options)
    application.add_middleware(TraceIdMiddleware, settings=settings)
    # Java: FilterConfig.xssFilterRegistration -> order HIGHEST_PRECEDENCE。add_middleware
    # 是 prepend，所以最后添加的 XssMiddleware 位于最外层（先于 CORS/TraceId/Security）。
    application.add_middleware(XssMiddleware, settings=settings)

    register_exception_handlers(application)

    # ---- Controllers -------------------------------------------------------
    application.include_router(sys_index_router)
    # Java: CaptchaController -- ``GET /captchaImage``, permitAll in SecurityConfig.
    application.include_router(captcha_router)
    # Java: CommonController -- ``/common/**``. ``GET /common/download`` is
    # ``anonymous()`` (an **authenticated** caller gets 403); ``POST /common/upload`` and
    # ``/common/uploads`` are login-only; ``GET /common/download/resource`` is
    # ``authenticated()`` -- ``/common/download**`` does **not** shadow it, because
    # AntPathMatcher tokenises to ["common", "download**"] and a leftover path segment
    # after the pattern is exhausted makes ``doMatch`` return false.
    application.include_router(common_router)
    # Java: DownTemplateController -- ``GET /downTemplate/{type}``. No SecurityConfig rule
    # matches it, so it is login-only. An unknown ``type`` answers 200 with an empty body
    # and no headers (the template lookup fails before the response is touched).
    application.include_router(down_template_router)
    # Java: SysLoginController -- ``POST /login`` (permitAll), ``GET /getInfo`` and
    # ``GET /getRouters`` (both authenticated via ``anyRequest()``).
    application.include_router(sys_login_router)
    # Java: SysProfileController -- ``/system/user/profile/**``, all ``authenticated()`` and
    # **no** ``@PreAuthorize`` (everyone edits their own profile). Must be registered
    # BEFORE ``sys_user_router``: ``sys_user_router`` owns ``GET /system/user/{user_id}``
    # and FastAPI matches in registration order, so ``GET /system/user/profile`` would
    # otherwise hit the path variable and fail ``int`` conversion (422 instead of 200).
    application.include_router(sys_profile_router)
    # Java: SysUserController -- ``/system/user/**``, all ``authenticated()`` (no rule above
    # matches it, so it falls through to ``anyRequest()``). ``export`` / ``importData`` are
    # not registered; see the module docstring.
    application.include_router(sys_user_router)
    # Java: SysPostController -- ``/system/post/**``, all ``authenticated()``. ``export`` is
    # not registered (ExcelUtil); see the module docstring.
    application.include_router(sys_post_router)
    # Java: SysDeptController -- ``/system/dept/**``, all ``authenticated()``. Only half the
    # mappings carry ``@PreAuthorize``; the rest are login-only (see the module docstring).
    application.include_router(sys_dept_router)
    # Java: SysRoleController -- ``/system/role/**``, all ``authenticated()``. ``list``'s
    # ``@PreAuthorize`` is commented out in Java, so it is login-only; ``export`` is not
    # registered (ExcelUtil); see the module docstring.
    application.include_router(sys_role_router)
    # Java: SysMenuController -- ``/system/menu/**``, all ``authenticated()``. ``list`` is
    # the only mapping that is not paged; ``treeselect`` / ``roleMenuTreeselect`` carry no
    # ``@PreAuthorize``; see the module docstring.
    application.include_router(sys_menu_router)
    # Java: SysNoticeController -- ``/system/notice/**``. Only add/edit/remove carry
    # ``@PreAuthorize``; ``list``'s annotation is commented out in Java. ``view/**`` is
    # ``anonymous()`` in SecurityConfig (anonymous allowed, authenticated -> 403).
    application.include_router(sys_notice_router)
    # Java: SysDictTypeController -- ``/system/dict/type/**``. ``optionselect`` has no
    # ``@PreAuthorize`` (login-only); ``export`` is not registered (ExcelUtil).
    application.include_router(sys_dict_type_router)
    # Java: SysDictDataController -- ``/system/dict/data/**``. ``/type/{dictType}`` and
    # ``/typemore/{dictType}`` are login-only (no ``@PreAuthorize``); ``/typemore`` groups
    # by dict type. ``export`` is not registered (ExcelUtil).
    application.include_router(sys_dict_data_router)
    # Java: SysConfigController -- ``/system/config/**``. ``configKey/{configKey}`` carries no
    # ``@PreAuthorize`` (login-only); ``export`` is not registered (ExcelUtil).
    application.include_router(sys_config_router)
    # Java: SysIndexMenuController -- ``/system/indexmenu/**``. Only ``getInfo`` / ``edit``
    # carry ``@PreAuthorize``; ``list`` / ``add`` / ``remove`` have theirs commented out in
    # Java. ``export`` is not registered (ExcelUtil).
    application.include_router(sys_index_menu_router)
    # Java: SysUpgradeInfoController -- ``/system/upgradeInfo/**``. **No** ``@PreAuthorize``
    # anywhere; ``/{id}`` takes a String (UUID), so the un-migrated ``export`` falls into it
    # and answers 200 without a ``data`` key instead of 500.
    application.include_router(sys_upgrade_info_router)
    # Java: SysFileController -- ``/system/file/**``. Only ``list`` (``base:sysflie:list``,
    # a typo copied from ``sys_menu.perms``) and ``DELETE /{ids}``
    # (``base:supplier:remove``) carry ``@PreAuthorize``; the other 15 mappings are
    # login-only. Two ``void`` download routes write bytes with
    # ``Content-Type: application/octet-stream; charset=UTF-8`` and answer 200 with an
    # empty body when OSS fails. There is no ``export`` here, so no ExcelUtil gap.
    application.include_router(sys_file_router)
    # Java: SysOperlogController -- ``/monitor/operlog/**``. Four mappings, all
    # ``monitor:operlog:*``; ``list`` is paged, ``export`` writes an ``操作日志`` sheet.
    application.include_router(monitor_operlog_router)
    # Java: SysLogininforController -- ``/monitor/logininfor/**``. Four mappings, all
    # ``monitor:logininfor:*``. ``DELETE /clean`` is declared **before** ``DELETE /{infoIds}``
    # in the module, because FastAPI matches in registration order while Spring's
    # ``AntPathMatcher`` prefers literals regardless of order -- same net result.
    application.include_router(monitor_logininfor_router)
    # Java: SysUserOnlineController -- ``/monitor/online/**``. ``list`` has **no**
    # ``startPage()`` (so ``total`` is the list length and paging is inert);
    # ``DELETE /{tokenId}`` only deletes ``login_tokens:<tokenId>`` from Redis.
    application.include_router(monitor_online_router)
    # Java: SysJobController -- ``/monitor/job/**``. 8 mappings. ``run`` 复用了
    # ``changeStatus`` 的权限点；``GET /{jobId}`` 查不到时响应里**没有 ``data`` 键**；
    # ``DELETE /{jobIds}`` 遇到不存在的 id 是 NPE（``{"msg":null,"code":500}``）。
    application.include_router(monitor_job_router)
    # Java: SysJobLogController -- ``/monitor/jobLog/**``. 5 mappings. ``GET /{configId}``
    # **永远 500**（路径变量与参数名 ``jobLogId`` 对不上 -> MissingPathVariableException），
    # 这是 Java 的真 bug，照抄；``DELETE /clean`` 在模块内先于 ``/{jobLogIds}`` 注册。
    application.include_router(monitor_job_log_router)
    # Java: CacheController -- ``GET /monitor/cache``. Returns the raw ``INFO`` /
    # ``INFO commandstats`` / ``DBSIZE`` of the Redis the app is actually wired to.
    application.include_router(monitor_cache_router)
    # Java: ServerController -- ``GET /monitor/server``. Uses psutil (was OSHI) and
    # **sleeps 1 second** inside ``setCpuInfo()``; see the module docstring.
    application.include_router(monitor_server_router)
    # Java: TestController -- ``/test/user/**``, a dev-only scaffold backed by an in-memory
    # ``LinkedHashMap`` (no database, no Redis). ``SecurityConfig`` has no rule for it, so it
    # falls through to ``anyRequest().authenticated()``: login-only, no permission point.
    # ``POST /test/user/save`` binds **request parameters** (query string or a urlencoded
    # form) because the Java signature has no ``@RequestBody``; ``PUT /update`` reads JSON.
    application.include_router(tool_test_router)
    # Java: GenController -- ``/tool/gen/**``, the 15 mappings of ``ruoyi-generator``. A
    # module that the earlier endpoint audit missed: ``ruoyi-admin`` depends on
    # ``ruoyi-generator``, so these routes are live. ``SecurityConfig`` has no rule for
    # ``/tool/**``, so they fall through to ``anyRequest().authenticated()``: login-only,
    # with the per-mapping ``@PreAuthorize`` on top. ``GET /{talbleId}`` is registered
    # **last** inside the module, otherwise it swallows ``/list`` / ``/all/list`` /
    # ``/db/list`` / ``/batchGenCode``. ``/column/{talbleId}`` reads its ``tableId`` from the
    # query string (the path variable is unbound in Java) and answers ``code: 0`` /
    # ``msg: null`` because it builds ``TableDataInfo`` by hand.
    application.include_router(tool_gen_router)
    # Java: BaseConfigServiceAreaController -- ``/base/configServiceArea/**``. Seven mappings;
    # ``listQuery`` / ``getInfo`` carry no ``@PreAuthorize``. ``/{fwqbm}`` takes a **String**
    # (a service-area code, not the UUID ``id``), so every literal route is registered
    # before it. ``export`` returns the generated **filename in ``msg``**, not the file.
    application.include_router(base_config_service_area_router)
    # Java: OdsSzdnGantryIpController / OdsSzdnTollStationIpController -- read-only IP tables.
    # Both carry **no** ``@PreAuthorize`` (login-only) and expose just ``/list`` + ``/{id}``
    # where ``id`` is a **Long**. The commented-out ``setTenantId(...)`` line in Java stays
    # commented out, so neither list is tenant-filtered.
    application.include_router(base_gantry_ip_router)
    application.include_router(base_toll_station_ip_router)
    # Java: the five read-only ODS controllers below follow the same generator template
    # (``WHERE 1 = 1`` + ``<if>`` list, ``/{pk}`` detail, no writes). None of them carries
    # ``@PreAuthorize``. Two of them do **not** key the detail statement on the table's
    # primary key: ``vehicleweight`` filters ``t.dataSource`` (String) and ``trailtracks``
    # filters ``t.uuid`` (String).
    application.include_router(base_fee_station_enter_router)
    application.include_router(base_prov_capture_router)
    application.include_router(base_station_capture_router)
    application.include_router(base_vehicle_weight_router)
    application.include_router(base_trail_tracks_router)
    # Java: OdsCxztFwqcllsController lives in ``com.ruoyi.web.controller.base`` but maps to
    # ``/manager/fwqclls`` -- the one place where package and URL path disagree. Its ``list``
    # is also the only read-only ODS list in this batch that carries a permission point
    # (``manager:fwqclls:list``).
    application.include_router(manager_fwqclls_router)

    # ---- The remaining 16 ``com.ruoyi.web.controller.base`` controllers ----------
    # 全部 25 个 Java base 控制器到此一一对应。每个 router 的 module docstring 都有一张
    # "Java 方法 / 路径 / 权限点" 对照表；这里只记**跨路由**才看得出来的坑。
    #
    # Java: CarWarningConfigController -- ``/base/config/**``. 这是模板里**唯一**给 ``list``
    # 加了权限点（``base:config:list``）的控制器；保存/删除会刷新 Redis 缓存，删除是物理删除。
    application.include_router(base_car_warning_config_router)
    # Java: CdcController -- ``/base/cdc/**``, 8 个映射、全部只要求登录。``DELETE
    # /dead-letters/clear`` 必须排在 ``DELETE /dead-letters/{messageId}`` 之前（Spring 让
    # 字面量天生优先，FastAPI 只看顺序）—— 该顺序已在模块内保证。
    application.include_router(base_cdc_router)
    # Java: DwdLcztFwqjcxxController / DwdLcztSfsjcxxController / DwdLcztSfzjcxxController --
    # ``/base/fwqjcxx`` / ``/base/sfsjcxx`` / ``/base/sfzjcxx``。三者的路径变量是 **String**
    # （``agentPk`` / ``sfsjPk`` / ``sfzjPk``），会吃掉所有单段 GET，所以 ``/list`` /
    # ``/export`` 在模块内先注册。``export`` 返回文件名（在 ``msg`` 里），不是文件字节。
    application.include_router(base_fwqjcxx_router)
    application.include_router(base_sfsjcxx_router)
    application.include_router(base_sfzjcxx_router)
    # Java: GeometryController -- ``/base/geometry/**``。``/syncAllGeometry`` /
    # ``/syncAllGeometry1`` **没有**权限注解，且是 fire-and-forget：任务丢进
    # ``threadPoolTaskExecutor`` 后接口立刻返回 200，真正的补桩号工作（可能长时间超时）
    # 在后台线程里跑，异常不影响响应。
    application.include_router(base_geometry_router)
    # Java: OdsLwzxsfsjFeeGantryFusion01Controller -- ``/base/feeGantry/**``。数据不来自本库，
    # 而是转发给 ``IOdsLwzxsfsjFeeGantryFusion01Service``（Forest 客户端）。``export`` 整段被
    # 注释掉，所以只有 ``/list``（``base:feeGantry:list``）+ ``/{bigId}``（登录即可）两个映射。
    application.include_router(base_fee_gantry_router)
    # Java: OdsLwzxsfsjFeeRecords01Controller -- ``/base/feerecords/**``。``list`` / ``export``
    # 共用 ``base:feerecords:list``；``export`` 走 easypoi 模板 ``templates/export/feeRecords.xlsx``，
    # 失败时回**空 body + 无响应头**（Java 在渲染成功之后才设头）。
    application.include_router(base_fee_records_router)
    # Java: OdsLwzxsfsjFeeStationExit01Controller -- ``/base/feestationexit/**``。同样是转发型；
    # 下游返回体缺 ``code`` 时 Java 拆箱 NPE（不是 ServiceException），这里保持同一分支。
    application.include_router(base_fee_station_exit_router)
    # Java: OdsRtSzdnSnapshotFlowAddcodeController -- ``/base/snapshotflow/**``。``/earliest-time``
    # 是字面量路由，必须排在 ``/{big_id}`` 之前（模块内已保证）。``list`` 优先走
    # ``SnapshotFlowEnhancedService``（分片聚合），异常时才回落到 Forest 客户端。
    application.include_router(base_snapshot_flow_router)
    # Java: OdsSzdnGantryController -- ``/base/gantry/**``。``list`` 从 Redis 的
    # ``SECTION_LIST`` 补路段名；``export`` 的数据源是 Redis 对象 ``gantry_list``（不是数据库），
    # 列表为空时**什么都不写**（200 + 空 body）。
    application.include_router(base_gantry_router)
    # Java: OdsSzdnSectionController / OdsSzdnTollController -- ``/base/section`` / ``/base/toll``，
    # 标准生成器模板；两者的 ``list`` / ``listAll`` 都没有 ``@PreAuthorize``。
    application.include_router(base_section_router)
    application.include_router(base_toll_router)
    # Java: OdsYhglVBaseOrgController -- ``/base/org/**``。主键是 ``big_id``（``IdType.INPUT``），
    # 路径变量叫 ``bigId`` / ``bigIds``；``list`` 是登录即可。
    application.include_router(base_org_router)
    # Java: ZdataLocationDictController -- ``/base/location/**``。路径变量是 **Long**，
    # 非数字路径由 FastAPI 直接 422（Spring 抛 MethodArgumentTypeMismatchException -> 400）。
    application.include_router(base_location_router)
    # Java: ZdataTrailFittingController -- ``/base/fitting/**``。只有 ``/list`` + ``/{id}``，
    # 没有导出、没有写接口。
    application.include_router(base_fitting_router)

    # ---- manager 包（``/manager/**``）----
    # Java: BussTestController -- ``/manager/busstest/**``。7 个映射；``syncCurrentTrack``
    # 在 Java 里返回 ``void``（HTTP 200 + 空 body），且忽略 service 的返回值。
    application.include_router(manager_buss_test_router)
    # Java: CarWarningRuleController -- ``/manager/warningrule/**``。save/delete 之后会重建
    # Redis 缓存 ``car_warning_rule:<userId>type<noticeType>``（先删后建，已有键**追加**）。
    application.include_router(manager_warning_rule_router)
    # Java: CarWhiteInfoController -- ``/manager/whiteinfo/**``。save/delete 之后整份覆盖
    # Redis 值 ``white_car_list``；列表 SQL 里的 ``createInfo`` 别名不在 ``resultMap`` 里，
    # 所以响应中该字段恒为 ``null``。
    application.include_router(manager_white_info_router)
    # Java: CarFeeRecordController -- ``/manager/feerecord/**``。标准 6 接口模板。
    application.include_router(manager_fee_record_router)
    # Java: CarRouteDetailController -- ``/manager/routedetail/**``。标准 6 接口模板；
    # ``export`` 走 ``ExcelUtil<CarRouteDetail>``（sheet 名见模块常量），不是 easypoi 模板。
    application.include_router(manager_route_detail_router)
    # ---- 下面 7 个是 easypoi 模板导出（``templates/export/*.xlsx``）的同类模板 ----
    # 共同点：``list`` 里 ``setTenantId(...)`` 在 Java 中被注释掉；``export`` 写完响应后
    # ``return null``，渲染失败时回**空 body + 无响应头**（Java 先渲染后设头）。
    #
    # Java: GantryCarController / GantryTradeInfoController / CarRouteInfoController --
    # 三者都按 ``car_type`` + ``car_vehicle`` 两个字典翻译字段，并把 ``createTime`` 转字符串。
    application.include_router(manager_gantry_car_router)
    application.include_router(manager_gantry_trade_router)
    application.include_router(manager_route_info_router)
    # Java: CarSplitRecordController -- ``/manager/splitrecord/**``。多一个 ``pass_type`` 字典，
    # 且 Java 用 ``carVehicle`` 的值去查它（疑似 bug，照抄，见模块 docstring）。
    application.include_router(manager_split_record_router)
    # Java: CarSuspiciousCheckController -- ``/manager/suspiciouscheck/**``。只翻 ``createTime``。
    application.include_router(manager_suspicious_check_router)
    # Java: CarQueryLogController -- ``/manager/querylog/**``。``export`` 在 Java 里声明在最后，
    # 这里保持同一注册顺序；``model_type`` / ``menu_point`` 两个字典。
    application.include_router(manager_query_log_router)
    # Java: CarWarningInfoController -- ``/manager/carwarning/**``。``list`` 的 ``@PreAuthorize``
    # 在 Java 里被注释掉（登录即可）；``list`` / ``export`` 共用一段查询参数规整（flag /
    # sectionCodeList / codeList）；``left join car_info`` 让两个条件落在 ``c.`` 列上。
    application.include_router(manager_warning_info_router)
    # Java: CarSuspiciousBackController -- ``/manager/carsuspiciousback/**``。
    # ``export`` 走 ``ExcelUtil<CarSuspiciousBack>``（sheet ``可疑车辆备份数据``）。
    application.include_router(manager_suspicious_back_router)
    # Java: CarInfoController -- ``/manager/carinfo/**``。8 个映射；``add`` 在 Java 里
    # **没有** ``@PreAuthorize``（照抄）；``export`` 走 easypoi 模板 ``carInfo.xlsx``；
    # ``POST /import`` 用 ``ImportSysUtil`` + ``ImportUtil.importExcel``（字典是
    # ``selectDictDataLaleMap``，即"标签 -> 值"）。
    application.include_router(manager_car_info_router)
    # Java: CarTrackInfoController -- ``/manager/cartrackinfo/**``。10 个映射；
    # ``listByCarId`` 本库无数据时回源 ``/base/sysutil/carTrackQueryByCarNo`` 并回写
    # ``zdata_trail_tracks``；``changeTrailInfo`` 先写 ``car_query_log`` 再算几何。
    # 注册顺序：``/{id}`` 在模块内最后声明，不会吞掉 ``/listByCarId`` 这类静态路径。
    application.include_router(manager_car_track_info_router)
    # Java: CarSuspiciousController -- ``/manager/suspicious/**``。15 个映射，只读接口都带
    # ``@PreAuthorize``；模块内 ``/{id}`` 声明在所有静态 GET 之后（FastAPI 按声明顺序匹配）。
    # 导出走 easypoi Word 模板 ``carSuspicious.docx`` + xlsx 模板 ``carSuspicious.xlsx``。
    application.include_router(manager_suspicious_router)
    # Java: CarExceptRecordController -- ``/manager/exceptrecord/**``。13 个映射，整体
    # **没有** ``@PreAuthorize``（照抄）；``epsId == null`` 时查询参数塞 ``-1``。
    application.include_router(manager_car_except_record_router)
    # Java: CarConfimFreeController -- ``/manager/confimfree/**``。13 个映射，整体
    # **没有** ``@PreAuthorize``；三个导出走 easypoi 模板（carConfirm / concernedList /
    # carStatistics）。模块内 ``/{id}`` 声明在所有静态 GET 之后。
    application.include_router(manager_car_confim_free_router)
    # Java: CarAduitFreeController -- ``/manager/aduitfree/**``。10 个映射，同样**没有**
    # ``@PreAuthorize``；``export`` 走 ``ExcelUtil``（sheet 名 ``补缴处理数据``）。
    application.include_router(manager_car_aduit_free_router)
    # Java: BigScreenController -- ``/manager/bigScreen/**``（**路径是驼峰**）。12 个映射，
    # 整个类**没有** ``@PreAuthorize``；``exceptRecordList`` 逐行补 ``orgId`` /
    # ``supplementaryStatus``（N+1，Java 原样）。
    application.include_router(manager_big_screen_router)

    # ---- flow 包（``/flow/**``）----
    # Java: FlowApplyInfoController -- ``/flow/applyinfo/**``。7 个映射，只有 ``/listAll``
    # 保留 ``@PreAuthorize``；``/list`` 会在控制器里 ``setCreateBy`` 限定"我的"。
    application.include_router(flow_apply_info_router)
    # Java: FlowCurrentNodeController -- ``/flow/currentnode/**``。10 个映射，整体**没有**
    # ``@PreAuthorize``；``/getInfoByBillId/{billOid}`` 查不到时回显查询对象而不是 ``null``。
    application.include_router(flow_current_node_router)
    # Java: FlowListController -- ``/flow/flowlist/**``。7 个映射，无权限；``/listnew`` 会在
    # 审核历史末尾补一条"待审批"/"流程结束"。
    application.include_router(flow_list_router)
    # Java: FlowMessageDisposeController -- ``/flow/messagedispose/**``。8 个映射，无权限；
    # ``/delmes/{mid}`` 是**物理**删除自己的处理记录。
    application.include_router(flow_message_dispose_router)
    # Java: FlowMessageInfoController -- ``/flow/messageinfo/**``。8 个映射，无权限；Java 的
    # POST/PUT 在块注释里，所以**不注册**。``/exportShrz`` 走 easypoi 模板。
    application.include_router(flow_message_info_router)
    # Java: FlowNameController -- ``/flow/flowname/**``。8 个映射，逐个挂 ``@PreAuthorize``；
    # ``/listQuery`` 例外（无权限，且按租户过滤）。
    application.include_router(flow_name_router)
    # Java: FlowTemplateController -- ``/flow/flowtemplate/**``。7 个映射，无权限；
    # ``/flowlist`` 在头部插一条虚拟节点（``id=-1`` / ``nodeKey=tj``）。
    application.include_router(flow_template_router)

    # Java: ResourcesConfig#addResourceHandlers --
    #   registry.addResourceHandler(Constants.RESOURCE_PREFIX + "/**")
    #           .addResourceLocations("file:" + RuoYiConfig.getProfile() + "/");
    # 上传/头像在库里存的是相对 url（``/profile/upload/...``、``/profile/avatar/...``），
    # 前端 <img :src> 直接用它，必须由后端提供静态映射，否则这些 url 全部 404。
    #
    # check_dir=False：Java 的资源处理器在目录不存在时不影响启动，只在请求时 404；
    # StaticFiles 默认 check_dir=True 会在 create_app() 时抛 RuntimeError，改变启动行为。
    application.mount(
        "/profile",
        StaticFiles(directory=Path(settings.ruoyi.profile), check_dir=False),
        name="profile",
    )

    if settings.app.health_endpoint_enabled:
        application.include_router(health_router)

    return application


app = create_app()
