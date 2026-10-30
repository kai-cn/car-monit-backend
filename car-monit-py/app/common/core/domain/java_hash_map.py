"""``HashMap`` 迭代序的最小复刻 / the bit of ``java.util.HashMap`` we actually need.

# Migrated from: java.util.HashMap (iteration order only)

为什么要复刻
------------
``AjaxResult`` / ``TableDataInfo`` / ``R`` 三者里，只有 ``AjaxResult`` 是 ``HashMap``::

    public class AjaxResult extends HashMap<String, Object>

另外两个都是普通 POJO，Jackson 按**字段声明序**输出：``TableDataInfo`` 是
``total, rows, code, msg``；``R<T> implements Serializable``（见 ``R.java:11``）是
``code, msg, data`` —— **不要**把 ``R`` 当成 ``HashMap`` 而把键序改掉。

``HashMap`` 的迭代序**不是插入序**，而是"桶号升序"：桶号由
``(h = key.hashCode()) ^ (h >>> 16)`` 的低 4 位决定（默认容量 16）。于是在 Java 侧
``AjaxResult.success()`` 的真实 JSON 是::

    {"msg":"操作成功","code":200}

而不是先 ``code`` 后 ``msg`` —— 这正是 RuoYi 全站响应的样子（``msg`` 在前）。

Python 的 ``dict`` 是插入序，如果照着 ``new AjaxResult(code, msg)`` 的赋值顺序写，
键序就会反过来。本模块把这个"反直觉但对外可见"的顺序算出来。

对照表（默认容量 16；本项目出现过的键全列在这里）
------------------------------------------------------
    ====  ==========================================================
    桶号  键（同桶内保持 put 的先后）
    ====  ==========================================================
    0     ``msg`` / ``postGroup`` / ``imgUrl``
    2     ``img`` / ``fileName`` / ``urls``
    3     ``code`` / ``roleIds`` / ``pjFlag``
    4     ``data`` / ``newFileNames`` / ``overdue``
    6     ``postIds`` / ``permissions``
    7     ``roles``
    9     ``newFileName``
    11    ``menus``
    13    ``uuid`` / ``posts`` / ``roleGroup`` / ``user``
    14    ``url`` / ``originalFilename`` / ``fileNames`` /
          ``originalFilenames`` / ``users`` / ``depts``
    15    ``token`` / ``checkedKeys``
    ====  ==========================================================

几个实际响应的最终键序::

    AjaxResult.success()                                 msg, code
    success().put("token", t)                            msg, code, token
    success().put("uuid").put("img")                     msg, img, code, uuid
    success().put("checkedKeys").put("depts")             msg, code, depts, checkedKeys
    SysUserController.getInfo(userId)                    msg, code, roleIds, data,
                                                         postIds, roles, posts

前三行是登录 / 验证码 / ``roleDeptTreeselect`` 的真实输出顺序。

同桶内的顺序
------------
``HashMap`` 在同一个桶里按**插入序**遍历（链表长度 < 8，本项目不可能触发树化），
所以这里用稳定排序：同桶的元素保持原有先后。

容量
----
``HashMap`` 默认容量 16、装载因子 0.75，第 13 个键会扩容到 32 并重排。
本项目键最多的是 ``SysUserController.getInfo``，7 个（``msg`` / ``code`` / ``roles`` /
``posts`` / ``data`` / ``postIds`` / ``roleIds``），远达不到阈值，
所以只实现容量 16 的桶号；真到了 13 个键，``put_in_order`` 会退化成插入序
（比"算错桶号"更安全）。
"""

from __future__ import annotations

from typing import Any, MutableMapping

#: ``HashMap`` 默认容量。
DEFAULT_CAPACITY = 16

#: 超过这个键数就该扩容重排了（``capacity * 0.75`` 的整型上限）。
_RESIZE_THRESHOLD = 12

_MASK_32 = 0xFFFFFFFF


def java_string_hash(value: str) -> int:
    """Java: ``String#hashCode()`` —— ``s[0]*31^(n-1) + ... + s[n-1]``，32 位有符号."""
    result = 0
    for char in value:
        result = (result * 31 + ord(char)) & _MASK_32
    return result - 0x100000000 if result >= 0x80000000 else result


def bucket_index(key: str, capacity: int = DEFAULT_CAPACITY) -> int:
    """Java: ``HashMap#hash(key) & (capacity - 1)`` —— 桶号."""
    unsigned = java_string_hash(key) & _MASK_32
    spread = (unsigned ^ (unsigned >> 16)) & _MASK_32
    return spread & (capacity - 1)


def put_in_order(target: MutableMapping[str, Any], key: str, value: Any) -> None:
    """按 ``HashMap`` 的迭代序写入（已存在的键只改值、**不换位置**）.

    ``dict`` 本身没有"插入到指定位置"的接口，所以重建一次：键数最多 6 个，
    代价可以忽略。
    """
    items = [(existing, current) for existing, current in dict.items(target) if existing != key]
    items.append((key, value))

    if len(items) <= _RESIZE_THRESHOLD:
        items.sort(key=lambda pair: bucket_index(pair[0]))

    dict.clear(target)
    for existing, current in items:
        dict.__setitem__(target, existing, current)


__all__ = [
    "DEFAULT_CAPACITY",
    "bucket_index",
    "java_string_hash",
    "put_in_order",
]
