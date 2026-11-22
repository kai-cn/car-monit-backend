# -*- coding: utf-8 -*-
"""写接口（POST -> 详情 -> PUT -> DELETE）双端生命周期回归。

共用一个 MySQL、各用各的 Redis DB：
  * 每个资源从 Java 的 /list 取一行真实数据做模板，两端各插一条 PARITY_* 标记记录；
  * 唯一列用不同随机盐，避免同一张表上互相撞唯一键；比对时把标记值/主键/随机数字屏蔽；
  * 定位新增行改用 SQL 按标记值查（列表接口有树形与数据权限过滤，回显不可靠）；
  * 结束后逐表扫描字符列，把 PARITY 行硬删干净；
  * 新增：每步之后核对「Go 的写只落 db2、Java 的写只落 db0」，防止缓存串号。

用法:
  python scripts/parity/compare_write.py                 # 全部资源
  python scripts/parity/compare_write.py /system/config   # 指定资源
  python scripts/parity/compare_write.py --clean          # 只清理
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402

TEXT_TYPES = ("char", "varchar", "tinytext", "text", "mediumtext", "longtext", "json")
MARK = pp.MARK
PAT = MARK + "%"

# 列表行 -> 请求体时要丢的键（嵌套结构、审计列、派生列、密码类）
DROP_KEYS = {
    "params", "rows", "total", "data", "columns", "tables", "info", "checkList",
    "trailList", "carExceptRecordList", "carAduitFreeList", "dictionaryInfoList",
    "subTable", "pkColumn", "children", "roles", "dept", "menuIds", "deptIds",
    "roleIds", "postIds", "businessTypes", "options", "createInfo", "createTimeStr",
    "inTimeStr", "outTimeStr", "flag", "nextValidTime", "raodTrailList",
    "trailDevCountBO", "password", "confirmPassword", "salt", "loginIp", "loginDate",
    "delFlag", "createBy", "createTime", "updateBy", "updateTime", "admin",
    "menuCheckStrictly", "deptCheckStrictly", "searchValue", "dataScope",
}
SKIP_KEYS = {"id", "uuid", "bigId", "agentPk", "operId", "infoId", "fid"}
UNIQ_KEYS = {
    "configKey", "dictType", "postCode", "userName", "roleKey", "tableName",
    "className", "fwqbm", "carNo", "noticeTitle", "dictName", "configName",
    "deptName", "menuName", "roleName", "postName", "whiteName", "ruleName",
    "flowName", "name", "title", "code", "nickName", "linkman", "phone",
    "tollName", "sectionName", "gantryName", "lxbh",
}

RESOURCES = [
    {"base": "/system/dict/type", "pk": "dictId", "table": "sys_dict_type"},
    {"base": "/system/dict/data", "pk": "dictCode", "table": "sys_dict_data"},
    {"base": "/system/config", "pk": "configId", "table": "sys_config"},
    {"base": "/system/notice", "pk": "noticeId", "table": "sys_notice"},
    {"base": "/system/post", "pk": "postId", "table": "sys_post"},
    # dept 的 parentId 必须真实存在（Java 直接 parentBO.getTreeLeavel()，缺父即 NPE）；
    # subCode = 插入前同级数量 + 1，同库并行后端必然多算 1，故忽略该列。
    {"base": "/system/dept", "pk": "deptId", "table": "sys_dept",
     "extra": {"parentId": 0}, "ignore": ["subCode"]},
    {"base": "/system/menu", "pk": "menuId", "table": "sys_menu", "keep": ["parentId"]},
    # 角色必须带 menuIds/deptIds（Java 无空判断，缺省即 NPE）
    {"base": "/system/role", "pk": "roleId", "table": "sys_role",
     "extra": {"menuIds": [], "deptIds": []}},
    # Java 的 SqlLogInterceptor 会把 BCrypt 串当正则替换，新增用户在 Java 侧必然 500
    {"base": "/system/user", "pk": "userId", "table": "sys_user",
     "keep": ["deptId"],
     "extra": {"password": "__SET_CARMONIT_ADMIN_PASSWORD__x", "phonenumber": "19@NUM@", "email": "@NUM@1@t.io"}},
    {"base": "/base/config", "pk": "id", "table": "car_warning_config"},
    {"base": "/base/configServiceArea", "pk": "id", "table": "base_config_service_area"},
    {"base": "/base/section", "pk": "id", "table": "ods_szdn_section"},
    {"base": "/base/toll", "pk": "id", "table": "ods_szdn_toll"},
    {"base": "/base/gantry", "pk": "id", "table": "ods_szdn_gantry"},
    {"base": "/base/org", "pk": "bigId", "table": "ods_yhgl_v_base_org"},
    {"base": "/base/geometry", "pk": "id", "table": "geometry"},
    {"base": "/manager/carinfo", "pk": "id", "table": "car_info"},
    {"base": "/manager/whiteinfo", "pk": "id", "table": "car_white_info"},
    {"base": "/manager/warningrule", "pk": "id", "table": "car_warning_rule"},
    {"base": "/manager/querylog", "pk": "id", "table": "car_query_log"},
    {"base": "/manager/suspiciouscheck", "pk": "id", "table": "car_suspicious_check"},
    {"base": "/manager/carsuspiciousback", "pk": "id", "table": "car_suspicious_back"},
    {"base": "/manager/cartrackinfo", "pk": "id", "table": "car_track_info"},
    {"base": "/manager/busstest", "pk": "id", "table": "buss_test"},
    # 以下表当前无数据，没有样本行可克隆，改用手工请求体
    {"base": "/manager/routeinfo", "pk": "id", "table": "car_route_info", "marker": "carNo",
     "body": {"carId": "@MARK@_ci_@SALT@", "carNo": "@MARK@_no_@SALT@", "carType": "1",
              "carVehicle": "2", "carNum": 2, "startAddress": "起点", "startLongitude": "115.1",
              "startLatitude": "26.1", "endAddress": "终点", "endLongitude": "116.1",
              "endLatitude": "27.1", "status": "0", "remark": "@MARK@_rm_@SALT@"}},
    {"base": "/manager/routedetail", "pk": "id", "table": "car_route_detail", "marker": "carNo",
     "body": {"routeId": "@MARK@_rt_@SALT@", "carId": "@MARK@_ci_@SALT@",
              "carNo": "@MARK@_no_@SALT@", "dataSource": "1", "dataSourceName": "来源",
              "roadSectionId": "1", "roadSectionName": "路段", "status": "0",
              "remark": "@MARK@_rm_@SALT@"}},
    {"base": "/manager/feerecord", "pk": "id", "table": "car_fee_record", "marker": "carNo",
     "body": {"exceptId": "@MARK@_ex_@SALT@", "carId": "@MARK@_ci_@SALT@",
              "carNo": "@MARK@_no_@SALT@", "carType": "1", "carVehicle": "2",
              "inStationId": "1", "inStation": "入口", "inTime": "2026-01-02 10:00:00",
              "outStationId": "2", "outStation": "出口", "outTime": "2026-01-02 11:00:00",
              "chargeType": "1", "amount": 12.5, "status": "0",
              "remark": "@MARK@_rm_@SALT@"}},
    {"base": "/manager/splitrecord", "pk": "id", "table": "car_split_record", "marker": "carNo",
     "body": {"carId": "@MARK@_ci_@SALT@", "carNo": "@MARK@_no_@SALT@", "carType": "1",
              "carVehicle": "2", "passType": "1", "inStationId": "1", "inStation": "入口",
              "inTime": "2026-01-02 10:00:00", "outStationId": "2", "outStation": "出口",
              "outTime": "2026-01-02 11:00:00", "amount": 3.5, "status": "0"}},
    {"base": "/manager/carwarning", "pk": "id", "table": "car_warning_info", "marker": "carNo",
     "body": {"carId": "@MARK@_ci_@SALT@", "carNo": "@MARK@_no_@SALT@", "carType": "1",
              "carVehicle": "2", "carNum": 1, "inStationId": "1", "inStation": "入口",
              "inTime": "2026-01-02 10:00:00", "gantryStationId": "2", "gantrytStation": "门架",
              "gantryTime": "2026-01-02 10:30:00", "roadCode": "R1", "roadName": "高速",
              "sectionCode": "S1", "sectionName": "路段", "status": "0"}},
    {"base": "/flow/flowname", "pk": "id", "table": "flow_name", "marker": "flowKey",
     "body": {"flowKey": "@MARK@_fk_@SALT@", "flowTitle": "@MARK@_ft_@SALT@",
              "flowContext": "内容", "bussName": "@MARK@_bn_@SALT@", "tenantName": "租户",
              "flowBusinessType": "1"}},
    {"base": "/flow/flowlist", "pk": "id", "table": "flow_list", "marker": "billOid",
     "body": {"billOid": "@MARK@_bo_@SALT@", "bussType": "1", "taskId": "@MARK@_tk_@SALT@",
              "flowRuid": "@MARK@_fr_@SALT@", "currentOid": "1", "shUser": "1",
              "shKey": "k", "shValue": "v"}},
    {"base": "/flow/flowtemplate", "pk": "id", "table": "flow_template", "marker": "nodeKey",
     "body": {"flowOid": "@MARK@_fo_@SALT@", "flowType": "1", "nodeOrder": 1,
              "nodeKey": "@MARK@_nk_@SALT@", "nodeName": "@MARK@_nn_@SALT@",
              "configType": "1", "configId": "1", "configName": "配置", "returnNum": 0}},
    # 覆盖率盘点（check_coverage.py）里剩下的纯 CRUD 资源族，都是 POST/PUT/DELETE base
    # + GET base/:id 齐全的那批：新增一律用标记值定位，删除只删自己建行。
    {"base": "/manager/exceptrecord", "pk": "id", "table": "car_except_record", "marker": "carNo"},
    {"base": "/manager/gantrycar", "pk": "id", "table": "gantry_car"},
    {"base": "/manager/gantrytrade", "pk": "id", "table": "gantry_trade_info"},
    {"base": "/manager/suspicious", "pk": "id", "table": "car_suspicious",
     "actions": [("PUT", "/check", {"isExcept": "0"})]},
    {"base": "/manager/aduitfree", "pk": "id", "table": "car_aduit_free"},
    # 这三张 flow 表在共享库里是空的（"无样本行"），必须自带 body 才跑得起来。
    {"base": "/flow/applyinfo", "pk": "id", "table": "flow_apply_info", "marker": "billOid",
     "body": {"billOid": "@MARK@_bo_@SALT@", "bussType": "1", "flowRuid": "@MARK@_fr_@SALT@",
              "msgTitle": "@MARK@_mt_@SALT@", "msgContext": "内容", "msgType": "1",
              "msgUrl": "http://parity", "applyName": "@MARK@_an_@SALT@",
              "currentOid": "1", "flowStatus": "1"}},
    {"base": "/flow/currentnode", "pk": "id", "table": "flow_current_node", "marker": "nodeKey",
     "body": {"flowOid": "1", "currentOid": "1", "nodeOrder": 1,
              "nodeKey": "@MARK@_nk_@SALT@", "nodeName": "@MARK@_nn_@SALT@",
              "configType": "1", "configId": "1", "configName": "配置",
              "billOid": "@MARK@_bo_@SALT@"}},
    {"base": "/flow/messagedispose", "pk": "id", "table": "flow_message_dispose",
     "marker": "bussName",
     "body": {"mid": "@MARK@_mid_@SALT@", "bussId": "@MARK@_bi_@SALT@",
              "bussName": "@MARK@_bn_@SALT@", "msgStatus": "1", "disposeOther": "0"}},
    # 这三张 dwd 表的主键是 agent_pk（Java 的 DeleteMapping 是 /{agentPks}），
    # locate() 会把 pk 蛇化成列名，所以 pk 写 JSON 键 agentPk。
    {"base": "/base/fwqjcxx", "pk": "agentPk", "table": "dwd_lczt_fwqjcxx"},
    {"base": "/base/sfsjcxx", "pk": "agentPk", "table": "dwd_lczt_sfsjcxx"},
    {"base": "/base/sfzjcxx", "pk": "agentPk", "table": "dwd_lczt_sfzjcxx"},
    # 共享库里 sys_upgrade_info 这张表不存在（Java 侧 §9 的缺表族），照样跑一遍：
    # 两端的 POST/PUT/DELETE 都该失败，失败形态属"同为 500 的错误文本"一族。
    # 表不在 ⇒ 取不到样本行，body 只能自带（内容无所谓，重点是两端都要失败在同一处）。
    {"base": "/system/upgradeInfo", "pk": "id", "table": "sys_upgrade_info", "marker": "version",
     "body": {"version": "@MARK@_ver_@SALT@", "content": "内容", "status": "0"}},
]

# 只做导入对拍、没有写生命周期的资源落在这些表里，--clean 时一并扫掉。
EXTRA_CLEAN_TABLES = ("car_except_record",)

NUMS = set()


def snake(name):
    return re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), name)


def num(x):
    """请求体里的数字型取值。

    19 位雪花 id 只能当字符串传：写成 JSON 数字的话，Go 侧 map[string]any 会按 float64
    解码，精度一丢就查不到那行（Java 的 String 字段拿的是原始 token，不受影响）。
    真实浏览器同样存不下 19 位数字，前端只会传字符串，所以这里保守到 15 位以内才转 int。
    """
    s = str(x)
    if s.lstrip("-").isdigit() and len(s.lstrip("-")) <= 15:
        return int(s)
    return s


def fill_tpl(value, salt, digits):
    if not isinstance(value, str):
        return value
    return value.replace("@SALT@", salt).replace("@NUM@", digits).replace("@MARK@", MARK)


def make_tpl(tpl, salt, digits):
    return {k: fill_tpl(v, salt, digits) for k, v in tpl.items()}


def make_body(row, salt, extra=None, keep=(), digits=""):
    body = {}
    for k, v in row.items():
        if k in DROP_KEYS or k in SKIP_KEYS or v is None or k in keep:
            continue
        if k.endswith("Id") or k.endswith("Ids") or isinstance(v, (dict, list)):
            continue
        body[k] = v
    for k in keep:
        if k in row:
            body[k] = row[k]
    tagged = False
    for k in list(body):
        if k in UNIQ_KEYS:
            body[k] = "%s_%s_%s" % (MARK, k[:6], salt)
            tagged = True
    if not tagged:
        body["remark"] = "%s_%s" % (MARK, salt)
    for k, v in (extra or {}).items():
        body[k] = fill_tpl(v, salt, digits)
    return body


def norm(value):
    if isinstance(value, dict):
        return {k: norm(v) for k, v in value.items()}
    if isinstance(value, list):
        return [norm(v) for v in value]
    if isinstance(value, str):
        s = pp.DT_RE.sub("<DT>", value)
        s = pp.UUID_RE.sub("<UUID>", s)
        s = pp.HEX32_RE.sub("<HEX32>", s)
        s = pp.LONG_ID_RE.sub("<ID>", s)
        s = pp.MARK_RE.sub("<PARITY>", s)
        for n in sorted(NUMS, key=len, reverse=True):
            s = s.replace(n, "<NUM>")
        return s
    if isinstance(value, int):
        if str(value) in NUMS:
            return "<NUM>"
        if abs(value) > 10 ** 14:
            return "<ID>"
    return value if not isinstance(value, float) else round(value, 6)


def table_columns(table, only_text=False):
    cond = ("and data_type in ('" + "','".join(TEXT_TYPES) + "')") if only_text else ""
    out = pp.sql("select column_name from information_schema.columns "
                 "where table_schema='carmonitdb' and table_name='" + table + "' " + cond +
                 " order by ordinal_position")
    if out.returncode != 0:
        return None
    return [c for c in out.stdout.split() if c and c != "NULL"]


def locate(table, pk, marker_value):
    cols, text_cols = table_columns(table), table_columns(table, only_text=True)
    if not cols or not text_cols or not marker_value:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_]+", str(marker_value)):
        return None
    pk_col = snake(pk)
    if pk_col not in cols:
        pk_col = "id" if "id" in cols else cols[0]
    where = " or ".join("`" + c + "`='" + str(marker_value) + "'" for c in text_cols)
    rows = pp.sql("select `" + pk_col + "` from `" + table + "` where " + where + " limit 1").stdout.split()
    return rows[0] if rows else None


def run_resource(tk_j, tk_g, res, log):
    base, table = res["base"], res.get("table")
    pk = res.get("pk", "id")
    list_url = "%s%s?pageNum=1&pageSize=1000" % (base, res.get("list", "/list"))
    sj, sg, nj, ng = pp.rand(), pp.rand(), pp.rand_digits(), pp.rand_digits()
    NUMS.update({sj, sg, nj, ng})

    if res.get("body"):
        body = make_tpl(res["body"], sj, nj)
        body_g = make_tpl(res["body"], sg, ng)
    else:
        sample = pp.req(pp.JAVA, list_url, tk_j)
        rows = sample.get("rows") or sample.get("data") or []
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            log.append({"res": base, "step": "sample",
                        "skip": "无样本行 " + json.dumps(sample, ensure_ascii=False)[:150]})
            return
        keep, extra = res.get("keep", ()), res.get("extra")
        body = make_body(rows[0], sj, extra, keep, nj)
        body_g = make_body(rows[0], sg, extra, keep, ng)

    marker_key = res.get("marker") or next((k for k in body if k in UNIQ_KEYS), "remark")

    rj = pp.req(pp.JAVA, base, tk_j, "POST", body)
    rg = pp.req(pp.GO, base, tk_g, "POST", body_g)
    d = pp.diff(norm(rj), norm(rg), "POST")
    if d:
        log.append({"res": base, "step": "POST", "diff": d[:8],
                    "java": json.dumps(rj, ensure_ascii=False)[:260],
                    "go": json.dumps(rg, ensure_ascii=False)[:260]})
    idj = locate(table, pk, body.get(marker_key))
    idg = locate(table, pk, body_g.get(marker_key))
    if idj is None or idg is None:
        log.append({"res": base, "step": "locate",
                    "note": "java=%s go=%s（未能定位新增行，跳过后续步骤）" % (idj, idg)})
        return
    NUMS.update({str(idj), str(idg)})

    detail = res.get("detail", "/%s")
    gj = pp.req(pp.JAVA, base + detail % idj, tk_j)
    gg = pp.req(pp.GO, base + detail % idg, tk_g)
    ignore = set(res.get("ignore", ())) | {pk, "id"}
    d = [x for x in pp.diff(norm(gj), norm(gg), "detail") if x[0].split("/")[-1] not in ignore]
    if d:
        log.append({"res": base, "step": "detail", "diff": d[:8]})

    if res.get("put", True):
        bj, bg = dict(body), dict(body_g)
        bj[pk], bg[pk] = num(idj), num(idg)
        if "remark" in bj:
            bj["remark"] = bg["remark"] = "%s_UPD" % MARK
        else:
            bj[marker_key] = "%s_UP_%s" % (MARK, sj)
            bg[marker_key] = "%s_UP_%s" % (MARK, sg)
        pj = pp.req(pp.JAVA, base, tk_j, "PUT", bj)
        pg = pp.req(pp.GO, base, tk_g, "PUT", bg)
        d = pp.diff(norm(pj), norm(pg), "PUT")
        if d:
            log.append({"res": base, "step": "PUT", "diff": d[:8],
                        "java": json.dumps(pj, ensure_ascii=False)[:260],
                        "go": json.dumps(pg, ensure_ascii=False)[:260]})

    # 业务动作端点（如可疑车辆核实）：只在自己刚建的那一行上做，做完仍由 DELETE 收干净。
    for method, sub, extra in res.get("actions", ()):
        aj, ag = dict(extra), dict(extra)
        aj[pk], ag[pk] = num(idj), num(idg)
        rj = pp.req(pp.JAVA, base + sub, tk_j, method, aj)
        rg = pp.req(pp.GO, base + sub, tk_g, method, ag)
        tag = "%s %s%s" % (method, base, sub)
        d = pp.diff(norm(rj), norm(rg), tag)
        if d:
            log.append({"res": base, "step": tag, "diff": d[:8],
                        "java": json.dumps(rj, ensure_ascii=False)[:260],
                        "go": json.dumps(rg, ensure_ascii=False)[:260]})

    if res.get("delete", True):
        dj = pp.req(pp.JAVA, base + "/%s" % idj, tk_j, "DELETE")
        dg = pp.req(pp.GO, base + "/%s" % idg, tk_g, "DELETE")
        d = pp.diff(norm(dj), norm(dg), "DELETE")
        if d:
            log.append({"res": base, "step": "DELETE", "diff": d[:8],
                        "java": json.dumps(dj, ensure_ascii=False)[:260],
                        "go": json.dumps(dg, ensure_ascii=False)[:260]})


def clean():
    fails = 0
    # 导入用例（compare_import.py）写进这些表，它们没有写生命周期，所以只在这里扫一遍。
    for res in RESOURCES + [{"table": t} for t in EXTRA_CLEAN_TABLES]:
        table = res.get("table")
        cols = table_columns(table, only_text=True)
        if cols is None:
            fails += 1
            print("CLEAN FAIL (schema):", table)
            continue
        if not cols:
            continue
        where = " or ".join("`" + c + "` like '" + PAT + "'" for c in cols)
        out = pp.sql("delete from `" + table + "` where " + where)
        err = out.stderr or ""
        if out.returncode != 0 and "doesn't exist" not in err:
            fails += 1
            print("CLEAN FAIL:", table, err[:150])
    # 测试期间可能写进两端的 PARITY 缓存键
    for db in (pp.JAVA_DB, pp.GO_DB):
        for key in pp.scan(PAT + "*", db=db) + pp.scan("*" + PAT + "*", db=db):
            pp.r("del", key, db=db)
    print("cleanup done, failures=%d" % fails)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    if args.clean:
        clean()
        return
    tk_j, tk_g = pp.login_java(), pp.login_go()
    log = []
    only = set(args.only)
    for res in RESOURCES:
        if only and res["base"] not in only:
            continue
        try:
            run_resource(tk_j, tk_g, res, log)
        except Exception as e:
            log.append({"res": res["base"], "step": "EXC", "err": str(e)[:200]})
        print("done %-32s 累计差异条目 %d" % (res["base"], len(log)))
    clean()
    out = os.path.join(os.environ.get("TEMP", "/tmp"), "write_compare.json")
    json.dump({"entries": len(log), "log": log}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n== 差异汇总 (%d) ==" % len(log))
    for x in log:
        print(json.dumps(x, ensure_ascii=False)[:400])
    print("报告:", out)


if __name__ == "__main__":
    main()
