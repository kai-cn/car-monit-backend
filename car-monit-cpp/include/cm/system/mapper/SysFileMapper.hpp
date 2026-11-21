#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysFileMapper
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysFile.hpp"

namespace cm::system::mapper {

class SysFileMapper {
public:
        static std::string selectSysFileListSql(const cm::domain::SysFile& file);
static std::pair<std::vector<cm::domain::SysFile>, long long> selectSysFileListEntityPage(
            const cm::domain::SysFile& file, const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysFile> selectSysFileList(const cm::domain::SysFile& file);
    static std::optional<cm::domain::SysFile> selectSysFileById(long long id);
    static std::vector<cm::domain::SysFile> selectSysFileByIds(const std::string& ids);
    static long long insertSysFile(const cm::domain::SysFile& file);
    static long long updateSysFile(const cm::domain::SysFile& file);
    static long long deleteSysFileById(long long id);
    static long long deleteSysFileByIds(const std::vector<long long>& ids);
    static long long deleteSysFileByIdNew(long long id);
    static long long updateCAFile(long long id);

    static cm::domain::SysFile mapSysFile(const cm::db::Row& row);
};

} // namespace cm::system::mapper
