// 对应 Java: SysConfigServiceImpl
#include "cm/system/service/SysConfigService.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/system/mapper/SysConfigMapper.hpp"

namespace cm::system::service {

using cm::constant::Constants;
using cm::constant::UserConstants;

std::vector<cm::domain::SysConfig> SysConfigService::selectConfigList(const cm::domain::SysConfig& config) {
    return cm::system::mapper::SysConfigMapper::selectConfigList(config);
}

std::optional<cm::domain::SysConfig> SysConfigService::selectConfigById(long long configId) {
    return cm::system::mapper::SysConfigMapper::selectConfigById(configId);
}

std::string SysConfigService::selectConfigByKey(const std::string& configKey) {
    auto& redis = cm::redis::RedisCache::instance();
    auto cached = redis.get(std::string(Constants::SYS_CONFIG_KEY) + configKey);
    if (cached && !cached->empty()) return *cached;

    cm::domain::SysConfig query;
    query.configKey = configKey;
    auto retConfig = cm::system::mapper::SysConfigMapper::selectConfig(query);
    if (retConfig && retConfig->configValue) {
        redis.set(std::string(Constants::SYS_CONFIG_KEY) + configKey, *retConfig->configValue);
        return *retConfig->configValue;
    }
    return "";
}

std::string SysConfigService::checkConfigKeyUnique(const cm::domain::SysConfig& config) {
    long long configId = config.configId.value_or(-1);
    auto info = cm::system::mapper::SysConfigMapper::checkConfigKeyUnique(config.configKey.value_or(""));
    if (info && info->configId.value_or(-1) != configId) {
        return UserConstants::NOT_UNIQUE_OLD;
    }
    return UserConstants::UNIQUE_OLD;
}

long long SysConfigService::insertConfig(cm::domain::SysConfig& config) {
    long long row = cm::system::mapper::SysConfigMapper::insertConfig(config);
    if (row > 0 && config.configKey && config.configValue) {
        cm::redis::RedisCache::instance().set(
            std::string(Constants::SYS_CONFIG_KEY) + *config.configKey, *config.configValue);
    }
    return row;
}

long long SysConfigService::updateConfig(cm::domain::SysConfig& config) {
    long long row = cm::system::mapper::SysConfigMapper::updateConfig(config);
    if (row > 0 && config.configKey && config.configValue) {
        cm::redis::RedisCache::instance().set(
            std::string(Constants::SYS_CONFIG_KEY) + *config.configKey, *config.configValue);
    }
    return row;
}

long long SysConfigService::deleteConfigByIds(const std::vector<long long>& configIds) {
    for (long long configId : configIds) {
        auto config = selectConfigById(configId);
        if (config && config->configType && *config->configType == UserConstants::YES) {
            throw cm::exception::CustomException(
                std::string("内置参数【") + config->configKey.value_or("") + "】不能删除 ");
        }
    }
    long long count = cm::system::mapper::SysConfigMapper::deleteConfigByIds(configIds);
    if (count > 0) {
        auto keys = cm::redis::RedisCache::instance().keys(std::string(Constants::SYS_CONFIG_KEY) + "*");
        if (!keys.empty()) cm::redis::RedisCache::instance().client().del(keys);
    }
    return count;
}

void SysConfigService::clearCache() {
    auto keys = cm::redis::RedisCache::instance().keys(std::string(Constants::SYS_CONFIG_KEY) + "*");
    if (!keys.empty()) cm::redis::RedisCache::instance().client().del(keys);
}

} // namespace cm::system::service
