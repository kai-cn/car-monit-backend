"""参数配置 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java

8 个映射，全部迁移
------------------
=============================  ======================  =============================
Java                           Method / Path            权限点
=============================  ======================  =============================
``list``                       GET ``/list``            ``system:config:list``
``export``                     GET ``/export``          ``system:config:export``
``getInfo``                    GET ``/{configId}``      ``system:config:query``
``getConfigKey``               GET ``/configKey/{key}`` **无**（登录即可）
``add``                        POST ``""``              ``system:config:add``
``edit``                       PUT ``""``               ``system:config:edit``
``remove``                     DELETE ``/{configIds}``  ``system:config:remove``
``clearCache``                 DELETE ``/clearCache``   ``system:config:remove``
=============================  ======================  =============================

``export`` 返回的是**文件名**，不是文件内容
---------------------------------------------
Java 是 ``return util.exportExcel(list, "参数数据")``，而 ``ExcelUtil`` 里的
``AjaxResult.success(filename)`` 命中的是 ``success(String)`` 重载 —— 于是文件名落在
``msg`` **而不是** ``data``。响应长这样::

    {"code": 200, "msg": "3f2a..._参数数据.xlsx"}

文件本身写到了 ``{ruoyi.profile}/download/`` 下，前端拿 ``msg`` 去调
``GET /common/download?fileName=...`` 才能真正下载（见 ``CommonController``）。

``getConfigKey`` 没有权限点
---------------------------
Java 源码上**没有** ``@PreAuthorize``（其余 6 个都有）。它是前端"按参数键名取值"
的数据源（登录页、字典之外的开关），补上权限会让没有参数管理权限的用户白屏。
与 ``dict/type/optionselect``、``notice/list`` 同类，别"顺手"补。

注册顺序（不是装饰性的）
------------------------
FastAPI 按**注册顺序**匹配，Spring 的 ``AntPathMatcher`` 优先字面量。模块里的顺序是：

::

    /list -> /export -> /configKey/{key} -> /{configId} -> POST "" -> PUT "" -> DELETE /clearCache -> DELETE /{configIds}

``/export`` **必须**排在 ``/{configId}`` 之前，否则 ``"export"`` 会在
``config_id: int`` 处转换失败。``/clearCache`` 同理必须排在 ``/{configIds}`` 之前，
否则 ``DELETE /system/config/clearCache`` 会被当成 ``configIds = "clearCache"``
而在 ``parse_id_array`` 处抛错。
``/list`` 与 ``/configKey/...`` 同理必须排在 ``/{configId}`` 之前。

``add`` / ``edit`` 的唯一性校验在写库之前
-----------------------------------------
``checkConfigKeyUnique`` 返回 ``"1"`` 时直接 ``AjaxResult.error(...)``，
**HTTP 200 + code 500** 且**不写库**。两条文案插的都是 ``configName``
（参数名称），不是 ``configKey``：

* ``"新增参数'" + config.getConfigName() + "'失败，参数键名已存在"``
* ``"修改参数'" + config.getConfigName() + "'失败，参数键名已存在"``

另外 ``add`` 上有 ``@RepeatSubmit`` —— 由 :func:`app.framework.interceptor.repeat_submit`
守卫：同一个 ``Authorization`` 头在 5 秒内用**完全相同的 body** 再提交一次，第二次
返回 ``{"code":500,"msg":"不允许重复提交，请稍候再试"}``（HTTP 200），且**不写库**。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.common.constant.user_constants import NOT_UNIQUE_OLD
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
    to_ajax,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.bean_validation import validate
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.interceptor.repeat_submit_interceptor import repeat_submit
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.sys_config import CONFIG_CONSTRAINTS, SysConfig
from app.system.service.sys_config_service import SysConfigService, get_config_service

router = APIRouter(prefix="/system/config", tags=["system-config"])

#: Java: ``com.ruoyi.web.controller.system.SysConfigController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysConfigController"

#: Java: ``"新增参数'" + config.getConfigName() + "'失败，参数键名已存在"``
ADD_CONFIG_EXISTS = "新增参数'{}'失败，参数键名已存在"
#: Java: ``"修改参数'" + config.getConfigName() + "'失败，参数键名已存在"``
EDIT_CONFIG_EXISTS = "修改参数'{}'失败，参数键名已存在"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysConfigService configService``。Spring 默认单例，
# 这里用模块级缓存复刻；测试直接替换 ``controller._CONFIG_SERVICE``。

_CONFIG_SERVICE: SysConfigService | None = None


def _config_service() -> SysConfigService:
    global _CONFIG_SERVICE
    if _CONFIG_SERVICE is None:
        _CONFIG_SERVICE = get_config_service()
    return _CONFIG_SERVICE


def reset_config_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _CONFIG_SERVICE
    _CONFIG_SERVICE = None


def _query_config(request: Request) -> SysConfig:
    """Java: 形参 ``SysConfig config``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysConfig, request.query_params)


#: 查询条件实体（``?configName=...&configType=...&params[beginTime]=...``）。
ConfigParam = Annotated[SysConfig, Depends(_query_config)]


def _validated_config(config: SysConfig) -> SysConfig:
    """Java: ``@Validated @RequestBody SysConfig``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` **之前** ——
    Spring MVC 先解析/校验参数，再进入方法代理。
    """
    validate(config, CONFIG_CONSTRAINTS)
    return config


#: 已校验的请求体。
ValidConfig = Annotated[SysConfig, Depends(_validated_config)]


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("system:config:list")
def list_configs(config: ConfigParam) -> TableDataInfo:
    """获取参数配置列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysConfig config)``.

    这条语句**没有** ``order by``，所以前端点表头排序是生效的（PageHelper 会追加），
    而不点排序时返回顺序由 MySQL 决定。
    """
    start_page()
    rows = _config_service().select_config_list(config)
    return get_data_table(rows)


@router.get("/export", response_model=None)
@pre_authorize_permi("system:config:export")
@log(title="参数管理", business_type=BusinessType.EXPORT, java_method="export")
def export(config: ConfigParam) -> AjaxResult:
    """导出参数配置. Java: ``@GetMapping("/export") public AjaxResult export(SysConfig config)``.

    ``export`` 拿的是**全量**结果（不受 ``startPage`` 影响），因为 Java 侧
    这里直接调 ``selectConfigList`` 而没有 ``startPage()``。

    返回体里的 ``msg`` 是生成的**文件名**，不是文件内容 —— 见模块文档。
    """
    rows = _config_service().select_config_list(config)
    return ExcelUtil(SysConfig).export_excel(rows, "参数数据")


@router.get("/configKey/{config_key}", response_model=None)
def get_config_key(config_key: str) -> AjaxResult:
    """根据参数键名查询参数值. Java: ``@GetMapping(value = "/configKey/{configKey}")``.

    没有 ``@PreAuthorize``，登录即可。查不到时 ``data`` 是**空串**
    （``StringUtils.EMPTY``），不是 ``null``。
    """
    return AjaxResult.success_data(_config_service().select_config_by_key(config_key))


@router.get("/{config_id}", response_model=None)
@pre_authorize_permi("system:config:query")
def get_info(config_id: int) -> AjaxResult:
    """查询参数配置详细. Java: ``@GetMapping(value = "/{configId}")``.

    查不到时 ``data`` 为 ``null``（不是 404）。
    """
    return AjaxResult.success_data(_config_service().select_config_by_id(config_id))


# --------------------------------------------------------------------------- 增删改


@router.post("", response_model=None, dependencies=[Depends(repeat_submit())])
@pre_authorize_permi("system:config:add")
@log(title="参数管理", business_type=BusinessType.INSERT, java_method="add")
def add(config: ValidConfig) -> AjaxResult:
    """新增参数配置. Java: ``@PostMapping public AjaxResult add(@Validated @RequestBody SysConfig config)``.

    唯一性校验失败时返回 ``AjaxResult.error(...)``（HTTP 200 + code 500），**不写库**。
    """
    if NOT_UNIQUE_OLD == _config_service().check_config_key_unique(config):
        return AjaxResult.error_message(ADD_CONFIG_EXISTS.format(config.config_name))
    config.create_by = SecurityUtils.get_username()
    return to_ajax(_config_service().insert_config(config))


@router.put("", response_model=None)
@pre_authorize_permi("system:config:edit")
@log(title="参数管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(config: ValidConfig) -> AjaxResult:
    """修改参数配置. Java: ``@PutMapping public AjaxResult edit(@Validated @RequestBody SysConfig config)``."""
    if NOT_UNIQUE_OLD == _config_service().check_config_key_unique(config):
        return AjaxResult.error_message(EDIT_CONFIG_EXISTS.format(config.config_name))
    config.update_by = SecurityUtils.get_username()
    return to_ajax(_config_service().update_config(config))


@router.delete("/clearCache", response_model=None)
@pre_authorize_permi("system:config:remove")
@log(title="参数管理", business_type=BusinessType.CLEAN, java_method="clearCache")
def clear_cache() -> AjaxResult:
    """清空缓存. Java: ``@DeleteMapping("/clearCache")``.

    只删 Redis 里的 ``sys_config:*``，**不动库**。下一次按键取值会回源重新填充。
    必须注册在 ``/{config_ids}`` 之前。
    """
    _config_service().clear_cache()
    return AjaxResult.success()


@router.delete("/{config_ids}", response_model=None)
@pre_authorize_permi("system:config:remove")
@log(title="参数管理", business_type=BusinessType.DELETE, java_method="remove")
def remove(config_ids: str) -> AjaxResult:
    """删除参数配置. Java: ``@DeleteMapping("/{configIds}")``.

    批里任何一条是内置参数（``config_type = "Y"``）就抛 ``CustomException`` ->
    HTTP 200 + code 500，**整批都不删**。
    """
    return to_ajax(_config_service().delete_config_by_ids(parse_id_array(config_ids)))


__all__ = [
    "router",
    "ADD_CONFIG_EXISTS",
    "EDIT_CONFIG_EXISTS",
    "ConfigParam",
    "ValidConfig",
    "list_configs",
    "export",
    "get_config_key",
    "get_info",
    "add",
    "edit",
    "clear_cache",
    "remove",
    "reset_config_controller",
]
