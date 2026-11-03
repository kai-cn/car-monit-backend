// 对应 Java: com.ruoyi.web.controller.base.CdcController
//            + com.ruoyi.base.service.cdc.{DeadLetterQueueService,CdcSyncService,CdcConfig,CdcMessage}
//
// 语义要点（逐条对着 Java 源码抄）：
//   * 队列数据只在 Redis：key 前缀 cdc:retry:（重试队列）/ cdc:dead:（死信队列），
//     value 是 fastjson2 序列化的 CdcMessage。RedisTemplate.keys(prefix + "*") 返回 HashSet，
//     因此消息列表顺序 = HashSet 迭代顺序（桶序），不是字典序。
//   * CdcSyncService.processCdcMessage 里三个 handleXxx 的 ES 调用在 Java 源码中已被注释掉，
//     所以只要 operationType 是合法枚举就一定返回 true；operationType 为 null 时
//     switch(null) 抛 NPE 被 catch → 返回 false。
//   * CdcConfig 没有任何 yml 覆盖（application.yml 里不存在 cdc: 段），
//     因此 /base/cdc/config 返回的就是 @Data 字段的默认值。
#include "cm/web/controller/base/CdcController.hpp"

#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::redis::RedisCache;

const std::string kRetryPrefix = "cdc:retry:";
const std::string kDeadPrefix = "cdc:dead:";

/** CdcMessage 字段声明序（Jackson 对 POJO 按声明序输出，null 字段照输出） */
const std::vector<std::string> kMessageFields = {
    "operationType", "sourceName", "database",   "table",
    "beforeData",    "afterData",  "timestamp",  "messageId",
    "retryCount"};

/** OdsRtSzdnSnapshotFlowAddcode 字段声明序（beforeData / afterData 的嵌套结构） */
const std::vector<std::string> kDataFields = {
    "bigId",          "datasource",       "cameratype",     "deviceid",
    "gantrycode",     "gantryname",       "roadcode",       "roadname",
    "sectioncode",    "sectionname",      "tollcode",       "tollname",
    "orgcode",        "orgname",          "direction",      "hexcode",
    "pileno",         "lon",              "lat",            "deviceip",
    "siteid",         "laneid",           "snapshottimeunix", "snapshottime",
    "receivedtimeunix", "receivedtime",   "platenumber",    "platecolor",
    "platecolorcode", "platetype",        "platetypecode",  "plateconfidence",
    "carbrand",       "carcolor",         "carcolorcode",   "cartype",
    "cartypecode",    "cardirection",     "snappicturepath", "loadtime",
    "gradelevel",     "datauuid",         "reserve3"};

Json pick(const Json& raw, const std::string& key) {
    if (!raw.is_object()) return Json(nullptr);
    auto it = raw.find(key);
    return it == raw.end() ? Json(nullptr) : *it;
}

/** 按声明序重排，缺失字段补 null（对应 Jackson 的 ALWAYS 包含策略） */
Json reorder(const Json& raw, const std::vector<std::string>& order, const Json& dflt) {
    Json out = Json::object();
    for (const auto& k : order) {
        auto v = pick(raw, k);
        out[k] = v.is_null() ? dflt : v;
    }
    // Java 不会输出实体之外的键，但 fastjson2 的 @type 之类的元数据要丢掉
    return out;
}

Json dataToJson(const Json& raw) {
    if (raw.is_null() || !raw.is_object()) return Json(nullptr);
    return reorder(raw, kDataFields, Json(nullptr));
}

/** Redis value → CdcMessage（Jackson 视角的响应体） */
Json messageToJson(const Json& raw) {
    Json m = Json::object();
    for (const auto& k : kMessageFields) m[k] = Json(nullptr);
    m["operationType"] = pick(raw, "operationType");
    m["sourceName"] = pick(raw, "sourceName");
    m["database"] = pick(raw, "database");
    m["table"] = pick(raw, "table");
    m["beforeData"] = dataToJson(pick(raw, "beforeData"));
    m["afterData"] = dataToJson(pick(raw, "afterData"));
    m["timestamp"] = pick(raw, "timestamp");
    m["messageId"] = pick(raw, "messageId");
    // int retryCount：缺省 0，不是 null
    auto rc = pick(raw, "retryCount");
    m["retryCount"] = rc.is_number() ? rc : Json(0);
    return m;
}

struct QueueEntry {
    std::string key;
    Json raw;
};

/** 对应 DeadLetterQueueService.get{DeadLetter,Retry}Messages()：keys → HashSet 序 → 逐条 get + 解析 */
std::vector<QueueEntry> loadMessages(const std::string& prefix) {
    std::vector<QueueEntry> out;
    auto keys = RedisCache::instance().keys(prefix + "*");
    if (keys.empty()) return out;
    keys = utils::javaSetOrder(keys);
    for (const auto& key : keys) {
        auto value = RedisCache::instance().get(key);
        if (!value) continue;  // Java: value == null → null → filter 掉
        Json raw;
        try {
            raw = cm::utils::parse_cached_json(*value);
        } catch (const std::exception&) {
            continue;  // Java: JSON.parseObject 抛异常 → log.error → null → filter 掉
        }
        if (!raw.is_object()) continue;
        out.push_back({key, std::move(raw)});
    }
    return out;
}

Json messageArray(const std::vector<QueueEntry>& entries) {
    Json arr = Json::array();
    for (const auto& e : entries) arr.push_back(messageToJson(e.raw));
    return arr;
}

long long queueSize(const std::string& prefix) {
    return static_cast<long long>(RedisCache::instance().keys(prefix + "*").size());
}

std::optional<std::string> messageIdOf(const Json& raw) {
    auto v = pick(raw, "messageId");
    if (v.is_null()) return std::nullopt;
    if (v.is_string()) return v.get<std::string>();
    return v.dump();
}

/** 对应 CdcSyncService.processCdcMessage：ES 调用在 Java 里已注释，合法枚举必成功 */
bool processMessage(const Json& raw) {
    auto type = pick(raw, "operationType");
    if (!type.is_string()) return false;  // switch(null) → NPE → catch → false
    const std::string t = type.get<std::string>();
    return t == "INSERT" || t == "UPDATE" || t == "DELETE";
}

void removeFromDeadLetterQueue(const std::string& messageId) {
    RedisCache::instance().del(kDeadPrefix + messageId);
}

/** 对应 CdcConfig 的 @Data 默认值（application.yml 无 cdc: 段，全部走字段初值） */
Json cdcConfigJson() {
    Json kafka = Json::object();
    kafka["bootstrapServers"] = "localhost:9092";
    kafka["consumerGroupId"] = "snapshot-flow-cdc-group";
    kafka["topic"] = "snapshot-flow-cdc";
    kafka["autoCommit"] = true;
    kafka["autoCommitInterval"] = 1000;
    kafka["sessionTimeout"] = 30000;
    kafka["concurrency"] = 3;

    Json esSync = Json::object();
    esSync["enabled"] = true;
    esSync["batchSize"] = 500;
    esSync["batchInterval"] = 5000;
    esSync["asyncThreads"] = 2;

    Json retry = Json::object();
    retry["maxAttempts"] = 3;
    retry["interval"] = 1000;
    retry["multiplier"] = 2.0;
    retry["maxInterval"] = 30000;

    Json cfg = Json::object();
    cfg["kafka"] = std::move(kafka);
    cfg["esSync"] = std::move(esSync);
    cfg["retry"] = std::move(retry);
    return cfg;
}

} // namespace

void registerCdcController(Router& r) {
    // GET /base/cdc/status —— new HashMap<>() 的 5 个键，Jackson 按桶序输出
    r.get("/base/cdc/status", [](RequestContext&) -> cm::http::ApiResponse {
        Json values = Json::object();
        values["retryQueueSize"] = queueSize(kRetryPrefix);
        values["deadLetterQueueSize"] = queueSize(kDeadPrefix);
        values["kafkaTopic"] = cdcConfigJson()["kafka"]["topic"];
        values["consumerGroupId"] = cdcConfigJson()["kafka"]["consumerGroupId"];
        values["maxRetryAttempts"] = cdcConfigJson()["retry"]["maxAttempts"];

        Json data = Json::object();
        for (const auto& k : utils::javaMapOrder({"retryQueueSize", "deadLetterQueueSize",
                                                 "kafkaTopic", "consumerGroupId",
                                                 "maxRetryAttempts"}))
            data[k] = values[k];
        return BaseController::ok(AjaxResult::success(data));
    });

    // GET /base/cdc/dead-letters
    r.get("/base/cdc/dead-letters", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(messageArray(loadMessages(kDeadPrefix))));
    });

    // GET /base/cdc/retry-messages
    r.get("/base/cdc/retry-messages", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(messageArray(loadMessages(kRetryPrefix))));
    });

    // POST /base/cdc/retry/{messageId}
    r.post("/base/cdc/retry/{messageId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const std::string id = ctx.pathVar("messageId");
        auto messages = loadMessages(kDeadPrefix);
        Json message = Json(nullptr);
        bool found = false;
        for (const auto& e : messages) {
            auto mid = messageIdOf(e.raw);
            if (!mid) {
                // Java: m.getMessageId().equals(...) 对 null 抛 NPE，整条请求 500
                throw cm::exception::NullPointerException();
            }
            if (*mid == id) {
                message = e.raw;
                found = true;
                break;
            }
        }
        if (!found) {
            return BaseController::ok(AjaxResult::error("重试失败，消息不存在或处理失败"));
        }
        if (!processMessage(message)) {
            return BaseController::ok(AjaxResult::error("重试失败，消息不存在或处理失败"));
        }
        removeFromDeadLetterQueue(id);
        return BaseController::ok(AjaxResult::success("重试成功"));
    });

    // POST /base/cdc/retry-all
    r.post("/base/cdc/retry-all", [](RequestContext&) -> cm::http::ApiResponse {
        auto messages = loadMessages(kDeadPrefix);
        int successCount = 0;
        for (const auto& e : messages) {
            if (!processMessage(e.raw)) continue;
            auto mid = messageIdOf(e.raw);
            if (!mid) throw cm::exception::NullPointerException();
            removeFromDeadLetterQueue(*mid);
            ++successCount;
        }
        return BaseController::ok(
            AjaxResult::success("批量重试完成，成功 " + std::to_string(successCount) + " 条"));
    });

    // DELETE /base/cdc/dead-letters/clear —— 必须先于 {messageId} 注册（Spring 取更精确的匹配）
    r.del("/base/cdc/dead-letters/clear", [](RequestContext&) -> cm::http::ApiResponse {
        for (const auto& e : loadMessages(kDeadPrefix)) {
            auto mid = messageIdOf(e.raw);
            if (!mid) continue;  // Java: 前缀 + null → 删 "cdc:dead:null"，实际不影响队列
            removeFromDeadLetterQueue(*mid);
        }
        return BaseController::ok(AjaxResult::success("已清空死信队列"));
    });

    // DELETE /base/cdc/dead-letters/{messageId}
    r.del("/base/cdc/dead-letters/{messageId}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        removeFromDeadLetterQueue(ctx.pathVar("messageId"));
        return BaseController::ok(AjaxResult::success("删除成功"));
    });

    // GET /base/cdc/config
    r.get("/base/cdc/config", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(AjaxResult::success(cdcConfigJson()));
    });
}

} // namespace cm::web
