# -*- coding: utf-8 -*-
"""GET 查询参数矩阵校验。

前几轮的对比都固定带 ?pageNum=1&pageSize=3，参数面的差异看不见。
本脚本对同一批列表端点跑一串查询参数变体（分页越界、pageSize=0/超大、
orderByColumn 合法与非法、isAsc 乱值、常用过滤条件），逐字段比对两端。

用法:
  MSYS2_ARG_CONV_EXCL='*' python scripts/parity/check_query_matrix.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402

ENDPOINTS = [
    ("/system/user/list", ["", "&status=0", "&userName=admin"]),
    ("/system/role/list", ["", "&status=0", "&roleName=管理"]),
    ("/system/dict/data/list", ["", "&dictType=sys_user_sex"]),
    ("/system/dict/type/list", ["", "&status=0"]),
    ("/system/config/list", ["", "&configKey=sys."]),
    ("/system/notice/list", ["", "&status=0"]),
    ("/system/post/list", ["", "&status=0"]),
    ("/system/dept/list", ["", "&status=0"]),
    ("/monitor/operlog/list", ["", "&businessType=1"]),
    ("/monitor/logininfor/list", ["", "&status=0"]),
    ("/monitor/job/list", ["", "&status=0"]),
    ("/monitor/jobLog/list", ["", "&status=0"]),
    ("/manager/carinfo/list", ["", "&status=0", "&carType=1"]),
    ("/manager/whiteinfo/list", ["", "&status=0"]),
    ("/manager/exceptrecord/list", ["", "&status=0"]),
    ("/manager/querylog/list", ["", "&status=0"]),
    ("/manager/cartrackinfo/list", ["", "&status=0"]),
    ("/manager/suspicious/list", ["", "&status=0"]),
    ("/base/gantry/list", ["", "&status=0"]),
    ("/base/geometry/list", ["", "&lxbh=G"]),
    ("/base/section/list", ["", "&roadCode=G6021"]),
    ("/base/org/list", ["", "&status=0"]),
    ("/flow/flowname/list", ["", "&flowBusinessType=1"]),
    ("/flow/flowtemplate/list", [""]),
    ("/tool/gen/list", ["", "&tableName=sys"]),
]

# 参数变体：分页边界 + 排序列 + 非法排序
VARIANTS = [
    "?pageNum=1&pageSize=3",
    "?pageNum=0&pageSize=3",
    "?pageNum=9999&pageSize=3",
    "?pageNum=1&pageSize=0",
    "?pageNum=1&pageSize=-1",
    "?pageNum=1&pageSize=99999",
    "?pageNum=1&pageSize=3&orderByColumn=createTime&isAsc=desc",
    "?pageNum=1&pageSize=3&orderByColumn=create_time&isAsc=ascending",
    "?pageNum=1&pageSize=3&orderByColumn=1%3Bdrop&isAsc=desc",
    "?pageNum=1&pageSize=3&isAsc=bogus",
    "?pageNum=1&pageSize=3&reasonable=false",
]


def brief(a, b):
    rows = lambda x: len(x.get("rows") or []) if isinstance(x.get("rows"), list) else -1
    return "java(%s,total=%s,rows=%s) go(%s,total=%s,rows=%s)" % (
        a.get("code"), a.get("total"), rows(a), b.get("code"), b.get("total"), rows(b))


def main():
    tk_j, tk_g = pp.login_java(), pp.login_go()
    bad, checked = [], 0
    for base, filters in ENDPOINTS:
        for extra in [""] + filters:
            for variant in VARIANTS:
                query = variant.lstrip("?")
                if extra:
                    query += "&" + extra.lstrip("&")
                url = base + "?" + query
                a, b = pp.req(pp.JAVA, url, tk_j), pp.req(pp.GO, url, tk_g)
                if not isinstance(a, dict) or not isinstance(b, dict) or "rows" not in a:
                    continue
                checked += 1
                d = pp.diff(pp.norm(a), pp.norm(b))
                # 排序差异表现为 rows 内容不同；分页/转义差异表现为 code、total、rows 长度
                if d:
                    bad.append((url, len(d), brief(a, b), str(d[0])[:120]))
    print("\n矩阵校验：比对 %d 个组合，存在差异 %d 个" % (checked, len(bad)))
    for url, n, shape, first in bad:
        print("  %-64s 差异%3d %s" % (url[:64], n, shape))
        print("      首条: %s" % first)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
