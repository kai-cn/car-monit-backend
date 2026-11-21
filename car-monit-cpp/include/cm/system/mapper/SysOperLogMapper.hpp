#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysOperLogMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysOperLog.hpp"

namespace cm::system::mapper {

class SysOperLogMapper {
public:
    static std::vector<cm::domain::SysOperLog> selectOperLogList(const cm::domain::SysOperLog& operLog);
    static std::optional<cm::domain::SysOperLog> selectOperLogById(long long operId);
    static int deleteOperLogByIds(const std::vector<long long>& operIds);
    static void cleanOperLog();
};

} // namespace cm::system::mapper
