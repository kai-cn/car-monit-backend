"""``SysLogininforMapper`` —— SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysLogininforMapper.java

两处必须钉住的地方
------------------
1. **投影顺序与 resultMap 不一致**：XML 的 ``select`` 列是
   ``info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time``，
   而 resultMap 声明的是 ``infoId, userName, status, ipaddr, …`` —— ``status`` 在第 7 位，
   不是第 3 位。MyBatis 按**列名**回填所以没事；Python 若按位置取，``status`` 会
   和 ``ipaddr`` 互换（一个"0/1"跑进了 IP 列）。
2. **``cleanLogininfor`` 是 ``truncate``**：DDL、隐式提交，不可回滚。Java 也是
   ``<update>`` 标签包 ``truncate``，不是 ``delete``。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.system.domain.sys_logininfor import SysLogininfor
from app.system.mapper.sys_logininfor_mapper import (
    SELECT_LOGININFOR_COLUMNS,
    _build_logininfor_list_sql,
    _map_logininfor,
)


def _sql(logininfor: SysLogininfor) -> str:
    return " ".join(_build_logininfor_list_sql(logininfor)[0].split())


def _params(logininfor: SysLogininfor) -> Dict[str, Any]:
    return _build_logininfor_list_sql(logininfor)[1]


class TestProjection:
    def test_column_order_matches_the_xml_not_the_result_map(self) -> None:
        """``status`` 在第 7 位 —— 这是 XML 原文，故意与 resultMap 不同。"""
        assert SELECT_LOGININFOR_COLUMNS == (
            "info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time"
        )

    def test_select_starts_with_the_shared_columns(self) -> None:
        assert _sql(SysLogininfor()).startswith(
            f"select {SELECT_LOGININFOR_COLUMNS} from sys_logininfor"
        )

    def test_order_by_is_always_present(self) -> None:
        assert _sql(SysLogininfor()).endswith("order by info_id desc")

    def test_no_where_when_every_condition_is_empty(self) -> None:
        assert " where " not in _sql(SysLogininfor())


class TestConditions:
    """``<if>`` 序列：ipaddr -> status -> userName -> beginTime -> endTime."""

    def test_ipaddr_like(self) -> None:
        logininfor = SysLogininfor(ipaddr="192.168")
        assert "ipaddr like concat('%', :ipaddr, '%')" in _sql(logininfor)
        assert _params(logininfor) == {"ipaddr": "192.168"}

    def test_status_is_exact_match(self) -> None:
        """``status`` 是 ``String``（"0"/"1"），判等而不是 like。"""
        logininfor = SysLogininfor(status="1")
        assert "status = :status" in _sql(logininfor)
        assert _params(logininfor) == {"status": "1"}

    def test_status_zero_string_is_applied(self) -> None:
        """``"0"`` 是成功 —— ``!= ''`` 在字符串上是**真**判据，不会像 operlog 那样被吃掉。"""
        logininfor = SysLogininfor(status="0")
        assert "status = :status" in _sql(logininfor)
        assert _params(logininfor) == {"status": "0"}

    def test_user_name_like(self) -> None:
        logininfor = SysLogininfor(user_name="admin")
        assert "user_name like concat('%', :user_name, '%')" in _sql(logininfor)

    def test_empty_strings_are_skipped(self) -> None:
        logininfor = SysLogininfor(ipaddr="", status="", user_name="")
        assert " where " not in _sql(logininfor)

    def test_blank_string_is_not_trimmed(self) -> None:
        logininfor = SysLogininfor(ipaddr=" ")
        assert "ipaddr like" in _sql(logininfor)


class TestDateRange:
    def test_begin_time(self) -> None:
        logininfor = SysLogininfor(params={"beginTime": "2024-01-01"})
        assert (
            "date_format(login_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"
            in _sql(logininfor)
        )
        assert _params(logininfor) == {"begin_time": "2024-01-01"}

    def test_end_time(self) -> None:
        logininfor = SysLogininfor(params={"endTime": "2024-12-31"})
        assert (
            "date_format(login_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"
            in _sql(logininfor)
        )
        assert _params(logininfor) == {"end_time": "2024-12-31"}

    def test_the_column_is_login_time_not_oper_time(self) -> None:
        """两个 mapper 的 SQL 长得像，别把列名抄串了。"""
        logininfor = SysLogininfor(params={"beginTime": "2024-01-01"})
        assert "oper_time" not in _sql(logininfor)


class TestConditionOrder:
    def test_matches_the_xml_order(self) -> None:
        logininfor = SysLogininfor(
            ipaddr="10.0",
            status="0",
            user_name="admin",
            params={"beginTime": "2024-01-01", "endTime": "2024-12-31"},
        )
        rendered = _sql(logininfor)
        positions = [
            rendered.index("ipaddr like"),
            rendered.index("status = :status"),
            rendered.index("user_name like"),
            rendered.index("date_format(login_time,'%y%m%d') >="),
            rendered.index("date_format(login_time,'%y%m%d') <="),
        ]
        assert positions == sorted(positions)

    def test_first_fragment_has_no_leading_and(self) -> None:
        rendered = _sql(SysLogininfor(status="0", user_name="admin"))
        assert "where status = :status" in rendered
        assert "where and" not in rendered


class TestMapLogininfor:
    def test_all_nine_columns(self) -> None:
        values = {
            "info_id": 12,
            "user_name": "admin",
            "ipaddr": "127.0.0.1",
            "login_location": "内网IP",
            "browser": "Chrome 12",
            "os": "Windows 10",
            "status": "0",
            "msg": "登录成功",
            "login_time": datetime(2024, 1, 1, 12, 0, 0),
        }
        row = _map_logininfor(values)

        assert row.info_id == 12
        assert row.status == "0"
        assert row.login_time == datetime(2024, 1, 1, 12, 0, 0)

    def test_mapping_is_by_name_so_status_does_not_swap_with_ipaddr(self) -> None:
        """按列名回填 —— 若改成按位置，``status`` 会拿到 ``ipaddr`` 的值。"""
        row = _map_logininfor(
            {
                "info_id": 1,
                "user_name": "a",
                "ipaddr": "1.1.1.1",
                "login_location": "loc",
                "browser": "b",
                "os": "o",
                "status": "1",
                "msg": "m",
            }
        )
        assert row.ipaddr == "1.1.1.1"
        assert row.status == "1"

    def test_missing_columns_stay_null(self) -> None:
        row = _map_logininfor({"info_id": 1})
        assert row.info_id == 1
        assert row.status is None
        assert row.login_time is None


class TestInsertAndCleanStatements:
    def test_insert_uses_sysdate_for_login_time(self) -> None:
        from app.system.mapper.sys_logininfor_mapper import _INSERT_LOGININFOR

        rendered = " ".join(_INSERT_LOGININFOR.split())
        assert rendered.endswith("sysdate())")
        assert ":login_time" not in rendered

    def test_insert_column_order_matches_the_xml(self) -> None:
        from app.system.mapper.sys_logininfor_mapper import _INSERT_LOGININFOR

        rendered = " ".join(_INSERT_LOGININFOR.split())
        assert rendered.startswith(
            "insert into sys_logininfor (user_name, status, ipaddr, login_location, "
            "browser, os, msg, login_time)"
        )

    def test_clean_is_a_truncate(self) -> None:
        from app.system.mapper.sys_logininfor_mapper import _CLEAN_LOGININFOR

        assert _CLEAN_LOGININFOR == "truncate table sys_logininfor"
