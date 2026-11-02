// 对应 Java: SysNoticeServiceImpl
#include "cm/system/service/SysNoticeService.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/system/mapper/SysNoticeMapper.hpp"

namespace cm::system::service {

std::vector<cm::domain::SysNotice> SysNoticeService::selectNoticeList(const cm::domain::SysNotice& notice) {
    return cm::system::mapper::SysNoticeMapper::selectNoticeList(notice);
}

std::optional<cm::domain::SysNotice> SysNoticeService::selectNoticeById(long long noticeId) {
    return cm::system::mapper::SysNoticeMapper::selectNoticeById(noticeId);
}

long long SysNoticeService::insertNotice(cm::domain::SysNotice& notice) {
    notice.noticeType = "1";
    notice.createBy = std::to_string(cm::security::SecurityUtils::getUserId());
    notice.tenantId = cm::security::SecurityUtils::getTenantId();
    return cm::system::mapper::SysNoticeMapper::insertNotice(notice);
}

long long SysNoticeService::updateNotice(cm::domain::SysNotice& notice) {
    notice.updateBy = std::to_string(cm::security::SecurityUtils::getUserId());
    return cm::system::mapper::SysNoticeMapper::updateNotice(notice);
}

long long SysNoticeService::deleteNoticeByIds(const std::vector<long long>& noticeIds) {
    return cm::system::mapper::SysNoticeMapper::deleteNoticeByIds(noticeIds);
}

} // namespace cm::system::service
