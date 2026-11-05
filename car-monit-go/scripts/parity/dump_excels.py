# -*- coding: utf-8 -*-
"""Java @Excel 注解真值打印（ExcelUtil 型导出的列定义）。

RuoYi 的 ExcelUtil 按「父类字段 + 本类字段的声明顺序」收集带 @Excel 的字段，
再按 sort() 稳定排序，只保留 type()==ALL 或 ==当前导出类型 的列。
渲染优先级（ExcelUtil.java:1076-1108）：
    dateFormat -> readConverterExp -> dictType -> BigDecimal(scale) -> handler -> 原值
其中 convertByExp / convertDictByExp **未命中返回空串**（不是原值）。

用法:
  python scripts/parity/dump_excels.py SysUser CarTollInfo ...      # 按类名
  python scripts/parity/dump_excels.py --file <绝对路径> [--type EXPORT|IMPORT|ALL]
"""
import os
import re
import sys

JAVA_ROOT = os.environ.get("PARITY_JAVA_ROOT", r"D:\work\IdeaProjects\car-monit-backend-new")
ANN_RE = re.compile(r"@Excel\s*\(([^;]*?)\)\s*(?:private|public|protected)?\s*[\w<>\[\], .?]+\s+(\w+)\s*[;=]",
                    re.S)
FIELD_RE = re.compile(r"(?:private|public|protected)\s+([\w<>\[\], .?]+)\s+(\w+)\s*[;=]")
ATTR_RE = re.compile(r'(\w+)\s*=\s*(".*?"|[\w.{}\[\]=,:\u4e00-\u9fff+*-]+)')


def find_java(name):
    for root, _, names in os.walk(os.path.join(JAVA_ROOT, "ruoyi-system", "src", "main", "java")):
        if name + ".java" in names:
            return os.path.join(root, name + ".java")
    for root, _, names in os.walk(os.path.join(JAVA_ROOT, "ruoyi-common", "src", "main", "java")):
        if name + ".java" in names:
            return os.path.join(root, name + ".java")
    return ""


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", l) for l in text.split("\n"))


def parse(path):
    """返回 [(java字段, 类型, {注解属性})]，顺序 = 父类字段 + 本类字段的声明顺序。"""
    text = strip_comments(open(path, encoding="utf-8", errors="ignore").read())
    out = []
    for m in re.finditer(r"@Excel\s*\(", text):
        # 取括号内的属性串
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        args = text[m.end():i]
        after = text[i + 1:i + 400]
        fm = FIELD_RE.search(after)
        if not fm:
            continue
        attrs = {}
        for k, v in ATTR_RE.findall(args):
            attrs[k] = v.strip()
        if not attrs and args.strip():
            attrs["name"] = args.strip()
        out.append((fm.group(2), fm.group(1), attrs))
    return out


def keep(attrs, want):
    if want == "ALL":
        return True
    t = attrs.get("type", "ALL")
    if t in ("Type.ALL", "ALL"):
        return True
    return t.endswith(want)


def sort_key(attrs):
    try:
        return int(attrs.get("sort", "0"))
    except ValueError:
        return 0


def show(cls, path, want):
    fields = parse(path)
    fields = [f for f in fields if keep(f[2], want)]
    fields = sorted(fields, key=lambda f: sort_key(f[2]))  # 稳定排序 = 声明顺序兜底
    print("== %s  %s  (@Excel 列 %d)" % (cls, path.replace(JAVA_ROOT, "..."), len(fields)))
    for i, (name, ftype, attrs) in enumerate(fields, 1):
        bits = []
        for k in ("name", "type", "dateFormat", "dictType", "readConverterExp", "separator",
                  "cellType", "scale", "handler", "isExport", "needMerge", "combo", "width"):
            if k in attrs:
                bits.append("%s=%s" % (k, attrs[k]))
        print("  %2d %-18s %-14s %s" % (i, name, ftype, " ".join(bits)))


def main():
    want = "EXPORT"
    args = []  # noqa
    tokens = sys.argv[1:]
    i = 0
    while i < len(tokens):
        a = tokens[i]
        if a == "--type":
            want = tokens[i + 1].upper()
            i += 2
            continue
        if a == "--file":
            args.append(("__file__", tokens[i + 1]))
            i += 2
            continue
        args.append((a, ""))
        i += 1
    for cls, path in args:
        if cls == "__file__":
            show(os.path.basename(path)[:-5], path, want)
            continue
        p = find_java(cls)
        if not p:
            print("== %s  未找到 java 文件" % cls)
            continue
        show(cls, p, want)


if __name__ == "__main__":
    main()
