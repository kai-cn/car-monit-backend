"""自定义操作日志记录注解 / the ``@Log`` annotation.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/annotation/Log.java

Java 是编译期元数据，由 ``LogAspect`` 在运行时读；Python 没有注解，这里落成一个
``frozen dataclass``（纯数据，不含任何行为），由 :func:`app.framework.aspectj.log_aspect.log`
构造，并在控制器上以**装饰器**的形式出现::

    @router.post("", response_model=None)
    @pre_authorize_permi("system:post:add")
    @log(title="岗位管理", business_type=BusinessType.INSERT, java_method="add")
    def add(post: ValidPost) -> AjaxResult:
        ...

装饰器放在**最里面**（紧贴 ``def``），对应 Spring 里的优先级关系：
``@PreAuthorize``（``AuthorizationManagerBeforeMethodInterceptor``，order 200）排在
``LogAspect``（``@Aspect`` 默认 ``LOWEST_PRECEDENCE``）**外层**，所以被权限拒绝的请求
**不会**留下审计记录。放在外层就反了。

字段默认值与 Java 的 ``default`` 逐字一致
------------------------------------------
=====================  =========================  ==============
字段                    Java ``default``          本工程用法
=====================  =========================  ==============
``title``              ``""``                     每次都显式给
``business_type``      ``BusinessType.OTHER``     每次都显式给
``operator_type``      ``OperatorType.MANAGE``    **从不显式给**（218 处全是默认）
``is_save_request_data``   ``true``              从不显式给
``is_save_response_data``  ``true``              从不显式给
``exclude_param_names``    ``{}``                从不显式给
=====================  =========================  ==============

``java_method`` 是**本工程新增**的字段，Java 没有
-----------------------------------------------
Java 的 ``method`` 列来自反射：``joinPoint.getTarget().getClass().getName() + "." +
joinPoint.getSignature().getName() + "()"``，也就是 ``com.ruoyi.web.controller.system.
SysPostController.add()``。Python 的函数名是 ``snake_case``（``change_status`` vs
``changeStatus``），无法从函数名反推 Java 名，所以显式声明。全类名见各控制器模块的
``JAVA_CONTROLLER`` 常量。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from app.common.enums.business_type import BusinessType
from app.common.enums.operator_type import OperatorType


@dataclass(frozen=True)
class Log:
    """Java: ``@interface Log`` —— 操作日志注解的等价物（纯数据）."""

    #: 模块. Java: ``public String title() default ""``
    title: str = ""
    #: 功能. Java: ``public BusinessType businessType() default BusinessType.OTHER``
    business_type: BusinessType = BusinessType.OTHER
    #: 操作人类别. Java: ``public OperatorType operatorType() default OperatorType.MANAGE``
    operator_type: OperatorType = OperatorType.MANAGE
    #: 是否保存请求的参数. Java: ``public boolean isSaveRequestData() default true``
    is_save_request_data: bool = True
    #: 是否保存响应的参数. Java: ``public boolean isSaveResponseData() default true``
    is_save_response_data: bool = True
    #: 排除指定的请求参数（额外排除，叠加在 ``LogAspect.EXCLUDE_PROPERTIES`` 之上）.
    #: Java: ``public String[] excludeParamNames() default {}``
    exclude_param_names: Tuple[str, ...] = field(default_factory=tuple)
    #: Java 方法名 —— 仅用于拼 ``sys_oper_log.method``，见模块 docstring。
    java_method: str = ""


__all__ = ["Log"]
