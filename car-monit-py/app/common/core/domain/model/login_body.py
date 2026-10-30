"""用户登录对象 / the ``POST /login`` request body.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginBody.java

``uuid`` defaults to ``""``, **not** ``None``
--------------------------------------------
Java declares ``private String uuid = "";``. That default is observable: when the client
omits ``uuid``, ``SysLoginService`` builds the Redis key ``"captcha_codes:" +
""`` -> ``captcha_codes:``; an **explicit** ``"uuid": null`` produces the literal
``captcha_codes:null`` instead. Neither key ever exists, so both end up as
"验证码已失效", but the log line and the key differ -- keep the ``""`` default.

No ``@Valid`` on the Java parameter, so nothing is validated here
-----------------------------------------------------------------
A missing ``username``/``password`` is not a 400. It reaches
``CommonUtil.checkPassword("")``, which fails the pattern, and the client gets the
password-strength error message -- reproduced verbatim by the controller.
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class LoginBody(DomainModel):
    """Java: ``LoginBody``."""

    #: 用户名
    username: Optional[str] = None

    #: 用户密码
    password: Optional[str] = None

    #: 验证码
    code: Optional[str] = None

    #: 唯一标识 -- Java initialiser, see the module docstring
    uuid: Optional[str] = ""


__all__ = ["LoginBody"]
