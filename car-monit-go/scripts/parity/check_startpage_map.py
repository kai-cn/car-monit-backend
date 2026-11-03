# -*- coding: utf-8 -*-
"""startPage 覆盖静态核对。

数据比对看不出一类差异：Java 控制器调了 startPage()，Go 端却用 web.Page(c)
（只在请求带分页参数时才 LIMIT）。如果那张表恰好是空的，两端都返回 0 行，
逐字段对比永远「一致」——flow/* 就是这么漏过去的。

做法：
  1. Java：每个 @*Mapping 方法 → 路由、是否返回 TableDataInfo、方法体里有没有 startPage(；
  2. Go：按函数体解析（含路由组前缀与跨函数的间接调用），得出每个路由处理函数用的是
     web.Page(c)（可选分页）还是 web.PageAlways(c)（无条件分页）；
  3. 交叉：Java 分页 / Go 不分页 = 少分页；Java 不分页 / Go 分页 = 加分页。

用法:
  MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python scripts/parity/check_startpage_map.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import (ANN_RE, CLASS_MAP_RE, MODULES, JAVA_ROOT, METHOD_ANN,  # noqa: E402
                    REQUEST_METHOD_RE, norm, paths_of, strip_comments)

GO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "internal", "modules")

# 方法 `func (h *noticeHandler) List(` 与自由函数 `func registerListGet(` 都要认：
# 只匹配带接收者的写法会把注册 helper 整个漏掉。
FUNC_RE = re.compile(r"^func (?:\((\w+ )?\*?(\w+)\) )?(\w+)\(")
CALL_RE = re.compile(r"\.\s*(\w+)\(")
# 注册行：HTTP 动词 + 第一个字符串字面量是路径，最后一个 `变量.方法` 是处理函数。
# 中间可能夹着 middleware.Perm("...") 这类带括号和引号的参数，所以不能用「不含右括号」的屏障。
VERB_RE = re.compile(r"\.(GET|POST|PUT|DELETE|PATCH|Any)\(")
HANDLER_RE = re.compile(r"(\w+)\.(\w+)")
GROUP_RE = re.compile(r"^\s*(\w+)\s*:?=\s*([\w.]+)\.Group\(\s*\"([^\"]+)\"")
PLAIN_RE = re.compile(r"^\s*(\w+)\s*:?=\s*([\w.]+)\s*$")
CTOR_RE = re.compile(r"^\s*(\w+)\s*:?=\s*new(\w+)\(|^\s*(\w+)\s*:?=\s*&(\w+)\{")
STRING_RE = re.compile(r"\"([^\"]*)\"")


def body_at(text, start):
    i = text.find("{", start)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return text[i:]


def scan_java():
    out = {}
    for module in MODULES:
        base = os.path.join(JAVA_ROOT, module, "src", "main", "java")
        if not os.path.isdir(base):
            continue
        for root, _, names in os.walk(base):
            for name in names:
                if not name.endswith(".java"):
                    continue
                raw = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
                if "@RestController" not in raw and "@Controller" not in raw:
                    continue
                text = strip_comments(raw)
                head = text.split("public class", 1)[0] if "public class" in text else text
                class_paths = [""]
                cm = CLASS_MAP_RE.search(head)
                if cm:
                    class_paths = paths_of(cm.group(1)) or [""]
                tail = text[len(head):]
                for m in ANN_RE.finditer(tail):
                    ann, args = m.group(1), (m.group(2) or "")[1:-1]
                    methods = REQUEST_METHOD_RE.findall(args) if ann == "RequestMapping" else None
                    methods = methods or ([METHOD_ANN[ann]] if ann != "RequestMapping"
                                          else ["GET", "POST", "PUT", "DELETE", "PATCH"])
                    body = body_at(tail, m.end())
                    table = "TableDataInfo" in tail[m.end():m.end() + 200]
                    paged = "startPage(" in body
                    for cp in class_paths:
                        for mp in paths_of(args) or [""]:
                            for verb in methods:
                                out[(verb, norm(cp + "/" + mp))] = (table, paged)
    return out


def split_top_level(s):
    """按顶层逗号切分参数列表（忽略括号与引号内的逗号）。"""
    parts, buf, depth, quote = [], [], 0, None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def param_names(sig):
    """`base, perm, title string, spec *X` → 位置化的参数名列表。"""
    names = []
    for part in split_top_level(sig):
        if not part:
            continue
        head = re.match(r"^(\w+(?:\s*,\s*\w+)*)\s+\S", part)
        if head:
            names.extend(n.strip() for n in head.group(1).split(","))
        else:
            m2 = re.match(r"^\w+$", part)
            if m2:
                names.append(part)
            else:  # `...string` / 匿名
                names.append("")
    return names


def scan_prefix_helpers():
    """找出「路径前缀是函数参数」的注册 helper，并收集各调用点传进来的前缀。

    形如 `auth.GET(base+"/list", ...)` 的注册，只有回到调用点才知道完整路径
    （manager/base 的 registerStandard 就是这么写的）。
    """
    helpers = {}   # (pkg, func) -> 参数下标
    for root, _, names in os.walk(GO_ROOT):
        for name in names:
            if not name.endswith(".go"):
                continue
            text = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
            for m in re.finditer(r"^func (\w+)\(([^)]*)\)\s*\{", text, re.M):
                idx = None
                body = body_at(text, m.end() - 1)
                gm = re.search(r"\.(?:GET|POST|PUT|DELETE|PATCH|Any)\(\s*(\w+)\s*\+", body)
                if gm:
                    ident = gm.group(1)
                    plist = param_names(m.group(2))
                    if ident in plist:
                        idx = plist.index(ident)
                if idx is None:
                    continue
                helpers[(root, m.group(1))] = idx
    values = {}
    if not helpers:
        return values
    for root, _, names in os.walk(GO_ROOT):
        for name in names:
            if not name.endswith(".go"):
                continue
            text = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
            for (pkg, fn), idx in helpers.items():
                if pkg != root:
                    continue
                for m in re.finditer(r"\b" + re.escape(fn) + r"\(", text):
                    buf, depth = [], 0
                    for ch in text[m.end():]:
                        if ch == "(":
                            depth += 1
                        elif ch == ")":
                            if depth == 0:
                                break
                            depth -= 1
                        buf.append(ch)
                    args = split_top_level("".join(buf))
                    if len(args) > idx:
                        lit = re.match(r'^"([^"]+)"', args[idx])
                        if lit:
                            values.setdefault((pkg, fn), []).append(norm(lit.group(1)))
    return values


PREFIX_HELPERS = scan_prefix_helpers()


def parse_go_files():
    """返回 (函数体表, 注册表, 包内同名方法索引)。

    函数按 **(包, 接收者类型, 方法名)** 分键：同包里 `func (h *noticeHandler) List` 与
    `func (h *fileHandler) List` 是不同方法，只按名字索引会互相顶掉。
    注册语句里的 `h.List` 需要靠同一个注册函数里的 `h := newNoticeHandler(...)` 才能定到类型。
    注册语句可能跨行（`g.POST("", middleware.Perm(...), h.Add)`），所以按括号配平拼成一条再解析。
    """
    helpers = PREFIX_HELPERS
    funcs, regs, by_name = {}, [], {}
    for root, _, names in os.walk(GO_ROOT):
        for name in names:
            if not name.endswith(".go") or name.endswith("_test.go"):
                continue
            pkg = root
            text = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
            cur, buf, groups, recvs = None, [], {}, {}
            file_groups, file_recvs = {}, {}
            pending = None

            def emit(verb, head, stmt, fn_key):
                paths = STRING_RE.findall(stmt)
                handlers = HANDLER_RE.findall(stmt)
                if not paths or not handlers:
                    return
                var, fn = handlers[-1]
                prefix = groups.get(head)
                if prefix is None:
                    prefix = file_groups.get(head, "")
                pfx2 = paths[0]
                # 路径写成 base+"/list" 时，回到调用点展开成每个真实前缀
                expanded = None
                joined = prefix + "/" + pfx2
                if fn_key in helpers and re.search(r"\w+\s*\+\s*\"" + re.escape(pfx2), stmt):
                    expanded = [v + pfx2 for v in helpers[fn_key]]
                targets = [norm(p) for p in (expanded or [joined])]
                for target in targets:
                    regs.append((verb, target, pkg,
                                 recvs.get(var) or file_recvs.get(var, ""), fn))

            for ln in text.split("\n"):
                if cur:
                    buf.append(ln)
                if pending is not None:
                    verb, head, stmt, depth = pending
                    stmt += " " + ln.strip()
                    depth += ln.count("(") - ln.count(")")
                    if depth <= 0:
                        emit(verb, head, stmt, (root, cur[2] if cur else ""))
                        pending = None
                    continue
                fm = FUNC_RE.match(ln)
                if fm:
                    if cur:
                        funcs[cur] = "\n".join(buf)
                    cur = (pkg, fm.group(2) or "", fm.group(3))
                    by_name.setdefault((pkg, fm.group(3)), []).append(cur)
                    buf, groups, recvs = [ln], {}, {}
                    continue
                gm = GROUP_RE.match(ln)
                if gm:
                    groups[gm.group(1)] = norm(gm.group(3))
                    file_groups[gm.group(1)] = norm(gm.group(3))
                    continue
                pm = PLAIN_RE.match(ln)
                if pm and "." in pm.group(2):
                    groups.setdefault(pm.group(1), "")
                    file_groups.setdefault(pm.group(1), "")
                    continue
                cm = CTOR_RE.match(ln)
                if cm:
                    ty = (cm.group(2) or cm.group(4))
                    ty = ty[0].lower() + ty[1:]
                    recvs[cm.group(1) or cm.group(3)] = ty
                    file_recvs[cm.group(1) or cm.group(3)] = ty
                    continue
                vm = VERB_RE.search(ln)
                if vm and '"' in ln:
                    stmt = ln[vm.start():]
                    depth = stmt.count("(") - stmt.count(")")
                    if depth <= 0:
                        emit(vm.group(1).upper(), ln.split(".")[0].strip(), stmt, (root, cur[2] if cur else ""))
                    else:
                        pending = (vm.group(1).upper(), ln.split(".")[0].strip(), stmt, depth)
            if cur:
                funcs[cur] = "\n".join(buf)
    return funcs, regs, by_name


def own_page(body):
    if "web.PageAlways(c)" in body:
        return "PageAlways"
    if re.search(r"web\.Page\(c\)", body):
        return "Page"
    return ""


def resolve_pages(funcs, by_name):
    pages = {key: own_page(body) for key, body in funcs.items()}
    for _ in range(4):  # 同包同类型内传递若干跳：handler → 私有 helper → executor
        changed = False
        for key, body in funcs.items():
            if pages[key]:
                continue
            pkg, _, _ = key
            for callee in CALL_RE.findall(body):
                cands = [c for c in by_name.get((pkg, callee), []) if c[1] == key[1]]
                for c in cands:
                    if pages.get(c):
                        pages[key] = pages[c]
                        changed = True
                        break
                if pages[key]:
                    break
        if not changed:
            break
    return {k: v for k, v in pages.items() if v}


def lookup(pages, by_name, pkg, recv, fn):
    """注册语句解析出的 (pkg, recv, fn) → 分页方式；返回 (page, 是否歧义)。"""
    if recv:
        key = (pkg, recv, fn)
        return pages.get(key, ""), False
    cands = [pages.get(k) for k in by_name.get((pkg, fn), [])]
    cands = [c for c in cands if c]
    if not cands:
        return "", False
    if len(set(cands)) > 1:
        return cands[0], True          # 同包同名但分页方式不一致：需要人工看
    return cands[0], False


def main():
    java = scan_java()
    funcs, regs, by_name = parse_go_files()
    pages = resolve_pages(funcs, by_name)
    seen, missing, extra, unknown, ambiguous, absent, nopage = set(), [], [], [], [], [], []
    for verb, path, pkg, recv, fn in regs:
        if (verb, path) in seen:
            continue
        seen.add((verb, path))
        jp = java.get((verb, path)) or java.get(("ANY", path))
        page, amb = lookup(pages, by_name, pkg, recv, fn)
        if amb:
            ambiguous.append((verb, path, fn))
        if jp is None:
            if page:
                unknown.append((verb, path, fn, page))
            continue
        table, paged = jp
        if not table:
            continue                     # 不返回 TableDataInfo 的方法与分页无关
        if not page:
            # 关键盲区：处理函数存在、但整条链路上没有任何分页构造。
            # 只有 Java 侧确实 startPage 时才是缺陷；像 gen/columnList 那样
            # 手工拼 TableDataInfo（total=list.size()）的端点本来就不该分页。
            if paged:
                absent.append((verb, path, fn))
        elif paged and page == "Page":
            missing.append((verb, path, fn))
        elif not paged and page == "PageAlways":
            extra.append((verb, path, fn))

    # Java 分页路由里，Go 侧压根没注册到的（由 routes.py 负责路由缺失，这里只提示数量）
    paged_java = {k for k, v in java.items() if v[0] and v[1]}
    unregistered = sorted(paged_java - seen)

    print("Java 路由 %d 条（其中返回 TableDataInfo 且 startPage 的 %d 条）；"
          "Go 分页处理函数 %d 个；Go 注册 %d 条"
          % (len(java), len(paged_java), len(pages), len(seen)))
    print("\n== Java 调 startPage，Go 用 web.Page(c)（空表时数据比对看不出来）: %d 条 ==" % len(missing))
    for verb, path, fn in missing:
        print("  %-6s %-46s %s" % (verb, path, fn))
    print("\n== Java 分页路由在 Go 里有注册但整条链路不分页（Go 直接返回全量）: %d 条 ==" % len(absent))
    for verb, path, fn in absent:
        print("  %-6s %-46s %s" % (verb, path, fn))
    print("\n== Java 没调 startPage，Go 却用 web.PageAlways(c): %d 条 ==" % len(extra))
    for verb, path, fn in extra:
        print("  %-6s %-46s %s" % (verb, path, fn))
    print("\n== 同包同名方法分页方式不一致（需人工确认）: %d 条 ==" % len(ambiguous))
    for verb, path, fn in ambiguous[:20]:
        print("  %-6s %-46s %s" % (verb, path, fn))
    print("\n== Java 侧找不到同名路由（Go 专有或路径写法差异）: %d 条 ==" % len(unknown))
    for verb, path, fn, page in unknown[:25]:
        print("  %-6s %-46s %s(%s)" % (verb, path, fn, page))
    print("\n== Java 分页但 Go 未注册该路由（路由缺失由 routes.py 判定）: %d 条 ==" % len(unregistered))
    for verb, path in unregistered[:25]:
        print("  %-6s %s" % (verb, path))
    return 1 if missing or extra or absent else 0


if __name__ == "__main__":
    sys.exit(main())
