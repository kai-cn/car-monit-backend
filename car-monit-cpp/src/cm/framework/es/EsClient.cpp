#include "cm/framework/es/EsClient.hpp"

#include "cm/common/utils/Logger.hpp"
#include "cm/framework/net/HttpClient.hpp"

namespace cm::es {

EsClient& EsClient::instance() {
    static EsClient c;
    return c;
}

void EsClient::configure(const EsConfig& cfg) { cfg_ = cfg; }

std::string EsClient::baseUrl() const {
    return "http://" + cfg_.host + ":" + std::to_string(cfg_.port);
}

bool EsClient::ping() {
    if (!cfg_.enabled) return false;
    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 3000;
    opt.readTimeoutMs = 3000;
    opt.maxRetryCount = 0;
    const auto r = cm::net::HttpClient::get(baseUrl() + "/", {}, opt);
    return r.error.empty() && r.status == 200;
}

bool EsClient::bulkIndex(const std::vector<std::pair<std::string, std::string>>& docs,
                         std::string& err) {
    if (!cfg_.enabled) {
        err = "ES 未启用";
        return false;
    }
    if (docs.empty()) return true;

    std::string body;
    body.reserve(docs.size() * 512);
    for (const auto& d : docs) {
        // 对应 IndexRequest(index).id(bigId)：_index/_id 用 JSON 转义，避免车牌等字段里的引号
        body += "{\"index\":{\"_index\":";
        body += Json(cfg_.index).dump();
        body += ",\"_id\":";
        body += Json(d.first).dump();
        body += "}}\n";
        body += d.second;
        body += "\n";
    }

    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 3000;
    opt.readTimeoutMs = cfg_.timeoutMs;
    opt.maxRetryCount = 0;  // 写操作不重放
    const auto r = cm::net::HttpClient::post(baseUrl() + "/_bulk", body,
                                             "application/x-ndjson; charset=UTF-8", {}, opt);
    if (!r.error.empty()) {
        err = "ES bulk 传输失败: " + r.error;
        return false;
    }
    if (r.status < 200 || r.status >= 300) {
        err = "ES bulk HTTP " + std::to_string(r.status) + ": " + r.body.substr(0, 300);
        return false;
    }
    // BulkResponse.hasFailures()
    if (Json::accept(r.body)) {
        const Json resp = Json::parse(r.body);
        if (resp.contains("errors") && resp["errors"].is_boolean() && resp["errors"].get<bool>()) {
            err = "ES bulk 存在失败项";
            return false;
        }
    }
    return true;
}

bool EsClient::search(const Json& body, Json& out, std::string& err) {
    if (!cfg_.enabled) {
        err = "ES 未启用";
        return false;
    }
    cm::net::HttpOptions opt;
    opt.connectTimeoutMs = 3000;
    opt.readTimeoutMs = cfg_.timeoutMs;
    opt.maxRetryCount = 1;
    const auto r = cm::net::HttpClient::post(
        baseUrl() + "/" + cfg_.index + "/_search", body.dump(),
        "application/json; charset=UTF-8", {}, opt);
    if (!r.error.empty()) {
        err = "ES 查询传输失败: " + r.error;
        return false;
    }
    if (r.status < 200 || r.status >= 300) {
        err = "ES 查询 HTTP " + std::to_string(r.status) + ": " + r.body.substr(0, 300);
        return false;
    }
    if (!Json::accept(r.body)) {
        err = "ES 查询响应不是合法 JSON";
        return false;
    }
    out = Json::parse(r.body);
    return true;
}

} // namespace cm::es
