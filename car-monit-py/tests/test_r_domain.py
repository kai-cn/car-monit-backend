"""``R<T>`` -- the generic response envelope.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/R.java

``R`` 与 ``AjaxResult`` 的差别只有一处，但它是**可观测**的：``data`` 为 ``null`` 时
``R`` 仍然写出 ``"data": null``，``AjaxResult`` 会把整个键省掉。前端对两者的判断
（``res.data === null``）依赖这个差别，所以单独钉一遍。
"""

from __future__ import annotations

import json

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.r import R


class TestR:
    def test_ok_carries_data_as_null(self) -> None:
        assert R.ok() == {"code": 200, "msg": "操作成功", "data": None}

    def test_ok_data_carries_the_payload(self) -> None:
        assert R.ok_data([1, 2]) == {"code": 200, "msg": "操作成功", "data": [1, 2]}

    def test_ok_data_msg_uses_the_custom_message(self) -> None:
        assert R.ok_data_msg("x", "自定义") == {"code": 200, "msg": "自定义", "data": "x"}

    def test_fail_uses_code_500_and_the_java_message(self) -> None:
        assert R.fail() == {"code": 500, "msg": "操作失败", "data": None}

    def test_fail_msg_puts_the_text_in_msg_not_data(self) -> None:
        """Java 的 ``R.fail("用户不存在")`` 选中的是 ``fail(String msg)`` 重载。"""
        assert R.fail_msg("用户不存在") == {"code": 500, "msg": "用户不存在", "data": None}

    def test_fail_data_keeps_the_payload(self) -> None:
        assert R.fail_data({"a": 1}) == {"code": 500, "msg": "操作失败", "data": {"a": 1}}

    def test_fail_data_msg_takes_data_then_message(self) -> None:
        assert R.fail_data_msg({"a": 1}, "坏了") == {"code": 500, "msg": "坏了", "data": {"a": 1}}

    def test_fail_code_overrides_the_status(self) -> None:
        assert R.fail_code(401, "未授权") == {"code": 401, "msg": "未授权", "data": None}

    def test_key_order_is_code_msg_data(self) -> None:
        """Jackson 按 getter 发现顺序输出：``getCode`` -> ``getMsg`` -> ``getData``。"""
        assert list(R.ok().keys()) == ["code", "msg", "data"]

    def test_data_null_survives_json_serialization(self) -> None:
        payload = json.loads(json.dumps(R.ok()))

        assert "data" in payload
        assert payload["data"] is None

    def test_ajax_result_omits_data_for_contrast(self) -> None:
        """对照组：同样是 ``code 200`` + 无数据，``AjaxResult`` 里**没有** ``data``。"""
        assert "data" not in AjaxResult.success()

    def test_ajax_result_keeps_data_when_present(self) -> None:
        assert AjaxResult.success_data([1]) == {"code": 200, "msg": "操作成功", "data": [1]}


class TestPredicates:
    def test_is_success(self) -> None:
        assert R.is_success(R.ok()) is True
        assert R.is_success(R.fail()) is False

    def test_is_error_is_the_negation(self) -> None:
        assert R.is_error(R.fail()) is True
        assert R.is_error(R.ok()) is False

    def test_constants_match_http_status(self) -> None:
        assert (R.SUCCESS, R.FAIL) == (200, 500)
