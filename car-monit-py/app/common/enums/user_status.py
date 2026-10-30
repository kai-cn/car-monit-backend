"""User account status.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/UserStatus.java

Java uses an ``enum`` carrying two fields (``code`` stored in ``sys_user.status`` /
``sys_user.del_flag``, and ``info`` used only in logs). Python's ``enum.Enum`` is the
closest construct; :meth:`UserStatus.get_code` / :meth:`UserStatus.get_info` keep the Java
accessor names so call sites such as
``UserStatus.DELETED.get_code().equals(user.getDelFlag())`` translate mechanically.
"""

from __future__ import annotations

from enum import Enum


class UserStatus(Enum):
    """用户状态."""

    # Java: OK("0", "正常")
    OK = ("0", "正常")
    # Java: DISABLE("1", "停用")
    DISABLE = ("1", "停用")
    # Java: DELETED("2", "删除")
    DELETED = ("2", "删除")

    def __init__(self, code: str, info: str) -> None:
        self.code = code
        self.info = info

    # Java: public String getCode()
    def get_code(self) -> str:
        return self.code

    # Java: public String getInfo()
    def get_info(self) -> str:
        return self.info


__all__ = ["UserStatus"]
