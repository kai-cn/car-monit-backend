"""Java <-> Python **文案**一致性审计：会进响应体的中文串（``msg`` / 异常消息）.

用法::

    python scripts/audit_messages.py            # 打印差异报告
    python scripts/audit_messages.py --json     # 输出机器可读结果

为什么需要这一层
----------------
``audit_endpoints`` 比路由、``audit_domains`` 比字段、``audit_envelopes`` 比信封形状，
但**响应体里那句 ``msg``** 始终没有检查过。RuoYi 的提示语散落在控制器（``AjaxResult.success("新增成功")``）
和 Service（``throw new CustomException("...")``）里，由 ``GlobalExceptionHandler`` 原样塞进
``{"msg": ...}``。少一个字、多一个全角叹号，前端弹窗和用户看到的就不一样。

两个方向都查
------------
* **Java -> Python**：Java 的每条文案必须在 Python 源码里**原样出现**（不能漏、不能改写）。
* **Python -> Java**：Python 的每条文案必须在 Java 源码树里出现（不能凭空发明）。

只比 ``AjaxResult.(success|error|warn)`` / ``put("msg", ...)`` / ``new *Exception("...")``
这三种「会进响应体」的写法——日志、Javadoc、注释里的中文不算，否则噪声无法收敛。

``ALLOWLIST`` 收录「Java 有但 Python 不该有」的文案，每条都写明原因（多为未接线的代码）。
新增例外必须同时改本文件与 ``COMPATIBILITY.md``。
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = PROJECT_ROOT / "car-monit-py"
JAVA_MODULES = (
    "ruoyi-admin",
    "ruoyi-system",
    "ruoyi-common",
    "ruoyi-framework",
    "ruoyi-quartz",
    "ruoyi-generator",
)

CJK = re.compile(r"[\u4e00-\u9fff]")

#: Java 侧「会进响应体」的字面量：``AjaxResult.success("..")`` / ``put("msg", "..")`` /
#: ``new XxxException("..")`` / ``String.format("..")``（后者几乎总是包在这两者里：
#: ``new CustomException(String.format("内置参数【%1$s】不能删除 ", ...))``）。
JAVA_RESPONSE_LITERAL = (
    re.compile(r'AjaxResult\s*\.\s*(?:success|error|warn)\s*\(\s*"([^"\\\n]{1,160})"'),
    re.compile(r'put\s*\(\s*"msg"\s*,\s*"([^"\\\n]{1,160})"'),
    re.compile(r'new\s+\w*(?:Exception|Error)\s*\(\s*"([^"\\\n]{1,160})"'),
    re.compile(r'(?:String|StringUtils)\s*\.\s*format\s*\(\s*"([^"\\\n]{1,160})"'),
)

#: Python 侧同样三类写法：``AjaxResult.*`` 与 ``raise <RuoYi 异常>(...)``。
#: 不能把 ``raise ValueError`` / ``RuntimeError`` 也算进来——那是 Python 内部诊断，
#: 不是响应体内容，否则噪声无法收敛。
#: 第三条是**模块级文案常量**（``EDIT_PHONE_EXISTS = "修改用户'{}'失败…"``）：
#: 为了让常量名可复用，Python 把文案提到模块顶端，抛出处只写常量名；
#: 不扫这一条，反向检查会漏掉真正“可能被发明”的那批文案。
PYTHON_RESPONSE_LITERAL = (
    re.compile(r'AjaxResult\s*\.\s*(?:success|error|warn)\(\s*f?"([^"\\\n]{1,160})"'),
    re.compile(
        r'raise\s+(?:ServiceException|BusinessException|CustomException|UtilException'
        r'|DemoModeException|AccessDeniedException)\s*\(\s*f?"([^"\\\n]{1,160})"'
    ),
    re.compile(r'^\s*[A-Z][A-Z0-9_]{3,}\s*=\s*f?"([^"\\\n]{1,160})"', re.MULTILINE),
)

#: 占位符与运行时插值：
#: * Java 的 ``{}`` / ``%s`` / ``%1$s``，Python 的 ``{xxx}`` / ``%s``
#: * 单引号括起来、运行时才填进去的片段（如 ``要求类型为：'%s'``）
#: * 方括号包住的运行时值（``请求路径中缺少必需的路径变量[%s]`` vs ``...[jobLogId]``）
#: 比对前两边都剔除，否则“格式化写法不同”会被误报成“文案不同”。
_PLACEHOLDER = re.compile(r"\{[^{}]*\}|%\d+\$[sdf]|%[sdf]|'[^'\n]*'|\[[^\[\]]{0,40}\]")

#: Python **替代第三方库**的内部诊断（必须自己写错误文案），整份文件豁免反向检查。
PYTHON_ONLY_FILES: Dict[str, str] = {
    "app/generator/util/velocity_engine.py": "自研 Velocity 解释器，Java 侧的语法错误由 Apache Velocity 以英文抛出",
    "app/base/service/forest/forest_client.py": "Forest HTTP 客户端的 Python 替代实现",
    "app/base/service/forest/http_base_info_api_service.py": "同上",
    "app/system/service/forest/file_api.py": "同上",
    "app/common/utils/oss_template.py": "boto3 适配层，Java 侧用 OSS SDK",
    "app/common/utils/import_util.py": "xlrd 依赖提示，Java 侧由 HSSF 工作簿承担",
    "app/common/utils/poi/excel_util.py": "``ColumnType.IMAGE`` 在 Java 里也是未实现分支",
    "app/common/core/text/convert.py": "复现 JDK 的 NPE 文案，Java 源码里也没有这个字面量",
    "app/framework/aspectj/log_aspect.py": "测试期断言，只在开发时抛出",
}

#: 「Java 有、Python 不该有」的文案 -> 原因。键是**原文**，一字不差。
ALLOWLIST: Dict[str, str] = {
    "部门停用，不允许新增": "SysDeptServiceImpl 里整段被块注释掉，线上走不到（Python 照抄了“不实现”）",
    "转换过程中发生错误": "MultipartFileUtil 把 byte[] 转 Spring MultipartFile 时才抛；Python 没有这一层转换",
    "startTime 和 endTime 不能为空": "SnapshotCursorPageQuery 只被 PartitionQueryServiceImpl 使用，该类没有任何控制器引用",
    "startTime 必须早于 endTime": "同上：PartitionQueryServiceImpl 未接线到任何端点",
    "ES查询失败": "SnapshotFlowElasticsearchService 未接线（Java 里 CDC 那次调用是注释状态）",
    "服务器限流异常，请稍候再试": "RateLimiterAspect 属未迁移项，全仓无 @RateLimiter 使用点",
    "访问过于频繁，请稍候再试": "同上",
    "mybatis typeAliasesPackage 路径扫描错误,参数typeAliasesPackage:": "MyBatis 专属启动期异常，Python 无此概念",
    "在 [": "ReflectUtils 反射工具类，Python 无对应实现",
    "全量同步完成，同步数: ": "DataConsistencyService 未接线（无控制器引用）",
}

#: 「整份 Java 文件里的文案都不用搬」-> 原因。用于**永不执行**的代码。
JAVA_ONLY_FILES: Dict[str, str] = {
    "ruoyi-system/src/main/java/com/ruoyi/base/task/ViewMaintenanceTask.java": "@Scheduled 入口，Java 无 @EnableScheduling，从不触发（COMPATIBILITY §11）",
    "ruoyi-system/src/main/java/com/ruoyi/base/task/ShardingTableTask.java": "同上；且分表的 INSERT 本身是死代码（§42.3）",
    "ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/ViewMaintenanceOptimizationService.java": "只被 ViewMaintenanceTask 调用，而它从不执行",
}

#: 文案不只写在 ``.java`` 里：提示语也可能放在 i18n 资源文件中由
#: ``MessageUtils.message("user.logout.success")`` 取出，源码里看不到中文。
#: 反向检查必须把这份文件也算成“Java 存在”。
JAVA_EXTRA_SOURCES = (
    "ruoyi-admin/src/main/resources/i18n/messages.properties",
)

#: Java 组装文案时会把运行时值拼在中间：
#: ``"新增用户'" + user.getUserName() + "'失败，登录账号已存在"``。
#: 逐字面量比对时两段都不完整，所以先把这个表达式从源码里“抹掉”，
#: 让两端字符串接成运行时真正的样子，再做包含判定。
_CONCAT_MIDDLE = re.compile(r'"\s*\+\s*[^;"\n{}]{1,60}?\+\s*"')


def _collapse_concat(source: str) -> str:
    """把 ``"A" + expr + "B"`` 折叠成 ``AB``（反复折叠直到不再变化，处理 ``a + x + b + y + c``）."""

    text = source
    while True:
        folded = _CONCAT_MIDDLE.sub("", text)
        if folded == text:
            return folded
        text = folded


def _core(text: str) -> str:
    """剔掉占位符后的“骨架”，用于跳过格式化差异（``{}`` vs ``{name}`` vs ``%s``）."""

    return _PLACEHOLDER.sub("", text).strip()


@dataclass
class MessageReport:
    """审计结果."""

    java: Dict[str, Set[str]] = field(default_factory=dict)
    python: Dict[str, Set[str]] = field(default_factory=dict)
    python_source: str = ""
    java_source: str = ""
    #: 折叠掉 ``"A" + expr + "B"`` 后的 Java 源码，专供反向检查用。
    java_concat: str = ""

    @property
    def java_cores(self) -> List[str]:
        """Java 各文案的骨架（按长度倒序，方便“包含”判定）."""

        return sorted({_core(item) for item in self.java if len(_core(item)) >= 4}, key=len, reverse=True)

    @property
    def python_cores(self) -> List[str]:
        """Python 各文案的骨架."""

        return sorted({_core(item) for item in self.python if len(_core(item)) >= 4}, key=len, reverse=True)

    def _java_file_exempt(self, files: Set[str]) -> bool:
        return bool(files) and all(path in JAVA_ONLY_FILES for path in files)

    @property
    def missing_in_python(self) -> List[Tuple[str, List[str]]]:
        rows: List[Tuple[str, List[str]]] = []
        cores = self.python_cores
        for literal in sorted(self.java):
            files = self.java[literal]
            if literal in ALLOWLIST or self._java_file_exempt(files):
                continue
            if literal in self.python_source:
                continue
            # 骨架对骨架：容忍“Java 用 %s 占位、Python 在调用点写死”这类格式化差异
            core = _core(literal)
            if len(core) >= 4 and any(core in item or item in core for item in cores):
                continue
            rows.append((literal, sorted(files)))
        return rows

    def _python_only_ok(self, files: Set[str]) -> bool:
        return bool(files) and all(path in PYTHON_ONLY_FILES for path in files)

    def _core_seen_in_java(self, literal: str) -> bool:
        """骨架对骨架比：容忍 Java 的字符串拼接与不同的占位符写法."""

        core = _core(literal)
        if len(core) < 4:
            return True
        if core in self.java_source:
            return True
        if core in self.java_concat:
            return True
        # 折叠后剩下的是 ``修改参数''失败…``（原来中间夹着运行时值），
        # 去掉引号才能和 Python 侧的 ``修改参数{}失败…`` 对齐。
        loose = core.replace("'", "")
        if loose and loose in self.java_concat.replace("'", ""):
            return True
        return any(core in item or item in core for item in self.java_cores if len(item) >= 4)

    @property
    def invented_in_python(self) -> List[Tuple[str, List[str]]]:
        rows: List[Tuple[str, List[str]]] = []
        for literal in sorted(self.python):
            files = self.python[literal]
            if self._python_only_ok(files) or self._core_seen_in_java(literal):
                continue
            rows.append((literal, sorted(files)))
        return rows


def _iter_java_files():
    for module in JAVA_MODULES:
        for path in (PROJECT_ROOT / module / "src").rglob("*.java"):
            if "target" in path.parts:
                continue
            yield path


def _collect(source_text: str, patterns, base: Path, bucket: Dict[str, Set[str]]) -> None:
    for pattern in patterns:
        for match in pattern.finditer(source_text):
            literal = match.group(1)
            if CJK.search(literal):
                bucket.setdefault(literal, set()).add(base.as_posix())


def build_report() -> MessageReport:
    report = MessageReport()
    java_chunks: List[str] = []
    for path in _iter_java_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        java_chunks.append(text)
        _collect(text, JAVA_RESPONSE_LITERAL, path.relative_to(PROJECT_ROOT), report.java)

    python_chunks: List[str] = []
    for path in sorted((PY_ROOT / "app").rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        python_chunks.append(text)
        _collect(text, PYTHON_RESPONSE_LITERAL, path.relative_to(PY_ROOT), report.python)

    report.java_source = "\n".join(java_chunks)
    extra_chunks: List[str] = []
    for relative in JAVA_EXTRA_SOURCES:
        path = PROJECT_ROOT / relative
        if path.exists():
            extra_chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    report.java_concat = _collapse_concat(report.java_source + "\n" + "\n".join(extra_chunks))
    report.python_source = "\n".join(python_chunks)
    return report


def render(report: MessageReport) -> str:
    lines: List[str] = []
    lines.append(f"Java 文案 : {len(report.java)} 种")
    lines.append(f"Python 文案: {len(report.python)} 种")
    lines.append(f"已登记的 Java 例外: {len(ALLOWLIST)} 种")
    lines.append(f"永不执行的 Java 文件: {len(JAVA_ONLY_FILES)} 个")
    lines.append(f"豁免反向检查的替代层文件: {len(PYTHON_ONLY_FILES)} 个")
    lines.append("")

    missing = report.missing_in_python
    lines.append(f"== Java 有、Python 侧找不到（{len(missing)}） ==")
    for literal, where in missing:
        lines.append(f"  {literal}   ({where[0]})")
    lines.append("")

    invented = report.invented_in_python
    lines.append(f"== Python 有、Java 侧找不到（{len(invented)}） ==")
    for literal, where in invented:
        lines.append(f"  {literal}   ({where[0]})")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="输出 JSON 而不是报告文本")
    arguments = parser.parse_args()

    report = build_report()
    missing = report.missing_in_python
    invented = report.invented_in_python

    if arguments.json:
        payload = {
            "java": len(report.java),
            "python": len(report.python),
            "allowlisted": len(ALLOWLIST),
            "javaOnlyFiles": len(JAVA_ONLY_FILES),
            "pythonOnlyFiles": len(PYTHON_ONLY_FILES),
            "missingInPython": [{"literal": item, "files": files} for item, files in missing],
            "inventedInPython": [{"literal": item, "files": files} for item, files in invented],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(report))

    return 1 if (missing or invented) else 0


if __name__ == "__main__":
    raise SystemExit(main())
