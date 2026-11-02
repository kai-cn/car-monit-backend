// 对应 Java: SysUpgradeInfoServiceImpl
#include "cm/system/service/SysUpgradeInfoService.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/system/mapper/SysUpgradeInfoMapper.hpp"

#include <chrono>

namespace cm::system::service {

std::vector<cm::domain::SysUpgradeInfo> SysUpgradeInfoService::selectSysUpgradeInfoList(const cm::domain::SysUpgradeInfo& info) {
    return cm::system::mapper::SysUpgradeInfoMapper::selectSysUpgradeInfoList(info);
}

std::optional<cm::domain::SysUpgradeInfo> SysUpgradeInfoService::selectSysUpgradeInfoById(const std::string& id) {
    return cm::system::mapper::SysUpgradeInfoMapper::selectSysUpgradeInfoById(id);
}

std::optional<cm::domain::SysUpgradeInfo> SysUpgradeInfoService::selectSysUpgradeInfoNewest(const cm::domain::SysUpgradeInfo& info) {
    return cm::system::mapper::SysUpgradeInfoMapper::selectSysUpgradeInfoNewest(info);
}

cm::core::domain::AjaxResult SysUpgradeInfoService::saveSysUpgradeInfo(cm::domain::SysUpgradeInfo& info) {
    long long userId = cm::security::SecurityUtils::getUserId();
    auto now = std::chrono::system_clock::now();
    auto nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();

    if (info.id && !info.id->empty()) {
        info.updateBy = std::to_string(userId);
        info.updateTime = nowMs;
        cm::system::mapper::SysUpgradeInfoMapper::updateSysUpgradeInfo(info);
    } else {
        info.id = cm::utils::simpleUuid();
        info.delFlag = "0";
        info.epsId = std::to_string(cm::security::SecurityUtils::getEpsId());
        info.tenantId = cm::security::SecurityUtils::getTenantId();
        info.createBy = std::to_string(userId);
        info.createTime = nowMs;
        info.updateBy = std::to_string(userId);
        info.updateTime = nowMs;
        cm::system::mapper::SysUpgradeInfoMapper::insertSysUpgradeInfo(info);
    }
    return cm::core::domain::AjaxResult::success("操作成功！", Json(*info.id));
}

cm::core::domain::AjaxResult SysUpgradeInfoService::deleteSysUpgradeInfoByIds(const std::vector<std::string>& ids) {
    long long count = cm::system::mapper::SysUpgradeInfoMapper::deleteSysUpgradeInfoByIds(ids);
    return cm::core::domain::AjaxResult::success(Json(count));
}

} // namespace cm::system::service
