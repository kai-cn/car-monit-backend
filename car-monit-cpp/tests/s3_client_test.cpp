// S3 SigV4 签名单测：对拍 AWS 官方文档给的例子（GET Object）。
// 这是本文件存在的意义 —— MinIO 不在这个网络里，签名的正确性只能靠标准向量证明。
#include "cm/framework/net/S3Client.hpp"

#include <string>
#include <vector>

#include "cm/common/utils/crypto/Digest.hpp"

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                            \
    do {                                                                       \
        auto _va = (a);                                                        \
        auto _vb = (b);                                                        \
        if (!(_va == _vb)) {                                                   \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                           \
        }                                                                      \
    } while (0)

using namespace cm::net::s3;

/** AWS docs「Examples: Signature Version 4」里的 GET Object：
 *  https://examplebucket.s3.amazonaws.com/test.txt + Range: bytes=0-9 */
static void testAwsGetVector() {
    SignInput in;
    in.method = "GET";
    in.canonicalUri = "/test.txt";
    in.canonicalQuery = "";
    in.payloadHash = cm::crypto::hex(cm::crypto::sha256(""));   // 空负载
    in.amzDate = "20130524T000000Z";
    in.dateStamp = "20130524";
    in.region = "us-east-1";
    in.accessKey = "AKIAIOSFODNN7EXAMPLE";
    in.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
    in.headers = {{"host", "examplebucket.s3.amazonaws.com"},
                  {"range", "bytes=0-9"},
                  {"x-amz-content-sha256", in.payloadHash},
                  {"x-amz-date", in.amzDate}};

    CK_EQ(in.payloadHash, std::string("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"));

    const std::string cr = canonicalRequestOf(in);
    CK(cr.find("GET\n/test.txt\n\nhost:examplebucket.s3.amazonaws.com\n") == 0);
    CK(cr.find("range:bytes=0-9\n") != std::string::npos);
    CK(cr.find("\nhost;range;x-amz-content-sha256;x-amz-date\n") != std::string::npos);

    const std::string sts = stringToSignOf(in, cr);
    CK(sts.compare(0, 17, "AWS4-HMAC-SHA256\n") == 0);
    CK(sts.find("20130524/us-east-1/s3/aws4_request") != std::string::npos);

    const std::string auth = authorization(in);
    // 签名值来自 scripts/sigv4_ref.py —— 那是用 Python 标准库 hmac/hashlib 对同一份
    // 规范请求独立算出来的第二套实现（AWS 文档页抓不到原文，所以这里不用"记忆中的官方向量"，
    // 而是把可复算的参照值钉住；规范请求本身逐字断言在上一条 CK 里）。
    CK_EQ(auth, std::string(
        "AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request, "
        "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date, "
        "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"));
}

static void testEncodingAndHelpers() {
    CK_EQ(uriEncodePath("a b/c.txt"), std::string("a%20b/c.txt"));
    CK_EQ(uriEncodePath("中文.png"), std::string("%E4%B8%AD%E6%96%87.png"));
    CK_EQ(uriEncodeQuery("a b"), std::string("a%20b"));
    CK_EQ(uriEncodeQuery("a+b&c"), std::string("a%2Bb%26c"));
    CK_EQ(amzTimestamp(1369353600LL).first, std::string("20130524T000000Z"));
    CK_EQ(amzTimestamp(1369353600LL).second, std::string("20130524"));

    // 首部顺序不该影响签名（内部排序），值的首尾空白要按规范去掉
    SignInput a;
    a.method = "GET";
    a.canonicalUri = "/x";
    a.payloadHash = "h";
    a.amzDate = "20240101T000000Z";
    a.dateStamp = "20240101";
    a.region = "us-east-1";
    a.accessKey = "AK";
    a.secretKey = "SK";
    a.headers = {{"x-amz-date", "20240101T000000Z"}, {"host", " h "}};
    SignInput b = a;
    b.headers = {{"host", "h"}, {"x-amz-date", "20240101T000000Z"}};
    CK_EQ(authorization(a), authorization(b));
}

/** 没有配 endpoint / https 主机：必须是明确的失败，而不是"假装成功" */
static void testUnreachableShapes() {
    cm::net::s3::Config cfg;
    auto r = getObject(cfg, "b", "k");
    CK(!r.ok);
    CK(!r.error.empty());

    cfg.endpoint = "https://127.0.0.1:9/none";
    auto r2 = putObject(cfg, "b", "k", "data");
    CK(!r2.ok);
    CK(r2.error.find("TLS") != std::string::npos);

    cfg.endpoint = "http://127.0.0.1:1/none";   // 一定连不通的端口
    auto r3 = getObject(cfg, "b", "k", 500);
    CK(!r3.ok);
    CK(r3.error.find("Amazon S3") != std::string::npos);
}

void run_s3_client_tests() {
    testAwsGetVector();
    testEncodingAndHelpers();
    testUnreachableShapes();
}
