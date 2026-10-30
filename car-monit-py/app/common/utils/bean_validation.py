"""Bean Validation 约束的最小实现 / the subset of ``javax.validation`` this project uses.

# Migrated from: javax.validation.constraints.NotBlank
# Migrated from: javax.validation.constraints.Size
# Migrated from: javax.validation.constraints.Email

Java 把校验注解挂在**实体**的 getter 上（``SysPost.getPostCode`` 等），由
``@Validated @RequestBody`` 触发的 Hibernate Validator 在"请求体反序列化之后、
方法体执行之前"检查。Python 侧有三个做法，这里选了第三种：

1. ``pydantic.Field(..., min_length=...)`` —— 不行。字段是 ``Optional`` 的（查询条件
   实体允许缺字段），约束加在模型上会让 ``bind_query_params`` 绑一半就炸；文案也只能是
   英文的 pydantic 风格，而 Java 抛的是注解里写死的中文 ``message``。
2. 每个端点手写一长串 ``if not post.post_code: return AjaxResult.error(...)`` —— 不行。
   语义不等价：那样返回的是 ``AjaxResult``，而 Java 是**抛异常**，客户端拿到的是
   ``{"code": 500, "msg": ...}``；两者的差别在"有没有 ``msg`` 前缀/是成功还是失败"上
   看不出来，但在"出错时方法体一行都没执行"这一点上完全不同（例如 ``add`` 不会走到
   ``setCreateBy``）。
3. **本模块**：约束声明在实体旁边（与 Java 同位置），端点通过
   :func:`validate` 顺序扫描，第一个违规抛 :class:`BeanValidationError`。

``BeanValidationError`` 继承 ``RuntimeError``，直接落到
``app.config.exception_handlers`` 里那个 ``@ExceptionHandler(RuntimeException.class)``
等价物上 —— ``AjaxResult.error(str(exc))``。而 Java 的
``handleMethodArgumentNotValidException`` 取
``getFieldError().getDefaultMessage()`` 后同样是 ``AjaxResult.error(message)``。
**两边的响应体逐字节相同。**

为什么不用 ``RequestValidationError``
-------------------------------------
``exception_handlers`` 已经给 ``RequestValidationError`` 也绑了
``AjaxResult.error(...)``，但那条路径只能看到 pydantic 的错误（``"Field required"``），
拿不到注解里的中文文案。两个处理器返回的结构一样，因此客户端看不出区别，只有 ``msg``
内容不同 —— 而 ``msg`` 是前端 ``$modal.msgError(response.msg)`` 直接弹给用户看的。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Union

from app.common.utils.string_utils import is_blank

#: Hibernate ``@Email`` 的正则。Java 侧是
#: ``Pattern.compile(".{0,64}@" + DOMAIN_PART_REGEX, CASE_INSENSITIVE)`` 配合 ``matches()``，
#: 所以**整串**必须是 ``本地部分(≤64)@域名``。注意它**不**校验本地部分的字符集 ——
#: ``"a b@c.d"`` 在 Java 里是通过的。这里照抄同一个宽松度，不要"顺手收紧"。
_EMAIL_PATTERN = re.compile(
    r"^.{0,64}@[a-z0-9\-\u0080-\uffff]+(?:\.[a-z0-9\-\u0080-\uffff]+)*$",
    re.IGNORECASE,
)


class BeanValidationError(RuntimeError):
    """Java: ``MethodArgumentNotValidException``.

    只带**一条**信息：违规字段的 ``message``。Java 的
    ``BindingResult`` 会攒下所有违规再取第一个，这里在遇到第一个违规时就抛 ——
    客户端看到的 ``msg`` 一致，且顺序是确定的（按约束表的声明顺序，也就是 Java 源码里
    注解的书写顺序）。

    ``getMessage()`` 那种"把整棵对象树 + 所有违规拼成一段"的文本没有复刻：它只进
    服务端日志，不进响应体。
    """


@dataclass(frozen=True)
class NotBlank:
    """Java: ``@NotBlank(message = "...")``.

    ``null`` / 空串 / 全空白都算违规 —— 与 ``StringUtils.isBlank`` 的判据一致，
    也和 ``javax.validation`` 的 ``NotBlank`` 定义一致（它比 ``@NotEmpty`` 多拒全空白）。
    """

    attribute: str
    message: str


@dataclass(frozen=True)
class Size:
    """Java: ``@Size(min = 0, max = 64, message = "...")``.

    ``null`` **视为通过**：这是 Bean Validation 的通用约定（``@Size`` 只约束长度，
    不管存在性）。所以 ``@NotBlank`` + ``@Size`` 组合起来才是"必填且不超长"。
    """

    attribute: str
    max: int
    message: str
    min: int = 0


@dataclass(frozen=True)
class Email:
    """Java: ``@Email(message = "邮箱格式不正确")``.

    与 ``@Size`` 一样，``null`` 与空串**视为通过** —— Hibernate 的
    ``AbstractEmailValidator`` 第一行就是 ``if ( value == null || value.length() == 0 )
    return true;``。所以 ``@NotBlank`` 与 ``@Email`` 是两件独立的事，只挂 ``@Email`` 的
    字段允许为空。

    实现用的是同一个正则（见 :data:`_EMAIL_PATTERN`）：本地部分允许任意字符但不超过
    64 个，域名必须是点分的 ``[a-z0-9-]``/非 ASCII 片段。中文域名（``@例子.中国``）因此
    能通过 —— 与 Java 一致。
    """

    attribute: str
    message: str


#: :func:`validate` 认得的约束类型。
Constraint = Union[NotBlank, Size, Email]


def validate(entity: Any, constraints: Iterable[Constraint]) -> None:
    """按顺序检查 ``constraints``，第一个违规立即抛 :class:`BeanValidationError`.

    参数
    ----
    entity
        实体实例。约束里的 ``attribute`` 是 **Python 字段名**（``post_code``），
        不是 JSON 别名（``postCode``）—— 实体模型已经用别名接住了外部命名。
    constraints
        该实体的约束表，见 ``app.system.domain.sys_post.POST_CONSTRAINTS``。
    """
    for constraint in constraints:
        value: Optional[Any] = getattr(entity, constraint.attribute, None)

        if isinstance(constraint, NotBlank):
            if is_blank(value):
                raise BeanValidationError(constraint.message)
            continue

        if isinstance(constraint, Email):
            # Hibernate: null 与空串都通过 @Email。
            if value is None or value == "":
                continue
            if not isinstance(value, str):
                value = str(value)
            if _EMAIL_PATTERN.match(value) is None:
                raise BeanValidationError(constraint.message)
            continue

        # Hibernate Validator: null 满足 @Size，不做长度判断。
        if value is None:
            continue
        length = len(value)
        if length < constraint.min or length > constraint.max:
            raise BeanValidationError(constraint.message)


__all__ = [
    "BeanValidationError",
    "Constraint",
    "Email",
    "NotBlank",
    "Size",
    "validate",
]
