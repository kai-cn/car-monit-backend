// spec 驱动 CRUD 引擎：把 Java 侧 “RuoYi Generator + MyBatis-Plus + PageHelper” 的
// 同构 CRUD 行为集中实现一次，实体只提供 Spec 数据。
#include "cm/framework/web/crud/CrudSpec.hpp"

#include <cstdlib>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/Excel.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/http/HttpResponse.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web::crud {
using cm::db::Db;
using cm::core::domain::AjaxResult;

std::string Spec::pkColumn() const {
    for (const auto& f : fields) {
        if (f.pk) return f.column;
    }
    return "id";
}

std::string Spec::pkJson() const {
    for (const auto& f : fields) {
        if (f.pk) return f.json;
    }
    return "id";
}

bool Spec::pkIsString() const {
    for (const auto& f : fields) {
        if (f.pk) return f.fmt != Fmt::Int && f.fmt != Fmt::Long && f.fmt != Fmt::Double;
    }
    return true;
}

bool Spec::isTailAlias(const std::string& name) const {
    if (selectTail.empty()) return false;
    // 逗号分隔的每个表达式，取结尾那个标识符就是它的列别名：
    // "concat(sd.dept_name, ' ', su.nick_name) createInfo" -> createInfo
    std::string item;
    size_t depth = 0;
    for (size_t i = 0; i <= selectTail.size(); ++i) {
        const char c = i == selectTail.size() ? ',' : selectTail[i];
        if (c == '(') ++depth;
        if (c == ')') --depth;
        if (c == ',' && depth == 0) {
            size_t end = item.size();
            while (end > 0 && std::isspace(static_cast<unsigned char>(item[end - 1]))) --end;
            size_t start = end;
            while (start > 0 && (std::isalnum(static_cast<unsigned char>(item[start - 1])) ||
                                 item[start - 1] == '_'))
                --start;
            if (start < end && item.substr(start, end - start) == name) return true;
            item.clear();
            continue;
        }
        item.push_back(c);
    }
    return false;
}

std::string Spec::selectColumns() const {
    std::string out;
    const std::string prefix = alias.empty() ? std::string() : (alias + ".");
    for (const auto& f : fields) {
        // column == nullptr：Java 里是父类的非列字段（如 BaseUuidEntity.deptSubCode），
        // MyBatis 不填、Jackson 输出 null，所以只进 JSON 不进 SELECT
        if (f.column == nullptr) continue;
        // Java 的 Vo 没投影这一列：它能当 WHERE 条件，但结果集里没有，
        // 照样 SELECT 出来就会凭空比 Java 多返回数据（实测 car_suspicious 的 track_josn）。
        if (!f.inVo) continue;
        if (!out.empty()) out += ", ";
        out += prefix + f.column;
    }
    // 派生列（createInfo 那种 concat）跟着 Vo 之后，顺序与 Java 的 SELECT 一致
    if (!selectTail.empty()) out += ", " + selectTail;
    return out;
}

std::string pkLiteral(const Spec& spec, const std::string& raw) {
    if (spec.pkIsString()) return Db::lit(raw);
    return Db::lit(static_cast<long long>(std::atoll(raw.c_str())));
}

namespace {

std::string fromClause(const Spec& s) {
    if (!s.fromSql.empty()) return s.fromSql;
    return "FROM " + std::string(s.table) + (s.alias.empty() ? std::string() : (" " + s.alias));
}

std::string qualified(const Spec& s, const std::string& col) {
    return s.alias.empty() ? col : (s.alias + "." + col);
}

bool isDateFmt(Fmt f) {
    return f == Fmt::DateYmd || f == Fmt::DateYmdHms || f == Fmt::DateIso || f == Fmt::DateTimeIso;
}

std::string jsonAsString(const Json& v) {
    if (v.is_string()) return v.get<std::string>();
    if (v.is_boolean()) return v.get<bool>() ? "1" : "0";
    if (v.is_number_integer()) return std::to_string(v.get<long long>());
    return v.dump();
}

/** JSON 值是否算“空”（对应 XML 的 x != null and x != ''） */
bool jsonEmpty(const Json& v) { return v.is_null() || (v.is_string() && v.get<std::string>().empty()); }

const Json* findField(const Json& obj, const std::string& key) {
    if (!obj.is_object()) return nullptr;
    auto it = obj.find(key);
    return it == obj.end() ? nullptr : &*it;
}

std::string jsonToSql(const Field& f, const Json& v) {
    if (!isDateFmt(f.fmt)) {
        if (v.is_number_integer()) return Db::lit(static_cast<long long>(v.get<long long>()));
        if (v.is_number_float()) return Db::lit(v.get<double>());
        if (v.is_boolean()) return Db::lit(v.get<bool>());
    }
    return Db::lit(jsonAsString(v));
}

/** 区间条件：对应 XML 里 date_format(col,'%Y%m%d') 比较 params.beginTime/endTime */
std::string rangeExpr(const Spec& s, const Field& f, const std::string& op, const std::string& value) {
    const std::string col = qualified(s, f.column);
    switch (s.rangeStyle) {
        case RangeStyle::DayYyyymmdd:
            return " and date_format(" + col + ", '%Y%m%d') " + op + " date_format(" +
                   Db::lit(value) + ", '%Y%m%d')";
        case RangeStyle::MonthYyyymm:
            return " and date_format(" + col + ", '%Y%m') " + op + " date_format(" + Db::lit(value) +
                   ", '%Y%m')";
        case RangeStyle::Raw:
            return " and " + col + " " + op + " " + Db::lit(value);
    }
    return {};
}

} // namespace

Json rowToJson(const Spec& spec, const cm::db::Row& row) {
    Json j = Json::object();
    for (const auto& f : spec.fields) {
        if (f.column == nullptr) {
            // `<include refid="Vo"/>,concat(...) createInfo` 这种派生列：Java 的实体上它
            // 只是普通属性（没有对应表列），所以 Field.column 是 nullptr，值只能从
            // selectTail 的别名里来。不认识它就等于"Java 有值、C++ 恒 null"。
            if (!spec.selectTail.empty() && spec.isTailAlias(f.json)) {
                auto v = row.get(f.json);
                j[f.json] = v ? Json(*v) : Json(nullptr);
                continue;
            }
            // 非列属性：Java 的字段初始值（= "0" / = new ArrayList<>()）会被 Jackson 原样输出，
            // 只有没有初始值时才是 null。列属性走下面的 DB 取值，NULL 就是 null。
            j[f.json] = f.dflt ? Json::parse(f.dflt) : Json(nullptr);
            continue;
        }
        auto v = row.get(f.column);
        if (!v) {
            // “列不在结果集里”（Vo 没投影）与“列值为 NULL”是两回事：前者 MyBatis 根本不调
            // setter，属性保持 Java 字段的声明初值；后者会被 setter 显式写成 null。
            j[f.json] = (!row.has(f.column) && f.dflt) ? Json::parse(f.dflt) : Json(nullptr);
            continue;
        }
        switch (f.fmt) {
            case Fmt::Int:
            case Fmt::Long: {
                auto n = row.optI64(f.column);
                j[f.json] = n ? Json(*n) : Json(nullptr);
                break;
            }
            case Fmt::Double:
                j[f.json] = v->empty() ? Json(nullptr) : Json(row.dbl(f.column));
                break;
            case Fmt::Bool: {
                auto b = row.optBool(f.column);
                j[f.json] = b ? Json(*b) : Json(nullptr);
                break;
            }
            case Fmt::DateYmd: {
                auto ms = utils::DateUtils::parseDbDateTime(*v);
                j[f.json] = ms ? Json(utils::DateUtils::formatMillis(*ms, utils::DateUtils::YYYY_MM_DD))
                               : Json(nullptr);
                break;
            }
            case Fmt::DateYmdHms: {
                auto ms = utils::DateUtils::parseDbDateTime(*v);
                j[f.json] = ms ? Json(utils::DateUtils::formatJsonDate(*ms)) : Json(*v);
                break;
            }
            case Fmt::DateIso:
            case Fmt::DateTimeIso: {
                auto ms = utils::DateUtils::parseDbDateTime(*v);
                j[f.json] = ms ? Json(utils::DateUtils::formatIsoDate(*ms)) : Json(nullptr);
                break;
            }
            case Fmt::Str:
            default:
                j[f.json] = Json(*v);
                break;
        }
    }
    return j;
}

std::string buildWhere(const Spec& spec, const Json& query) {
    std::string where = "WHERE 1=1" + spec.extraWhere;
    for (const auto& f : spec.fields) {
        if (f.cond == Cond::None) continue;
        // 条件左值以 XML 为准：RuoYi 里“属性自身列”和“条件实际过滤的列”并不总是一致
        // （car_suspicious 的 sectionCode/sectionName 查的是 track_names，
        //  car_except_record 的 exceptIds 是 find_in_set(t.id, …)）。
        // 查询辅助属性（applyTime1 / carNoQuery）本身不是列，左值只能来自 condColumn。
        const std::string col = f.condColumn ? qualified(spec, f.condColumn)
                              : (f.column ? qualified(spec, f.column) : std::string());
        if (col.empty()) continue;
        if (f.cond == Cond::DateRange) {
            const Json* params = findField(query, "params");
            if (params == nullptr) continue;
            if (const Json* b = findField(*params, "beginTime"); b != nullptr && !jsonEmpty(*b)) {
                where += rangeExpr(spec, f, ">=", jsonAsString(*b));
            }
            if (const Json* e = findField(*params, "endTime"); e != nullptr && !jsonEmpty(*e)) {
                where += rangeExpr(spec, f, "<=", jsonAsString(*e));
            }
            continue;
        }
        const Json* v = findField(query, f.json);
        if (v == nullptr) continue;
        const bool skip = (f.cond == Cond::EqNotNull) ? v->is_null() : jsonEmpty(*v);
        if (skip) continue;
        switch (f.cond) {
            case Cond::Like:
                where += " and " + col + " like concat('%', " + Db::lit(jsonAsString(*v)) + ", '%')";
                break;
            // XML 里写的是 col >= STR_TO_DATE(#{applyTime1},'%Y-%m-%d %H:%i:%s')。
            // MySQL 对 DATETIME 与字符串常量做的隐式转换与 STR_TO_DATE 同格式，直接传字面量等价。
            case Cond::Gte:
                where += " and " + col + " >= " + Db::lit(jsonAsString(*v));
                break;
            case Cond::Lte:
                where += " and " + col + " <= " + Db::lit(jsonAsString(*v));
                break;
            case Cond::Ne:
                where += " and " + col + " != " + Db::lit(jsonAsString(*v));
                break;
            case Cond::NotLike:
                where += " and " + col + " not like concat('%', " + Db::lit(jsonAsString(*v)) + ", '%')";
                break;
            case Cond::FindInSet:
                where += " and find_in_set(" + Db::lit(jsonAsString(*v)) + ", " + col + ")";
                break;
            case Cond::FindInSetCol: {
                // XML 里写的是 find_in_set(t.id, #{exceptIds})：左值另有其列（通常是主键）
                const std::string left =
                    f.condColumn ? qualified(spec, f.condColumn) : col;
                where += " and find_in_set(" + left + ", " + Db::lit(jsonAsString(*v)) + ")";
                break;
            }
            default:
                where += " and " + col + " = " + Db::lit(jsonAsString(*v));
                break;
        }
    }
    return where;
}

Json bindQuery(const Spec& spec, RequestContext& ctx) {
    Json q = Json::object();
    for (const auto& f : spec.fields) {
        // Spring 的参数绑定是把**所有**有 setter 的属性都填上，与它是不是查询条件无关。
        // controller 里的前置处理常常读的就是非条件属性
        // （listHistory 读 getCode() 再 setTrackNames()），只绑条件就会读到空。
        if (auto v = ctx.optParam(f.json)) q[f.json] = *v;
    }
    Json params = Json::object();
    if (auto b = ctx.optParam("params[beginTime]")) params["beginTime"] = *b;
    if (auto e = ctx.optParam("params[endTime]")) params["endTime"] = *e;
    if (!params.empty()) q["params"] = params;
    return q;
}

/** MetaObjectHandler 的两个 fill 钩子：它们改的是**实体**，所以后续 "只写非 null 列"
 *  的循环自然会把补上的值带进 SQL —— 这里同样先补进 body 的副本，再走原逻辑。
 *  ⚠️ insertFill 里 tenantId 判的是 "epsId == null"（Java 的复制粘贴错误）：
 *     epsId 有值时 tenantId 就不会被补。照抄。 */
Json applyInsertFill(const Spec& spec, const Json& body) {
    if (!spec.auditFillInsert) return body;
    Json out = body;
    const long long userId = cm::security::SecurityUtils::getUserId();
    const long long epsId = cm::security::SecurityUtils::getEpsId();
    const bool hadEps = findField(out, "epsId") != nullptr;
    const auto putIf = [&](const char* key, Json v) {
        if (findField(out, key) == nullptr) out[key] = std::move(v);
    };
    putIf("createTime", Json(cm::utils::DateUtils::getTime()));
    putIf("createBy", Json(userId));
    putIf("epsId", Json(epsId));
    if (!hadEps) putIf("tenantId", Json(cm::security::SecurityUtils::getTenantId()));
    return out;
}

Json applyUpdateFill(const Spec& spec, const Json& body) {
    if (!spec.auditFillUpdate) return body;
    Json out = body;
    if (findField(out, "updateTime") == nullptr) {
        out["updateTime"] = Json(cm::utils::DateUtils::getTime());
    }
    if (findField(out, "updateBy") == nullptr) {
        out["updateBy"] = Json(cm::security::SecurityUtils::getUserId());
    }
    return out;
}

std::string buildInsert(const Spec& spec, const Json& bodyIn) {
    const Json body = applyInsertFill(spec, bodyIn);
    std::string cols, vals;
    // MyBatis-Plus 的 IdType.ASSIGN_UUID（BasePlusEntity / BasePlusEntityNew / BaseUuidEntity 都是）
    // 在**客户端**生成 32 位无横线小写 UUID：请求没带 id 时也必须补上，否则 INSERT 直接缺主键列。
    const std::string generatedPk = (spec.pkIsString() && !findField(body, spec.pkJson()))
                                        ? cm::utils::simpleUuid()
                                        : std::string();
    for (const auto& f : spec.fields) {
        if (!f.insertable) continue;
        if (f.pk && f.autoIncrement) continue;  // 自增主键交给数据库
        const Json* v = findField(body, f.json);
        if (v == nullptr || v->is_null()) {
            if (f.pk && !generatedPk.empty()) {
                if (!cols.empty()) {
                    cols += ", ";
                    vals += ", ";
                }
                cols += f.column;
                vals += Db::lit(generatedPk);
                continue;
            }
            continue;  // MyBatis-Plus 默认 NOT_NULL 策略
        }
        if (!cols.empty()) {
            cols += ", ";
            vals += ", ";
        }
        cols += f.column;
        vals += jsonToSql(f, *v);
    }
    if (cols.empty()) return "INSERT INTO " + std::string(spec.table) + " VALUES ()";
    return "INSERT INTO " + std::string(spec.table) + " (" + cols + ") VALUES (" + vals + ")";
}

std::string buildUpdate(const Spec& spec, const Json& bodyIn) {
    const Json body = applyUpdateFill(spec, bodyIn);
    const Json* pk = findField(body, spec.pkJson());
    if (pk == nullptr || pk->is_null()) return {};  // 无主键时 Java 侧不会发 UPDATE
    const std::string pk_col = std::string(spec.pkColumn());
    const std::string pk_value = pkLiteral(spec, jsonAsString(*pk));
    std::string sets;
    for (const auto& f : spec.fields) {
        if (!f.updatable || f.pk) continue;
        const Json* v = findField(body, f.json);
        if (v == nullptr || v->is_null()) continue;  // null 不更新，空串照写
        if (!sets.empty()) sets += ", ";
        sets += std::string(f.column) + " = " + jsonToSql(f, *v);
    }
    if (sets.empty()) {
        // 全字段为 null：MP 不会生成 SET，这里用恒等赋值保持“语句合法且无副作用”
        return "UPDATE " + std::string(spec.table) + " SET " + pk_col + " = " + pk_col + " WHERE " +
               pk_col + " = " + pk_value;
    }
    return "UPDATE " + std::string(spec.table) + " SET " + sets + " WHERE " + pk_col + " = " + pk_value;
}

cm::http::ApiResponse exportExcel(const Spec& spec, const Json& rows, const std::string& sheetName) {
    std::vector<cm::common::utils::ExcelColumn> cols;
    for (const auto& f : spec.fields) {
        if (f.excel == nullptr) continue;
        cm::common::utils::ExcelColumn c;
        c.name = f.excel;
        c.field = f.json;
        c.isNumeric = (f.fmt == Fmt::Int || f.fmt == Fmt::Long || f.fmt == Fmt::Double);
        cols.push_back(c);
    }
    std::vector<Json> items;
    if (rows.is_array()) {
        for (const auto& r : rows) items.push_back(r);
    }
    // 对应 ExcelUtil.exportExcel：写出真 xlsx 到 profile/download，
    // 返回值是 AjaxResult.success(filename) —— String 命中 msg 重载，所以没有 data
    const std::string filename = cm::common::utils::Excel::encodingFilename(sheetName);
    cm::common::utils::Excel::writeDownloadFile(
        filename, cm::common::utils::Excel::exportXlsx(cols, items, sheetName));
    return cm::http::ApiResponse::json(AjaxResult::success(filename).toJson());
}

namespace {

Json fetchRows(const Spec& spec, const cm::db::Result& res) {
    Json arr = Json::array();
    for (const auto& row : res.rows) {
        Json j = rowToJson(spec, row);
        if (spec.hooks.afterRow) spec.hooks.afterRow(j, row);
        arr.push_back(std::move(j));
    }
    return arr;
}

std::string orderSqlOf(const Spec& spec, const cm::db::PageRequest& page) {
    // PageHelper 用前端传来的 order_by（已过 SqlUtil.escapeOrderBySql），
    // 没有则回落到 XML 里写死的 order by
    if (!page.orderBy.empty()) return " ORDER BY " + page.orderBy;
    if (!spec.orderBy.empty()) return " ORDER BY " + spec.orderBy;
    return {};
}

std::string selectSql(const Spec& spec, const std::string& where, const std::string& order) {
    return "SELECT " + spec.selectColumns() + " " + fromClause(spec) + " " + where + order;
}

cm::http::ApiResponse runList(const Spec& spec, RequestContext& ctx) {
    Json query = bindQuery(spec, ctx);
    if (spec.hooks.beforeQuery) spec.hooks.beforeQuery(ctx, query);
    const std::string where = buildWhere(spec, query);
    const auto page = ctx.pageRequest();
    const std::string order = orderSqlOf(spec, page);
    if (page.enabled) {
        auto pr = cm::db::queryPage("SELECT COUNT(1) " + fromClause(spec) + " " + where,
                                    selectSql(spec, where, order), page);
        return BaseController::ok(BaseController::dataTable(fetchRows(spec, pr.rows), pr.total));
    }
    cm::db::Result res;
    Json arr = Json::array();
    if (Db::instance().query(selectSql(spec, where, order), res)) arr = fetchRows(spec, res);
    return BaseController::ok(BaseController::dataTable(arr, static_cast<long long>(arr.size())));
}

cm::http::ApiResponse runExport(const Spec& spec, RequestContext& ctx) {
    Json query = bindQuery(spec, ctx);
    if (spec.hooks.beforeQuery) spec.hooks.beforeQuery(ctx, query);
    cm::db::Result res;
    Json arr = Json::array();
    if (Db::instance().query(selectSql(spec, buildWhere(spec, query), {}), res)) {
        arr = fetchRows(spec, res);
    }
    return exportExcel(spec, arr,
                       spec.excelSheetName.empty() ? std::string("Sheet1") : spec.excelSheetName);
}

cm::http::ApiResponse runGetInfo(const Spec& spec, RequestContext& ctx, const std::string& pkVar) {
    const std::string where =
        "WHERE " + std::string(spec.pkColumn()) + " = " + pkLiteral(spec, ctx.pathVar(pkVar));
    cm::db::Result res;
    Json arr = Json::array();
    if (Db::instance().query(selectSql(spec, where, {}), res)) arr = fetchRows(spec, res);
    // Java: 记录不存在时 AjaxResult.success(null)
    return BaseController::ok(AjaxResult::success(arr.empty() ? Json(nullptr) : arr.front()));
}

cm::http::ApiResponse runAdd(const Spec& spec, RequestContext& ctx) {
    Json body = ctx.body();
    if (spec.hooks.beforeInsert) spec.hooks.beforeInsert(ctx, body);
    long long affected = 0;
    if (!Db::instance().execute(buildInsert(spec, body), &affected)) {
        return BaseController::ok(AjaxResult::error("新增失败"));
    }
    return BaseController::ok(BaseController::toAjax(affected));
}

cm::http::ApiResponse runEdit(const Spec& spec, RequestContext& ctx) {
    Json body = ctx.body();
    if (spec.hooks.beforeUpdate) spec.hooks.beforeUpdate(ctx, body);
    const std::string sql = buildUpdate(spec, body);
    if (sql.empty()) return BaseController::ok(AjaxResult::error("修改失败"));
    long long affected = 0;
    if (!Db::instance().execute(sql, &affected)) {
        return BaseController::ok(AjaxResult::error("修改失败"));
    }
    return BaseController::ok(BaseController::toAjax(affected));
}

cm::http::ApiResponse runRemove(const Spec& spec, RequestContext& ctx, const std::string& pkVar) {
    std::string in;
    for (const auto& part : utils::StringUtils::split(ctx.pathVar(pkVar), ',')) {
        if (part.empty()) continue;
        if (!in.empty()) in += ", ";
        in += pkLiteral(spec, part);
    }
    if (in.empty()) return BaseController::ok(AjaxResult::error("删除失败"));
    const std::string pk_col = std::string(spec.pkColumn());
    const std::string sql = spec.softDeleteColumn.empty()
                                ? ("DELETE FROM " + std::string(spec.table) + " WHERE " + pk_col +
                                   " IN (" + in + ")")
                                : ("UPDATE " + std::string(spec.table) + " SET " +
                                   spec.softDeleteColumn + " = '1' WHERE " + pk_col + " IN (" + in + ")");
    long long affected = 0;
    if (!Db::instance().execute(sql, &affected)) {
        return BaseController::ok(AjaxResult::error("删除失败"));
    }
    return BaseController::ok(BaseController::toAjax(affected));
}

} // namespace

void registerListVariant(Router& router, const std::string& path, const Spec& spec, ListKind kind,
                         const char* perm) {
    auto sp = std::make_shared<Spec>(spec);
    auto b = router.get(path, [sp, kind](RequestContext& ctx) -> cm::http::ApiResponse {
        Json query = bindQuery(*sp, ctx);
        if (sp->hooks.beforeQuery) sp->hooks.beforeQuery(ctx, query);
        const std::string where = buildWhere(*sp, query);
        const auto page = ctx.pageRequest();
        const std::string order = orderSqlOf(*sp, page);
        if (kind == ListKind::Paged && page.enabled) {
            auto pr = cm::db::queryPage("SELECT COUNT(1) " + fromClause(*sp) + " " + where,
                                        selectSql(*sp, where, order), page);
            return BaseController::ok(BaseController::dataTable(fetchRows(*sp, pr.rows), pr.total));
        }
        cm::db::Result res;
        Json arr = Json::array();
        if (Db::instance().query(selectSql(*sp, where, order), res)) arr = fetchRows(*sp, res);
        if (kind == ListKind::Counted)
            return BaseController::ok(BaseController::dataTable(arr, static_cast<long long>(arr.size())));
        // Plain：对应 Java 的 return AjaxResult.success(list)
        return BaseController::ok(AjaxResult::success(arr));
    });
    if (perm) b.permi(perm);
}

void registerCrud(Router& router, const std::string& base, const Spec& spec, const Perms& perms,
                  const std::string& pkVar) {
    auto sp = std::make_shared<Spec>(spec);
    const std::string pk = pkVar;

    auto list = router.get(base + "/list", [sp](RequestContext& ctx) { return runList(*sp, ctx); });
    if (perms.list) list.permi(perms.list);

    auto exp = router.get(base + "/export", [sp](RequestContext& ctx) { return runExport(*sp, ctx); });
    if (perms.exportList) exp.permi(perms.exportList);

    auto info = router.get(base + "/{" + pk + "}",
                           [sp, pk](RequestContext& ctx) { return runGetInfo(*sp, ctx, pk); });
    if (perms.query) info.permi(perms.query);

    auto add = router.post(base, [sp](RequestContext& ctx) { return runAdd(*sp, ctx); });
    if (perms.add) add.permi(perms.add);

    auto edit = router.put(base, [sp](RequestContext& ctx) { return runEdit(*sp, ctx); });
    if (perms.edit) edit.permi(perms.edit);

    auto del = router.del(base + "/{" + pk + "}",
                          [sp, pk](RequestContext& ctx) { return runRemove(*sp, ctx, pk); });
    if (perms.remove) del.permi(perms.remove);
}

void registerReadOnly(Router& router, const std::string& base, const Spec& spec, const Perms& perms,
                      const std::string& pkVar) {
    auto sp = std::make_shared<Spec>(spec);
    const std::string pk = pkVar;

    auto list = router.get(base + "/list", [sp](RequestContext& ctx) { return runList(*sp, ctx); });
    if (perms.list) list.permi(perms.list);

    auto exp = router.get(base + "/export", [sp](RequestContext& ctx) { return runExport(*sp, ctx); });
    if (perms.exportList) exp.permi(perms.exportList);

    auto info = router.get(base + "/{" + pk + "}",
                           [sp, pk](RequestContext& ctx) { return runGetInfo(*sp, ctx, pk); });
    if (perms.query) info.permi(perms.query);
}

std::string selectSqlOf(const Spec& spec, const std::string& where, const std::string& order) {
    return selectSql(spec, where, order);
}

Json fetchRowsOf(const Spec& spec, const cm::db::Result& res) { return fetchRows(spec, res); }

std::string fromClauseOf(const Spec& spec) { return fromClause(spec); }

std::string fastJson2CachedArray(const Spec& spec, const std::vector<cm::db::Row>& rows,

                                 const std::string& elemType) {
    // fastjson2 在写之前把字段按名字排序，所以这里的顺序与 spec.fields / SELECT 顺序无关
    std::vector<const Field*> ordered;
    for (const auto& f : spec.fields) {
        if (f.column == nullptr || !f.inVo) continue;   // 非列属性 / Vo 没投影 ⇒ Java 里是 null
        ordered.push_back(&f);
    }
    std::sort(ordered.begin(), ordered.end(), [](const Field* a, const Field* b) {
        return std::string(a->json) < std::string(b->json);
    });

    std::string out = "[";
    for (size_t r = 0; r < rows.size(); ++r) {
        if (r) out += ",";
        out += "{\"@type\":" + Json(elemType).dump();
        for (const Field* f : ordered) {
            auto v = rows[r].get(f->column);
            if (!v) continue;                            // null 整个键都不写（fastjson2 默认丢 null）
            std::string raw;
            switch (f->fmt) {
                case Fmt::Int:
                    raw = *v;                            // Integer 不带后缀
                    break;
                case Fmt::Long:
                    raw = *v + "L";                      // Long 写出来带 L，不是合法 JSON
                    break;
                case Fmt::Bool:
                    raw = (*v == "1" || *v == "true") ? "true" : "false";
                    break;
                case Fmt::Double:
                    raw = *v;   // BigDecimal 保持 DB 标度：0.00 不会塌成 0
                    break;
                case Fmt::DateYmd:
                case Fmt::DateYmdHms:
                case Fmt::DateIso:
                case Fmt::DateTimeIso: {
                    // 缓存走的是 fastjson2 的默认日期格式（带时分秒），不是 @JsonFormat
                    auto ms = utils::DateUtils::parseDbDateTime(*v);
                    raw = ms ? Json(utils::DateUtils::formatMillis(
                                     *ms, "yyyy-MM-dd HH:mm:ss")).dump()
                             : Json(*v).dump();
                    break;
                }
                case Fmt::Str:
                default:
                    raw = Json(*v).dump();
                    break;
            }
            if (raw.empty()) raw = *v;   // 数值列的原文就是字面量
            out += "," + Json(std::string(f->json)).dump() + ":" + raw;
        }
        out += "}";
    }
    out += "]";
    return out;
}

} // namespace cm::web::crud
