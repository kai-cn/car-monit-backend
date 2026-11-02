// 对应 Java: SysDictDataController
#include "cm/web/BaseController.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/system/service/SysDictDataService.hpp"
#include "cm/system/service/SysDictTypeService.hpp"

namespace cm::web {

void registerSysDictDataController(cm::web::Router& r) {
    r.get("/system/dict/data/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();
        cm::domain::SysDictData dictData;
        dictData.dictType = ctx.optParam("dictType");
        dictData.dictLabel = ctx.optParam("dictLabel");
        dictData.status = ctx.optParam("status");
        auto list = cm::system::service::SysDictDataService::selectDictDataList(dictData);
        Json rowsArr = Json::array();
        for (const auto& d : list) rowsArr.push_back(d.toJson());
        auto countSql = "select count(1) from sys_dict_data where 1=1";
        auto dataSql = "select * from sys_dict_data where 1=1";
        auto result = cm::db::queryPage(countSql, dataSql, page);
        return BaseController::ok(BaseController::dataTable(rowsArr, result.total));
    }).permi("system:dict:list");

    r.get("/system/dict/data/export", [](RequestContext& ctx) -> cm::http::ApiResponse {
        cm::domain::SysDictData dictData;
        dictData.dictType = ctx.optParam("dictType");
        dictData.dictLabel = ctx.optParam("dictLabel");
        dictData.status = ctx.optParam("status");
        auto list = cm::system::service::SysDictDataService::selectDictDataList(dictData);
        return BaseController::ok(BaseController::success(std::string("Excel导出功能未实现")));
    }).permi("system:dict:export");

    r.get("/system/dict/data/{dictCode}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        long long dictCode = ctx.pathVarLong("dictCode");
        auto dictData = cm::system::service::SysDictDataService::selectDictDataById(dictCode);
        if (dictData) {
            return BaseController::ok(BaseController::success(dictData->toJson()));
        }
        return BaseController::ok(BaseController::error("字典数据不存在"));
    }).permi("system:dict:query");

    r.get("/system/dict/data/type/{dictType}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string dictType = ctx.pathVar("dictType");
        auto data = cm::system::service::SysDictTypeService::selectDictDataByType(dictType);
        Json arr = Json::array();
        for (const auto& d : data) arr.push_back(d.toJson());
        return BaseController::ok(BaseController::success(arr));
    });

    r.get("/system/dict/data/typemore/{dictType}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string dictType = ctx.pathVar("dictType");
        auto data = cm::system::service::SysDictTypeService::selectDictDataByTypeMore(dictType);
        // Group by dictType
        Json grouped = Json::object();
        for (const auto& d : data) {
            std::string key = d.dictType.value_or("");
            if (!grouped.contains(key)) grouped[key] = Json::array();
            grouped[key].push_back(d.toJson());
        }
        return BaseController::ok(BaseController::success(grouped));
    });

    r.post("/system/dict/data", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysDictData dict;
        dict.fromJson(body);
        dict.createBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysDictDataService::insertDictData(dict);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:add");

    r.put("/system/dict/data", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto body = ctx.body();
        cm::domain::SysDictData dict;
        dict.fromJson(body);
        dict.updateBy = cm::security::SecurityUtils::getUsername();
        long long rows = cm::system::service::SysDictDataService::updateDictData(dict);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:edit");

    r.del("/system/dict/data/{dictCodes}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string dictCodesStr = ctx.pathVar("dictCodes");
        std::vector<long long> dictCodes;
        std::string cur;
        for (char c : dictCodesStr) {
            if (c == ',') {
                if (!cur.empty()) { dictCodes.push_back(std::stoll(cur)); cur.clear(); }
            } else cur += c;
        }
        if (!cur.empty()) dictCodes.push_back(std::stoll(cur));
        long long rows = cm::system::service::SysDictDataService::deleteDictDataByIds(dictCodes);
        return BaseController::ok(BaseController::toAjax(rows));
    }).permi("system:dict:remove");
}

} // namespace cm::web
