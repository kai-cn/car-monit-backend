"""``SysOperLogMapper`` —— SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysOperLogMapper.java

这一层为什么值钱
----------------
操作日志的 `<if>` 链路一旦拼错，接口**不会报错**，只会悄悄多查/少查一批行。
这里有四处改错了只会在生产上慢慢发现：

1. ``businessType`` 的判据是 ``!= null and != 0``，**不是** ``!= ''``（§38.1）。
   XML 原文写的是 ``businessType != ''``，但 OGNL 把 ``''`` 折成 ``0.0``，
   于是选"其它"（0）时会查出**全部**记录。
2. ``businessTypes`` 是**数组**条件（``in``），与 ``businessType`` 的单值条件**并存**，
   两者都可能有。
3. ``status`` 只判 ``!= null`` —— 没有 ``!= ''``，所以 ``status=""`` 也会生效
   （与 ``title`` 恰好相反）。
4. ``selectOperLogList`` 自带 ``order by oper_id desc``，所以 PageHelper
   **不会**追加客户端排序。

本文件只测**纯函数**（``_build_oper_log_list_sql`` / ``_map_oper_log`` / 常量），
不碰数据库：``session_scope`` 那层由 ``test_sys_oper_log_service.py`` 的替身覆盖。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import pytest

from app.system.domain.sys_oper_log import SysOperLog
from app.system.mapper.sys_oper_log_mapper import (
    SELECT_OPER_LOG_VO,
    _build_oper_log_list_sql,
    _map_oper_log,
)


def _sql(oper_log: SysOperLog) -> str:
    return " ".join(_build_oper_log_list_sql(oper_log)[0].split())


def _params(oper_log: SysOperLog) -> Dict[str, Any]:
    return _build_oper_log_list_sql(oper_log)[1]


class TestProjection:
    def test_the_sixteen_columns_and_the_table(self) -> None:
        assert _sql(SysOperLog()).startswith(
            "select oper_id, title, business_type, method, request_method, operator_type, "
            "oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, "
            "status, error_msg, oper_time from sys_oper_log"
        )

    def test_select_oper_log_vo_is_the_shared_fragment(self) -> None:
        """``<sql id="selectOperLogVo">`` —— 列表与详情共用，不能各写一份。"""
        assert "select oper_id" in SELECT_OPER_LOG_VO
        assert "from sys_oper_log" in SELECT_OPER_LOG_VO

    def test_order_by_is_always_present(self) -> None:
        """业务列自带 ``order by oper_id desc`` ⇒ PageHelper 不再追加客户端排序。"""
        assert _sql(SysOperLog()).endswith("order by oper_id desc")

    def test_no_where_when_every_condition_is_empty(self) -> None:
        assert " where " not in _sql(SysOperLog())


class TestBusinessTypeOgnlTrap:
    """§38.1 —— ``businessType != ''`` 在 OGNL 里等价于 ``!= 0``。"""

    def test_zero_is_dropped(self) -> None:
        """选"其它"（0）时条件被丢掉 —— 查出全部记录，这是 Java 的既有行为。"""
        oper_log = SysOperLog(business_type=0)
        assert "business_type = " not in _sql(oper_log)
        assert "business_type" not in _params(oper_log)

    def test_non_zero_is_applied(self) -> None:
        oper_log = SysOperLog(business_type=3)
        assert "business_type = :business_type" in _sql(oper_log)
        assert _params(oper_log) == {"business_type": 3}

    def test_none_is_dropped(self) -> None:
        assert "business_type = " not in _sql(SysOperLog(business_type=None))


class TestBusinessTypesArray:
    """``<if test="businessTypes != null and businessTypes.length > 0">``."""

    def test_array_becomes_an_in_clause(self) -> None:
        oper_log = SysOperLog(business_types=[1, 2])
        assert "business_type in (" in _sql(oper_log)
        assert sorted(_params(oper_log).values()) == [1, 2]

    def test_empty_array_produces_no_condition(self) -> None:
        oper_log = SysOperLog(business_types=[])
        assert "business_type in" not in _sql(oper_log)

    def test_array_and_scalar_coexist(self) -> None:
        """前端可以同时传 ``businessType=1&businessTypes=2,3`` —— 两个条件都留着。"""
        oper_log = SysOperLog(business_type=1, business_types=[2, 3])
        rendered = _sql(oper_log)
        assert "business_type = :business_type" in rendered
        assert "business_type in (" in rendered
        assert " and " in rendered


class TestStatus:
    """``<if test="status != null">`` —— **没有** ``!= ''``."""

    def test_zero_is_applied(self) -> None:
        """``status = 0``（正常）必须生效 —— 与 ``business_type`` 的 0 不同。"""
        oper_log = SysOperLog(status=0)
        assert "status = :status" in _sql(oper_log)
        assert _params(oper_log) == {"status": 0}

    def test_one_is_applied(self) -> None:
        assert "status = :status" in _sql(SysOperLog(status=1))


class TestLikeConditions:
    """``title`` / ``oper_name`` —— ``!= null and != ''`` + ``like concat('%', ..., '%')``."""

    def test_title_like(self) -> None:
        oper_log = SysOperLog(title="用户管理")
        assert "title like concat('%', :title, '%')" in _sql(oper_log)
        assert _params(oper_log) == {"title": "用户管理"}

    def test_oper_name_like(self) -> None:
        oper_log = SysOperLog(oper_name="admin")
        assert "oper_name like concat('%', :oper_name, '%')" in _sql(oper_log)
        assert _params(oper_log) == {"oper_name": "admin"}

    def test_empty_string_is_skipped(self) -> None:
        oper_log = SysOperLog(title="", oper_name="")
        assert "like" not in _sql(oper_log)

    def test_blank_string_is_not_trimmed(self) -> None:
        """判据是 ``!= ''`` 而**不是** ``isNotBlank`` —— 一个空格也算"有值"。"""
        oper_log = SysOperLog(title=" ")
        assert "title like" in _sql(oper_log)
        assert _params(oper_log) == {"title": " "}


class TestDateRange:
    """``params.beginTime`` / ``params.endTime`` -> ``date_format(...)`` 比较."""

    def test_begin_time(self) -> None:
        oper_log = SysOperLog(params={"beginTime": "2024-01-01"})
        assert (
            "date_format(oper_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"
            in _sql(oper_log)
        )
        assert _params(oper_log) == {"begin_time": "2024-01-01"}

    def test_end_time(self) -> None:
        oper_log = SysOperLog(params={"endTime": "2024-12-31"})
        assert (
            "date_format(oper_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"
            in _sql(oper_log)
        )
        assert _params(oper_log) == {"end_time": "2024-12-31"}

    def test_both(self) -> None:
        oper_log = SysOperLog(params={"beginTime": "2024-01-01", "endTime": "2024-12-31"})
        rendered = _sql(oper_log)
        assert ">= date_format(:begin_time" in rendered
        assert "<= date_format(:end_time" in rendered

    def test_the_placeholder_is_snake_case(self) -> None:
        """Java 的属性是 ``params.beginTime``，SQL 占位符是 ``:begin_time``。"""
        params = _params(SysOperLog(params={"beginTime": "2024-01-01"}))
        assert "beginTime" not in params
        assert "begin_time" in params


class TestConditionOrder:
    """``<if>`` 序列：title -> businessType -> businessTypes -> status -> operName -> 时间."""

    def test_matches_the_xml_order(self) -> None:
        oper_log = SysOperLog(
            title="t",
            business_type=1,
            business_types=[2],
            status=0,
            oper_name="admin",
            params={"beginTime": "2024-01-01", "endTime": "2024-12-31"},
        )
        rendered = _sql(oper_log)
        positions = [
            rendered.index("title like"),
            rendered.index("business_type = :business_type"),
            rendered.index("business_type in ("),
            rendered.index("status = :status"),
            rendered.index("oper_name like"),
            rendered.index("date_format(oper_time,'%y%m%d') >="),
            rendered.index("date_format(oper_time,'%y%m%d') <="),
        ]
        assert positions == sorted(positions)

    def test_first_fragment_has_no_leading_and(self) -> None:
        """MyBatis 的 ``<where>`` 会吃掉首个 ``AND``；这里必须自己保证语法合法。"""
        rendered = _sql(SysOperLog(title="t", status=0))
        assert "where title like" in rendered
        assert "where and" not in rendered


class TestMapOperLog:
    """Java: ``resultMap="SysOperLogResult"`` —— 按列名回填，不按位置。"""

    def test_all_sixteen_columns(self) -> None:
        values = {
            "oper_id": 7,
            "title": "用户管理",
            "business_type": 1,
            "method": "com.ruoyi.web.controller.SysUserController.add()",
            "request_method": "POST",
            "operator_type": 1,
            "oper_name": "admin",
            "dept_name": "研发部门",
            "oper_url": "/system/user",
            "oper_ip": "127.0.0.1",
            "oper_location": "内网IP",
            "oper_param": "{}",
            "json_result": '{"code":200}',
            "status": 0,
            "error_msg": None,
            "oper_time": datetime(2024, 1, 1, 12, 0, 0),
        }
        row = _map_oper_log(values)

        assert row.oper_id == 7
        assert row.business_type == 1
        assert row.operator_type == 1
        assert row.status == 0
        assert row.oper_time == datetime(2024, 1, 1, 12, 0, 0)

    def test_unknown_columns_are_ignored(self) -> None:
        """``businessTypes`` 不在结果集里；多出来的列不能塞进实体。"""
        row = _map_oper_log({"oper_id": 1, "business_types": "[1,2]"})
        assert row.oper_id == 1
        assert row.business_types is None

    def test_missing_columns_stay_null(self) -> None:
        row = _map_oper_log({"oper_id": 3})
        assert row.oper_id == 3
        assert row.title is None
        assert row.oper_time is None


class TestInsertAndCleanStatements:
    """这两条常量照抄 XML —— 抄错只能靠对比源码发现。"""

    def test_insert_writes_sysdate_not_a_bound_oper_time(self) -> None:
        from app.system.mapper.sys_oper_log_mapper import _INSERT_OPER_LOG

        rendered = " ".join(_INSERT_OPER_LOG.split())
        assert rendered.endswith("sysdate())")
        assert ":oper_time" not in rendered
        assert "business_types" not in rendered

    def test_clean_is_a_truncate(self) -> None:
        from app.system.mapper.sys_oper_log_mapper import _CLEAN_OPER_LOG

        assert _CLEAN_OPER_LOG == "truncate table sys_oper_log"
