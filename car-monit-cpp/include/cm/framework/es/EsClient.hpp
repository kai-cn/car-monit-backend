#pragma once
// 最小 Elasticsearch REST 客户端（对应 Java RestHighLevelClient 在本工程用到的子集）。
//
// Java 侧只用到三件事（SnapshotFlowElasticsearchService）：
//   1. bulk 批量索引（IndexRequest.id(bigId).source(JSON)）
//   2. 单条 saveOrUpdate（同一个 bulk，1 条）
//   3. searchPage：bool + wildcard/term/range + sort + from/size
// 所以这里实现 /_bulk、/{index}/_search、GET / 三个端点，HTTP 走现有的 HttpClient。
#include <string>
#include <utility>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::es {

struct EsConfig {
    bool enabled{false};
    std::string host{"127.0.0.1"};
    int port{9200};
    std::string index{"snapshot-flow"};
    int timeoutMs{30000};
};

class EsClient {
public:
    static EsClient& instance();

    void configure(const EsConfig& cfg);
    bool enabled() const { return cfg_.enabled; }
    const EsConfig& config() const { return cfg_; }

    /** 对应 RestHighLevelClient.ping() */
    bool ping();
    /** 批量索引。[{id, json}]，json 是文档原文（fastjson2 形态） */
    bool bulkIndex(const std::vector<std::pair<std::string, std::string>>& docs, std::string& err);
    /** 执行查询 DSL，返回完整响应 JSON（调用方取 hits.hits[]._source） */
    bool search(const Json& body, Json& out, std::string& err);

private:
    EsClient() = default;
    std::string baseUrl() const;

    EsConfig cfg_;
};

} // namespace cm::es
