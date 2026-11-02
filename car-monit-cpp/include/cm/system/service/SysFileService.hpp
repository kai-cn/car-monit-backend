#pragma once
#include <optional>
#include <string>
#include <vector>
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/system/domain/SysFile.hpp"

namespace cm::system::service {

class SysFileService {
public:
    static std::vector<cm::domain::SysFile> selectSysFileList(const cm::domain::SysFile& file);
    static std::optional<cm::domain::SysFile> selectSysFileById(long long id);
    static std::vector<cm::domain::SysFile> selectSysFileByIds(const std::string& ids);
    static cm::core::domain::AjaxResult deleteSysFileById(long long id);
    static cm::core::domain::AjaxResult deleteSysFileByIds(const std::vector<long long>& ids);
    static cm::core::domain::AjaxResult saveSysFile(cm::domain::SysFile& file);
    static cm::core::domain::AjaxResult updateCAFile(cm::domain::SysFile& file);
};

} // namespace cm::system::service
