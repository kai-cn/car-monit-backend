// 对应 Java: com.ruoyi.system.mapper.SysConfigMapper
// SQL 与 ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml 保持一致。
#include "cm/system/mapper/SysConfigMapper.hpp"

#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

namespace {

constexpr const char* kSelectConfigVo =
    "select config_id, config_name, config_key, config_value, config_type,"
    " create_by, create_time, update_by, update_time, remark"
    " from sys_config";

std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}

} // namespace

cm::domain::SysConfig SysConfigMapper::mapConfig(const cm::db::Row& row) {
    cm::domain::SysConfig c;
    c.configId = row.optI64("config_id");
    c.configName = row.get("config_name");
    c.configKey = row.get("config_key");
    c.configValue = row.get("config_value");
    c.configType = row.get("config_type");
    c.createBy = row.get("create_by");
    c.createTime = parseDbDate(row.get("create_time"));
    c.updateBy = row.get("update_by");
    c.updateTime = parseDbDate(row.get("update_time"));
    c.remark = row.get("remark");
    return c;
}

std::string SysConfigMapper::selectConfigListSql(const cm::domain::SysConfig& config) {
    std::string sql = std::string(kSelectConfigVo) + " where 1=1";
    if (config.configName && !config.configName->empty()) {
        sql += " AND config_name like " + cm::db::bind("%" + *config.configName + "%");
    }
    if (config.configType && !config.configType->empty()) {
        sql += " AND config_type = " + cm::db::bind(*config.configType);
    }
    if (config.configKey && !config.configKey->empty()) {
        sql += " AND config_key like " + cm::db::bind("%" + *config.configKey + "%");
    }
    // params.beginTime / endTime support
    if (config.params.contains("beginTime") && config.params["beginTime"].is_string()) {
        std::string bt = config.params["beginTime"].get<std::string>();
        if (!bt.empty()) {
            sql += " AND date_format(create_time,'%y%m%d') >= date_format(" + cm::db::bind(bt) + ",'%y%m%d')";
        }
    }
    if (config.params.contains("endTime") && config.params["endTime"].is_string()) {
        std::string et = config.params["endTime"].get<std::string>();
        if (!et.empty()) {
            sql += " AND date_format(create_time,'%y%m%d') <= date_format(" + cm::db::bind(et) + ",'%y%m%d')";
        }
    }
    return sql;
}

std::pair<std::vector<cm::domain::SysConfig>, long long> SysConfigMapper::selectConfigListEntityPage(const cm::domain::SysConfig& config,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectConfigListSql(config);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysConfig> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapConfig(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysConfig> SysConfigMapper::selectConfigList(const cm::domain::SysConfig& config) {
    const std::string sql = selectConfigListSql(config);
    cm::db::Result res;
    std::vector<cm::domain::SysConfig> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) {
        list.push_back(mapConfig(row));
    }
    return list;
}

std::optional<cm::domain::SysConfig> SysConfigMapper::selectConfig(const cm::domain::SysConfig& config) {
    std::string sql = std::string(kSelectConfigVo) + " where 1=1";
    if (config.configId) {
        sql += " and config_id = " + cm::db::bind(*config.configId);
    }
    if (config.configKey && !config.configKey->empty()) {
        sql += " and config_key = " + cm::db::bind(*config.configKey);
    }
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapConfig(res.rows.front());
}

std::optional<cm::domain::SysConfig> SysConfigMapper::selectConfigById(long long configId) {
    cm::domain::SysConfig c;
    c.configId = configId;
    return selectConfig(c);
}

std::optional<cm::domain::SysConfig> SysConfigMapper::checkConfigKeyUnique(const std::string& configKey) {
    std::string sql = std::string(kSelectConfigVo) + " where config_key = " +
                      cm::db::bind(configKey) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapConfig(res.rows.front());
}

long long SysConfigMapper::insertConfig(const cm::domain::SysConfig& config) {
    std::string cols = "create_time";
    std::string vals = "sysdate()";
    if (config.configName && !config.configName->empty()) {
        cols += ", config_name";
        vals += ", " + cm::db::bind(*config.configName);
    }
    if (config.configKey && !config.configKey->empty()) {
        cols += ", config_key";
        vals += ", " + cm::db::bind(*config.configKey);
    }
    if (config.configValue && !config.configValue->empty()) {
        cols += ", config_value";
        vals += ", " + cm::db::bind(*config.configValue);
    }
    if (config.configType && !config.configType->empty()) {
        cols += ", config_type";
        vals += ", " + cm::db::bind(*config.configType);
    }
    if (config.createBy && !config.createBy->empty()) {
        cols += ", create_by";
        vals += ", " + cm::db::bind(*config.createBy);
    }
    if (config.remark && !config.remark->empty()) {
        cols += ", remark";
        vals += ", " + cm::db::bind(*config.remark);
    }
    std::string sql = "insert into sys_config (" + cols + ") values (" + vals + ")";
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysConfigMapper::updateConfig(const cm::domain::SysConfig& config) {
    std::string sql = "update sys_config set";
    bool first = true;
    auto append = [&](const std::string& clause) {
        if (!first) sql += ",";
        sql += " " + clause;
        first = false;
    };
    if (config.configName && !config.configName->empty()) {
        append("config_name = " + cm::db::bind(*config.configName));
    }
    if (config.configKey && !config.configKey->empty()) {
        append("config_key = " + cm::db::bind(*config.configKey));
    }
    if (config.configValue && !config.configValue->empty()) {
        append("config_value = " + cm::db::bind(*config.configValue));
    }
    if (config.configType && !config.configType->empty()) {
        append("config_type = " + cm::db::bind(*config.configType));
    }
    if (config.updateBy && !config.updateBy->empty()) {
        append("update_by = " + cm::db::bind(*config.updateBy));
    }
    if (config.remark) {
        append("remark = " + cm::db::bind(*config.remark));
    }
    append("update_time = sysdate()");
    sql += " where config_id = " + cm::db::bind(config.configId.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysConfigMapper::deleteConfigById(long long configId) {
    std::string sql = "delete from sys_config where config_id = " + cm::db::bind(configId);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysConfigMapper::deleteConfigByIds(const std::vector<long long>& configIds) {
    if (configIds.empty()) return 0;
    std::string sql = "delete from sys_config where config_id in " +
                      cm::db::bindIn(configIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
