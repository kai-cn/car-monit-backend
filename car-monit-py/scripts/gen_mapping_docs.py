"""生成 ``MAPPING_BASE/MANAGER/FLOW/TOOL/GENERATOR.md``。

# Migrated from: (no Java equivalent -- 文档生成器)

为什么用脚本生成
----------------
这 5 份对照表里 90% 的内容是**机械可推导**的：Java 控制器 → Python 模块（``# Migrated from:``
行）、方法级注解 → ``(method, path, 权限点, @Log)``、以及 ``create_app()`` 里真正注册的
处理函数名。手抄 340 多个端点必然抄错、且日后改代码就会失真。

所以：**表和计数由脚本产出，解释性文字写在下面的 ``PACKAGES`` 配置里**。
要改文档，改配置或改代码，然后重跑::

    python scripts/gen_mapping_docs.py

``scripts/`` 下其余三个脚本是**校验**用的（``audit_endpoints`` / ``audit_domains`` /
``audit_envelopes``），本脚本只负责出版；两者口径一致：都用
``audit_endpoints.iter_java_endpoints`` 解析 Java，都读 ``create_app().routes`` 读 Python。
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_endpoints as base  # noqa: E402

MIGRATED = re.compile(r"^#\s*Migrated from:\s*(\S+)\s*$", re.MULTILINE)
LOG_ANNOTATION = re.compile(r"@Log\s*\(")

PACKAGES: Dict[str, dict] = {
    "base": {
        "title": "基础数据（`com.ruoyi.web.controller.base`）",
        "controller_dir": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/base",
        "notes": [
            "`OdsCxztFwqcllsController` 的文件在 `controller/base/` 下，路径却是 `/manager/fwqclls`，"
            "权限点也是 `manager:fwqclls:list` —— Java 原文如此，不是抄错。",
            "`GeometryController#getHenDa` 用的是 **`base:geometry:list`**（不是 `:query`）："
            "同一个控制器里 `getInfo` 反而没有权限点。",
            "ODS 表的 `export` 一律用**列表权限**（`base:feerecords:list`、`base:snapshotflow:list`），"
            "只有配置类实体的 `export` 才有独立的 `:export` 权限点。",
            "导出端点（24 个，全工程口径）在 Java 里先 `ExcelUtil.exportExcel(response, ...)` "
            "把 xlsx 写进响应流，末尾的 `return AjaxResult.success(\"导出成功\")` **到不了客户端**；"
            "所以 Python 直接返回 `Response`，这是 `scripts/audit_envelopes.py` 里唯一放行的"
            "「`AjaxResult` → `Response`」情形（判定依据是 Java 形参里有 `HttpServletResponse`）。",
            "`list`/`getInfo` 的 Python 函数名带业务后缀（`list_fwqclls`、`list_fee_gantries`、"
            "`list_geometries`），避免同名 `list` 在一个模块内重名；对应关系见 §4 表。",
        ],
        "tests": [
            ("Controller", "`tests/test_base_config_service_area_controller.py`", 19,
             "`/base/configServiceArea` 的 7 个端点：路由表、权限点、`@Log`、分页与导出"),
            ("Controller", "`tests/test_base_ods_controllers.py`", 36,
             "第二批 8 个 ODS 控制器：注解展开、权限点、导出走流"),
            ("Controller", "`tests/test_base_ods_readonly.py`", 58,
             "6 个只读 ODS 模块：`list` 的分页与 `getInfo` 的 404/空对象语义"),
            ("Controller", "`tests/test_base_ip_tables.py`", 31,
             "`/base/gantryIp` 与 `/base/tollStationIp` 两套设备 IP 表"),
            ("Mapper", "`tests/test_base_config_service_area_mapper.py`", 20,
             "`BaseConfigServiceAreaMapper` / Service：SQL 形状与批量删除语义"),
        ],
    },
    "manager": {
        "title": "车辆监控业务（`com.ruoyi.web.controller.manager`）",
        "controller_dir": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager",
        "notes": [
            "`bigscreen/BigScreenController` 单独一层路径（`/manager/bigScreen/**`），"
            "Python 侧对应 `app/api/manager/bigscreen/big_screen_controller.py`，目录也照搬。",
            "`BussTestController#syncCurrentTrack` 是 `void`：Java 只往响应里写一个空体，"
            "Python 返回 `Response(status_code=200)`（`COMPATIBILITY.md` 有登记）。",
            "绝大多数 `export` 是**先写 Excel 再返回**（`AjaxResult` 到不了客户端），"
            "`exportAbnormalPassage` 则是 `void` —— 两种都按「写流」处理。",
            "`CarExceptRecordController` 的导入端点把文案提成了模块级常量"
            "（`TEMPLATE_INVALID_MESSAGE` 等），文案与 Java 一字不差，由 "
            "`scripts/audit_messages.py` 双向比对守住。",
            "业务校验**直接返回 `AjaxResult`**（不是抛异常），文案里的错别字照抄："
            "`可疑车俩不存在！`（“车俩”）、`录入区间时间重复！`、`车牌号存在重复，请确定！` —— "
            "Python 用同名常量保存，一字不差，由 `scripts/audit_messages.py` 守住。",
        ],
        "tests": [
            ("Controller", "`tests/test_manager_controllers.py`", 53,
             "19 个业务控制器：路由、权限点、`@Log`、CRUD 的 `code/msg` 契约"),
            ("Controller", "`tests/test_big_screen_controller.py`", 30,
             "大屏接口：参数绑定、聚合结构、惰性 import 的回归护栏"),
        ],
    },
    "flow": {
        "title": "审批流（`com.ruoyi.web.controller.flow`）",
        "controller_dir": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow",
        "notes": [
            "只有 `FlowNameController` 带 `@PreAuthorize`（`flow:flowname:*`），其余 6 个控制器"
            "共 48 个端点**完全没有权限点**（只受登录保护）—— Java 原文如此，不是漏搬。",
            "写操作都带 `@Log`，`title` 各不相同：我的申请 / 流程_当前节点 / 审核历史记录 / "
            "系统消息处理人 / 系统内部消息 / 流程名称 / 流程节点。",
            "路径变量名不统一（`{ids}` / `{mid}` / `{billOid}` / `{id}`），Python 照抄；"
            "FastAPI 按名字取值，改名字会直接 422。",
            "`FlowMessageInfoController` 的四个 `list*` 在 Python 里换成了可读名"
            "（`list_pending` / `list_messages` / `list_done` / `list_finished`），路径不变。",
        ],
        "tests": [
            ("Controller", "`tests/test_flow_controllers.py`", 55,
             "55 条端点逐条契约：路径、权限点、响应信封、参数校验"),
        ],
    },
    "tool": {
        "title": "开发脚手架（`com.ruoyi.web.controller.tool`）",
        "controller_dir": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool",
        "notes": [
            "`TestController` 是 RuoYi 自带的**演示用**控制器：不碰数据库、不碰 Redis，"
            "数据只在进程内存的 `LinkedHashMap<Integer, UserEntity>` 里。按迁移原则第 4 条"
            "「不擅自删除看似无用的 Java 代码」整块照搬，包括下面这些怪癖。",
            "5 个端点**全都没有权限点**：`SecurityConfig` 里没有一条规则命中 `/test/**`，"
            "落到 `anyRequest().authenticated()` —— 登录即可。",
            "`POST /test/user/save` 的形参**没有** `@RequestBody`，Spring 按表单/query 绑定；"
            "发 JSON 会三个字段全 `null` 并回 `{\"code\":500,\"msg\":\"用户ID不能为空\"}`。照搬。",
            "`PUT /test/user/update` 的形参**有** `@RequestBody`，读 JSON。两个写端点绑定方式不同，"
            "**不是不一致，是 Java 原文**。",
            "列表顺序是**插入顺序**（`LinkedHashMap`），`put` 已存在的键只改值、不动位置。",
        ],
        "tests": [
            ("Controller", "`tests/test_tool_test_controller.py`", 26,
             "5 个端点：无权限点的鉴权边界、save 的表单绑定、内存 Map 的插入顺序与覆盖语义"),
        ],
    },
    "generator": {
        "title": "代码生成（`com.ruoyi.generator`）",
        "controller_dir": "ruoyi-generator/src/main/java/com/ruoyi/generator/controller",
        "notes": [
            "`GenController` 在 **`ruoyi-generator` 模块**（不在 `ruoyi-admin`），"
            "但路径挂在 `/tool/gen` 下 —— 与 `ruoyi-admin` 的 `TestController` 同属 `/tool` 前缀。",
            "两处路径变量**拼写就是 `talbleId`**（`GET /tool/gen/{talbleId}`、"
            "`GET /tool/gen/column/{talbleId}`）—— Java 原文的错别字，照抄不改；"
            "Python 侧只是改成了 `{talble_id}`。",
            "`download` 与 `batchGenCode` 在 Java 里返回 `void`：zip 直接写响应流，"
            "Python 返回 `Response`（`audit_envelopes` 的 `void → Response` 之一）。",
            "15 个映射里 12 个带 `@PreAuthorize`；`all/list`、`getColumnList`、`getAllColumnList` "
            "三个**没有**（登录即可）。`/{talbleId}` 必须**最后注册** —— 否则会把 `/list`、"
            "`/batchGenCode` 当成 id，在 `int()` 处 500。",
            "模板引擎没引 Apache Velocity，而是 `app/generator/util/velocity_engine.py` 的"
            "自研解释器（理由见 `COMPATIBILITY.md`）；`VelocityUtils` 的上下文拼装逐行照搬。",
        ],
        "tests": [
            ("Controller", "`tests/test_gen_controller.py`", 70,
             "15 个端点：权限点、`@Log`、`talbleId` 拼写、`download`/`batchGenCode` 写流"),
            ("Mapper", "`tests/test_gen_table_mapper.py`", 23,
             "`GenTableMapper` 10 条 statement 的 SQL 形状"),
            ("Mapper", "`tests/test_gen_table_column_mapper.py`", 17,
             "`GenTableColumnMapper` 8 条 statement 的 SQL 形状"),
            ("Service", "`tests/test_gen_table_service.py`", 43,
             "五个 `init*` 的顺序、三段校验、导入的包装异常"),
        ],
    },
}

READING = """\
> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
>
> 表由 `scripts/gen_mapping_docs.py` 从源码生成（`# Migrated from:` 行 + 方法级注解 +
> `create_app()` 真正注册的路由），**手改会被下次生成覆盖**：要改就改代码，再重跑脚本。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md)。
>
> 阅读约定：
>
> - `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
>   逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
> - Python 用 `snake_case`，Java 用 `camelCase`，转换是机械的：
>   `selectJobList` → `select_job_list`。
> - `@Log` 列写成 `title / businessType`；`—` 表示 Java 侧没有该注解。
> - 权限点列写的是 `@PreAuthorize("@ss.hasPermi('...')")` 里的那个串；`—` 表示没有权限注解
>   （只受「登录」保护）。
> - 路径列写的是 **Java 的 URI 模板**；Python 侧路径变量按 PEP8 改成 snake_case
>   （`{jobId}` → `{job_id}`、`{IDs}` → `{ids}`），路由匹配结果不受影响。
"""


def _collect_java() -> Tuple[List, Dict, Dict]:
    items: List = []
    log_by: Dict = {}
    file_by_controller: Dict[str, Path] = {}
    for directory in base.JAVA_SOURCES:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*Controller.java")):
            source = path.read_text(encoding="utf-8", errors="replace")
            cleaned = base.strip_comments(source)
            items.extend(base.iter_java_endpoints(cleaned, path.stem))
            file_by_controller[path.stem] = path
            for match in LOG_ANNOTATION.finditer(cleaned):
                args, _ = base._balanced_paren_args(cleaned, match.end() - 1)
                title = re.search(r'title\s*=\s*"([^"]*)"', args)
                business = re.search(r"businessType\s*=\s*BusinessType\.(\w+)", args)
                java_method = base._enclosing_method(cleaned, match.end() + len(args))
                log_by[(path.stem, java_method)] = (
                    title.group(1) if title else "",
                    business.group(1) if business else "",
                )
    return items, log_by, file_by_controller


def _collect_python_names() -> Dict[Tuple[str, str], str]:
    sys.path.insert(0, str(ROOT))
    from app.main import create_app  # noqa: PLC0415 -- 需要 sys.path 先就位

    names: Dict[Tuple[str, str], str] = {}
    for route in create_app().routes:
        path = getattr(route, "path", "")
        if not path.startswith("/"):
            continue
        for method in sorted(getattr(route, "methods", None) or set()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            endpoint = getattr(route, "endpoint", None)
            names[(method, base.normalize_path(path))] = getattr(endpoint, "__name__", "?")
    return names


def _file_map(package: str) -> Dict[str, List[Tuple[str, str]]]:
    """``分组 -> [(Java 路径, Python 路径)]``，来源是各 Python 文件的 ``# Migrated from:``."""

    grouped: Dict[str, List[Tuple[str, str]]] = collections.defaultdict(list)
    for path in sorted((ROOT / "app").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:2000]
        relative = path.relative_to(ROOT).as_posix()
        parts = relative.split("/")
        group = parts[2] if parts[1] == package and len(parts) > 3 else parts[1]
        for match in MIGRATED.finditer(head):
            java = match.group(1)
            if java.startswith("(no Java"):
                continue
            if package == "generator":
                if "com/ruoyi/generator" not in java:
                    continue
            elif f"/controller/{package}/" not in java and f"/{package}/" not in java:
                continue
            grouped[group].append((java, relative))
    return grouped


def _render(package: str, config: dict, items: List, log_by: Dict, python_names: Dict) -> str:
    marker = config["controller_dir"].replace("/", "\\")
    package_items = [
        item
        for item in items
        if marker in str(java_file_of.get(item.controller, ""))
    ]
    java_dir = PROJECT_ROOT / config["controller_dir"]
    java_files = sorted(java_dir.rglob("*.java")) if java_dir.exists() else []
    controllers = collections.Counter(item.controller for item in package_items)
    grouped = _file_map(package)
    test_total = sum(row[2] for row in config["tests"])

    lines: List[str] = []
    lines.append(f"# MAPPING_{package.upper()}.md — {config['title']} Java ↔ Python 对照表")
    lines.append("")
    lines.append(READING)
    lines.append("---")
    lines.append("")
    lines.append("## 1. 切片概况")
    lines.append("")
    lines.append("| 项 | 数 | 依据 |")
    lines.append("|---|---|---|")
    lines.append(f"| Java 控制器 | {len(java_files)} | `{config['controller_dir']}/` 下全部 `*Controller.java` |")
    lines.append(
        f"| 端点 | {len(package_items)} | 方法级注解展开后的条数（`value = {{...}}` 会展开成多条），"
        "与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |"
    )
    api_files = [python for _, python in grouped.get("api", [])]
    api_dir = str(Path(api_files[0]).parent.as_posix()) if api_files else f"app/api/{package}"
    lines.append(f"| Python 控制器模块 | {len(api_files)} | `{api_dir}/` |")
    for group in ("domain", "mapper", "service", "util", "sharding"):
        if grouped.get(group):
            lines.append(
                f"| {group.capitalize()} 对照行 | {len(grouped[group])} | 按 `# Migrated from:` 反查到的"
                " Java 文件行数（Mapper 的接口与 XML 分别计） |"
            )
    lines.append(f"| 测试 | {test_total} | 见 §5 |")
    lines.append("")
    lines.append("## 2. 要点")
    lines.append("")
    for index, note in enumerate(config["notes"], start=1):
        lines.append(f"{index}. {note}")
    lines.append("")
    lines.append("## 3. 文件级对照")
    lines.append("")
    order = ["api", "domain", "mapper", "service", "util", "sharding"]
    others = [group for group in sorted(grouped) if group not in order]
    for index, group in enumerate([group for group in order if grouped.get(group)] + others, start=1):
        rows = grouped[group]
        lines.append(f"### 3.{index} {group}（{len(rows)} 行）")
        lines.append("")
        lines.append("| Java | Python |")
        lines.append("|---|---|")
        for java, python in rows:
            lines.append(f"| `{java}` | `{python}` |")
        lines.append("")

    lines.append(f"## 4. 控制器端点（{len(package_items)} 个）")
    lines.append("")
    for index, controller in enumerate(sorted(controllers), start=1):
        rows = [item for item in package_items if item.controller == controller]
        lines.append(f"### 4.{index} `{controller}`（{len(rows)} 个映射）")
        lines.append("")
        lines.append("| Java | Python | Method / Path | 权限点 | `@Log` |")
        lines.append("|---|---|---|---|---|")
        for item in sorted(rows, key=lambda row: (row.method, row.path)):
            python_name = python_names.get((item.method, base.normalize_path(item.path)), "—")
            permission = item.permission or "—"
            title, business = log_by.get((item.controller, item.java_method), ("", ""))
            log = " / ".join(part for part in (title, business) if part) or "—"
            lines.append(
                f"| `{item.java_method}` | `{python_name}` | {item.method} `{item.path}`"
                f" | `{permission}` | {log} |"
            )
        lines.append("")

    lines.append("## 5. 测试")
    lines.append("")
    lines.append("| 层 | Python 测试文件 | 用例数 | 覆盖点 |")
    lines.append("|---|---|---|---|")
    for layer, name, count, focus in config["tests"]:
        lines.append(f"| {layer} | {name} | **{count}** | {focus} |")
    lines.append(f"| 合计 | — | **{test_total}** | — |")
    lines.append("")
    lines.append(
        f"用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条"
        "（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。"
    )
    lines.append("")
    return "\n".join(lines)


java_items, log_by, java_file_of = _collect_java()
python_names = _collect_python_names()
for name in PACKAGES:
    target = ROOT / f"MAPPING_{name.upper()}.md"
    target.write_text(_render(name, PACKAGES[name], java_items, log_by, python_names), encoding="utf-8")
    print(f"written {target.name}")
