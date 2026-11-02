#pragma once
// 对应 Java: com.ruoyi.common.core.domain.R
// POJO，Jackson 按字段声明序输出：code -> msg -> data（data 为 null 也输出）
#include <optional>
#include <string>

#include "cm/common/constant/HttpStatus.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::core::domain {

class R {
public:
    static constexpr int SUCCESS = constant::HttpStatus::SUCCESS;
    static constexpr int FAIL = constant::HttpStatus::ERROR;

    int code{0};
    std::optional<std::string> msg;
    Json data = Json(nullptr);

    R() = default;

    static R ok() { return restResult(Json(nullptr), SUCCESS, "操作成功"); }
    static R ok(Json data) { return restResult(std::move(data), SUCCESS, "操作成功"); }
    static R ok(Json data, const std::string& msg) { return restResult(std::move(data), SUCCESS, msg); }
    static R fail() { return restResult(Json(nullptr), FAIL, "操作失败"); }
    static R fail(const std::string& msg) { return restResult(Json(nullptr), FAIL, msg); }
    static R fail(Json data) { return restResult(std::move(data), FAIL, "操作失败"); }
    static R fail(Json data, const std::string& msg) { return restResult(std::move(data), FAIL, msg); }
    static R fail(int code, const std::string& msg) { return restResult(Json(nullptr), code, msg); }

    static bool isSuccess(const R& r) { return r.code == SUCCESS; }
    static bool isError(const R& r) { return !isSuccess(r); }

    Json toJson() const {
        Json j = Json::object();
        j["code"] = code;
        j["msg"] = msg ? Json(*msg) : Json(nullptr);
        j["data"] = data;
        return j;
    }
    std::string dump() const { return toJson().dump(); }

private:
    static R restResult(Json data, int code, const std::string& msg) {
        R r;
        r.code = code;
        r.data = std::move(data);
        r.msg = msg;
        return r;
    }
};

} // namespace cm::core::domain
