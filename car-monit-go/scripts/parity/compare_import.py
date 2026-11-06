# -*- coding: utf-8 -*-
"""Excel 导入接口双端回归：同一份 xlsx 上传两端，比对响应与落库结果。

覆盖三个上传端点：
  POST /system/user/importData      POST /manager/carinfo/import
  POST /manager/exceptrecord/import

上传的文件是脚本现造的 inlineStr 单表 xlsx，表头逐字取 Java 侧的导入列
（SysUser 的 @Excel、CarInfoController.initList()、CarExceptRecordController.initListTwo()），
数据行的字符列一律带 PARITY 标记，收尾用 compare_write.py --clean 删干净。

两端共用一个 MySQL，所以每端各用自己的标记值（_J / _G）：否则先跑的那端写进去的行
会被后跑的那端看见，首轮对拍就是这么被污染的。落库对照查的也是这一端自己的标记值
（carNo 是等值条件，所以要用行里那个完整的值，不能只给前缀）。

用法:
  python scripts/parity/compare_import.py [--only 路径或标签片段]
"""
import argparse
import io
import json
import os
import re
import sys
import uuid
import zipfile
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402

MARK = pp.MARK

# initListTwo() 的 21 个标题；空标题是模板里合并单元格的残留，Java 照样拿它当 colName 报错。
EXCEPT_HEADERS = ["序号", "出口收费站", "出口时间", "通行PASSID", "车牌", "交易车型", "车种",
                  "入口站", "入口时间", "漏交通行费类型", "", "交易金额", "", "", "应交金额", "", "",
                  "实际追交金额", "", "", "备注"]
# 真实模板 importCarExcept.xlsx 的前三行：第 1 行标题，第 2 行 initListTwo 表头，
# 第 3 行是合并单元格的子表头 —— 数据从第 4 行（下标 3）才开始。
EXCEPT_TITLE = [["少交高速公路通行费流水明细表"]]
EXCEPT_MID = [["", "", "", "", "", "", "", "", "", "一级类型", "二级类型", "省内", "省外", "小计",
               "省内", "省外", "小计", "省内", "省外", "小计", ""]]

CAR_HEADERS = ["车牌颜色", "车牌号", "车型", "车种", "轴数", "逃费类型", "逃费金额（元）", "备注"]


def except_row(plate="{M}挂", out_t="2025-01-02 10:00:00", in_t="2025-01-01 09:00:00",
               esc="入口少轴", charge="1.00", total="2.00", car_type="货1", remark="{M}备注"):
    """按 initListTwo 的 21 列摆一行流水；只暴露会触发校验差异的几个格子。"""
    return ["1", "出口站A", out_t, "PASS{M}", plate, car_type, "客车",
            "入口站A", in_t, "入口少轴", esc, "", "", charge, "", "", total,
            "", "", "", remark]


def car_row(plate="{M}挂", car_num="2", amount="1.00", color="黄色", remark="{M}"):
    return [color, plate, "客一", "客车", car_num, "入口少轴", amount, remark]


def build_xlsx(headers, rows, prefix=None, mid=None):
    """最小可用的 xlsx：单元格全部用 inlineStr（POI 与 excelize 都能读）。

    prefix 在表头行之前，mid 在表头行之后（模板的子表头），数据行紧接其后。
    """
    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def row_xml(vals, r):
        cells = []
        for i, v in enumerate(vals):
            ref = "%s%d" % (col_name(i + 1), r)
            cells.append('<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                         % (ref, esc(v)))
        return '<row r="%d">%s</row>' % (r, "".join(cells))

    lines = [row_xml(r, i + 1) for i, r in enumerate(prefix or [])]
    base = len(lines) + 1
    lines.append(row_xml(headers, base))
    lines.extend(row_xml(r, base + 1 + i) for i, r in enumerate(mid or []))
    data_at = base + 1 + len(mid or [])
    lines.extend(row_xml(r, data_at + i) for i, r in enumerate(rows))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + "".join(lines) + "</sheetData></worksheet>")
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.'
          'spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
          'officedocument.spreadsheetml.worksheet+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
              'relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


def col_name(idx):
    s = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        s = chr(65 + rem) + s
    return s


def post_file(base, path, token, filename, content, fields=None):
    b = "----" + uuid.uuid4().hex
    body = b""
    for k, v in (fields or {}).items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
    body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
             "Content-Type: application/octet-stream\r\n\r\n" % (b, filename)).encode()
    body += content + b"\r\n"
    body += ("--%s--\r\n" % b).encode()
    import urllib.request
    req = urllib.request.Request(base + path, data=body, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "multipart/form-data; boundary=" + b})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read()
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", -1)
        return code, (e.read() if hasattr(e, "read") else str(e).encode())


# 每个用例：表头 + 一行 PARITY 数据。
#   expect_error: 数据是故意做错的，只比错误清单，不重复上传也不查落库
#   key_index:    行里哪一格是本端的标记值，落库对照按它精确查
CASES = [
    {
        "path": "/system/user/importData",
        "label": "用户（新增/重复/updateSupport）",
        # 首轮（新增用户）与随后的落库对照属已知 Java 侧缺陷：
        # SysUserMapper.insertUser 在设置参数时抛 IndexOutOfBoundsException: No group 2
        # —— 与 /system/user 的 POST 是同一处缺陷（见 PARITY-2026-11-02 §8），
        # Go 能正常插入，不镜像这个崩溃。
        "known": {"首轮": "Java insertUser 抛 'No group 2'（同 /system/user POST 缺陷）",
                  "落库": "Java 那侧没插进去，Go 插成功了"},
        "headers": ["用户序号", "用户编码", "部门编号", "登录名称", "用户名称", "用户类型", "用户邮箱",
                    "手机号码", "用户性别", "帐号状态", "证书Id", "证书实体Id", "业务id", "业务名称",
                    "单位名称", "租户单位id", "租户单位名称", "角色编码"],
        "row": ["", "1", "25367", "{M}", "{M}用户", "1", "", "15888888888", "0", "0",
                "", "", "", "", "", "", "", ""],
        # 三轮：新增 → 重复(拒绝) → updateSupport(更新)。Java 的消息模板逐条不同，都要对。
        "fields": {"updateSupport": "false"},
        "rounds": [{"updateSupport": "false"}, {"updateSupport": "false"}, {"updateSupport": "true"}],
        "list": "/system/user/list?userName=%s&pageNum=1&pageSize=10",
        "key_index": 3,
    },
    {
        "path": "/manager/carinfo/import",
        "label": "车辆（合法数据）",
        # 表头必须逐字等于 CarInfoController.initList() 的 ImportEntity 标题，否则两端都会
        # 回 "模板不正确"（那只能证明校验一致，证明不了解析与落库）。
        "headers": CAR_HEADERS,
        "row": ["黄色", "{M}挂", "客一", "客车", "2", "入口少轴", "1.00", "{M}"],
        "fields": {"isUpdateSupport": "false"},
        "list": "/manager/carinfo/list?carNo=%s&pageNum=1&pageSize=10",
        "key_index": 1,
    },
    {
        "path": "/manager/carinfo/import",
        "label": "车辆（规则 1/3/2 报错）",
        "headers": CAR_HEADERS,
        # 车牌颜色空(1)、轴数带小数(3)、逃费金额非数字(2)：三条都要按列位报出 Java 的原文。
        "row": ["", "{M}挂", "客一", "", "2.5", "入口少轴", "abc", ""],
        "fields": {"isUpdateSupport": "false"},
        "expect_error": True,
    },
    {
        "path": "/manager/exceptrecord/import",
        "label": "流水（日期不满足规则 8）",
        "headers": EXCEPT_HEADERS,
        "prefix": EXCEPT_TITLE, "mid": EXCEPT_MID,
        # 出入口时间只写到日，而规则 1,8 要求 yyyy-MM-dd HH:mm:ss。
        # 车牌列会被 Java 按 '_' 拆成「车牌_车牌颜色」，所以本端标记不能带下划线，
        # 否则两端都会落到同一个 car_no="PARITY" 上，共用库就又互相可见了。
        "sides": (MARK + "J", MARK + "G"),
        "row": ["1", "出口站A", "2025-01-02", "PASS{M}", "{M}挂", "货1", "客车",
                "入口站A", "2025-01-01", "入口少轴", "入口少轴", "", "", "1.00", "", "", "2.00",
                "", "", "", "{M}备注"],
        "fields": {"isUpdateSupport": "false"},
        "expect_error": True,
    },
    {
        "path": "/manager/exceptrecord/import",
        "label": "流水（合法数据）",
        "headers": EXCEPT_HEADERS,
        "prefix": EXCEPT_TITLE, "mid": EXCEPT_MID,
        "sides": (MARK + "J", MARK + "G"),
        "row": ["1", "出口站A", "2025-01-02 10:00:00", "PASS{M}", "{M}挂", "货1", "客车",
                "入口站A", "2025-01-01 09:00:00", "入口少轴", "入口少轴", "", "", "1.00", "", "", "2.00",
                "", "", "", "{M}备注"],
        "fields": {"isUpdateSupport": "false"},
        "list": "/manager/exceptrecord/list?carNo=%s&pageNum=1&pageSize=10",
        "key_index": 4,
    },
    # ---- 多行用例：单行覆盖不到跨行的那几个分支 -------------------------------
    {
        "path": "/manager/exceptrecord/import",
        "label": "流水（多行业务错误：顺序与 rowNo）",
        "headers": EXCEPT_HEADERS,
        "prefix": EXCEPT_TITLE, "mid": EXCEPT_MID,
        "sides": (MARK + "J", MARK + "G"),
        # 格式全合法 ⇒ 第一段不报错，第二段才有机会逐行报：时间倒挂 / 收费>应缴 / 字典查不到。
        "rows": [
            except_row(plate="{M}挂B"),
            except_row(plate="{M}挂B", in_t="2025-01-02 11:00:00"),
            except_row(plate="{M}挂B", charge="5.00"),
            except_row(plate="{M}挂B", esc="没这个类型"),
        ],
        "fields": {"isUpdateSupport": "false"},
        "expect_error": True,
    },
    {
        "path": "/manager/exceptrecord/import",
        "label": "流水（同车牌区间重叠：这一行不写库）",
        "headers": EXCEPT_HEADERS,
        "prefix": EXCEPT_TITLE, "mid": EXCEPT_MID,
        "sides": (MARK + "J", MARK + "G"),
        # 第二行与第一行区间重叠 ⇒ saveCarExceptRecord 的 isExitsTime 命中就 return error，
        # 而控制器忽略返回值：响应里两行都带着，库里只有第一行。
        "rows": [
            except_row(plate="{M}挂C", in_t="2025-02-01 09:00:00", out_t="2025-02-01 10:00:00"),
            except_row(plate="{M}挂C", in_t="2025-02-01 09:30:00", out_t="2025-02-01 11:00:00"),
        ],
        "fields": {"isUpdateSupport": "false"},
        "list": "/manager/exceptrecord/list?carNo=%s&pageNum=1&pageSize=10",
        "key_index": 4,
    },
    {
        "path": "/manager/exceptrecord/import",
        "label": "流水（结束行终止读行）",
        "headers": EXCEPT_HEADERS,
        "prefix": EXCEPT_TITLE, "mid": EXCEPT_MID,
        "sides": (MARK + "J", MARK + "G"),
        # dataRtnExcel08 见到首格是 break/结束 就 break：它后面那行合法数据一律不读。
        "rows": [
            except_row(plate="{M}挂D", in_t="2025-03-01 09:00:00", out_t="2025-03-01 10:00:00"),
            ["结束"] + [""] * 20,
            except_row(plate="{M}挂D", in_t="2025-03-02 09:00:00", out_t="2025-03-02 10:00:00"),
        ],
        "fields": {"isUpdateSupport": "false"},
        "list": "/manager/exceptrecord/list?carNo=%s&pageNum=1&pageSize=10",
        "key_index": 4,
    },
    {
        "path": "/manager/carinfo/import",
        "label": "车辆（跨行级联：一行报错后合法行也不入库）",
        "headers": CAR_HEADERS,
        # Java: importList 只在 errorList 仍为空时追加 ⇒ 第 3 行虽然合法也进不去，
        # 而且第二段字典校验整段被跳过（所以不能指望它报字典错）。
        "rows": [
            car_row(plate="{M}挂2"),
            car_row(plate="{M}挂3", car_num="x"),
            car_row(plate="{M}挂4"),
        ],
        "fields": {"isUpdateSupport": "false"},
        "expect_error": True,
    },
    {
        "path": "/manager/carinfo/import",
        "label": "车辆（错误数 >100 提前收尾）",
        "headers": CAR_HEADERS,
        # 每行一个格式错：Java 的循环条件是 errorList.size() > 100 才 break，
        # 所以错误条数停在 101 —— Go 必须在同一行停下。
        "rows": [car_row(plate="{M}挂%d" % i, car_num="x") for i in range(105)],
        "fields": {"isUpdateSupport": "false"},
        "expect_error": True,
    },
]


def brief(raw):
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"__raw__": re.sub(r"\s+", " ", raw.decode("utf-8", "ignore"))[:300]}
    if isinstance(obj, dict) and isinstance(obj.get("msg"), str):
        # 导入结果里的随机主键不属于两端差异，压掉噪声
        obj = dict(obj)
        obj["msg"] = re.sub(r"[\da-f]{32}", "<HEX32>", obj["msg"])
    return obj


def render(row, tag):
    return [v.replace("{M}", tag) if isinstance(v, str) else v for v in row]


def case_rows(case, tag):
    """用例可以只给一行（row），也可以给多行（rows）—— 多行才能覆盖跨行的分支。"""
    src = case.get("rows") or [case["row"]]
    return [render(r, tag) for r in src]


def report(tag, sj, aj, sg, ag, known=None):
    print("   [%s] JAVA %s %s" % (tag, sj, json.dumps(aj, ensure_ascii=False)[:300]))
    print("   %s GO   %s %s" % (" " * (len(tag) + 3), sg, json.dumps(ag, ensure_ascii=False)[:300]))
    if sj != sg:
        print("     差异", json.dumps(["__status__", sj, sg], ensure_ascii=False)[:220])
        return 1
    diff = pp.diff(pp.norm(aj), pp.norm(ag))
    if not diff:
        print("     一致")
        return 0
    if known:
        print("     已知 Java 侧缺陷，不镜像：%s" % known)
    for x in diff[:6]:
        print("     差异", json.dumps(x, ensure_ascii=False)[:220])
    return 0 if known else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    tk_j, tk_g = pp.login_java(), pp.login_go()
    problems = 0
    for case in CASES:
        path, label = case["path"], case.get("label") or path
        if args.only and args.only not in path and args.only not in label:
            continue
        side_j, side_g = case.get("sides") or (MARK + "_J", MARK + "_G")
        rows_j, rows_g = case_rows(case, side_j), case_rows(case, side_g)
        xj = build_xlsx(case["headers"], rows_j, case.get("prefix"), case.get("mid"))
        xg = build_xlsx(case["headers"], rows_g, case.get("prefix"), case.get("mid"))
        print("\n== POST %s  %s  (%d 行 / %d 字节 xlsx)"
              % (path, label, len(rows_j), len(xj)))
        rounds = case.get("rounds") or [case.get("fields")]
        for idx, rnd in enumerate(rounds):
            tag = ["首轮", "重复", "updateSupport"][idx] if idx < 3 else "r%d" % idx
            sj, rj = post_file(pp.JAVA, path, tk_j, "parity.xlsx", xj, rnd)
            sg, rg = post_file(pp.GO, path, tk_g, "parity.xlsx", xg, rnd)
            problems += report(tag, sj, brief(rj), sg, brief(rg),
                               (case.get("known") or {}).get(tag))
        if case.get("expect_error"):
            continue
        # 再传一次同样的内容：Java 按 car_no(+in_time) 命中已有行就走 updateById，
        # 这一轮的响应体和落库都要对上（updateBy/updateTime 是最容易漏 stamp 的一格）。
        sj, rj = post_file(pp.JAVA, path, tk_j, "parity.xlsx", xj, case.get("fields"))
        sg, rg = post_file(pp.GO, path, tk_g, "parity.xlsx", xg, case.get("fields"))
        problems += report("重复上传", sj, brief(rj), sg, brief(rg))
        # 落库结果对照（各端查自己那个标记值，行内容应当一致）
        lj = pp.norm(pp.req(pp.JAVA, case["list"] % quote(rows_j[0][case["key_index"]]), token=tk_j))
        lg = pp.norm(pp.req(pp.GO, case["list"] % quote(rows_g[0][case["key_index"]]), token=tk_g))
        dj = pp.diff(lj, lg)
        print("   落库对照 %s 条(JAVA) / %s 条(GO)  差异 %d" % (
            lj.get("total") if isinstance(lj, dict) else "?",
            lg.get("total") if isinstance(lg, dict) else "?", len(dj)))
        for d in dj[:6]:
            print("     ", json.dumps(d, ensure_ascii=False)[:220])
        if dj:
            if (case.get("known") or {}).get("落库"):
                print("      （已知 Java 侧缺陷：%s）" % case["known"]["落库"])
            else:
                problems += 1
    print("\n== 导入回归：问题 %d 处（收尾请跑 compare_write.py --clean 清 PARITY 行）" % problems)


if __name__ == "__main__":
    main()
