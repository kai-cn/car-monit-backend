#pragma once
// 对应 Java: com.ruoyi.framework.web.exception.GlobalExceptionHandler
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {

class ExceptionMapper {
public:
    /** 当前线程正在处理的异常（由 dispatch 的 catch 块设置） */
    static cm::http::ApiResponse map(std::exception_ptr ep);
};

} // namespace cm::web
