// 两个 Excel 导入端点。对应 Java:
//   CarInfoController#doImport（178-315 行）
//     + CarInfoServiceImpl.{doImport,saveCarInfo,updateRedisCarList}
//   CarExceptRecordController#doImport（341-626 行）
//     + CarExceptRecordServiceImpl.{saveCarExceptRecord,saveCarExcept}
//   com.ruoyi.web.util.{ImportSysUtil,ImportUtil}（表头/数据/规则三段在 ImportExcel.hpp）
//
// 逐条照抄的"看着像 bug"的行为 —— 改掉任何一条都算接口不一致：
//   * 表头逐格 String.equals 严格比较。carinfo 比第 1 行；exceptrecord 比第 2 行 **或** 第 3 行，
//     而且两次比的是同一份 colsName —— Java 里 gzListThree 调的也是 initListTwo()，
//     那个看起来专为第 3 行写的 initListThree() 全程没被调用。
//   * errorList 跨行共享 ⇒ 第一行出错之后每一行都进不了 importList，但循环照跑（只在 >100 时
//     break），所以最多 101 条错误，且 importList 里只有第一个错误之前的行。
//   * rowNo = index + 2（getErrorBO 内部 +1、调用点又 +1）。exceptrecord 的数据从 Excel 第 4 行
//     开始，报出来的 rowNo 仍从 2 开始 ⇒ 与真实行号差 2。
//   * errorList 非空 ⇒ 一行都不写库，返回 {"msg":"error","code":500,"data":[…]}，HTTP 200。
//   * 字典 label→value 走 Collectors.toMap：重复 label 抛 IllegalStateException ⇒ 整个请求 500。
//   * saveCarInfo / saveCarExceptRecord 的返回值在导入循环里被丢弃 ⇒
//     "车牌号存在重复，请确定！"、"录入区间时间重复！"永远不会出现在响应里，
//     但那两个分支"少写一行、少刷一次缓存"的副作用要留着。
//   * 导入响应里的 data 是**服务层加工后**的同一批对象（id/delFlag/createBy/… 都被 setter 改过），
//     所以必须原地改 importList，不能拷一份出来改。
#include "cm/web/controller/manager/ManagerImportControllers.hpp"

#include <algorithm>
#include <map>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/Xlsx.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/system/mapper/SysDictDataMapper.hpp"
#include "cm/web/BaseController.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"
#include "cm/web/util/ImportExcel.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::CommonUtil;
using cm::utils::DateUtils;
using cm::utils::StringUtils;
using cm::web::crud::Field;
using cm::web::crud::Fmt;
using cm::web::crud::Spec;
using cm::web::importx::ImportEntity;
using cm::web::importx::ImportErrorEntity;

// ------------------------------------------------------------------ 实体值
//
// Java 侧是 fastjson2 把 Map<String,String> 转成实体：String 属性永远拿到原文（空串就是空串，
// 不是 null）；数值/日期属性由文本转换，空文本 -> null。
// Val 用四态复刻，并把 BigDecimal 的**原文**留着：new BigDecimal("1.50") 序列化出来是 1.50，
// 过一遍 double 就成 1.5，字节级对不上。日期同理 —— 规则 8 保证文本已经是
// "yyyy-MM-dd HH:mm:ss"，比较和输出都用原文，不必绕 epoch（顺带避开本机时区的坑）。
struct Val {
    enum T { NONE, STR, NUM, DEC, DATE } t{NONE};
    std::string s;

    bool isNull() const { return t == NONE; }
    bool numeric() const { return t == NUM || t == DEC; }
    /** CommonUtil.isNull(getter()) */
    std::string plain() const { return t == NONE ? std::string() : s; }
};

Val strVal(std::string s) { Val v; v.t = Val::STR; v.s = std::move(s); return v; }
Val numVal(std::string s) { Val v; v.t = Val::NUM; v.s = std::move(s); return v; }
Val dateVal(std::string s) { Val v; v.t = Val::DATE; v.s = std::move(s); return v; }

struct Ent {
    std::map<std::string, Val> f;

    Val& operator[](const std::string& k) { return f[k]; }
    const Val* find(const std::string& k) const {
        auto it = f.find(k);
        return it == f.end() ? nullptr : &it->second;
    }
    bool present(const std::string& k) const { return find(k) != nullptr; }
    std::string plain(const std::string& k) const {
        const Val* v = find(k);
        return v ? v->plain() : std::string();
    }
    bool blank(const std::string& k) const { return !StringUtils::isNotBlank(plain(k)); }
};

const Field* specField(const Spec& spec, const std::string& json) {
    for (const auto& f : spec.fields) {
        if (json == f.json) return &f;
    }
    return nullptr;
}

/** fastjson2 的 String -> 声明类型 */
void bindText(const Spec& spec, Ent& e, const std::string& json, const std::string& raw) {
    const Field* f = specField(spec, json);
    if (f == nullptr) return;
    switch (f->fmt) {
        case Fmt::Int:
        case Fmt::Long:
            if (raw.empty()) return;                 // 不赋值 ⇒ Java 里保持 null
            try { e[json] = numVal(std::to_string(std::stoll(raw))); }
            catch (...) { e[json] = numVal(raw); }
            return;
        case Fmt::Double:
            if (raw.empty()) return;
            e[json] = Val();
            e[json].t = Val::DEC;                    // BigDecimal：原文即标度
            e[json].s = raw;
            return;
        case Fmt::DateYmd:
        case Fmt::DateYmdHms:
        case Fmt::DateIso:
        case Fmt::DateTimeIso:
            if (raw.empty()) return;
            e[json] = dateVal(raw);
            return;
        default:
            e[json] = strVal(raw);
            return;
    }
}

std::string sqlLit(const Val& v) {
    if (v.isNull()) return "NULL";
    return v.numeric() ? v.s : Db::lit(v.s);
}

/** Jackson 对实体的输出：字段声明序（spec 就是按这个顺序生成的）。
 *  没被 setter 碰过的属性回到 Java 声明处的初值，没有初值才是 null。 */
Json entityJson(const Spec& spec, const Ent& e) {
    Json out = Json::object();
    for (const auto& f : spec.fields) {
        const std::string key(f.json);
        const Val* v = e.find(key);
        if (v == nullptr) {
            out[key] = f.dflt ? Json::parse(f.dflt) : Json(nullptr);
            continue;
        }
        if (v->isNull()) { out[key] = Json(nullptr); continue; }
        const bool numericSlot = f.fmt == Fmt::Int || f.fmt == Fmt::Long || f.fmt == Fmt::Double;
        if (numericSlot && v->numeric()) {
            out[key] = Json::parse(v->s);            // parse 而不是 double：保住 1.50 的写法
            continue;
        }
        out[key] = Json(v->s);
    }
    return out;
}

Json entityArrayJson(const Spec& spec, const std::vector<Ent>& list) {
    Json arr = Json::array();
    for (const auto& e : list) arr.push_back(entityJson(spec, e));
    return arr;
}

// ------------------------------------------------------------------ 通用件

cm::db::Result mustRun(const std::string& sql) {
    cm::db::Result res;
    if (!Db::instance().query(sql, res)) {
        throw cm::exception::ServiceException("数据访问异常，SQL 执行失败: " + sql.substr(0, 200));
    }
    return res;
}

long long mustCount(const std::string& sql) {
    cm::db::Result res = mustRun(sql);
    if (res.rows.empty() || res.rows[0].columns().empty()) return 0;
    const std::string v = res.rows[0].str(res.rows[0].columns()[0]);
    try { return v.empty() ? 0 : std::stoll(v); } catch (...) { return 0; }
}

/** ISysDictDataServiceImpl.selectDictDataLaleMap。
 *  ⚠️ Collectors.toMap 遇到重复 label 抛 IllegalStateException("Duplicate key …") ⇒ 500；
 *     悄悄让后者覆盖前者就会留下"C++ 能用、Java 500"的不一致。 */
std::map<std::string, std::string> dictLabelMap(const std::string& dictType) {
    cm::domain::SysDictData q;
    q.dictType = dictType;
    std::map<std::string, std::string> out;
    for (const auto& d : cm::system::mapper::SysDictDataMapper::selectDictDataList(q)) {
        const std::string label = d.dictLabel ? *d.dictLabel : std::string();
        const std::string value = d.dictValue ? *d.dictValue : std::string();
        auto it = out.find(label);
        if (it != out.end()) {
            throw cm::exception::ServiceException("Duplicate key " + label +
                                                  " (attempted merging values " + it->second +
                                                  " and " + value + ")");
        }
        out.emplace(label, value);
    }
    return out;
}

std::vector<std::string> colNamesOf(const std::vector<ImportEntity>& bo) {
    std::vector<std::string> names;
    for (const auto& e : bo) names.push_back(e.colName);
    return names;
}

/** Spring 的 @RequestParam("file") MultipartFile：缺这段抛
 *  MissingServletRequestPartException("Required part 'file' is not present.")
 *  ⇒ GlobalExceptionHandler 兜住 ⇒ HTTP 200 + code:500。 */
const cm::http::MultipartPart& filePart(RequestContext& ctx) {
    for (const auto& p : ctx.req.parts) {
        if (p.name == "file") return p;
    }
    throw cm::exception::ServiceException("Required part 'file' is not present.");
}

/** new XSSFWorkbook(stream) 读不动就抛 ⇒ 这里也必须 500，不能退化成"空表"。
 *  dateWithTime 对应两套取格函数：carinfo 走 getCellFormatValue07（日期是 yyyy/MM/dd），
 *  exceptrecord 走 getCellFormatValue08（yyyy-MM-dd HH:mm:ss）—— 同一份文件两边读出来的
 *  文本是不一样的。 */
cm::utils::Xlsx loadSheet(const std::string& bytes, bool dateWithTime) {
    cm::utils::Xlsx x;
    std::string err;
    if (!cm::utils::Xlsx::load(bytes, dateWithTime, x, &err)) {
        throw cm::exception::ServiceException("Your input stream is not a valid OOXML package: " +
                                              err);
    }
    return x;
}

cm::http::ApiResponse errorResponse(const std::vector<ImportErrorEntity>& errors) {
    Json arr = Json::array();
    for (const auto& e : errors) arr.push_back(e.toJson());
    return BaseController::ok(AjaxResult::error("error", arr));
}

std::string replaceAll(std::string s, const std::string& from, const std::string& to) {
    if (from.empty()) return s;
    size_t pos = 0;
    while ((pos = s.find(from, pos)) != std::string::npos) {
        s.replace(pos, from.size(), to);
        pos += to.size();
    }
    return s;
}

// ------------------------------------------------------------------ 落库
//
// MyBatis-Plus 的 insert/updateById 用 NOT_NULL 策略：属性为 null 就整列不出现在 SQL 里。
// 下面两张列表只列导入链路真的会赋值的属性。
struct Col {
    const char* json;
    const char* column;
};
const Col CAR_INFO_COLS[] = {
    {"id", "id"}, {"carNo", "car_no"}, {"carType", "car_type"}, {"carVehicle", "car_vehicle"},
    {"carNum", "car_num"}, {"escapedType", "escaped_type"}, {"escapedAmount", "escaped_amount"},
    {"remark", "remark"}, {"plateColor", "plate_color"}, {"delFlag", "del_flag"},
    {"createBy", "create_by"}, {"createTime", "create_time"}, {"updateBy", "update_by"},
    {"updateTime", "update_time"}, {"epsId", "eps_id"}, {"tenantId", "tenant_id"},
    {"status", "status"},
};
const Col EXCEPT_COLS[] = {
    {"id", "id"}, {"carId", "car_id"}, {"carNo", "car_no"}, {"carType", "car_type"},
    {"carVehicle", "car_vehicle"}, {"carNum", "car_num"}, {"passType", "pass_type"},
    {"inStationId", "in_station_id"}, {"inStation", "in_station"}, {"inTime", "in_time"},
    {"outStationId", "out_station_id"}, {"outStation", "out_station"}, {"outTime", "out_time"},
    {"totalAmount", "total_amount"}, {"chargeAmount", "charge_amount"},
    {"difAmount", "dif_amount"}, {"escapedType", "escaped_type"}, {"remark", "remark"},
    {"backCol1", "back_col1"}, {"status", "status"}, {"delFlag", "del_flag"},
    {"createBy", "create_by"}, {"createTime", "create_time"}, {"updateBy", "update_by"},
    {"updateTime", "update_time"}, {"epsId", "eps_id"}, {"tenantId", "tenant_id"},
};

void appendPairs(const Col* cols, size_t n, const Ent& e, std::string& colsOut,
                 std::string& valsOut) {
    for (size_t i = 0; i < n; ++i) {
        const Val* v = e.find(cols[i].json);
        if (v == nullptr || v->isNull()) continue;
        if (!colsOut.empty()) { colsOut += ", "; valsOut += ", "; }
        colsOut += cols[i].column;
        valsOut += sqlLit(*v);
    }
}

std::string setPairs(const Col* cols, size_t n, const Ent& e) {
    std::string sets;
    for (size_t i = 0; i < n; ++i) {
        const Val* v = e.find(cols[i].json);
        if (v == nullptr || v->isNull()) continue;
        if (!sets.empty()) sets += ", ";
        sets += std::string(cols[i].column) + " = " + sqlLit(*v);
    }
    return sets;
}

void insertCarInfo(const Ent& car) {
    std::string cols, vals;
    appendPairs(CAR_INFO_COLS, std::size(CAR_INFO_COLS), car, cols, vals);
    mustRun("INSERT INTO car_info (" + cols + ") VALUES (" + vals + ")");
}

void updateCarInfo(const Ent& car) {
    const std::string sets = setPairs(CAR_INFO_COLS, std::size(CAR_INFO_COLS), car);
    if (sets.empty()) return;   // 全 null：MP 不会发 UPDATE
    // @TableLogic 让 updateById 的 WHERE 带上 del_flag='0'
    mustRun("UPDATE car_info SET " + sets + " WHERE id = " + Db::lit(car.plain("id")) +
            " AND del_flag = '0'");
}

/** 对应 CarInfoServiceImpl.updateRedisCarList()：两条缓存都来自 selectCarInfoList(new CarInfo())
 *  的全量结果，写 Redis 时不设过期。
 *  ⚠️ 值必须是 fastjson2 WriteClassName 那种形态（@type、字段按名排序、Long 带 L、null 省略），
 *     直接 dump() 的严格 JSON 会让 Java 反序列化成 JSONObject，用到就 ClassCastException。 */
void updateRedisCarList() {
    const Spec& spec = cm::web::crud::specCarInfo();
    cm::db::Result res = mustRun(cm::web::crud::selectSqlOf(
        spec, cm::web::crud::buildWhere(spec, Json::object()),
        spec.orderBy.empty() ? std::string() : " ORDER BY " + spec.orderBy));
    cm::redis::RedisCache& cache = cm::redis::RedisCache::instance();
    cache.set("car_list", cm::web::crud::fastJson2CachedArray(
                              spec, res.rows, "com.ruoyi.manager.domain.CarInfo"));

    std::string jc = "[";
    for (size_t i = 0; i < res.rows.size(); ++i) {
        if (i) jc += ",";
        // CarVO 只赋了 carId/carNo，其余属性 null ⇒ fastjson2 不写出来
        jc += "{\"@type\":\"com.ruoyi.base.domain.CarVO\",\"carId\":" +
              Json(res.rows[i].str("id")).dump() + ",\"carNo\":" +
              Json(res.rows[i].str("car_no")).dump() + "}";
    }
    cache.set("car_list_jc", jc + "]");
}

/** selectCarInfoList(CarInfo{carNo}) —— 与 /manager/carinfo/list 同一条语句，
 *  所以"异常流水已全部补缴 ⇒ 这辆车查不到"的那个 not exists 照样生效。 */
cm::db::Result selectCarInfoByNo(const std::string& carNo) {
    const Spec& spec = cm::web::crud::specCarInfo();
    Json q = Json::object();
    q["carNo"] = Json(carNo);
    return mustRun(cm::web::crud::selectSqlOf(
        spec, cm::web::crud::buildWhere(spec, q), " ORDER BY " + spec.orderBy));
}

/** 对应 CarInfoServiceImpl.saveCarInfo()。返回值在 exceptrecord 导入里被丢弃，
 *  但"重复车牌 ⇒ 既不写库也不刷缓存"的副作用要保留。 */
void saveCarInfo(Ent& car) {
    cm::db::Transaction tx;   // @Transactional(rollbackFor = Exception.class)
    car["carNo"] = strVal(CommonUtil::isNull(car.plain("carNo")));
    std::string dup = "select count(1) from car_info t where t.del_flag = '0' and t.car_no = " +
                      Db::lit(car.plain("carNo"));
    if (StringUtils::isNotBlank(car.plain("id"))) {
        dup += " and t.id != " + Db::lit(car.plain("id"));
    }
    if (mustCount(dup) > 0) {
        tx.commit();   // 同样是"return 而非 throw"⇒ 事务提交（其实什么都没写）
        return;        // Java: return AjaxResult.error("车牌号存在重复，请确定！")
    }

    const long long userId = cm::security::SecurityUtils::getUserId();
    if (StringUtils::isNotBlank(car.plain("id"))) {
        car["updateBy"] = numVal(std::to_string(userId));
        car["updateTime"] = dateVal(DateUtils::getTime());
        updateCarInfo(car);
        updateRedisCarList();
        tx.commit();   // @Transactional：正常返回才提交，抛异常由析构回滚
        return;
    }
    if (!car.present("escapedAmount") || car["escapedAmount"].isNull()) {
        car["escapedAmount"] = numVal("0");   // BigDecimal.ZERO ⇒ 标度 0，输出就是 0
    }
    car["id"] = strVal(cm::utils::simpleUuid());
    car["delFlag"] = strVal("0");
    car["createBy"] = numVal(std::to_string(userId));
    car["epsId"] = numVal(std::to_string(cm::security::SecurityUtils::getEpsId()));
    car["createTime"] = dateVal(DateUtils::getTime());
    car["updateBy"] = numVal(std::to_string(userId));
    car["updateTime"] = dateVal(DateUtils::getTime());
    // CarInfo 的父类 BasePlusEntityInputNew 上没有 @TableField(fill=…)，tenantId 不会被填
    insertCarInfo(car);
    updateRedisCarList();
    tx.commit();
}

/** 对应 CarExceptRecordServiceImpl.saveCarExcept(carNo)：按车牌把异常流水汇总回写 car_info。 */
void saveCarExcept(const std::string& carNo) {
    cm::db::Result list = mustRun(
        "select t.car_no, count(1) exceptNum, round(sum(t.dif_amount),2) exceptAmount,"
        " round(sum(t.total_amount),2) total_amount, round(sum(t.charge_amount),2) charge_amount,"
        " group_concat(distinct t.escaped_type SEPARATOR ',') escaped_type"
        " from car_except_record t where t.del_flag = '0' and t.car_no = " +
        Db::lit(carNo) + " group by t.car_no");
    std::map<std::string, std::string> carMap;
    for (const auto& row : selectCarInfoByNo(carNo).rows) {
        carMap[CommonUtil::isNull(row.str("car_no"))] = row.str("id");
    }
    for (const auto& row : list.rows) {
        const std::string no = CommonUtil::isNull(row.str("car_no"));
        if (StringUtils::isBlank(no)) continue;
        auto it = carMap.find(no);
        if (it == carMap.end()) continue;
        // uptcarInfo 上只赋了 id / escapedType / escapedAmount 三个属性
        std::string sets;
        const auto esc = row.get("escaped_type");
        if (esc) sets += "escaped_type = " + Db::lit(*esc);
        const auto amt = row.get("except_amount");
        if (amt) sets += (sets.empty() ? std::string("escaped_amount = ") : ", escaped_amount = ") + *amt;
        if (sets.empty()) continue;
        mustRun("UPDATE car_info SET " + sets + " WHERE id = " + Db::lit(it->second) +
                " AND del_flag = '0'");
    }
}

/** 对应 CarExceptRecordServiceImpl.saveCarExceptRecord()。返回值同样被导入循环丢弃 ⇒
 *  "录入区间时间重复！"只是静默不写这一行。 */
void saveCarExceptRecord(Ent& rec) {
    cm::db::Transaction tx;
    const Val& inTime = rec["inTime"];
    const Val& outTime = rec["outTime"];
    if (!inTime.isNull() && !outTime.isNull()) {
        std::string dup = "select count(1) from car_except_record t where t.del_flag = '0'";
        if (StringUtils::isNotBlank(rec.plain("id"))) {
            dup += " and t.id != " + Db::lit(rec.plain("id"));
        }
        // ⚠️ Java 的 isExitsTime 把 in/out 用反了（out_time >= #{inTime} 且 in_time <= #{outTime}），
        //     那是"区间有交集"的判断，跟文案说的"重复"不是一回事 —— 照抄。
        dup += " and t.out_time >= " + Db::lit(inTime.s) + " and t.in_time <= " + Db::lit(outTime.s);
        dup += " and t.car_no = " + Db::lit(rec.plain("carNo"));
        if (mustCount(dup) > 0) {
            tx.commit();   // Java 是 return（不是抛）⇒ 事务照常提交，这一行只是不写
            return;        // AjaxResult.error("录入区间时间重复！")，返回值被调用方丢弃
        }
    }

    if (StringUtils::isNotBlank(rec.plain("id"))) {
        const std::string sets = setPairs(EXCEPT_COLS, std::size(EXCEPT_COLS), rec);
        if (!sets.empty()) {
            mustRun("UPDATE car_except_record SET " + sets + " WHERE id = " +
                    Db::lit(rec.plain("id")) + " AND del_flag = '0'");
        }
    } else {
        rec["status"] = strVal("0");
        // BasePlusEntity 是 ASSIGN_UUID：没带主键时 MP 在客户端补 32 位无横线 UUID
        if (!rec.present("id") || rec["id"].isNull()) rec["id"] = strVal(cm::utils::simpleUuid());
        // MyBatisPlusHandlerConfig.insertFill —— ⚠️ Java 里 tenantId 判的是 epsId 是否为空
        // （复制粘贴错了），照抄：epsId 已有值时 tenantId 也不填。
        if (!rec.present("createTime") || rec["createTime"].isNull()) {
            rec["createTime"] = dateVal(DateUtils::getTime());
        }
        if (!rec.present("createBy") || rec["createBy"].isNull()) {
            rec["createBy"] = numVal(std::to_string(cm::security::SecurityUtils::getUserId()));
        }
        const bool hadEps = rec.present("epsId") && !rec["epsId"].isNull();
        if (!hadEps) {
            rec["epsId"] = numVal(std::to_string(cm::security::SecurityUtils::getEpsId()));
            rec["tenantId"] = numVal(std::to_string(cm::security::SecurityUtils::getTenantId()));
        }
        std::string cols, vals;
        appendPairs(EXCEPT_COLS, std::size(EXCEPT_COLS), rec, cols, vals);
        mustRun("INSERT INTO car_except_record (" + cols + ") VALUES (" + vals + ")");
    }

    if (StringUtils::isNotBlank(rec.plain("carNo"))) saveCarExcept(rec.plain("carNo"));
    tx.commit();
}

// ------------------------------------------------------------------ 两份表定义

/** CarInfoController.initList() —— 8 列。⚠️ "逃费金额（元）"是全角括号 */
const std::vector<ImportEntity>& carInfoEntities() {
    static const std::vector<ImportEntity> v = {
        {"车牌颜色", "plateColor", "1"}, {"车牌号", "carNo", "1"},
        {"车型", "carType", "1"},        {"车种", "carVehicle", ""},
        {"轴数", "carNum", "3"},         {"逃费类型", "escapedType", "1"},
        {"逃费金额（元）", "escapedAmount", "2"}, {"备注", "remark", ""},
    };
    return v;
}

/** CarExceptRecordController.initListTwo() —— 22 列。
 *  空串是有意的：合并表头里非首列的表头文本是 ""，没有对应实体属性的列 prop 也是 ""。
 *  规则串里的 "1" 对 chargeAmount/totalAmount 意思是"必填"，所以这两格为空会报"不能为空"。 */
const std::vector<ImportEntity>& exceptEntities() {
    static const std::vector<ImportEntity> v = {
        {"序号", "", ""},
        {"出口收费站", "outStation", ""},
        {"出口时间", "outTime", "1,8"},
        {"通行PASSID", "passType", ""},
        {"车牌", "carNo", "1"},
        {"交易车型", "carType", ""},
        {"车种", "carVehicle", ""},
        {"入口站", "inStation", ""},
        {"入口时间", "inTime", "1,8"},
        {"漏交通行费类型", "backCol1", ""},
        {"", "escapedType", "1"},
        {"交易金额", "", ""},
        {"", "", ""},
        {"", "chargeAmount", "1,2"},
        {"应交金额", "", ""},
        {"", "", ""},
        {"", "totalAmount", "1,2"},
        {"实际追交金额", "", ""},
        {"", "", ""},
        {"", "", ""},
        {"备注", "remark", ""},
        {"", "", ""},
    };
    return v;
}

/** dataRtnExcel08 的列宽来自 strName（22），跳过的列来自 strNum */
const std::vector<int> exceptSkipCols() { return {0, 11, 12, 14, 15, 17, 18, 19, 21}; }

/** car_type → car_vehicle：Java 是一串 else-if，不在名单里的一律 99 */
std::string vehicleOfCarType(const std::string& carType) {
    if (carType == "1" || carType == "2" || carType == "3" || carType == "4") return "1";
    if (carType == "11" || carType == "12" || carType == "13" || carType == "14" ||
        carType == "15" || carType == "16")
        return "2";
    if (carType == "21" || carType == "22" || carType == "23" || carType == "24" ||
        carType == "25" || carType == "26")
        return "3";
    return "99";
}

/** 两段共用的"逐行 importExcel，成功才进 importList，>100 break" */
template <typename MakeEnt>
void checkRows(const std::vector<ImportEntity>& gzList,
               const std::vector<std::vector<std::string>>& sheetList, MakeEnt makeEnt,
               std::vector<ImportErrorEntity>& errorList, std::vector<Ent>& importList) {
    for (size_t i = 0; i < sheetList.size(); ++i) {
        Json objMap = Json::object();
        const bool clean =
            cm::web::importx::importRow(errorList, gzList, static_cast<int>(i), sheetList[i], objMap);
        if (clean) {
            Ent e;
            for (const auto& bo : gzList) {
                if (bo.colProp.empty()) continue;
                const std::string raw = objMap.contains(bo.colProp) && objMap[bo.colProp].is_string()
                                            ? objMap[bo.colProp].get<std::string>()
                                            : std::string();
                makeEnt(e, bo.colProp, raw);
            }
            importList.push_back(std::move(e));
        }
        if (errorList.size() > 100) break;
    }
}

// ------------------------------------------------------------------ POST /manager/carinfo/import

cm::http::ApiResponse doCarInfoImport(RequestContext& ctx) {
    const Spec& spec = cm::web::crud::specCarInfo();
    const cm::http::MultipartPart& part = filePart(ctx);
    // Java: fileName.lastIndexOf(".xlsx") == -1 —— 是"包含"，不是"以…结尾"
    if (part.filename.rfind(".xlsx") == std::string::npos) {
        return BaseController::ok(AjaxResult::error("请上传Excel文件(.xlsx)"));
    }
    cm::utils::Xlsx x = loadSheet(part.data, false);   // getCellFormatValue07：日期是 yyyy/MM/dd
    const auto& gzList = carInfoEntities();
    const auto colsName = colNamesOf(gzList);
    if (!cm::web::importx::colVda(x, 0, colsName)) {
        return BaseController::ok(AjaxResult::error("导入失败,模板不正确,请下载对应的模板！"));
    }
    const auto sheetList = cm::web::importx::dataRtn(x, 1, colsName.size());
    if (sheetList.empty()) {
        return BaseController::ok(AjaxResult::error("导入失败,模板excel没有数据可以导入，请确定！"));
    }

    std::vector<ImportErrorEntity> errorList;
    std::vector<Ent> importList;
    checkRows(gzList, sheetList,
              [&spec](Ent& e, const std::string& prop, const std::string& raw) {
                  bindText(spec, e, prop, raw);
              },
              errorList, importList);

    if (errorList.empty()) {
        const auto plateColorMap = dictLabelMap("plate_color");
        const auto carTypeMap = dictLabelMap("car_type");
        const auto carVehicleMap = dictLabelMap("car_vehicle");
        const auto escapedTypeMap = dictLabelMap("escaped_type");

        for (size_t i = 0; i < importList.size(); ++i) {
            const int rowArg = static_cast<int>(i) + 1;   // getErrorBO 里还会再 +1
            Ent& addbo = importList[i];

            const std::string plateColor = CommonUtil::isNull(addbo.plain("plateColor"));
            if (StringUtils::isNotBlank(plateColor)) {
                auto it = plateColorMap.find(plateColor);
                if (it != plateColorMap.end()) addbo["plateColor"] = strVal(it->second);
                else errorList.push_back(cm::web::importx::errorBo(
                    rowArg, "车牌颜色", plateColor + " 车牌颜色不存在,请在字典菜单维护！"));
            }
            const std::string carType = CommonUtil::isNull(addbo.plain("carType"));
            if (StringUtils::isNotBlank(carType)) {
                auto it = carTypeMap.find(carType);
                if (it != carTypeMap.end()) addbo["carType"] = strVal(it->second);
                else errorList.push_back(cm::web::importx::errorBo(
                    rowArg, "车型", carType + " 车型不存在,请在字典菜单维护！"));
            }
            const std::string carVehicle = CommonUtil::isNull(addbo.plain("carVehicle"));
            if (StringUtils::isNotBlank(carVehicle)) {
                auto it = carVehicleMap.find(carVehicle);
                if (it != carVehicleMap.end()) addbo["carVehicle"] = strVal(it->second);
                else errorList.push_back(cm::web::importx::errorBo(
                    rowArg, "车种", carVehicle + " 车种不存在,请在字典菜单维护！"));
            }
            // 逃费类型：deleteEnd（只去一个尾逗号）→ 全角逗号换半角 → 逐个翻译拼回 "v1,v2,"
            // → 再 deleteEnd 去掉最后一个逗号。认不出的逐个报错，值里不会带上它。
            const std::string escapedType =
                replaceAll(CommonUtil::deleteEnd(addbo.plain("escapedType")), "，", ",");
            std::string escapedTypeValue;
            if (!escapedType.empty()) {
                for (const auto& one : cm::web::importx::javaSplitComma(escapedType)) {
                    auto it = escapedTypeMap.find(one);
                    if (it != escapedTypeMap.end()) {
                        escapedTypeValue += CommonUtil::isNull(it->second) + ",";
                    } else {
                        errorList.push_back(cm::web::importx::errorBo(
                            rowArg, "逃费类型", one + " 逃费类型不存在,请在字典菜单维护！"));
                    }
                }
            }
            addbo["escapedType"] = strVal(CommonUtil::deleteEnd(escapedTypeValue));

            if (errorList.size() > 100) break;
        }
    }

    if (errorList.empty()) {
        const long long userId = cm::security::SecurityUtils::getUserId();
        std::vector<size_t> addIdx, updIdx;
        for (size_t i = 0; i < importList.size(); ++i) {
            Ent& addbo = importList[i];
            addbo["carNo"] = strVal(CommonUtil::isNull(addbo.plain("carNo")));   // 去空格
            cm::db::Result q = selectCarInfoByNo(addbo.plain("carNo"));
            if (!q.rows.empty()) addbo["id"] = strVal(q.rows[0].str("id"));
        }
        // CarInfoServiceImpl.doImport —— 整段没有 @Transactional，插一半失败就留一半
        for (size_t i = 0; i < importList.size(); ++i) {
            Ent& car = importList[i];
            if (StringUtils::isNotBlank(car.plain("id"))) {
                car["updateBy"] = numVal(std::to_string(userId));
                car["updateTime"] = dateVal(DateUtils::getTime());
                updIdx.push_back(i);
            } else {
                if (!car.present("escapedAmount") || car["escapedAmount"].isNull()) {
                    car["escapedAmount"] = numVal("0");
                }
                car["id"] = strVal(cm::utils::simpleUuid());
                car["delFlag"] = strVal("0");
                car["createBy"] = numVal(std::to_string(userId));
                car["epsId"] = numVal(std::to_string(cm::security::SecurityUtils::getEpsId()));
                car["createTime"] = dateVal(DateUtils::getTime());
                car["updateBy"] = numVal(std::to_string(userId));
                car["updateTime"] = dateVal(DateUtils::getTime());
                addIdx.push_back(i);
            }
        }
        for (size_t idx : addIdx) {
            // Java 在插入前**又**重设了一次 createTime（注释还写着"创建的时间一样"，其实每行各取各的）
            importList[idx]["createTime"] = dateVal(DateUtils::getTime());
            insertCarInfo(importList[idx]);
        }
        for (size_t idx : updIdx) updateCarInfo(importList[idx]);
        updateRedisCarList();
    }

    if (!errorList.empty()) return errorResponse(errorList);
    return BaseController::ok(AjaxResult::success("数据导入成功", entityArrayJson(spec, importList)));
}

// ------------------------------------------------------------- POST /manager/exceptrecord/import

cm::http::ApiResponse doExceptImport(RequestContext& ctx) {
    const Spec& spec = cm::web::crud::specCarExceptRecord();
    const cm::http::MultipartPart& part = filePart(ctx);
    if (part.filename.rfind(".xlsx") == std::string::npos) {
        return BaseController::ok(AjaxResult::error("请上传Excel文件(.xlsx)"));
    }
    cm::utils::Xlsx x = loadSheet(part.data, true);    // getCellFormatValue08：日期带时分秒

    // ⚠️ gzList 与 gzListThree 都是 initListTwo()：Java 里那句
    //    `List<ImportEntity> gzListThree = initListTwo();` 不是笔误，是原样；
    //    initListThree() 定义了但没人调。所以两次表头比的是同一份名字，只是行号 1/2 换着来。
    const auto& gzList = exceptEntities();
    const auto colsName = colNamesOf(gzList);
    if (!cm::web::importx::colVda(x, 1, colsName) && !cm::web::importx::colVda(x, 2, colsName)) {
        return BaseController::ok(AjaxResult::error("导入失败,模板不正确,请下载对应的模板！"));
    }
    const auto sheetList =
        cm::web::importx::dataRtn(x, 3, colsName.size(), exceptSkipCols());
    if (sheetList.empty()) {
        return BaseController::ok(AjaxResult::error("导入失败,模板excel没有数据可以导入，请确定！"));
    }

    std::vector<ImportErrorEntity> errorList;
    std::vector<Ent> importList;
    checkRows(gzList, sheetList,
              [&spec](Ent& e, const std::string& prop, const std::string& raw) {
                  bindText(spec, e, prop, raw);
              },
              errorList, importList);

    std::vector<Ent> addCars;
    std::map<std::string, std::string> addCarMap;

    if (errorList.empty()) {
        std::map<std::string, std::string> carMap;      // 车牌 -> car_info.id
        std::map<std::string, Val> carNumMap;
        for (const auto& row : selectCarInfoByNo(std::string()).rows) {
            // selectCarInfoList(new CarInfo())：注意那条 not exists 会把"已缴清"的车整个滤掉
            carMap[CommonUtil::isNull(row.str("car_no"))] = row.str("id");
            const auto num = row.get("car_num");
            carNumMap[CommonUtil::isNull(row.str("car_no"))] =
                num ? numVal(*num) : Val();
        }
        std::map<std::string, std::string> tollMap;
        for (const auto& row : mustRun("select distinct t.toll_code,t.toll_name FROM ods_szdn_toll t"
                                       " WHERE 1=1 order by t.toll_name").rows) {
            tollMap[CommonUtil::isNull(row.str("toll_name"))] =
                CommonUtil::isNull(row.str("toll_code"));
        }
        const auto carTypeMap = dictLabelMap("car_type_change");
        const auto escapedTypeMap = dictLabelMap("escaped_type");
        const auto plateColorMap = dictLabelMap("plate_color");

        for (size_t i = 0; i < importList.size(); ++i) {
            const int rowArg = static_cast<int>(i) + 1;
            Ent& addbo = importList[i];

            const std::string carType = CommonUtil::isNull(addbo.plain("carType"));
            if (StringUtils::isNotBlank(carType)) {
                auto it = carTypeMap.find(carType);
                if (it != carTypeMap.end()) addbo["carType"] = strVal(it->second);
                // 认不出就**不报错也不改**：这是与 carinfo 导入最不一样的一处
            }
            // 车种由车型推出来，Excel 里那一格（colProp=carVehicle）先被覆盖掉再判空
            const std::string carVehicle = vehicleOfCarType(CommonUtil::isNull(addbo.plain("carType")));
            if (StringUtils::isNotBlank(carVehicle)) addbo["carVehicle"] = strVal(carVehicle);

            // 车牌 "_颜色" 形态：拆完把颜色只用于新建车辆，实体本身没有 plateColor 属性
            std::string carNo = CommonUtil::isNull(addbo.plain("carNo"));
            std::string plateColor;
            if (carNo.find('_') != std::string::npos) {
                const auto pieces = StringUtils::split(carNo, '_');   // Java split("_")：丢尾空串
                if (pieces.size() > 1) plateColor = pieces[1];
                carNo = pieces.empty() ? std::string() : pieces[0];
            }
            addbo["carNo"] = strVal(carNo);
            if (StringUtils::isNotBlank(plateColor)) {
                auto it = plateColorMap.find(plateColor);
                if (it != plateColorMap.end()) plateColor = CommonUtil::isNull(it->second);
            }

            if (StringUtils::isNotBlank(carNo)) {
                auto it = carMap.find(carNo);
                if (it != carMap.end()) {
                    addbo["carId"] = strVal(it->second);
                    const Val& num = carNumMap[carNo];
                    if (!num.isNull()) addbo["carNum"] = num;
                } else if (addCarMap.find(carNo) == addCarMap.end()) {
                    Ent nc;
                    nc["carNo"] = strVal(carNo);
                    nc["plateColor"] = strVal(plateColor);
                    nc["carType"] = addbo["carType"];
                    nc["carVehicle"] = addbo["carVehicle"];
                    addCars.push_back(std::move(nc));
                    addCarMap[carNo] = carNo;
                }
            }

            const std::string escapedType = CommonUtil::isNull(addbo.plain("escapedType"));
            if (StringUtils::isNotBlank(escapedType)) {
                auto it = escapedTypeMap.find(escapedType);
                if (it != escapedTypeMap.end()) addbo["escapedType"] = strVal(it->second);
                else errorList.push_back(cm::web::importx::errorBo(
                    rowArg, "逃费类型", escapedType + " 逃费类型不存在,请在字典菜单维护！"));
            }

            const std::string inStation = CommonUtil::isNull(addbo.plain("inStation"));
            if (StringUtils::isNotBlank(inStation)) {
                auto it = tollMap.find(inStation);
                if (it != tollMap.end()) {
                    addbo["inStation"] = strVal(inStation);
                    addbo["inStationId"] = strVal(it->second);
                    // 认不出：不报错，stationId 留 null
                }
            }
            const std::string outStation = CommonUtil::isNull(addbo.plain("outStation"));
            if (StringUtils::isNotBlank(outStation)) {
                auto it = tollMap.find(outStation);
                if (it != tollMap.end()) {
                    addbo["outStation"] = strVal(outStation);
                    addbo["outStationId"] = strVal(it->second);
                }
            }

            const Val& total = addbo["totalAmount"];
            const Val& charge = addbo["chargeAmount"];
            if (!total.isNull() && !charge.isNull()) {
                double a = 0, b = 0;
                try { a = std::stod(total.s); b = std::stod(charge.s); } catch (...) {}
                if (a < b) {
                    errorList.push_back(
                        cm::web::importx::errorBo(rowArg, "缴费金额", "收费金额不能大于应缴金额"));
                }
            }
            const Val& inTime = addbo["inTime"];
            const Val& outTime = addbo["outTime"];
            if (!inTime.isNull() && !outTime.isNull()) {
                // 两边都是定长 "yyyy-MM-dd HH:mm:ss"，字典序比较即时间序
                if (inTime.s > outTime.s) {
                    errorList.push_back(
                        cm::web::importx::errorBo(rowArg, "时间", "入口时间大于出口时间，请确认!"));
                }
            }

            if (errorList.size() > 100) break;
        }
    }

    if (errorList.empty()) {
        for (auto& car : addCars) saveCarInfo(car);
        for (auto& addbo : importList) {
            const Val& total = addbo["totalAmount"];
            const Val& charge = addbo["chargeAmount"];
            if (!total.isNull() && !charge.isNull()) {
                double a = 0, b = 0;
                try { a = std::stod(total.s); b = std::stod(charge.s); } catch (...) {}
                // BigDecimal.subtract 保持标度：两个都是 .00 时结果也写成两位
                addbo["difAmount"].t = Val::DEC;
                char buf[64];
                std::snprintf(buf, sizeof(buf), "%.2f", a - b);
                addbo["difAmount"].s = buf;
            }
            Json q = Json::object();
            q["carNo"] = Json(addbo.plain("carNo"));
            if (!addbo["inTime"].isNull()) q["inTime"] = Json(addbo["inTime"].s);
            const std::string sql = cm::web::crud::selectSqlOf(
                spec, cm::web::crud::buildWhere(spec, q), " ORDER BY " + spec.orderBy);
            cm::db::Result same = mustRun(sql);
            if (!same.rows.empty()) addbo["id"] = strVal(same.rows[0].str("id"));
            saveCarExceptRecord(addbo);
        }
    }

    if (!errorList.empty()) return errorResponse(errorList);
    return BaseController::ok(AjaxResult::success("数据导入成功", entityArrayJson(spec, importList)));
}

}  // namespace

void registerManagerImportControllers(Router& r) {
    // Java 侧两个方法都没有 @PreAuthorize（只有 @Log），所以只吃默认的 authenticated()
    r.post("/manager/carinfo/import", [](RequestContext& ctx) { return doCarInfoImport(ctx); });
    r.post("/manager/exceptrecord/import",
           [](RequestContext& ctx) { return doExceptImport(ctx); });
}

}  // namespace cm::web
