// 对应 Java: SysDictDataMapper
#include "cm/system/mapper/SysDictDataMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {
namespace {
constexpr const char* kSelectDictDataVo =
    "select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class,"
    " is_default, status, create_by, create_time, remark from sys_dict_data";
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
}

cm::domain::SysDictData SysDictDataMapper::mapDictData(const cm::db::Row& row) {
    cm::domain::SysDictData d;
    d.dictCode = row.optI64("dict_code");
    d.dictSort = row.optI64("dict_sort");
    d.dictLabel = row.get("dict_label");
    d.dictValue = row.get("dict_value");
    d.dictType = row.get("dict_type");
    d.cssClass = row.get("css_class");
    d.listClass = row.get("list_class");
    d.isDefault = row.get("is_default");
    d.status = row.get("status");
    d.createBy = row.get("create_by");
    d.createTime = parseDbDate(row.get("create_time"));
    d.updateBy = row.get("update_by");
    d.updateTime = parseDbDate(row.get("update_time"));
    d.remark = row.get("remark");
    return d;
}

std::string SysDictDataMapper::selectDictDataListSql(const cm::domain::SysDictData& dd) {
    std::string sql = std::string(kSelectDictDataVo) + " where 1=1";
    if (dd.dictType && !dd.dictType->empty())
        sql += " AND dict_type = " + cm::db::Db::lit(*dd.dictType);
    if (dd.dictLabel && !dd.dictLabel->empty())
        sql += " AND dict_label like " + cm::db::Db::lit("%" + *dd.dictLabel + "%");
    if (dd.status && !dd.status->empty())
        sql += " AND status = " + cm::db::Db::lit(*dd.status);
    sql += " order by dict_sort asc";
    return sql;
}

std::pair<std::vector<cm::domain::SysDictData>, long long> SysDictDataMapper::selectDictDataListEntityPage(const cm::domain::SysDictData& dd,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectDictDataListSql(dd);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysDictData> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapDictData(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysDictData> SysDictDataMapper::selectDictDataList(const cm::domain::SysDictData& dd) {
    const std::string sql = selectDictDataListSql(dd);
    cm::db::Result res;
    std::vector<cm::domain::SysDictData> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapDictData(row));
    return list;
}

std::vector<cm::domain::SysDictData> SysDictDataMapper::selectDictDataByType(const std::string& dictType) {
    std::string sql = std::string(kSelectDictDataVo) + " where status = '0' and dict_type = " +
                      cm::db::Db::lit(dictType) + " order by dict_sort asc";
    cm::db::Result res;
    std::vector<cm::domain::SysDictData> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapDictData(row));
    return list;
}

std::vector<cm::domain::SysDictData> SysDictDataMapper::selectDictDataByTypeMore(const std::string& dictTypes) {
    // Parse comma-separated dictTypes
    std::vector<std::string> types;
    std::string cur;
    for (char c : dictTypes) {
        if (c == ',') { if (!cur.empty()) { types.push_back(cur); cur.clear(); } }
        else cur += c;
    }
    if (!cur.empty()) types.push_back(cur);
    if (types.empty()) return {};
    std::string sql = std::string(kSelectDictDataVo) + " where status = '0' and dict_type in " +
                      cm::db::Db::inList(types) + " order by dict_type, dict_sort asc";
    cm::db::Result res;
    std::vector<cm::domain::SysDictData> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapDictData(row));
    return list;
}

std::optional<cm::domain::SysDictData> SysDictDataMapper::selectDictDataById(long long dictCode) {
    std::string sql = std::string(kSelectDictDataVo) + " where dict_code = " + cm::db::Db::lit(dictCode);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDictData(res.rows.front());
}

std::string SysDictDataMapper::selectDictLabel(const std::string& dictType, const std::string& dictValue) {
    std::string sql = "select dict_label from sys_dict_data where dict_type = " +
                      cm::db::Db::lit(dictType) + " and dict_value = " + cm::db::Db::lit(dictValue);
    auto v = cm::db::Db::instance().scalar(sql);
    return v.value_or("");
}

long long SysDictDataMapper::countDictDataByType(const std::string& dictType) {
    std::string sql = "select count(1) from sys_dict_data where dict_type = " + cm::db::Db::lit(dictType);
    return cm::db::Db::instance().count(sql);
}

long long SysDictDataMapper::insertDictData(const cm::domain::SysDictData& dd) {
    std::string cols = "create_time";
    std::string vals = "sysdate()";
    if (dd.dictSort) { cols += ", dict_sort"; vals += ", " + cm::db::Db::lit(*dd.dictSort); }
    if (dd.dictLabel && !dd.dictLabel->empty()) { cols += ", dict_label"; vals += ", " + cm::db::Db::lit(*dd.dictLabel); }
    if (dd.dictValue && !dd.dictValue->empty()) { cols += ", dict_value"; vals += ", " + cm::db::Db::lit(*dd.dictValue); }
    if (dd.dictType && !dd.dictType->empty()) { cols += ", dict_type"; vals += ", " + cm::db::Db::lit(*dd.dictType); }
    if (dd.cssClass && !dd.cssClass->empty()) { cols += ", css_class"; vals += ", " + cm::db::Db::lit(*dd.cssClass); }
    if (dd.listClass && !dd.listClass->empty()) { cols += ", list_class"; vals += ", " + cm::db::Db::lit(*dd.listClass); }
    if (dd.isDefault && !dd.isDefault->empty()) { cols += ", is_default"; vals += ", " + cm::db::Db::lit(*dd.isDefault); }
    if (dd.status) { cols += ", status"; vals += ", " + cm::db::Db::lit(*dd.status); }
    if (dd.remark && !dd.remark->empty()) { cols += ", remark"; vals += ", " + cm::db::Db::lit(*dd.remark); }
    if (dd.createBy && !dd.createBy->empty()) { cols += ", create_by"; vals += ", " + cm::db::Db::lit(*dd.createBy); }
    std::string sql = "insert into sys_dict_data (" + cols + ") values (" + vals + ")";
    long long affected = 0, insertId = 0;
    cm::db::Db::instance().execute(sql, &affected, &insertId);
    return affected;
}

long long SysDictDataMapper::updateDictData(const cm::domain::SysDictData& dd) {
    std::string sql = "update sys_dict_data set";
    bool first = true;
    auto append = [&](const std::string& c) { if (!first) sql += ","; sql += " " + c; first = false; };
    if (dd.dictSort) append("dict_sort = " + cm::db::Db::lit(*dd.dictSort));
    if (dd.dictLabel && !dd.dictLabel->empty()) append("dict_label = " + cm::db::Db::lit(*dd.dictLabel));
    if (dd.dictValue && !dd.dictValue->empty()) append("dict_value = " + cm::db::Db::lit(*dd.dictValue));
    if (dd.dictType && !dd.dictType->empty()) append("dict_type = " + cm::db::Db::lit(*dd.dictType));
    if (dd.cssClass) append("css_class = " + cm::db::Db::lit(*dd.cssClass));
    if (dd.listClass) append("list_class = " + cm::db::Db::lit(*dd.listClass));
    if (dd.isDefault && !dd.isDefault->empty()) append("is_default = " + cm::db::Db::lit(*dd.isDefault));
    if (dd.status) append("status = " + cm::db::Db::lit(*dd.status));
    if (dd.remark) append("remark = " + cm::db::Db::lit(*dd.remark));
    if (dd.updateBy && !dd.updateBy->empty()) append("update_by = " + cm::db::Db::lit(*dd.updateBy));
    append("update_time = sysdate()");
    sql += " where dict_code = " + cm::db::Db::lit(dd.dictCode.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictDataMapper::updateDictDataType(const std::string& oldDictType, const std::string& newDictType) {
    std::string sql = "update sys_dict_data set dict_type = " + cm::db::Db::lit(newDictType) +
                      " where dict_type = " + cm::db::Db::lit(oldDictType);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictDataMapper::deleteDictDataById(long long dictCode) {
    std::string sql = "delete from sys_dict_data where dict_code = " + cm::db::Db::lit(dictCode);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictDataMapper::deleteDictDataByIds(const std::vector<long long>& dictCodes) {
    if (dictCodes.empty()) return 0;
    std::string sql = "delete from sys_dict_data where dict_code in " + cm::db::Db::inList(dictCodes);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
