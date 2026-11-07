# -*- coding: utf-8 -*-
"""全路由对拍覆盖率盘点：Go 注册的每一条路由，是否被某条对拍真正跑过。

口径全部来自各对拍脚本自己的定义（不另写一份匹配规则，避免"脚本改了、盘点没跟上"）：
  * 上传          —— compare_upload_errors.PATHS + compare_import.CASES
  * 导出/导入模板 —— compare_export_all 的 export|import 路由口径
  * 写生命周期    —— compare_write.RESOURCES 的资源族（同前缀的 POST/PUT/DELETE 即算覆盖）
  * GET 三档      —— compare_get.in_tier(api/business/framework)
顺序就是上面这个：一条 POST /xxx/importData 既是"上传"也匹配 import 关键词，
先判上传才不会被 export 口径吃掉。

剩下的分两类：
  * destructive —— 按约定不能盲打的（清日志、踢会话、跑定时任务、全局同步、落盘上传、
                   改口令、删建桶），逐条写理由，不是缺口；
  * uncovered   —— 真缺口，要么补进某个对拍口径，要么给出"确无对拍价值"的新理由。

用法:
  python scripts/parity/check_coverage.py [--log 启动日志] [--out report.json]
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import GIN_RE, norm  # noqa: E402
import compare_get  # noqa: E402
import compare_import  # noqa: E402
import compare_upload_errors  # noqa: E402
import compare_write  # noqa: E402

DEFAULT_LOG = os.path.join(os.environ.get("TEMP", "/tmp"), "go-ref-9982.log")

# 确无对拍价值的注册路由（精确匹配），值是理由。
EXEMPT = {
    ("GET", "/"): "静态首页，无业务返回体；三档 GET 的 load_routes 明确跳过",
    ("GET", "/healthz"): "Go 侧自加的探活，Java 无对应路由",
    ("HEAD", "/"): "Gin 自动注册的 HEAD，Java 侧由同一 handler 兜住",
    ("OPTIONS", "/"): "CORS 预检，不是业务接口",
    ("PATCH", "/"): "根路径多方法占位，返回体与 GET / 同一个欢迎页，check_oss.py 已在匿名口径比过",
    ("POST", "/"): "同上，根路径占位",
    ("PUT", "/"): "同上，根路径占位",
    ("DELETE", "/"): "同上，根路径占位",
    ("POST", "/logout"): "只回 200 空体；pp.py 每轮对拍都重新登录，等价于跑过",
    ("POST", "/login"): "响应里是随机 token，逐字段比无意义；登录链路本身每轮都在两端各跑一次",
    ("GET", "/captchaImage"): "uuid 与图片字节都是随机/运行态；pp.py 的 Java 登录每轮都在读它",
}

# 按约定不能盲打的端点（method 正则 + 路径正则 + 理由）。
DESTRUCTIVE = [
    ("POST", r"^/common/upload$", "往共享盘 uploadPath 落文件，且文件名随机"),
    ("(POST|PUT)", r"^/system/file/(upload|updateCAFile)", "写共享盘 / 覆盖业务文件表"),
    ("(POST|PUT)", r"^/system/file/uploadByUrl", "抓外部 URL 落地，打外部服务"),
    ("DELETE", r"^/system/file", "真删库里的文件行"),
    ("(POST|PUT)", r"^/system/user/resetPwd", "会改掉别人账号的口令"),
    ("(POST|PUT)", r"updatePwd", "改掉当前登录账号的口令"),
    ("PUT", r"^/monitor/job/run", "立刻触发定时任务（会真跑业务）"),
    ("PUT", r"^/monitor/job/changeStatus", "启停调度，影响共享实例"),
    ("(POST|PUT|DELETE)", r"^/monitor/job(/|$)", "Quartz 调度器写操作，启停是全局态"),
    ("DELETE", r"^/monitor/jobLog(/|$)", "清任务日志是破坏性运维"),
    ("DELETE", r"^/monitor/(logininfor|operlog)(/|$)", "清审计/登录日志，删的是别人也在看的表"),
    ("DELETE", r"^/monitor/online", "强退在线会话，会踢掉共享环境里其他人的 token"),
    ("(POST)", r"^/base/cdc/retry", "全局重投 Kafka 死信，副作用大"),
    ("DELETE", r"^/base/cdc/dead-letters", "清死信队列"),
    ("(POST|PUT)", r"submitEntrustFlow|submitReturn|saveFlowAuit", "走审批流转，会改流程实例状态"),
    ("POST", r"syncSuspiciousCarTask|syncCurrentTrack|syncAll", "全局同步，打外部路网/腾讯接口"),
    ("(POST|DELETE)", r"^/oss/", "对不可达的 MinIO 建/删桶与对象；GET 与预签名由 check_oss.py 比"),
    ("(POST|PUT|DELETE)", r"^/tool/gen", "代码生成器会往工程里写文件"),
    ("(POST|PUT|DELETE)", r"^/test/user", "脚手架测试路由，Java 侧是 demo 表"),
]
DESTRUCTIVE = [(m, re.compile(p), why) for m, p, why in DESTRUCTIVE]


# 写生命周期只建模 CRUD 四步（POST 建一行 → GET 详情 → PUT → DELETE 自建行）；
# 这几个端点不是"新增一行"的语义，用标记值都定位不到自己的行，硬塞进 RESOURCES
# 只会在共享库里留下删不干净的尾巴。
NOT_CRUD = [
    ("(POST|PUT|DELETE)", r"^/manager/confimfree",
     "POST 收 exceptIds 串，回写 car_except_record 的补缴状态，是编排动作而非建行"),
    ("(POST|PUT|DELETE)", r"^/system/indexmenu",
     "POST 收 menuIds 串按菜单展开成多行，表里没有可当标记的文本列，自建行删不干净"),
    ("(POST|PUT|DELETE)", r"^/system/file",
     "文件行的新增必须先往共享盘落文件（已列破坏性），PUT/DELETE 没有自建行可操作"),
    ("POST", r"^/common/uploads$", "批量落盘上传，与 /common/upload 同一条约定"),
]

# 导出复扫（compare_export_all）里除了 export|import 关键词，还单列了 /downTemplate/{type}。
EXPORTISH = re.compile(r"export|import|downtemplate", re.I)


def registered(log_path):
    """启动日志里的 [GIN-debug] 行 ⇒ (method, 归一化路径) 全集。"""
    text = open(log_path, encoding="utf-8", errors="ignore").read()
    out = []
    for m in GIN_RE.finditer(text):
        method, path = m.group(1), norm(m.group(2))
        if path.startswith("http"):
            continue
        out.append((method, path))
    return out


def upload_paths():
    return {c["path"] for c in compare_import.CASES} | set(compare_upload_errors.PATHS)


def write_paths():
    """写生命周期真正会打的 URL：资源 base 本身、base/:x（详情与删除）、以及声明的 actions 子路径。"""
    out = set()
    for res in compare_write.RESOURCES:
        base = res.get("base")
        if not base:
            continue
        out.add(base)
        out.add(base + "/:x")
        for _method, sub, _extra in res.get("actions", ()):
            out.add(base + sub)
    return out


def classify(method, path):
    """返回这条路由被哪条对拍覆盖（按口径优先级取第一个命中），没覆盖返回空串。"""
    if path in upload_paths():
        return "upload"
    if EXPORTISH.search(path):
        return "export"
    if path in write_paths():
        return "write"
    if method == "GET":
        for tier in ("api", "business", "framework"):
            if compare_get.in_tier(path, tier):
                return "get:" + tier
    return ""


def match_rule(rules, method, path):
    for m_re, p_re, why in rules:
        if re.fullmatch(m_re, method) and re.search(p_re, path):
            return why
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    if not os.path.exists(args.log):
        raise SystemExit("找不到启动日志 %s（用 --log 指定 Go 参照实例的日志）" % args.log)

    rows = registered(args.log)
    buckets = defaultdict(list)
    reasons = {}
    for method, path in rows:
        if (method, path) in EXEMPT:
            buckets["exempt"].append((method, path))
            continue
        kind = classify(method, path)
        if kind:
            buckets[kind].append((method, path))
            continue
        why = match_rule(NOT_CRUD, method, path)
        if why:
            buckets["not-crud"].append((method, path))
            reasons["%s %s" % (method, path)] = why
            continue
        why = match_rule(DESTRUCTIVE, method, path)
        if why:
            buckets["destructive"].append((method, path))
            reasons["%s %s" % (method, path)] = why
            continue
        buckets["uncovered"].append((method, path))

    print("== 覆盖率盘点：%d 条注册路由 ==" % len(rows))
    order = ["get:api", "get:business", "get:framework", "export", "write", "upload",
             "exempt", "not-crud", "destructive", "uncovered"]
    for key in order:
        print("  %-12s %d 条" % (key, len(buckets.get(key, []))))
    covered = sum(len(buckets.get(k, [])) for k in
                  ("get:api", "get:business", "get:framework", "export", "write", "upload"))
    valuable = len(rows) - len(buckets.get("exempt", [])) - len(buckets.get("destructive", [])) \
        - len(buckets.get("not-crud", []))
    print("  ⇒ 实际被对拍覆盖 %d / 可比 %d = %.1f%%，未覆盖 %d 条"
          % (covered, valuable, 100.0 * covered / max(1, valuable), len(buckets.get("uncovered", []))))

    if buckets.get("uncovered"):
        print("\n== 未覆盖（真缺口：要么补进口径，要么给出豁免理由）==")
        by_method = defaultdict(list)
        for method, path in buckets["uncovered"]:
            by_method[method].append(path)
        for method in sorted(by_method):
            print("   %s (%d)" % (method, len(by_method[method])))
            for path in sorted(set(by_method[method])):
                print("      ", path)
    if buckets.get("destructive") or buckets.get("not-crud"):
        print("\n== 有理由地不打（%d 条，按理由归并）==" % (
            len(buckets.get("destructive", [])) + len(buckets.get("not-crud", []))))
        grouped = defaultdict(list)
        for key, why in reasons.items():
            grouped[why].append(key)
        for why in sorted(grouped, key=lambda w: -len(grouped[w])):
            print("   %2d 条  %s" % (len(grouped[why]), why))

    if args.out:
        json.dump({"total": len(rows),
                   "counts": {k: len(v) for k, v in buckets.items()},
                   "coverage_pct": round(100.0 * covered / max(1, valuable), 1),
                   "uncovered": sorted(["%s %s" % (m, p) for m, p in buckets.get("uncovered", [])]),
                   "reasoned": sorted(reasons),
                   "reasons": reasons},
                  open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n报告:", args.out)


if __name__ == "__main__":
    main()
