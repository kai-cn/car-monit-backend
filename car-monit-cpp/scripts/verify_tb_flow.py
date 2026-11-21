#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：POST /flow/flowname/tbFlow（模板流程 × is_uint='1' 单位 的笛卡尔积同步）。

库里没有 is_uint='1' 的单位（真实数据全是 '0'），模板流程也没有可用的节点，
所以本脚本自带夹具并在结束时全部删除：
  * 2 个临时单位（sys_dept，新插入行，不改任何既有数据）
  * 1 条临时模板流程（create_by=-1）+ 3 个节点，RETURN_NUM 分别是 NULL / 1 / 99
    —— 正好覆盖 saveFlow 的三个分支：首个节点、按 nodeOrder 找到退回节点、找不到回落首个节点。
断言的是新增行的每个字段与指针，然后调第二次验幂等，最后硬删除本轮所有行。

用法：python scripts/verify_tb_flow.py [port] [token]
"""
import json
import subprocess
import sys
import time
import urllib.error
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
        print("PASS  " + label + ("  |  " + str(detail)[:170] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def mysql(sql):
    cmd = ["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot", "carmonitdb",
           "-N", "-B", "-e", sql]
    r = subprocess.run(cmd, capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace")
        err = "\n".join(l for l in err.splitlines() if "Using a password" not in l)
        raise RuntimeError(err or out)
    return [l.split("\t") for l in out.splitlines()] if out else []


def post_tb(body="{}"):
    r = urllib.request.Request(BASE + "/flow/flowname/tbFlow", method="POST")
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=body.encode("utf-8"), timeout=180) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


TAG = "QODER_TB_%d" % int(time.time() % 100000)
TPL_ID = TAG + "_F"
N1, N2, N3 = TAG + "_N1", TAG + "_N2", TAG + "_N3"
FLOW_KEY = TAG + "_KEY"

before_names = {r[0] for r in mysql("select ID from flow_name")}
before_nodes = {r[0] for r in mysql("select ID from flow_template")}
max_dept = int(mysql("select ifnull(max(DEPT_ID),0) from sys_dept")[0][0])
D1, D2 = max_dept + 1, max_dept + 2

fixtures = False
try:
    mysql(
        "insert into sys_dept (PARENT_ID,ANCESTORS,DEPT_NAME,ORDER_NUM,STATUS,DEL_FLAG,is_uint)"
        " values (0,'0','%sA',1,'0','0','1'),(0,'0','%sB',2,'0','0','1')" % (TAG, TAG))
    dept_rows = mysql("select DEPT_ID from sys_dept where DEPT_NAME like '%s%%'" % TAG)
    depts = sorted(r[0] for r in dept_rows)
    check("夹具单位建好（is_uint=1 会被 Java 的 selectDeptList 捞到）", len(depts) == 2, depts)
    mysql(
        "insert into flow_name (ID,FLOW_KEY,FLOW_TITLE,FLOW_CONTEXT,BUSS_NAME,sort,DEL_FLAG,"
        "create_by,flow_business_type,TENANT_ID) values ('%s','%s','标题X','说明X','业务X',7,'0',-1,'0',NULL)"
        % (TPL_ID, FLOW_KEY))
    for nid, order, rnum in ((N1, 1, "NULL"), (N2, 2, "1"), (N3, 3, "99")):
        mysql("insert into flow_template (ID,FLOW_OID,NODE_ORDER,NODE_NAME,RETURN_NUM,DEL_FLAG,"
              "create_by) values ('%s','%s',%d,'节点%d',%s,'0',-1)" % (nid, TPL_ID, order, order, rnum))
    fixtures = True

    created_before = mysql("select count(1) from flow_name where del_flag='0' and create_by=-1")
    st, hdr, body = post_tb()
    j = json.loads(body.decode("utf-8"))
    check("tbFlow 200", st == 200, (st, body[:120]))
    check("响应是 AjaxResult.success(\"同步成功！\")：AjaxResult 的 HashMap 桶序 msg,code 且没有 data",
          list(j.keys()) == ["msg", "code"] and j.get("code") == 200 and j.get("msg") == "同步成功！", j)
    check("Content-Type 是 application/json;charset=UTF-8",
          hdr.get("Content-Type") == "application/json;charset=UTF-8", hdr.get("Content-Type"))

    after = mysql("select ID, FLOW_KEY, FLOW_TITLE, FLOW_CONTEXT, BUSS_NAME, sort, TENANT_ID,"
                  " FLOW_BUSINESS_TYPE, DEL_FLAG, create_by, eps_id from flow_name")
    new_rows = [r for r in after if r[0] not in before_names]
    # new_rows 里也含脚本自己插的夹具行，按主键排除
    mine = [r for r in new_rows if r[1] == FLOW_KEY and r[0] != TPL_ID]
    check("给 2 个单位各建了 1 条流程", len(mine) == 2,
          [(r[0], r[6]) for r in mine])
    check("新流程的 tenant_id 就是那 2 个 is_uint=1 的单位",
          sorted(r[6] for r in mine) == sorted(depts), (sorted(r[6] for r in mine), depts))
    check("flow_business_type 被强制成 '1'（模板自己是 '0'）",
          mine and all(r[7] == "1" for r in mine), [r[7] for r in mine])
    check("title/context/bussName/sort 照抄模板",
          mine and all((r[2], r[3], r[4], r[5]) == ("标题X", "说明X", "业务X", "7") for r in mine),
          [(r[2], r[3], r[4], r[5]) for r in mine][:1])
    check("del_flag=0 且 create_by 是当前用户（不是模板的 -1）",
          mine and all(r[8] == "0" and r[9] not in ("-1", "NULL") for r in mine),
          [(r[8], r[9]) for r in mine][:1])
    ts_rows = mysql("select ID, create_time, update_time from flow_name where ID in (%s)"
                    % ",".join("'%s'" % r[0] for r in mine))
    check("create_time 与 update_time 完全相同（Java 复用同一个 curDate）",
          all(r[1] == r[2] for r in ts_rows), [(r[0], r[1], r[2]) for r in ts_rows][:1])

    nodes = mysql("select ID, FLOW_OID, PREVIOUS_NODE_OID, NEXT_NODE_OID, RETURN_NODE_OID,"
                  " create_by, DEL_FLAG, EPS_ID, NODE_ORDER from flow_template")
    copies = [n for n in nodes if n[1] in {r[0] for r in mine}]
    check("每个新流程复制了 3 个节点（夹具自己的 3 个不计入）", len(copies) == 6, len(copies))
    check("节点副本 create_by=-2（Java 硬编码）、del_flag=0",
          copies and all(n[5] == "-2" and n[6] == "0" for n in copies),
          sorted({(n[5], n[6]) for n in copies}))
    check("节点副本的 eps_id 是当前人的部门（不是模板的）",
          copies and len({n[7] for n in copies}) == 1 and {n[7] for n in copies} !=
          {n[7] for n in nodes if n[1] == TPL_ID},
          sorted({n[7] for n in copies}))
    by_flow = {}
    for n in copies:
        by_flow.setdefault(n[1], {})[n[8]] = n
    ptr_ok = True
    detail = []
    for fid, per in by_flow.items():
        a, b, c = per.get("1"), per.get("2"), per.get("3")
        if not (a and b and c):
            ptr_ok = False
            detail.append((fid, "缺节点"))
            continue
        # 首个：previous/return='0'，next=第二个；第二个：previous=第一个，next=第三个，
        # return 按 (flowOid,nodeOrder=1) 找到第一个；末个：next='-1'，
        # return 按 nodeOrder=99 找不到 => 回落首个
        want = [(a[2], "0"), (a[3], b[0]), (a[4], "0"),
                (b[2], a[0]), (b[3], c[0]), (b[4], a[0]),
                (c[2], b[0]), (c[3], "-1"), (c[4], a[0])]
        for got, exp in want:
            if got != exp:
                ptr_ok = False
                detail.append((fid, got, exp))
    check("首节点 previous/return='0'、按 returnNum 找到退回节点、"
          "returnNum=99 回落首个、末节点 next='-1'", ptr_ok, detail[:4])

    # 幂等
    _st2, _h2, body2 = post_tb()
    j2 = json.loads(body2.decode("utf-8"))
    names2 = {r[0] for r in mysql("select ID from flow_name")}
    nodes2 = {r[0] for r in mysql("select ID from flow_template")}
    check("第二次仍返回同步成功", j2.get("msg") == "同步成功！", j2)
    check("幂等：没有再插 flow_name",
          names2 == before_names | {r[0] for r in new_rows} | {TPL_ID}, len(names2))
    check("幂等：没有再插 flow_template",
          nodes2 == before_nodes | {n[0] for n in copies} | {N1, N2, N3}, len(nodes2))
finally:
    if fixtures:
        mysql("delete from flow_template where FLOW_OID in (select ID from flow_name where ID like '%s%%')"
              % TAG)
        mysql("delete from flow_template where ID like '%s%%'" % TAG)
        mysql("delete from flow_name where ID like '%s%%'" % TAG)
        # 本轮复制出来的行主键是新生成的，只能按"调用前快照之外 + 属于本轮模板/夹具"来删
        leftover = [r[0] for r in mysql("select ID from flow_name") if r[0] not in before_names]
        if leftover:
            mysql("delete from flow_template where FLOW_OID in (%s)"
                  % ",".join("'%s'" % i for i in leftover))
            mysql("delete from flow_name where ID in (%s)" % ",".join("'%s'" % i for i in leftover))
        mysql("delete from sys_dept where DEPT_NAME like '%s%%'" % TAG)

left_n = [r[0] for r in mysql("select ID from flow_name") if r[0] not in before_names]
left_t = [r[0] for r in mysql("select ID from flow_template") if r[0] not in before_nodes]
left_d = mysql("select DEPT_ID from sys_dept where DEPT_NAME like '%s%%'" % TAG)
check("清理后 flow_name 与调用前一致", not left_n, left_n[:3])
check("清理后 flow_template 与调用前一致", not left_t, left_t[:3])
check("清理后没有残留夹具单位", not left_d, left_d)

print("----")
print("TB FLOW: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
