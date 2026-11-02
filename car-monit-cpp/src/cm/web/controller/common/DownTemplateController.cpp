// 对应 Java: com.ruoyi.web.controller.common.DownTemplateController
#include "cm/web/controller/common/DownTemplateController.hpp"

#include <filesystem>
#include <fstream>
#include <sstream>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

void registerDownTemplateController(Router& r) {
    // GET /downTemplate/{type}
    r.get("/downTemplate/{type}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string type = ctx.pathVar("type");
        std::string url = "templates/down";

        if (type == "goodsFkApplyDetail") {
            url = url + "/importGoodsFkApplyDetail.xlsx";
        } else if (type == "goodsRkApplyDetail") {
            url = url + "/importGoodsRkApplyDetail.xlsx";
        } else if (type == "planListDetail") {
            url = url + "/importPlanListDetail.xlsx";
        } else if (type == "importPsbz") {
            url = url + "/importPsbz.xlsx";
        } else if (type == "importSupplierAnnualScore") {
            url = url + "/importSupplierAnnualScore.xlsx";
        } else if (type == "carinfo") {
            url = url + "/importCar.xlsx";
        } else if (type == "carExcept") {
            url = url + "/importCarExcept.xlsx";
        } else {
            auto a = BaseController::error("不支持的模板类型: " + type);
            return cm::http::ApiResponse::json(a.toJson());
        }

        try {
            // Java: TemplateExportParams params = new TemplateExportParams(url, true);
            // 此处直接从 config/static 目录读取模板文件
            std::string filePath = "config/static/" + url;

            if (!std::filesystem::exists(filePath)) {
                throw cm::exception::ServiceException("模板文件不存在: " + url);
            }

            std::ifstream in(filePath, std::ios::binary);
            if (!in) {
                throw cm::exception::ServiceException("无法读取模板文件: " + url);
            }

            std::ostringstream ss;
            ss << in.rdbuf();
            std::string content = ss.str();
            in.close();

            cm::http::ApiResponse resp;
            resp.status = 200;
            resp.content_type = "application/octet-stream;charset=UTF-8";
            resp.body = std::move(content);
            resp.headers["Content-Disposition"] = "attachment";
            return resp;
        } catch (const std::exception& e) {
            LOG_ERROR("DownTemplateController", std::string("下载模板失败: ") + e.what());
            auto a = BaseController::error(e.what());
            return cm::http::ApiResponse::json(a.toJson());
        }
    });
}

} // namespace cm::web
