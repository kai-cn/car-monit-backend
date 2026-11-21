// 对应 Java: SysFileController (partial - CRUD only, file upload/download not ported)
#include "cm/web/BaseController.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysFileService.hpp"

namespace cm::web {

void registerSysFileController(cm::web::Router& r) {
    r.get("/system/file/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysFile file;
        file.id = ctx.optParam("id") ? std::stoll(*ctx.optParam("id")) : std::optional<long long>{};
        file.fileName = ctx.optParam("fileName");
        file.bucketName = ctx.optParam("bucketName");
        file.original = ctx.optParam("original");
        file.type = ctx.optParam("type");
        file.bussType = ctx.optParam("bussType");
        file.bussName = ctx.optParam("bussName");
        auto [list, total] = cm::system::service::SysFileService::selectSysFileListEntityPage(file, page);
        Json rowsArr = Json::array();
        for (const auto& f : list) rowsArr.push_back(f.toJson());
        return BaseController::ok(BaseController::dataTable(rowsArr, total));
    }).permi("base:sysflie:list");

    r.get("/system/file/getInfoById/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long id = ctx.pathVarLong("id");
        auto file = cm::system::service::SysFileService::selectSysFileById(id);
        if (file) {
            return BaseController::ok(BaseController::success(file->toJson()));
        }
        return BaseController::ok(BaseController::error("文件不存在"));
    });

    r.get("/system/file/{ids}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string ids = ctx.pathVar("ids");
        // Remove trailing comma if present
        if (!ids.empty() && ids.back() == ',') ids.pop_back();
        if (ids.empty()) ids = "-111111";
        auto files = cm::system::service::SysFileService::selectSysFileByIds(ids);
        Json arr = Json::array();
        for (const auto& f : files) arr.push_back(f.toJson());
        return BaseController::ok(BaseController::success(arr));
    });

    r.del("/system/file/del/{id}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long id = ctx.pathVarLong("id");
        auto result = cm::system::service::SysFileService::deleteSysFileById(id);
        return BaseController::ok(result);
    });

    r.del("/system/file/{ids}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string idsStr = ctx.pathVar("ids");
        std::vector<long long> ids;
        std::string cur;
        for (char c : idsStr) {
            if (c == ',') {
                if (!cur.empty()) { ids.push_back(std::stoll(cur)); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) ids.push_back(std::stoll(cur));
        auto result = cm::system::service::SysFileService::deleteSysFileByIds(ids);
        return BaseController::ok(result);
    }).permi("base:supplier:remove");

    r.put("/system/file", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysFile file;
        file.fromJson(body);
        auto result = cm::system::service::SysFileService::saveSysFile(file);
        return BaseController::ok(result);
    });

    r.get("/system/file/getNewCa", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysFile file;
        file.bussType = "CA";
        auto list = cm::system::service::SysFileService::selectSysFileList(file);
        if (!list.empty()) {
            return BaseController::ok(BaseController::success(list[0].toJson()));
        }
        return BaseController::ok(BaseController::error("未找到CA驱动程序"));
    });

    r.post("/system/file/updateCAFile", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysFile file;
        file.fromJson(body);
        auto result = cm::system::service::SysFileService::updateCAFile(file);
        return BaseController::ok(result);
    });
}

} // namespace cm::web
