// 对应 Java: com.ruoyi.web.controller.base.GeometryController（getHenDa / syncAllGeometry /
//            syncAllGeometry1）+ com.ruoyi.base.service.impl.HenDaServiceImpl
//            + com.ruoyi.web.controller.base.OdsRtSzdnSnapshotFlowAddcodeController#earliest-time
//
// 这一批是"外部服务在场才有意义"的接口。本环境里 36.200.20.14:7890 与 127.0.0.1:9901
// 都连不通，所以**可观测的正是失败路径**，而 Java 对失败的处理各不相同，必须逐条对上：
//   * getPileToLonLat 自己 catch(Exception) → return null ⇒ getHenDa 恒为
//     {"msg":"操作成功","code":200}（连 data 键都没有），完全看不出远端挂了；
//   * syncAllGeometry / syncAllGeometry1 是"先 return success，再把活丢线程池"
//     ⇒ 响应与后台结果无关，后台失败只进日志（§5.1 记的那条 Java 缺陷）；
//   * earliest-time 用的是 Forest 声明式调用且**没有 try/catch** ⇒ 传输异常逃到
//     GlobalExceptionHandler ⇒ HTTP 200 + {"msg":"<异常文本>","code":500}。
//
// ⚠️ 未对真实 HenDa/GeoServer 验证过（网内不可达）。桩号→经纬度的入库分支
//    （11 次探测、≥5 条才写 geometry）按源码逐行移植，但没有实测机会。
#include "cm/web/controller/base/GeometrySyncController.hpp"

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/EncryptUtils.hpp"
#include <algorithm>
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;

/** 对应 HenDaServiceImpl.getPileToLonLat：失败一律吞成 null */
std::optional<Json> henDaPileToLonLat(const std::string& roadCode, const std::string& pile,
                                      const std::string& direction) {
    try {
        // new HashMap<>(3) ⇒ 表容量是 4（tableSizeFor(3)=4），桶序按 capacity=4 算，
        // 与默认 16 的表不一样 —— 用 javaMapOrder() 的默认容量就会给出错的键序
        std::vector<std::pair<std::string, std::string>> kv = {
            {"layerName", "rdlinelong"},
            {"filter", "lxbh='" + roadCode + "'  and gxfx = '" + direction + "'"},  // 两个空格
            {"m", pile},
        };
        std::ostringstream json;
        json << '{';
        bool first = true;
        std::vector<std::string> keys = {"layerName", "filter", "m"};
        std::stable_sort(keys.begin(), keys.end(), [](const std::string& a, const std::string& b) {
            return cm::utils::javaBucketIndex(a, 4) < cm::utils::javaBucketIndex(b, 4);
        });
        for (const auto& key : keys) {
            for (const auto& [k, v] : kv) {
                if (k != key) continue;
                if (!first) json << ',';
                first = false;
                const std::string escaped = Json(v).dump();   // 带首尾引号的 JSON 字符串
                json << '"' << k << '"' << ':' << '"' << escaped.substr(1, escaped.size() - 2)
                     << '"';
            }
        }
        json << '}';

        const auto now = std::chrono::system_clock::now();
        const long long millis =
            std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
        const std::string nonce = std::to_string(millis);
        // SimpleDateFormat("yyyyMMddHHmmss") 用的是**默认时区**
        std::tm lt{};
        const std::time_t t = std::chrono::system_clock::to_time_t(now);
#if defined(_WIN32)
        localtime_s(&lt, &t);
#else
        localtime_r(&t, &lt);
#endif
        char stamp[24];
        std::strftime(stamp, sizeof stamp, "%Y%m%d%H%M%S", &lt);
        const std::string timestamp = stamp;

        const auto& cfg = cm::config::AppConfig::instance();
        const std::string signature =
            cm::crypto::getCiphertext(cfg.hengdaAppid, cfg.hengdaSecret, nonce, timestamp);
        // URLEncoder.encode(json,"utf8") 一次，Forest 再把整个值编一次 ⇒ 双重编码
        const std::string params = cm::net::urlEncodeQuery(json.str());
        const std::string url = cfg.hengdaUrl + "/getLonLatByPos";
        auto resp = cm::net::HttpClient::getWithQuery(
            url, {{"params", params},
                  {"appid", cfg.hengdaAppid},
                  {"nonce", nonce},
                  {"signature", signature},
                  {"timestamp", timestamp}},
            {{"Connection", "close"}}, [] {
                cm::net::HttpOptions o;
                o.connectTimeoutMs = 30000;   // 该方法单独设了 connectTimeout
                o.readTimeoutMs = 60000;
                return o;
            }());
        if (!resp.is2xx()) return std::nullopt;
        Json body = Json::parse(resp.body);
        // lonLatByPos.getJSONObject("data") —— 缺 data 或非对象都会抛，被 catch 吞掉
        if (!body.is_object() || !body.contains("data") || !body["data"].is_object())
            return std::nullopt;
        const Json& d = body["data"];
        if (!d.contains("x") || !d.contains("y")) return std::nullopt;
        Json rtn = Json::object();
        rtn["longitude"] = Json(cm::jstr(d, "x"));
        rtn["latitude"] = Json(cm::jstr(d, "y"));
        return rtn;
    } catch (...) {
        // 防止线程中断：报错就跳过这个经纬度
        return std::nullopt;
    }
}

/** double 的 Java 打印形态（整数值也要带 .0），用于 Arrays.deepToString */
std::string javaDouble(double v) {
    if (std::isnan(v)) return "NaN";
    if (std::isinf(v)) return v > 0 ? "Infinity" : "-Infinity";
    std::ostringstream o;
    o.precision(17);
    o << v;
    std::string s = o.str();
    if (s.find('.') == std::string::npos && s.find('e') == std::string::npos &&
        s.find("Inf") == std::string::npos && s.find("NaN") == std::string::npos)
        s += ".0";
    // 去掉 stringstream 在 17 位精度下多出来的尾巴
    if (s.find('.') != std::string::npos && s.find('e') == std::string::npos) {
        for (int prec = 1; prec <= 17; ++prec) {
            std::ostringstream t;
            t.precision(prec);
            t << v;
            std::string ts = t.str();
            if (ts.find('.') == std::string::npos) ts += ".0";
            if (std::stod(ts) == v) return ts;
        }
    }
    return s;
}

std::string deepToString(const std::vector<std::pair<double, double>>& list) {
    std::ostringstream o;
    o << '[';
    for (size_t i = 0; i < list.size(); ++i) {
        if (i) o << ", ";
        o << '[' << javaDouble(list[i].first) << ", " << javaDouble(list[i].second) << ']';
    }
    o << ']';
    return o.str();
}

struct GeoRow {
    std::string lxbh;
    std::string lxfx;
    std::string qdzh;   // 空串 = Java 的 Integer null
};

/** 对应 syncGeometry 里丢给线程池的那个 Runnable：11 次探测一轮，≥5 条才入库，
 *  然后 qdzh++ 继续，直到一轮里不足 7 条为止。 */
void runSyncTask(GeoRow g) {
    try {
        if (g.qdzh.empty())   // Java: Integer qdzh 为 null 时 qdzh + "." + i 直接 NPE，
            return;           // 且发生在池线程里 —— 客户端完全看不见
        long long qdzh = std::stoll(g.qdzh);
        std::vector<std::pair<double, double>> pts;
        int count = 10;
        int i = 0;
        while (count >= 7) {
            const std::string zh = (i < 10) ? (std::to_string(qdzh) + "." + std::to_string(i))
                                            : std::to_string(qdzh + 1);
            auto hit = henDaPileToLonLat(g.lxbh, zh, g.lxfx);
            if (hit) {
                // getDoubleValue：键不存在/为 null 时是 0.0（不是异常）
                const double lon = hit->contains("longitude") ? std::stod((*hit)["longitude"].get<std::string>()) : 0.0;
                const double lat = hit->contains("latitude") ? std::stod((*hit)["latitude"].get<std::string>()) : 0.0;
                pts.emplace_back(lon, lat);
            }
            if (i == 10) {
                count = static_cast<int>(pts.size());
                if (pts.size() >= 5) {
                    const std::string paths = deepToString(pts);
                    Db::instance().execute(
                        "insert into geometry (lxbh, lxfx, qdzh, zdzh, paths) values (" +
                        cm::db::bind(g.lxbh) + ", " + cm::db::bind(g.lxfx) + ", " + std::to_string(qdzh) +
                        ", " + std::to_string(qdzh + 1) + ", " + cm::db::bind(paths) + ")");
                }
                pts.clear();
                qdzh++;
                i = 0;
            } else {
                i++;
            }
        }
    } catch (...) {
        // Java 也一样：池线程里的异常只进 uncaught handler，不影响已返回的响应
    }
}

} // namespace

void registerGeometrySyncController(Router& r) {
    // GET /base/geometry/getHenDa —— 九条里唯一有 @PreAuthorize 的一条
    r.get("/base/geometry/getHenDa", [](RequestContext& ctx) -> cm::http::ApiResponse {
        // Geometry 从 query 绑定；用的是瞬态字段 zhStr（不是 qdzh）
        const std::string lxbh = ctx.optParam("lxbh").value_or("");
        const std::string lxfx = ctx.optParam("lxfx").value_or("");
        const std::string zhStr = ctx.optParam("zhStr").value_or("");
        auto rtn = henDaPileToLonLat(lxbh, zhStr, lxfx);
        // AjaxResult.success(null) ⇒ data 键整个消失，也完全不提"远端失败"
        return BaseController::ok(rtn ? AjaxResult::success(*rtn) : AjaxResult::success());
    }).permi("base:geometry:list");

    // GET /base/geometry/syncAllGeometry —— 先答 success，再往线程池丢活
    r.get("/base/geometry/syncAllGeometry", [](RequestContext&) -> cm::http::ApiResponse {
        // geometryService.syncAllGeometry()：纯本地读 geometry_copy1 ⨝ geometry。
        // 表不存在时是**同步**抛异常 ⇒ code:500（这是这条接口少数可观测的分支之一）
        cm::db::Result res;
        const std::string sql =
            "select t1.lxbh, t1.lxfx, IFNULL(t2.zdzh,t1.qdzh) qdzh"
            " from (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh FROM geometry_copy1"
            " group by lxbh, lxfx) t1"
            " left join (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh FROM geometry"
            " group by lxbh, lxfx) t2 on t1.lxbh = t2.lxbh and t1.lxfx = t2.lxfx"
            " where t2.zdzh is null or t2.zdzh < t1.zdzh order by t1.lxbh";
        if (!Db::instance().query(sql, res))
            throw cm::exception::ServiceException("数据访问异常，SQL 执行失败: " + sql.substr(0, 200));
        std::vector<GeoRow> rows;
        for (const auto& row : res.rows)
            rows.push_back({row.str("lxbh"), row.str("lxfx"), row.str("qdzh")});
        // 每行一个任务，fire-and-forget（Java 用的是 core=50/queue=1000 的 threadPoolTaskExecutor）
        for (const auto& g : rows) {
            std::thread(runSyncTask, g).detach();
        }
        return BaseController::ok(AjaxResult::success());
    });

    // GET /base/geometry/syncAllGeometry1 —— 把 query 绑成一个 Geometry 丢进线程池，不做任何校验
    r.get("/base/geometry/syncAllGeometry1", [](RequestContext& ctx) -> cm::http::ApiResponse {
        GeoRow g;
        g.lxbh = ctx.optParam("lxbh").value_or("");
        g.lxfx = ctx.optParam("lxfx").value_or("");
        if (auto v = ctx.optParam("qdzh"); v && !v->empty()) g.qdzh = *v;   // 否则保持 null
        std::thread(runSyncTask, g).detach();
        return BaseController::ok(AjaxResult::success());
    });

    // GET /base/snapshotflow/earliest-time —— Forest 且**没有 try/catch**
    r.get("/base/snapshotflow/earliest-time", [](RequestContext&) -> cm::http::ApiResponse {
        const std::string url =
            cm::config::AppConfig::instance().vehicleMonitorBaseUrl + "/base/snapshotflow/earliest-time";
        auto resp = cm::net::HttpClient::get(url);
        if (!resp.ok())
            throw cm::exception::ServiceException(resp.error);   // ⇒ HTTP 200 + code:500
        if (resp.is2xx()) {
            // 上游返的是 AjaxResult 信封，而声明的返回类型是裸 java.util.Date
            // ⇒ fastjson 转换异常 ⇒ 同样是 code:500，"data 是日期串"那条分支基本走不到
            // Forest 的目标类型是**裸 java.util.Date**：整个响应体都要当成日期来解。
            // 上游实际返的是 AjaxResult 信封（对象），fastjson 转 Date 会抛 ⇒ code:500，
            // 所以"data 是日期串"和"暂无数据"两条分支在真实环境里几乎走不到。
            // 空 body：Forest 解出 null ⇒ 走 else 分支
            if (resp.body.empty())
                return BaseController::ok(AjaxResult::success(std::string("暂无数据")));
            Json body = Json::parse(resp.body);
            std::string value;
            if (body.is_string()) {
                value = body.get<std::string>();
            } else if (body.is_number()) {
                value = std::to_string(body.get<long long>());
            } else if (body.is_null() || resp.body.empty()) {
                value = "";
            } else {
                throw cm::exception::ServiceException("can not cast to Date, value : " + resp.body);
            }
            if (value.empty()) return BaseController::ok(AjaxResult::success(std::string("暂无数据")));
            auto ms = cm::utils::DateUtils::parseDbDateTime(value);
            if (!ms) {
                // 上游也可能直接给 ISO 串：DateUtils::parseDate 返回 TimePoint
                auto tp = cm::utils::DateUtils::parseDate(value);
                if (tp)
                    ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                             tp->time_since_epoch())
                             .count();
            }
            if (!ms) throw cm::exception::ServiceException("can not cast to Date, value : " + value);
            // success(Date) 走的是 data 重载；而 success("暂无数据") 命中的是 msg 重载
            // ⇒ 两条分支的响应形状不同（一条有 data、一条把中文塞进 msg）
            return BaseController::ok(
                AjaxResult::success(Json(cm::utils::DateUtils::formatIsoDate(*ms))));
        }
        throw cm::exception::ServiceException("HTTP" + std::to_string(resp.status) + " Error:");
    });
}

} // namespace cm::web
