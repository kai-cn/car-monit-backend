// 对应 Java: com.ruoyi.web.controller.manager.{CarSuspicious,CarExceptRecord,CarConfimFree,CarAduitFree}Controller
//            的非同构 CRUD 接口
//
// 这批端点的共同套路是“先给查询对象塞一个默认值（查不到而不是查全表），再走原本的分页查询”，
// 所以直接复用生成器暴露的 Spec（include/cm/web/specs/ManagerCrudSpecs.hpp），
// 只在其上叠加 Java 里的前置条件；统计类接口则是 XML 里独立的 group by 语句。
#include "cm/web/controller/manager/ManagerExtraControllers.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/aspect/OperLogAspect.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/BaseCrudSpecs.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::CommonUtil;
using cm::utils::StringUtils;
using namespace cm::web::crud;

/** 对应 CommonUtil.isBlank(getX()) -> setX("-1")：不传或全空白都算空 */
void presetBlank(Json& query, const char* key) {
    std::string v;
    if (query.contains(key) && !query[key].is_null()) {
        if (query[key].is_string()) v = query[key].get<std::string>();
    }
    if (!StringUtils::isBlank(v)) return;
    query[key] = "-1";
}

/** TrailBo（com.ruoyi.base.domain.vo.TrailBo）的字段声明序与类型。
 *  listByCarByTime 把 track_josn 用 fastjson 反序列化成 List<TrailBo> 再交给 Jackson，
 *  于是"track_josn 里多出来的键被丢掉、缺的键输出 null、顺序按声明序"这三件事同时成立 ——
 *  照抄字段表才能一模一样，不能把解析结果原样吐回去。 */
enum class Tk { Str, Num, Bool, Obj };
// TrailBo 的 32 个字段，声明序。中间那 9 个是**包级私有**的嵌套 BO（Lombok 照样生成 public getter，
// 所以 Jackson 会输出它们）：真实 track_josn 里从没有过这些键（实测 64 行全为 0 命中），
// 但 Jackson 的 inclusion 是 ALWAYS ⇒ 必须输出成 null，不能整个键少掉。
static const std::vector<std::pair<const char*, Tk>> TRAIL_BO = {
    {"pointUuid", Tk::Str},   {"stateType", Tk::Str},   {"pointFlag", Tk::Str},
    {"pointJosn", Tk::Str},   {"borderWeighingCaptureBO", Tk::Obj}, {"gantryCaptureBO", Tk::Obj},
    {"provCaptureBO", Tk::Obj}, {"stationCapture", Tk::Obj}, {"feeRecord", Tk::Obj},
    {"feeStationEnter", Tk::Obj}, {"feeStationExit", Tk::Obj},
    {"captureTime", Tk::Str}, {"directionIn", Tk::Bool}, {"locationCode", Tk::Str},
    {"locationFlag", Tk::Str}, {"ipType", Tk::Str},     {"locationJosn", Tk::Str},
    {"gantryIpBO", Tk::Obj},  {"stationIpBO", Tk::Obj}, {"devCode", Tk::Str},
    {"devName", Tk::Str},     {"imagesArry", Tk::Str},  {"lon", Tk::Num},
    {"lat", Tk::Num},         {"roadCode", Tk::Str},    {"sectionCode", Tk::Str},
    {"direction", Tk::Str},   {"pileno", Tk::Str},      {"preCaptureTime", Tk::Str},
    {"countNum", Tk::Num},    {"pilenoDec", Tk::Num},   {"isQuery", Tk::Str},
};

/** 对应 JSON.parseArray(trackJosn, TrailBo.class) 的类型转换再序列化 */
Json projectTrailBo(const Json& src) {
    Json out = Json::object();
    for (const auto& [name, kind] : TRAIL_BO) {
        if (!src.contains(name) || src[name].is_null()) {
            out[name] = Json(nullptr);
            continue;
        }
        const Json& v = src[name];
        if (kind == Tk::Num) {
            if (v.is_number()) {
                out[name] = v;  // 已经是数字：保持原字面量的最短表示，与 BigDecimal 一致
            } else if (v.is_boolean()) {
                out[name] = Json(v.get<bool>() ? 1 : 0);
            } else {
                try {
                    out[name] = Json(std::stod(v.is_string() ? v.get<std::string>() : v.dump()));
                } catch (...) {
                    out[name] = Json(nullptr);
                }
            }
        } else if (kind == Tk::Bool) {
            if (v.is_boolean()) out[name] = v;
            else if (v.is_string()) out[name] = Json(v.get<std::string>() == "true");
            else if (v.is_number()) out[name] = Json(v.get<double>() != 0.0);
            else out[name] = Json(nullptr);
        } else if (kind == Tk::Obj) {
            // 嵌套的 Ods* BO。⚠️ Java 会先反序列化成那个类型再序列化 ⇒ 未声明的键会被丢掉、
            // 缺的键补 null。这里原样透传：实测 64 行 track_josn 里这 9 个键一次都没出现过，
            // 只有客户端自己 POST 时才可能有值，为了"少一个键"去复刻 7 个 Ods 类（2000+ 行）
            // 不值当，差异记在 FINAL_DIFFERENCES §3。
            out[name] = v.is_object() ? v : Json(nullptr);
        } else {
            // 目标类型是 String：数字/布尔取它的 JSON 文本（fastjson 保留原始字面量）
            out[name] = v.is_string() ? v : Json(v.dump());
        }
    }
    return out;
}

/** 把统计别名接进 spec：那些属性在实体上不是表列，只有这类 group by 查询才给值 */
Spec aliasSpec(const Spec& base, std::vector<std::pair<const char*, const char*>> aliases) {
    Spec s = base;
    for (const auto& [json, col] : aliases) {
        for (auto& f : s.fields) {
            if (std::string(f.json) == json) f.column = col;
        }
    }
    return s;
}

cm::db::Result select(const std::string& sql) {
    cm::db::Result res;
    Db::instance().query(sql, res);
    return res;
}

/** 与 select() 的区别：查询失败直接抛（Java 侧 MyBatis 抛 BadSqlGrammarException → 500，
 *  而不是"空列表"）。新写的端点一律用这个，见 COMPATIBILITY.md §2.12。 */
cm::db::Result mustRun(const std::string& sql) {
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) {
        throw cm::exception::ServiceException("数据访问异常，SQL 执行失败: " + sql.substr(0, 200));
    }
    return res;
}

} // namespace

Json projectTrailBoJson(const Json& src) { return projectTrailBo(src); }

// ---------------------------------------------------------------- 轨迹本地查询
// listByCarByTime 与 listByCarId 共用；对应 ZdataTrailTracksServiceImpl.carTrackQuery
// 加上控制器里那段 track_josn → List<TrailBo> 的展开。
CarTrackLocal carTrackQueryLocal(RequestContext& ctx, const Json& q) {
    const auto& sp = specZdataTrailTracks();
    auto p = [&](const char* k) { return cm::jstr(q, k); };
    const std::string carNo = p("carNo");
    const std::string plateKey = p("plateKey");
    const std::string apply1 = p("applyTime1");
    const std::string apply2 = p("applyTime2");
    const std::string entoll = p("entollstationid");

    // getCyly 与 getHistoryTrail 共享的那三段条件
    auto baseWhere = [&]() {
        std::string w = " WHERE 1=1";
        if (!StringUtils::isBlank(carNo)) w += " and t.plate_key = " + Db::lit(carNo);
        if (!StringUtils::isBlank(apply1))
            w += " and t.enter_time >= STR_TO_DATE(" + Db::lit(apply1) + ",'%Y-%m-%d')";
        if (!StringUtils::isBlank(apply2))
            w += " and t.enter_time < date_add(STR_TO_DATE(" + Db::lit(apply2)
                 + ",'%Y-%m-%d'), interval 1 day)";
        return w;
    };

    std::vector<std::string> uuidList;
    std::map<std::string, long long> passCount;
    if (p("isCylx") == "1") {
        const std::string cy =
            "SELECT uuid, passCount FROM (SELECT t.uuid, gc.passCount, ROW_NUMBER() OVER ("
            "PARTITION BY t.plate_key, t.entollstationid, t.extollstationid "
            "ORDER BY t.enter_time DESC) as rn FROM zdata_trail_tracks t INNER JOIN ("
            "SELECT plate_key, entollstationid, extollstationid, COUNT(*) as passCount "
            "FROM zdata_trail_tracks t" + baseWhere() +
            " GROUP BY plate_key, entollstationid, extollstationid ORDER BY passCount DESC LIMIT 3) gc"
            " ON t.plate_key = gc.plate_key AND t.entollstationid = gc.entollstationid"
            " AND t.extollstationid = gc.extollstationid) a WHERE rn = 1 order by passCount desc";
        // startPage() 拦到的是**第一条**查询，也就是 getCyly；后面的 getHistoryTrail 不分页
        const auto page0 = ctx.pageRequest();
        cm::db::Result cyres;
        if (page0.enabled) {
            cyres = cm::db::queryPage("select count(1) from (" + cy + ") cm_tmp", cy, page0).rows;
        } else {
            cyres = mustRun(cy);
        }
        for (const auto& row : cyres.rows) {
            const std::string u = row.str("uuid");
            if (u.empty()) continue;
            uuidList.push_back(u);
            // Collectors.toMap：同一个 uuid 出现两次会抛 IllegalStateException -> 500
            if (passCount.count(u)) throw cm::exception::ServiceException("Duplicate key " + u);
            passCount[u] = row.i64("passCount");
        }
    }

    std::string where = baseWhere();
    if (!StringUtils::isBlank(plateKey))
        where += " and t.plate_key like concat('%', " + Db::lit(plateKey) + ", '%')";
    if (!StringUtils::isBlank(entoll))
        where += " and t.entollstationid = " + Db::lit(entoll);
    if (!uuidList.empty()) {
        where += " and uuid in (";
        for (size_t i = 0; i < uuidList.size(); ++i) {
            if (i) where += ",";
            where += Db::lit(uuidList[i]);
        }
        where += ")";
    }
    // 列清单照抄 getHistoryTrail 的 select：不是实体的全部列，
    // 没选到的属性 MyBatis 不填，Java 响应里就是 null
    static const std::string COLS =
        "t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, t.exit_time, t.create_time,"
        " t.enter_locationcode, t.exit_locationcode, t.track_josn, t.enaxlecount,"
        " t.entolllaneid, t.entollstationid, t.entollstationname, t.envehicleclass,"
        " t.envehicleid, t.envehicletype, t.enweight, t.extolllaneid, t.extollstationid,"
        " t.extollstationname, t.exvehicleclass, t.exvehicleid, t.exvehicletype, t.exweight,"
        " t.start_lon, t.strat_lat, t.end_lon, t.end_lat";
    const auto page = ctx.pageRequest();
    const std::string order = !page.orderBy.empty() ? " ORDER BY " + page.orderBy
                                                     : " ORDER BY t.enter_time desc";
    const std::string sql = "SELECT " + COLS + " FROM zdata_trail_tracks t" + where + order;

    std::vector<cm::db::Row> carlist;
    long long total = 0;
    if (p("isCylx") == "1") {
        // 这条不分页，PageInfo(list) 拿不到 Page => total 退化成 list.size()
        carlist = mustRun(sql).rows;
        total = static_cast<long long>(carlist.size());
    } else if (page.enabled) {
        auto pr = cm::db::queryPage("SELECT COUNT(1) FROM zdata_trail_tracks t" + where, sql, page);
        carlist = pr.rows.rows;
        total = pr.total;
    } else {
        carlist = mustRun(sql).rows;
        total = static_cast<long long>(carlist.size());
    }

    Json rtnList = Json::array();
    for (const auto& row : carlist) {
        Json tracks = rowToJson(sp, row);
        const std::string keyValue = cm::jstr(tracks, "trackJosn");
        // Java: 只有 track_josn 非空的行才进 rtnList（total 里却仍然算它们）
        if (StringUtils::isBlank(keyValue)) continue;

        // isCylx=1 时 plateKey 会被追加"(通行N次)"，且发生在序列化之前
        std::string plate = cm::jstr(tracks, "plateKey");
        auto it = passCount.find(cm::jstr(tracks, "uuid"));
        if (it != passCount.end()) plate += "(通行" + std::to_string(it->second) + "次)";
        tracks["plateKey"] = Json(plate);

        tracks["trailPoints"] = Json("");
        tracks["trackJosn"] = Json("");
        // service 里的四个 new BigDecimal(...)：空值跳过，非法数字照样抛出去（Java 也是 500）
        for (auto& kv : std::vector<std::pair<const char*, const char*>>{
                 {"startLon", "startLonDec"}, {"stratLat", "stratLatDec"},
                 {"endLon", "endLonDec"}, {"endLat", "endLatDec"}}) {
            const std::string v = cm::jstr(tracks, kv.first);
            if (!StringUtils::isBlank(v)) tracks[kv.second] = Json(std::stod(v));
        }

        Json trailList = Json::array();
        for (const auto& e : Json::parse(keyValue)) trailList.push_back(projectTrailBo(e));

        Json devCount = Json::object();
        devCount["exceptNum"] = Json(0);
        devCount["trailDevList"] = Json::array();  // 字段名是 TrailDevList，Jackson 首字母小写
        devCount["trailList"] = Json(nullptr);
        devCount["exceptMsg"] = Json(nullptr);

        Json info = Json::object();
        info["trailUuid"] = Json(CommonUtil::isNull(plate));
        info["enterTime"] = Json(nullptr);
        info["tracks"] = std::move(tracks);
        info["trailList"] = std::move(trailList);
        info["raodTrailList"] = Json::array();  // getCarGeometry 那段没被调用，恒为空数组
        info["trailDevCountBO"] = std::move(devCount);
        rtnList.push_back(std::move(info));
    }
    return CarTrackLocal{std::move(rtnList), total, !carlist.empty()};
}

// ---------------------------------------------------------------- TrailBo 的查询参数
// Spring 把 query 绑到 TrailBo 的属性上，Forest 再把这个对象拍平回 query string。
// 两步都得按声明序，所以共用 TRAIL_BO 那张表。
// 绑出来的值一律存**文本**（数字属性保留调用方给的标度，BigDecimal.toString() 就是那个样子），
// 因为这份对象只用于 isNoneBlank 判断和出站拍平，响应里那份 TrailBo 是上游返的。
Json bindTrailBoQuery(RequestContext& ctx) {
    Json out = Json::object();
    for (const auto& [name, kind] : TRAIL_BO) {
        if (kind == Tk::Obj) continue;   // gantryIpBO.a=x 这种嵌套写法不支持（见 FINAL_DIFFERENCES）
        auto raw = ctx.optParam(name);
        if (!raw) continue;              // 没传 ⇒ 属性保持 null，键根本不出现
        if (kind == Tk::Str) {
            out[name] = Json(*raw);      // String 属性的 "" 是值，不是 null
            continue;
        }
        const std::string v = CommonUtil::isNull(*raw);
        if (v.empty()) continue;         // 数字/布尔转换器：空串 ⇒ null
        if (kind == Tk::Bool) {
            // Spring 的 StringToBooleanConverter 认这八个字面量（大小写不敏感），其余抛异常
            static const std::vector<std::pair<const char*, bool>> kBool = {
                {"true", true}, {"on", true}, {"yes", true}, {"1", true},
                {"false", false}, {"off", false}, {"no", false}, {"0", false}};
            bool hit = false;
            for (const auto& [text, val] : kBool) {
                if (StringUtils::equalsIgnoreCase(v, text)) {
                    out[name] = Json(val ? "true" : "false");
                    hit = true;
                    break;
                }
            }
            if (!hit) throw cm::exception::ServiceException(
                        "Failed to convert property value of type 'java.lang.String' to required "
                        "type 'java.lang.Boolean' for property '" + std::string(name) + "'");
            continue;
        }
        try {
            size_t pos = 0;
            std::stod(v, &pos);
            if (pos != v.size()) throw std::invalid_argument(v);
        } catch (...) {
            throw cm::exception::ServiceException(
                "Failed to convert property value of type 'java.lang.String' to required type "
                "'java.math.BigDecimal' for property '" + std::string(name) + "'");
        }
        out[name] = Json(v);   // 原样文本，保住标度（116.500 不能变成 116.5）
    }
    return out;
}

std::vector<std::pair<std::string, std::string>> flattenTrailBoQuery(const Json& bo) {
    // 实机抓包（Forest 1.5.x）：null 省略、BigDecimal 原样带标度、布尔小写、
    // 嵌套对象转 JSON 文本、空串渲染成**没有等号**的裸键名。
    std::vector<std::pair<std::string, std::string>> out;
    for (const auto& [name, kind] : TRAIL_BO) {
        if (!bo.contains(name) || bo[name].is_null()) continue;
        const Json& v = bo[name];
        std::string text = v.is_string() ? v.get<std::string>()
                                         : (v.is_boolean() ? std::string(v.get<bool>() ? "true"
                                                                                        : "false")
                                                           : cm::aspect::fastJsonCompact(v, {}, true));
        out.emplace_back(std::string(name), std::move(text));
    }
    return out;
}


const Spec& suspiciousHistorySpec() {
    static const Spec s = [] {
        Spec s = specCarSuspicious();
        s.table = "car_suspicious_back";
        s.orderBy = "t.id";
        s.hooks.beforeQuery = [](RequestContext&, Json& q) {
            // Java: deleteEnd() 去掉一个结尾逗号后只用于判断，原值照样参与查询
            const std::string probe = CommonUtil::deleteEnd(cm::jstr(q, "sectionCode"));
            if (!StringUtils::isBlank(probe) &&
                probe.find(cm::constant::Constants::section_all) != std::string::npos)
                q["sectionCode"] = "";
            // Java: “选择对象”传的是 code，落到 trackNames 这个 LIKE 条件上
            const std::string code = cm::jstr(q, "code");
            if (!StringUtils::isBlank(code)) q["trackNames"] = Json(code);
        };
        return s;
    }();
    return s;
}

void registerManagerExtraControllers(Router& r) {
    // ---- 车牌维度：Java 一律先把 carNo 兜成 "-1"，避免全表扫 ----

    // GET /manager/suspicious/listHistory —— 备份表的历史可疑车辆
    registerListVariant(r, "/manager/suspicious/listHistory", suspiciousHistorySpec(),
                        ListKind::Paged, "manager:suspicious:list");

    // GET /manager/suspicious/listCarNo
    {
        Spec s = specCarSuspicious();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/suspicious/listCarNo", s, ListKind::Paged);
    }
    // GET /manager/exceptrecord/listCarNo
    {
        Spec s = specCarExceptRecord();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/exceptrecord/listCarNo", s, ListKind::Paged);
    }
    // GET /manager/exceptrecord/listExceptId —— 同样兜底，条件是 find_in_set(t.id, #{exceptIds})
    {
        Spec s = specCarExceptRecord();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "exceptIds"); };
        registerListVariant(r, "/manager/exceptrecord/listExceptId", s, ListKind::Paged);
    }
    // GET /manager/confimfree/listCarNo
    {
        Spec s = specCarConfimFree();
        s.hooks.beforeQuery = [](RequestContext&, Json& q) { presetBlank(q, "carNo"); };
        registerListVariant(r, "/manager/confimfree/listCarNo", s, ListKind::Paged);
    }

    // GET /manager/cartrackinfo/listByCarByTime —— 车辆历史记录
    // 对应 ZdataTrailTracksServiceImpl.carTrackQuery + 控制器里的 track_josn 展开。
    // Java 里"查远程接口"那一大段（httpSysUtilApiService.carTrackQueryByTime）整块被注释掉了，
    // 只剩本地 SQL，所以这条不需要外部依赖就能 1:1 复刻。
    r.get("/manager/cartrackinfo/listByCarByTime", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto local = carTrackQueryLocal(ctx, bindQuery(specZdataTrailTracks(), ctx));
        return BaseController::ok(BaseController::dataTable(local.rtnList, local.total));
    });

    // GET /manager/exceptrecord/exceptRecordCount
    // 对应 CarExceptRecordMapper.exceptRecordCount：按车牌聚合，返回单个实体（查不到为 null）
    r.get("/manager/exceptrecord/exceptRecordCount", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string carNo = ctx.optParam("carNo").value_or("");
        if (StringUtils::isBlank(carNo)) carNo = "-1";
        std::string sql =
            "select t.car_no,count(1) exceptNum,round(sum(t.dif_amount),2) exceptAmount,"
            "round(sum(t.total_amount),2) total_amount,round(sum(t.charge_amount),2) charge_amount "
            "from car_except_record t where t.del_flag = '0' and t.car_no = " +
            Db::lit(carNo);
        if (auto v = ctx.optParam("status"); v && !StringUtils::isBlank(*v))
            sql += " and t.status = " + Db::lit(*v);
        sql += " group by t.car_no";

        static const Spec cs = aliasSpec(specCarExceptRecord(),
                                         {{"exceptNum", "exceptNum"},
                                          {"exceptAmount", "exceptAmount"},
                                          {"totalAmount", "total_amount"},
                                          {"chargeAmount", "charge_amount"},
                                          {"carNo", "car_no"}});
        auto res = select(sql);
        // Java 的 resultMap 只认列名，未投影的属性保持 null
        Json data = res.rows.empty() ? Json(nullptr) : rowToJson(cs, res.rows[0]);
        return BaseController::ok(AjaxResult::success(data));
    });

    // GET /manager/confimfree/listCount —— 同上，free 记录的聚合
    r.get("/manager/confimfree/listCount", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string carNo = ctx.optParam("carNo").value_or("");
        if (StringUtils::isBlank(carNo)) carNo = "-1";
        std::string sql =
            "select t.car_no,count(1) confimFreeNum,"
            "round(ifnull(sum(t.aduit_amount),0) + ifnull(sum(t.amount),0),2) confimFreeAmount "
            "from car_confim_free t where t.del_flag = '0' and t.car_no = " +
            Db::lit(carNo);
        if (auto v = ctx.optParam("status"); v && !StringUtils::isBlank(*v))
            sql += " and t.status = " + Db::lit(*v);
        sql += " group by t.car_no";

        static const Spec cs = aliasSpec(specCarConfimFree(),
                                         {{"confimFreeNum", "confimFreeNum"},
                                          {"confimFreeAmount", "confimFreeAmount"},
                                          {"carNo", "car_no"}});
        auto res = select(sql);
        Json data = res.rows.empty() ? Json(nullptr) : rowToJson(cs, res.rows[0]);
        return BaseController::ok(AjaxResult::success(data));
    });

    // GET /manager/exceptrecord/getConfirmId/{id}
    // Java: selectCarConfimFreeByExceptIds([id]) 取第一条的 id，没有则 "-1"
    r.get("/manager/exceptrecord/getConfirmId/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string id = ctx.pathVar("id");
        const std::string sql =
            "SELECT t.ID FROM car_confim_free t WHERE t.del_flag = '0' and (find_in_set(" +
            Db::lit(id) + ", t.except_ids) > 0)";
        auto res = select(sql);
        const std::string confirmId = res.rows.empty() ? std::string("-1") : res.rows[0].str("ID");
        AjaxResult success = AjaxResult::success();
        success.put("data", confirmId);
        return BaseController::ok(success);
    });

    // GET /manager/confimfree/except/{exceptIds} —— 按异常流水 id 串组装"确认补缴"表单
    // 对应 CarConfimFreeServiceImpl.selectCarConfimFreeByExceptIds(String)
    r.get("/manager/confimfree/except/{exceptIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string exceptIds = cm::utils::CommonUtil::deleteEnd(ctx.pathVar("exceptIds"));
        if (StringUtils::isBlank(exceptIds))
            return BaseController::ok(AjaxResult::error("请选择车辆异常流水！"));

        const auto& rs = specCarExceptRecord();
        Json q = Json::object();
        q["exceptIds"] = exceptIds;
        // selectSqlOf 而不是自己拼 FROM：specCarExceptRecord 现在带 join 与派生列 createInfo
        auto res = select(cm::web::crud::selectSqlOf(rs, cm::web::crud::buildWhere(rs, q),
                                                     " ORDER BY " + rs.orderBy)).rows;
        if (res.empty()) return BaseController::ok(AjaxResult::error("异常车辆流水不存在！"));

        std::vector<std::string> carNos, epsIds;
        for (const auto& row : res) {
            const std::string carNo = row.str("car_no");
            if (std::find(carNos.begin(), carNos.end(), carNo) == carNos.end()) carNos.push_back(carNo);
            const std::string eps = row.get("eps_id") ? row.str("eps_id") : std::string("<null>");
            if (std::find(epsIds.begin(), epsIds.end(), eps) == epsIds.end()) epsIds.push_back(eps);
        }
        if (carNos.size() > 1) return BaseController::ok(AjaxResult::error("请勿选择多辆车！"));
        if (epsIds.size() > 1)
            return BaseController::ok(AjaxResult::error("选择的异常流水存在多个录入单位，请确认！"));

        // Java 在这些分支上都会早退，只有"已追缴"检查还要再查一次 confim_free
        std::string in;
        size_t pos = 0;
        while (true) {
            size_t comma = exceptIds.find(',', pos);
            std::string item = exceptIds.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
            if (!in.empty()) in += " OR ";
            in += "find_in_set(" + Db::lit(StringUtils::trim(item)) + ", t.except_ids) > 0";
            if (comma == std::string::npos) break;
            pos = comma + 1;
        }
        const auto& cs = specCarConfimFree();
        if (!select(std::string("SELECT t.ID FROM ") + cs.table + " t WHERE t.del_flag = '0' and (" + in + ")")
                        .rows.empty())
            return BaseController::ok(AjaxResult::error("车辆补缴单已追缴，请勿重复补缴！"));

        const auto& first = res.front();
        Json vo = cm::web::crud::rowToJson(cs, cm::db::Row{});  // 骨架：全部键在、值 null
        vo["carId"] = first.get("car_id") ? Json(first.str("car_id")) : Json(nullptr);
        vo["carNo"] = first.get("car_no") ? Json(first.str("car_no")) : Json(nullptr);
        vo["carType"] = first.get("car_type") ? Json(first.str("car_type")) : Json(nullptr);
        vo["carVehicle"] = first.get("car_vehicle") ? Json(first.str("car_vehicle")) : Json(nullptr);
        vo["exceptIds"] = exceptIds;
        if (!epsIds.empty() && epsIds.front() != "<null>") vo["orgId"] = epsIds.front();
        // Java: epsList 里有 null 时 setOrgId(null+"") —— 得到字符串 "null"
        if (!epsIds.empty() && epsIds.front() == "<null>") vo["orgId"] = "null";

        double dif = 0.0;
        for (const auto& row : res)
            if (row.get("dif_amount")) dif += row.dbl("dif_amount");
        if (dif != 0.0) dif = std::round(dif * 100.0) / 100.0;  // setScale(2, HALF_UP)
        vo["difAmount"] = Json(dif);
        vo["backCol1"] = "0.3";  // Java: new BigDecimal("0.3") + ""
        vo["amount"] = Json(std::round(dif * 0.3 * 100.0) / 100.0);
        return BaseController::ok(AjaxResult::success(vo));
    });

    // GET /manager/aduitfree/incomeDetailList
    // 对应 CarAduitFreeMapper.incomeDetailList：两张表的 union all，再按创建时间倒序分页
    r.get("/manager/aduitfree/incomeDetailList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string orgId = ctx.optParam("orgId").value_or("");
        if (StringUtils::isBlank(orgId)) orgId = "-1";  // Java: getOrgId() 为空时兜成 "-1"
        const std::string applyTime1 = ctx.optParam("applyTime1").value_or("");
        const std::string applyTime2 = ctx.optParam("applyTime2").value_or("");
        const std::string carNo = ctx.optParam("carNo").value_or("");

        auto half = [&](const char* table, bool aduit) {
            std::string s = std::string("select ifnull(a.amount, 0) amount, a.car_no, a.org_id, ") +
                            "d.dept_name orgName,a.create_time from " + table +
                            " a left join sys_dept d on d.dept_id = a.org_id where a.del_flag = '0'";
            if (aduit) s += " and a.status = '0'";
            s += " and a.org_id = " + Db::lit(orgId);
            if (!StringUtils::isBlank(applyTime1))
                s += " and a.create_time >= STR_TO_DATE(" + Db::lit(applyTime1) + ",'%Y-%m-%d')";
            if (!StringUtils::isBlank(applyTime2))
                s += " and a.create_time < date_add(STR_TO_DATE(" + Db::lit(applyTime2) +
                     ", '%Y-%m-%d'), interval 1 day)";
            if (!StringUtils::isBlank(carNo))
                s += " and a.car_no like concat('%', " + Db::lit(carNo) + ", '%')";
            return s;
        };
        const std::string inner = half("car_aduit_free", true) + " UNION all " + half("car_confim_free", false);
        const std::string data = "select t.* from (" + inner + ") t order by t.create_time desc";
        const auto page = ctx.pageRequest();
        auto pr = cm::db::queryPage("select count(1) from (" + inner + ") page_count", data, page);

        // resultType=CarConfimFree：按列名自动映射，只有这 5 个属性会有值
        static const Spec cs = aliasSpec(specCarConfimFree(), {{"orgName", "orgName"}});
        Json rows = Json::array();
        for (const auto& row : pr.rows.rows) rows.push_back(rowToJson(cs, row));
        return BaseController::ok(BaseController::dataTable(rows, pr.total));
    });
}

} // namespace cm::web
