// 对应 Java: com.ruoyi.common.utils.file.FileUploadUtils + FileUtils
#include "cm/framework/web/FileUpload.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <regex>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/http/HttpRequest.hpp"

namespace cm::framework::web {

namespace {

std::string toLower(std::string s) {
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

} // namespace

const std::vector<std::string>& FileUpload::defaultAllowedExtension() {
    static const std::vector<std::string> ext = {
        // 图片
        "bmp", "gif", "jpg", "jpeg", "png",
        // word excel powerpoint
        "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "txt",
        // 压缩文件
        "rar", "zip", "gz", "bz2",
        // 视频格式
        "mp4", "avi", "rmvb",
        // pdf
        "pdf"
    };
    return ext;
}

bool FileUpload::isAllowedExtension(const std::string& extension, const std::vector<std::string>& allowed) {
    std::string ext = toLower(extension);
    for (const auto& a : allowed) {
        if (toLower(a) == ext) return true;
    }
    return false;
}

std::string FileUpload::sanitizeFilename(const std::string& filename) {
    std::string result;
    for (char c : filename) {
        // 去掉路径分隔符
        if (c == '/' || c == '\\') continue;
        // 只保留安全字符：字母、数字、下划线、连字符、点、中文
        if (std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '-' || c == '.' ||
            (static_cast<unsigned char>(c) >= 0x80)) {
            result.push_back(c);
        }
    }
    return result;
}

std::string FileUpload::datePath() {
    return cm::utils::DateUtils::dateTimeNow(cm::utils::DateUtils::YYYY_MM_DD);
}

std::string FileUpload::uniqueId() {
    return cm::utils::simpleUuid();
}

std::string FileUpload::getExtension(const std::string& fileName) {
    auto pos = fileName.rfind('.');
    if (pos == std::string::npos || pos + 1 >= fileName.size()) return "";
    return toLower(fileName.substr(pos + 1));
}

std::string FileUpload::getName(const std::string& fileName) {
    if (fileName.empty()) return "";
    auto posUnix = fileName.rfind('/');
    auto posWin = fileName.rfind('\\');
    size_t pos = std::string::npos;
    if (posUnix != std::string::npos && posWin != std::string::npos) {
        pos = std::max(posUnix, posWin);
    } else if (posUnix != std::string::npos) {
        pos = posUnix;
    } else if (posWin != std::string::npos) {
        pos = posWin;
    }
    if (pos == std::string::npos) return fileName;
    return fileName.substr(pos + 1);
}

std::string FileUpload::upload(const std::string& baseDir,
                                const std::string& originalFilename,
                                const std::string& contentType,
                                const std::string& data,
                                const std::vector<std::string>& allowedExtension) {
    auto& cfg = cm::config::AppConfig::instance();

    // 检查文件大小
    if (data.size() > static_cast<size_t>(cfg.maxFileSize)) {
        throw cm::exception::FileSizeLimitExceededException(cfg.maxFileSize / 1024 / 1024);
    }

    // 检查文件名长度
    if (originalFilename.size() > 100) {
        throw cm::exception::FileNameLengthLimitExceededException(100);
    }

    // 获取扩展名
    std::string extension = getExtension(originalFilename);
    if (extension.empty() && !contentType.empty()) {
        // 从 Content-Type 推断扩展名
        if (contentType.find("image/png") != std::string::npos) extension = "png";
        else if (contentType.find("image/jpeg") != std::string::npos) extension = "jpg";
        else if (contentType.find("image/gif") != std::string::npos) extension = "gif";
        else if (contentType.find("image/bmp") != std::string::npos) extension = "bmp";
    }

    // 检查扩展名白名单
    if (!isAllowedExtension(extension, allowedExtension)) {
        throw cm::exception::InvalidExtensionException(extension, cm::utils::StringUtils::join(allowedExtension, ","));
    }

    // 消毒文件名
    std::string safeName = sanitizeFilename(originalFilename);
    if (safeName.empty()) safeName = "file";

    // 生成新文件名：datePath/uuid.extension
    std::string newFileName = datePath() + "/" + uniqueId() + "." + extension;

    // 构造完整路径
    std::filesystem::path absPath = std::filesystem::path(baseDir) / newFileName;

    // 路径穿越防护
    std::string absStr = absPath.string();
    std::string baseStr = std::filesystem::path(baseDir).string();
    if (absStr.find(baseStr) != 0) {
        throw cm::exception::FileException("文件路径非法");
    }

    // 创建目录
    std::filesystem::create_directories(absPath.parent_path());

    // 写入文件
    std::ofstream out(absPath, std::ios::binary);
    if (!out) {
        throw cm::exception::FileException("无法创建文件: " + absStr);
    }
    out.write(data.data(), static_cast<std::streamsize>(data.size()));
    out.close();

    // 返回 /profile/... 形式的 URL
    // Java: Constants.RESOURCE_PREFIX + "/" + currentDir + "/" + fileName
    // currentDir = upload 子目录（baseDir 去掉 profile 前缀）
    std::string profile = cfg.profile;
    size_t dirLastIndex = profile.size() + 1;
    std::string currentDir;
    if (baseDir.size() > dirLastIndex) {
        currentDir = baseDir.substr(dirLastIndex);
    }
    return std::string(cm::constant::Constants::RESOURCE_PREFIX) + "/" + currentDir + "/" + newFileName;
}

bool FileUpload::checkAllowDownload(const std::string& resource) {
    // 禁止目录上跳级别
    if (resource.find("..") != std::string::npos) {
        return false;
    }

    // 检查允许下载的文件规则
    std::string extension = getExtension(resource);
    return isAllowedExtension(extension, defaultAllowedExtension());
}

std::string FileUpload::percentEncode(const std::string& s) {
    return cm::http::HttpRequest::urlEncode(s);
}

} // namespace cm::framework::web
