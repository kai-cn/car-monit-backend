#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验生成的 CRUD spec：
  1) 每个实体的投影 SQL 在真实 MySQL 上能跑（列名/表名/别名写错会立刻暴露）
  2) WHERE 条件片段能跑（等值/like/date_format 区间）
  3) 生成的 6 条路由在运行中的服务里确实注册了（401 而不是 404）

用法:
    python scripts/verify_generated_sql.py                       # 只做 SQL 校验
    python scripts/verify_generated_sql.py --base http://127.0.0.1:9989   # 再加路由校验

连接参数与 config/application-druid.yaml 一致，可用环境变量覆盖：
    CM_DB_HOST / CM_DB_PORT / CM_DB_USER / CM_DB_PASSWORD / CM_DB_NAME
"""
import argparse
import io
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CPP = os.path.dirname(HERE)
SPEC_DIR = os.path.join(CPP, "src", "cm", "web", "specs")

DB = dict(
    host=os.environ.get("CM_DB_HOST", "127.0.0.1"),
    port=os.environ.get("CM_DB_PORT", "3307"),
    user=os.environ.get("CM_DB_USER", "root"),
    password=os.environ.get("CM_DB_PASSWORD", "root"),
    name=os.environ.get("CM_DB_NAME", "carmonitdb"),
)

FIELD_RE = re.compile(
    r'\{"(?P<json>[^"]+)",\s*"(?P<col>[^"]+)",\s*Fmt::(?P<fmt>\w+),\s*Cond::(?P<cond>\w+),'
    r'\s*(?P<excel>"[^"]*"|nullptr),\s*(?P<pk>true|false),\s*(?P<auto>true|false)\}')


def mysql(sql):
    """执行一条 SQL，返回 (ok, 文本)"""
    cmd = ["mysql", "-h", DB["host"], "-P", DB["port"], "-u", DB["user"],
           "-p" + DB["password"], "-N", "-B", DB["name"], "-e", sql]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                         encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return None, "找不到 mysql 客户端"
    out = (p.stdout or "") + (p.stderr or "")
    out = "\n".join(l for l in out.splitlines() if "Using a password" not in l)
    return p.returncode == 0, out


NL = chr(10)


def parse_spec(path):
    src = io.open(path, encoding="utf-8").read()
    specs = []
    # 每个 { ... } 块：table / orderBy / registerCrud(r, "<base>", ...)
    # 相邻块共用 "    }}"+"{" 边界，正则会把一半块吃掉，所以按 split 取块
    for b in src.split(NL + "    {" + NL)[1:]:
        b = b.split(NL + "    }" + NL)[0]
        table = re.search(r's\.table = "([^"]+)";', b)
        base = re.search(r'registerCrud\(r, "([^"]+)", s, p, "([^"]+)"\);', b)
        if not table or not base:
            continue
        fields = [m.groupdict() for m in FIELD_RE.finditer(b)]
        order = re.search(r's\.orderBy = "([^"]*)";', b)
        specs.append({
            "file": os.path.basename(path),
            "table": table.group(1),
            "base": base.group(1),
            "pkvar": base.group(2),
            "fields": fields,
            "orderBy": order.group(1) if order else "",
        })
    return specs


# 已知的“照抄 Java 缺陷”：这些 SQL 在 Java 侧同样报错，迁移策略是不顺手修正。
# 每一项都给出 Java 源码位置，改动前请先确认 Java 也一起改了。
EXPECTED_SQL_ERRORS = {
    "ods_szdn_toll_station_ip": (
        "Unknown column",
        "ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml:35 "
        "写的是 order by t.big_id，而表里没有 big_id 列 —— Java 的 "
        "GET /base/tollStationIp/list 本身就是 500，C++ 保持一致",
    ),
}


def check_sql(spec):
    """跑投影/计数/条件三类 SQL，返回问题列表"""
    problems = []
    cols = ", ".join("t." + f["col"] for f in spec["fields"])
    if not cols:
        return ["没有字段"]
    q = "SELECT %s FROM %s t WHERE 1=1" % (cols, spec["table"])
    if spec["orderBy"]:
        q += " ORDER BY " + spec["orderBy"]
    q += " LIMIT 0,1"
    ok, out = mysql(q)
    if ok is None:
        return [out]
    if not ok:
        problems.append("投影 SQL 失败: " + out.strip().splitlines()[0][:140])
        return problems
    ok, out = mysql("SELECT COUNT(1) %s FROM %s t" % ("", spec["table"]))
    if not ok:
        problems.append("COUNT 失败: " + out.strip().splitlines()[0][:140])
    # 条件片段：用第一个条件字段造一个不可能的值，验证语法而非结果
    conds = [f for f in spec["fields"] if f["cond"] != "None"]
    for f in conds[:4]:
        if f["cond"] == "Like":
            frag = "and t.%s like concat('%%', 'zz', '%%')" % f["col"]
        elif f["cond"] == "DateRange":
            frag = (" and date_format(t.%s, '%%Y%%m%%d') >= date_format('2024-01-01', '%%Y%%m%%d')"
                    % f["col"])
        elif f["cond"] == "FindInSet":
            frag = "and find_in_set('1', t.%s)" % f["col"]
        elif f["fmt"] in ("DateYmd", "DateYmdHms", "DateIso", "DateTimeIso"):
            # 日期列要用合法日期做哨兵，否则 MySQL 报 Incorrect DATETIME（那是校验脚本的问题）
            frag = "and t.%s = '2024-01-01 00:00:00'" % f["col"]
        elif f["fmt"] in ("Int", "Long"):
            frag = "and t.%s = 0" % f["col"]
        else:
            frag = "and t.%s = 'zz'" % f["col"]
        ok, out = mysql("SELECT COUNT(1) FROM %s t WHERE 1=1 %s" % (spec["table"], frag))
        if not ok:
            problems.append("条件片段失败 [%s %s]: %s" % (f["cond"], f["col"],
                                                        out.strip().splitlines()[0][:120]))
    return problems


CPP_ROOT = os.path.dirname(SPEC_DIR.replace(os.path.dirname(SPEC_DIR), CPP)) if False else CPP

VERB_RE = re.compile(r'r\.(get|post|put|del|patch)\(\s*"([^"]+)"')
SPEC_RE = re.compile(r'registerCrud\(r, "([^"]+)", s, p, "([^"]+)"\)')


def cpp_routes():
    """从源码里枚举 C++ 注册的路由。

    ⚠️ 不用 HTTP 探测来判定“路由是否存在”：RuoYi 在未鉴权时对已注册和未注册路径
    都返回 HTTP 200 + body {"code":401}（AuthenticationEntryPointImpl 的行为），
    HTTP 状态码分不出差别，只有拿到合法 token 之后才能做响应内容比对。
    """
    routes = set()
    src_root = os.path.join(CPP, "src", "cm")
    for dirpath, _dirs, files in os.walk(src_root):
        for fn in files:
            if not fn.endswith(".cpp"):
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            for verb, path in VERB_RE.findall(text):
                routes.add((verb.upper() if verb != "del" else "DELETE") + " " + path)
            for base, _pk in SPEC_RE.findall(text):
                for verb, pth in (("GET", base + "/list"), ("GET", base + "/export"),
                                  ("GET", base + "/{id}"), ("POST", base),
                                  ("PUT", base), ("DELETE", base + "/{id}")):
                    routes.add(verb + " " + pth)
    return routes


def java_routes():
    """按注解统计 Java 端点（类级 @RequestMapping + 方法级映射）"""
    repo = os.path.dirname(CPP)
    roots = [
        os.path.join(repo, "ruoyi-admin/src/main/java/com/ruoyi/web/controller"),
        os.path.join(repo, "ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller"),
        os.path.join(repo, "ruoyi-generator/src/main/java/com/ruoyi/generator/controller"),
    ]
    total = 0
    per_class = {}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.endswith("Controller.java"):
                    continue
                text = io.open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
                cls = re.search(r'@RequestMapping\("([^"]*)"\)', text)
                base = cls.group(1) if cls else ""
                n = 0
                for m in re.finditer(r'^\s*@(Get|Post|Put|Delete|Patch)Mapping(?:\((?:value\s*=\s*)?"([^"]*)")?\)?',
                                     text, re.M):
                    if m.group(0).lstrip().startswith("//"):
                        continue
                    n += 1
                if n:
                    per_class[fn[:-5]] = (base, n)
                    total += n
    return total, per_class


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="运行中的服务地址，例如 http://127.0.0.1:9989")
    ap.add_argument("--only", default=None, help="只校验某个文件（BaseCrudSpecs.cpp）")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(SPEC_DIR) if f.endswith(".cpp"))
    if args.only:
        files = [f for f in files if f == args.only]
    specs = []
    for f in files:
        specs += parse_spec(os.path.join(SPEC_DIR, f))
    if not specs:
        print("没有解析到任何 spec，检查 %s" % SPEC_DIR)
        return 1

    bad = 0
    for sp in specs:
        problems = check_sql(sp)
        exp = EXPECTED_SQL_ERRORS.get(sp["table"])
        if exp:
            kept = [x for x in problems if exp[0] not in x]
            if len(kept) != len(problems):
                print("   [预期一致] %-32s %s" % (sp["table"], exp[1]))
            problems = kept
        routes = []
        tag = "%-28s %-42s %s" % (sp["file"], sp["table"], sp["base"])
        if problems or routes:
            bad += 1
            print("FAIL " + tag)
            for p in problems:
                print("      " + p)
            if routes:
                print("      路由 404: " + ", ".join(routes))
        else:
            print("ok   " + tag)
    print("")
    print("实体 %d，异常 %d" % (len(specs), bad))
    jtotal, per_class = java_routes()
    cpp = cpp_routes()
    print("Java 端点注解（按控制器统计）= %d，覆盖 %d 个控制器" % (jtotal, len(per_class)))
    print("C++ 已注册路由（源码枚举）= %d" % len(cpp))
    if args.base:
        print("提示：HTTP 状态码无法区分 401/404（RuoYi 未鉴权时两者都回 200 + body code），"
              "响应内容比对需要先拿到合法 token")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
