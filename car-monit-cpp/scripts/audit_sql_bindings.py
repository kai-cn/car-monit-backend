#!/usr/bin/env python3
# 审计 SQL 值路径是否已经全部改成参数绑定。
#
# 判定规则：
#   * Db::lit("...") / Db::lit(123) / Db::lit(true) / Db::lit(nullptr)
#       -> 字面量白名单（常量，不来自请求；保留内联）
#   * 任何带变量/函数调用/拼接的 Db::lit(...)
#       -> 违规：原文应使用 cm::db::bind(...) / bindIn(...) / bindNull()
#   * Db::inList(...) 已迁移为 cm::db::bindIn(...)；仍有残留则报违规
#
# 用法： python scripts/audit_sql_bindings.py [--root car-monit-cpp]
# 退出码：0 = 无违规；1 = 有违规（列出文件:行号:参数）。
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {
    ROOT / "src/cm/framework/db/Db.cpp",
    ROOT / "include/cm/framework/db/Db.hpp",
    ROOT / "src/cm/framework/db/Param.cpp",
    ROOT / "include/cm/framework/db/Param.hpp",
}
LITERAL_STRING = re.compile(r'^"(?:[^"\\]|\\.)*"$')
LITERAL_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")
LITERAL_WORDS = {"true", "false", "nullptr"}


def is_literal(arg: str) -> bool:
    s = arg.strip()
    if not s:
        return True
    if LITERAL_STRING.match(s) or LITERAL_NUMBER.match(s) or s in LITERAL_WORDS:
        return True
    # 多个字符串字面量拼接（"a" "b"）
    if re.match(r'^"(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*$', s):
        return True
    return False


def find_close(text: str, open_idx: int) -> int:
    depth = 0
    i = open_idx
    in_str = False
    quote = ""
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                in_str = False
            i += 1
            continue
        if c in ('"', "'"):
            in_str = True
            quote = c
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def main() -> int:
    violations = []
    whitelist = 0
    files = list(ROOT.glob("src/**/*.cpp")) + list(ROOT.glob("src/**/*.hpp")) + \
            list(ROOT.glob("include/**/*.hpp")) + list(ROOT.glob("include/**/*.h"))
    for path in files:
        if path in SKIP:
            continue
        text = path.read_text(encoding="utf-8")
        # 跳过明显的注释行（单行 // 与块注释内的 * 行）；注释里的示例不算违规
        for m in re.finditer(r"(?:cm::db::Db|Db)::lit\(", text):
            close = find_close(text, m.end() - 1)
            if close < 0:
                continue
            ln = line_of(text, m.start())
            line_start = text.rfind("\n", 0, m.start()) + 1
            prefix = text[line_start:m.start()].lstrip()
            if prefix.startswith("//") or prefix.startswith("*"):
                continue
            arg = text[m.end():close]
            if is_literal(arg):
                whitelist += 1
            else:
                violations.append(f"{path.relative_to(ROOT)}:{ln}: Db::lit({arg.strip()})")
        # inList 残留
        for m in re.finditer(r"(?:cm::db::Db|Db)::inList\(", text):
            ln = line_of(text, m.start())
            line_start = text.rfind("\n", 0, m.start()) + 1
            prefix = text[line_start:m.start()].lstrip()
            if prefix.startswith("//") or prefix.startswith("*"):
                continue
            violations.append(f"{path.relative_to(ROOT)}:{ln}: Db::inList(...) 应改为 cm::db::bindIn(...)")

    print(f"literal-only Db::lit whitelist: {whitelist}")
    if violations:
        print(f"violations: {len(violations)}")
        for v in violations:
            print("  " + v)
        return 1
    print("violations: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
