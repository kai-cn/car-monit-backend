#!/usr/bin/env python3
"""flow 审批三件套的端到端验证（建临时流程 → 走完 → 清理）。

为什么需要它：saveFlowAuit 要跨 flow_current_node / flow_list / flow_message_info /
flow_message_dispose / flow_apply_info 和业务表 buss_test 连续写 6~8 张表，
只看代码或只测错误分支都不足以证明它真的对。

它会插入一批 QODER_FLOW_ 前缀的临时数据，跑完（无论成功失败）一律删掉。
因此**只能在开发库上跑** —— 它会真的写 buss_test / flow_* 这些业务表。

用法：
    python scripts/verify_flow_approval.py --port 9990
前置：Redis 里有可用的 login_tokens:* 会话（脚本自己挑一个，并把它所属用户当审批人）。
"""
import argparse
import json
import os
import subprocess
import sys
import sys as _sys
import time

if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_probe as L  # noqa: E402

BILL = "QODER_FLOW_BILL"
FLOW_NAME_ID = "QODER_FLOW_NAME"
NODE1 = "QODER_FLOW_N1"
NODE2 = "QODER_FLOW_N2"
PREFIXES = (BILL, FLOW_NAME_ID, NODE1, NODE2)


def mysql(sql, db="carmonitdb"):
    cmd = ["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot", db, "-N", "-B", "-e", sql]
    r = subprocess.run(cmd, capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace")
        err = "\n".join(l for l in err.splitlines() if "Using a password" not in l)
        raise RuntimeError(err or out)
    return out


def call(base, path, token, verb, body=None):
    cmd = ["curl", "-s", "--ssl-no-revoke", "-X", verb, "-H", "Authorization: Bearer " + token,
           "-H", "Content-Type: application/json"]
    if body is not None:
        cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    cmd.append(base + path)
    return json.loads(subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace"))


def cleanup():
    """把这次造的数据全部删掉（含审批过程产生的消息与流程记录）"""
    mysql("""
      delete from flow_current_node where BILL_OID = '{b}' or ID in ('{q1}','{q2}');
      delete from flow_list where bill_oid = '{b}';
      delete from flow_message_dispose where mid in (select id from flow_message_info where bill_oid='{b}');
      delete from flow_message_info where bill_oid = '{b}';
      delete from flow_apply_info where bill_oid = '{b}';
      delete from flow_template where ID in ('{n1}','{n2}') or FLOW_OID='{f}';
      delete from flow_name where ID = '{f}';
      delete from buss_test where id = '{b}';
    """.format(b=BILL, f=FLOW_NAME_ID, n1=NODE1, n2=NODE2, q1=NODE1, q2=NODE2))


def seed(user_id, user_name):
    cleanup()  # 上一次异常退出留下的残留
    mysql(
        "insert into buss_test (id, bill_name, flow_status) values ('{b}','qoder自测单据','1');".format(b=BILL))
    mysql("insert into flow_name (ID, FLOW_KEY, FLOW_TITLE, BUSS_NAME, del_flag, create_time)"
          " values ('{f}','qoder_flow_test','迁移自测流程','buss_test','0', now());".format(f=FLOW_NAME_ID))
    mysql("""insert into flow_template (ID, FLOW_OID, NODE_ORDER, NODE_KEY, NODE_NAME,
               NEXT_NODE_OID, PREVIOUS_NODE_OID, CONFIG_TYPE, CONFIG_ID, CONFIG_NAME, del_flag, create_time)
             values ('{n1}','{f}',1,'ks','科室审核','{n2}','0','1','{u}','{un}','0', now()),
                    ('{n2}','{f}',2,'ld','领导审核','-1','{n1}','1','{u}','{un}','0', now());""".format(
        n1=NODE1, n2=NODE2, f=FLOW_NAME_ID, u=user_id, un=user_name))
    mysql("""insert into flow_current_node (ID, FLOW_OID, CURRENT_OID, NODE_ORDER, NODE_KEY, NODE_NAME,
               BILL_OID, AUIT_EMP_OID, AUIT_EMP_NAME, del_flag, create_time)
             values ('{c}','{f}','{n1}',1,'ks','科室审核','{b}','{u}','{un}','0', now());""".format(
        c=NODE1 + "_CUR", n1=NODE1, f=FLOW_NAME_ID, b=BILL, u=user_id, un=user_name))


def state():
    return {
        "node": mysql("select concat(CURRENT_OID,'|',auit_emp_oid) from flow_current_node where bill_oid='%s'" % BILL),
        "flow_status": mysql("select flow_status from buss_test where id='%s'" % BILL),
        "sh_time": mysql("select ifnull(sh_time,'-') from buss_test where id='%s'" % BILL),
        "list_keys": mysql("select group_concat(sh_key order by id) from flow_list where bill_oid='%s'" % BILL),
        "msg2": mysql("select count(1) from flow_message_info where bill_oid='%s' and msg_type='2'" % BILL),
        "msg1": mysql("select count(1) from flow_message_info where bill_oid='%s' and msg_type='1'" % BILL),
        "dispose": mysql("select count(1) from flow_message_dispose d join flow_message_info m on d.mid=m.id"
                         " where m.bill_oid='%s'" % BILL),
        "apply_status": mysql("select flow_status from flow_apply_info where bill_oid='%s'" % BILL),
        "apply_names": mysql("select ifnull(back_col1,'-') from flow_apply_info where bill_oid='%s'" % BILL),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9990)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    base = "http://%s:%d" % (args.host, args.port)

    uuid, info = L.find_live_session(args.port, args.host)
    if not uuid:
        print("!! Redis 里没有可用会话", file=sys.stderr)
        return 2
    token = L.jwt_for(uuid)
    me = json.loads(info)["user"]
    user_id, user_name = me["userId"], me.get("nickName") or me.get("userName")
    print("# 审批人 = %s(%s)" % (user_name, user_id))

    seed(user_id, user_name)
    fails = 0
    try:
        # 1) 缺结论 —— 必须在任何写库之前就返回
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT", {"billOid": BILL})
        ok = r.get("code") == 500 and r.get("msg") == "请填写审核结论！"
        print("%s 缺 shValue -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1

        # 2) 单据不存在
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT",
                 {"billOid": "QODER_NOT_EXIST", "shValue": "1"})
        ok = r.get("msg") == "对不起，该单据已审核，请确定！"
        print("%s 单据不存在 -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1

        # 3) 第一次审核（同意）：应推进到 node2，业务状态 2=审批中
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT",
                 {"billOid": BILL, "shValue": "1", "shContext": "科室同意"})
        ok = r.get("code") == 200 and r.get("msg") == "审核成功！"
        print("%s 一审(同意) -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1
        s = state()
        print("   流转后:", json.dumps(s, ensure_ascii=False))
        checks = [("节点推进到二审", s["node"] == NODE2 + "|" + str(user_id)),
                  ("业务状态=2", s["flow_status"] == "2"),
                  ("审核记录 T", (s["list_keys"] or "") == "T"),
                  ("办理消息 1 条", s["msg2"] == "1"),
                  ("申请单状态=2", s["apply_status"] == "2")]
        for name, cond in checks:
            print("%s   %s" % ("OK " if cond else "FAIL", name))
            fails += 0 if cond else 1

        # 4) 第二次审核（同意，下一节点是 -1）：流程结束，状态 3，盖 sh_time，节点清空
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT",
                 {"billOid": BILL, "shValue": "1", "shContext": "领导同意"})
        s = state()
        checks = [("二审返回审核成功", r.get("msg") == "审核成功！"),
                  ("节点已全部处理完", s["node"] == ""),
                  ("业务状态=3", s["flow_status"] == "3"),
                  ("sh_time 已盖章", s["sh_time"] not in ("-", "", None)),
                  ("审核记录 T,T（两次同意）", s["list_keys"] == "T,T"),
                  ("通知消息 1 条", s["msg1"] == "1"),
                  ("申请单状态=3", s["apply_status"] == "3")]
        for name, cond in checks:
            print("%s %s" % ("OK " if cond else "FAIL", name))
            fails += 0 if cond else 1

        # 5) 重复审核（已无节点）→ 回到"该单据已审核"
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT",
                 {"billOid": BILL, "shValue": "1"})
        ok = r.get("msg") == "对不起，该单据已审核，请确定！"
        print("%s 重复审核 -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1

        # 6) 委托：当前无节点，应报"当前流程节点不存在!"（有节点时的委托由 saveFlowAuit 之外覆盖）
        r = call(base, "/flow/currentnode/submitEntrustFlow", token, "POST",
                 {"billOid": BILL, "entrustUserId": str(user_id), "entrustUserName": str(user_name)})
        ok = r.get("msg") == "当前流程节点不存在!"
        print("%s 无节点时委托 -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1

        # 7) 撤销：单据已走完，节点为空 -> 撤销失败
        r = call(base, "/flow/currentnode/submitReturn", token, "POST", {"billOid": BILL})
        ok = r.get("msg") == "撤销失败，该单据已撤销，请确定！"
        print("%s 结束后撤销 -> %s" % ("OK " if ok else "FAIL", json.dumps(r, ensure_ascii=False)[:120]))
        fails += 0 if ok else 1

        # 8) 撤销的正路：重新造一条"仍在第一个节点"的单据
        mysql("delete from flow_current_node where bill_oid='%s'" % BILL)
        mysql("""insert into flow_current_node (ID, FLOW_OID, CURRENT_OID, NODE_ORDER, NODE_KEY, NODE_NAME,
                 BILL_OID, AUIT_EMP_OID, AUIT_EMP_NAME, del_flag, create_time)
                 values ('{c}','{f}','{n1}',1,'ks','科室审核','{b}','{u}','{un}','0', now())""".format(
            c=NODE1 + "_CUR2", f=FLOW_NAME_ID, n1=NODE1, b=BILL, u=user_id, un=user_name))
        before = state()
        r = call(base, "/flow/currentnode/submitReturn", token, "POST", {"billOid": BILL})
        after = state()
        checks = [("撤销返回成功", r.get("msg") == "撤销成功！"),
                  ("节点被清空", after["node"] == ""),
                  ("业务状态回到 1(草稿)", after["flow_status"] == "1"),
                  ("办理消息被打上删除标记",
                   mysql("select ifnull(sum(del_flag='1'),0) from flow_message_info where bill_oid='%s'" % BILL) == "1")]
        for name, cond in checks:
            print("%s %s   [撤销前 %s -> 后 %s]" % ("OK " if cond else "FAIL", name,
                                                    before["node"][:12], after["node"][:12]))
            fails += 0 if cond else 1

        # 9) 事务性：把业务表名改成不存在的表 —— updateFlowTable 会失败，
        #    此前"删节点 + 写消息 + 写申请单"必须整笔回滚（Java 靠 @Transactional）
        mysql("insert into flow_current_node (ID, FLOW_OID, CURRENT_OID, NODE_ORDER, NODE_KEY, NODE_NAME,"
              " BILL_OID, AUIT_EMP_OID, AUIT_EMP_NAME, del_flag, create_time)"
              " values ('{c}','{f}','{n1}',1,'ks','科室审核','{b}','{u}','{un}','0', now())".format(
                  c=NODE1 + "_CUR3", f=FLOW_NAME_ID, n1=NODE1, b=BILL, u=user_id, un=user_name))
        mysql("update flow_name set buss_name='qoder_no_such_table' where ID='%s'" % FLOW_NAME_ID)
        # 基线：这一步之前已经提交的数据不能被动过
        snap = ("select concat("
                " (select count(1) from flow_current_node where bill_oid='%s'),'|',"
                " (select count(1) from flow_message_info where bill_oid='%s'),'|',"
                " (select count(1) from flow_list where bill_oid='%s'),'|',"
                " (select count(1) from flow_apply_info where bill_oid='%s'))" % (BILL, BILL, BILL, BILL))
        before = mysql(snap)
        r = call(base, "/flow/currentnode/saveFlowAuit", token, "PUT",
                 {"billOid": BILL, "shValue": "1"})
        after = mysql(snap)
        ok = r.get("code") == 500 and before == after
        print("%s 中途失败需整笔回滚 (code=%s 前后一致=%s 基线=%s 事后=%s)"
              % ("OK " if ok else "FAIL", r.get("code"), before == after, before, after))
        fails += 0 if ok else 1
    finally:
        cleanup()
        left = mysql("select count(1) from buss_test where id='%s'" % BILL)
        print("# 清理后残留: buss_test=%s flow_name=%s" % (
            left, mysql("select count(1) from flow_name where ID='%s'" % FLOW_NAME_ID)))

    print("FLOW APPROVAL: %s" % ("ALL PASSED" if fails == 0 else "%d FAILED" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
