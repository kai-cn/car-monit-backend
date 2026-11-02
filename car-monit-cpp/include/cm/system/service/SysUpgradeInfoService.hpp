#pragma once
#include <optional>
#include <string>
#include <vector>
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/system/domain/SysUpgradeInfo.hpp"

namespace cm::system::service {

class SysUpgradeInfoService {
public:
    static std::vector<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoList(const cm::domain::SysUpgradeInfo& info);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoById(const std::string& id);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoNewest(const cm::domain::SysUpgradeInfo& info);
    static cm::core::domain::AjaxResult saveSysUpgradeInfo(cm::domain::SysUpgradeInfo& info);
    static cm::core::domain::AjaxResult deleteSysUpgradeInfoByIds(const std::vector<std::string>& ids);
};

} // namespace cm::system::service
