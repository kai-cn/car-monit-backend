// 轨迹几何相关的三条端点。对应 Java:
//   CarTrackInfoController#changeTrailInfo（PUT /manager/cartrackinfo/changeTrailInfo）
//   CarSuspiciousController#listFileCarNo（GET /manager/suspicious/listFileCarNo）
//   CarSuspiciousController#gethistoryInfo（GET /manager/suspicious/history/{id}）
// 加上 CarSuspiciousServiceImpl.selectCarSuspiciousById / selectCarSuspiciousHistoryById
// 与 CarQueryLogServiceImpl.queryLog。
// 另有两条依赖外部接口的轨迹入口：
//   CarTrackInfoController#listByCarId（GET /manager/cartrackinfo/listByCarId）
//   CarTrackInfoController#carSnapShot（GET /manager/cartrackinfo/carSnapShot）
//
// 这三条都只是"把同一段轨迹计算套在不同入口上"，真正的回退链在 TrailGeometry.hpp 顶部。
// 需要照抄的行为：
//   * 响应里的实体投影是 **Jackson**（声明序 + null 全输出），与 Redis 里那套 fastjson2
//     （按名排序 + null 省略）是两种不同形态，不能混用。
//   * getCarGeometry 会往 TrailBo 上写 pilenoDec，而 controller 用的是同一个 list 对象 ⇒
//     响应里 trailList 与 trailDevCountBO.trailList 都带出这个副作用（同一批点出现两遍）。
//   * listFileCarNo 的 total 是 rtnList.size()，不是数据库总数（PageInfo 拿到的是普通
//     ArrayList）；startPage() 只作用于第一条 mapper 查询，也就是列表本身。
//   * listFileCarNo 在查询前强行覆盖 carNo("-1")/isExcept("1")/checkStatus("1")，
//     调用方传的 isExcept/checkStatus 一律被丢弃。
//   * escapedTypeName 是 label 逐个拼 "x,"，**结尾那个逗号不删**（其他地方都会 deleteEnd）。
//   * chargeAmount/totalAmount/difAmount 在 CarSuspicious 上是 **String**，值是 BigDecimal
//     累加后的 toString() ⇒ 标度按加数最大标度保留（"0" + "12.50" = "12.50"）。
#include "cm/web/controller/manager/ManagerTrailInfoControllers.hpp"

#include <algorithm>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "cm/base/service/TrailGeometry.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/aspect/OperLogAspect.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/system/mapper/SysDictDataMapper.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/controller/manager/ManagerExtraControllers.hpp"
#include "cm/web/specs/BaseCrudSpecs.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"
#include "cm/web/util/ImportExcel.hpp"
#include "cm/web/util/SuspiciousShared.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::CommonUtil;
using cm::utils::DateUtils;
using cm::utils::StringUtils;
using cm::web::crud::Fmt;
using cm::web::crud::Spec;

// ---------------------------------------------------------------- 实体投影

/** 属性缺失/为 null 与"值类型不对"在 Java 里都有确定结果：
 *  缺失 ⇒ setter 不调用 ⇒ 字段初值；这里没有初值的实体就统一 null。 */
Json projectViaSpec(const Spec& spec, const Json& src) {
    Json out = Json::object();
    for (const auto& f : spec.fields) {
        const std::string key(f.json);
        if (!src.is_object() || !src.contains(key) || src[key].is_null()) {
            out[key] = f.dflt ? Json::parse(f.dflt) : Json(nullptr);
            continue;
        }
        const Json& v = src[key];
        if (v.is_array() || v.is_object()) {
            out[key] = v;               // List/嵌套对象原样（见 projectTrailBo 里同类取舍的说明）
            continue;
        }
        switch (f.fmt) {
            case Fmt::Int:
            case Fmt::Long:
                if (v.is_number()) out[key] = Json(static_cast<long long>(v.get<double>()));
                else if (v.is_boolean()) out[key] = Json(v.get<bool>() ? 1 : 0);
                else {
                    try { out[key] = Json(std::stoll(v.get<std::string>())); }
                    catch (...) { out[key] = Json(nullptr); }
                }
                break;
            case Fmt::Double:
                if (v.is_number()) out[key] = v;
                else {
                    try { out[key] = Json(std::stod(v.get<std::string>())); }
                    catch (...) { out[key] = Json(nullptr); }
                }
                break;
            case Fmt::Bool:
                if (v.is_boolean()) out[key] = v;
                else if (v.is_string()) out[key] = Json(v.get<std::string>() == "true");
                else out[key] = Json(v.get<double>() != 0.0);
                break;
            case Fmt::DateYmd:
            case Fmt::DateYmdHms:
            case Fmt::DateIso:
            case Fmt::DateTimeIso:
                // @JsonFormat 的字段输出字符串；数字（epoch millis）按同一格式渲染
                if (v.is_number()) {
                    out[key] = Json(DateUtils::formatMillis(
                        static_cast<long long>(v.get<double>()),
                        f.fmt == Fmt::DateYmd ? DateUtils::YYYY_MM_DD
                                              : DateUtils::YYYY_MM_DD_HH_MM_SS));
                } else {
                    out[key] = v;
                }
                break;
            default:
                out[key] = v.is_string() ? v : Json(v.dump());
                break;
        }
    }
    return out;
}

Json projectTracks(const Json& src) {
    return projectViaSpec(cm::web::crud::specZdataTrailTracks(), src);
}

Json jarrOf(const std::vector<Json>& items) {
    Json a = Json::array();
    for (const auto& i : items) a.push_back(i);
    return a;
}

/** TrailInfo 的 6 个键（trailUuid/enterTime/tracks/trailList/raodTrailList/trailDevCountBO）。
 *  ⚠️ enterTime 在 TrailInfo 上**没有** @JsonFormat，而 ZdataTrailTracks.enterTime 有 ——
 *     同一个时间值，前者输出 epoch 毫秒数字、后者输出 "yyyy-MM-dd HH:mm:ss" 字符串。
 *     这个不对称是真的，别统一。 */
Json projectTrailInfo(const Json& src) {
    Json out = Json::object();
    out["trailUuid"] = src.contains("trailUuid") && !src["trailUuid"].is_null()
                           ? (src["trailUuid"].is_string() ? src["trailUuid"]
                                                           : Json(src["trailUuid"].dump()))
                           : Json(nullptr);
    if (src.contains("enterTime") && !src["enterTime"].is_null()) {
        const Json& v = src["enterTime"];
        if (v.is_number()) {
            out["enterTime"] = v;
        } else {
            auto ms = DateUtils::parseDbDateTime(v.get<std::string>());
            out["enterTime"] = ms ? Json(static_cast<long long>(*ms)) : Json(nullptr);
        }
    } else {
        out["enterTime"] = Json(nullptr);
    }
    out["tracks"] = src.contains("tracks") && !src["tracks"].is_null()
                        ? projectTracks(src["tracks"]) : Json(nullptr);

    std::vector<Json> list;
    const bool hasList = src.contains("trailList") && src["trailList"].is_array();
    if (hasList) {
        for (const auto& e : src["trailList"]) list.push_back(projectTrailBoJson(e));
    }
    // 没带 / 显式 null 都是 null：TrailInfo 没有任何字段初始值，setter 不调用就是 null，
    // 输出 [] 等于凭空多一个元素类型不同的值
    out["trailList"] = hasList ? jarrOf(list) : Json(nullptr);
    out["raodTrailList"] = src.contains("raodTrailList") && !src["raodTrailList"].is_null()
                               ? src["raodTrailList"] : Json(nullptr);
    out["trailDevCountBO"] = src.contains("trailDevCountBO") && !src["trailDevCountBO"].is_null()
                                 ? src["trailDevCountBO"] : Json(nullptr);
    return out;
}

// ---------------------------------------------------------------- BigDecimal 加法

/** 十进制文本按 scale=max(scaleA, scaleB) 相加，输出 BigDecimal.toString() 的形态。
 *  DECIMAL 列取回来就是普通十进制串，不需要处理指数。 */
std::string bigDecimalAdd(const std::string& a, const std::string& b) {
    auto split = [](const std::string& s, bool& neg, std::string& ip, std::string& fp) {
        neg = false;
        size_t i = 0;
        if (!s.empty() && (s[0] == '-' || s[0] == '+')) { neg = s[0] == '-'; i = 1; }
        const size_t dot = s.find('.', i);
        ip = s.substr(i, dot == std::string::npos ? std::string::npos : dot - i);
        fp = dot == std::string::npos ? std::string() : s.substr(dot + 1);
        if (ip.empty()) ip = "0";
    };
    bool na = false, nb = false;
    std::string ia, fa, ib, fb;
    split(a, na, ia, fa);
    split(b, nb, ib, fb);
    const size_t scale = std::max(fa.size(), fb.size());
    fa.append(scale - fa.size(), '0');
    fb.append(scale - fb.size(), '0');
    // 整数部分补到同宽后按 "整数+小数" 的长整数字符串做加减
    ia.insert(0, std::max(ia.size(), ib.size()) - ia.size(), '0');
    ib.insert(0, std::max(ia.size(), ib.size()) - ib.size(), '0');
    std::string da = ia + fa, db = ib + fb;
    bool neg = false;
    std::string res;
    const auto cmpAbs = [](const std::string& x, const std::string& y) {
        if (x.size() != y.size()) return x.size() < y.size() ? -1 : 1;
        return x < y ? -1 : (x > y ? 1 : 0);
    };
    const auto addAbs = [](const std::string& x, const std::string& y) {
        std::string out;
        int carry = 0;
        for (size_t i = x.size(); i-- > 0;) {
            int s = (x[i] - '0') + (y[i] - '0') + carry;
            out.push_back(static_cast<char>('0' + s % 10));
            carry = s / 10;
        }
        if (carry) out.push_back(static_cast<char>('0' + carry));
        std::reverse(out.begin(), out.end());
        return out;
    };
    const auto subAbs = [](std::string x, std::string y) {   // 假定 x >= y
        std::string out;
        int borrow = 0;
        for (size_t i = x.size(); i-- > 0;) {
            int d = (x[i] - '0') - borrow - (i < y.size() ? (y[i] - '0') : 0);
            borrow = d < 0 ? 1 : 0;
            if (d < 0) d += 10;
            out.push_back(static_cast<char>('0' + d));
        }
        std::reverse(out.begin(), out.end());
        size_t p = 0;
        while (p + 1 < out.size() && out[p] == '0') ++p;
        return out.substr(p);
    };
    if (na == nb) {
        res = addAbs(da, db);
        neg = na;
    } else {
        const int c = cmpAbs(da, db);
        res = c < 0 ? subAbs(db, da) : (c > 0 ? subAbs(da, db) : std::string("0"));
        neg = c < 0 ? nb : (c > 0 ? na : false);
    }
    while (res.size() < scale + 1) res.insert(res.begin(), '0');
    std::string ip = res.substr(0, res.size() - scale);
    std::string fp = res.substr(res.size() - scale);
    size_t p = 0;
    while (p + 1 < ip.size() && ip[p] == '0') ++p;
    ip = ip.substr(p);
    // BigDecimal.toString()：scale>0 就保留尾随 0（这正是这里要复刻的重点）
    std::string text = (neg && res != std::string(scale, '0') ? "-" : "") + ip +
                       (scale ? "." + fp : std::string());
    return text;
}

// ---------------------------------------------------------------- 查询

// mustRunSql / suspiciousByIdRow 见 cm/web/util/SuspiciousShared.hpp
cm::db::Result mustRun(const std::string& sql) { return mustRunSql(sql); }

std::map<std::string, std::string> dictValueToLabel(const std::string& dictType) {
    cm::domain::SysDictData q;
    q.dictType = dictType;
    std::map<std::string, std::string> out;
    for (const auto& d : cm::system::mapper::SysDictDataMapper::selectDictDataList(q)) {
        const std::string value = d.dictValue ? *d.dictValue : std::string();
        const std::string label = d.dictLabel ? *d.dictLabel : std::string();
        auto it = out.find(value);
        if (it != out.end()) {
            throw cm::exception::ServiceException("Duplicate key " + value +
                                                  " (attempted merging values " + it->second +
                                                  " and " + label + ")");
        }
        out.emplace(value, label);
    }
    return out;
}

/** car_suspicious / car_suspicious_back 的 by-id 查询：Vo 之外还要 track_josn */
Json suspiciousByIdRow(const Spec& spec, const std::string& table, const std::string& id) {
    return cm::web::suspiciousByIdRow(spec, table, id);
}

/** selectCarSuspiciousCheckList(CarSuspiciousCheck{carId=id})。
 *  把原始行也带出去：三个金额在 Java 侧是 BigDecimal，累加必须用库里的原文标度
 *  （"0" + "12.50" = "12.50"），走一遍 double 就变成 12.5 了。 */
cm::db::Result checkRows(const std::string& carId) {
    const Spec& spec = cm::web::crud::specCarSuspiciousCheck();
    Json q = Json::object();
    q["carId"] = Json(carId);
    return mustRun(cm::web::crud::selectSqlOf(spec, cm::web::crud::buildWhere(spec, q),
                                              " ORDER BY " + spec.orderBy));
}

Json checkListJsonOf(const cm::db::Result& res) {
    const Spec& spec = cm::web::crud::specCarSuspiciousCheck();
    Json arr = Json::array();
    for (const auto& row : res.rows) arr.push_back(cm::web::crud::rowToJson(spec, row));
    return arr;
}

/** CarSuspiciousServiceImpl.selectCarSuspiciousById 里"查询实时轨迹"那一段。
 *  tracks / carTrailList 都以**可变**形态交给 TrailGeometry，因为 pilenoDec 的副作用
 *  要体现在最终的 JSON 上 —— 所以这里先投影成实体形态、再把投影结果交进去算。 */
void attachSuspiciousTrail(Json& row) {
    const std::string trackJosn = cm::jstr(row, "trackJosn");
    Json trailInfo = Json::object();
    std::vector<Json> carTrailList;
    Json raodTrailList = Json::array();
    bool haveList = false;

    if (StringUtils::isNotBlank(trackJosn)) {
        trailInfo = cm::utils::parse_cached_json(trackJosn);
        Json projected = projectTrailInfo(trailInfo);
        const Json tracks = projected.contains("tracks") ? projected["tracks"] : Json(nullptr);
        if (projected.contains("trailList") && projected["trailList"].is_array()) {
            for (const auto& e : projected["trailList"]) carTrailList.push_back(e);
            haveList = true;
        }
        if (haveList && !carTrailList.empty()) {
            raodTrailList = cm::base::TrailGeometry::carGeometryByPlanNew(tracks, carTrailList);
        }
        projected["trailUuid"] = Json(cm::jstr(row, "carNo"));
        projected["trailList"] = haveList ? jarrOf(carTrailList) : projected["trailList"];
        projected["raodTrailList"] = raodTrailList;
        // ⚠️ getTrailDevBO 无条件调用，而 carTrailList 为 null 时 Java 在 for-each 上抛 NPE
        if (!haveList) throw cm::exception::NullPointerException();
        projected["trailDevCountBO"] =
            cm::base::TrailGeometry::trailDevCountBo(tracks, carTrailList);
        trailInfo = projected;
    }

    Json arr = Json::array();
    arr.push_back(trailInfo.is_object() && trailInfo.empty() ? projectTrailInfo(Json::object())
                                                             : trailInfo);
    row["trailList"] = arr;
}

// ---------------------------------------------------------------- 端点

/** CarQueryLogServiceImpl.queryLog(cond,"1","1") → saveCarQueryLog → MP insert。
 *  CarQueryLog extends BasePlusEntity：ASSIGN_UUID + insertFill ⇒ id/create_by/create_time/eps_id
 *  由框架补；⚠️ insertFill 里 tenantId 判的是 "epsId == null"（Java 的复制粘贴错误），
 *  所以已认证请求填了 epsId 之后 **tenantId 不会被填**。del_flag 走库默认值。 */
void queryLog(const std::string& queryCondition, const std::string& modelType,
              const std::string& menuPoint) {
    const long long userId = cm::security::SecurityUtils::getUserId();
    const long long epsId = cm::security::SecurityUtils::getEpsId();
    std::string loginIp;
    if (auto lu = cm::security::SecurityUtils::current(); lu && lu->user.loginIp) {
        loginIp = *lu->user.loginIp;
    }
    mustRun("INSERT INTO car_query_log (id, user_id, user_name, user_ip, model_type, menu_point,"
            " query_condition, create_by, create_time, eps_id) VALUES (" +
            cm::db::bind(cm::utils::simpleUuid()) + ", " + cm::db::bind(std::to_string(userId)) + ", " +
            cm::db::bind(cm::security::SecurityUtils::getUserRealName()) + ", " + cm::db::bind(loginIp) +
            ", " + cm::db::bind(modelType) + ", " + cm::db::bind(menuPoint) + ", " +
            cm::db::bind(queryCondition) + ", " + std::to_string(userId) + ", " +
            cm::db::bind(DateUtils::getTime()) + ", " + std::to_string(epsId) + ")");
}

/** PUT /manager/cartrackinfo/changeTrailInfo */
cm::http::ApiResponse changeTrailInfo(RequestContext& ctx) {
    Json body = cm::parse_json(ctx.req.body);
    // queryLog 在轨迹计算**之前**，且写的是 fastjson2 的紧凑形态（丢 null）——
    // 与响应里 Jackson 的完整形态不是同一份文本。
    queryLog(cm::aspect::fastJsonCompact(body, {}, true), "1", "1");   // POJO ⇒ 字段名排序

    Json trailInfo = projectTrailInfo(body);
    const bool tracksOk = body.contains("tracks") && !body["tracks"].is_null();
    const bool listOk = body.contains("trailList") && body["trailList"].is_array() &&
                        !body["trailList"].empty();
    if (tracksOk && listOk) {
        std::vector<Json> josnList;
        for (const auto& e : trailInfo["trailList"]) josnList.push_back(e);
        Json raod = cm::base::TrailGeometry::carGeometryByPlanNew(trailInfo["tracks"], josnList);
        trailInfo["trailList"] = jarrOf(josnList);      // 带 pilenoDec 副作用的同一批对象
        trailInfo["raodTrailList"] = raod;
        trailInfo["trailDevCountBO"] =
            cm::base::TrailGeometry::trailDevCountBo(trailInfo["tracks"], josnList);
    }
    return BaseController::ok(AjaxResult::success(trailInfo));
}

/** GET /manager/suspicious/listFileCarNo */
cm::http::ApiResponse listFileCarNo(RequestContext& ctx) {
    const Spec& spec = cm::web::crud::specCarSuspicious();
    Json query = cm::web::crud::bindQuery(spec, ctx);
    // startPage() 之后的这三行覆盖在**查询对象**上，客户端传的 isExcept/checkStatus 会被丢掉
    const std::string carNo = cm::jstr(query, "carNo");
    if (StringUtils::isBlank(carNo)) query["carNo"] = Json("-1");
    query["isExcept"] = Json("1");
    query["checkStatus"] = Json("1");

    const auto page = ctx.pageRequest();
    const std::string where = cm::web::crud::buildWhere(spec, query);
    const std::string order = " ORDER BY " + (!page.orderBy.empty() ? page.orderBy : spec.orderBy);
    const std::string dataSql = cm::web::crud::selectSqlOf(spec, where, order);

    std::vector<cm::db::Row> rows;
    if (page.enabled) {
        auto pr = cm::db::queryPage("select count(1) from (" + dataSql + ") page_count", dataSql,
                                    page);
        rows = pr.rows.rows;
    } else {
        rows = mustRun(dataSql).rows;
    }

    const auto escapedTypeMap = dictValueToLabel("escaped_type");
    Json rtnList = Json::array();
    for (const auto& row : rows) {
        Json one = cm::web::crud::rowToJson(spec, row);
        const std::string id = cm::jstr(one, "id");
        Json rtn = suspiciousByIdRow(spec, "car_suspicious", id);
        if (rtn.is_null()) {
            // Java: selectCarSuspiciousById 返回 null 后直接 rtn.getCheckList() ⇒ NPE ⇒ 500
            throw cm::exception::NullPointerException();
        }
        const cm::db::Result checked = checkRows(id);
        rtn["checkList"] = checkListJsonOf(checked);
        attachSuspiciousTrail(rtn);

        // checkList 一定是数组（非 null），所以 Java 那段求和恒定执行；
        // 只要有一行的金额为 NULL，BigDecimal.add(null) 就 NPE ⇒ 整个请求 500
        std::string chargeAmount = "0", totalAmount = "0", difAmount = "0";
        for (const auto& c : checked.rows) {
            const auto add = [&](const char* col, std::string& acc) {
                const auto v = c.get(col);
                if (!v) throw cm::exception::NullPointerException();
                acc = bigDecimalAdd(acc, *v);
            };
            add("charge_amount", chargeAmount);
            add("total_amount", totalAmount);
            add("dif_amount", difAmount);
        }
        rtn["chargeAmount"] = Json(chargeAmount);
        rtn["totalAmount"] = Json(totalAmount);
        rtn["difAmount"] = Json(difAmount);
        const std::string bussType = CommonUtil::deleteEnd(cm::jstr(rtn, "escapedType"));
        if (StringUtils::isNotBlank(bussType)) {
            std::string bussName;
            for (const auto& one : cm::web::importx::javaSplitComma(bussType)) {
                auto it = escapedTypeMap.find(one);
                if (it != escapedTypeMap.end()) bussName += it->second + ",";
            }
            rtn["escapedTypeName"] = Json(bussName);   // ⚠️ 结尾逗号保留
        }
        rtnList.push_back(rtn);
    }
    // ⚠️ total = rtnList.size()，不是 DB count
    return BaseController::ok(BaseController::dataTable(rtnList, static_cast<long long>(rtnList.size())));
}

/** GET /manager/suspicious/history/{id} */
cm::http::ApiResponse historyById(RequestContext& ctx) {
    const Spec& spec = cm::web::suspiciousHistorySpec();
    const std::string id = ctx.pathVar("id");
    Json row = suspiciousByIdRow(spec, "car_suspicious_back", id);
    if (row.is_null()) return BaseController::ok(AjaxResult::success(row));
    row["checkList"] = checkListJsonOf(checkRows(id));
    attachSuspiciousTrail(row);
    return BaseController::ok(AjaxResult::success(row));
}

// ---------------------------------------------------------------- 外部接口（Forest）
// com.ruoyi.base.service.forest.HttpSysUtilApiService：
//   @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base/sysutil")
// 两条都没有 try/catch，所以上游连不上就是异常 → HTTP 200 + code:500（与全站约定一致）。
std::string sysutilUrl(const std::string& path) {
    return cm::config::AppConfig::instance().vehicleMonitorBaseUrl + "/base/sysutil" + path;
}

/** TrailDevCountBO 的空壳：控制器两条分支都手搭这一个对象（字段声明序见 Java 类）。 */
Json emptyTrailDevCount() {
    Json d = Json::object();
    d["exceptNum"] = Json(0);
    d["trailDevList"] = Json::array();
    d["trailList"] = Json(nullptr);
    d["exceptMsg"] = Json(nullptr);
    return d;
}

/** GET /manager/cartrackinfo/listByCarId
 *  本地查不到才回退远程，而**回退命中时会写库**（先按车牌删、再 saveBatch），
 *  这个写副作用是 Java 原样，不是这里的发明。 */
cm::http::ApiResponse listByCarId(RequestContext& ctx) {
    Json query = cm::web::crud::bindQuery(cm::web::crud::specZdataTrailTracks(), ctx);
    // Java: setCarNo(CommonUtil.isNull(getCarNo())) 顺带 trim，再 blank 兜成 "-1"（查不到而不是查全表）
    std::string carNo = CommonUtil::isNull(cm::jstr(query, "carNo"));
    if (StringUtils::isBlank(carNo)) carNo = "-1";
    query["carNo"] = Json(carNo);

    auto local = cm::web::carTrackQueryLocal(ctx, query);
    Json rtnList = std::move(local.rtnList);
    long long totalNum = local.total;

    // 判的是 DB 行数：track_josn 全空的行进不了 rtnList，但照样算"有数据"⇒ 不回退
    if (!local.hasRows) {
        // @Query CarParaVO 只带非 null 属性，声明序 carNo/pageNum/pageSize（实机抓包核对）
        std::vector<std::pair<std::string, std::string>> params = {
            {"carNo", carNo}, {"pageNum", "1"}, {"pageSize", "20"}};
        auto resp = cm::net::HttpClient::getWithQuery(sysutilUrl("/carTrackQueryByCarNo"), params);
        if (!resp.ok()) throw cm::exception::ServiceException(resp.error);
        // Forest 的目标类型是 TableDataInfo：空响应体解出 null，紧接着 .getRows() 就是 NPE
        if (resp.body.empty()) throw cm::exception::NullPointerException();
        Json body = Json::parse(resp.body);
        const Json rows = body.is_object() && body.contains("rows") ? body["rows"] : Json(nullptr);
        if (rows.is_array() && !rows.empty()) {
            std::vector<Json> addlist;    // 落库那份：只带非 null 属性（MyBatis-Plus NOT_NULL）
            for (const auto& row : rows) {
                Json info = projectTrailInfo(row);
                const bool hasTracks = row.is_object() && row.contains("tracks") &&
                                       !row["tracks"].is_null();
                // Java: trailInfo.getTracks() 是 null 的话下一句 getPlateKey() 就 NPE ⇒ 500
                if (!hasTracks) throw cm::exception::NullPointerException();
                Json entity = row["tracks"];
                entity["plateKey"] = Json(CommonUtil::isNull(cm::jstr(entity, "plateKey")));
                entity["pointCount"] = Json(static_cast<long long>(0));
                const Json trailList = info["trailList"];
                if (!trailList.is_null()) {
                    // 存的是 fastjson2 的形态（按名排序、null 省略），不是 Jackson 那份
                    entity["trackJosn"] = Json(cm::aspect::fastJsonCompact(trailList, {}, true));
                    entity["pointCount"] = Json(static_cast<long long>(trailList.size()));
                }
                addlist.push_back(entity);
                // 响应里的 tracks 就是这同一个被改过的对象 ⇒ 序列化时带上这三处修改
                info["tracks"] = projectTracks(entity);
                info["raodTrailList"] = Json::array();
                info["trailDevCountBO"] = emptyTrailDevCount();
                rtnList.push_back(std::move(info));
            }
            // 这条链路上没有事务：删先提交、再逐条插（插到一半失败，删掉的也回不来）
            Db::instance().execute("delete from zdata_trail_tracks t where plate_key in (" +
                                   cm::db::bind(carNo) + ")");
            for (const auto& e : addlist) {
                Db::instance().execute(
                    cm::web::crud::buildInsert(cm::web::crud::specZdataTrailTracks(), e));
            }
            totalNum = body.contains("total") && body["total"].is_number()
                           ? static_cast<long long>(body["total"].get<double>()) : 0;
        }
    }
    // 手搭的 TableDataInfo：code=200 / msg=查询成功 / total 先是 PageInfo(carlist)，回退命中后换成远程的 total
    return BaseController::ok(BaseController::dataTable(rtnList, totalNum));
}

/** GET /manager/cartrackinfo/carSnapShot —— 整条链路都是外部接口，
 *  两个前置条件不齐就直接给个空的 success。 */
cm::http::ApiResponse carSnapShot(RequestContext& ctx) {
    Json bo = cm::web::bindTrailBoQuery(ctx);
    // stateType 过了 isNull（顺带 trim），pointUuid 没过 —— 这个不对称照抄
    const std::string stateType = CommonUtil::isNull(cm::jstr(bo, "stateType"));
    const std::string pointUuid = cm::jstr(bo, "pointUuid");
    if (StringUtils::isBlank(stateType) || StringUtils::isBlank(pointUuid)) {
        return BaseController::ok(AjaxResult::success());   // 没有 data 键
    }
    auto resp = cm::net::HttpClient::getWithQuery(sysutilUrl("/getByTrailBo"),
                                                  cm::web::flattenTrailBoQuery(bo));
    if (!resp.ok()) throw cm::exception::ServiceException(resp.error);
    if (resp.body.empty()) {
        // Forest 解出 null ⇒ AjaxResult.success((Object) null) ⇒ 依旧没有 data 键
        return BaseController::ok(AjaxResult::success());
    }
    Json body = Json::parse(resp.body);
    if (!body.is_object()) {
        throw cm::exception::ServiceException("can not cast to TrailBo, value : " + resp.body);
    }
    // 声明的返回类型是 TrailBo 本体：上游要是返 AjaxResult 信封，32 个键会全成 null
    return BaseController::ok(AjaxResult::success(projectTrailBoJson(body)));
}

}  // namespace

void registerManagerTrailInfoControllers(Router& r) {
    r.put("/manager/cartrackinfo/changeTrailInfo",
          [](RequestContext& ctx) { return changeTrailInfo(ctx); });
    r.get("/manager/suspicious/listFileCarNo",
          [](RequestContext& ctx) { return listFileCarNo(ctx); });
    r.get("/manager/suspicious/history/{id}", [](RequestContext& ctx) { return historyById(ctx); });
    r.get("/manager/cartrackinfo/listByCarId", [](RequestContext& ctx) { return listByCarId(ctx); });
    r.get("/manager/cartrackinfo/carSnapShot", [](RequestContext& ctx) { return carSnapShot(ctx); });
}

}  // namespace cm::web
