"""用户常量信息.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/UserConstants.java

Java declared ``public static final`` fields; Python has no constants, so this is a
namespace of module-level values. Every literal is copied verbatim -- several leak into
HTTP responses (``LAYOUT`` / ``ParentView`` component names, the ``M``/``C``/``F`` menu
types), so changing one changes what the frontend receives.

``UNIQUE`` / ``NOT_UNIQUE`` are Java ``boolean``s, i.e. real booleans here, while
``UNIQUE_OLD`` / ``NOT_UNIQUE_OLD`` are ``String``s -- the project uses the string pair in
its own ``checkMenuNameUnique`` / ``checkDeptNameUnique`` implementations.
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------- 状态

#: 平台内系统用户的唯一标志
SYS_USER: Final[str] = "SYS_USER"
#: 正常状态
NORMAL: Final[str] = "0"
#: 异常状态
EXCEPTION: Final[str] = "1"
#: 用户封禁状态
USER_DISABLE: Final[str] = "1"
#: 角色封禁状态
ROLE_DISABLE: Final[str] = "1"
#: 部门正常状态
DEPT_NORMAL: Final[str] = "0"
#: 部门停用状态
DEPT_DISABLE: Final[str] = "1"
#: 字典正常状态
DICT_NORMAL: Final[str] = "0"
#: 是否为系统默认（是）
YES: Final[str] = "Y"

# --------------------------------------------------------------------------- 菜单

#: 是否菜单外链（是）-- 注意语义是反的：``0`` 才是外链
YES_FRAME: Final[str] = "0"
#: 是否菜单外链（否）
NO_FRAME: Final[str] = "1"
#: 菜单类型（目录）
TYPE_DIR: Final[str] = "M"
#: 菜单类型（菜单）
TYPE_MENU: Final[str] = "C"
#: 菜单类型（按钮）
TYPE_BUTTON: Final[str] = "F"
#: Layout组件标识
LAYOUT: Final[str] = "Layout"
#: ParentView组件标识
PARENT_VIEW: Final[str] = "ParentView"
#: InnerLink组件标识
INNER_LINK: Final[str] = "InnerLink"

# --------------------------------------------------------------------------- 校验

#: 校验是否唯一的返回标识
UNIQUE: Final[bool] = True
#: 校验是否唯一的返回标识
NOT_UNIQUE: Final[bool] = False
#: 校验返回结果码（本项目自用，与上面的 boolean 并存）
UNIQUE_OLD: Final[str] = "0"
#: 校验返回结果码（本项目自用）
NOT_UNIQUE_OLD: Final[str] = "1"

#: 用户名长度限制
USERNAME_MIN_LENGTH: Final[int] = 2
#: 用户名长度限制
USERNAME_MAX_LENGTH: Final[int] = 20
#: 密码长度限制
PASSWORD_MIN_LENGTH: Final[int] = 5
#: 密码长度限制
PASSWORD_MAX_LENGTH: Final[int] = 20

#: 新增用户默认密码
DEFAULT_PWD: Final[str] = "Sys@cg0624!"


__all__ = [
    "SYS_USER",
    "NORMAL",
    "EXCEPTION",
    "USER_DISABLE",
    "ROLE_DISABLE",
    "DEPT_NORMAL",
    "DEPT_DISABLE",
    "DICT_NORMAL",
    "YES",
    "YES_FRAME",
    "NO_FRAME",
    "TYPE_DIR",
    "TYPE_MENU",
    "TYPE_BUTTON",
    "LAYOUT",
    "PARENT_VIEW",
    "INNER_LINK",
    "UNIQUE",
    "NOT_UNIQUE",
    "UNIQUE_OLD",
    "NOT_UNIQUE_OLD",
    "USERNAME_MIN_LENGTH",
    "USERNAME_MAX_LENGTH",
    "PASSWORD_MIN_LENGTH",
    "PASSWORD_MAX_LENGTH",
    "DEFAULT_PWD",
]
