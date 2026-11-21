"""定时任务调度测试 bean（``@Component("ryTask")``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/RyTask.java

四个方法**全部是空壳**（只打印），是 RuoYi 自带的"手工触发验证调度器是否工作"用的
示例任务。线上 ``sys_job`` 表里 4 条默认数据就指向它::

    ryTask.ryNoParams
    ryTask.ryParams('ry')
    ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)

``ryMultipleParams`` 是**唯一**一条同时用到 5 种参数类型的调用目标，因此它也是
:mod:`app.quartz.util.job_invoke_util` 的类型判定顺序（``'`` -> Boolean -> Long ->
Double -> Integer）的"活体用例"：``316.50D`` 只有先被 ``D`` 命中才不会落进
``Integer``。

输出走 ``System.out``
---------------------
Java 用的是 ``System.out.println`` 而不是日志，所以这里也用 :func:`print`；
把它"升级"成 ``logger.info`` 会让日志级别 / 输出位置与 Java 不一致。

``autoBuildGoodsHb`` 是**空方法体**
------------------------------
Java 里连一行注释都没有，没有任何调用点（``sys_job`` 里也没有对应行），但按
"不删除看似无用的代码"的原则原样迁移。
"""

from __future__ import annotations

from typing import Optional

from app.common.utils import string_utils as StringUtils

#: Java: ``@Component("ryTask")`` 的 Bean 名 —— ``JobInvokeUtil.getBeanName`` 按点号切出来的第一段。
BEAN_NAME = "ryTask"


class RyTask:
    """Java: ``class RyTask``（``@Component("ryTask")``）."""

    # Java: public void ryMultipleParams(String s, Boolean b, Long l, Double d, Integer i)
    def ry_multiple_params(
        self,
        s: str,
        b: Optional[bool],
        length: Optional[int],
        d: Optional[float],
        i: Optional[int],
    ) -> None:
        """多参方法.

        Java 的 ``System.out.println`` 里 ``StringUtils.format`` 的占位符是 ``{}``，
        按**出现顺序**逐个替换；``Boolean`` / ``Long`` / ``Double`` / ``Integer`` 走
        ``toString()``（``true`` / ``2000`` / ``316.5`` / ``100``）。
        """
        print(
            StringUtils.format(
                "执行多参方法： 字符串类型{}，布尔类型{}，长整型{}，浮点型{}，整形{}",
                s,
                _java_str(b),
                _java_str(length),
                _java_str(d),
                _java_str(i),
            )
        )

    # Java: public void ryParams(String params)
    def ry_params(self, params: Optional[str]) -> None:
        """有参方法（字符串直接拼接，``null`` 会拼成 ``"null"``）。"""
        print("执行有参方法：" + _java_str(params))

    # Java: public void ryNoParams()
    def ry_no_params(self) -> None:
        print("执行无参方法")

    # Java: public void autoBuildGoodsHb()  —— 空方法体，Java 原文如此
    def auto_build_goods_hb(self) -> None:
        """空方法体（Java 里没有任何语句，也没有调用点）。"""


def _java_str(value: object) -> str:
    """Java 字符串拼接 / ``String.valueOf`` 对 ``null`` 的写法是 ``"null"``."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        # Java 的 ``Boolean.toString`` / ``String.valueOf(boolean)`` 是**小写**，
        # Python 的 ``str(True)`` 是 ``"True"`` —— 线上日志里是 ``布尔类型true``。
        return "true" if value else "false"
    return str(value)


__all__ = ["BEAN_NAME", "RyTask"]
