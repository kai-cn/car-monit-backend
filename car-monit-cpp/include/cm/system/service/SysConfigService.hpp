#pragma once
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>
#include "cm/system/domain/SysConfig.hpp"

namespace cm::system::service {

class SysConfigService {
public:
    /** 对应 startPage() + selectConfigList + getDataTable：rows 与 total 共用同一条 SQL */
    static std::pair<std::vector<cm::domain::SysConfig>, long long> selectConfigListEntityPage(const cm::domain::SysConfig& config,
            const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysConfig> selectConfigList(const cm::domain::SysConfig& config);
    static std::optional<cm::domain::SysConfig> selectConfigById(long long configId);
    static std::string selectConfigByKey(const std::string& configKey);
    static std::string checkConfigKeyUnique(const cm::domain::SysConfig& config);
    static long long insertConfig(cm::domain::SysConfig& config);
    static long long updateConfig(cm::domain::SysConfig& config);
    static long long deleteConfigByIds(const std::vector<long long>& configIds);
    static void clearCache();
};

} // namespace cm::system::service
