"""Tests for the shared core types.

# Migrated from: (no Java unit test exists for AjaxResult / TableDataInfo)

这些用例把「线上真实响应字节」固定下来，防止后续重构悄悄改变 JSON 形状。
Each assertion is copied from the Java implementation, not from observed Python output.
"""

from __future__ import annotations

import pytest

from app.common.constant.http_status import HttpStatus
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo, get_data_table


class TestHttpStatus:
    """Java: ``com.ruoyi.common.constant.HttpStatus``."""

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("SUCCESS", 200),
            ("CREATED", 201),
            ("ACCEPTED", 202),
            ("NO_CONTENT", 204),
            ("MOVED_PERM", 301),
            ("SEE_OTHER", 303),
            ("NOT_MODIFIED", 304),
            ("BAD_REQUEST", 400),
            ("UNAUTHORIZED", 401),
            ("FORBIDDEN", 403),
            ("NOT_FOUND", 404),
            ("BAD_METHOD", 405),
            ("CONFLICT", 409),
            ("UNSUPPORTED_TYPE", 415),
            ("ERROR", 500),
            ("NOT_IMPLEMENTED", 501),
            ("WARN", 601),
        ],
    )
    def test_constants(self, name: str, value: int) -> None:
        assert getattr(HttpStatus, name) == value


class TestAjaxResult:
    """Java: ``com.ruoyi.common.core.domain.AjaxResult``."""

    def test_success_has_no_data_key_when_data_is_null(self) -> None:
        """Java: ``AjaxResult.success()`` -> ``{code:200, msg:"操作成功"}``.

        ``AjaxResult extends HashMap<String, Object>``（见 ``AjaxResult.java:14``），
        所以 JSON 的键序是 **HashMap 桶序**，不是插入序：``msg`` 落在 0 号桶、
        ``code`` 落在 3 号桶，序列化出来是 ``{"msg":...,"code":...}``。
        线上 RuoYi 的真实响应就是这个顺序。
        """
        result = AjaxResult.success_message("操作成功")
        assert list(result.keys()) == ["msg", "code"]
        assert result["code"] == 200
        assert result["msg"] == "操作成功"

    def test_success_with_data_follows_hash_map_bucket_order(self) -> None:
        """``HashMap`` 桶序：``msg``(0) -> ``code``(3) -> ``data``(4)。"""
        result = AjaxResult.success_data({"id": 1})
        assert list(result.keys()) == ["msg", "code", "data"]
        assert result["data"] == {"id": 1}

    def test_error_default_code_is_500(self) -> None:
        result = AjaxResult.error_message("失败")
        assert result["code"] == HttpStatus.ERROR
        assert result["msg"] == "失败"

    def test_error_with_code(self) -> None:
        result = AjaxResult.error_code(HttpStatus.FORBIDDEN, "没有权限")
        assert result["code"] == 403
        assert result["msg"] == "没有权限"

    def test_warn_code_is_601(self) -> None:
        """Java: ``AjaxResult.warn(msg)`` uses ``HttpStatus.WARN`` = 601."""
        result = AjaxResult.warn("警告")
        assert result["code"] == 601

    def test_is_success(self) -> None:
        assert AjaxResult.success_data(1).is_success() is True
        assert AjaxResult.error_message("x").is_success() is False

    def test_put_chain_is_fluent_like_java(self) -> None:
        """Java: ``new AjaxResult().put("k", "v")`` -- HashMap semantics, same key overwrites.

        Python 里覆写 ``dict.put`` 会破坏 dict 协议，所以保留原名语义、改名为 ``put_chain``。
        """
        result = AjaxResult()
        returned = result.put_chain("k", "v")
        assert returned is result
        assert result["k"] == "v"
        assert result.get("missing") is None

    @pytest.mark.parametrize(
        ("first", "second", "expected"),
        [
            # 验证码：msg(0) -> img(2) -> code(3) -> uuid(13)
            ("uuid", "img", ["msg", "img", "code", "uuid"]),
            # 角色部门树：msg(0) -> code(3) -> depts(14) -> checkedKeys(15)
            ("checkedKeys", "depts", ["msg", "code", "depts", "checkedKeys"]),
            # 角色菜单树：msg(0) -> code(3) -> menus(11) -> checkedKeys(15)
            ("menus", "checkedKeys", ["msg", "code", "menus", "checkedKeys"]),
            # 上传：msg(0) -> fileName(2) -> code(3) -> newFileName(9) -> url(14)
            ("url", "fileName", ["msg", "fileName", "code", "url"]),
            # 同桶（都是 4）时保持 put 先后
            ("data", "newFileNames", ["msg", "code", "data", "newFileNames"]),
        ],
    )
    def test_put_chain_places_keys_by_bucket_not_by_call_order(
        self, first: str, second: str, expected: list
    ) -> None:
        """``put_chain`` 必须模拟 ``HashMap`` 的**桶序**，而不是追加到末尾。

        这是全站响应键序的根基：写错成 ``ajax[key] = value`` 就会变成插入序，
        四个键以上的响应立刻与 Java 不一致（验证码、上传、树选择都会中招）。
        """
        result = AjaxResult.success()
        result.put_chain(first, 1)
        result.put_chain(second, 2)

        assert list(result.keys()) == expected


class TestTableDataInfo:
    """Java: ``com.ruoyi.common.core.page.TableDataInfo``."""

    def test_defaults_match_java_field_initialisers(self) -> None:
        """Java 字段默认值：long total=0, List rows=null, int code=0, String msg=null。"""
        page = TableDataInfo()
        assert page.total == 0
        assert page.rows is None
        assert page.code == 0
        assert page.msg is None

    def test_serialization_field_order(self) -> None:
        """Java field declaration order: total, rows, code, msg."""
        page = TableDataInfo.of([{"a": 1}], 1)
        page.set_code(200)
        page.set_msg("查询成功")
        assert list(page.to_dict().keys()) == ["total", "rows", "code", "msg"]
        assert page.to_dict() == {"total": 1, "rows": [{"a": 1}], "code": 200, "msg": "查询成功"}

    def test_get_data_table_mirrors_base_controller(self) -> None:
        """Java: ``BaseController#getDataTable`` 固定 setCode(200) + setMsg("查询成功")。"""
        page = get_data_table([], 0)
        assert page.code == 200
        assert page.msg == "查询成功"
        assert page.rows == []
        assert page.total == 0
