#pragma once
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/system/domain/SysUpgradeInfo.hpp"

namespace cm::system::service {

class SysUpgradeInfoService {
public:
    /** 对应 startPage() + selectSysUpgradeInfoList + getDataTable：rows 与 total 共用同一条 SQL */
    static std::pair<std::vector<cm::domain::SysUpgradeInfo>, long long> selectSysUpgradeInfoListEntityPage(const cm::domain::SysUpgradeInfo& info,
            const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoList(const cm::domain::SysUpgradeInfo& info);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoById(const std::string& id);
    static std::optional<cm::domain::SysUpgradeInfo> selectSysUpgradeInfoNewest(const cm::domain::SysUpgradeInfo& info);
    static cm::core::domain::AjaxResult saveSysUpgradeInfo(cm::domain::SysUpgradeInfo& info);
    static cm::core::domain::AjaxResult deleteSysUpgradeInfoByIds(const std::vector<std::string>& ids);
};

} // namespace cm::system::service
