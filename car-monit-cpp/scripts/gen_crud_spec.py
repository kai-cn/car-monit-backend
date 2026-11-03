#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Java 源码 + MyBatis XML 抽取 RuoYi 同构 CRUD 元信息，生成 C++ 侧的 Spec 表。

用法:
    python scripts/gen_crud_spec.py --area base            # 生成 src/cm/web/specs/BaseCrudSpecs.cpp
    python scripts/gen_crud_spec.py --list                 # 列出可生成的控制器

为什么需要它：这些控制器的字段/条件/权限在 Java 侧是确定的、可读的，
手写 C++ 只会把抄错的风险放大。脚本把“抽取”变成可重跑的机械过程，
生成产物再人工复核个例（非 CRUD 的接口仍由手写控制器负责）。
"""
import argparse
import io
import os
import re
import sys

# Java 仓库根：本脚本在 <repo>/car-monit-cpp/scripts/ 下，向上两级即 Java 工程根
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_variants  # noqa: E402  list 变体识别
from db_cols import real_columns  # noqa: E402  生成前核对真实列

REPO = os.environ.get("CM_JAVA_ROOT") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JAVA_ROOT = os.path.join(REPO, "ruoyi-admin/src/main/java/com/ruoyi/web/controller")
DOMAIN_ROOTS = [
    os.path.join(REPO, "ruoyi-system/src/main/java/com/ruoyi"),
    os.path.join(REPO, "ruoyi-common/src/main/java/com/ruoyi"),
    os.path.join(REPO, "ruoyi-quartz/src/main/java/com/ruoyi"),
    os.path.join(REPO, "ruoyi-generator/src/main/java/com/ruoyi"),
]
MAPPER_ROOT = os.path.join(REPO, "ruoyi-system/src/main/resources/mapper")
QUARTZ_MAPPER_ROOT = os.path.join(REPO, "ruoyi-quartz/src/main/resources/mapper")

AREAS = {
    "base": ("base", "Base"),
    "system": ("system", "System"),
    "quartz": ("quartz", "Quartz"),
    "manager": ("manager", "Manager"),
    "flow": ("flow", "Flow"),
}

TYPE_MAP = {
    "String": "Str",
    "Long": "Long",
    "long": "Long",
    "Integer": "Int",
    "int": "Int",
    "Double": "Double",
    "double": "Double",
    "Float": "Double",
    "BigDecimal": "Double",
    "Boolean": "Bool",
    "boolean": "Bool",
    "Date": "DateIso",
    "LocalDateTime": "DateYmdHms",
    "LocalDate": "DateYmd",
}

# C++ 侧 Fmt 枚举的全部取值，用来校验父类字段表里的类型名
FMT_NAMES = {"Str", "Int", "Long", "Double", "Bool",
             "DateYmd", "DateYmdHms", "DateIso", "DateTimeIso"}

# Jackson 序列化 POJO 时先输出父类字段、再输出子类字段，且不过滤 null。
# RuoYi 的两个父类字段多、多数还不是本表的列（MyBatis 填不到就保持 null → JSON 里输出 null），
# 但键一个都不能少，否则 C++ 的 rows 少一整排键。
#   column=None：只进 JSON、不进 SELECT。
#   真正是否 SELECT，由 resultMap 有没有映射这个 property 决定（见 gen_entity）。
BASE_FIELDS = {
    "BaseEntity": [
        ("createBy", "create_by", "Str"),
        ("createTime", "create_time", "DateYmdHms"),
        ("updateBy", "update_by", "Str"),
        ("updateTime", "update_time", "DateYmdHms"),
        ("remark", "remark", "Str"),
        # searchValue 是 @JsonIgnore；params 的 getter 懒加载空 Map 且 @JsonInclude(NON_EMPTY)
        # ——两者在 Java 响应里都不出现，所以这里也不列
    ],
    "BaseUuidEntity": [
        ("id", "id", "Str"),
        ("epsId", "eps_id", "Long"),
        ("delFlag", "del_flag", "Str"),
        ("createBy", "create_by", "Long"),
        ("createTime", "create_time", "DateYmdHms"),
        ("updateBy", "update_by", "Long"),
        ("updateTime", "update_time", "DateYmdHms"),
        ("sort", "sort", "Int"),
        ("remark", "remark", "Str"),
        ("tenantId", "tenant_id", "Long"),
        ("deptSubCode", "dept_sub_code", "Str"),
        ("flag", "flag", "Str"),
        ("searchValue", "search_value", "Str"),
        ("params", None, "Map"),
    ],
}

# BasePlusEntity / …New / …Input / …InputNew / …Long 五个变体的字段与声明序完全相同
# （manager 域大量实体用它），统一成一份表，避免各写一遍再抄错。
_BASE_PLUS = [
    ("id", "id", "Str"),
    ("epsId", "eps_id", "Long"),
    ("delFlag", "del_flag", "Str"),
    ("createBy", "create_by", "Long"),
    ("createTime", "create_time", "DateYmdHms"),
    ("updateBy", "update_by", "Long"),
    ("updateTime", "update_time", "DateYmdHms"),
    ("sort", "sort", "Int"),
    ("tenantId", "tenant_id", "Long"),
]
for _name in ("BasePlusEntity", "BasePlusEntityNew", "BasePlusEntityInput",
              "BasePlusEntityInputNew", "BasePlusEntityLong"):
    BASE_FIELDS[_name] = _BASE_PLUS

# 这些父类的 id 就是主键（实体自己不再声明 @TableId）
_PK_ID_BASES = {"BaseUuidEntity"} | {n for n in (
    "BasePlusEntity", "BasePlusEntityNew", "BasePlusEntityInput",
    "BasePlusEntityInputNew", "BasePlusEntityLong")}


def rel(path):
    """把绝对路径缩写成相对 Java 仓库根的路径，便于在生成的 C++ 里对照源码"""
    if not path:
        return ""
    ap = os.path.abspath(path)
    root = os.path.abspath(REPO)
    if ap.startswith(root):
        ap = ap[len(root) + 1:]
    return ap.replace(chr(92), "/")


def read(path):
    if not os.path.exists(path):
        return ""
    return io.open(path, encoding="utf-8").read()


def camelize(snake):
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def find_domain_class(entity):
    for root in DOMAIN_ROOTS:
        for dirpath, _dirs, files in os.walk(root):
            if entity + ".java" in files:
                return os.path.join(dirpath, entity + ".java")
    return None


def find_mapper_xml(entity):
    # quartz / generator 的 XML 不在 ruoyi-system 下，必须一起找
    for root in (MAPPER_ROOT, QUARTZ_MAPPER_ROOT):
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if entity + "Mapper.xml" in files:
                return os.path.join(dirpath, entity + "Mapper.xml")
    return None


def xml_known_columns(xml_src):
    """XML 里出现过的列名集合。resultMap 没声明、selectVo 也没有的 Java 字段，
    说明它是派生属性（例如 uitEmpName / userId 这种 getter 拼出来的），
    不能当成数据库列去 SELECT。"""
    known = set()
    for m in re.finditer(r'column="([A-Za-z0-9_]+)"', xml_src):
        known.add(m.group(1).lower())
    vo = re.search(r'<sql id="select[^"]*">(.*?)</sql>', xml_src, re.S)
    pool = (vo.group(1) if vo else '') + xml_src
    for m in re.finditer(r'(?:t\.|as\s+)([a-z_][a-z0-9_]*)', pool):
        known.add(m.group(1).lower())
    for m in re.finditer(r'^\s*`?([a-z_][a-z0-9_]*)`?\s*,?\s*$', pool, re.M):
        known.add(m.group(1).lower())
    return known


def snake_case(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and not name[i - 1].isupper():
            out.append('_')
        out.append(ch.lower())
    return ''.join(out)

def parse_domain(entity):
    """返回 (table, pk_field, pk_is_auto, [(java_name, java_type, jsonfmt, excel_name)])"""
    path = find_domain_class(entity)
    if path is None:
        return None
    src = read(path)
    if not src:
        return None
    m = re.search(r'@TableName\("([^"]+)"\)', src)
    table = m.group(1) if m else None
    # 没有 @TableName 时（多数 flow_* 实体走 BaseUuidEntity），表名以 Mapper XML 的
    # "from <table> t" 为准 —— XML 才是实际执行的 SQL，比按类名猜更可靠
    if not table:
        _xml, _ = None, None

    m = re.search(r'@TableId\((?:value\s*=\s*)?"?([A-Za-z0-9_]*)"?,?\s*(?:type\s*=\s*IdType\.(\w+))?', src)
    pk_field, pk_auto = (m.group(1) if m and m.group(1) else None), bool(m and m.group(2) == "AUTO")
    # 父类决定 JSON 里那一批前缀字段（BaseEntity 的 createBy 是 String，
    # BaseUuidEntity 的 createBy 是 Long，输出形态不同，不能混用）
    bm = re.search(r'\bclass\s+\w+\s+extends\s+(\w+)', src)
    base_cls = bm.group(1) if bm else None

    fields = []
    # 逐个 private 字段，带它上面的注解
    for fm in re.finditer(
        r'((?:@\w+(?:\([^)]*\))?\s*\n\s*)*)private\s+([\w.<>,\s]+?)\s+(\w+)\s*;', src
    ):
        annos, jtype, name = fm.group(1), fm.group(2).strip(), fm.group(3)
        jtype = jtype.split("<")[0].strip()
        if name in ("serialVersionUID",):
            continue
        excel = None
        ex = re.search(r'@Excel\(([^)]*)\)', annos)
        if ex:
            nm = re.search(r'name\s*=\s*"([^"]*)"', ex.group(1))
            excel = nm.group(1) if nm else ""
            if "readConverterExp" in ex.group(1):
                excel = excel or ""
        jm = re.search(r'@JsonFormat\([^)]*pattern\s*=\s*"([^"]+)"', annos)
        fmt = None
        if jm:
            pat = jm.group(1)
            fmt = "DateYmd" if pat == "yyyy-MM-dd" else ("DateYmdHms" if "HH" in pat else None)
        if re.search(r'@TableField\(\s*exist\s*=\s*false', annos):
            continue
        mapped = TYPE_MAP.get(jtype, "Str")
        if jtype in ("Date", "LocalDateTime", "LocalDate") and fmt:
            mapped = fmt
        fields.append((name, jtype, mapped, excel, bool(re.search(r'@JsonIgnore', annos))))
    return table, pk_field, pk_auto, fields, path, base_cls


def parse_xml_columns(entity):
    """resultMap: property -> column"""
    path = find_mapper_xml(entity)
    if path is None:
        return {}, "", None
    src = read(path)
    mapping = {}
    for m in re.finditer(r'<result\s+property="(\w+)"\s+column="(\w+)"', src):
        mapping[m.group(1)] = m.group(2)
    for m in re.finditer(r'<id\s+property="(\w+)"\s+column="(\w+)"', src):
        mapping[m.group(1)] = m.group(2)
    return mapping, src, path


def parse_conditions(xml_src):
    """从 selectList 的 <if> 抽条件：property -> ('eq'|'like'|'range'|'find_in_set')"""
    conds = {}
    for m in re.finditer(r'<if test="([^"]+)">(.*?)</if>', xml_src, re.S):
        test, body = m.group(1), m.group(2)
        prop = re.match(r"(\w+)\s*!=\s*(null|'')", test)
        if not prop:
            if "params.beginTime" in test or "params.endTime" in test:
                col = re.search(r'date_format\((?:\w+\.)?(\w+)', body)
                if col:
                    conds[("range", camelize(col.group(1)))] = "range"
            continue
        name = prop.group(1)
        low = body.lower()
        if "like concat" in low:
            conds[name] = "like"
        elif "find_in_set" in low:
            conds[name] = "find_in_set"
        elif "=" in low:
            conds[name] = "eq"
        elif "!=" in low:
            conds[name] = "eq"
    # <if test="X != null"> 不判空串 -> eqNotNull
    for m in re.finditer(r'<if test="(\w+)\s*!=\s*null\s*">', xml_src):
        conds.setdefault(m.group(1), "eq_notnull")
    order = re.search(r'order\s+by\s+([^<;]+)', xml_src, re.I)
    return conds, (order.group(1).strip() if order else "")


def parse_controller(ctrl_path):
    src = read(ctrl_path)
    base = re.search(r'@RequestMapping\("([^"]+)"\)', src)
    info = {"base": base.group(1) if base else "", "perms": {}, "methods": [], "pathvar": "id"}
    for m in re.finditer(
        r'(@PreAuthorize\("@ss\.(hasPermi|hasAnyPermi)\(\'([^\']+)\'\)"\)\s*\n?\s*)?'
        r'@(Get|Post|Put|Delete)Mapping(?:\((?:value\s*=\s*)?"([^"]*)"\))?',
        src, re.S):
        perm_kind, perm = (m.group(2), m.group(3)) if m.group(2) else (None, None)
        verb, path = m.group(4), (m.group(5) or "")
        name_m = re.search(r'public\s+[\w<>]+\s+(\w+)\s*\(', src[m.end():m.end() + 400])
        method = name_m.group(1) if name_m else ""
        info["methods"].append((verb, path, method, perm))
        key = {"list": "list", "export": "export", "getInfo": "query", "add": "add",
               "edit": "edit", "remove": "remove"}.get(method)
        if perm and key:
            info["perms"][key] = perm
        pv = re.search(r'@PathVariable\("?(\w+)"?\)', src[m.end():m.end() + 400])
        if pv and verb in ("Get", "Delete"):
            info["pathvar"] = pv.group(1)
    title = re.search(r'@Log\(\s*title\s*=\s*"([^"]+)"', src)
    info["title"] = title.group(1) if title else ""
    return info


def c_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def gen_entity(entity, ctrl_path):
    parsed = parse_domain(entity)
    if not parsed:
        return None
    table, pk_field, pk_auto, fields, dpath, base_cls = parsed
    colmap, xml_src, xpath = parse_xml_columns(entity)
    if not table:
        fm = re.search(r'from\s+([a-z_][a-z0-9_]*)\s+t', xml_src, re.I)
        if fm:
            table = fm.group(1)
        else:
            # 退而求其次：驼峰转下划线（与 MyBatis-Plus 默认命名策略一致）
            table = re.sub(r'([a-z0-9])([A-Z])', lambda m: m.group(1) + "_" + m.group(2).lower(),
                           entity)
            table = table[0].lower() + table[1:]
    conds, order_by = parse_conditions(xml_src)
    known = xml_known_columns(xml_src)
    ctrl = parse_controller(ctrl_path)

    # 生成前先用真实库核对列：对不上说明这不是单表同构 CRUD，直接跳过
    cols = real_columns(table)
    if cols is not None:
        bad = []
        for _n, _t, _f, _e, _ig in fields:
            if _ig:
                continue
            _col = (colmap.get(_n) or snake_case(_n)).lower()
            if known and _col not in known and _n != pk_field:
                continue  # 派生属性，本来就不会进 spec
            if _col not in cols:
                bad.append(_col)
        if bad:
            sys.stderr.write("跳过 %s：表 %s 不存在列 %s（多半是 join 派生字段，需手写）%s"
                             % (entity, table, ",".join(bad), chr(10)))
            return None

    L = []
    L.append("    {")
    L.append("        // %s" % rel(dpath))
    if xpath:
        L.append("        // %s" % rel(xpath))
    L.append("        Spec s;")
    L.append('        s.table = "%s";' % table)
    # 表别名以 XML 为准（sys_role 的 selectRoleVo 用的是 `from sys_role r`，
    # 而 XML 里写死的 order by / where 都带 r. 前缀，硬编码 t 会拼出非法 SQL）。
    # 只看主查询的 FROM：`(select x from tbl t1 ...)` 这种子查询别名要排除。
    cands = []
    for am in re.finditer(r'\bfrom\s+' + re.escape(table) + r'\s+([A-Za-z_]\w*)\b', xml_src, re.I):
        line_start = xml_src.rfind("\n", 0, am.start()) + 1
        if re.search(r'\bselect\b', xml_src[line_start:am.start()], re.I):
            continue
        a = am.group(1)
        if a.lower() not in ("where", "left", "inner", "right", "join", "on", "order",
                             "group", "as", "limit", "having", "set"):
            cands.append(a)
    # XML 里 order by 的前缀就是那条 list 语句的别名，优先与它一致
    ob_prefix = (order_by or "").split(".")[0].strip() if order_by else ""
    alias = ob_prefix if ob_prefix in cands else (cands[0] if cands else "t")
    L.append('        s.alias = "%s";' % alias)
    L.append("        s.fields = {")
    # 1) 父类字段先输出（Jackson 的声明序），列以 resultMap 为准；
    #    resultMap 没映射的保持“只进 JSON 的 null”，与 MyBatis 不填的行为一致。
    own_names = {n for n, _jt, _fmt, _ex, _ig in fields}
    for name, _fallback, bfmt in BASE_FIELDS.get(base_cls or "", []):
        if name in own_names:
            continue  # 子类自己声明了同名字段，以子类为准
        col = colmap.get(name)
        if col and cols is not None and col.lower() not in cols:
            sys.stderr.write("  %s.%s: resultMap 声明的列 %s 在表 %s 里不存在，按 null 输出%s"
                             % (entity, name, col, table, chr(10)))
            col = None
        # BaseUuidEntity / BasePlus* 的 id 没有 @TableId 注解，但确实是主键
        is_pk = name == pk_field or (base_cls in _PK_ID_BASES and name == "id"
                                     and not pk_field and col is not None)
        cpp_fmt = bfmt if bfmt in FMT_NAMES else "Str"
        L.append('            {"%s", %s, Fmt::%s, Cond::None, nullptr, %s, false, false, false},'
                 % (name, ('"%s"' % col) if col else "nullptr", cpp_fmt,
                    "true" if is_pk else "false"))
    # 2) 子类自有字段
    for name, jtype, fmt, excel, ignored in fields:
        if ignored:
            continue
        is_pk = (name == pk_field)
        col = colmap.get(name) or snake_case(name)
        if known and col.lower() not in known and not is_pk:
            continue  # 派生属性：XML 里没有这一列，跳过（对齐 MP @TableField(exist=false)）
        cond_cpp = {
            "eq": "Cond::Eq", "like": "Cond::Like", "eq_notnull": "Cond::EqNotNull",
            "find_in_set": "Cond::FindInSet", "range": "Cond::DateRange",
        }.get(conds.get(name, "None"), "Cond::None")
        ex = '\"%s\"' % c_escape(excel) if excel else "nullptr"
        L.append('            {"%s", "%s", Fmt::%s, %s, %s, %s, %s},' % (
            name, col, fmt, cond_cpp, ex, "true" if is_pk else "false",
            "true" if (is_pk and pk_auto) else "false"))
    L.append("        };")
    if order_by:
        L.append('        s.orderBy = "%s";' % c_escape(order_by))
    title = ctrl.get("title") or entity
    L.append('        s.excelSheetName = "%s";' % c_escape(title))
    if ctrl.get("range_column"):
        L.append('        s.rangeColumn = "%s";' % ctrl["range_column"])
    perms = ctrl["perms"]
    L.append("        Perms p;")
    for key, field in (("list", "list"), ("export", "exportList"), ("query", "query"),
                       ("add", "add"), ("edit", "edit"), ("remove", "remove")):
        if key in perms:
            L.append('        p.%s = "%s";' % (field, perms[key]))
    L.append('        registerCrud(r, "%s", s, p, "%s");' % (ctrl["base"], ctrl["pathvar"]))
    for vpath, vkind, vperm in spec_variants.classify_variants(
            spec_variants.method_bodies(read(ctrl_path)), entity):
        if vperm:
            L.append("        registerListVariant(r, \"%s%s\", s, %s, \"%s\");"
                    % (ctrl["base"], vpath, vkind, vperm))
        else:
            L.append("        registerListVariant(r, \"%s%s\", s, %s);"
                    % (ctrl["base"], vpath, vkind))
    L.append("    }")
    return "\n".join(L), ctrl["base"], entity


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=False, choices=list(AREAS))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--only-entities", default=None, help="逗号分隔的实体白名单，例如 SysPost,SysIndexMenu")
    args = ap.parse_args()

    CTRL_ROOTS = {
        "quartz": os.path.join(REPO, "ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller"),
        "generator": os.path.join(REPO, "ruoyi-generator/src/main/java/com/ruoyi/generator/controller"),
    }
    sub, _pfx = AREAS[args.area]
    area_dir = CTRL_ROOTS.get(args.area, os.path.join(JAVA_ROOT, sub)) if args.area else None
    if args.list or not args.area:
        for d in ([area_dir] if area_dir else []):
            for f in sorted(os.listdir(d)):
                if f.endswith("Controller.java"):
                    print(f[:-14])
        return

    ns_suffix, ns_prefix = AREAS[args.area]
    generated, bases = [], []
    allow = set((args.only_entities or "").split(",")) if args.only_entities else None
    for f in sorted(os.listdir(area_dir)):
        if not f.endswith("Controller.java"):
            continue
        entity = f[:-len("Controller.java")]
        if allow is not None and entity not in allow:
            continue
        out = gen_entity(entity, os.path.join(area_dir, f))
        if out is None:
            print("!! 无法解析: " + entity, file=sys.stderr)
            continue
        body, base, _ = out
        generated.append(body)
        bases.append((entity, base))

    out_default = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "src", "cm", "web", "specs",
                              "%sCrudSpecs.cpp" % ns_prefix)
    path = args.out or out_default
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "crud_spec_template.tmpl")
    content = io.open(tmpl_path, encoding="utf-8").read()
    content = (content.replace("@@AREA@@", args.area)
                      .replace("@@PREFIX@@", ns_prefix)
                      .replace("@@BODY@@", chr(10).join(generated)))
    io.open(path, "w", encoding="utf-8", newline="\r\n").write(content)
    print("生成 %s：%d 个实体" % (path, len(bases)))
    for e, b in bases:
        print("   %-45s %s" % (e, b))


if __name__ == "__main__":
    main()

