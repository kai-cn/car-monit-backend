#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对拍 “C++ spec 的 SELECT 列清单” 与 “Java Mapper XML 里 selectXxxVo 的列清单”。

为什么单独一个脚本：MyBatis 只填结果集里出现的列，Vo 没写的属性在 Java 响应里是
null（或字段初始值）；而 C++ 的 Spec::selectColumns() 会把所有带 column 的字段都投影出来，
于是同一份 spec 既用于 WHERE 又用于 SELECT，多投影的列会变成“Java 是 null，C++ 是真值”。
本脚本逐实体列出差异，只报能确定的（Vo 是显式列清单、不含 * 与 include）。

用法：python scripts/audit_projection.py [--csv]
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA = os.path.dirname(ROOT)
SPECS = os.path.join(ROOT, "src", "cm", "web", "specs")

VO_RE = re.compile(r'<sql\s+id="(select\w*Vo|\w*Vo)">\s*(.*?)\s*</sql>', re.S)
# 列名大小写不敏感（XML 里既有 t.id 也有 t.ID / t.BILL_OID），统一按小写比较
COL_RE = re.compile(r'\b(\w+)\.([A-Za-z_][A-Za-z0-9_]*)')
FIELD_RE = re.compile(r'\n\s*\{"(\w+)",\s*(?:"(\w+)"|nullptr),')


def spec_fields(body):
    """解析 spec 的字段初始化列表，返回 [(json, column, inVo)]。

    ⚠️ 必须解析第 12 个参数 inVo：Spec::selectColumns() 会跳过 inVo=false 的列
    （Java 的 <sql id="selectXxxVo"> 没投影它，但它仍可作 WHERE 左值）。
    只看前两个字段会把这类"只作条件、不投影"的列误报成多投影。
    """
    out = []
    for m in FIELD_RE.finditer(body):
        json_name = m.group(1)
        column = m.group(2) if m.group(2) else None
        # 从 '{' 开始扫到配对的 '}'，再按深度 0 的逗号切分
        start = m.start() + m.group(0).index('{')
        depth = 0
        end = None
        for i in range(start, len(body)):
            ch = body[i]
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        args = []
        if end is not None:
            cur, d = '', 0
            for ch in body[start + 1:end]:
                if ch in '([{':
                    d += 1
                elif ch in ')]}':
                    d -= 1
                if ch == ',' and d == 0:
                    args.append(cur.strip())
                    cur = ''
                else:
                    cur += ch
            args.append(cur.strip())
        # 参数位：0 json / 1 column / 2 fmt / 3 cond / 4 excel / 5 pk / 6 autoIncrement
        #         / 7 insertable / 8 updatable / 9 condColumn / 10 dflt / 11 inVo
        in_vo = True
        if len(args) >= 12 and args[11] == 'false':
            in_vo = False
        out.append((json_name, column, in_vo))
    return out


def java_xml_for(entity_pkg):
    """按实体类名找 mapper xml（com.ruoyi.<pkg>.domain.Foo -> mapper/<pkg>/FooMapper.xml）"""
    return entity_pkg


def read(p):
    try:
        with io.open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def spec_files():
    for name in sorted(os.listdir(SPECS)):
        if name.endswith("CrudSpecs.cpp"):
            yield os.path.join(SPECS, name), read(os.path.join(SPECS, name))


def parse_specs(text):
    """返回 [(spec函数名, table, [(json, column_or_None, inVo)])]"""
    out = []
    for m in re.finditer(r'const Spec&\s+(\w+)\(\)\s*\{(.*?)\n\}\n', text, re.S):
        body = m.group(2)
        tm = re.search(r's\.table\s*=\s*"([^"]+)"', body)
        if not tm:
            continue
        out.append((m.group(1), tm.group(1), spec_fields(body)))
    return out


def vo_columns(xml_src):
    """从 Vo 里抽列名；遇到 * 或 include 判定为不可比较，返回 None"""
    m = VO_RE.search(xml_src)
    if not m:
        return None
    seg = m.group(2)
    if "*" in seg or "<include" in seg or "<if" in seg or "<choose" in seg:
        return None
    cols = set()
    for _alias, col in COL_RE.findall(seg):
        cols.add(col.lower())
    # 兼容 "t.id," 之外的裸列名
    for tok in re.findall(r'^\s*([a-z_][a-z0-9_]*)\s*,?\s*$', seg, re.M):
        cols.add(tok.lower())
    return cols or None


def main():
    total_specs = 0
    comparable = 0
    diff_entities = []
    for path, text in spec_files():
        for fname, table, fields in parse_specs(text):
            total_specs += 1
            xml = os.path.join(JAVA, "ruoyi-system", "src", "main", "resources", "mapper")
            hits = []
            for dirpath, _dirnames, filenames in os.walk(xml):
                for fn in filenames:
                    if fn.endswith("Mapper.xml"):
                        src = read(os.path.join(dirpath, fn))
                        if re.search(r'\bfrom\s+%s\s+t\b' % table, src, re.I):
                            hits.append((fn, src))
            if not hits:
                continue
            # 同一个表可能被别的 Mapper（join 查询）也引用，优先用与实体同名的 XML，
            # 否则会拿 CarConfimFreeMapper 的 Vo 去比 car_info，报出一屏假差异
            cls = fname[4:] if fname.startswith("spec") else fname
            hits.sort(key=lambda h: 0 if h[0] == cls + "Mapper.xml" else 1)
            cols = None
            src_used = None
            for fn, src in hits:
                c = vo_columns(src)
                if c:
                    cols, src_used = c, fn
                    break
            if cols is None:
                continue
            comparable += 1
            # 只比对真正会被 SELECT 出来的列（inVo=true）；inVo=false 的列只作 WHERE 左值
            projected = {c.lower() for _j, c, in_vo in fields if c and in_vo}
            extra = sorted(projected - cols)
            if extra:
                diff_entities.append((fname, table, src_used, extra))

    print("spec 总数=%d  可与 Vo 对拍=%d  存在多投影=%d" % (total_specs, comparable, len(diff_entities)))
    for fname, table, src_used, extra in diff_entities:
        print("\n%s  (%s, 依据 %s)  多投影 %d 列:" % (fname, table, src_used, len(extra)))
        print("   " + ", ".join(extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
