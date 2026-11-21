#pragma once
// 对应 Java: com.ruoyi.system.domain.SysLogininfor
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::domain {

struct SysLogininfor : BaseEntity {
    std::optional<long long> infoId;
    std::optional<std::string> userName;
    std::optional<std::string> status;
    std::optional<std::string> ipaddr;
    std::optional<std::string> loginLocation;
    std::optional<std::string> browser;
    std::optional<std::string> os;
    std::optional<std::string> msg;
    std::optional<long long> loginTime;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "infoId", infoId);
        putStr(j, "userName", userName);
        putStr(j, "status", status);
        putStr(j, "ipaddr", ipaddr);
        putStr(j, "loginLocation", loginLocation);
        putStr(j, "browser", browser);
        putStr(j, "os", os);
        putStr(j, "msg", msg);
        putJsonDate(j, "loginTime", loginTime);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        infoId = getI64(j, "infoId");
        userName = getStr(j, "userName");
        status = getStr(j, "status");
        ipaddr = getStr(j, "ipaddr");
        loginLocation = getStr(j, "loginLocation");
        browser = getStr(j, "browser");
        os = getStr(j, "os");
        msg = getStr(j, "msg");
        loginTime = getDate(j, "loginTime");
    }

    static SysLogininfor fromRow(const cm::db::Row& row) {
        SysLogininfor r;
        r.infoId = row.optI64("info_id");
        r.userName = row.get("user_name");
        r.status = row.get("status");
        r.ipaddr = row.get("ipaddr");
        r.loginLocation = row.get("login_location");
        r.browser = row.get("browser");
        r.os = row.get("os");
        r.msg = row.get("msg");
        r.loginTime = utils::DateUtils::parseDbDateTime(row.str("login_time"));
        return r;
    }
};

} // namespace cm::domain
