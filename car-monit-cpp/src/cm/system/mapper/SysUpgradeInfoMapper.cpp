// 对应 Java: SysUpgradeInfoMapper
#include "cm/system/mapper/SysUpgradeInfoMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {
namespace {
constexpr const char* kSelectVo =
    "select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by,"
    " t.create_time, t.update_by, t.update_time, t.tenant_id from sys_upgrade_info t";
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
}

cm::domain::SysUpgradeInfo SysUpgradeInfoMapper::mapSysUpgradeInfo(const cm::db::Row& row) {
    cm::domain::SysUpgradeInfo info;
    info.id = row.get("id");
    info.ver = row.get("ver");
    info.info = row.get("info");
    info.backCol1 = row.get("back_col1");
    info.epsId = row.get("eps_id");
    info.delFlag = row.get("del_flag");
    info.createBy = row.get("create_by");
    info.createTime = parseDbDate(row.get("create_time"));
    info.updateBy = row.get("update_by");
    info.updateTime = parseDbDate(row.get("update_time"));
    info.tenantId = row.optI64("tenant_id");
    return info;
}

std::string SysUpgradeInfoMapper::selectSysUpgradeInfoListSql(const cm::domain::SysUpgradeInfo& q) {
    std::string sql = std::string(kSelectVo) + " where t.del_flag = '0'";
    if (q.id && !q.id->empty()) sql += " and t.id = " + cm::db::bind(*q.id);
    if (q.ver && !q.ver->empty()) sql += " and t.ver = " + cm::db::bind(*q.ver);
    if (q.info && !q.info->empty()) sql += " and t.info = " + cm::db::bind(*q.info);
    if (q.backCol1 && !q.backCol1->empty()) sql += " and t.back_col1 = " + cm::db::bind(*q.backCol1);
    if (q.epsId && !q.epsId->empty()) sql += " and t.eps_id = " + cm::db::bind(*q.epsId);
    if (q.tenantId) sql += " and t.tenant_id = " + cm::db::bind(*q.tenantId);
    if (q.createBy && !q.createBy->empty()) sql += " and t.create_by = " + cm::db::bind(*q.createBy);
    sql += " order by t.create_time desc, t.id";
    return sql;
}

std::pair<std::vector<cm::domain::SysUpgradeInfo>, long long> SysUpgradeInfoMapper::selectSysUpgradeInfoListEntityPage(const cm::domain::SysUpgradeInfo& q,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectSysUpgradeInfoListSql(q);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysUpgradeInfo> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapSysUpgradeInfo(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysUpgradeInfo> SysUpgradeInfoMapper::selectSysUpgradeInfoList(const cm::domain::SysUpgradeInfo& q) {
    const std::string sql = selectSysUpgradeInfoListSql(q);
    cm::db::Result res;
    std::vector<cm::domain::SysUpgradeInfo> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapSysUpgradeInfo(row));
    return list;
}

std::optional<cm::domain::SysUpgradeInfo> SysUpgradeInfoMapper::selectSysUpgradeInfoById(const std::string& id) {
    std::string sql = std::string(kSelectVo) + " where t.id = " + cm::db::bind(id);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapSysUpgradeInfo(res.rows.front());
}

std::optional<cm::domain::SysUpgradeInfo> SysUpgradeInfoMapper::selectSysUpgradeInfoNewest(const cm::domain::SysUpgradeInfo&) {
    std::string sql = std::string(kSelectVo) + " where t.del_flag = '0' and t.back_col1 = '1'"
                      " ORDER BY t.UPDATE_TIME desc LIMIT 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapSysUpgradeInfo(res.rows.front());
}

long long SysUpgradeInfoMapper::insertSysUpgradeInfo(const cm::domain::SysUpgradeInfo& info) {
    std::string cols, vals;
    auto add = [&](const std::string& c, const std::string& v) {
        if (!cols.empty()) { cols += ", "; vals += ", "; }
        cols += c; vals += v;
    };
    if (info.id && !info.id->empty()) add("id", cm::db::bind(*info.id));
    if (info.ver) add("ver", cm::db::bind(*info.ver));
    if (info.info) add("info", cm::db::bind(*info.info));
    if (info.backCol1) add("back_col1", cm::db::bind(*info.backCol1));
    if (info.epsId) add("eps_id", cm::db::bind(*info.epsId));
    if (info.delFlag) add("del_flag", cm::db::bind(*info.delFlag));
    if (info.createBy) add("create_by", cm::db::bind(*info.createBy));
    if (info.createTime) add("create_time", "from_unixtime(" + std::to_string(*info.createTime / 1000) + ")");
    if (info.updateBy) add("update_by", cm::db::bind(*info.updateBy));
    if (info.updateTime) add("update_time", "from_unixtime(" + std::to_string(*info.updateTime / 1000) + ")");
    if (info.tenantId) add("tenant_id", cm::db::bind(*info.tenantId));
    std::string sql = "insert into sys_upgrade_info (" + cols + ") values (" + vals + ")";
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysUpgradeInfoMapper::updateSysUpgradeInfo(const cm::domain::SysUpgradeInfo& info) {
    std::string sql = "update sys_upgrade_info set";
    bool first = true;
    auto append = [&](const std::string& c) { if (!first) sql += ","; sql += " " + c; first = false; };
    if (info.ver) append("ver = " + cm::db::bind(*info.ver));
    if (info.info) append("info = " + cm::db::bind(*info.info));
    if (info.backCol1) append("back_col1 = " + cm::db::bind(*info.backCol1));
    if (info.epsId) append("eps_id = " + cm::db::bind(*info.epsId));
    if (info.delFlag) append("del_flag = " + cm::db::bind(*info.delFlag));
    if (info.createBy) append("create_by = " + cm::db::bind(*info.createBy));
    if (info.createTime) append("create_time = from_unixtime(" + std::to_string(*info.createTime / 1000) + ")");
    if (info.updateBy) append("update_by = " + cm::db::bind(*info.updateBy));
    if (info.updateTime) append("update_time = from_unixtime(" + std::to_string(*info.updateTime / 1000) + ")");
    if (info.tenantId) append("tenant_id = " + cm::db::bind(*info.tenantId));
    sql += " where id = " + cm::db::bind(info.id.value_or(""));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysUpgradeInfoMapper::deleteSysUpgradeInfoById(const std::string& id) {
    std::string sql = "update sys_upgrade_info set del_flag = '1' where id = " + cm::db::bind(id);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysUpgradeInfoMapper::deleteSysUpgradeInfoByIds(const std::vector<std::string>& ids) {
    if (ids.empty()) return 0;
    std::string sql = "update sys_upgrade_info set del_flag = '1' where id in " + cm::db::bindIn(ids);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
