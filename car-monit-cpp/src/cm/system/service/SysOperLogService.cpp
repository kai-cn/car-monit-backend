// 对应 Java: com.ruoyi.system.service.impl.SysOperLogServiceImpl
#include "cm/system/service/SysOperLogService.hpp"

#include "cm/system/mapper/SysOperLogMapper.hpp"

namespace cm::system::service {

std::vector<cm::domain::SysOperLog> SysOperLogService::selectOperLogList(const cm::domain::SysOperLog& operLog) {
    return cm::system::mapper::SysOperLogMapper::selectOperLogList(operLog);
}

std::optional<cm::domain::SysOperLog> SysOperLogService::selectOperLogById(long long operId) {
    return cm::system::mapper::SysOperLogMapper::selectOperLogById(operId);
}

int SysOperLogService::deleteOperLogByIds(const std::vector<long long>& operIds) {
    return cm::system::mapper::SysOperLogMapper::deleteOperLogByIds(operIds);
}

void SysOperLogService::cleanOperLog() {
    cm::system::mapper::SysOperLogMapper::cleanOperLog();
}

} // namespace cm::system::service
