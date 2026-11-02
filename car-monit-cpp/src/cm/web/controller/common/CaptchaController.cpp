// 对应 Java: com.ruoyi.web.controller.common.CaptchaController
#include <string>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/CaptchaUtil.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/controller/Controllers.hpp"

namespace cm::web {

void registerCaptchaController(Router& r) {
    r.get("/captchaImage", [](RequestContext&) -> cm::http::ApiResponse {
        const std::string uuid = cm::utils::simpleUuid();
        const std::string verifyKey =
            std::string(cm::constant::Constants::CAPTCHA_CODE_KEY) + uuid;

        std::string capStr;
        std::string code;
        auto& cfg = cm::config::AppConfig::instance();
        if (cfg.captchaType == "math") {
            auto c = cm::utils::CaptchaUtil::randomMath();
            capStr = c.text;
            code = c.code;
        } else if (cfg.captchaType == "char") {
            auto c = cm::utils::CaptchaUtil::randomChar(4);
            capStr = c.text;
            code = c.code;
        } else {
            // Java 侧若 captchaType 非法，code/image 为 null 仍会写缓存并返回空图；
            // 此处保持空字符串行为
        }

        auto& cache = cm::redis::RedisCache::instance();
        cache.set(verifyKey, code,
                  static_cast<long long>(cm::constant::Constants::CAPTCHA_EXPIRATION) * 60);

        std::string png;
        try {
            png = cm::utils::CaptchaUtil::renderPng(capStr);
        } catch (const std::exception& e) {
            auto err = cm::core::domain::AjaxResult::error(e.what());
            return cm::http::ApiResponse::json(err.toJson());
        }

        auto ajax = cm::core::domain::AjaxResult::success();
        ajax.put("uuid", uuid);
        ajax.put("img", cm::utils::CaptchaUtil::base64(png));
        return cm::http::ApiResponse::json(ajax.toJson());
    }).permitAll();
}

} // namespace cm::web
