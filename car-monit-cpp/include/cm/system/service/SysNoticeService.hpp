#pragma once
#include <optional>
#include <string>
#include <vector>
#include "cm/system/domain/SysNotice.hpp"

namespace cm::system::service {

class SysNoticeService {
public:
    static std::vector<cm::domain::SysNotice> selectNoticeList(const cm::domain::SysNotice& notice);
    static std::optional<cm::domain::SysNotice> selectNoticeById(long long noticeId);
    static long long insertNotice(cm::domain::SysNotice& notice);
    static long long updateNotice(cm::domain::SysNotice& notice);
    static long long deleteNoticeByIds(const std::vector<long long>& noticeIds);
};

} // namespace cm::system::service
