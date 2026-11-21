// CarTrackInfoServiceImpl 那三条轨迹几何函数的移植。回退链与 quirk 见 hpp 顶部。
#include "cm/base/service/TrailGeometry.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "cm/base/util/GpsUtil.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/redis/RedisClient.hpp"

namespace cm::base {
namespace {

using cm::utils::CommonUtil;
using cm::utils::StringUtils;
using cm::constant::Constants;

// 腾讯路线规划那对固定凭据是从 Java 里抄来的（LonLatPathsUtils 里就是硬编码）。
// ⚠️ 生产密钥写死在源码里本身就是 Java 的问题，移植不改变它，也不要在日志里打出来。
constexpr const char* TX_KEY = "UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6";
constexpr const char* TX_SECRET = "M9yNPgh8FLp33A0plztTK5sehD6gMqny";
constexpr const char* TX_URL = "/ws/direction/v1/driving/";

struct GeomRow {
    std::string lxbh;
    bool hasQdzh{false};
    long long qdzh{0};
    bool hasZdzh{false};
    long long zdzh{0};
    std::string paths;
};

/** Geometry 的 JSON 形态：7 个键、声明序，new Geometry() 只填 lxbh/paths，其余是 null。
 *  paths 是**字符串**字段，里面装着序列化过的 JSON 数组 ⇒ 输出是转义后的字符串而不是嵌套数组。 */
Json geometryObject(const Json& lxbh, const std::string& paths) {
    Json g = Json::object();
    g["id"] = Json(nullptr);
    g["lxbh"] = lxbh;
    g["lxfx"] = Json(nullptr);
    g["qdzh"] = Json(nullptr);
    g["zdzh"] = Json(nullptr);
    g["paths"] = Json(paths);
    g["zhStr"] = Json(nullptr);
    return g;
}

/** 属性缺失与显式 null 在 Java 里都是 null；这里统一返回可选值 */
const Json* field(const Json& bo, const char* key) {
    if (!bo.is_object()) return nullptr;
    auto it = bo.find(key);
    if (it == bo.end() || it->is_null()) return nullptr;
    return &*it;
}

std::string strField(const Json& bo, const char* key) {
    const Json* v = field(bo, key);
    if (v == nullptr) return "";
    return CommonUtil::isNull(v->is_string() ? v->get<std::string>() : v->dump());
}

long long longField(const Json& bo, const char* key, bool* present) {
    const Json* v = field(bo, key);
    if (present) *present = v != nullptr;
    if (v == nullptr) return 0;
    if (v->is_number()) return static_cast<long long>(v->get<double>());
    try { return std::stoll(v->dump()); } catch (...) { return 0; }
}

std::string numberText(const Json& bo, const char* key) {
    const Json* v = field(bo, key);
    if (v == nullptr) return "";
    // CommonUtil.isNull(Object) 走的是 toString()：BigDecimal#toString 允许科学计数法，
    // 而腾讯那条 API 用的是 toPlainString() —— 这两者在缓存键与请求里本来就可能不一样，
    // 键这一侧照抄 toString 语义（见 getCarGeometryByPlan 的注释）。
    return CommonUtil::isNull(v->is_string() ? v->get<std::string>() : v->dump());
}

// ---------------------------------------------------------------- BigDecimal-ish

/** 十进制文本 -> {符号, 整数位数字, 小数位数字}；不是合法十进制就返回 false
 *  （对应 new BigDecimal(String) 抛 NumberFormatException）。 */
bool splitDecimal(const std::string& text, bool& neg, std::string& intDigits, std::string& fracDigits) {
    neg = false;
    intDigits.clear();
    fracDigits.clear();
    size_t i = 0;
    if (i < text.size() && (text[i] == '+' || text[i] == '-')) {
        neg = text[i] == '-';
        ++i;
    }
    bool anyDigit = false;
    bool seenDot = false;
    for (; i < text.size(); ++i) {
        const char c = text[i];
        if (c >= '0' && c <= '9') {
            anyDigit = true;
            (seenDot ? fracDigits : intDigits).push_back(c);
        } else if (c == '.' && !seenDot) {
            seenDot = true;
        } else {
            return false;
        }
    }
    if (!anyDigit) return false;   // ".5" 在 Java 里也是非法的
    if (intDigits.empty()) intDigits = "0";
    return true;
}

/** 小数数字串按 scale 位 HALF_UP 舍入后的整数部分（等价 setScale(scale,HALF_UP).intValue()：
 *  先舍入到 scale 位，再**向零截断**取整）。 */
long long roundedIntegerPart(std::string intDigits, std::string fracDigits, size_t scale, bool neg) {
    if (fracDigits.size() > scale) {
        const char roundDigit = fracDigits[scale];
        fracDigits = fracDigits.substr(0, scale);
        if (roundDigit >= '5') {                 // HALF_UP 只看被丢掉部分的首位（数值大小）
            // 从最低位往上进 1，必要时溢出到整数部分
            size_t p = fracDigits.size();
            bool carry = true;
            while (carry && p-- > 0) {
                const int d = fracDigits[p] - '0' + 1;
                fracDigits[p] = static_cast<char>('0' + (d % 10));
                carry = d >= 10;
            }
            if (carry) {
                std::string tmp;
                long long n = 0;
                try { n = std::stoll(intDigits); } catch (...) {}
                tmp = std::to_string(n + 1);
                intDigits = tmp;
            }
        }
    }
    long long v = 0;
    try { v = std::stoll(intDigits); } catch (...) {}
    return neg ? -v : v;                          // intValue() 是向零截断
}

std::optional<double> toDouble(const std::string& text) {
    try {
        size_t used = 0;
        const double d = std::stod(text, &used);
        if (used != text.size()) return std::nullopt;
        return d;
    } catch (...) {
        return std::nullopt;
    }
}

// ---------------------------------------------------------------- 缓存与 DB

/** GeometryServiceImpl.updateRedisList() + getRedisList()：
 *  缓存的是"lxbh 与 paths 都非空"的子集，返回的是未过滤的全集；
 *  两者对 getCarGeometry 的结果没有可观察差别 —— paths 为空的行本来就被
 *  `isNotBlank(paths)` 跳过，lxbh 为空的行 trim 后变成 ""，永远碰不到真实的 roadCode。
 *  所以这里直接按缓存（过滤后）那一份分组，并在写缓存时保持同一形态。 */
std::map<std::string, std::vector<GeomRow>> roadGeometryGroups() {
    auto cached = cm::redis::RedisCache::instance().get(Constants::lxbh_jdwd);
    std::vector<GeomRow> rows;
    if (cached && !cached->empty()) {
        Json j = cm::utils::parse_cached_json(*cached);
        if (j.is_array()) {
            for (const auto& e : j) {
                GeomRow g;
                g.lxbh = strField(e, "lxbh");
                bool has = false;
                g.qdzh = longField(e, "qdzh", &has);
                g.hasQdzh = has;
                g.zdzh = longField(e, "zdzh", &has);
                g.hasZdzh = has;
                g.paths = strField(e, "paths");
                rows.push_back(std::move(g));
            }
        }
    } else {
        cm::db::Result res;
        const std::string sql =
            "select t.id, t.lxbh, t.lxfx, t.qdzh, t.zdzh, t.paths from geometry t"
            " WHERE 1=1 and t.lxfx = '1' order by lxbh,t.qdzh";
        if (!cm::db::Db::instance().query(sql, res)) {
            throw cm::exception::ServiceException("数据访问异常，SQL 执行失败: " + sql);
        }
        std::string cacheJson = "[{\"@type\":\"com.ruoyi.base.domain.Geometry\"";
        bool first = true;
        for (const auto& r : res.rows) {
            GeomRow g;
            g.lxbh = CommonUtil::isNull(r.str("lxbh"));   // setLxbh(isNull(...))：trim 是原地的
            const auto qd = r.get("qdzh");
            g.hasQdzh = qd.has_value();
            if (qd) { try { g.qdzh = std::stoll(*qd); } catch (...) {} }
            const auto zd = r.get("zdzh");
            g.hasZdzh = zd.has_value();
            if (zd) { try { g.zdzh = std::stoll(*zd); } catch (...) {} }
            g.paths = r.str("paths");
            if (StringUtils::isBlank(g.lxbh) || StringUtils::isBlank(g.paths)) continue;
            rows.push_back(g);
            if (!first) cacheJson += ",";
            first = false;
            // fastjson2 的写出形态：键按名字排序、null 省略（qdzh/zdzh 是 Integer，不带 L）
            cacheJson += "{\"id\":" + Json(r.str("id")).dump();
            cacheJson += ",\"lxbh\":" + Json(g.lxbh).dump();
            if (!StringUtils::isBlank(r.str("lxfx")))
                cacheJson += ",\"lxfx\":" + Json(r.str("lxfx")).dump();
            if (qd) cacheJson += ",\"qdzh\":" + *qd;
            if (zd) cacheJson += ",\"zdzh\":" + *zd;
            cacheJson += ",\"paths\":" + Json(g.paths).dump();
            cacheJson += "}";
        }
        cacheJson += "]";
        cm::redis::RedisCache::instance().set(Constants::lxbh_jdwd, cacheJson);
    }
    std::map<std::string, std::vector<GeomRow>> out;
    for (const auto& g : rows) out[g.lxbh].push_back(g);
    return out;
}

/** RoadPathImpl.getShortestRoadPath：整个方法只有一个 catch(Exception){return null;}，
 *  其余所有不顺利的路径（返回体为空 / success 非 true / data 缺失 / 点为空）也都落到
 *  末尾的 return null —— 失败永不缓存，由调用方降级到下一层。 */
std::optional<std::string> shortestRoadPath(const std::vector<std::string>& nodeIds) {
    try {
        Json body = Json::object();
        Json ids = Json::array();
        for (const auto& n : nodeIds) ids.push_back(Json(n));
        body["nodeIds"] = ids;
        body["pathType"] = Json("SHORTEST");
        body["includeCoordinates"] = Json("TRUE");
        body["queryMode"] = Json("LENIENT");
        const auto url = cm::config::AppConfig::instance().getString("roadPathUrl") + "/api/routes/query";
        // 这里虽然是 POST，但语义是只读查询（/api/routes/query），与 Java 一样允许重试；
        // HttpClient 默认只重试幂等方法，所以显式打开。
        cm::net::HttpOptions opt;
        opt.retryNonIdempotent = true;
        const auto resp = cm::net::HttpClient::post(url, body.dump(), "application/json", {}, opt);
        if (!resp.is2xx()) return std::nullopt;
        Json j = cm::utils::parse_cached_json(resp.body);
        const Json* success = field(j, "success");
        if (success == nullptr || !success->is_boolean() || !success->get<bool>()) {
            return std::nullopt;
        }
        const Json* data = field(j, "data");
        if (data == nullptr) return std::nullopt;
        const Json* arr = field(*data, "data");
        if (arr == nullptr || !arr->is_array() || arr->empty()) return std::nullopt;
        Json rtn = Json::array();
        for (const auto& o : *arr) {
            const Json* segs = field(o, "segmentRoutes");
            if (segs == nullptr || !segs->is_array()) continue;
            for (const auto& seg : *segs) {
                const Json* pts = field(seg, "routePoints");
                if (pts == nullptr || !pts->is_array()) continue;
                for (const auto& p : *pts) rtn.push_back(p);
            }
        }
        if (rtn.empty()) return std::nullopt;
        return rtn.dump();
    } catch (...) {
        return std::nullopt;
    }
}

std::string trimNum6(double v) {
    // Java: BigDecimal.valueOf(v).setScale(6, HALF_UP).doubleValue() 再参与字符串拼接，
    // 拼出来的是 Double.toString 的形态（116.03809 而不是 116.038090）。
    // ⚠️ 极小数 Java 会印成 1.0E-6、C++ 印成 1e-06；这条分支需要真实腾讯服务才能验，
    //    本机不可达时恒走降级，不影响可观察行为。
    const double r = std::round(std::fabs(v) * 1e6) / 1e6 * (v < 0 ? -1.0 : 1.0);
    Json j(r);
    std::string s = j.dump();
    if (s.find('.') == std::string::npos && s.find('e') == std::string::npos) s += ".0";
    return s;
}

double round6(double v) { return std::round(std::fabs(v) * 1e6) / 1e6 * (v < 0 ? -1.0 : 1.0); }

std::string md5LowerHex(const std::string& s) {
    return cm::crypto::hex(cm::crypto::md5(s));
}

/** LonLatPathsUtils.calcLonAndLatPaths —— 整个方法体包在 catch(Exception){return null;} 里，
 *  连 result 为 null 造成的 NPE 都被吞掉，所以任何不顺利都是"返回 null ⇒ 上层降级"。 */
std::optional<std::string> tencentPaths(const std::string& curLon, const std::string& curLat,
                                        const std::string& nextLon, const std::string& nextLat,
                                        const std::string& heading, const std::string& waypoints) {
    try {
        const auto cur = GpsUtil::gps84ToGcj02(std::stod(curLat), std::stod(curLon));
        const auto next = GpsUtil::gps84ToGcj02(std::stod(nextLat), std::stod(nextLon));
        const std::string from = trimNum6(cur.first) + "," + trimNum6(cur.second);
        const std::string to = trimNum6(next.first) + "," + trimNum6(next.second);

        std::string url = cm::config::AppConfig::instance().getString("tx-service-url") + TX_URL +
                          "?from=" + from + "&to=" + to;
        if (StringUtils::isNotBlank(heading)) url += "&heading=" + heading;
        if (StringUtils::isNotBlank(waypoints)) url += "&waypoints=" + waypoints;
        url += std::string("&key=") + TX_KEY + "&sig=" +
               md5LowerHex(TrailGeometry::txSignatureSource(from, to, heading, waypoints) + TX_SECRET);

        const auto resp = cm::net::HttpClient::get(url);
        if (!resp.is2xx()) return std::nullopt;
        Json result = cm::utils::parse_cached_json(resp.body);
        if (cm::jlong(result, "status", -1) != 0) return std::nullopt;
        const Json* res = field(result, "result");
        if (res == nullptr) return std::nullopt;
        const Json* routes = field(*res, "routes");
        if (routes == nullptr || !routes->is_array() || routes->empty()) return std::nullopt;
        const Json* polyline = field((*routes)[0], "polyline");
        if (polyline == nullptr || !polyline->is_array()) return std::nullopt;

        // 折线是增量编码：前两个点是绝对值，之后每个点加"两个位置之前"的值
        const size_t n = polyline->size();
        std::vector<double> arr(n, 0.0);
        if (n == 0) return std::nullopt;
        arr[0] = (*polyline)[0].get<double>();
        if (n > 1) arr[1] = (*polyline)[1].get<double>();
        for (size_t i = 2; i < n; ++i) {
            arr[i] = arr[i - 2] + (*polyline)[i].get<double>() / 1000000.0;
        }

        Json rtn = Json::array();
        for (size_t i = 0; i + 1 < n; i += 2) {
            const auto gps = GpsUtil::gcj02ToGps84(arr[i], arr[i + 1]);
            const double lon = round6(gps.second);
            const double lat = round6(gps.first);
            rtn.push_back(Json::array({Json(lon), Json(lat)}));   // gpsG = {lon, lat}
        }
        return rtn.dump();
    } catch (...) {
        return std::nullopt;
    }
}

} // namespace

// ---------------------------------------------------------------- 纯函数

bool TrailGeometry::normalizePileno(const std::string& pileno, std::string& out) {
    // 顺序照抄：+→. ，然后 ZK、YK、K 依次删除（replace 是全量替换，不是只去前缀）
    std::string s = pileno;
    std::string tmp;
    for (size_t i = 0; i < s.size();) {
        if (s[i] == '+') { tmp.push_back('.'); ++i; continue; }
        if (s.compare(i, 2, "ZK") == 0) { i += 2; continue; }
        if (s.compare(i, 2, "YK") == 0) { i += 2; continue; }
        if (s[i] == 'K') { ++i; continue; }
        tmp.push_back(s[i++]);
    }
    bool neg = false;
    std::string intD, fracD;
    if (!splitDecimal(tmp, neg, intD, fracD)) return false;
    out = tmp;
    return true;
}

long long TrailGeometry::scale4ThenTrunc(const std::string& decimalText) {
    bool neg = false;
    std::string intD, fracD;
    if (!splitDecimal(decimalText, neg, intD, fracD)) return 0;
    return roundedIntegerPart(std::move(intD), std::move(fracD), 4, neg);
}

std::string TrailGeometry::txSignatureSource(const std::string& from, const std::string& to,
                                            const std::string& heading,
                                            const std::string& waypoints) {
    // sig() 用的是 LinkedHashMap，但随后 Arrays.sort(keySet()) ⇒ 顺序是 from,key,to,waypoints
    std::vector<std::pair<std::string, std::string>> params = {{"from", from}, {"to", to}};
    if (StringUtils::isNotBlank(heading)) params.emplace_back("heading", heading);
    if (StringUtils::isNotBlank(waypoints)) params.emplace_back("waypoints", waypoints);
    params.emplace_back("key", TX_KEY);
    std::vector<std::string> names;
    for (const auto& p : params) names.push_back(p.first);
    std::sort(names.begin(), names.end());
    std::string sb = std::string(TX_URL) + "?";
    for (size_t i = 0; i < names.size(); ++i) {
        const auto it = std::find_if(params.begin(), params.end(),
                                     [&](const auto& p) { return p.first == names[i]; });
        // ⚠️ 值为空白时 Java 只跳过 "名=值"，**不跳过分隔符**，于是留下一个光秃秃的 & —— 照抄
        if (it != params.end() && !StringUtils::trim(it->second).empty()) {
            sb += names[i] + "=" + StringUtils::trim(it->second);
        }
        if (i + 1 < names.size()) sb += "&";
    }
    return sb;
}

// ---------------------------------------------------------------- 三条回退链

/** getCarGeometry：纯本地桩号→geometry 表区间拼接。
 *  副作用：给命中的 TrailBo 写 pilenoDec（调用方共享同一批对象，响应里会带出来）。 */
Json TrailGeometry::carGeometry(const Json& tracks, std::vector<Json>& josnList) {
    (void)tracks;
    // LinkedHashMap(2) ⇒ 路线顺序 = roadCode 首次出现顺序
    std::vector<std::pair<std::string, std::vector<Json*>>> map;
    for (auto& bo : josnList) {
        const std::string roadCode = strField(bo, "roadCode");
        const std::string pileno = strField(bo, "pileno");
        if (StringUtils::isBlank(roadCode) || StringUtils::isBlank(pileno)) continue;
        std::string chang;
        if (!normalizePileno(pileno, chang)) {
            // Java: new BigDecimal(changPileno) 抛 NumberFormatException，没人接 ⇒ 500
            throw cm::exception::ServiceException(chang + " (java.lang.NumberFormatException)");
        }
        bo["pilenoDec"] = Json(toDouble(chang).value_or(0.0));
        bool hit = false;
        for (auto& e : map) {
            if (e.first == roadCode) { e.second.push_back(&bo); hit = true; break; }
        }
        if (!hit) map.emplace_back(roadCode, std::vector<Json*>{&bo});
    }

    const auto roadMap = roadGeometryGroups();
    Json out = Json::array();
    for (auto& [roadCode, list] : map) {
        if (list.empty()) continue;
        // reserver 取的是**排序前**的首/末位置
        int reserver = 0;
        const double firstDec = toDouble(strField(*list.front(), "pilenoDec")).value_or(0.0);
        const double lastDec = toDouble(strField(*list.back(), "pilenoDec")).value_or(0.0);
        if (firstDec > lastDec) reserver = 1;

        std::stable_sort(list.begin(), list.end(), [](Json* a, Json* b) {
            return toDouble(strField(*a, "pilenoDec")).value_or(0.0) <
                   toDouble(strField(*b, "pilenoDec")).value_or(0.0);
        });

        const long long sq = scale4ThenTrunc(strField(*list.front(), "pilenoDec"));
        long long sz = sq;
        if (list.size() > 1) {
            sz = scale4ThenTrunc(strField(*list.back(), "pilenoDec")) + 1;
        }

        std::vector<const GeomRow*> addlist;
        auto it = roadMap.find(roadCode);
        if (it != roadMap.end()) {
            for (const auto& filtbo : it->second) {
                const long long qd = filtbo.hasQdzh ? filtbo.qdzh : 0;
                const long long zd = filtbo.hasZdzh ? filtbo.zdzh : 0;
                int countNum = 0;
                if (qd <= sq && zd >= sz) countNum++;
                if (qd > sq && qd < sz) countNum++;
                if (zd > sq && zd < sz) countNum++;
                if (qd >= sq && zd <= sz) countNum++;
                if (countNum > 0) addlist.push_back(&filtbo);
            }
        }
        if (addlist.empty()) continue;

        Json pathsArr = Json::array();
        for (const GeomRow* g : addlist) {
            if (StringUtils::isBlank(g->paths)) continue;
            // hutool 的 JSONUtil.parseArray：paths 列本身是 JSON 数组文本
            Json sub = cm::utils::parse_cached_json(g->paths);
            if (sub.is_array()) for (auto& p : sub) pathsArr.push_back(p);
        }
        if (reserver == 1) std::reverse(pathsArr.begin(), pathsArr.end());
        out.push_back(geometryObject(Json(roadCode), pathsArr.dump()));
    }
    return out;
}

Json TrailGeometry::carGeometryByPlan(const Json& tracksIn, std::vector<Json>& josnList) {
    Json tracks = tracksIn;
    const bool tracksNull = tracks.is_null();
    if (tracksNull) tracks = Json::object();

    const Json* sLon = field(tracks, "startLonDec");
    const Json* sLat = field(tracks, "stratLatDec");
    const Json* eLon = field(tracks, "endLonDec");
    const Json* eLat = field(tracks, "endLatDec");
    if (sLon == nullptr || sLat == nullptr || eLon == nullptr || eLat == nullptr) {
        return carGeometry(tracks, josnList);
    }

    // ⚠️ 键用 toString() 语义、请求用 toPlainString()，Java 就是这样不一致的
    const std::string key = std::string(Constants::car_lxgh) + numberText(tracks, "plateKey") +
                            numberText(tracks, "startLonDec") + numberText(tracks, "stratLatDec") +
                            numberText(tracks, "endLonDec") + numberText(tracks, "endLatDec") +
                            std::to_string(josnList.size());

    Json lxbh = Json();                       // "" 起步，可能被置成 null（见下面的 quirk）
    std::string wayPoints;
    for (const auto& bo : josnList) {
        if (field(bo, "lon") == nullptr || field(bo, "lat") == nullptr) continue;
        const double lon = cm::jdouble(bo, "lon");
        const double lat = cm::jdouble(bo, "lat");
        const Json* rc = field(bo, "roadCode");
        // `"".equals(lxbh) && !"".equals(roadCode)`：roadCode 为 **null** 时后者也是 true，
        // 于是 lxbh 被置成 null，之后 "".equals(null) 恒 false ⇒ 整个方法里 lxbh 就锁死在 null。
        if (lxbh.is_string() && lxbh.get<std::string>().empty() &&
            !(rc != nullptr && rc->is_string() && rc->get<std::string>().empty())) {
            lxbh = rc ? *rc : Json(nullptr);
        }
        const auto gc = GpsUtil::gps84ToGcj02(lat, lon);
        if (!wayPoints.empty()) wayPoints += ";";
        wayPoints += trimNum6(gc.first) + "," + trimNum6(gc.second);   // 注意是 lat,lon
    }

    std::optional<std::string> paths;
    bool fromCache = false;
    if (auto cached = cm::redis::RedisCache::instance().get(key); cached && !cached->empty()) {
        // getCacheObject 拿到的若是 String，CommonUtil.isNull(obj) 就是 trim 后的串
        paths = CommonUtil::isNull(*cached);
        fromCache = true;
    }
    if (!fromCache) {
        // ⚠️ heading 传的是空串，于是 URL 与签名两处都被 isNotBlank 跳过
        paths = tencentPaths(numberText(tracks, "startLonDec"), numberText(tracks, "stratLatDec"),
                            numberText(tracks, "endLonDec"), numberText(tracks, "endLatDec"), "",
                            wayPoints);
        if (paths) cm::redis::RedisCache::instance().set(key, *paths);
    }
    if (!paths) return carGeometry(tracks, josnList);

    Json one = Json::array();
    one.push_back(geometryObject(lxbh, *paths));
    return one;
}

Json TrailGeometry::carGeometryByPlanNew(const Json& tracksIn, std::vector<Json>& josnList) {
    std::string apiMap = "1";
    if (auto cached = cm::redis::RedisCache::instance().get(Constants::API_MAP);
        cached && StringUtils::isNotBlank(*cached)) {
        apiMap = CommonUtil::isNull(*cached);
    }
    if (apiMap == "0") return carGeometryByPlan(tracksIn, josnList);

    Json tracks = tracksIn;
    if (tracks.is_null()) tracks = Json::object();

    const std::string en = strField(tracks, "entollstationid");
    const std::string ex = strField(tracks, "extollstationid");
    if (StringUtils::isBlank(en) || StringUtils::isBlank(ex)) {
        return carGeometryByPlan(tracks, josnList);
    }

    std::vector<std::string> nodeIds;
    nodeIds.push_back(en);
    Json lxbh = Json();
    for (const auto& bo : josnList) {
        const Json* rc = field(bo, "roadCode");
        if (lxbh.is_string() && lxbh.get<std::string>().empty() &&
            !(rc != nullptr && rc->is_string() && rc->get<std::string>().empty())) {
            lxbh = rc ? *rc : Json(nullptr);
        }
        const std::string devCode = strField(bo, "devCode");
        if (StringUtils::isNotBlank(devCode)) nodeIds.push_back(devCode);
    }
    nodeIds.push_back(ex);

    const std::string key = std::string(Constants::car_lxgh) + numberText(tracks, "plateKey") +
                            en + ex + std::to_string(josnList.size());

    std::optional<std::string> paths;
    bool fromCache = false;
    if (auto cached = cm::redis::RedisCache::instance().get(key); cached && !cached->empty()) {
        paths = CommonUtil::isNull(*cached);
        fromCache = true;
    }
    if (!fromCache) {
        paths = shortestRoadPath(nodeIds);
        if (paths) cm::redis::RedisCache::instance().set(key, *paths);
    }
    if (!paths) return carGeometryByPlan(tracks, josnList);

    Json one = Json::array();
    one.push_back(geometryObject(lxbh, *paths));
    return one;
}

/** getTrailDevBO：设备分组只看 stateType 是 GantryCapture / FeeRecord 的点。 */
Json TrailGeometry::trailDevCountBo(const Json& tracksIn, std::vector<Json>& josnList) {
    Json tracks = tracksIn;
    if (tracks.is_null()) tracks = Json::object();

    long long exceptNum = 0;
    Json trailDevList = Json::array();
    std::map<std::string, std::vector<Json*>> map;
    std::vector<Json*> rtnList;

    for (auto& bo : josnList) {
        const std::string stateType = strField(bo, "stateType");
        const std::string devName = strField(bo, "devName");
        if (stateType == Constants::GANTRY_CAPTURE || stateType == Constants::FEE_RECORD) {
            if (StringUtils::isNotBlank(devName)) {
                auto it = map.find(devName);
                if (it == map.end()) {
                    rtnList.push_back(&bo);      // 每个设备只留一个代表
                    map[devName].push_back(&bo);
                } else {
                    it->second.push_back(&bo);   // 同设备的后续点只进组，不进 rtnList
                }
            } else {
                rtnList.push_back(&bo);          // devName 为空的既不分组也不计入异常
            }
        } else {
            rtnList.push_back(&bo);
        }
    }

    for (Json* bo : rtnList) {
        const std::string stateType = strField(*bo, "stateType");
        const std::string devName = strField(*bo, "devName");
        Json devBo = Json::object();
        devBo["status"] = Json("0");
        Json trailList = Json::array();

        if (stateType == Constants::GANTRY_CAPTURE || stateType == Constants::FEE_RECORD) {
            auto it = map.find(devName);
            if (it != map.end()) {
                int conutGantryCapture = 0, conutFeeRecord = 0;
                for (Json* m : it->second) {
                    const std::string st = strField(*m, "stateType");
                    if (st == Constants::GANTRY_CAPTURE) conutGantryCapture++;
                    else if (st == Constants::FEE_RECORD) conutFeeRecord++;
                }
                // "有牌识、无流水" 才算这个设备异常 —— 按**设备组**计数，不是按点
                if (conutGantryCapture > 0 && conutFeeRecord == 0) {
                    devBo["status"] = Json("1");
                    exceptNum++;
                }
                for (Json* m : it->second) trailList.push_back(*m);
            } else {
                trailList.push_back(*bo);
            }
        } else {
            trailList.push_back(*bo);
        }
        devBo["devName"] = Json(devName);
        devBo["trailList"] = trailList;
        trailDevList.push_back(devBo);
    }

    // TrailDevBO 的字段声明序是 status/devName，TrailDevCountBO 是 exceptNum/TrailDevList/trailList/exceptMsg
    Json all = Json::array();
    for (const auto& bo : josnList) all.push_back(bo);

    std::string tips;
    if (field(tracks, "startLonDec") == nullptr || field(tracks, "stratLatDec") == nullptr) {
        tips = "起始位置";
    }
    if (field(tracks, "endLonDec") == nullptr || field(tracks, "endLatDec") == nullptr) {
        tips = tips.empty() ? std::string("终点位置") : tips + "和终点位置";
    }
    std::string exceptMsg;
    if (StringUtils::isNotBlank(tips)) {
        exceptMsg = "由于无法获取轨迹" + tips +
                    "，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。";
    }

    Json bo = Json::object();
    bo["exceptNum"] = Json(exceptNum);
    bo["trailDevList"] = trailDevList;   // ⚠️ Java 字段名是大写开头的 TrailDevList，JSON 键是 trailDevList
    bo["trailList"] = all;               // 与调用方的 trailList 是同一批对象 ⇒ 响应里重复出现
    bo["exceptMsg"] = Json(exceptMsg);
    return bo;
}

} // namespace cm::base
