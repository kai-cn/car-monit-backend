// 对应 Java: SysNoticeController
#include "cm/web/BaseController.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysNoticeService.hpp"

namespace cm::web {

void registerSysNoticeController(cm::web::Router& r) {
    r.get("/system/notice/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysNotice notice;
        notice.noticeTitle = ctx.optParam("noticeTitle");
        notice.noticeType = ctx.optParam("noticeType");
        notice.createBy = ctx.optParam("createBy");
        notice.status = ctx.optParam("status");
        auto [list, total] = cm::system::service::SysNoticeService::selectNoticeListEntityPage(notice, page);
        Json rowsArr = Json::array();
        for (const auto& n : list) rowsArr.push_back(n.toJson());
        return BaseController::ok(BaseController::dataTable(rowsArr, total));
    });

    r.get("/system/notice/listquery", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysNotice notice;
        notice.noticeTitle = ctx.optParam("noticeTitle");
        notice.noticeType = ctx.optParam("noticeType");
        notice.createBy = ctx.optParam("createBy");
        notice.status = "0";
        auto [list, total] = cm::system::service::SysNoticeService::selectNoticeListEntityPage(notice, page);
        Json rowsArr = Json::array();
        for (const auto& n : list) rowsArr.push_back(n.toJson());
        return BaseController::ok(BaseController::dataTable(rowsArr, total));
    });

    r.get("/system/notice/{noticeId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long noticeId = ctx.pathVarLong("noticeId");
        auto notice = cm::system::service::SysNoticeService::selectNoticeById(noticeId);
        if (notice) {
            return BaseController::ok(BaseController::success(notice->toJson()));
        }
        return BaseController::ok(BaseController::error("公告不存在"));
    });

    r.get("/system/notice/view/{noticeId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long noticeId = ctx.pathVarLong("noticeId");
        auto notice = cm::system::service::SysNoticeService::selectNoticeById(noticeId);
        if (notice) {
            return BaseController::ok(BaseController::success(notice->toJson()));
        }
        return BaseController::ok(BaseController::error("公告不存在"));
    }).permitAll();

    r.post("/system/notice", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysNotice notice;
        notice.fromJson(body);
        long long rows = cm::system::service::SysNoticeService::insertNotice(notice);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:notice:add");

    r.put("/system/notice", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysNotice notice;
        notice.fromJson(body);
        long long rows = cm::system::service::SysNoticeService::updateNotice(notice);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:notice:edit");

    r.del("/system/notice/{noticeIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string noticeIdsStr = ctx.pathVar("noticeIds");
        std::vector<long long> noticeIds;
        std::string cur;
        for (char c : noticeIdsStr) {
            if (c == ',') {
                if (!cur.empty()) { noticeIds.push_back(std::stoll(cur)); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) noticeIds.push_back(std::stoll(cur));
        long long rows = cm::system::service::SysNoticeService::deleteNoticeByIds(noticeIds);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:notice:remove");
}

} // namespace cm::web
