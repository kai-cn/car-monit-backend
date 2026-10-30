"""``LogAspect`` 的等价实现 —— :mod:`app.framework.aspectj.log_aspect`.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java
#   + ruoyi-common/src/main/java/com/ruoyi/common/annotation/Log.java
#   + ruoyi-common/src/main/java/com/ruoyi/common/enums/{BusinessType,BusinessStatus,OperatorType}.java

这一层测什么
------------
审计行是"事后取证"用的，错了不会有人立刻发现，所以这里把 Java 侧每一条**可观察**的
规则都钉成用例：

* 枚举的 ``ordinal()`` —— 落库的是数字，顺序错了整份报表的筛选就全错；
* ``@Log`` 注解默认值 —— ``businessType = OTHER``、``operatorType = MANAGE``、两个
  ``isSave*`` 都是 ``true``、``excludeParamNames`` 为空；
* 成功 / 失败分支：``return AjaxResult.error(...)`` 仍然是 ``status = 0``，只有**抛异常**
  才是 ``status = 1``（见 ``log_aspect`` docstring 踩坑记录第 1 条）；
* 未登录时**一行都不写**（第 2 条）；
* ``oper_param`` 的来源与序列化（query/表单 vs 入参；null 省略、空容器保留、按键名排序）；
* ``217`` 个调用点的盘点：数量、``java_method``、``JAVA_CONTROLLER`` 与
  ``# Migrated from:`` 头是否一致。

本模块自身扮演"一个控制器"——它声明 :data:`JAVA_CONTROLLER`，下面的样例函数用
``@log`` 装饰，于是 ``_resolve_java_controller`` 能取到全类名，无需真的拉起 FastAPI。
"""

from __future__ import annotations

import io
import re
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from starlette.datastructures import UploadFile
from starlette.requests import Request

from app.common.annotation.log import Log
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.enums.business_status import BusinessStatus
from app.common.enums.business_type import BusinessType
from app.common.enums.http_method import HttpMethod
from app.common.enums.operator_type import OperatorType
from app.common.exception.exceptions import CustomException
from app.framework.aspectj import log_aspect
from app.framework.aspectj.log_aspect import log
from app.framework.manager.factory import async_factory
from app.system.domain.sys_oper_log import SysOperLog
from app.system.domain.sys_post import SysPost

#: 本模块冒充一个控制器；``sys_oper_log.method`` 需要这个全类名。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysPostController"

APP_ROOT = Path(log_aspect.__file__).resolve().parents[3]
API_ROOT = APP_ROOT / "app" / "api"
DECORATOR = re.compile(r"^@log\((.+)\)$", re.MULTILINE)
MIGRATED_FROM = re.compile(r"^# Migrated from: (\S+\.java)", re.MULTILINE)
JAVA_CONTROLLER_LINE = re.compile(r'^JAVA_CONTROLLER = "([^"]+)"', re.MULTILINE)


# --------------------------------------------------------------------------- 样例端点


@log(title="岗位管理", business_type=BusinessType.INSERT, java_method="add")
def _add_post(post: SysPost) -> AjaxResult:
    return AjaxResult.success()


@log(title="岗位管理", business_type=BusinessType.DELETE, java_method="remove")
def _remove_post(post_id: int) -> AjaxResult:
    raise CustomException("x" * 3000)


@log(
    title="用户管理",
    business_type=BusinessType.UPDATE,
    java_method="edit",
    exclude_param_names=("password",),
    is_save_response_data=False,
)
def _edit_user(user: SysUser) -> AjaxResult:
    return AjaxResult.success()


@log(title="岗位管理", business_type=BusinessType.EXPORT, java_method="export")
def _export_posts() -> AjaxResult:
    return AjaxResult.success()


# --------------------------------------------------------------------------- 测试替身


class _FakeAsyncManager:
    """Java ``AsyncManager.me().execute(task)`` —— 这里**同步**执行，方便断言写入的行."""

    @classmethod
    def me(cls) -> "_FakeAsyncManager":
        return cls()

    def execute(self, task: Any) -> None:
        task()


class _FakeOperLogService:
    def __init__(self, sink: List[SysOperLog]) -> None:
        self._sink = sink

    def insert_operlog(self, oper_log: SysOperLog) -> int:
        self._sink.append(oper_log)
        return 1


def make_request(
    method: str = "POST",
    path: str = "/system/post",
    query: str = "",
    headers: Optional[Dict[str, str]] = None,
) -> Request:
    """构造一个最小的 Starlette ``Request``（等价于 MockHttpServletRequest）."""
    raw = [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in (headers or {}).items()]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": path.split("?", 1)[0],
            "raw_path": path.split("?", 1)[0].encode("latin-1"),
            "query_string": query.encode("latin-1"),
            "root_path": "",
            "headers": raw,
            "client": ("127.0.0.1", 54321),
            "server": ("127.0.0.1", 9989),
        }
    )


@pytest.fixture(autouse=True)
def auditor(monkeypatch: pytest.MonkeyPatch) -> Any:
    """把 "请求上下文 + 登录态 + 异步落库" 三条外部依赖都换成可控替身."""
    rows: List[SysOperLog] = []
    state: Dict[str, Any] = {"request": make_request(), "login_user": _login_user()}

    monkeypatch.setattr(log_aspect, "AsyncManager", _FakeAsyncManager)
    monkeypatch.setattr(async_factory, "get_oper_log_service", lambda: _FakeOperLogService(rows))
    monkeypatch.setattr(async_factory, "get_real_address_by_ip", lambda ip: "内网IP")
    monkeypatch.setattr(log_aspect, "get_request", lambda: state["request"])

    def _get_login_user() -> Any:
        value = state["login_user"]
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(log_aspect, "get_login_user", _get_login_user)

    class _Auditor:
        """一次用例的观察窗口：落库的行 + 可切换的请求/登录态."""

        written = rows
        context = state

        @staticmethod
        def anonymous() -> None:
            state["login_user"] = CustomException("获取用户信息异常", 401)

    return _Auditor()


def _login_user(user_name: str = "admin", dept_name: str = "吉安东路管理中心") -> LoginUser:
    user = SysUser(user_id=1, user_name=user_name, dept=SysDept(dept_id=103, dept_name=dept_name))
    return LoginUser(user=user, permissions={"*:*:*"})


# --------------------------------------------------------------------------- 枚举


class TestEnums:
    """落库的是 ``ordinal()``，顺序即契约."""

    def test_business_type_ordinals(self) -> None:
        assert [item.name for item in BusinessType] == [
            "OTHER",
            "INSERT",
            "UPDATE",
            "DELETE",
            "GRANT",
            "EXPORT",
            "IMPORT",
            "FORCE",
            "GENCODE",
            "CLEAN",
        ]
        assert BusinessType.INSERT.ordinal() == 1
        assert BusinessType.CLEAN.ordinal() == 9

    def test_business_status_ordinals(self) -> None:
        assert BusinessStatus.SUCCESS.ordinal() == 0
        assert BusinessStatus.FAIL.ordinal() == 1

    def test_operator_type_ordinals(self) -> None:
        assert OperatorType.OTHER.ordinal() == 0
        assert OperatorType.MANAGE.ordinal() == 1
        assert OperatorType.MOBILE.ordinal() == 2

    def test_http_method_matches_by_name(self) -> None:
        assert HttpMethod.resolve("POST") is HttpMethod.POST
        assert HttpMethod.resolve("get") is None  # Java 的 valueOf 区分大小写
        assert HttpMethod.GET.matches("GET")
        assert not HttpMethod.GET.matches("POST")


class TestLogAnnotation:
    """Java ``@Log`` 的属性默认值."""

    def test_defaults(self) -> None:
        annotation = Log()

        assert annotation.title == ""
        assert annotation.business_type is BusinessType.OTHER
        assert annotation.operator_type is OperatorType.MANAGE
        assert annotation.is_save_request_data is True
        assert annotation.is_save_response_data is True
        assert annotation.exclude_param_names == ()


# --------------------------------------------------------------------------- 成功 / 失败


class TestSuccessRow:
    def test_every_column_matches_the_java_row(self, auditor: Any) -> None:
        post = SysPost(post_id=9, post_code="probeA", post_name="探针岗位", post_sort="99", status="0")

        _add_post(post)

        assert len(auditor.written) == 1
        row = auditor.written[0]
        assert row.title == "岗位管理"
        assert row.business_type == BusinessType.INSERT.ordinal()
        assert row.operator_type == OperatorType.MANAGE.ordinal()
        assert row.status == BusinessStatus.SUCCESS.ordinal()
        assert row.error_msg is None
        assert row.method == f"{JAVA_CONTROLLER}.add()"
        assert row.request_method == "POST"
        assert row.oper_url == "/system/post"
        assert row.oper_ip == "127.0.0.1"
        # oper_location 由异步任务补（远程查询，不能在请求线程里做）
        assert row.oper_location == "内网IP"
        assert row.oper_name == "admin"
        assert row.dept_name == "吉安东路管理中心"
        # Java: StringUtils.isNotNull(jsonResult) -> JSON.toJSONString(...)
        # ``AjaxResult`` 是 ``HashMap``，桶序 msg(0) -> code(3)，不是 put 序。
        assert row.json_result == '{"msg":"操作成功","code":200}'

    def test_rest_error_result_is_still_success(self, auditor: Any) -> None:
        """``return AjaxResult.error(...)`` 没有抛异常 -> ``status = 0``（踩坑记录第 1 条）."""

        @log(title="岗位管理", business_type=BusinessType.INSERT, java_method="add")
        def _duplicate(post: SysPost) -> AjaxResult:
            return AjaxResult.error_message("岗位名称已存在")

        _duplicate(SysPost(post_id=9))

        row = auditor.written[0]
        assert row.status == BusinessStatus.SUCCESS.ordinal()
        assert row.error_msg is None
        assert row.json_result == '{"msg":"岗位名称已存在","code":500}'

    def test_no_arguments_still_logs(self, auditor: Any) -> None:
        """零参端点（如 ``export``）在 GET 下走 paramsMap 分支，结果是 ``{}``."""

        auditor.context["request"] = make_request("GET", "/system/post/export")

        _export_posts()

        row = auditor.written[0]
        assert row.oper_param == "{}"
        assert row.request_method == "GET"


class TestFailureRow:
    def test_exception_sets_fail_and_propagates(self, auditor: Any) -> None:
        with pytest.raises(CustomException):
            _remove_post(9)

        row = auditor.written[0]
        assert row.status == BusinessStatus.FAIL.ordinal()
        # Java: errorMsg = StringUtils.substring(exception.getMessage(), 0, 2000)
        assert len(row.error_msg) == log_aspect.CONTENT_MAX
        assert row.json_result is None

    def test_not_authenticated_writes_nothing(self, auditor: Any) -> None:
        """``SecurityUtils.getLoginUser()`` 抛异常 -> 整行都不写（踩坑记录第 2 条）."""
        auditor.anonymous()

        _export_posts()

        assert auditor.written == []

    def test_business_result_survives_an_audit_failure(
        self, auditor: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """审计写失败不能影响业务响应（Java 整个 ``handleLog`` 包在 try/catch 里）."""

        def _boom(_ip: str) -> str:
            raise RuntimeError("地址服务挂了")

        monkeypatch.setattr(async_factory, "get_real_address_by_ip", _boom)

        result = _add_post(SysPost(post_id=9))

        assert result == AjaxResult.success()
        assert auditor.written == []


# --------------------------------------------------------------------------- oper_param


class TestRequestValue:
    def test_post_serializes_arguments_in_alphabetical_order(self, auditor: Any) -> None:
        """fastjson2 + ``PropertyPreFilter`` 输出字母序，且省略 null 成员、保留空容器."""
        post = SysPost(post_id=9, post_code="probeA", post_name="探针岗位", post_sort="99", status="0")

        _add_post(post)

        param = auditor.written[0].oper_param
        assert param == (
            '{"flag":false,"params":{},"postCode":"probeA","postId":9,"postName":"探针岗位",'
            '"postSort":"99","status":"0"}'
        )

    def test_query_params_win_over_arguments(self, auditor: Any) -> None:
        """``paramsMap`` 非空时序列化 paramsMap（GET / DELETE 都走这条）."""
        auditor.context["request"] = make_request("PUT", "/system/post", query="postCode=ceo&postSort=1")

        _add_post(SysPost(post_id=9, post_name="不出现"))

        assert auditor.written[0].oper_param == '{"postCode":"ceo","postSort":"1"}'

    def test_repeated_query_keys_are_comma_joined(self, auditor: Any) -> None:
        """Java ``StringUtils.join(values, ",")``."""
        auditor.context["request"] = make_request("GET", "/system/post/list", query="status=0&status=1")

        _export_posts()

        assert auditor.written[0].oper_param == '{"status":"0,1"}'

    def test_excluded_and_sensitive_properties_are_dropped(self, auditor: Any) -> None:
        """``EXCLUDE_PROPERTIES`` 恒排除；``excludeParamNames`` 再叠加."""
        user = SysUser(user_id=1, user_name="admin", password="secret", email="a@b.c", remark="备注")

        _edit_user(user)

        param = auditor.written[0].oper_param
        assert "secret" not in param
        assert "password" not in param
        assert '"userName":"admin"' in param

    def test_response_data_can_be_switched_off(self, auditor: Any) -> None:
        _edit_user(SysUser(user_id=1, user_name="admin"))

        assert auditor.written[0].json_result is None


# --------------------------------------------------------------------------- 截断 / 过滤


class TestHelpers:
    def test_oper_url_is_truncated_to_255(self, auditor: Any) -> None:
        auditor.context["request"] = make_request("GET", "/" + "a" * 400)

        _export_posts()

        assert len(auditor.written[0].oper_url) == log_aspect.URL_MAX

    def test_request_uri_keeps_percent_encoding(self) -> None:
        request = make_request("GET", "/system/post/%E4%B8%AD")

        assert log_aspect._request_uri(request) == "/system/post/%E4%B8%AD"

    def test_filter_object_looks_at_the_first_element_only(self) -> None:
        """Java 的循环体第一轮就 ``return``，不是 ``any()`` —— 照搬."""
        upload = UploadFile(file=io.BytesIO(b""), filename="a.txt")

        assert log_aspect._is_filter_object(upload) is True
        assert log_aspect._is_filter_object([upload]) is True
        assert log_aspect._is_filter_object([1, upload]) is False
        assert log_aspect._is_filter_object([]) is False
        assert log_aspect._is_filter_object({"file": upload}) is True
        assert log_aspect._is_filter_object({"id": 1}) is False

    def test_multipart_argument_is_not_serialized(self, auditor: Any) -> None:
        upload = UploadFile(file=io.BytesIO(b"x"), filename="原始名.txt")

        @log(title="文件", business_type=BusinessType.INSERT, java_method="upload")
        def _upload(file: UploadFile) -> AjaxResult:
            return AjaxResult.success()

        _upload(upload)

        assert auditor.written[0].oper_param in ("", "{}")

    def test_json_result_uses_compact_separators_and_no_ascii_escape(self) -> None:
        assert log_aspect._json_for_result({"msg": "操作成功"}) == '{"msg":"操作成功"}'

    def test_missing_java_controller_fails_fast(self) -> None:
        """缺 ``JAVA_CONTROLLER`` 时导入期就报错，而不是悄悄记一行错的 method."""
        module = types.ModuleType("_fake_controller_without_constant")
        exec("def noop():\n    return 1\n", module.__dict__)  # noqa: S102 - 造一个"控制器"
        sys.modules[module.__name__] = module
        try:
            with pytest.raises(RuntimeError, match="JAVA_CONTROLLER"):
                log(title="无全类名")(module.noop)
        finally:
            sys.modules.pop(module.__name__, None)


# --------------------------------------------------------------------------- 盘点


class TestMigrationInventory:
    """Java 里 ``@Log`` 的调用点必须与 Python 的 ``@log`` 一一对应."""

    @staticmethod
    def _decorations() -> Dict[Path, List[Dict[str, str]]]:
        found: Dict[Path, List[Dict[str, str]]] = {}
        for path in sorted(API_ROOT.rglob("*_controller.py")):
            text = path.read_text(encoding="utf-8")
            rows = []
            for line in text.splitlines():
                match = DECORATOR.match(line.strip())
                if match:
                    rows.append(dict(re.findall(r'(\w+)=("[^"]*"|[\w.]+)', match.group(1))))
            if rows:
                found[path] = rows
        return found

    def test_call_site_count(self) -> None:
        total = sum(len(rows) for rows in self._decorations().values())

        # Java 源里 233 处活的 @Log（另有 5 处整段被块注释掉，不计）。
        # 其中 9 处来自 ruoyi-quartz 的两个控制器：
        # SysJobController 6（export/add/edit/changeStatus/run/remove）
        # + SysJobLogController 3（export/remove/clean）。
        # 另 7 处来自 ruoyi-generator 的 GenController
        # （importTable/update/edit/remove/genCode+edit/genCode+remove/genCode）。
        assert total == 233

    def test_every_call_site_declares_java_method(self) -> None:
        missing = [
            f"{path.name}:{row}"
            for path, rows in self._decorations().items()
            for row in rows
            if "java_method" not in row
        ]

        assert missing == []

    def test_java_controller_matches_the_migrated_from_header(self) -> None:
        mismatched = []
        for path, rows in self._decorations().items():
            text = path.read_text(encoding="utf-8")
            header = MIGRATED_FROM.search(text)
            constant = JAVA_CONTROLLER_LINE.search(text)
            if header is None or constant is None:
                mismatched.append(f"{path.name}: 缺少头部或 JAVA_CONTROLLER")
                continue
            expected = (
                header.group(1).split("src/main/java/")[-1][: -len(".java")].replace("/", ".")
            )
            if constant.group(1) != expected:
                mismatched.append(f"{path.name}: {constant.group(1)} != {expected}")

        assert mismatched == []
