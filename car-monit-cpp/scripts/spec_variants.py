# 识别 Java 控制器里“list 的复制粘贴变体”，供 gen_crud_spec.py 生成额外路由。
#
# 只自动识别两种确定形态（其余一律交回手写，不猜）：
#   Paged —— 方法体里有 startPage() 且用 getDataTable(list) 返回
#   Plain —— 方法体调用 select<Entity>List(...) 且用 AjaxResult.success(list) 返回、不分页
# 扫描用状态机数大括号，避免跨行正则。
import re

_MAP_RE = re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?"([^"]*)"')
_PERM_RE = re.compile(r"hasPermi\('([^']+)'")
_NAME_RE = re.compile(r'public\s+[\w<>.,\[\]\s]+\s+(\w+)\s*\(')

STANDARD = frozenset(["/list", "/export", "", "/clean", "/clearCache"])

# 出现这些关键字说明方法体里有额外业务逻辑，不能当成 list 的同构变体
# 注意 "try" 这种子串会命中 gantryService 之类的标识符，所以一律带上结构符号
_LOGIC_HINTS = ("if (", "if(", "for (", "for(", "while", "try {", "try{", "new ", 
                ".size()", ".isEmpty", ".get(0)", "== ", "!= ", "StringUtils", "CommonUtil")


def _annotation_block(src, pos):
    """从映射注解往上取连续的注解/注释行，遇到代码行即停"""
    lines = src[:pos].splitlines()
    collected = []
    for line in reversed(lines):
        t = line.strip()
        if t == "":
            continue
        if t.startswith("@") or t.startswith("*") or t.startswith("/*") or t.startswith("//"):
            collected.append(t)
            continue
        break
    return chr(10).join(reversed(collected))


def _braced_block(src, brace_pos):
    if brace_pos < 0:
        return ""
    depth = 0
    for k in range(brace_pos, len(src)):
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[brace_pos:k + 1]
    return ""


def method_bodies(src):
    out = []
    for m in _MAP_RE.finditer(src):
        verb, path = m.group(1), m.group(2) or ""
        # 只往上收集紧邻的注解块，否则会读到上一个方法的 @PreAuthorize
        head = _annotation_block(src, m.start())
        tail = src[m.end():m.end() + 500]
        # 权限只从紧邻的注解块取：Java 里 @PreAuthorize 写在 @GetMapping 上方，
        # 往 tail 找会读到下一个控制器的注解（比如 export 的权限）
        pm = _PERM_RE.search(head)
        nm = _NAME_RE.search(tail)
        body = _braced_block(src, src.find("{", m.end()))
        out.append({"verb": verb, "path": path, "name": nm.group(1) if nm else "",
                    "perm": pm.group(1) if pm else "", "body": body})
    return out


def classify_variants(bodies, entity):
    res = []
    for b in bodies:
        path = b["path"]
        if b["verb"] != "Get" or path in STANDARD or path.startswith("{"):
            continue
        body = b["body"]
        if not body:
            continue
        if any(h in body for h in _LOGIC_HINTS):
            continue  # 有额外逻辑：交回手写，不做同构注册
        if "startPage()" in body and "getDataTable(" in body:
            res.append((path, "ListKind::Paged", b["perm"]))
            continue
        if ("startPage()" not in body
                and body.count("return ") == 1
                and ("select" + entity + "List") in body
                and re.search(r'AjaxResult\s*\.\s*success\s*\(\s*(list|\w*List)\s*\)', body)):
            res.append((path, "ListKind::Plain", b["perm"]))
    return res
