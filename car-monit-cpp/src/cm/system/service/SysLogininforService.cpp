// 对应 Java: com.ruoyi.system.service.impl.SysLogininforServiceImpl
#include "cm/system/service/SysLogininforService.hpp"

#include "cm/system/mapper/SysLogininforMapper.hpp"

namespace cm::system::service {

std::vector<cm::domain::SysLogininfor> SysLogininforService::selectLogininforList(const cm::domain::SysLogininfor& logininfor) {
    return cm::system::mapper::SysLogininforMapper::selectLogininforList(logininfor);
}

int SysLogininforService::deleteLogininforByIds(const std::vector<long long>& infoIds) {
    return cm::system::mapper::SysLogininforMapper::deleteLogininforByIds(infoIds);
}

void SysLogininforService::cleanLogininfor() {
    cm::system::mapper::SysLogininforMapper::cleanLogininfor();
}

} // namespace cm::system::service
