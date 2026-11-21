#include "cm/framework/web/ExceptionMapper.hpp"

#include <string>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/web/Errors.hpp"

namespace cm::web {
namespace {

cm::http::ApiResponse ajax(int code, const std::optional<std::string>& msg, bool msgIsNull = false) {
    Json j = Json::object();
    j["msg"] = msgIsNull ? Json(nullptr) : Json(msg.value_or(""));
    j["code"] = code;
    return json(j);
}

} // namespace

cm::http::ApiResponse ExceptionMapper::map(std::exception_ptr ep) {
    try {
        std::rethrow_exception(ep);
    } catch (const cm::exception::AccessDeniedException& e) {
        LOG_ERROR("GlobalExceptionHandler", std::string("权限校验失败: ") + e.what());
        return ajax(403, std::string("没有权限，请联系管理员授权"));
    } catch (const cm::exception::HttpRequestMethodNotSupportedException& e) {
        return ajax(500, std::string(e.what()));
    } catch (const cm::exception::MethodArgumentTypeMismatchException& e) {
        return ajax(500, std::string(e.what()));
    } catch (const cm::exception::MissingPathVariableException& e) {
        return ajax(500, std::string(e.what()));
    } catch (const cm::exception::DemoModeException&) {
        return ajax(500, std::string("演示模式，不允许操作"));
    } catch (const cm::exception::ServiceException& e) {
        LOG_ERROR("GlobalExceptionHandler", e.getMessage());
        if (e.getCode()) return ajax(*e.getCode(), e.getMessage());
        return ajax(500, e.getMessage());
    } catch (const cm::exception::NullPointerException&) {
        // Java: AjaxResult.error(e.getMessage()) 且 getMessage() == null
        return ajax(500, std::nullopt, true);
    } catch (const cm::exception::BaseException& e) {
        LOG_ERROR("GlobalExceptionHandler", e.getMessage());
        return ajax(500, e.getMessage());
    } catch (const std::exception& e) {
        LOG_ERROR("GlobalExceptionHandler", std::string("未知异常: ") + e.what());
        return ajax(500, std::string(e.what()));
    } catch (...) {
        return ajax(500, std::nullopt, true);
    }
}

} // namespace cm::web
