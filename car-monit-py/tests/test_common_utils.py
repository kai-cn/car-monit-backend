"""Parity tests for the migrated ``common/utils`` layer.

Every assertion below encodes a behaviour of the **Java** implementation, not of idiomatic
Python. When a test looks odd (e.g. asserting that ``172.168.1.1`` is an internal address) the
docstring points at the Java line that makes it so.

Java reference:
  * ``com.ruoyi.common.utils.StringUtils``
  * ``com.ruoyi.common.core.text.StrFormatter``
  * ``com.ruoyi.common.utils.DateUtils``
  * ``com.ruoyi.common.utils.ip.IpUtils``
  * ``com.ruoyi.common.utils.sql.SqlUtil``
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.common.core.text import str_formatter
from app.common.utils import (
    date_utils,
    ip_utils,
    sql_utils,
    string_utils,
    uuid_utils,
)


class TestStrFormatter:
    """``StrFormatter.format`` -- ``{}`` replacement with Java's escaping rules."""

    def test_replaces_in_order(self) -> None:
        assert str_formatter.format("this is {} for {}", "a", "b") == "this is a for b"

    def test_single_backslash_escapes_the_placeholder(self) -> None:
        # Java StrFormatter lines 73-74: the escaped branch appends
        # ``strPattern[handledPosition : delimIndex-1]`` (dropping the backslash) and then a bare
        # ``'{'`` -- the closing ``'}'`` is re-emitted by the trailing append. So ``\{}`` collapses
        # to a literal ``{}``, NOT to ``\{}``. Verified against
        # ruoyi-common/.../core/text/StrFormatter.java:73-75.
        assert str_formatter.format("this is \\{} for {}", "a", "b") == "this is {} for a"

    def test_double_backslash_keeps_placeholder_active(self) -> None:
        # Java: "this is \\\\{} for {}" -> "this is \a for b"
        assert str_formatter.format("this is \\\\{} for {}", "a", "b") == "this is \\a for b"

    def test_none_renders_as_java_null(self) -> None:
        # Convert.utf8Str(null) -> null; StringBuilder.append((String) null) -> "null".
        # str(None) would produce "None" and silently change every error message.
        assert str_formatter.format("用户：{} 不存在", None) == "用户：null 不存在"

    def test_missing_arguments_leave_placeholders_untouched(self) -> None:
        assert str_formatter.format("{} and {}", 1) == "1 and {}"

    def test_no_placeholder_returns_the_same_instance(self) -> None:
        pattern = "welcome"
        assert str_formatter.format(pattern, 1) is pattern

    def test_blank_pattern_is_returned_unchanged(self) -> None:
        assert str_formatter.format("   ", "x") == "   "

    def test_no_arguments_returns_pattern_unchanged(self) -> None:
        pattern = "a {} b"
        assert str_formatter.format(pattern) is pattern

    def test_numbers_use_java_to_string(self) -> None:
        assert str_formatter.format("{}", 1.0) == "1.0"
        assert str_formatter.format("{}", True) == "True"


class TestStringUtilsEmptiness:
    """``StringUtils.isEmpty`` overload dispatch."""

    @pytest.mark.parametrize("value", [None, "", "   ", [], (), {}, set()])
    def test_empty_values(self, value: object) -> None:
        assert string_utils.is_empty(value) is True

    @pytest.mark.parametrize("value", ["a", " a ", [0], (0,), {"k": 1}, {1}, 0, False])
    def test_non_empty_values(self, value: object) -> None:
        assert string_utils.is_empty(value) is False

    def test_scalars_are_not_collections(self) -> None:
        # Java would not compile this; Python must still answer "not empty" (the object exists).
        assert string_utils.is_empty(0) is False

    def test_trim_uses_java_whitespace_not_python_strip(self) -> None:
        # Java String.trim() only strips chars <= U+0020, so the ideographic space survives
        # and the string is NOT empty. Python's strip() would collapse it to "".
        assert string_utils.is_empty("\u3000") is False
        assert string_utils.java_trim("\u3000x\u3000") == "\u3000x\u3000"

    def test_nbsp_is_not_java_whitespace(self) -> None:
        # Character.isWhitespace('\u00a0') is false; str.isspace() says true.
        assert string_utils.is_blank("\u00a0") is False
        assert "\u00a0".isspace() is True

    def test_has_text(self) -> None:
        assert string_utils.has_text(None) is False
        assert string_utils.has_text("") is False
        assert string_utils.has_text("  ") is False
        assert string_utils.has_text(" x ") is True

    def test_trim_null_becomes_empty_string(self) -> None:
        assert string_utils.trim(None) == ""
        assert string_utils.trim("  x  ") == "x"


class TestStringUtilsCollections:
    def test_split_regex_drops_trailing_empties_like_java(self) -> None:
        assert string_utils.split_regex("a,b,,", ",") == ["a", "b"]
        assert "a,b,,".split(",") == ["a", "b", "", ""]

    def test_split_regex_negative_limit_keeps_empties(self) -> None:
        assert string_utils.split_regex("a,b,,", ",", limit=-1) == ["a", "b", "", ""]

    def test_split_regex_positive_limit_keeps_remainder(self) -> None:
        assert string_utils.split_regex("a,b,c", ",", limit=2) == ["a", "b,c"]

    def test_str2_list(self) -> None:
        assert string_utils.str2_list("a, b ,c", ",", True, True) == ["a", "b", "c"]
        assert string_utils.str2_list("a,,b", ",", True, False) == ["a", "b"]
        assert string_utils.str2_list("a,,b", ",", False, False) == ["a", "", "b"]
        assert string_utils.str2_list("   ", ",", True, False) == []

    def test_str2_set_deduplicates(self) -> None:
        assert string_utils.str2_set("a,a,b", ",") == {"a", "b"}

    def test_string_to_list_returns_mutable_list(self) -> None:
        result = string_utils.string_to_list("1,2,3")
        result.append("4")
        assert result == ["1", "2", "3", "4"]
        assert string_utils.string_to_list(None) == []

    def test_split_uses_any_char_of_the_separator_set(self) -> None:
        # Commons-Lang StringUtils.split(str, "\\|") splits on '\' AND '|'.
        assert string_utils.split("a|b\\c", "\\|") == ["a", "b", "c"]

    def test_contains_any(self) -> None:
        assert string_utils.contains_any(["a", "b"], "c", "b") is True
        assert string_utils.contains_any(["a"], "c") is False
        assert string_utils.contains_any(None, "c") is False
        assert string_utils.contains_any(["a"]) is False


class TestStringUtilsNaming:
    def test_to_under_score_case(self) -> None:
        assert string_utils.to_under_score_case("AbcDef") == "abc_def"
        assert string_utils.to_under_score_case("userName") == "user_name"
        assert string_utils.to_under_score_case("HTTPServer") == "http_server"
        assert string_utils.to_under_score_case(None) is None

    def test_to_camel_case(self) -> None:
        assert string_utils.to_camel_case("user_name") == "userName"
        assert string_utils.to_camel_case("USER_NAME") == "userName"
        assert string_utils.to_camel_case("username") == "username"
        assert string_utils.to_camel_case(None) is None

    def test_convert_to_camel_case(self) -> None:
        assert string_utils.convert_to_camel_case("HELLO_WORLD") == "HelloWorld"
        assert string_utils.convert_to_camel_case("hello") == "Hello"
        assert string_utils.convert_to_camel_case("") == ""
        assert string_utils.convert_to_camel_case(None) == ""

    def test_hide(self) -> None:
        assert string_utils.hide("13800138000", 3, 7) == "138****8000"
        assert string_utils.hide(None, 0, 1) == ""
        assert string_utils.hide("abc", 5, 6) == ""
        assert string_utils.hide("abc", 0, 99) == "***"

    def test_padl(self) -> None:
        assert string_utils.padl("7", 3, "0") == "007"
        assert string_utils.padl("12345", 3, "0") == "345"
        assert string_utils.padl(None, 3, "0") == "000"
        assert string_utils.padl_number(7, 3) == "007"


class TestAntPathMatch:
    """``StringUtils.isMatch`` -- the filter that decides which URLs bypass authentication."""

    @pytest.mark.parametrize(
        ("pattern", "url"),
        [
            ("/login", "/login"),
            ("/profile/**", "/profile/a/b.png"),
            ("/profile/**", "/profile/"),
            ("/**/*.html", "/a/b/index.html"),
            ("/*/api-docs", "/v2/api-docs"),
            ("/swagger-resources/**", "/swagger-resources/configuration/ui"),
            ("/common/download**", "/common/download"),
        ],
    )
    def test_matches(self, pattern: str, url: str) -> None:
        assert string_utils.is_match(pattern, url) is True

    @pytest.mark.parametrize(
        ("pattern", "url"),
        [
            ("/login", "/login/x"),
            ("/*/api-docs", "/a/b/api-docs"),
            ("/profile/*", "/profile/a/b.png"),
            ("/", "/login"),
            # A trailing "**" without a separator does NOT cross a '/' boundary:
            # the pattern tokenizes to ["common", "download**"] while the path becomes
            # ["common", "download", "resource"], so stage 1 consumes both pattern
            # segments and the pattern runs out first -> false. This is exactly why
            # SecurityConfig lists '/common/download/resource**' as a separate rule:
            # if the short pattern matched it, that second rule could never be reached.
            ("/common/download**", "/common/download/resource"),
        ],
    )
    def test_does_not_match(self, pattern: str, url: str) -> None:
        assert string_utils.is_match(pattern, url) is False

    def test_single_star_does_not_cross_segments(self) -> None:
        assert string_utils.is_match("/system/*", "/system/user") is True
        assert string_utils.is_match("/system/*", "/system/user/list") is False


class TestIpUtils:
    def test_internal_ip_standard_ranges(self) -> None:
        assert ip_utils.internal_ip("10.1.2.3") is True
        assert ip_utils.internal_ip("172.16.0.1") is True
        assert ip_utils.internal_ip("172.31.255.254") is True
        assert ip_utils.internal_ip("192.168.1.1") is True
        assert ip_utils.internal_ip("127.0.0.1") is True
        assert ip_utils.internal_ip("8.8.8.8") is False

    def test_switch_fall_through_bug_is_preserved(self) -> None:
        # Java's switch has no ``break`` after case 172, so 172.168.x.x falls through into
        # the 192.168 branch and is reported as internal. Documented, not fixed.
        assert ip_utils.internal_ip("172.168.1.1") is True
        # 172.1.x.x does not hit the 192.168 branch and is correctly public.
        assert ip_utils.internal_ip("172.1.1.1") is False

    def test_text_to_numeric_format_v4(self) -> None:
        assert ip_utils.text_to_numeric_format_v4("1.2.3.4") == [1, 2, 3, 4]
        assert ip_utils.text_to_numeric_format_v4("192.168.0.1") == [192, 168, 0, 1]
        assert ip_utils.text_to_numeric_format_v4("256.1.1.1") is None
        assert ip_utils.text_to_numeric_format_v4("") is None
        assert ip_utils.text_to_numeric_format_v4("a.b.c.d") is None
        # Single-element form is a 32-bit decimal address.
        assert ip_utils.text_to_numeric_format_v4("16909060") == [1, 2, 3, 4]

    def test_get_multistage_reverse_proxy_ip_takes_first_known(self) -> None:
        # Java trims the whole header and only THEN splits on ',', so every element except the
        # first keeps its leading space: "unknown, 1.2.3.4, 5.6.7.8" -> " 1.2.3.4".
        # IpUtils.java:259-265 assigns ``ip = subIp`` verbatim, so the space survives into
        # sys_logininfor.ipaddr. Preserved on purpose; do not .strip() the result.
        assert ip_utils.get_multistage_reverse_proxy_ip("unknown, 1.2.3.4, 5.6.7.8") == " 1.2.3.4"
        assert ip_utils.get_multistage_reverse_proxy_ip("1.2.3.4, 5.6.7.8") == "1.2.3.4"
        assert ip_utils.get_multistage_reverse_proxy_ip(None) == ""

    def test_get_multistage_truncates_to_255(self) -> None:
        long_ip = "1" * 300
        assert len(ip_utils.get_multistage_reverse_proxy_ip(long_ip)) == 255

    def test_is_matched_ip(self) -> None:
        assert ip_utils.is_matched_ip("1.2.3.4", "1.2.3.4") is True
        assert ip_utils.is_matched_ip("1.2.3.*", "1.2.3.4") is True
        assert ip_utils.is_matched_ip("1.2.3.4-1.2.3.10", "1.2.3.7") is True
        assert ip_utils.is_matched_ip("1.2.3.4-1.2.3.10", "1.2.3.11") is False
        assert ip_utils.is_matched_ip("1.1.1.1;2.2.2.2", "2.2.2.2") is True
        assert ip_utils.is_matched_ip("", "1.2.3.4") is False

    def test_is_ip_and_wildcard(self) -> None:
        assert ip_utils.is_ip("1.2.3.4") is True
        assert ip_utils.is_ip("1.2.3") is False
        assert ip_utils.is_ip_wild_card("1.2.3.*") is True
        assert ip_utils.is_ip_wild_card("*.*.*.*") is True
        assert ip_utils.is_ip_wild_card("1.2.*") is False

    def test_get_ip_addr_prefers_x_forwarded_for(self) -> None:
        class _Client:
            host = "9.9.9.9"

        class _Request:
            client = _Client()
            headers = {"x-forwarded-for": "1.2.3.4"}

        assert ip_utils.get_ip_addr(_Request()) == "1.2.3.4"

    def test_get_ip_addr_falls_back_to_remote_addr(self) -> None:
        class _Client:
            host = "9.9.9.9"

        class _Request:
            client = _Client()
            headers: dict = {}

        assert ip_utils.get_ip_addr(_Request()) == "9.9.9.9"

    def test_get_ip_addr_ipv6_loopback(self) -> None:
        class _Client:
            host = "0:0:0:0:0:0:0:1"

        class _Request:
            client = _Client()
            headers: dict = {}

        assert ip_utils.get_ip_addr(_Request()) == "127.0.0.1"

    def test_get_ip_addr_without_request(self) -> None:
        assert ip_utils.get_ip_addr(None) == "unknown"


class TestDateUtils:
    def test_parse_date_to_str(self) -> None:
        value = datetime(2026, 10, 23, 8, 5, 9, 123000)
        assert date_utils.parse_date_to_str("yyyy-MM-dd HH:mm:ss", value) == "2026-10-23 08:05:09"
        assert date_utils.parse_date_to_str("yyyyMMddHHmmss", value) == "20261023080509"
        assert date_utils.parse_date_to_str("yyyy-MM-dd HH:mm:ss.SSS", value) == "2026-10-23 08:05:09.123"

    def test_parse_date_to_str_null_inputs(self) -> None:
        assert date_utils.parse_date_to_str("yyyy-MM-dd", None) is None
        assert date_utils.parse_date_to_str(None, datetime.now()) is None
        assert date_utils.parse_date_to_str("  ", datetime.now()) is None

    def test_parse_date_tries_every_pattern(self) -> None:
        assert date_utils.parse_date("2026-10-23") == datetime(2026, 10, 23)
        assert date_utils.parse_date("2026/10/23 08:00:00") == datetime(2026, 10, 23, 8, 0, 0)
        assert date_utils.parse_date("2026.10") == datetime(2026, 10, 1)
        assert date_utils.parse_date("not-a-date") is None
        assert date_utils.parse_date(None) is None

    def test_date_time_parse_raises_on_bad_input(self) -> None:
        with pytest.raises(ValueError):
            date_utils.date_time_parse("yyyy-MM-dd", "nope")

    def test_timestamp_is_truncated_to_millis(self) -> None:
        value = date_utils.get_timestamp()
        assert value.microsecond % 1000 == 0

    def test_different_days_truncates_before_abs(self) -> None:
        start = datetime(2026, 10, 1, 12, 0, 0)
        # 11.5 hours -> int() -> 0 days, matching Java's (int) cast before Math.abs.
        assert date_utils.different_days_by_millisecond(start, datetime(2026, 10, 1, 23, 30)) == 0
        assert date_utils.different_days_by_millisecond(start, datetime(2026, 10, 4)) == 2
        assert date_utils.different_days_by_millisecond(datetime(2026, 10, 4), start) == 2

    def test_time_distance_format(self) -> None:
        start = datetime(2026, 10, 1, 0, 0, 0)
        end = datetime(2026, 10, 2, 3, 4, 0)
        assert date_utils.time_distance(end, start) == "1天3小时4分钟"

    def test_get_timestamp_new2_is_two_days_earlier(self) -> None:
        delta = date_utils.get_timestamp() - date_utils.get_timestamp_new2()
        assert 1 < delta.days <= 2


class TestSqlUtils:
    def test_valid_order_by_passes_through(self) -> None:
        assert sql_utils.escape_order_by_sql("create_time desc") == "create_time desc"
        assert sql_utils.escape_order_by_sql("a.b, c") == "a.b, c"

    def test_none_and_empty_pass_through(self) -> None:
        assert sql_utils.escape_order_by_sql(None) is None
        assert sql_utils.escape_order_by_sql("") == ""

    @pytest.mark.parametrize("value", ["a;drop table x", "a'", "(select 1)", "a--"])
    def test_invalid_order_by_raises(self, value: str) -> None:
        with pytest.raises(sql_utils.UtilException):
            sql_utils.escape_order_by_sql(value)

    def test_too_long_raises(self) -> None:
        with pytest.raises(sql_utils.UtilException):
            sql_utils.escape_order_by_sql("a" * 501)

    def test_filter_keyword(self) -> None:
        with pytest.raises(sql_utils.UtilException):
            sql_utils.filter_keyword("select * from dual")
        sql_utils.filter_keyword("normal text")


class TestUuidUtils:
    def test_random_uuid_has_dashes(self) -> None:
        value = uuid_utils.random_uuid()
        assert len(value) == 36 and value.count("-") == 4

    def test_simple_uuid_has_no_dashes(self) -> None:
        value = uuid_utils.simple_uuid()
        assert len(value) == 32 and "-" not in value

    def test_uuids_are_unique(self) -> None:
        assert len({uuid_utils.random_uuid() for _ in range(100)}) == 100
