// 对应 Java: SysDictTypeMapper
#include "cm/system/mapper/SysDictTypeMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {
namespace {
constexpr const char* kSelectDictTypeVo =
    "select dict_id, dict_name, dict_type, status, create_by, create_time, remark from sys_dict_type";
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
}

cm::domain::SysDictType SysDictTypeMapper::mapDictType(const cm::db::Row& row) {
    cm::domain::SysDictType d;
    d.dictId = row.optI64("dict_id");
    d.dictName = row.get("dict_name");
    d.dictType = row.get("dict_type");
    d.status = row.get("status");
    d.createBy = row.get("create_by");
    d.createTime = parseDbDate(row.get("create_time"));
    d.remark = row.get("remark");
    return d;
}

std::string SysDictTypeMapper::selectDictTypeListSql(const cm::domain::SysDictType& dt) {
    std::string sql = std::string(kSelectDictTypeVo) + " where 1=1";
    if (dt.dictName && !dt.dictName->empty())
        sql += " AND dict_name like " + cm::db::Db::lit("%" + *dt.dictName + "%");
    if (dt.status && !dt.status->empty())
        sql += " AND status = " + cm::db::Db::lit(*dt.status);
    if (dt.dictType && !dt.dictType->empty())
        sql += " AND dict_type like " + cm::db::Db::lit("%" + *dt.dictType + "%");
    if (dt.params.contains("beginTime") && dt.params["beginTime"].is_string()) {
        std::string bt = dt.params["beginTime"].get<std::string>();
        if (!bt.empty()) sql += " AND date_format(create_time,'%y%m%d') >= date_format(" + cm::db::Db::lit(bt) + ",'%y%m%d')";
    }
    if (dt.params.contains("endTime") && dt.params["endTime"].is_string()) {
        std::string et = dt.params["endTime"].get<std::string>();
        if (!et.empty()) sql += " AND date_format(create_time,'%y%m%d') <= date_format(" + cm::db::Db::lit(et) + ",'%y%m%d')";
    }
    sql += " order by create_time desc";
    return sql;
}

std::pair<std::vector<cm::domain::SysDictType>, long long> SysDictTypeMapper::selectDictTypeListEntityPage(const cm::domain::SysDictType& dt,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectDictTypeListSql(dt);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysDictType> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapDictType(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysDictType> SysDictTypeMapper::selectDictTypeList(const cm::domain::SysDictType& dt) {
    const std::string sql = selectDictTypeListSql(dt);
    cm::db::Result res;
    std::vector<cm::domain::SysDictType> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapDictType(row));
    return list;
}

std::vector<cm::domain::SysDictType> SysDictTypeMapper::selectDictTypeAll() {
    std::string sql = std::string(kSelectDictTypeVo) + " order by create_time desc";
    cm::db::Result res;
    std::vector<cm::domain::SysDictType> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapDictType(row));
    return list;
}

std::optional<cm::domain::SysDictType> SysDictTypeMapper::selectDictTypeById(long long dictId) {
    std::string sql = std::string(kSelectDictTypeVo) + " where dict_id = " + cm::db::Db::lit(dictId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDictType(res.rows.front());
}

std::optional<cm::domain::SysDictType> SysDictTypeMapper::selectDictTypeByType(const std::string& dictType) {
    std::string sql = std::string(kSelectDictTypeVo) + " where dict_type = " + cm::db::Db::lit(dictType);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDictType(res.rows.front());
}

std::optional<cm::domain::SysDictType> SysDictTypeMapper::checkDictTypeUnique(const std::string& dictType) {
    std::string sql = std::string(kSelectDictTypeVo) + " where dict_type = " + cm::db::Db::lit(dictType) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapDictType(res.rows.front());
}

long long SysDictTypeMapper::insertDictType(const cm::domain::SysDictType& dt) {
    std::string cols = "create_time";
    std::string vals = "sysdate()";
    if (dt.dictName && !dt.dictName->empty()) { cols += ", dict_name"; vals += ", " + cm::db::Db::lit(*dt.dictName); }
    if (dt.dictType && !dt.dictType->empty()) { cols += ", dict_type"; vals += ", " + cm::db::Db::lit(*dt.dictType); }
    if (dt.status) { cols += ", status"; vals += ", " + cm::db::Db::lit(*dt.status); }
    if (dt.remark && !dt.remark->empty()) { cols += ", remark"; vals += ", " + cm::db::Db::lit(*dt.remark); }
    if (dt.createBy && !dt.createBy->empty()) { cols += ", create_by"; vals += ", " + cm::db::Db::lit(*dt.createBy); }
    std::string sql = "insert into sys_dict_type (" + cols + ") values (" + vals + ")";
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictTypeMapper::updateDictType(const cm::domain::SysDictType& dt) {
    std::string sql = "update sys_dict_type set";
    bool first = true;
    auto append = [&](const std::string& c) { if (!first) sql += ","; sql += " " + c; first = false; };
    if (dt.dictName && !dt.dictName->empty()) append("dict_name = " + cm::db::Db::lit(*dt.dictName));
    if (dt.dictType && !dt.dictType->empty()) append("dict_type = " + cm::db::Db::lit(*dt.dictType));
    if (dt.status) append("status = " + cm::db::Db::lit(*dt.status));
    if (dt.remark) append("remark = " + cm::db::Db::lit(*dt.remark));
    if (dt.updateBy && !dt.updateBy->empty()) append("update_by = " + cm::db::Db::lit(*dt.updateBy));
    append("update_time = sysdate()");
    sql += " where dict_id = " + cm::db::Db::lit(dt.dictId.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictTypeMapper::deleteDictTypeById(long long dictId) {
    std::string sql = "delete from sys_dict_type where dict_id = " + cm::db::Db::lit(dictId);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysDictTypeMapper::deleteDictTypeByIds(const std::vector<long long>& dictIds) {
    if (dictIds.empty()) return 0;
    std::string sql = "delete from sys_dict_type where dict_id in " + cm::db::Db::inList(dictIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
