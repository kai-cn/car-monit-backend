#pragma once
// S3/MinIO 对象存储客户端（AWS Signature V4，零第三方依赖）。
//
// 对应 Java: com.ruoyi.common.utils.http.OssTemplate
//   AmazonS3Client.builder().withEndpointConfiguration(...)
//     .withCredentials(...).disableChunkedEncoding()
//     .withPathStyleAccessEnabled(ossProperties.getPathStyleAccess())   // 默认 true
// ⇒ 路径风格 http://<endpoint>/<bucket>/<key>，SigV4，普通 Content-Length（不是 aws-chunked）。
//
// 配置来自 application.yml 的 oss.endpoint / oss.accessKey / oss.secretKey / oss.bucketName；
// 没有 oss.region ⇒ SDK 落到默认区域，MinIO 端只要签名里区域自洽就不校验它，
// 所以这里同样用空区域以外的固定值参与签名（见 kDefaultRegion 的注释）。
#include <string>
#include <utility>
#include <vector>

#include "cm/framework/net/HttpClient.hpp"

namespace cm::net::s3 {

/** Java 侧 oss.region 未配置；AWS SDK 会用 "us-east-1" 作为默认区域参与签名，
 *  MinIO 忽略其值但要求 credential scope 自洽。 */
inline constexpr const char* kDefaultRegion = "us-east-1";

struct Config {
    std::string endpoint;      ///< "http://172.30.100.102:9002"（不含末尾 /）
    std::string accessKey;
    std::string secretKey;
    std::string region{kDefaultRegion};
};

/** AWS SigV4 的 URI 编码：S3 的 path 里 '/' 不编码，其余非 unreserved 字符编成大写十六进制 */
std::string uriEncodePath(const std::string& raw);
std::string uriEncodeQuery(const std::string& raw);

struct SignInput {
    std::string method;
    std::string canonicalUri;     ///< 已按 uriEncodePath 编码，以 / 开头
    std::string canonicalQuery;   ///< 已排序已编码，不含 '?'；没有就空串
    std::string payloadHash;      ///< sha256(body) 的小写十六进制
    std::string amzDate;          ///< 20130524T000000Z
    std::string dateStamp;        ///< 20130524
    std::string region;
    std::string accessKey;
    std::string secretKey;
    /** 参与签名的首部，键必须是小写（host / x-amz-* / content-type / range …） */
    std::vector<std::pair<std::string, std::string>> headers;
};

std::string canonicalRequestOf(const SignInput& in);
std::string stringToSignOf(const SignInput& in, const std::string& canonicalRequest);
std::string signingKey(const std::string& secret, const std::string& dateStamp,
                       const std::string& region);
/** 返回完整的 Authorization 头值 */
std::string authorization(const SignInput& in);

struct Result {
    bool ok{false};
    int status{0};
    std::string error;        ///< 非空即失败（对应 Java 抛出的 AmazonClientException 文本）
    std::string body;         ///< getObject 用
    std::string contentType;

    bool is2xx() const { return status >= 200 && status < 300; }
};

/** PUT Object：Content-Type 照抄 OssTemplate —— 恒为 application/octet-stream */
Result putObject(const Config& cfg, const std::string& bucket, const std::string& key,
                 const std::string& body, long long timeoutMs = 60000);
/** GET Object */
Result getObject(const Config& cfg, const std::string& bucket, const std::string& key,
                 long long timeoutMs = 60000);
/** DELETE Object */
Result deleteObject(const Config& cfg, const std::string& bucket, const std::string& key,
                   long long timeoutMs = 60000);

/** 供单测注入时间：返回 (amzDate, dateStamp) */
std::pair<std::string, std::string> amzTimestamp(long long epochSeconds);

} // namespace cm::net::s3
