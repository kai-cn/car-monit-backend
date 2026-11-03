#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysNoticeMapper
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysNotice.hpp"

namespace cm::system::mapper {

class SysNoticeMapper {
public:
        static std::string selectNoticeListSql(const cm::domain::SysNotice& notice);
static std::pair<std::vector<cm::domain::SysNotice>, long long> selectNoticeListEntityPage(
            const cm::domain::SysNotice& notice, const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysNotice> selectNoticeList(const cm::domain::SysNotice& notice);
    static std::optional<cm::domain::SysNotice> selectNoticeById(long long noticeId);
    static long long insertNotice(const cm::domain::SysNotice& notice);
    static long long updateNotice(const cm::domain::SysNotice& notice);
    static long long deleteNoticeById(long long noticeId);
    static long long deleteNoticeByIds(const std::vector<long long>& noticeIds);

    static cm::domain::SysNotice mapNotice(const cm::db::Row& row);
};

} // namespace cm::system::mapper
