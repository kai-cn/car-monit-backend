#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysConfigMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysConfig.hpp"

namespace cm::system::mapper {

class SysConfigMapper {
public:
    static std::vector<cm::domain::SysConfig> selectConfigList(const cm::domain::SysConfig& config);
    static std::optional<cm::domain::SysConfig> selectConfig(const cm::domain::SysConfig& config);
    static std::optional<cm::domain::SysConfig> selectConfigById(long long configId);
    static std::optional<cm::domain::SysConfig> checkConfigKeyUnique(const std::string& configKey);
    static long long insertConfig(const cm::domain::SysConfig& config);
    static long long updateConfig(const cm::domain::SysConfig& config);
    static long long deleteConfigById(long long configId);
    static long long deleteConfigByIds(const std::vector<long long>& configIds);

    static cm::domain::SysConfig mapConfig(const cm::db::Row& row);
};

} // namespace cm::system::mapper
