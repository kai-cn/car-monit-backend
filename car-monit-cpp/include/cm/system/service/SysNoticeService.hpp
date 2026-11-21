#pragma once
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>
#include "cm/system/domain/SysNotice.hpp"

namespace cm::system::service {

class SysNoticeService {
public:
    /** 对应 startPage() + selectNoticeList + getDataTable：rows 与 total 共用同一条 SQL */
    static std::pair<std::vector<cm::domain::SysNotice>, long long> selectNoticeListEntityPage(const cm::domain::SysNotice& notice,
            const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysNotice> selectNoticeList(const cm::domain::SysNotice& notice);
    static std::optional<cm::domain::SysNotice> selectNoticeById(long long noticeId);
    static long long insertNotice(cm::domain::SysNotice& notice);
    static long long updateNotice(cm::domain::SysNotice& notice);
    static long long deleteNoticeByIds(const std::vector<long long>& noticeIds);
};

} // namespace cm::system::service
