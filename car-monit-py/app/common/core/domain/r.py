"""响应信息主体 / the generic ``R<T>`` response envelope.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/R.java

``R`` 与 :class:`~app.common.core.domain.ajax_result.AjaxResult` 的两点区别
----------------------------------------------------------------------------
两者都回 ``code`` / ``msg`` / ``data``，但**序列化形状不同**，很容易搞混：

=========================================  ==============================  ==============================
场景                                       ``AjaxResult``                  ``R``
=========================================  ==============================  ==============================
``data`` 为 ``null``                        **省略** ``data`` 键             **保留** ``"data": null``
键的顺序                                   ``code`` / ``msg`` / ``data``    ``code`` / ``msg`` / ``data``
默认文案                                   "操作成功" / "操作失败"           "操作成功" / "操作失败"
=========================================  ==============================  ==============================

``AjaxResult`` 是 ``HashMap`` 子类，``put("data", null)`` 会被
``StringUtils.isNotNull`` 挡掉；``R`` 是普通 POJO，``data`` 字段**总会**被 Jackson
写出去。前端对两者的处理也因此不同（``R`` 的 ``data === null`` 是可靠的"无数据"信号）。

重载映射（Java 的重载在 Python 里没有对应物，每个 arity 一个显式名字）
----------------------------------------------------------------------
    ==========================================  =========================================
    Java                                        Python
    ==========================================  =========================================
    ``R.ok()``                                   :meth:`R.ok`
    ``R.ok(T data)``                             :meth:`R.ok_data`
    ``R.ok(T data, String msg)``                 :meth:`R.ok_data_msg`
    ``R.fail()``                                 :meth:`R.fail`
    ``R.fail(String msg)``                       :meth:`R.fail_msg`
    ``R.fail(T data)``                           :meth:`R.fail_data`
    ``R.fail(T data, String msg)``               :meth:`R.fail_data_msg`
    ``R.fail(int code, String msg)``             :meth:`R.fail_code`
    ==========================================  =========================================

``fail(T data)`` 与 ``fail(String msg)`` 在 Java 里靠**静态类型**区分：``TestController``
的 ``R.fail("用户不存在")`` 里字符串字面量的类型是 ``String``，编译器选中的是
``fail(String msg)``（而不是 ``fail(T data)``）。Python 没有这层区分，所以调用点必须
显式挑 :meth:`R.fail_msg` —— 选错会让"用户不存在"跑到 ``data`` 里。
"""

from __future__ import annotations

from typing import Any

from app.common.constant.http_status import HttpStatus


class R(dict):
    """响应信息主体 / response envelope that **always** carries ``data``."""

    CODE_TAG = "code"
    MSG_TAG = "msg"
    DATA_TAG = "data"

    #: Java: ``public static final int SUCCESS = HttpStatus.SUCCESS``.
    SUCCESS = HttpStatus.SUCCESS
    #: Java: ``public static final int FAIL = HttpStatus.ERROR``.
    FAIL = HttpStatus.ERROR

    # Java: private static <T> R<T> restResult(T data, int code, String msg)
    @classmethod
    def _rest_result(cls, data: Any, code: int, msg: str) -> "R":
        result = cls()
        # 键序 = Jackson 的 getter 发现顺序（getCode -> getMsg -> getData）。
        dict.__setitem__(result, cls.CODE_TAG, code)
        dict.__setitem__(result, cls.MSG_TAG, msg)
        # 与 AjaxResult 相反：这里**永远**写 data，null 也写。
        dict.__setitem__(result, cls.DATA_TAG, data)
        return result

    # Java: public static <T> R<T> ok()
    @classmethod
    def ok(cls) -> "R":
        return cls._rest_result(None, cls.SUCCESS, "操作成功")

    # Java: public static <T> R<T> ok(T data)
    @classmethod
    def ok_data(cls, data: Any) -> "R":
        return cls._rest_result(data, cls.SUCCESS, "操作成功")

    # Java: public static <T> R<T> ok(T data, String msg)
    @classmethod
    def ok_data_msg(cls, data: Any, msg: str) -> "R":
        return cls._rest_result(data, cls.SUCCESS, msg)

    # Java: public static <T> R<T> fail()
    @classmethod
    def fail(cls) -> "R":
        return cls._rest_result(None, cls.FAIL, "操作失败")

    # Java: public static <T> R<T> fail(String msg)
    @classmethod
    def fail_msg(cls, msg: str) -> "R":
        return cls._rest_result(None, cls.FAIL, msg)

    # Java: public static <T> R<T> fail(T data)
    @classmethod
    def fail_data(cls, data: Any) -> "R":
        return cls._rest_result(data, cls.FAIL, "操作失败")

    # Java: public static <T> R<T> fail(T data, String msg)
    @classmethod
    def fail_data_msg(cls, data: Any, msg: str) -> "R":
        return cls._rest_result(data, cls.FAIL, msg)

    # Java: public static <T> R<T> fail(int code, String msg)
    @classmethod
    def fail_code(cls, code: int, msg: str) -> "R":
        return cls._rest_result(None, code, msg)

    # Java: public static <T> Boolean isSuccess(R<T> ret)
    @staticmethod
    def is_success(ret: "R") -> bool:
        return ret.get(R.CODE_TAG) == R.SUCCESS

    # Java: public static <T> Boolean isError(R<T> ret)
    @staticmethod
    def is_error(ret: "R") -> bool:
        return not R.is_success(ret)


__all__ = ["R"]
