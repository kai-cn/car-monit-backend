#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：代码生成器的 3 条 DB 侧端点（importTable / PUT / synchDb）。

这三条会写 gen_table / gen_table_column，所以脚本自己挑一张**当前没导过**的库表当夹具，
验完按新建的 table_id 硬删除，最后断言"与调用前逐行一致"。

断言的重点是 GenUtils 那套映射在真实表上落地后的样子（映射表本身在
tests/gen_utils_test.cpp 里已用纯函数钉住），以及三条端点各自的畸形行为：
  * importTable 没有"已存在就跳过"，导两次就是两套行；
  * synchDb 只补新列 + 删库里没有的列，**从不更新**已存在的列（手加的列会被删）；
  * PUT 的 options 由 body 的 params 重新序列化，不带 params 就被写成 "{}"（原 parentMenuId 抹掉）；
  * updateGenTableColumn 前 12 个赋值是无条件的，body 没带的字段会被写成 NULL。

用法：python scripts/verify_gen_write.py [port] [token]
"""
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT
PUT, POST = "PUT", "POST"
JSON_CT = "application/json;charset=UTF-8"

ok = bad = 0


def _num(column_type):
    """括号里的第一段（int(11) -> 11）；没有括号返回 -1"""
    if "(" not in column_type:
        return -1
    inside = column_type.split("(")[1].split(")")[0]
    return int(inside.split(",")[0]) if inside.split(",")[0].isdigit() else -1


def _scale(column_type):
    if "(" not in column_type:
        return -1
    inside = column_type.split("(")[1].split(")")[0]
    parts = inside.split(",")
    return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1




def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:170] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot", "carmonitdb",
                        "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return [l.split("\t") for l in out.splitlines()] if out else []


def call(path, method="GET", body=None, ctype=None, token=None):
    r = urllib.request.Request(BASE + path, method=method)
    t = TOKEN if token is None else token
    if t:
        r.add_header("Authorization", "Bearer " + t)
    data = body.encode("utf-8") if isinstance(body, str) else body
    if data is not None and ctype:
        r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def js(path, method="GET", body=None, ctype=None, token=None):
    st, raw = call(path, method, body, ctype, token)
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:
        return st, {"raw": raw[:200]}


before_tables = {r[0] for r in mysql("select table_id from gen_table")}
before_cols = {r[0] for r in mysql("select column_id from gen_table_column")}
cand = mysql("select table_name from information_schema.tables where table_schema=database()"
             " and table_name not like 'qrtz\\_%' and table_name not like 'gen\\_%'"
             " and table_name not in (select table_name from gen_table) limit 1")
if not cand:
    print("库里找不到没导过的表，无法验证")
    sys.exit(2)
TN = cand[0][0]
print("# 夹具表 = %s" % TN)

try:
    st, j = js("/tool/gen/importTable?tables=" + urllib.parse.quote(TN), method="POST")
    check("importTable 200 且响应没有 data 键（AjaxResult.success()）",
          st == 200 and list(j.keys()) == ["msg", "code"] and j.get("code") == 200, j)

    rows = mysql("select table_id, class_name, package_name, module_name, business_name,"
                 " function_name, function_author, create_by, tpl_category, gen_type, options,"
                 " table_comment, create_time from gen_table where table_name='%s'" % TN)
    check("gen_table 插入了 1 行", len(rows) == 1, rows)
    t = rows[0]
    TABLE_ID = t[0]
    segs = TN.split("_")
    exp_class = "".join((p[:1].upper() + p[1:].lower()) for p in segs if p)
    check("class_name = convertToCamelCase(表名)（autoRemovePre=false ⇒ 前缀保留）",
          t[1] == exp_class, (t[1], exp_class))
    check("package_name/module_name 取自 generator.yml 的 com.ruoyi.manager",
          t[2] == "com.ruoyi.manager" and t[3] == "manager", (t[2], t[3]))
    check("business_name = 最后一个下划线之后的部分", t[4] == segs[-1], t[4])
    check("function_author 恒为 ruoyi、create_by 是当前登录名",
          t[6] == "ruoyi" and t[7] == "admin", (t[6], t[7]))
    check("initTable 不给 tpl_category/gen_type/options 赋值 ⇒ 走 DDL 默认（crud/zip/NULL）",
          t[8] == "crud" and t[9] in ("0", "NULL", "zip") and t[10] == "NULL",
          (t[8], t[9], t[10]))

    cols = mysql("select column_id, column_name, java_field, java_type, is_pk, is_increment,"
                 " is_required, is_insert, is_edit, is_list, is_query, query_type, html_type,"
                 " sort, create_by, column_comment from gen_table_column where table_id=%s"
                 " order by sort" % TABLE_ID)
    db_cols = mysql("select column_name, data_type, column_type, column_key, is_nullable,"
                    " ordinal_position, column_comment from information_schema.columns"
                    " where table_schema=database() and table_name='%s' order by ordinal_position" % TN)
    check("每一列都导入了", len(cols) == len(db_cols), (len(cols), len(db_cols)))
    by_name = {c[1]: c for c in cols}
    bad_pk = [c[1] for c in cols if c[4] != ("1" if (c[1]) in [d[0] for d in db_cols if d[3] == "PRI"] else "0")]
    check("is_pk 与 information_schema 的 column_key 一致", not bad_pk, bad_pk[:4])
    check("is_insert 对**每一列**都是 '1'（包括主键和 del_flag）",
          all(c[7] == "1" for c in cols), sorted({c[7] for c in cols}))
    check("主键列的 is_edit/is_list/is_query 是 NULL（Java 从不写 '0'）",
          all(c[8] == "NULL" and c[9] == "NULL" and c[10] == "NULL" for c in cols if c[4] == "1"),
          [(c[1], c[8], c[9], c[10]) for c in cols if c[4] == "1"][:2])
    for special in ["id", "create_by", "create_time", "del_flag", "update_by", "update_time", "remark"]:
        if special in by_name:
            c = by_name[special]
            exp_edit = "NULL" if special in ("id", "create_by", "create_time", "del_flag") else "1"
            exp_list = "NULL" if special in ("id", "create_by", "create_time", "del_flag",
                                             "update_by", "update_time") else "1"
            exp_query = "NULL"
            check("列 %s 的 is_edit/is_list/is_query 按三张 NOT_* 名单" % special,
                  (c[8], c[9], c[10]) == (exp_edit, exp_list, exp_query),
                  (c[8], c[9], c[10], "expect", exp_edit, exp_list, exp_query))
    name_cols = [c for c in cols if c[1].lower().endswith("name")]
    qt_default = mysql("select column_default from information_schema.columns"
                       " where table_schema=database() and table_name='gen_table_column'"
                       " and column_name='query_type'")[0][0]
    check("*name 列的 query_type 是 LIKE；其余列**整条不写** ⇒ 落到 DDL 默认值（Java 同样）",
          all(c[11] == "LIKE" for c in name_cols)
          and all(c[11] == qt_default for c in cols if not c[1].lower().endswith("name")),
          [(c[1], c[11]) for c in cols][:6] + [("default", qt_default)])
    mismatch = []
    for c in cols:
        d = next((x for x in db_cols if x[0] == c[1]), None)
        if not d:
            mismatch.append(("缺列", c[1]))
            continue
        if str(c[13]) != d[5]:
            mismatch.append(("sort", c[1], c[13], d[5]))
        if (c[6] == "1") != (d[4] == "NO" and d[3] != "PRI"):
            mismatch.append(("is_required", c[1], c[6], d[3], d[4]))
        if c[15] != (d[6] if d[6] != "NULL" else "NULL") and not (c[15] == "NULL" and d[6] == ""):
            mismatch.append(("column_comment", c[1], repr(c[15]), repr(d[6])))
    check("sort=ordinal_position、is_required 只在 not-null 且非主键时为 '1'、comment 原样",
          not mismatch, mismatch[:4])

    types = []
    for c in cols:
        d = next((x for x in db_cols if x[0] == c[1]), None)
        if not d:
            continue
        dt = d[1]
        if dt in ("char", "varchar", "nvarchar", "varchar2"):
            exp = ("String", "textarea" if (d[2] != "NULL" and _num(d[2]) >= 500) else "input")
        elif dt in ("text", "tinytext", "mediumtext", "longtext"):
            exp = ("String", "textarea")
        elif dt in ("datetime", "date", "time", "timestamp"):
            exp = ("Date", "datetime")
        elif dt in ("int", "bigint", "smallint", "tinyint", "mediumint", "float", "double", "decimal"):
            n = _num(d[2])
            if d[2].startswith("decimal") and "(" in d[2] and _scale(d[2]) > 0:
                jt = "BigDecimal"
            elif "(" not in d[2] or n > 10:
                jt = "Long"
            else:
                jt = "Integer"
            exp = (jt, "input")
        else:
            exp = (c[3], c[12])   # 未知类型：javaType 默认 String、htmlType 不赋值
        if c[1].lower().endswith("status"):
            exp = (exp[0], "radio")
        elif c[1].lower().endswith(("type", "sex")):
            exp = (exp[0], "select")
        elif c[1].lower().endswith("image"):
            exp = (exp[0], "imageUpload")
        elif c[1].lower().endswith("file"):
            exp = (exp[0], "fileUpload")
        elif c[1].lower().endswith("content"):
            exp = (exp[0], "editor")
        if (c[3], c[12]) != exp:
            types.append((c[1], d[2], (c[3], c[12]), exp))
    check("java_type / html_type 与 GenUtils 的映射表一致（含 htmlType 覆盖链）",
          not types, types[:5])

    st2, j2 = js("/tool/gen/%s" % TABLE_ID)
    info = (j2.get("data") or {}).get("info") or {}
    check("导入结果能被 /tool/gen/{tableId} 读回（跨端点一致）",
          info.get("tableName") == TN and info.get("className") == t[1],
          (info.get("tableName"), info.get("className")))

    # ---- PUT /tool/gen ----
    tid2 = TABLE_ID
    body = json.dumps({"tableId": int(tid2), "tableName": TN, "tableComment": "改过的注释",
                       "className": "X", "tplCategory": "crud", "functionName": "fn",
                       "genPath": "/x", "updateBy": "qoder"})
    st3, j3 = js("/tool/gen", method=PUT, body=body, ctype=JSON_CT)
    check("PUT /tool/gen 200 且无 data", st3 == 200 and list(j3.keys()) == ["msg", "code"], j3)
    after = mysql("select table_comment, options, remark, update_by, gen_path, class_name,"
                  " function_name from gen_table where table_id=%s" % tid2)[0]
    check("body 不带 params ⇒ options 被重新序列化成 '{}'（原值被抹掉）",
          after[1] == "{}", repr(after[1]))
    check("未出现在 body 里的列不被更新（<if> 生效），出现的按非空写入",
          after[0] == "改过的注释" and after[4] == "/x" and after[5] == "X" and after[6] == "fn",
          after)
    check("remark 不在 body 里 ⇒ 不写（<if test=\"remark != null\">）", after[2] == "NULL", after[2])

    one_col = mysql("select column_id, column_name from gen_table_column where table_id=%s"
                    " and column_name <> 'id' limit 1" % tid2)[0]
    # 这个 body 必须真的改掉 gen_table 一行：Java 的 `if (row > 0)` 用的是 MySQL 的
    # **changed-rows** 语义，同一秒内提交同样的值会返回 0 ⇒ 列的更新被整批静默跳过。
    # 这里带一个每次不同的 tableComment，保证 row>0。
    js("/tool/gen", method=PUT,
       body=json.dumps({"tableId": int(tid2), "tableComment": "wipe-%d" % int(time.time() * 1000),
                        "columns": [
                            {"columnId": int(one_col[0]), "columnName": one_col[1],
                             "javaField": "x"}]}),
       ctype=JSON_CT)
    wiped = mysql("select column_comment, java_type, is_edit, dict_type, html_type"
                  " from gen_table_column where column_id=%s" % one_col[0])[0]
    check("updateGenTableColumn 的无条件赋值：body 没带的字段被写成 NULL",
          wiped == ["NULL", "NULL", "NULL", "NULL", "NULL"], wiped)
    _st5, j5 = js("/tool/gen", method=PUT, body=json.dumps({"tableId": int(tid2), "columns": [
        {"columnId": int(one_col[0])}]}), ctype=JSON_CT)
    check("columns[].javaField 的 @NotBlank ⇒ \"Java属性不能为空\"",
          j5.get("code") == 500 and j5.get("msg") == "Java属性不能为空", j5)
    _st6, j6 = js("/tool/gen", method=PUT, body=json.dumps(
        {"tableId": int(tid2), "tplCategory": "tree"}), ctype=JSON_CT)
    check("tplCategory=tree 且没有 params ⇒ 树编码字段不能为空",
          j6.get("msg") == "树编码字段不能为空", j6)
    _st7, j7 = js("/tool/gen", method=PUT, body=json.dumps(
        {"tableId": int(tid2), "tplCategory": "tree",
         "params": {"treeCode": "a", "treeParentCode": "b"}}), ctype=JSON_CT)
    check("只补两个 ⇒ 树名称字段不能为空（三条按顺序判，只有第一条失败的会返回）",
          j7.get("msg") == "树名称字段不能为空", j7)
    _st8, j8 = js("/tool/gen", method=PUT, body=json.dumps(
        {"tableId": int(tid2), "tplCategory": "sub", "subTableName": ""}), ctype=JSON_CT)
    check("tplCategory=sub 时子表校验**不可达**（Java 把它嵌在 tree 分支里）⇒ 照样成功",
          j8.get("code") == 200, j8)

    # ---- synchDb（赶在导两次之前，此时同名只有一行） ----
    _st9, j9 = js("/tool/gen/synchDb/" + urllib.parse.quote(TN + "_not_exist_at_all"))
    check("表名不存在 ⇒ NPE（而不是那句友好提示）",
          j9.get("code") == 500 and "getColumns" in str(j9.get("msg")), j9)
    gone = mysql("select column_id, column_name from gen_table_column where table_id=%s"
                 " and column_name <> 'id' limit 1" % tid2)[0]
    mysql("delete from gen_table_column where column_id=%s" % gone[0])
    mysql("insert into gen_table_column (table_id, column_id, column_name, java_field, java_type,"
          " create_time) values (%s, 999999901, 'zzz_hand_added_col', 'zzzHandAddedCol', 'String',"
          " sysdate())" % tid2)
    keep = mysql("select column_id from gen_table_column where table_id=%s and column_name='remark'"
                 " limit 1" % tid2)
    if keep:
        mysql("update gen_table_column set java_type='XXX_手工改过' where column_id=%s" % keep[0][0])
    st10, j10 = js("/tool/gen/synchDb/" + urllib.parse.quote(TN))
    check("synchDb 200 + code:200 且无 data",
          st10 == 200 and list(j10.keys()) == ["msg", "code"] and j10.get("code") == 200, j10)
    names = {r[0] for r in mysql("select column_name from gen_table_column where table_id=%s" % tid2)}
    check("库里已经没有的列（手加的）被删掉", "zzz_hand_added_col" not in names, sorted(names)[:6])
    check("被删掉的那一列重新补回来了", gone[1] in names, gone[1])
    if keep:
        jt = mysql("select java_type from gen_table_column where table_id=%s and column_name='remark'"
                   % tid2)[0][0]
        check("已存在的列**从不更新**：手工改过的 java_type 仍然是改后的值", jt == "XXX_手工改过", jt)
    dup = mysql("select column_id from gen_table_column where column_id=999999901")
    check("synchDb 之后手加列确实不在（同上一条，独立确认）", not dup, dup)

    # ---- 导两次：Java 没有"已存在就跳过"；之后 synchDb 会撞 TooManyResults ----
    js("/tool/gen/importTable?tables=" + urllib.parse.quote(TN), method=POST)
    two = mysql("select count(1) from gen_table where table_name='%s'" % TN)
    check("重复制品没有去重：同一张表导两次 = 2 行（Java 原样）", two and two[0][0] == "2", two)
    _st12, j12 = js("/tool/gen/synchDb/" + urllib.parse.quote(TN))
    check("导过两次之后再 synchDb ⇒ MyBatis selectOne 抛 TooManyResults ⇒ code:500",
          j12.get("code") == 500 and "selectOne" in str(j12.get("msg")), j12)

    st11, raw11 = call("/tool/gen/importTable?tables=" + urllib.parse.quote(TN), method="POST", token="")
    check("无 token ⇒ HTTP 200 + body code 401",
          json.loads(raw11.decode("utf-8")).get("code") == 401, raw11[:60])
finally:
    for sql in ("delete from gen_table_column where table_id in"
                " (select table_id from gen_table where table_name='%s')" % TN,
                "delete from gen_table where table_name='%s'" % TN,
                "delete from gen_table_column where column_id=999999901",
                "delete from gen_table_column where table_id=%s" % TABLE_ID,
                "delete from gen_table where table_id=%s" % TABLE_ID):
        try:
            mysql(sql)
        except Exception as e:                       # noqa: BLE001
            print("# 清理语句失败: %r" % (e,))

after_t = {r[0] for r in mysql("select table_id from gen_table")}
after_c = {r[0] for r in mysql("select column_id from gen_table_column")}
check("清理后 gen_table 与调用前一致", after_t == before_tables, sorted(after_t - before_tables))
check("清理后 gen_table_column 与调用前一致", after_c == before_cols, len(after_c - before_cols))

print("----")
print("GEN WRITE: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
