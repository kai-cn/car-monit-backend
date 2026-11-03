// 对应 Java: com.ruoyi.web.controller.common.CommonController
#include "cm/web/controller/common/CommonController.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "cm/common/compat/Path.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/security/TokenService.hpp"
#include "cm/framework/web/FileUpload.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

namespace {

/** 对应 Java FileUtils.checkAllowDownload + token 校验 */
bool checkAllowDownload(const std::string& fileName, const cm::http::HttpRequest& req) {
    // 检查文件名合法性
    if (!cm::framework::web::FileUpload::checkAllowDownload(fileName)) {
        return false;
    }
    // Java: checkAllowDownload 支持 token 从 param 或 header 获取
    // 此处简化：仅检查文件名合法性
    return true;
}

std::string getRealFileName(const std::string& fileName) {
    // Java: System.currentTimeMillis() + fileName.substring(fileName.indexOf("_") + 1)
    auto now = std::chrono::system_clock::now();
    auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    auto pos = fileName.find('_');
    if (pos == std::string::npos) {
        return std::to_string(millis) + fileName;
    }
    return std::to_string(millis) + fileName.substr(pos + 1);
}

} // namespace

void registerCommonController(Router& r) {
    // GET /common/download
    r.get("/common/download", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string fileName = ctx.param("fileName");
        std::string deleteStr = ctx.param("delete");
        bool deleteFile = (deleteStr == "true" || deleteStr == "1");

        try {
            if (!checkAllowDownload(fileName, ctx.req)) {
                throw cm::exception::ServiceException(
                    cm::utils::StringUtils::format("文件名称({})非法，不允许下载。 ", fileName));
            }

            auto& cfg = cm::config::AppConfig::instance();
            std::string downloadPath = cfg.profile + "/download/" + fileName;
            // 落盘路径必须是 UTF-8 语义：Windows 的 std::filesystem 默认按本地码页解释窄字符串
            const std::filesystem::path file = cm::compat::fsPath(downloadPath);

            if (!std::filesystem::exists(file)) {
                throw cm::exception::ServiceException("文件不存在: " + fileName);
            }

            std::ifstream in(file, std::ios::binary);
            if (!in) {
                throw cm::exception::ServiceException("无法读取文件: " + fileName);
            }

            std::ostringstream ss;
            ss << in.rdbuf();
            std::string content = ss.str();
            in.close();

            if (deleteFile) {
                std::filesystem::remove(file);
            }

            std::string realFileName = getRealFileName(fileName);
            std::string encodedName = cm::framework::web::FileUpload::percentEncode(realFileName);

            cm::http::ApiResponse resp;
            resp.status = 200;
            resp.content_type = "application/octet-stream";
            resp.body = std::move(content);
            resp.headers["Content-Disposition"] = "attachment; filename=" + encodedName +
                                                   "; filename*=utf-8''" + encodedName;
            resp.headers["Access-Control-Expose-Headers"] = "Content-Disposition,download-filename";
            resp.headers["download-filename"] = encodedName;
            return resp;
        } catch (const std::exception& e) {
            LOG_ERROR("CommonController", std::string("下载文件失败: ") + e.what());
            auto a = BaseController::error(e.what());
            return cm::http::ApiResponse::json(a.toJson());
        }
    }).anonymous();
    // ↑ SecurityConfig: .antMatchers("/common/download**").anonymous() == access("isAnonymous()")，
    //   带合法 token 的请求会拿到容器级 403；浏览器 <a href> 下载不带 Authorization 头，因此正常。

    // POST /common/upload
    r.post("/common/upload", [](RequestContext& ctx) -> cm::http::ApiResponse {
        try {
            auto& cfg = cm::config::AppConfig::instance();
            std::string filePath = cfg.profile + "/upload";

            auto part = ctx.req.getPart("file");
            if (!part) {
                throw cm::exception::ServiceException("未找到上传文件");
            }

            std::string fileName = cm::framework::web::FileUpload::upload(
                filePath, part->filename, part->content_type, part->data);

            // Java: serverConfig.getUrl() + fileName
            std::string url = "http://localhost:" + std::to_string(cfg.port) + fileName;

            auto ajax = BaseController::success();
            ajax.put("url", url);
            ajax.put("fileName", fileName);
            ajax.put("newFileName", cm::framework::web::FileUpload::getName(fileName));
            ajax.put("originalFilename", part->filename);
            return cm::http::ApiResponse::json(ajax.toJson());
        } catch (const std::exception& e) {
            auto ajax = BaseController::error(e.what());
            return cm::http::ApiResponse::json(ajax.toJson());
        }
    });

    // POST /common/uploads
    r.post("/common/uploads", [](RequestContext& ctx) -> cm::http::ApiResponse {
        try {
            auto& cfg = cm::config::AppConfig::instance();
            std::string filePath = cfg.profile + "/upload";

            std::vector<std::string> urls;
            std::vector<std::string> fileNames;
            std::vector<std::string> newFileNames;
            std::vector<std::string> originalFilenames;

            for (const auto& part : ctx.req.parts) {
                if (!part.isFile()) continue;

                std::string fileName = cm::framework::web::FileUpload::upload(
                    filePath, part.filename, part.content_type, part.data);

                std::string url = "http://localhost:" + std::to_string(cfg.port) + fileName;
                urls.push_back(url);
                fileNames.push_back(fileName);
                newFileNames.push_back(cm::framework::web::FileUpload::getName(fileName));
                originalFilenames.push_back(part.filename);
            }

            auto ajax = BaseController::success();
            ajax.put("urls", cm::utils::StringUtils::join(urls, ","));
            ajax.put("fileNames", cm::utils::StringUtils::join(fileNames, ","));
            ajax.put("newFileNames", cm::utils::StringUtils::join(newFileNames, ","));
            ajax.put("originalFilenames", cm::utils::StringUtils::join(originalFilenames, ","));
            return cm::http::ApiResponse::json(ajax.toJson());
        } catch (const std::exception& e) {
            auto ajax = BaseController::error(e.what());
            return cm::http::ApiResponse::json(ajax.toJson());
        }
    });

    // GET /common/download/resource
    r.get("/common/download/resource", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string resource = ctx.param("resource");

        try {
            if (!checkAllowDownload(resource, ctx.req)) {
                throw cm::exception::ServiceException(
                    cm::utils::StringUtils::format("资源文件({})非法，不允许下载。 ", resource));
            }

            // Java: 本地资源路径（注释掉的代码）
            // String localPath = RuoYiConfig.getProfile();
            // String downloadPath = localPath + StringUtils.substringAfter(resource, Constants.RESOURCE_PREFIX);

            auto& cfg = cm::config::AppConfig::instance();
            std::string localPath = cfg.profile;
            std::string relPath = cm::utils::StringUtils::substringAfter(resource, cm::constant::Constants::RESOURCE_PREFIX);
            std::string downloadPath = localPath + "/" + relPath;
            const std::filesystem::path file = cm::compat::fsPath(downloadPath);

            // 路径穿越防护
            if (downloadPath.find("..") != std::string::npos) {
                throw cm::exception::ServiceException("非法的资源路径");
            }

            if (!std::filesystem::exists(file)) {
                throw cm::exception::ServiceException("资源文件不存在: " + resource);
            }

            std::ifstream in(file, std::ios::binary);
            if (!in) {
                throw cm::exception::ServiceException("无法读取资源文件: " + resource);
            }

            std::ostringstream ss;
            ss << in.rdbuf();
            std::string content = ss.str();
            in.close();

            std::string downloadName = cm::framework::web::FileUpload::getName(downloadPath);
            std::string encodedName = cm::framework::web::FileUpload::percentEncode(downloadName);

            cm::http::ApiResponse resp;
            resp.status = 200;
            resp.content_type = "application/octet-stream";
            resp.body = std::move(content);
            resp.headers["Content-Disposition"] = "attachment; filename=" + encodedName +
                                                   "; filename*=utf-8''" + encodedName;
            resp.headers["Access-Control-Expose-Headers"] = "Content-Disposition,download-filename";
            resp.headers["download-filename"] = encodedName;
            return resp;
        } catch (const std::exception& e) {
            LOG_ERROR("CommonController", std::string("下载文件失败: ") + e.what());
            auto a = BaseController::error(e.what());
            return cm::http::ApiResponse::json(a.toJson());
        }
    }); // SecurityConfig: .antMatchers("/common/download/resource**").authenticated()
}

} // namespace cm::web
