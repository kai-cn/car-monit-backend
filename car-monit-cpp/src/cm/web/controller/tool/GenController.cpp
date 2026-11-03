// 对应 Java: com.ruoyi.generator.controller.GenController（DB 侧 8 条）
//
// 剩下 4 条（preview / download / genCode / batchGenCode）依赖 28 份 Velocity 模板与 zip 打包，
// C++ 侧没有模板引擎，见 COMPATIBILITY.md 与 PORTING_REPORT.md §2；未注册的接口按 404 处理，
// 不会返回假数据。
//
// JSON 形态说明（都是照源码抄，不是"看着合理就行"）：
//   * GenTable / GenTableColumn 继承 BaseEntity，Jackson 先输出父类字段再按声明序输出自有字段；
//     BaseEntity 的 searchValue 是 @JsonIgnore、params 是懒加载空 Map + @JsonInclude(NON_EMPTY)，
//     所以两个都不出现。
//   * 两个实体还有一批"只有 getter 没有字段"的派生属性（isSub/isTree/isCrud、
//     capJavaField/pk/increment/...），Jackson 会把它们排在所有字段之后。
//   * selectGenTableById / selectGenTableByName / selectGenTableAll 与列表 LEFT JOIN，
//     resultMap 里只有 <id property="tableId">、没有 <collection>，所以 MyBatis 会按 table_id
//     把多行**折叠成一个对象**，列字段取第一行 —— 这里同样只取第一行。
#include "cm/web/controller/tool/GenController.hpp"

#include <algorithm>
#include <cctype>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/page/TableDataInfo.hpp"
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::StringUtils;

enum Kind { kStr = 0, kNum = 1, kDate = 2, kNone = 3 };

struct Col {
    const char* json;
    const char* column;  // nullptr = 结果集里没有这一列（恒为 null）
    Kind kind;
};

Json fieldJson(const Col& c, const cm::db::Row& row) {
    if (c.column == nullptr) return Json(nullptr);
    auto v = row.get(c.column);
    if (!v || v->empty()) return Json(nullptr);
    switch (c.kind) {
        case kNum:
            return Json(row.i64(c.column));
        case kDate: {
            auto ms = cm::utils::DateUtils::parseDbDateTime(*v);
            return ms ? Json(cm::utils::DateUtils::formatJsonDate(*ms)) : Json(*v);
        }
        default:
            return Json(*v);
    }
}

bool flag1(const std::string& v) { return v == "1"; }

std::string capitalize(const std::string& s) {
    if (s.empty()) return s;
    std::string out = s;
    out[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(out[0])));
    return out;
}

bool equalsAnyIgnoreCase(const std::string& v, const std::vector<std::string>& set) {
    return std::find(set.begin(), set.end(), StringUtils::toLower(v)) != set.end();
}

/** 逗号分隔的主键串 -> 数值列表（Java 的 @PathVariable Long[]） */
std::vector<long long> splitIds(const std::string& raw) {
    std::vector<long long> out;
    for (const auto& part : StringUtils::split(raw, ',')) {
        const std::string t = StringUtils::trim(part);
        if (t.empty()) continue;
        out.push_back(std::atoll(t.c_str()));
    }
    return out;
}

/** BaseEntity 的可见字段（searchValue/params 不出现在响应里） */
const std::vector<Col>& baseCols() {
    static const std::vector<Col> v = {
        {"createBy", "create_by", kStr},
        {"createTime", "create_time", kDate},
        {"updateBy", "update_by", kStr},
        {"updateTime", "update_time", kDate},
        {"remark", "remark", kStr},
    };
    return v;
}

/** GenTable 自有字段（声明序） */
const std::vector<Col>& genTableOwnCols() {
    static const std::vector<Col> v = {
        {"tableId", "table_id", kNum},
        {"tableName", "table_name", kStr},
        {"tableComment", "table_comment", kStr},
        {"subTableName", "sub_table_name", kStr},
        {"subTableFkName", "sub_table_fk_name", kStr},
        {"className", "class_name", kStr},
        {"tplCategory", "tpl_category", kStr},
        {"packageName", "package_name", kStr},
        {"moduleName", "module_name", kStr},
        {"businessName", "business_name", kStr},
        {"functionName", "function_name", kStr},
        {"functionAuthor", "function_author", kStr},
        {"genType", "gen_type", kStr},
        {"genPath", "gen_path", kStr},
        {"pkColumn", nullptr, kNone},
        {"subTable", nullptr, kNone},
        {"columns", nullptr, kNone},
        {"dictionaryInfoList", nullptr, kNone},
        {"dictionaryInfoString", "dictionary_info_string", kStr},
        {"options", "options", kStr},
        {"treeCode", "tree_code", kStr},
        {"treeParentCode", "tree_parent_code", kStr},
        {"treeName", "tree_name", kStr},
        {"parentMenuId", "parent_menu_id", kStr},
        {"parentMenuName", "parent_menu_name", kStr},
        {"dictionaryListKeySuffix", "dictionary_list_key_suffix", kStr},
        {"uploadInfo", nullptr, kNone},
        {"richTextInfo", nullptr, kNone},
        {"columnDialogInfo", nullptr, kNone},
        {"filterColumnList", nullptr, kNone},
    };
    return v;
}

Json genTableJson(const cm::db::Row& row) {
    Json j = Json::object();
    for (const auto& c : baseCols()) j[c.json] = fieldJson(c, row);
    for (const auto& c : genTableOwnCols()) j[c.json] = fieldJson(c, row);
    // 派生属性（只有 getter）排在字段之后，按源码里的方法声明顺序
    const std::string tpl = row.str("tpl_category");
    j["sub"] = Json(tpl == "sub");
    j["tree"] = Json(tpl == "tree");
    j["crud"] = Json(tpl == "crud");
    return j;
}

/** GenTableColumn 自有字段（声明序） */
const std::vector<Col>& genColumnOwnCols() {
    static const std::vector<Col> v = {
        {"columnId", "column_id", kNum},
        {"tableId", "table_id", kNum},
        {"columnName", "column_name", kStr},
        {"columnComment", "column_comment", kStr},
        {"columnType", "column_type", kStr},
        {"javaType", "java_type", kStr},
        {"javaField", "java_field", kStr},
        {"isPk", "is_pk", kStr},
        {"isIncrement", "is_increment", kStr},
        {"isRequired", "is_required", kStr},
        {"isInsert", "is_insert", kStr},
        {"isEdit", "is_edit", kStr},
        {"isList", "is_list", kStr},
        {"isQuery", "is_query", kStr},
        {"queryType", "query_type", kStr},
        {"htmlType", "html_type", kStr},
        {"dictType", "dict_type", kStr},
        {"dictTypeCamelCase", "dict_type_camel_case", kStr},
        {"sort", "sort", kNum},
        {"generateLinkTableFlag", "generate_link_table_flag", kStr},
        {"linkTableId", "link_table_id", kNum},
        {"linkTable", nullptr, kNone},
        {"singleSelection", "single_selection", kStr},
        {"multipleSelections", "multiple_selections", kStr},
        {"dialogSearchColumnIds", "dialog_search_column_ids", kStr},
        {"dialogListColumnIds", "dialog_list_column_ids", kStr},
        {"dialogSearchColumnList", nullptr, kNone},
        {"dialogShowColumnList", nullptr, kNone},
        {"dialogSearchColumnNames", "dialog_search_column_names", kStr},
        {"dialogListColumnNames", "dialog_list_column_names", kStr},
        {"fieldMapString", "field_map_string", kStr},
        {"tableFieldList", nullptr, kNone},
        {"customFieldList", nullptr, kNone},
        {"majorLinkFieldInfo", nullptr, kNone},
    };
    return v;
}

Json genColumnJson(const cm::db::Row& row) {
    Json j = Json::object();
    for (const auto& c : baseCols()) j[c.json] = fieldJson(c, row);
    for (const auto& c : genColumnOwnCols()) j[c.json] = fieldJson(c, row);
    // 只有 getter 的派生属性，按方法声明顺序：capJavaField, pk, increment, required,
    // insert, edit, list, query, superColumn, usableColumn
    const std::string javaField = row.str("java_field");
    j["capJavaField"] = Json(javaField.empty() ? std::string() : capitalize(javaField));
    j["pk"] = Json(flag1(row.str("is_pk")));
    j["increment"] = Json(flag1(row.str("is_increment")));
    j["required"] = Json(flag1(row.str("is_required")));
    j["insert"] = Json(flag1(row.str("is_insert")));
    j["edit"] = Json(flag1(row.str("is_edit")));
    j["list"] = Json(flag1(row.str("is_list")));
    j["query"] = Json(flag1(row.str("is_query")));
    static const std::vector<std::string> kSuper = {
        "createby", "createtime", "updateby", "updatetime", "remark",
        "parentname", "parentid", "ordernum", "ancestors"};
    static const std::vector<std::string> kUsable = {"parentid", "ordernum", "remark"};
    j["superColumn"] = Json(equalsAnyIgnoreCase(javaField, kSuper));
    j["usableColumn"] = Json(equalsAnyIgnoreCase(javaField, kUsable));
    return j;
}

cm::db::Result run(const std::string& sql) {
    cm::db::Result res;
    Db::instance().query(sql, res);
    return res;
}

const char* kGenTableVo =
    "select table_id, table_name, table_comment, sub_table_name, sub_table_fk_name, class_name,"
    " tpl_category, package_name, module_name, business_name, function_name, function_author,"
    " gen_type, gen_path, options, create_by, create_time, update_by, update_time, remark"
    " from gen_table";

/** selectGenTableList 的 <where>：lower(列) like lower(concat('%',?,'%')) + params 时间区间 */
std::string genTableWhere(const RequestContext& ctx) {
    std::string w = " where 1=1";
    const std::string tableName = ctx.optParam("tableName").value_or("");
    const std::string tableComment = ctx.optParam("tableComment").value_or("");
    const std::string begin = ctx.optParam("params[beginTime]").value_or("");
    const std::string end = ctx.optParam("params[endTime]").value_or("");
    if (!tableName.empty())
        w += " AND lower(table_name) like lower(concat('%', " + Db::lit(tableName) + ", '%'))";
    if (!tableComment.empty())
        w += " AND lower(table_comment) like lower(concat('%', " + Db::lit(tableComment) + ", '%'))";
    if (!begin.empty())
        w += " AND date_format(create_time,'%y%m%d') >= date_format(" + Db::lit(begin) + ", '%y%m%d')";
    if (!end.empty())
        w += " AND date_format(create_time,'%y%m%d') <= date_format(" + Db::lit(end) + ", '%y%m%d')";
    return w;
}

std::vector<Json> genTableList(const std::string& sql) {
    std::vector<Json> out;
    for (const auto& row : run(sql).rows) out.push_back(genTableJson(row));
    return out;
}

Json jsonArray(const std::vector<Json>& items) {
    Json arr = Json::array();
    for (const auto& i : items) arr.push_back(i);
    return arr;
}

/** selectGenTableColumnList 的 <where>
 *  XML 写的是 `tableId != null and tableId != ''`：OGNL 会把 '' 转成 0，
 *  所以 tableId=0 时条件不成立（Java 侧本来就不会按 0 过滤）。 */
std::string columnWhere(const Json& body) {
    std::string w = " where 1=1";
    long long tableId = -1;
    if (body.contains("tableId") && !body["tableId"].is_null()) {
        try {
            tableId = body["tableId"].is_string() ? std::stoll(body["tableId"].get<std::string>())
                                                  : body["tableId"].get<long long>();
        } catch (...) {
            tableId = -1;
        }
    }
    if (tableId > 0) w += " AND table_id = " + Db::lit(tableId);
    auto strAt = [&](const char* k) -> std::string {
        if (!body.contains(k) || !body[k].is_string()) return std::string();
        return body[k].get<std::string>();
    };
    const std::string columnName = strAt("columnName");
    const std::string javaField = strAt("javaField");
    if (!columnName.empty()) w += " AND `column_name` LIKE CONCAT('%', " + Db::lit(columnName) + ", '%%')";
    if (!javaField.empty()) w += " AND java_field LIKE CONCAT('%', " + Db::lit(javaField) + ", '%%')";
    return w;
}

const char* kGenColumnVo =
    "select field_map_string, link_table_id, single_selection, multiple_selections,"
    " dialog_search_column_ids, dialog_list_column_ids, column_id, table_id, column_name,"
    " column_comment, column_type, java_type, java_field, is_pk, is_increment, is_required,"
    " is_insert, is_edit, is_list, is_query, query_type, html_type, dict_type, sort,"
    " create_by, create_time, update_by, update_time from gen_table_column";

std::vector<Json> columnListByIds(const std::vector<std::string>& ids) {
    std::vector<Json> out;
    if (ids.empty()) return out;  // Java: CollectionUtils.isEmpty(idList) -> return null
    std::string in;
    for (const auto& id : ids) {
        if (!in.empty()) in += ", ";
        in += Db::lit(id);
    }
    auto res = run(std::string(kGenColumnVo) + " where column_id in (" + in + ") order by sort");
    for (const auto& row : res.rows) out.push_back(genColumnJson(row));
    return out;
}

std::vector<std::string> splitComma(const std::string& s) {
    // Java StringUtils.stringToList：split(",")，丢掉尾部空串
    std::vector<std::string> out;
    if (s.empty()) return out;
    size_t pos = 0;
    while (pos <= s.size()) {
        size_t comma = s.find(',', pos);
        out.push_back(s.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos));
        if (comma == std::string::npos) break;
        pos = comma + 1;
    }
    while (!out.empty() && out.back().empty()) out.pop_back();
    return out;
}

} // namespace

void registerGenController(Router& r) {
    // GET /tool/gen/list —— 代码生成业务列表（分页）
    r.get("/tool/gen/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string where = genTableWhere(ctx);
        const auto page = ctx.pageRequest();
        const std::string dataSql = std::string(kGenTableVo) + where + " ORDER BY create_time DESC";
        if (page.enabled) {
            auto pr = cm::db::queryPage(std::string("select count(0) from gen_table") + where, dataSql, page);
            std::vector<Json> rows;
            for (const auto& row : pr.rows.rows) rows.push_back(genTableJson(row));
            return BaseController::ok(BaseController::dataTable(jsonArray(rows), pr.total));
        }
        auto list = genTableList(dataSql);
        return BaseController::ok(BaseController::dataTable(jsonArray(list), static_cast<long long>(list.size())));
    }).permi("tool:gen:list");

    // GET /tool/gen/all/list —— 不分页，AjaxResult.success(list)（无 @PreAuthorize）
    r.get("/tool/gen/all/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto list = genTableList(std::string(kGenTableVo) + genTableWhere(ctx) + " ORDER BY create_time DESC");
        return BaseController::ok(AjaxResult::success(jsonArray(list)));
    });

    // GET /tool/gen/db/list —— 尚未导入的数据库表（information_schema）
    r.get("/tool/gen/db/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string sql =
            "select table_name, table_comment, create_time, update_time from information_schema.tables"
            " where table_schema = (select database())"
            " AND table_name NOT LIKE 'qrtz_%' AND table_name NOT LIKE 'gen_%'"
            " AND table_name NOT IN (select table_name from gen_table)";
        const std::string tableName = ctx.optParam("tableName").value_or("");
        const std::string tableComment = ctx.optParam("tableComment").value_or("");
        const std::string begin = ctx.optParam("params[beginTime]").value_or("");
        const std::string end = ctx.optParam("params[endTime]").value_or("");
        if (!tableName.empty())
            sql += " AND lower(table_name) like lower(concat('%', " + Db::lit(tableName) + ", '%'))";
        if (!tableComment.empty())
            sql += " AND lower(table_comment) like lower(concat('%', " + Db::lit(tableComment) + ", '%'))";
        if (!begin.empty())
            sql += " AND date_format(create_time,'%y%m%d') >= date_format(" + Db::lit(begin) + ", '%y%m%d')";
        if (!end.empty())
            sql += " AND date_format(create_time,'%y%m%d') <= date_format(" + Db::lit(end) + ", '%y%m%d')";
        const auto page = ctx.pageRequest();
        if (page.enabled) {
            auto pr = cm::db::queryPage(
                "select count(0) from information_schema.tables where table_schema = (select database())"
                " AND table_name NOT LIKE 'qrtz_%' AND table_name NOT LIKE 'gen_%'"
                " AND table_name NOT IN (select table_name from gen_table)"
                + (tableName.empty() ? std::string()
                                     : " AND lower(table_name) like lower(concat('%', " + Db::lit(tableName) + ", '%'))"),
                sql, page);
            std::vector<Json> rows;
            for (const auto& row : pr.rows.rows) rows.push_back(genTableJson(row));
            return BaseController::ok(BaseController::dataTable(jsonArray(rows), pr.total));
        }
        auto list = genTableList(sql);
        return BaseController::ok(BaseController::dataTable(jsonArray(list), static_cast<long long>(list.size())));
    }).permi("tool:gen:list");

    // GET /tool/gen/column/{talbleId} —— 表字段列表
    // ⚠️ Java 的方法签名是 columnList(Long tableId)，而路径变量写成了 {talbleId}（拼错），
    //    两边名字不一致；本机跑不到 Java 应用，无法确认 Spring 到底是取到路径变量、还是
    //    回落到 query 参数（那样 tableId 会是 null -> 空列表）。这里按"取路径变量"实现。
    //    另外这个接口 new TableDataInfo() 只 setRows/setTotal，code/msg 保持字段默认 0/null。
    r.get("/tool/gen/column/{talbleId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long tableId = std::atoll(ctx.pathVar("talbleId").c_str());
        auto res = run(std::string(kGenColumnVo) + " where table_id = " + Db::lit(tableId) + " order by sort");
        Json rows = Json::array();
        for (const auto& row : res.rows) rows.push_back(genColumnJson(row));
        // 对应 new TableDataInfo() + setRows/setTotal：框架不会填 code/msg，所以是 0 / null
        cm::core::page::TableDataInfo info;
        info.total = static_cast<long long>(res.rows.size());
        info.rows = rows;
        return cm::http::ApiResponse::json(info.toJson());
    }).permi("tool:gen:list");

    // GET /tool/gen/{talbleId} —— 表详情：info（折叠后的单行）+ rows（列）+ tables（全部表）
    r.get("/tool/gen/{talbleId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const long long tableId = std::atoll(ctx.pathVar("talbleId").c_str());
        // info：与列表 LEFT JOIN 后按 table_id 折叠，列字段取第一行
        auto res = run(
            "SELECT t.table_id, t.table_name, t.table_comment, t.sub_table_name, t.sub_table_fk_name,"
            " t.class_name, t.tpl_category, t.package_name, t.module_name, t.business_name,"
            " t.function_name, t.function_author, t.gen_type, t.gen_path, t.options, t.remark,"
            " c.column_id, c.column_name, c.column_comment, c.column_type, c.java_type, c.java_field,"
            " c.is_pk, c.is_increment, c.is_required, c.is_insert, c.is_edit, c.is_list, c.is_query,"
            " c.query_type, c.html_type, c.dict_type, c.field_map_string, c.link_table_id,"
            " c.single_selection, c.multiple_selections, c.dialog_search_column_ids,"
            " c.dialog_list_column_ids, c.sort"
            " FROM gen_table t LEFT JOIN gen_table_column c ON t.table_id = c.table_id"
            " where t.table_id = " + Db::lit(tableId) + " order by c.sort");
        Json info = res.rows.empty() ? Json(nullptr) : genTableJson(res.rows[0]);

        // tables：selectGenTableAll（同样折叠，每张表取第一行）
        auto all = run(
            "SELECT t.table_id, t.table_name, t.table_comment, t.sub_table_name, t.sub_table_fk_name,"
            " t.class_name, t.tpl_category, t.package_name, t.module_name, t.business_name,"
            " t.function_name, t.function_author, t.options, t.remark,"
            " c.column_id, c.column_name, c.column_comment, c.column_type, c.java_type, c.java_field,"
            " c.is_pk, c.is_increment, c.is_required, c.is_insert, c.is_edit, c.is_list, c.is_query,"
            " c.query_type, c.html_type, c.dict_type, c.field_map_string, c.link_table_id,"
            " c.single_selection, c.multiple_selections, c.dialog_search_column_ids,"
            " c.dialog_list_column_ids, c.sort"
            " FROM gen_table t LEFT JOIN gen_table_column c ON t.table_id = c.table_id order by c.sort");
        std::vector<Json> tables;
        std::vector<long long> seen;  // resultMap 只有 <id tableId>，MyBatis 按 table_id 折叠多行
        for (const auto& row : all.rows) {
            const long long tid = row.i64("table_id");
            if (std::find(seen.begin(), seen.end(), tid) != seen.end()) continue;
            seen.push_back(tid);
            tables.push_back(genTableJson(row));
        }

        // rows：列清单，并把 dialogXxxColumnIds 换成对应的列名串
        auto cols = run(std::string(kGenColumnVo) + " where table_id = " + Db::lit(tableId) + " order by sort");
        Json rows = Json::array();
        for (const auto& row : cols.rows) {
            Json j = genColumnJson(row);
            const std::string searchIds = row.str("dialog_search_column_ids");
            if (!searchIds.empty()) {
                std::string joined;
                for (const auto& c : columnListByIds(splitComma(searchIds))) {
                    if (!joined.empty()) joined += ",";
                    joined += cm::jstr(c, "columnName", std::string());
                }
                if (!joined.empty()) j["dialogSearchColumnNames"] = Json(joined);
            }
            const std::string listIds = row.str("dialog_list_column_ids");
            if (!listIds.empty()) {
                std::string joined;
                for (const auto& c : columnListByIds(splitComma(listIds))) {
                    if (!joined.empty()) joined += ",";
                    joined += cm::jstr(c, "columnName", std::string());
                }
                if (!joined.empty()) j["dialogListColumnNames"] = Json(joined);
            }
            rows.push_back(std::move(j));
        }

        // map = new HashMap()，键 info/rows/tables 的迭代顺序由 HashMap 桶序决定
        Json data = Json::object();
        for (const auto& k : cm::utils::javaMapOrder({"info", "rows", "tables"})) {
            data[k] = (k == "info") ? info : (k == "rows") ? rows : jsonArray(tables);
        }
        return BaseController::ok(AjaxResult::success(data));
    }).permi("tool:gen:query");

    // POST /tool/gen/getColumnList —— 分页取字段列表（无 @PreAuthorize）
    r.post("/tool/gen/getColumnList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string where = columnWhere(ctx.body());
        const std::string dataSql = std::string(kGenColumnVo) + where + " ORDER BY sort";
        const auto page = ctx.pageRequest();
        if (page.enabled) {
            auto pr = cm::db::queryPage(std::string("select count(0) from gen_table_column") + where, dataSql, page);
            Json rows = Json::array();
            for (const auto& row : pr.rows.rows) rows.push_back(genColumnJson(row));
            return BaseController::ok(BaseController::dataTable(rows, pr.total));
        }
        Json rows = Json::array();
        for (const auto& row : run(dataSql).rows) rows.push_back(genColumnJson(row));
        return BaseController::ok(BaseController::dataTable(rows, static_cast<long long>(rows.size())));
    });

    // POST /tool/gen/getAllColumnList —— 不分页（无 @PreAuthorize）
    r.post("/tool/gen/getAllColumnList", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto res = run(std::string(kGenColumnVo) + columnWhere(ctx.body()) + " ORDER BY sort");
        Json rows = Json::array();
        for (const auto& row : res.rows) rows.push_back(genColumnJson(row));
        return BaseController::ok(AjaxResult::success(rows));
    });

    // DELETE /tool/gen/{tableIds} —— 先删表再删列（都是硬删除）
    r.del("/tool/gen/{tableIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto ids = splitIds(ctx.pathVar("tableIds"));
        if (ids.empty()) return BaseController::ok(AjaxResult::success());
        std::string in;
        for (auto id : ids) {
            if (!in.empty()) in += ", ";
            in += Db::lit(id);
        }
        Db::instance().execute("delete from gen_table where table_id in (" + in + ")");
        Db::instance().execute("delete from gen_table_column where table_id in (" + in + ")");
        return BaseController::ok(AjaxResult::success());
    }).permi("tool:gen:remove");
}

} // namespace cm::web
