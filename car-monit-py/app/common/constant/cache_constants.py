"""Redis key prefixes.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/CacheConstants.java

Why this module duplicates entries from :mod:`app.common.constant.constants`
---------------------------------------------------------------------------
The Java project declares ``LOGIN_TOKEN_KEY``, ``CAPTCHA_CODE_KEY``,
``SYS_CONFIG_KEY`` and ``SYS_DICT_KEY`` **twice**: once in ``Constants`` and once in
``CacheConstants``. Both copies carry the same literal, so the duplication is invisible
at runtime -- but call sites reference different classes, and deleting either copy would
change the 1:1 file mapping. Both modules are therefore kept, exactly as in Java.

Which class a call site uses is recorded per migrated file, e.g.
``SysPasswordService`` imports ``CacheConstants`` while ``TokenService`` imports
``Constants``. Do not "clean this up": a future re-sync of the two literals would then
silently diverge from Java.
"""

from __future__ import annotations

from typing import Final

#: 登录用户 redis key
LOGIN_TOKEN_KEY: Final[str] = "login_tokens:"
#: 验证码 redis key
CAPTCHA_CODE_KEY: Final[str] = "captcha_codes:"
#: 参数管理 cache key
SYS_CONFIG_KEY: Final[str] = "sys_config:"
#: 字典管理 cache key
SYS_DICT_KEY: Final[str] = "sys_dict:"
#: 防重提交 redis key
REPEAT_SUBMIT_KEY: Final[str] = "repeat_submit:"
#: 限流 redis key
RATE_LIMIT_KEY: Final[str] = "rate_limit:"
#: 登录账户密码错误次数 redis key
PWD_ERR_CNT_KEY: Final[str] = "pwd_err_cnt:"

__all__ = [
    "LOGIN_TOKEN_KEY",
    "CAPTCHA_CODE_KEY",
    "SYS_CONFIG_KEY",
    "SYS_DICT_KEY",
    "REPEAT_SUBMIT_KEY",
    "RATE_LIMIT_KEY",
    "PWD_ERR_CNT_KEY",
]
