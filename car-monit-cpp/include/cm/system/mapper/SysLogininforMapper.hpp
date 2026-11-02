#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysLogininforMapper
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/system/domain/SysLogininfor.hpp"

namespace cm::system::mapper {

class SysLogininforMapper {
public:
    static std::vector<cm::domain::SysLogininfor> selectLogininforList(const cm::domain::SysLogininfor& logininfor);
    static int deleteLogininforByIds(const std::vector<long long>& infoIds);
    static void cleanLogininfor();
};

} // namespace cm::system::mapper
