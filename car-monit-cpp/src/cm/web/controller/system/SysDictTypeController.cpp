// 对应 Java: SysDictTypeController
#include "cm/web/BaseController.hpp"
#include "cm/common/constant/UserConstants.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysDictTypeService.hpp"

namespace cm::web {

void registerSysDictTypeController(cm::web::Router& r) {
    r.get("/system/dict/type/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysDictType dictType;
        dictType.dictName = ctx.optParam("dictName");
        dictType.dictType = ctx.optParam("dictType");
        dictType.status = ctx.optParam("status");
        auto [list, total] = cm::system::service::SysDictTypeService::selectDictTypeListEntityPage(dictType, page);
        Json rowsArr = Json::array();
        for (const auto& d : list) rowsArr.push_back(d.toJson());
        return BaseController::ok(BaseController::dataTable(rowsArr, total));
    }).permi("system:dict:list");

    r.get("/system/dict/type/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysDictType dictType;
        dictType.dictName = ctx.optParam("dictName");
        dictType.dictType = ctx.optParam("dictType");
        dictType.status = ctx.optParam("status");
        auto list = cm::system::service::SysDictTypeService::selectDictTypeList(dictType);
        return BaseController::ok(BaseController::success(std::string("Excel导出功能未实现")));
    }).permi("system:dict:export");

    r.get("/system/dict/type/{dictId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long dictId = ctx.pathVarLong("dictId");
        auto dictType = cm::system::service::SysDictTypeService::selectDictTypeById(dictId);
        if (dictType) {
            return BaseController::ok(BaseController::success(dictType->toJson()));
        }
        return BaseController::ok(BaseController::error("字典类型不存在"));
    }).permi("system:dict:query");

    r.post("/system/dict/type", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysDictType dict;
        dict.fromJson(body);
        if (cm::constant::UserConstants::NOT_UNIQUE_OLD ==
            cm::system::service::SysDictTypeService::checkDictTypeUnique(dict)) {
            return BaseController::ok(BaseController::error(
                "新增字典'" + dict.dictName.value_or("") + "'失败，字典类型已存在"));
        }
        dict.createBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysDictTypeService::insertDictType(dict);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:add");

    r.put("/system/dict/type", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysDictType dict;
        dict.fromJson(body);
        if (cm::constant::UserConstants::NOT_UNIQUE_OLD ==
            cm::system::service::SysDictTypeService::checkDictTypeUnique(dict)) {
            return BaseController::ok(BaseController::error(
                "修改字典'" + dict.dictName.value_or("") + "'失败，字典类型已存在"));
        }
        dict.updateBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysDictTypeService::updateDictType(dict);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:edit");

    r.del("/system/dict/type/{dictIds}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string dictIdsStr = ctx.pathVar("dictIds");
        std::vector<long long> dictIds;
        std::string cur;
        for (char c : dictIdsStr) {
            if (c == ',') {
                if (!cur.empty()) { dictIds.push_back(std::stoll(cur)); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) dictIds.push_back(std::stoll(cur));
        long long rows = cm::system::service::SysDictTypeService::deleteDictTypeByIds(dictIds);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:remove");

    r.del("/system/dict/type/clearCache", [](RequestContext&) -> cm::http::ApiResponse {
        cm::system::service::SysDictTypeService::clearCache();
        return BaseController::ok(BaseController::success());
    }).permi("system:dict:remove");

    r.get("/system/dict/type/optionselect", [](RequestContext&) -> cm::http::ApiResponse {
        auto dictTypes = cm::system::service::SysDictTypeService::selectDictTypeAll();
        Json arr = Json::array();
        for (const auto& d : dictTypes) arr.push_back(d.toJson());
        return BaseController::ok(BaseController::success(arr));
    });
}

} // namespace cm::web
