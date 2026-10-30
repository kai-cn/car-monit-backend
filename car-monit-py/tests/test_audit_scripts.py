"""两个新增审计脚本（``scripts/audit_envelopes.py`` / ``scripts/audit_messages.py``）的单测.

# Migrated from: (no Java equivalent -- 审计脚本是本工程的自研工具)

为什么必须测
------------
这两个脚本是「零差异」结论的**证据来源**。如果它们自己会静默漏判（比如把
``AjaxResult`` 误判成等价、把 ``%1$s`` 当成文案差异），那么报告里的 0 就没有意义。
所以这里不测"跑起来能出结果"，而是测**判定规则**本身：

* ``normalize_envelope`` / ``_core``：泛型与占位符的归一化；
* ``iter_java_envelopes``：能不能从一段 Java 控制器里正确拿到信封与
  ``HttpServletResponse`` 标志（导出接口的例外判定全靠它）；
* ``Report.is_allowed``：只有「写响应流的 AjaxResult -> Response」才放行；
* ``MessageReport`` 双向判定：允许表、整文件豁免、骨架包含。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Set

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_envelopes as envelopes  # noqa: E402
import audit_messages as messages  # noqa: E402


# --------------------------------------------------------------------------- #
# 信封审计
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("AjaxResult", "AjaxResult"),
        ("TableDataInfo", "TableDataInfo"),
        ("R", "R"),
        ("R<List<UserEntity>>", "R"),
        ("R<String>", "R"),
        ("List<ImportEntity>", "List"),
        ("void", "void"),
        ("String", "String"),
        ("List [ ImportEntity ]", "List"),
    ],
)
def test_normalize_envelope_strips_generics(raw: str, expected: str) -> None:
    """``R<List<UserEntity>>`` 必须归一成 ``R``，否则和 Python 的 ``R`` 对不上。"""

    assert envelopes.normalize_envelope(raw) == expected


_JAVA_SOURCE = """
package com.ruoyi.web.controller.demo;

@RestController
@RequestMapping("/demo")
public class DemoController extends BaseController
{
    @PreAuthorize("@ss.hasPermi('demo:list')")
    @GetMapping("/list")
    public TableDataInfo list(DemoParam param)
    {
        startPage();
        return getDataTable(service.selectList(param));
    }

    /**
     * 导出（写进响应流，那句 AjaxResult 到不了客户端）
     */
    @GetMapping("/export")
    public AjaxResult export(DemoParam param, HttpServletResponse response)
    {
        List<Demo> list = service.selectList(param);
        ExcelUtil<Demo> util = new ExcelUtil<Demo>(Demo.class);
        util.exportExcel(response, list, "演示数据");
        return AjaxResult.success("导出成功");
    }

    @PostMapping(value = {"/sync", "/sync2"})
    public AjaxResult sync()
    {
        return AjaxResult.success();
    }
}
"""


def test_iter_java_envelopes_reads_envelope_and_stream_flag() -> None:
    """导出接口的 ``writes_stream`` 必须为 ``True`` —— 这是唯一的例外判定依据。"""

    found = {
        (item.method, item.path): item
        for item in envelopes.iter_java_envelopes(_JAVA_SOURCE, "DemoController")
    }

    assert sorted(found) == [
        ("GET", "/demo/export"),
        ("GET", "/demo/list"),
        ("POST", "/demo/sync"),
        ("POST", "/demo/sync2"),
    ]

    assert found[("GET", "/demo/list")].envelope == "TableDataInfo"
    assert found[("GET", "/demo/list")].writes_stream is False

    export = found[("GET", "/demo/export")]
    assert export.envelope == "AjaxResult"
    assert export.writes_stream is True
    assert export.java_method == "export"

    # 数组形式的 value = {"/sync", "/sync2"} 要展开成两条
    assert found[("POST", "/demo/sync2")].envelope == "AjaxResult"
    assert found[("POST", "/demo/sync2")].writes_stream is False


def test_envelope_is_allowed_only_for_real_stream_exports() -> None:
    """``AjaxResult -> Response`` 只有「形参带 response」才放行，否则是真差异。"""

    exported = envelopes.JavaEnvelope(
        controller="DemoController",
        method="GET",
        path="/demo/export",
        java_method="export",
        envelope="AjaxResult",
        writes_stream=True,
    )
    plain = envelopes.JavaEnvelope(
        controller="DemoController",
        method="GET",
        path="/demo/list",
        java_method="list",
        envelope="AjaxResult",
        writes_stream=False,
    )

    assert envelopes.Report.is_allowed(exported, "Response") is True
    assert envelopes.Report.is_allowed(plain, "Response") is False
    assert envelopes.Report.is_allowed(plain, "AjaxResult") is True
    # 分页体被写成普通信封：任何情况都不放过
    assert envelopes.Report.is_allowed(plain, "TableDataInfo") is False


def test_report_lists_mismatches_and_skips_unmatched_routes() -> None:
    """配对不上的路由不参与信封比较（那是 ``audit_endpoints`` 的职责）。"""

    matched = envelopes.JavaEnvelope("A", "GET", "/a", "a", "TableDataInfo")
    unmatched = envelopes.JavaEnvelope("B", "GET", "/b", "b", "AjaxResult")
    report = envelopes.Report(
        java=[matched, unmatched],
        python={("GET", "/a"): "AjaxResult"},
    )

    assert [item.path for item in report.comparable] == ["/a"]
    mismatched = report.mismatched
    assert len(mismatched) == 1
    assert mismatched[0][0].path == "/a"
    assert mismatched[0][1] == "AjaxResult"


# --------------------------------------------------------------------------- #
# 文案审计
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("新增成功", "新增成功"),
        ("内置参数【%1$s】不能删除 ", "内置参数【】不能删除"),
        ("内置参数【{}】不能删除 ", "内置参数【】不能删除"),
        ("角色{0}已分配", "角色已分配"),
        ("参数[{name}]不合法", "参数不合法"),
        ("请求路径中缺少必需的路径变量[%s]", "请求路径中缺少必需的路径变量"),
        ("请求路径中缺少必需的路径变量[jobLogId]", "请求路径中缺少必需的路径变量"),
        ("要求类型为：'%s'", "要求类型为："),
        ("要求类型为：'java.lang.Long'", "要求类型为："),
    ],
)
def test_core_strips_placeholders_and_quoted_values(raw: str, expected: str) -> None:
    """``_core`` 只去占位符，不动中文本身——否则“文案不同”会被它抹平。"""

    assert messages._core(raw) == expected


def _report(
    java: Dict[str, Set[str]],
    python: Dict[str, Set[str]],
    java_source: str = "",
    python_source: str = "",
) -> messages.MessageReport:
    return messages.MessageReport(
        java=java,
        python=python,
        java_source=java_source,
        python_source=python_source,
    )


def test_forward_check_flags_lost_message_and_honours_allowlist() -> None:
    """Java 文案在 Python 里找不到要报出来；允许表与整文件豁免要能压住它。"""

    report = _report(
        java={
            "新增成功": {"ruoyi-admin/src/main/java/com/ruoyi/web/controller/A.java"},
            "在 [": {"ruoyi-common/src/main/java/com/ruoyi/common/utils/ReflectUtils.java"},
            "[视图维护任务] %s执行失败": {
                "ruoyi-system/src/main/java/com/ruoyi/base/task/ViewMaintenanceTask.java"
            },
        },
        python={},
        python_source="",
    )

    missing = [literal for literal, _ in report.missing_in_python]
    assert missing == ["新增成功"]


def test_forward_check_matches_by_core_across_formats() -> None:
    """Java 用 ``%s``、Python 在调用点写死类型名，骨架相同就算一致。"""

    report = _report(
        java={"请求参数类型不匹配，参数[%s]要求类型为：'%s'，但输入值为：'%s'": {"G.java"}},
        python={"请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Long'，但输入值为：'%s'": {"b.py"}},
        python_source="",
    )

    assert report.missing_in_python == []


def test_reverse_check_flags_invented_message() -> None:
    """Python 凭空造出的响应文案必须报出来（否则前端弹窗会和 Java 不一致）。"""

    report = _report(
        java={"删除成功": {"A.java"}},
        python={"删除成果": {"app/system/service/x_service.py"}},
        java_source="删除成功",
    )

    assert [literal for literal, _ in report.invented_in_python] == ["删除成果"]


def test_reverse_check_exempts_replacement_layers_and_known_cores() -> None:
    """替代第三方库的文件、以及与 Java 骨架一致的文案，都不算“凭空发明”。"""

    replacement_layer = sorted(messages.PYTHON_ONLY_FILES)[0]
    report = _report(
        java={"内置参数": {"A.java"}},
        python={
            "map 字面量缺少冒号": {replacement_layer},
            "内置参数【】不能删除": {"app/system/service/sys_config_service.py"},
        },
        java_source="内置参数【%1$s】不能删除",
    )

    assert report.invented_in_python == []


def test_collapse_concat_rebuilds_the_runtime_message() -> None:
    """Java 把运行时值拼在中间时，折叠后要能还原成运行时真正的那句话。"""

    source = 'return AjaxResult.error("新增用户\'" + user.getUserName() + "\'失败，登录账号已存在");'

    assert "新增用户''失败，登录账号已存在" in messages._collapse_concat(source)


def test_collapse_concat_handles_three_fragments() -> None:
    """``"A" + x + "B" + y + "C"`` 要反复折叠到稳定。"""

    assert messages._collapse_concat('"A" + x + "B" + y + "C"') == '"ABC"'


def test_reverse_check_accepts_java_concatenation() -> None:
    """Java 用 ``"前缀'" + 变量 + "'后缀"`` 拼出来的文案，不能算 Python 凭空发明。"""

    java_source = '"新增用户\'" + user.getUserName() + "\'失败，登录账号已存在"'
    report = messages.MessageReport(
        java={},
        python={"新增用户'{}'失败，登录账号已存在": {"app/api/system/sys_user_controller.py"}},
        java_source=java_source,
        java_concat=messages._collapse_concat(java_source),
    )

    assert report.invented_in_python == []


def test_reverse_check_reads_i18n_resources() -> None:
    """提示语也可能放在 ``messages.properties`` 里（``user.logout.success=退出成功``），
    资源文件要算成“Java 存在”，否则会误报成发明文案。"""

    assert messages.JAVA_EXTRA_SOURCES
    for relative in messages.JAVA_EXTRA_SOURCES:
        assert (messages.PROJECT_ROOT / relative).exists(), relative

    resources = (messages.PROJECT_ROOT / messages.JAVA_EXTRA_SOURCES[0]).read_text(encoding="utf-8")
    report = messages.MessageReport(
        java={},
        python={"退出成功": {"app/framework/security/handle/logout_success_handler_impl.py"}},
        java_source="",
        java_concat=messages._collapse_concat(resources),
    )

    assert report.invented_in_python == []


def test_module_level_message_constant_is_collected() -> None:
    """``EDIT_PHONE_EXISTS = "修改用户'{}'失败…"`` 这类常量也要进采样，
    否则反向检查看不见控制器里真正会被弹出的文案。"""

    source = 'EDIT_PHONE_EXISTS = "修改用户\'{}\'失败，手机号码已存在"\n\n\nclass X:\n    pass\n'
    bucket: Dict[str, Set[str]] = {}

    messages._collect(source, messages.PYTHON_RESPONSE_LITERAL, Path("app/x.py"), bucket)

    assert "修改用户'{}'失败，手机号码已存在" in bucket


def test_allowlist_keys_all_have_a_reason() -> None:
    """允许表的每条都要写原因，防止有人图省事把差异塞进来。"""

    assert messages.ALLOWLIST
    assert all(reason.strip() for reason in messages.ALLOWLIST.values())
    assert all(reason.strip() for reason in messages.JAVA_ONLY_FILES.values())
    assert all(reason.strip() for reason in messages.PYTHON_ONLY_FILES.values())
