#pragma once
// 对应 Java: com.ruoyi.system.service.ISysLogininforService
#include <string>
#include <vector>

#include "cm/system/domain/SysLogininfor.hpp"

namespace cm::system::service {

class SysLogininforService {
public:
    static std::vector<cm::domain::SysLogininfor> selectLogininforList(const cm::domain::SysLogininfor& logininfor);
    static int deleteLogininforByIds(const std::vector<long long>& infoIds);
    static void cleanLogininfor();
};

} // namespace cm::system::service
