#pragma once
#include <optional>
#include <string>
#include <vector>
#include "cm/system/domain/SysConfig.hpp"

namespace cm::system::service {

class SysConfigService {
public:
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
