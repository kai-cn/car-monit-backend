#pragma once
// 对应 Java: com.ruoyi.common.utils.file.FileUploadUtils + FileUtils
//
// 文件上传/下载工具类。实现与 Java 版本一致的安全检查：
//   - 文件名消毒（去掉路径分隔符、限制字符集）
//   - 扩展名白名单
//   - 文件大小限制（默认 40MB，与 AppConfig.maxFileSize 一致）
//   - 日期子目录（yyyy/MM/dd）
//   - 路径穿越防护（禁止 ".."）
#include <string>
#include <vector>

namespace cm::framework::web {

class FileUpload {
public:
    /** 默认允许上传的扩展名（对应 MimeTypeUtils.DEFAULT_ALLOWED_EXTENSION） */
    static const std::vector<std::string>& defaultAllowedExtension();

    /** 上传单个文件，返回 /profile/upload/... 形式的 URL */
    static std::string upload(const std::string& baseDir,
                              const std::string& originalFilename,
                              const std::string& contentType,
                              const std::string& data,
                              const std::vector<std::string>& allowedExtension = defaultAllowedExtension());

    /** 检查文件是否允许下载（禁止 ".." + 扩展名白名单） */
    static bool checkAllowDownload(const std::string& resource);

    /** 从完整路径中提取文件名（去掉目录部分） */
    static std::string getName(const std::string& fileName);

    /** 获取文件扩展名（小写，不含点） */
    static std::string getExtension(const std::string& fileName);

    /** 生成日期子目录路径（yyyy/MM/dd） */
    static std::string datePath();

    /** 生成唯一文件名（对应 IdUtils.fastSimpleUUID） */
    static std::string uniqueId();

    /** 对下载文件名进行 URL 编码（对应 FileUtils.percentEncode） */
    static std::string percentEncode(const std::string& s);

private:
    /** 检查扩展名是否在白名单内 */
    static bool isAllowedExtension(const std::string& extension, const std::vector<std::string>& allowed);

    /** 消毒文件名：去掉路径分隔符，只保留安全字符 */
    static std::string sanitizeFilename(const std::string& filename);
};

} // namespace cm::framework::web
