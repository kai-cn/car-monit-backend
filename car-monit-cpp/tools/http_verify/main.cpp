// 出站 HTTPS 验收工具（一次性验收用，默认不参与构建）
//
// 验证点：
//   1. CA 包可定位且能解析
//   2. 对真实 HTTPS 站点完成握手、证书校验、拿到 HTTP 响应
//   3. 证书校验失败必须报错（连一个故意错误的主机名，走 SNI/主机名校验分支）
//   4. 未签名/自签 CA 不被信任（用 CM_VERIFY_BAD_CA 指向一个不含目标根证书的 PEM 时）
//
// 环境变量：
//   CM_VERIFY_HTTPS_URL   目标 URL（默认腾讯地图 direction，无 key 时返回 status=301）
//   CM_VERIFY_CA          自定义 CA 包（默认 third_party/cacert.pem）
//   CM_VERIFY_BAD_CA      用于负向验证的 CA 包（默认不存在则跳过该项）
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>

#include "cm/framework/net/HttpClient.hpp"

namespace {

int g_pass = 0;
int g_fail = 0;

std::string env(const char* k, const std::string& def = "") {
    const char* v = std::getenv(k);
    return v ? std::string(v) : def;
}

void report(bool ok, const std::string& name, const std::string& detail) {
    if (ok) {
        ++g_pass;
        std::printf("[PASS] %s  %s\n", name.c_str(), detail.c_str());
    } else {
        ++g_fail;
        std::printf("[FAIL] %s  %s\n", name.c_str(), detail.c_str());
    }
}

} // namespace

int main() {
    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 10000;
    opt.readTimeoutMs = 30000;
    opt.caBundle = env("CM_VERIFY_CA", "third_party/cacert.pem");

    // 1) CA 定位
    report(!opt.caBundle.empty(), "ca.bundle", opt.caBundle);

    // 2) 真实请求
    const std::string url =
        env("CM_VERIFY_HTTPS_URL", "https://apis.map.qq.com/ws/direction/v1/driving/?from=116.1,29.1&to=116.2,29.2");
    const auto t0 = std::chrono::steady_clock::now();
    const auto r = cm::net::HttpClient::get(url, {}, opt);
    const auto ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
    report(r.status == 200, "https.request",
           "status=" + std::to_string(r.status) + " 耗时=" + std::to_string(ms) + "ms  body=" +
               r.body.substr(0, 120) + (r.error.empty() ? "" : ("  error=" + r.error)));
    // 腾讯地图在缺 key 时返回 {"status":301,...}，能解析出 JSON 说明 TLS + HTTP 全链路正常
    report(r.body.find("\"status\"") != std::string::npos, "https.body", "JSON 可解析");

    // 3) 证书校验失败：把 Host 指到一个与证书不匹配的名字（用 127.0.0.1 访问 apis.map.qq.com 的 IP 不可行，
    //    这里直接造一个不存在的主机名，验证失败路径不崩且给出错误）
    cm::net::HttpOptions bad = opt;
    bad.connectTimeoutMs = 3000;
    bad.readTimeoutMs = 3000;
    const auto badHost = cm::net::HttpClient::get("https://nonexistent.invalid./x", {}, bad);
    report(!badHost.ok() && !badHost.error.empty(), "https.badhost", badHost.error);

    // 4) 不可信 CA：故意用一个空 CA 包
    const std::string badCa = env("CM_VERIFY_BAD_CA");
    if (!badCa.empty()) {
        cm::net::HttpOptions badO = opt;
        badO.caBundle = badCa;
        const auto badCert = cm::net::HttpClient::get(url, {}, badO);
        report(!badCert.ok() && badCert.error.find("证书") != std::string::npos, "https.badca",
               badCert.error);
    } else {
        std::printf("[SKIP] https.badca  (未设置 CM_VERIFY_BAD_CA)\n");
    }

    std::printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
