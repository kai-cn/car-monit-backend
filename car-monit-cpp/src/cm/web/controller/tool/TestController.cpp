// 对应 Java: com.ruoyi.web.controller.tool.TestController
#include "cm/web/controller/tool/TestController.hpp"

#include <map>

#include "cm/common/core/domain/R.hpp"
#include "cm/common/utils/Convert.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/web/Router.hpp"

namespace cm::web {

namespace {

// 对应 Java UserEntity
struct UserEntity {
    int userId{0};
    std::string username;
    std::string password;
    std::string mobile;

    Json toJson() const {
        Json j = Json::object();
        j["userId"] = userId;
        j["username"] = username;
        j["password"] = password;
        j["mobile"] = mobile;
        return j;
    }

    void fromJson(const Json& j) {
        if (j.contains("userId") && j["userId"].is_number_integer()) {
            userId = j["userId"].get<int>();
        }
        if (j.contains("username") && j["username"].is_string()) {
            username = j["username"].get<std::string>();
        }
        if (j.contains("password") && j["password"].is_string()) {
            password = j["password"].get<std::string>();
        }
        if (j.contains("mobile") && j["mobile"].is_string()) {
            mobile = j["mobile"].get<std::string>();
        }
    }
};

// 对应 Java: private final static Map<Integer, UserEntity> users = new LinkedHashMap<>();
std::map<int, UserEntity>& getUsers() {
    static std::map<int, UserEntity> users = {
        {1, {1, "admin", "admin123", "15888888888"}},
        {2, {2, "ry", "admin123", "15666666666"}}
    };
    return users;
}

} // namespace

void registerTestController(Router& r) {
    // GET /test/user/list
    r.get("/test/user/list", [](RequestContext&) -> cm::http::ApiResponse {
        auto& users = getUsers();
        Json userList = Json::array();
        for (const auto& [id, user] : users) {
            userList.push_back(user.toJson());
        }
        auto result = cm::core::domain::R::ok(userList);
        return cm::http::ApiResponse::json(result.toJson());
    });

    // GET /test/user/{userId}
    r.get("/test/user/{userId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        int userId = static_cast<int>(ctx.pathVarLong("userId"));
        auto& users = getUsers();

        if (!users.empty() && users.count(userId) > 0) {
            auto result = cm::core::domain::R::ok(users[userId].toJson());
            return cm::http::ApiResponse::json(result.toJson());
        } else {
            auto result = cm::core::domain::R::fail("用户不存在");
            return cm::http::ApiResponse::json(result.toJson());
        }
    });

    // POST /test/user/save
    r.post("/test/user/save", [](RequestContext& ctx) -> cm::http::ApiResponse {
        UserEntity user;
        // 从 query params 或 form params 获取
        if (auto v = ctx.optParam("userId")) user.userId = cm::utils::Convert::toInt(*v);
        if (auto v = ctx.optParam("username")) user.username = *v;
        if (auto v = ctx.optParam("password")) user.password = *v;
        if (auto v = ctx.optParam("mobile")) user.mobile = *v;

        if (user.userId == 0) {
            auto result = cm::core::domain::R::fail("用户ID不能为空");
            return cm::http::ApiResponse::json(result.toJson());
        }

        auto& users = getUsers();
        users[user.userId] = user;
        auto result = cm::core::domain::R::ok();
        return cm::http::ApiResponse::json(result.toJson());
    });

    // PUT /test/user/update
    r.put("/test/user/update", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        UserEntity user;
        user.fromJson(body);

        if (user.userId == 0) {
            auto result = cm::core::domain::R::fail("用户ID不能为空");
            return cm::http::ApiResponse::json(result.toJson());
        }

        auto& users = getUsers();
        if (users.empty() || users.count(user.userId) == 0) {
            auto result = cm::core::domain::R::fail("用户不存在");
            return cm::http::ApiResponse::json(result.toJson());
        }

        users.erase(user.userId);
        users[user.userId] = user;
        auto result = cm::core::domain::R::ok();
        return cm::http::ApiResponse::json(result.toJson());
    });

    // DELETE /test/user/{userId}
    r.del("/test/user/{userId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        int userId = static_cast<int>(ctx.pathVarLong("userId"));
        auto& users = getUsers();

        if (!users.empty() && users.count(userId) > 0) {
            users.erase(userId);
            auto result = cm::core::domain::R::ok();
            return cm::http::ApiResponse::json(result.toJson());
        } else {
            auto result = cm::core::domain::R::fail("用户不存在");
            return cm::http::ApiResponse::json(result.toJson());
        }
    });
}

} // namespace cm::web
