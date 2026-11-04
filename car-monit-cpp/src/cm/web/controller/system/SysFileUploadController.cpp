// 对应 Java: com.ruoyi.web.controller.system.SysFileController 的 9 个上传/下载端点
//            + com.ruoyi.system.service.impl.SysFileServiceImpl + com.ruoyi.common.utils.http.OssTemplate
//
// 与 Java 的关键一致点（逐条来自源码，不是推测）：
//   * 对象名 = simpleUUID + "." + FileUtil.extName(originalFilename)，平铺在桶根，没有日期目录。
//     extName 取**最后一个** '.' 之后的部分，保留大小写；没有点/空名/以点结尾 → 空串。
//   * 扩展名白名单用 indexOf(...) > -1（**子串**匹配）而不是 equals，命中才写 sys_file 并 PUT；
//     未命中则 id=-1，不写库、不 PUT，但 map 照样返回（id 是字符串 "-1"）。
//   * 先写库后 PUT（uploadFiles/uploadSupplier/uploadPdf 的 PDF 分支），且 uploadFiles 没有
//     @Transactional ⇒ PUT 失败会留下"库里有行、桶里没对象"的孤儿行，这是 Java 的既有行为。
//   * 返回的 map 是 HashMap，键序按桶序 = bucketName,fileName,id,url（不是插入顺序）。
//   * GET /{bucket}/{fileName} 失败时**吞掉异常**：HTTP 200 + 空 body，而不是 404。
//     bucket 直接来自 URL，不做任何校验，所以跨桶读也照抄。
//   * uploadPdf 的非 PDF 分支只把原始字节写到本地 profile/upload/<uuid>/ 下，
//     既不入桶也不写库，返回的 map 少一个 id 键（Word 转 PDF 那整段在 Java 里被注释了）。
//   * uploadFileEnc 的方法体 100% 被注释掉 ⇒ 恒返回 data:[]，不加密、不碰存储。
//
// ⚠️ 与 Java 的不可避免差异（详见 COMPATIBILITY.md §5.4）：
//   * sys_file.id 是雪花值，逐次调用不可能与 Java 历史值相同；这里实现同一套雪花算法
//     （毫秒左移 22 | 数据中心 5 | 机器 5 | 序列 12），只保证"单调、19 位十进制、非自增"。
//   * S3 失败的 msg 文本来自我们自己的 HTTP 层，措辞与 AmazonSDK 不同（结构一致：HTTP 200 + code:500）。
//   * 没有 TLS：https 的 endpoint / uploadByUrl 的 https 源地址一律按传输层失败处理。
#include "cm/web/controller/system/SysFileUploadController.hpp"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <system_error>
#include <ctime>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/compat/Path.hpp"
#include "cm/common/utils/crypto/Base64.hpp"
#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/net/HttpClient.hpp"
#include "cm/framework/net/S3Client.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::utils::CommonUtil;
using cm::utils::StringUtils;
namespace fs = std::filesystem;

/** 对应 RuoYi 的 IdWorker.nextId()（雪花）。epoch 与 Java 侧不同也没关系：
 *  值本身不是接口契约，"19 位、单调递增、非数据库自增"才是。 */
long long nextSnowflakeId() {
    static const long long kTwepoch = 1288834974657LL;   // Java 雪花算法的起始时间
    static std::atomic<long long> last{0};
    static std::atomic<long long> seq{0};
    const long long ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                             std::chrono::system_clock::now().time_since_epoch())
                             .count();
    long long id = (ms - kTwepoch) << 22;
    const long long prev = last.exchange(ms);
    if (prev == ms) {
        id |= (seq.fetch_add(1) & 0xFFFLL);
    } else {
        seq.store(0);
    }
    return id;
}

/** 对应 hutool FileUtil.extName：最后一个点之后，保留大小写；空/无点/以点结尾 → "" */
std::string extName(const std::string& name) {
    const size_t dot = name.find_last_of('.');
    if (dot == std::string::npos || dot + 1 >= name.size()) return "";
    return name.substr(dot + 1);
}

/** 对应 fileLog / fileSupplierLog / fileLogId 的扩展名白名单（子串匹配，先小写）。
 *  fileLogId 那份多了一个 `ext.indexOf(".ppt")` —— ext 永远不含点，是死条件，
 *  但两处列表**都**不含裸 "ppt"，所以 .ppt 文件一律走 id=-1 分支。 */
bool extAllowed(const std::string& ext, bool withDeadPptDot) {
    if (ext.empty()) return false;
    std::string e = ext;
    for (auto& c : e) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    static const char* kAll[] = {"doc",  "docx", "pdf",  "xlsx", "xls", "pptx", "txt",
                                 "zip",  "rar",  "jpg",  "jpeg", "png", "gif",  "mp3",
                                 "mp4",  "flv",  "3gp"};
    for (const char* t : kAll) {
        if (e.find(t) != std::string::npos) return true;
    }
    if (withDeadPptDot && e.find(".ppt") != std::string::npos) return true;
    return false;
}

/** 白名单命中 ⇒ 落库并返回真实主键；否则返回 -1（不查库、不写库） */
long long saveFileRow(const std::string& key, const std::string& original, long long fileSize,
                      const std::string& bussName, long long forcedId, bool withDeadPptDot) {
    const std::string ext = extName(original);
    if (!extAllowed(ext, withDeadPptDot)) return -1;
    std::string e = ext;
    for (auto& c : e) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    const std::string uid = std::to_string(cm::security::SecurityUtils::getUserId());
    const long long id = forcedId != 0 ? forcedId : nextSnowflakeId();
    // insertSysFile 的列集合（<if test="X != null">）：buss_type / tenant_id 这些上传路径从不赋值
    std::string sql = "insert into sys_file (id, file_name, bucket_name, original, type, file_size,"
                      " create_user, create_time, update_user, update_time, del_flag";
    std::string vals = std::to_string(id) + ", " + Db::lit(key) + ", "
                       + Db::lit(cm::config::AppConfig::instance().ossBucketName) + ", "
                       + Db::lit(original) + ", " + Db::lit(e) + ", " + std::to_string(fileSize) + ", "
                       + Db::lit(uid) + ", sysdate(), " + Db::lit(uid) + ", sysdate(), '0'";
    if (!bussName.empty()) {
        sql += ", buss_name";
        vals += ", " + Db::lit(bussName);
    }
    sql += ") values (" + vals + ")";
    Db::instance().execute(sql);
    return id;
}

cm::net::s3::Config s3Config() {
    const auto& c = cm::config::AppConfig::instance();
    cm::net::s3::Config cfg;
    cfg.endpoint = c.ossEndpoint;
    cfg.accessKey = c.ossAccessKey;
    cfg.secretKey = c.ossSecretKey;
    cfg.region = "us-east-1";   // Java 没有配 oss.region，SDK 用默认区域参与签名
    return cfg;
}

/** HashMap 桶序：bucketName, fileName, id, url */
Json fileMap(const std::string& bucket, const std::string& key, const std::string* id) {
    Json m = Json::object();
    m["bucketName"] = Json(bucket);
    m["fileName"] = Json(key);
    if (id) m["id"] = Json(*id);
    m["url"] = Json("/system/file/" + bucket + "/" + key);
    return m;
}

/** 上传一组文件：Java 的 uploadFiles —— 先库后桶，PUT 失败即整体 error 并**丢弃已累积的 map** */
AjaxResult uploadFiles(const std::vector<cm::http::MultipartPart>& files,
                       const std::vector<std::string>* bussNames) {
    const auto cfg = s3Config();
    const std::string bucket = cfg.endpoint.empty() ? "" : cm::config::AppConfig::instance().ossBucketName;
    Json data = Json::array();
    for (size_t i = 0; i < files.size(); ++i) {
        const auto& f = files[i];
        std::string bussName;
        if (bussNames) {
            // Java: bussNames[i] 越界会抛 ArrayIndexOutOfBoundsException，且在 try 之外
            if (i >= bussNames->size())
                throw cm::exception::CustomException(
                    "Index " + std::to_string(i) + " out of bounds for length " +
                    std::to_string(bussNames->size()));
            bussName = (*bussNames)[i];
        }
        const std::string key = cm::utils::simpleUuid() + "." + extName(f.filename);
        const long long fileId =
            saveFileRow(key, f.filename, static_cast<long long>(f.data.size()), bussName, 0, false);
        const std::string idStr = std::to_string(fileId);
        data.push_back(fileMap(bucket, key, &idStr));
        if (fileId != -1) {
            auto r = cm::net::s3::putObject(cfg, bucket, key, f.data);
            if (!r.ok) {
                // 孤儿行：insertSysFile 已提交，这里不回滚（Java 同样没有事务）
                return AjaxResult::error(r.error.empty() ? "S3 put failed" : r.error);
            }
        }
    }
    return AjaxResult::success(data);
}

/** Java 那边是非 PDF 就直接 FileOutputStream 落盘：没有日期目录、没有扩展名白名单，
 *  所以不能复用 FileUpload::upload（两者都会改路径/拒绝扩展名）。 */
bool writeLocalFile(const std::string& path, const std::string& data, std::string* err) {
    std::error_code ec;
    const fs::path p(cm::compat::fsPath(path));
    fs::create_directories(p.parent_path(), ec);
    if (ec) {
        *err = "目录创建失败: " + ec.message();
        return false;
    }
    std::ofstream out(p, std::ios::binary | std::ios::trunc);
    if (!out) {
        *err = "文件打开失败: " + path;
        return false;
    }
    out.write(data.data(), static_cast<std::streamsize>(data.size()));
    out.close();
    if (!out) {
        *err = "写入中断: " + path;
        return false;
    }
    return true;
}

const cm::http::MultipartPart* findFiles(const RequestContext& ctx, const std::string& name,
                                         std::vector<cm::http::MultipartPart>& out) {
    for (const auto& p : ctx.req.parts) {
        if (p.name == name && p.isFile()) out.push_back(p);
    }
    return out.empty() ? nullptr : &out.front();
}

} // namespace

void registerSysFileUploadController(Router& r) {
    // POST /system/file/upload
    r.post("/system/file/upload", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::vector<cm::http::MultipartPart> files;
        findFiles(ctx, "files", files);
        if (files.empty())
            return BaseController::ok(AjaxResult::error(
                "Required MultipartFile[] parameter 'files' is not present"));
        return BaseController::ok(uploadFiles(files, nullptr));
    });

    // POST /system/file/uploadSupplier —— files 与 bussNames 按下标一一对应
    r.post("/system/file/uploadSupplier", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::vector<cm::http::MultipartPart> files;
        findFiles(ctx, "files", files);
        if (files.empty())
            return BaseController::ok(AjaxResult::error(
                "Required MultipartFile[] parameter 'files' is not present"));
        std::vector<std::string> bussNames = ctx.params("bussNames");
        return BaseController::ok(uploadFiles(files, &bussNames));
    });

    // POST /system/file/uploadPdf —— 只有小写 "pdf" 走桶，其余只落本地磁盘且少一个 id 键
    r.post("/system/file/uploadPdf", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto cfg = s3Config();
        const std::string bucket = cm::config::AppConfig::instance().ossBucketName;
        Json data = Json::array();
        std::vector<cm::http::MultipartPart> files;
        findFiles(ctx, "files", files);
        if (files.empty())
            return BaseController::ok(AjaxResult::error(
                "Required MultipartFile[] parameter 'files' is not present"));
        for (const auto& f : files) {
            const std::string ext = extName(f.filename);       // 这里的比较**不**忽略大小写
            const std::string key = cm::utils::simpleUuid() + "." + ext;
            if (ext == "pdf") {
                const long long fileId =
                    saveFileRow(key, f.filename, static_cast<long long>(f.data.size()), "", 0, false);
                const std::string idStr = std::to_string(fileId);
                data.push_back(fileMap(bucket, key, &idStr));
                if (fileId != -1) {
                    auto put = cm::net::s3::putObject(cfg, bucket, key, f.data);
                    if (!put.ok) return BaseController::ok(AjaxResult::error(put.error));
                }
                continue;
            }
            // Java: RuoYiConfig.getUploadPath() + "/" + uuid36（带横线），Word 转 PDF 整段被注释
            const std::string dir = cm::config::AppConfig::instance().profile + "/upload/" +
                                    cm::utils::uuid();
            std::string err;
            if (!writeLocalFile(dir + "/" + key, f.data, &err))
                return BaseController::ok(AjaxResult::error("写本地文件失败: " + err));
            data.push_back(fileMap(bucket, key, nullptr));   // 非 PDF：没有 id 键
        }
        return BaseController::ok(AjaxResult::success(data));
    });

    // POST /system/file/uploadFileEnc —— 方法体在 Java 里全是注释：恒空数组，不加密
    r.post("/system/file/uploadFileEnc", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(Json::array()));
    });

    // POST /system/file/uploadByUrl —— 失败被逐项吞掉，所以 data 可能比入参短
    r.post("/system/file/uploadByUrl", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto cfg = s3Config();
        const std::string bucket = cm::config::AppConfig::instance().ossBucketName;
        Json body = ctx.body();
        const Json* list = nullptr;
        if (body.is_object() && body.contains("list") && body["list"].is_array())
            list = &body["list"];
        else if (!body.is_object())
            return BaseController::ok(AjaxResult::error("null"));   // Java: list 为 null → NPE
        Json data = Json::array();
        if (!list) return BaseController::ok(AjaxResult::success(data));
        for (const auto& item : *list) {
            // Java: setFileName(CommonUtil.isNull(getFileName()) + ".jpg") —— 强加后缀
            const std::string name =
                CommonUtil::isNull(item.contains("fileName") && item["fileName"].is_string()
                                       ? item["fileName"].get<std::string>()
                                       : std::string()) +
                ".jpg";
            const std::string url =
                item.contains("url") && item["url"].is_string() ? item["url"].get<std::string>()
                                                                : std::string();
            if (StringUtils::isBlank(url)) continue;     // 空 url：静默跳过，无 map 无错误
            auto got = cm::net::HttpClient::get(url);
            if (!got.ok() || !got.is2xx()) continue;     // 取不到：catch 里的 return 被注释了
            const std::string key = cm::utils::simpleUuid() + "." + extName(name);
            const long long fileId =
                saveFileRow(key, name, static_cast<long long>(got.body.size()), "", 0, false);
            const std::string idStr = std::to_string(fileId);
            data.push_back(fileMap(bucket, key, &idStr));
            if (fileId != -1) {
                auto put = cm::net::s3::putObject(cfg, bucket, key, got.body);
                if (!put.ok) continue;                   // 同样吞掉
            }
        }
        return BaseController::ok(AjaxResult::success(data));
    });

    // POST /system/file/uploadFileId —— 客户端指定主键；先删旧行旧对象再插新的
    r.post("/system/file/uploadFileId", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto cfg = s3Config();
        const std::string bucket = cm::config::AppConfig::instance().ossBucketName;
        Json body = ctx.body();
        long long reqId = 0;
        bool hasId = false;
        if (body.is_object() && body.contains("id") && !body["id"].is_null()) {
            hasId = true;
            if (body["id"].is_number()) reqId = body["id"].get<long long>();
            else if (body["id"].is_string()) {
                try { reqId = std::stoll(body["id"].get<std::string>()); } catch (...) { reqId = 0; }
            }
        }
        // Java 里那个 "主键不能为空" 的 error 被构造出来又丢掉了（没有 return），照抄：继续往下走
        const std::string dataUrl =
            body.is_object() && body.contains("files") && body["files"].is_string()
                ? body["files"].get<std::string>() : std::string();
        const size_t comma = dataUrl.find(',');
        if (comma == std::string::npos)
            throw cm::exception::CustomException(
                "Index 1 out of bounds for length 1");     // Java: baseStrs[1] 越界
        const std::string header = dataUrl.substr(0, comma);         // data:image/png;base64
        const std::string mime = header.substr(0, header.find(';'));
        const std::string subtype = mime.find('/') == std::string::npos
                                        ? std::string()
                                        : mime.substr(mime.find('/') + 1);
        const long long millis = std::chrono::duration_cast<std::chrono::milliseconds>(
                                     std::chrono::system_clock::now().time_since_epoch())
                                     .count();
        // Java: currentTimeMillis() + (int) Math.random() * 10000 —— 强转优先级使那半截恒为 0
        const std::string original = std::to_string(millis) + "." + subtype;
        std::string bytes;
        // sun.misc.BASE64Decoder 是宽松解码：非法字符被跳过而不是抛异常，
        // 这里解不出来就当作空负载，让后面的白名单/PUT 去复现 Java 的结果
        cm::crypto::base64Decode(dataUrl.substr(comma + 1), bytes);
        const std::string key = cm::utils::simpleUuid() + "." + extName(original);

        cm::db::Transaction tx;
        Json data = Json::array();
        const std::string echoId = hasId ? std::to_string(reqId) : std::string("-1");
        data.push_back(fileMap(bucket, key, &echoId));
        if (!hasId) {
            // Java: fileId.equals(-1L) 对 null 解引用 → NPE → code:500
            return BaseController::ok(AjaxResult::error(
                "Cannot invoke \"Long.equals(Object)\" because \"fileId\" is null"));
        }
        const long long fileId =
            saveFileRow(key, original, static_cast<long long>(bytes.size()), "", reqId, true);
        if (fileId != -1) {
            // fileLogId 先按 id 删旧行（硬删）并 removeObject，两者都包在空 catch 里
            cm::db::Result old;
            Db::instance().query("select file_name from sys_file where id = " +
                                     std::to_string(reqId), old);
            if (!old.rows.empty()) {
                // 失败也不管：Java 把 removeObject + 硬删包在一个空 catch 里
                cm::net::s3::deleteObject(cfg, bucket, old.rows[0].str("file_name"));
                Db::instance().execute("delete from sys_file where id = " + std::to_string(reqId));
            }
            const std::string uid =
                std::to_string(cm::security::SecurityUtils::getUserId());
            const std::string ins =
                std::string("insert into sys_file (id, file_name, bucket_name, original, type,"
                            " file_size, create_user, create_time, update_user, update_time,"
                            " del_flag) values (") +
                std::to_string(reqId) + ", " + Db::lit(key) + ", " + Db::lit(bucket) + ", " +
                Db::lit(original) + ", " + Db::lit(subtype) + ", " +
                std::to_string(bytes.size()) + ", " + Db::lit(uid) + ", sysdate(), " +
                Db::lit(uid) + ", sysdate(), '0')";
            if (!Db::instance().execute(ins))
                return BaseController::ok(AjaxResult::error("插入 sys_file 失败"));
            auto put = cm::net::s3::putObject(cfg, bucket, key, bytes);
            if (!put.ok) {
                // @Transactional 回滚库（不调 commit 即回滚），
                // 但 removeObject 已经发生、回滚不了 —— Java 同样如此
                return BaseController::ok(AjaxResult::error(put.error));
            }
        }
        tx.commit();
        return BaseController::ok(AjaxResult::success(data));
    });

    // POST /system/file/uploadFile —— 小程序入口：字段名是单数 file，扩展名**区分大小写**
    r.post("/system/file/uploadFile", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const cm::http::MultipartPart* mu = nullptr;
        for (const auto& p : ctx.req.parts) {
            if (p.name == "file") { mu = &p; break; }
        }
        if (!mu) throw cm::exception::CustomException("null");   // Java: 数组里塞 null → NPE
        // Java 只有这条路径做 ISO-8859-1 → UTF-8 的补救；我们收到的 filename 已是 UTF-8
        const std::string ext = extName(mu->filename);
        auto hasAny = [&](std::initializer_list<const char*> ts) {
            for (const char* t : ts) {
                if (ext.find(t) != std::string::npos) return true;
            }
            return false;
        };
        if (ext.empty() || !hasAny({"jpg", "jpeg", "png", "gif"}))
            return BaseController::ok(AjaxResult::error("上传失败,请上传照片格式的附件！"));
        if (mu->data.size() > 1024ULL * 1024ULL * 15ULL)
            return BaseController::ok(AjaxResult::error("上传失败,你上传的附件大于15M！"));
        std::vector<cm::http::MultipartPart> one{*mu};
        return BaseController::ok(uploadFiles(one, nullptr));
    });

    // GET /system/file/view/{bucket}/{fileName} —— anonymous()：带 token 反而被容器级拒绝
    // GET /system/file/{bucket}/{fileName}      —— authenticated()
    // 两者是同一个 service 方法：失败一律 HTTP 200 + 空 body（异常被吞）
    auto getFile = [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string bucket = ctx.pathVar("bucket");
        const std::string key = ctx.pathVar("fileName");
        auto r = cm::net::s3::getObject(s3Config(), bucket, key);
        cm::http::ApiResponse resp;
        if (!r.ok) {
            resp.status = 200;
            resp.body.clear();           // 连 Content-Type 都不设：Java 的 setContentType 在调用之后
            return resp;
        }
        resp.status = 200;
        resp.content_type = "application/octet-stream; charset=UTF-8";
        resp.body = r.body;
        return resp;
    };
    r.get("/system/file/view/{bucket}/{fileName}", getFile).anonymous();
    r.get("/system/file/{bucket}/{fileName}", getFile);
}

} // namespace cm::web
