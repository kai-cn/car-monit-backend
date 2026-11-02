#pragma once
// 对应 Java: com.ruoyi.common.core.controller.BaseController
#include <string>
#include <type_traits>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/page/TableDataInfo.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/http/HttpResponse.hpp"
#include "cm/framework/web/Router.hpp"

namespace cm::web {

/** 把数据库行按 mapper 转成 JSON 数组 */
template <class Fn>
inline Json rowsToArray(const cm::db::Result& res, Fn&& mapper) {
    Json arr = Json::array();
    for (const auto& row : res.rows) arr.push_back(mapper(row));
    return arr;
}

/** 对应 BaseController 的通用返回封装 */
class BaseController {
public:
    using Ajax = cm::core::domain::AjaxResult;

    /** 对应 BaseController.success() */
    static Ajax success() { return Ajax::success(); }
    static Ajax success(const std::string& msg) { return Ajax::success(msg); }
    static Ajax success(const Json& data) { return Ajax::success(data); }
    static Ajax success(const std::string& msg, const Json& data) {
        return Ajax::success(msg, data);
    }
    static Ajax error() { return Ajax::error(); }
    static Ajax error(const std::string& msg) { return Ajax::error(msg); }
    static Ajax warn(const std::string& msg) { return Ajax::warn(msg); }

    /** 对应 toAjax(int rows)：Java 只有 int 版本，C++ 里用模板收所有整型，
     *  否则 int 实参会在 long long / bool 两个重载之间歧义 */
    template <class T, std::enable_if_t<std::is_integral_v<T> && !std::is_same_v<T, bool>, int> = 0>
    static Ajax toAjax(T rows) {
        return rows > 0 ? Ajax::success() : Ajax::error();
    }
    /** 对应 toAjax(boolean result) */
    static Ajax toAjax(bool result) { return result ? Ajax::success() : Ajax::error(); }

    /** 对应 getDataTable(List) */
    static cm::core::page::TableDataInfo dataTable(Json rows, long long total) {
        return cm::core::page::TableDataInfo(std::move(rows), total);
    }
    static cm::core::page::TableDataInfo dataTable(const cm::db::PageResult& page) {
        return cm::core::page::TableDataInfo(Json::array(), page.total);
    }

    /** 统一输出 */
    static cm::http::ApiResponse ok(const Ajax& a) {
        return cm::http::ApiResponse::json(a.toJson());
    }
    static cm::http::ApiResponse ok(const cm::core::page::TableDataInfo& t) {
        return cm::http::ApiResponse::json(t.toJson());
    }
};

} // namespace cm::web
