#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对拍 Mapper XML 里每个 <if> 的“条件左值列”与“属性自身列”。

RuoYi 生成器写出的 XML 通常是 `and t.<列> = #{<属性>}`，两者一一对应，
所以 C++ 的 spec 一直拿属性自己的列当条件左值。但业务代码里改过条件的那些
（car_suspicious 的 sectionCode/sectionName 实际查的是 track_names，
 car_except_record 的 exceptIds 实际是 find_in_set(t.id, …)）如果没记录成 condColumn，
C++ 就会拼出一条“语义不同”的 WHERE —— 传了过滤参数却按另一列过滤。

用法：python scripts/audit_cond_columns.py
"""
import io
import os
import re
import sys

JAVA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAPPER_ROOTS = [
    os.path.join(JAVA, "ruoyi-system", "src", "main", "resources", "mapper"),
    os.path.join(JAVA, "ruoyi-quartz", "src", "main", "resources"),
    os.path.join(JAVA, "ruoyi-generator", "src", "main", "resources"),
]
SPEC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "src", "cm", "web", "specs")


def read(p):
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def snake(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and not name[i - 1].isupper():
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def spec_columns(entity):
    """从生成的 spec 里取 property -> (column, condColumn)"""
    for fn in sorted(os.listdir(SPEC_DIR)):
        text = read(os.path.join(SPEC_DIR, fn))
        m = re.search(r'const Spec&\s+spec%s\(\)\s*\{(.*?)\n\}\n' % re.escape(entity), text, re.S)
        if not m:
            continue
        out = {}
        for row in re.findall(r'\{"(\w+)",\s*(?:"(\w+)"|nullptr),(.*?)\},', m.group(1)):
            rest = row[2]
            cols = re.findall(r'"(\w+)"', rest)
            out[row[0]] = (row[1], cols[0] if cols else None)
        return out
    return None


def main():
    bad = []
    for root in MAPPER_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for f in sorted(files):
                if not f.endswith("Mapper.xml"):
                    continue
                entity = f[:-len("Mapper.xml")]
                src = read(os.path.join(dirpath, f))
                props = {m.group(1): m.group(2) for m in
                         re.finditer(r'<result\s+property="(\w+)"\s+column="(\w+)"', src)}
                stmts = re.findall(r'<select\b[^>]*id="(select\w*(?:List|Vo)?)"[^>]*>(.*?)</select>',
                                   src, re.S)
                spec = spec_columns(entity)
                seen = set()
                for sid, body in stmts:
                    for expr, inner in re.findall(r'<if\s+test="(.*?)">(.*?)</if>', body, re.S):
                        used = re.findall(r'#\{(\w+)', inner)
                        test_props = re.findall(r'\b(\w+)\s*!=', expr)
                        prop = (used or test_props or [None])[0]
                        if not prop or len(used) != 1:
                            continue
                        left = re.search(r'(?:(\w+)\.)?([a-z_][a-z0-9_]*)\s*(?:=|like|!=|>|<|in\b)',
                                         inner.strip())
                        if not left:
                            continue
                        col = left.group(2)
                        own = props.get(prop) or snake(prop)
                        if col.lower() == own.lower():
                            continue
                        key = (entity, prop, col)
                        if key in seen:
                            continue
                        seen.add(key)
                        declared = None
                        if spec and prop in spec:
                            declared = spec[prop][1] or spec[prop][0]
                        bad.append((entity, sid, prop, own, col, declared))
    print("条件左值列 != 属性自身列：%d 处" % len(bad))
    for e, sid, prop, own, col, decl in bad:
        flag = "OK " if (decl and decl.lower() == col.lower()) else "!! "
        print("%s%s.%s  属性列=%-18s 条件列=%-18s spec condColumn=%s"
              % (flag, e, prop, own, col, decl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
