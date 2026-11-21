#pragma once
// 对应 Java: com.ruoyi.system.service.ISysUserOnlineService
#include <string>
#include <vector>

#include "cm/common/core/domain/model/LoginUser.hpp"
#include "cm/system/domain/SysUserOnline.hpp"

namespace cm::system::service {

class SysUserOnlineService {
public:
    static std::vector<cm::domain::SysUserOnline> selectOnlineByInfo(const std::string& ipaddr, const std::string& userName);
    static cm::domain::SysUserOnline loginUserToUserOnline(const cm::domain::LoginUser& user);
};

} // namespace cm::system::service
