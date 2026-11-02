// 对应 Java: SysFileServiceImpl (partial - CRUD only, file upload/download not ported)
#include "cm/system/service/SysFileService.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/system/mapper/SysFileMapper.hpp"

#include <chrono>

namespace cm::system::service {

std::vector<cm::domain::SysFile> SysFileService::selectSysFileList(const cm::domain::SysFile& file) {
    return cm::system::mapper::SysFileMapper::selectSysFileList(file);
}

std::optional<cm::domain::SysFile> SysFileService::selectSysFileById(long long id) {
    return cm::system::mapper::SysFileMapper::selectSysFileById(id);
}

std::vector<cm::domain::SysFile> SysFileService::selectSysFileByIds(const std::string& ids) {
    return cm::system::mapper::SysFileMapper::selectSysFileByIds(ids);
}

cm::core::domain::AjaxResult SysFileService::deleteSysFileById(long long id) {
    long long count = cm::system::mapper::SysFileMapper::deleteSysFileById(id);
    return cm::core::domain::AjaxResult::success(Json(count));
}

cm::core::domain::AjaxResult SysFileService::deleteSysFileByIds(const std::vector<long long>& ids) {
    long long count = cm::system::mapper::SysFileMapper::deleteSysFileByIds(ids);
    return cm::core::domain::AjaxResult::success(Json(count));
}

cm::core::domain::AjaxResult SysFileService::saveSysFile(cm::domain::SysFile& file) {
    auto now = std::chrono::system_clock::now();
    auto nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    if (file.id) {
        file.updateTime = nowMs;
        cm::system::mapper::SysFileMapper::updateSysFile(file);
    } else {
        file.createTime = nowMs;
        file.updateTime = nowMs;
        cm::system::mapper::SysFileMapper::insertSysFile(file);
    }
    return cm::core::domain::AjaxResult::success();
}

cm::core::domain::AjaxResult SysFileService::updateCAFile(cm::domain::SysFile& file) {
    if (file.id) {
        cm::system::mapper::SysFileMapper::updateCAFile(*file.id);
    }
    return cm::core::domain::AjaxResult::success();
}

} // namespace cm::system::service
