#!/usr/bin/env python3
# 从 Java 控制器的 @Log 注解生成 C++ 侧的操作日志规则表。
#
# 对应 Java: com.ruoyi.framework.aspectj.LogAspect
#   operLog.setMethod(targetClass.getName() + "." + methodName + "()")
#   businessType / operatorType 存的是枚举 ordinal（不是名字）
#   isSaveRequestData / isSaveResponseData / excludeParamNames 决定记不记参数、排除哪些键
#
# 生成物：car-monit-cpp/src/cm/web/specs/OperLogTable.cpp
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CPP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(CPP_DIR)

JAVA_CTRL_ROOTS = [
    "ruoyi-admin/src/main/java/com/ruoyi/web/controller",
    "ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller",
    "ruoyi-generator/src/main/java/com/ruoyi/generator/controller",
]

VERB_MAP = {"Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE", "Patch": "PATCH"}
# 注解顺序在方法签名之前并不固定（SysFileController 是 @PostMapping 写在 @Log 之上），
# 因此按"方法签名 + 其上方连续的注解块"解析，而不是从 mapping 行往上找 @Log。
MAP_ANY_RE = re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\b(?:\(([^)]*)\))?')
CLASS_RM_RE = re.compile(r'@RequestMapping\("([^"]*)"\)')
METHOD_SIG_RE = re.compile(r'^(public|private|protected)\s+(?!class\b|interface\b|enum\b)[\w$<>\[\],.\s]+?\s+([\w$]+)\s*\(')
PACKAGE_RE = re.compile(r'^\s*package\s+([\w.]+)\s*;', re.M)
LOG_RE = re.compile(r'@Log\(([^)]*)\)')
BUSINESS_TYPES = ["OTHER", "INSERT", "UPDATE", "DELETE", "GRANT",
                  "EXPORT", "IMPORT", "FORCE", "GENCODE", "CLEAN"]
OPERATOR_TYPES = ["OTHER", "MANAGE", "MOBILE"]


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def normalize(path):
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/+", "/", p)
    return p


def join_path(base, sub):
    return normalize(base + "/" + sub.lstrip("/")) if sub else normalize(base)


def parse_log(attrs):
    """@Log 的属性 -> dict（缺省值照抄 ruoyi-common/.../annotation/Log.java）"""
    out = {"title": "", "businessType": 0, "operatorType": OPERATOR_TYPES.index("MANAGE"),
           "saveRequest": True, "saveResponse": True, "exclude": []}
    t = re.search(r'title\s*=\s*"([^"]*)"', attrs)
    if t:
        out["title"] = t.group(1)
    b = re.search(r'businessType\s*=\s*BusinessType\.(\w+)', attrs)
    if b and b.group(1) in BUSINESS_TYPES:
        out["businessType"] = BUSINESS_TYPES.index(b.group(1))
    o = re.search(r'operatorType\s*=\s*OperatorType\.(\w+)', attrs)
    if o and o.group(1) in OPERATOR_TYPES:
        out["operatorType"] = OPERATOR_TYPES.index(o.group(1))
    sr = re.search(r'isSaveRequestData\s*=\s*(\w+)', attrs)
    if sr:
        out["saveRequest"] = sr.group(1) == "true"
    sp = re.search(r'isSaveResponseData\s*=\s*(\w+)', attrs)
    if sp:
        out["saveResponse"] = sp.group(1) == "true"
    ex = re.search(r'excludeParamNames\s*=\s*(\{[^}]*\}|"[^"]*")', attrs)
    if ex:
        out["exclude"] = re.findall(r'"([^"]*)"', ex.group(1))
    return out


def is_noise(text):
    t = text.strip()
    return t == "" or t.startswith("//") or t.startswith("*") or t.startswith("/*") or t == "*/"


def annotation_block(lines, idx):
    """收集方法签名 idx 上方连续的注解行（跳过注释/空行），返回拼接后的注解文本"""
    parts = []
    j = idx - 1
    while j >= 0:
        t = lines[j].strip()
        if t.startswith("@"):
            parts.append(t)
            j -= 1
            continue
        if is_noise(lines[j]):
            j -= 1
            continue
        break
    parts.reverse()
    return " ".join(parts)


def mapping_targets(annotations):
    """返回 [(verb, path), ...]；一个 mapping 可以声明多个路径（@GetMapping({"/", "/{id}"})）"""
    out = []
    for m in MAP_ANY_RE.finditer(annotations):
        verb = VERB_MAP.get(m.group(1))
        body = m.group(2) or ""
        paths = re.findall(r'"([^"]*)"', body) or [""]
        for p in paths:
            out.append((verb, p))
    return out


def java_log_rules():
    rules = []
    for rel in JAVA_CTRL_ROOTS:
        root = os.path.join(REPO, rel)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, fns in os.walk(root):
            for fn in sorted(fns):
                if not fn.endswith(".java"):
                    continue
                path = os.path.join(dirpath, fn)
                src = read(path)
                if "@Log(" not in src:
                    continue
                pkg = PACKAGE_RE.search(src)
                fqpkg = pkg.group(1) if pkg else ""
                cls = fn[:-len(".java")]
                fqcn = (fqpkg + "." + cls) if fqpkg else cls
                bm = CLASS_RM_RE.search(src)
                base = bm.group(1) if bm else ""
                lines = src.splitlines()
                for i, raw in enumerate(lines):
                    if raw.strip().startswith("//"):
                        continue
                    sig = METHOD_SIG_RE.match(raw.strip())
                    if not sig:
                        continue
                    name = sig.group(2)
                    if name == cls:  # 构造器
                        continue
                    ann = annotation_block(lines, i)
                    lm = LOG_RE.search(ann)
                    if not lm:
                        continue
                    log = parse_log(lm.group(1))
                    targets = mapping_targets(ann)
                    if not targets:
                        print("WARN %s.%s 有 @Log 但没有 @*Mapping" % (cls, name))
                        continue
                    for verb, sub in targets:
                        rules.append({
                            "http": verb,
                            "path": join_path(base, sub),
                            "title": log["title"],
                            "businessType": log["businessType"],
                            "operatorType": log["operatorType"],
                            "saveRequest": log["saveRequest"],
                            "saveResponse": log["saveResponse"],
                            "exclude": log["exclude"],
                            "classMethod": "%s.%s()" % (fqcn, name),
                        })
    # 同 (verb, path) 只保留一条，和 Spring 的映射唯一性一致
    uniq = {}
    for r in rules:
        uniq[(r["http"], r["path"])] = r
    return [uniq[k] for k in sorted(uniq)]


def cpp_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def render(rules):
    out = [
        "// 自动生成，请勿手改：scripts/gen_operlog_table.py",
        "// 来源：Java 各控制器的 @Log 注解（LogAspect 的切点即 @annotation(Log)）",
        '#include "cm/framework/aspect/OperLogAspect.hpp"',
        "",
        "namespace cm::aspect {",
        "",
        "const std::vector<LogRule>& logRules() {",
        "    static const std::vector<LogRule> rules = {",
    ]
    for r in rules:
        exc = ", ".join(cpp_str(x) for x in r["exclude"])
        out.append(
            "        {%s, %s, %s, %d, %d, %s, %s, {%s}, %s}," % (
                cpp_str(r["http"]), cpp_str(r["path"]), cpp_str(r["title"]),
                r["businessType"], r["operatorType"],
                "true" if r["saveRequest"] else "false",
                "true" if r["saveResponse"] else "false",
                exc, cpp_str(r["classMethod"])))
    out += [
        "    };",
        "    return rules;",
        "}",
        "",
        "} // namespace cm::aspect",
        "",
    ]
    return "\r\n".join(out)


def main():
    rules = java_log_rules()
    dst = os.path.join(CPP_DIR, "src", "cm", "web", "specs", "OperLogTable.cpp")
    io.open(dst, "w", encoding="utf-8", newline="").write(render(rules))
    by_type = {}
    for r in rules:
        by_type[BUSINESS_TYPES[r["businessType"]]] = by_type.get(BUSINESS_TYPES[r["businessType"]], 0) + 1
        if r["title"] == "":
            print("WARN 空 title: %s %s (%s)" % (r["http"], r["path"], r["classMethod"]))
    sys.stdout.buffer.write(("生成 %d 条 @Log 规则 -> %s\n" % (len(rules), dst)).encode("utf-8"))
    sys.stdout.buffer.write(("按 businessType: %s\n" % sorted(by_type.items())).encode("utf-8"))


if __name__ == "__main__":
    main()
