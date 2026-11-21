#pragma once
// 对应 Java: LoginBody / RegisterBody
#include <optional>
#include <string>

#include "cm/common/core/domain/BaseEntity.hpp"

namespace cm::domain {

struct LoginBody {
    std::optional<std::string> username;
    std::optional<std::string> password;
    std::optional<std::string> code;
    std::string uuid{""};

    void fromJson(const Json& j) {
        username = getStr(j, "username");
        password = getStr(j, "password");
        code = getStr(j, "code");
        uuid = getStr(j, "uuid").value_or("");
    }
};

struct RegisterBody : LoginBody {};

} // namespace cm::domain
