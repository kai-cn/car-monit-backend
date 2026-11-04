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
import json
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


def vo_projection(xml_src, cols):
    """实体自己的 Mapper XML 里，list 查询真正 SELECT 出来的列集合。

    MyBatis 只填结果集里出现的列：Vo 没写的属性，Java 响应里是 null（或字段声明初值）。
    C++ 的 Spec 同时驱动 WHERE 与 SELECT，不记录这件事就会把 track_josn / eps_id 这种
    “能当条件但 Vo 不投影”的列查出来返回，凭空比 Java 多给数据
    （实测 /manager/suspicious/list 的 9 个键）。
    返回 None 表示无法确定（没有 Vo / Vo 里有 * 与动态标签 / 那是 join 出来的 Vo），
    这时维持全投影，宁缺毋滥。
    """
    sqls = re.findall(r'<sql\s+id="(select\w*)">(.*?)</sql>', xml_src, re.S)
    if len(sqls) != 1:
        return None
    vo_id, vo_body = sqls[0]
    if re.search(r'\*|<include|<if\b|<choose|<where', vo_body, re.I):
        return None
    # Vo 必须真的被本 XML 的查询引用，否则这份列清单不属于这条 spec
    if '<include refid="%s"' % vo_id not in xml_src:
        return None
    found = {c.lower() for _a, c in re.findall(r'\b(\w+)\.([a-zA-Z_]\w*)', vo_body)}
    found |= {c.lower() for c in re.findall(r'^\s*`?([a-z_][a-z0-9_]*)`?\s*,?\s*$', vo_body, re.M)}
    if not found:
        return None
    if cols:
        # 超过三分之一不是本表的列 => 这是别的实体/多表 join 的 Vo，不可信
        if len([c for c in found if c not in cols]) > len(found) // 3:
            return None
    return found


def invo_tail(in_vo, written):
    """Field 的第 12 位是 inVo；aggregate 初始化只能顺序补默认值，
    所以要先按“已经写到第几位”把中间的空位填上。"""
    if in_vo:
        return ""
    return ", nullptr" * max(0, 11 - written) + ", false"


def snake_case(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and not name[i - 1].isupper():
            out.append('_')
        out.append(ch.lower())
    return ''.join(out)

def json_literal(raw):
    """Java 字段初始值 -> JSON 字面量字符串；认不出的返回 None（按 null 处理）"""
    if not raw:
        return None
    t = raw.strip()
    if re.match(r'^-?\d+$', t):
        return t
    if re.match(r'^-?\d+\.\d+[fFdD]?$', t):
        return re.sub(r'[fFdD]$', '', t)
    if t in ("true", "false"):
        return t
    if re.match(r'^".*"$', t) or re.match(r"^'.*'$", t):
        return json.dumps(t[1:-1])
    if t == "BigDecimal.ZERO":
        return "0"
    if t == "BigDecimal.ONE":
        return "1"
    if t == "BigDecimal.TEN":
        return "10"
    if t == "Integer.MAX_VALUE":
        return str(2 ** 31 - 1)
    if t == "Long.MAX_VALUE":
        return str(2 ** 63 - 1)
    if re.match(r'^new\s+(ArrayList|LinkedList|CopyOnWriteArrayList)<>', t) or t.startswith("Lists.newArrayList"):
        return "[]"
    if re.match(r'^new\s+HashMap<>', t) or t.startswith("Maps.newHashMap"):
        return "{}"
    if re.match(r'^new\s+HashSet<>', t):
        return "[]"
    return None


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
    # 逐个 private 字段，带它上面的注解。初值也要抓：Java 的 `private String x = "0";`
    # 在 Jackson 里就是 "0"，不是 null（漏掉初值会让响应少键或把值写成 null）。
    # 类型里要允许数组/泛型（Long[] menuIds 这类漏掉过整根键）。
    for fm in re.finditer(
        r'((?:@\w+(?:\([^)]*\))?\s*\n\s*)*)private\s+([\w.<>,\s\[\]]+?)\s+(\w+)\s*(?:=\s*([^;]+))?\s*;', src
    ):
        annos, jtype, name = fm.group(1), fm.group(2).strip(), fm.group(3)
        dflt = (fm.group(4) or "").strip()
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
        # @TableField(exist=false) 不是表列，但仍然是实体的字段：
        # Jackson 会输出这个键（值多为 null），所以这里不跳过，交给 gen_entity 降级成 nullptr 列
        mapped = TYPE_MAP.get(jtype, "Str")
        if jtype in ("Date", "LocalDateTime", "LocalDate") and fmt:
            mapped = fmt
        fields.append((name, jtype, mapped, excel, bool(re.search(r'@JsonIgnore', annos)),
                       json_literal(dflt)))
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


def parse_write_columns(xml_src):
    """返回 (可 INSERT 的属性集合, 可 UPDATE 的属性集合)，取自 generator 风格的
    insertXxx / updateXxx 语句里的 <if test="prop != null">。

    为什么要管：这些 XML 决定了 Java 侧落库到底写哪些列 —— 父类的
    create_by/create_time/eps_id/del_flag 都在 insert 里，update 里带 update_by/update_time。
    实体没有这种语句（走 MyBatis-Plus BaseMapper）时返回空集，调用方按"全部可写"处理。
    """
    ins, upd = set(), set()
    for m in re.finditer(r"<insert\b[^>]*id=\"insert\w*\".*?</insert>", xml_src, re.S):
        for im in re.finditer(r'<if test="(\w+)\s*!=\s*null[^"]*">', m.group(0)):
            ins.add(im.group(1))
    for m in re.finditer(r'<update\b[^>]*id="update\w*".*?</update>', xml_src, re.S):
        for um in re.finditer(r'<if test="(\w+)\s*!=\s*null[^"]*">', m.group(0)):
            upd.add(um.group(1))
    return ins, upd


def parse_conditions(xml_src):
    """从 selectList 的 <if> 抽条件：
    返回 (property -> 条件形态, order by, property -> 条件左值列名)"""
    conds = {}
    cond_cols = {}
    for m in re.finditer(r'<if test="([^"]+)">(.*?)</if>', xml_src, re.S):
        test, body = m.group(1), m.group(2)
        prop = re.match(r"(\w+)\s*!=\s*(null|'')", test)
        if not prop:
            if "params.beginTime" in test or "params.endTime" in test:
                col = re.search(r'date_format\((?:\w+\.)?(\w+)', body)
                if col:
                    # 键必须是字段名：conds 是按属性名查的，之前用元组当键 => 区间条件永远没生效
                    conds.setdefault(camelize(col.group(1)), "range")
            continue
        name = prop.group(1)
        low = body.lower()
        if "find_in_set" in low:
            # 参数顺序有两种写法，语义完全相反：
            #   find_in_set(#{deptId}, ancestors)   值在列里   -> find_in_set
            #   find_in_set(t.id, #{exceptIds})     列在值里   -> find_in_set_col
            first = re.search(r'find_in_set\s*\(\s*([^,]+),', low)
            arg = first.group(1).strip() if first else ""
            if arg.startswith("#{"):
                conds[name] = "find_in_set"
            else:
                conds[name] = "find_in_set_col"
                left = re.search(r'find_in_set\s*\(\s*([\w.]+)\s*,', body, re.I)
                if left:
                    cond_cols[name] = left.group(1)
            continue
        # “一列一参数”的简单比较：运算符决定条件形态，左边的列名可能并不是该属性自己的列
        # （RuoYi 业务代码里改过条件的地方全靠这一步才不漏：<if test="sectionCode != ''">
        #  实际过滤 t.track_names；<if test="applyTime1 != ''"> 过滤 t.in_time >=）
        simple = re.match(r"\s*(?:and\s+)?(?:(\w+)\.)?([a-z_][a-z0-9_]*)\s*"
                          r"(>=|<=|<>|!=|not\s+like|like|=|<|>)", body, re.I)
        if not simple or len(re.findall(r"#\{\w+", body)) != 1:
            if "like concat" in low:
                conds[name] = "like"
            continue
        op = re.sub(r"\s+", " ", simple.group(3)).lower()
        cond_cols.setdefault(name, simple.group(2))
        conds[name] = {
            "like": "like", "not like": "not_like", "=": "eq", "!=": "ne", "<>": "ne",
            ">": "gte", ">=": "gte", "<": "lte", "<=": "lte",
        }[op]
    # <if test="X != null"> 不判空串 -> eqNotNull
    for m in re.finditer(r'<if test="(\w+)\s*!=\s*null\s*">', xml_src):
        conds.setdefault(m.group(1), "eq_notnull")
    order = re.search(r'order\s+by\s+([^<;]+)', xml_src, re.I)
    return conds, (order.group(1).strip() if order else ""), cond_cols


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
    conds, order_by, cond_cols = parse_conditions(xml_src)
    w_ins, w_upd = parse_write_columns(xml_src)

    def write_flags(name, has_col):
        """insertable/updatable：没有 generator 风格的 insertXxx/updateXxx 时按 MP 语义全可写"""
        ins = (name in w_ins) if w_ins else True
        upd = (name in w_upd) if w_upd else True
        if not has_col:  # 不是表列，任何写语句都不该带上它
            return False, False
        return ins, upd
    known = xml_known_columns(xml_src)
    ctrl = parse_controller(ctrl_path)

    # 生成前先用真实库核对列：对不上说明这不是单表同构 CRUD，直接跳过
    cols = real_columns(table)
    if cols is not None:
        bad = []
        for _n, _t, _f, _e, _ig, _d in fields:
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

    fn = "spec%s" % entity
    vo = vo_projection(xml_src, cols)
    L = []
    # Spec 以文件级函数暴露，手写控制器可复用同一份列定义
    L.append("const Spec& %s() {" % fn)
    L.append("    static const Spec s = [] {")
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
    # XML 的 selectList 里写死在 <if> 之外的 where 片段（几乎必然是逻辑删除过滤）。
    # 丢了它就等于把 del_flag='1' 的行也返回给前端，与 Java 结果集不同；
    # 只看 <if> 之外的部分，否则会把"用户传了 status 才生效"的条件误当成恒定过滤。
    list_stmt = re.search(r'<select\b[^>]*id="select\w*(?:List|Vo)?"[^>]*>(.*?)</select>', xml_src, re.S)
    probe = list_stmt.group(1) if list_stmt else xml_src
    probe = re.sub(r"<if\b[^>]*>.*?</if>", " ", probe, flags=re.S)
    probe += re.sub(r"<if\b[^>]*>.*?</if>", " ",
                    re.search(r'<sql id="select\w*Vo">(.*?)</sql>', xml_src, re.S).group(1)
                    if re.search(r'<sql id="select\w*Vo">(.*?)</sql>', xml_src, re.S) else "",
                    flags=re.S)
    fixed = []
    if re.search(r"(?:\b%s\.|\b)del_flag\s*=\s*'0'" % re.escape(alias), probe, re.I):
        fixed.append(" and %s.del_flag = '0'" % alias)
    if re.search(r"(?:\b%s\.|\b)status\s*=\s*'0'" % re.escape(alias), probe, re.I):
        fixed.append(" and %s.status = '0'" % alias)
    if fixed:
        L.append('        s.extraWhere = "%s";' % "".join(fixed))
    L.append("        s.fields = {")
    COND_CPP = {
        "eq": "Cond::Eq", "ne": "Cond::Ne", "like": "Cond::Like", "not_like": "Cond::NotLike",
        "gte": "Cond::Gte", "lte": "Cond::Lte", "eq_notnull": "Cond::EqNotNull",
        "find_in_set": "Cond::FindInSet", "find_in_set_col": "Cond::FindInSetCol",
        "range": "Cond::DateRange",
    }

    def cond_col_for(name, own_col, kind):
        """XML 里条件左值列与属性自身的列不一致时返回该列。
        只认本表的真实列 —— 左值是函数（date_format(...)）或别的表的列时一律放弃覆盖，
        宁可维持原有行为，也不把 WHERE 拼成非法 SQL。"""
        if kind == "None" or name not in cond_cols:
            return None
        left = cond_cols[name]
        if left.startswith(alias + "."):
            left = left[len(alias) + 1:]
        if "." in left:
            left = left.split(".")[-1]
        if own_col and left.lower() == own_col.lower():
            return None
        if cols is not None and left.lower() not in cols:
            return None
        return left

    # 1) 父类字段先输出（Jackson 的声明序），列以 resultMap 为准；
    #    resultMap 没映射的保持“只进 JSON 的 null”，与 MyBatis 不填的行为一致。
    own_names = {n for n, _jt, _fmt, _ex, _ig, _d in fields}
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
        ins, upd = write_flags(name, col is not None)
        # 父类字段同样可能是 XML 里的查询条件（epsId / tenantId / createBy / createTime 的
        # params.beginTime|endTime 区间…）。以前这里写死 Cond::None，条件被静默丢掉 =>
        # 前端传了过滤参数却返回全量（实测 /manager/exceptrecord/list?epsId=... 273 行应为 249 行）。
        cond_kind = conds.get(name, "None")
        cond_cpp = COND_CPP.get(cond_kind, "Cond::None")
        left = cond_col_for(name, col, cond_kind)
        cond_col = '\"%s\"' % left if left else "nullptr"
        in_vo = vo is None or col is None or col.lower() in vo
        L.append('            {"%s", %s, Fmt::%s, %s, nullptr, %s, false, %s, %s, %s%s},'
                 % (name, ('"%s"' % col) if col else "nullptr", cpp_fmt, cond_cpp,
                    "true" if is_pk else "false",
                    "true" if ins else "false", "true" if upd else "false", cond_col,
                    invo_tail(in_vo, 10)))
    # 2) 子类自有字段
    for name, jtype, fmt, excel, ignored, dflt in fields:
        if ignored:
            continue
        is_pk = (name == pk_field)
        col = colmap.get(name) or snake_case(name)
        ex = '\"%s\"' % c_escape(excel) if excel else "nullptr"
        if known and col.lower() not in known and not is_pk:
            # 派生属性 / @TableField(exist=false)：MyBatis 不填值，但 Jackson 照样输出键。
            # 有 Java 字段初值的输出初值（如 supplementaryStatus = "0"、children = new ArrayList<>()），
            # 没有的才是 null。
            # 例外：XML 里仍然可能拿它当查询条件，且条件左值是别的列
            #       （car_except_record 的 find_in_set(t.id, #{exceptIds})、
            #        car_suspicious 的 applyTime1 -> t.in_time >=、carNoQuery -> t.car_no like）
            cond_kind = conds.get(name, "None")
            cond_cpp = COND_CPP.get(cond_kind, "Cond::None")
            if cond_kind == "range":
                cond_cpp = "Cond::None"   # 区间条件必须有真实列可投，派生属性带不动
            left = None if cond_cpp == "Cond::None" else cond_col_for(name, None, cond_kind)
            if cond_cpp != "Cond::None" and left is None and cond_kind != "find_in_set":
                cond_cpp = "Cond::None"   # 左值列不可信，宁可不加条件
            cond_col = '\"%s\"' % left if left else "nullptr"
            dflt_cpp = '"%s"' % dflt.replace('"', '\\"') if dflt else "nullptr"
            L.append('            {"%s", nullptr, Fmt::%s, %s, %s, false, false, false, false, %s, %s},'
                     % (name, fmt if fmt in FMT_NAMES else "Str", cond_cpp, ex, cond_col, dflt_cpp))
            continue
        cond_kind = conds.get(name, "None")
        cond_cpp = COND_CPP.get(cond_kind, "Cond::None")
        ins, upd = write_flags(name, True)
        tail = ""
        left = cond_col_for(name, col, cond_kind)
        if left:
            tail = ', "%s"' % left  # Field 的 condColumn：条件左值另有其列
        L.append('            {"%s", "%s", Fmt::%s, %s, %s, %s, %s, %s, %s%s%s},' % (
            name, col, fmt, cond_cpp, ex, "true" if is_pk else "false",
            "true" if (is_pk and pk_auto) else "false",
            "true" if ins else "false", "true" if upd else "false", tail,
            invo_tail(vo is None or col.lower() in vo, 10 if tail else 9)))
    L.append("        };")
    if order_by:
        L.append('        s.orderBy = "%s";' % c_escape(order_by))
    title = ctrl.get("title") or entity
    L.append('        s.excelSheetName = "%s";' % c_escape(title))
    if ctrl.get("range_column"):
        L.append('        s.rangeColumn = "%s";' % ctrl["range_column"])
    perms = ctrl["perms"]
    # 注册部分单独成块：Spec 已经是函数，Perms 与路由留在 registerXxxArea 里
    L.append("        return s;")
    L.append("    }();")
    L.append("    return s;")
    L.append("}")
    L.append("")
    R = []
    R.append("    {")
    R.append("        // %s" % rel(dpath))
    if xpath:
        R.append("        // %s" % rel(xpath))
    R.append("        Perms p;")
    for key, field in (("list", "list"), ("export", "exportList"), ("query", "query"),
                       ("add", "add"), ("edit", "edit"), ("remove", "remove")):
        if key in perms:
            R.append('        p.%s = "%s";' % (field, perms[key]))
    R.append('        registerCrud(r, "%s", %s(), p, "%s");' % (ctrl["base"], fn, ctrl["pathvar"]))
    for vpath, vkind, vperm in spec_variants.classify_variants(
            spec_variants.method_bodies(read(ctrl_path)), entity):
        if vperm:
            R.append("        registerListVariant(r, \"%s%s\", %s(), %s, \"%s\");"
                     % (ctrl["base"], vpath, fn, vkind, vperm))
        else:
            R.append("        registerListVariant(r, \"%s%s\", %s(), %s);"
                     % (ctrl["base"], vpath, fn, vkind))
    R.append("    }")
    return "\n".join(L), "\n".join(R), ctrl["base"], entity, fn


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
    specs, generated, bases = [], [], []
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
        spec_src, body, base, _, fn = out
        specs.append(spec_src)
        generated.append(body)
        bases.append((entity, base, fn))

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_default = os.path.join(root, "src", "cm", "web", "specs",
                               "%sCrudSpecs.cpp" % ns_prefix)
    path = args.out or out_default
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "crud_spec_template.tmpl")
    content = io.open(tmpl_path, encoding="utf-8").read()
    content = (content.replace("@@AREA@@", args.area)
                      .replace("@@PREFIX@@", ns_prefix)
                      .replace("@@SPECS@@", chr(10).join(specs))
                      .replace("@@BODY@@", chr(10).join(generated)))
    io.open(path, "w", encoding="utf-8", newline="\r\n").write(content)

    # 声明文件：手写控制器 include 它即可复用同一个 Spec
    hdr_path = os.path.join(root, "include", "cm", "web", "specs",
                            "%sCrudSpecs.hpp" % ns_prefix)
    os.makedirs(os.path.dirname(hdr_path), exist_ok=True)
    hdr = [
        "// 由 scripts/gen_crud_spec.py 生成，与 src/cm/web/specs/%sCrudSpecs.cpp 成对。" % ns_prefix,
        "// 手写控制器通过这里复用同一份列定义，不要再抄一遍字段表。",
        "#pragma once",
        '#include "cm/framework/web/crud/CrudSpec.hpp"',
        "",
        "namespace cm::web::crud {",
        "",
    ]
    for _e, _b, fn in bases:
        hdr.append("const Spec& %s();" % fn)
    hdr += ["", "} // namespace cm::web::crud", ""]
    io.open(hdr_path, "w", encoding="utf-8", newline="\r\n").write(chr(10).join(hdr))

    print("生成 %s：%d 个实体" % (path, len(bases)))
    for e, b, _fn in bases:
        print("   %-45s %s" % (e, b))


if __name__ == "__main__":
    main()

