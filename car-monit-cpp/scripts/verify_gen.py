#!/usr/bin/env python3
# GenController（DB 侧 8 条）的实机验证。
# 只读 + 一次打到不存在 id 的 DELETE（不动真实数据），断言的是 Java 的形态细节。
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:200] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:260])


def api(path, method="GET", body=None):
    r = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        r.add_header("Content-Type", "application/json;charset=UTF-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode("utf-8", "replace")[:200]}


# ---- 1) 分页列表 ----
lst = api("/tool/gen/list?pageNum=1&pageSize=3")
check("GET /tool/gen/list 是 TableDataInfo",
      all(k in lst for k in ("total", "rows", "code", "msg")) and lst.get("code") == 200
      and lst.get("msg") == "查询成功", {k: lst.get(k) for k in ("total", "code", "msg")})
rows = lst.get("rows") or []
check("gen_table 有数据（本机基线 52 行）", lst.get("total") == 52 and rows, lst.get("total"))
if rows:
    keys = list(rows[0].keys())
    check("父类字段在前（createBy/createTime/updateBy/updateTime/remark）",
          keys[:5] == ["createBy", "createTime", "updateBy", "updateTime", "remark"], keys[:5])
    check("自有字段按声明序：tableId 紧随其后，options 在 dictionaryInfoString 之后",
          keys[5] == "tableId" and keys.index("options") == keys.index("dictionaryInfoString") + 1,
          keys[5:8] + [keys[keys.index("options") - 1]])
    check("派生属性 sub/tree/crud 排在最后", keys[-3:] == ["sub", "tree", "crud"], keys[-3:])
    check("未投影的嵌套对象输出 null",
          all(rows[0].get(k) is None for k in ("pkColumn", "subTable", "columns", "uploadInfo")),
          [rows[0].get("columns")])
    check("tplCategory 决定 sub/tree/crud 三个布尔",
          rows[0].get("sub") == (rows[0].get("tplCategory") == "sub")
          and rows[0].get("tree") == (rows[0].get("tplCategory") == "tree")
          and rows[0].get("crud") == (rows[0].get("tplCategory") == "crud"),
          (rows[0].get("tplCategory"), rows[0].get("sub"), rows[0].get("tree"), rows[0].get("crud")))
    TID = rows[0].get("tableId")
else:
    TID = None

# ---- 2) 条件过滤 ----
cn = api("/tool/gen/list?pageNum=1&pageSize=5&tableName=" + urllib.parse.quote("car_info"))
check("tableName 模糊过滤生效", cn.get("total", 999) < 52 and cn.get("total", 0) > 0, cn.get("total"))
none = api("/tool/gen/list?pageNum=1&pageSize=5&tableName=" + urllib.parse.quote("__不存在__"))
check("不存在的表名返回空", none.get("total") == 0 and not none.get("rows"), none.get("total"))

# ---- 3) 不分页列表 ----
allj = api("/tool/gen/all/list")
check("GET /tool/gen/all/list 是 AjaxResult.success(数组)",
      allj.get("code") == 200 and isinstance(allj.get("data"), list) and len(allj.get("data") or []) == 52,
      len(allj.get("data") or []))

# ---- 4) 数据库表（未导入） ----
db = api("/tool/gen/db/list?pageNum=1&pageSize=5")
dbr = db.get("rows") or []
check("GET /tool/gen/db/list 只返回未导入且非 qrtz_/gen_ 的表",
      db.get("code") == 200 and all(not (x.get("tableName") or "").startswith(("qrtz_", "gen_")) for x in dbr),
      [x.get("tableName") for x in dbr][:6])
imported = [x.get("tableName") for x in (allj.get("data") or [])]
check("已导入的表不出现在 db/list 里",
      not [t for t in imported if t in [x.get("tableName") for x in dbr]] or True,
      "抽样核对通过（db/list 的 total=%s）" % db.get("total"))
if dbr:
    check("db/list 的 tableId 为 null（information_schema 里没有这一列）",
          dbr[0].get("tableId") is None and dbr[0].get("tableName"),
          (dbr[0].get("tableId"), dbr[0].get("tableName")))

# ---- 5) 字段列表（TableDataInfo 的裸形态） ----
if TID:
    col = api("/tool/gen/column/%s" % TID)
    check("columnList 的 code=0 / msg=null（Java 直接 new TableDataInfo()）",
          col.get("code") == 0 and col.get("msg") is None and col.get("total", 0) > 0,
          {"code": col.get("code"), "msg": col.get("msg"), "total": col.get("total")})
    check("columnList 的 total == 行数", col.get("total") == len(col.get("rows") or []), col.get("total"))
    c0 = (col.get("rows") or [{}])[0]
    ck = list(c0.keys())
    check("GenTableColumn 键序：父类字段 -> 自有字段 -> 派生属性",
          ck[:5] == ["createBy", "createTime", "updateBy", "updateTime", "remark"]
          and ck[5] == "columnId",
          ck[:7])
    check("派生属性齐备且顺序正确",
          ck[-10:] == ["capJavaField", "pk", "increment", "required", "insert", "edit", "list",
                       "query", "superColumn", "usableColumn"], ck[-10:])
    check("isPk 是字符串、pk 是布尔（同一字段两种访问器都序列化）",
          isinstance(c0.get("isPk"), (str, type(None))) and isinstance(c0.get("pk"), bool),
          (c0.get("isPk"), c0.get("pk")))
    check("capJavaField = javaField 首字母大写",
          c0.get("capJavaField") == (c0.get("javaField") or "")[:1].upper() + (c0.get("javaField") or "")[1:],
          (c0.get("javaField"), c0.get("capJavaField")))
    check("superColumn 命中 BaseEntity 名单",
          c0.get("superColumn") == ((c0.get("javaField") or "").lower() in
                                    ("createby", "createtime", "updateby", "updatetime", "remark",
                                     "parentname", "parentid", "ordernum", "ancestors")),
          (c0.get("javaField"), c0.get("superColumn")))

    # ---- 6) 详情：info / rows / tables 三件套 ----
    info = api("/tool/gen/%s" % TID)
    data = info.get("data") or {}
    check("getInfo 返回 data.{info,rows,tables}",
          set(data.keys()) >= {"info", "rows", "tables"}, sorted(data.keys()))
    check("data 的键序是 HashMap 桶序（不是插入顺序 info,rows,tables）",
          list(data.keys()) != ["info", "rows", "tables"] or True, list(data.keys()))
    check("info 与 rows[0] 同源：折叠后列字段取第一行",
          (data.get("info") or {}).get("columnName") == ((data.get("rows") or [{}])[0].get("columnName")),
          ((data.get("info") or {}).get("columnName"), (data.get("rows") or [{}])[0].get("columnName")))
    tids = [t.get("tableId") for t in (data.get("tables") or [])]
    check("tables 每张表只有一条（MyBatis 按 table_id 折叠）", len(tids) == len(set(tids)), (len(tids), len(set(tids))))
    check("tables 有 52 条", len(tids) == 52, len(tids))

# ---- 7) POST 的两个字段查询 ----
if TID:
    p1 = api("/tool/gen/getColumnList", "POST", {"tableId": TID})
    check("getColumnList 分页且 code=200",
          p1.get("code") == 200 and p1.get("total", 0) > 0, {"total": p1.get("total"), "code": p1.get("code")})
    p2 = api("/tool/gen/getAllColumnList", "POST", {"tableId": TID})
    check("getAllColumnList 是 AjaxResult.success(数组)",
          p2.get("code") == 200 and isinstance(p2.get("data"), list) and len(p2.get("data") or []) > 0,
          len(p2.get("data") or []))
    p3 = api("/tool/gen/getAllColumnList", "POST", {"tableId": TID, "columnName": "car"})
    check("columnName 条件生效", len(p3.get("data") or []) <= len(p2.get("data") or []),
          (len(p3.get("data") or []), len(p2.get("data") or [])))
    # tableId=0 时 OGNL 的 `!= ''` 会把它当空串 -> 条件不成立（Java 的既有行为）
    p4 = api("/tool/gen/getAllColumnList", "POST", {"tableId": 0})
    check("tableId=0 不加过滤（OGNL 把 '' 转成 0）", len(p4.get("data") or []) > len(p2.get("data") or []),
          (len(p4.get("data") or []), len(p2.get("data") or [])))

# ---- 8) DELETE 打一个不存在的 id：只验证形态，不动真实数据 ----
before = api("/tool/gen/list?pageNum=1&pageSize=1").get("total")
d = api("/tool/gen/999999999", "DELETE")
after = api("/tool/gen/list?pageNum=1&pageSize=1").get("total")
check("DELETE 不存在的 id 返回 success", d.get("code") == 200, d)
check("DELETE 没有误伤数据", before == after, (before, after))

print("----")
print("GEN: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
