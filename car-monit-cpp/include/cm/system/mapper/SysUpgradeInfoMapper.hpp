#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysUpgradeInfoMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysUpgradeInfo.hpp"

namespace cm::system::mapper {

class SysUpgradeInfoMapper {
public:
    static std::vector<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoList(const cm::domain::SysUpgradeInfo& info);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoById(const std::string& id);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoNewest(const cm::domain::SysUpgradeInfo& info);
    static long long insertSysUpgradeInfo(const cm::domain::SysUpgradeInfo& info);
    static long long updateSysUpgradeInfo(const cm::domain::SysUpgradeInfo& info);
    static long long deleteSysUpgradeInfoById(const std::string& id);
    static long long deleteSysUpgradeInfoByIds(const std::vector<std::string>& ids);

    static cm::domain::SysUpgradeInfo mapSysUpgradeInfo(const cm::db::Row& row);
};

} // namespace cm::system::mapper
