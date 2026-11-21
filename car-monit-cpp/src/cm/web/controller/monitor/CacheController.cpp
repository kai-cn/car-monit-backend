// 对应 Java: com.ruoyi.web.controller.monitor.CacheController
#include "cm/web/controller/monitor/CacheController.hpp"

#include <map>
#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {

namespace {

/** 解析 Redis INFO 输出为 key-value 对 */
std::map<std::string, std::string> parseRedisInfo(const std::vector<std::string>& lines) {
    std::map<std::string, std::string> info;
    for (const auto& line : lines) {
        if (line.empty() || line[0] == '#' || line[0] == '\r') continue;
        auto pos = line.find(':');
        if (pos != std::string::npos) {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            // 去掉末尾的 \r
            if (!value.empty() && value.back() == '\r') value.pop_back();
            info[key] = value;
        }
    }
    return info;
}

} // namespace

void registerCacheController(Router& r) {
    // GET /monitor/cache
    r.get("/monitor/cache", [](RequestContext&) -> cm::http::ApiResponse {
        auto& client = cm::redis::RedisCache::instance().client();

        // Java: redisTemplate.execute((RedisCallback<Object>) connection -> connection.info())
        auto infoLines = client.info();
        auto commandStatsLines = client.info("commandstats");
        long long dbSize = client.dbsize();

        // 构造返回结果
        Json result = Json::object();

        // info
        Json infoJson = Json::object();
        auto infoMap = parseRedisInfo(infoLines);
        for (const auto& [k, v] : infoMap) {
            infoJson[k] = v;
        }
        result["info"] = infoJson;

        // dbSize
        result["dbSize"] = dbSize;

        // commandStats -> pieList
        Json pieList = Json::array();
        auto cmdMap = parseRedisInfo(commandStatsLines);
        for (const auto& [key, property] : cmdMap) {
            // Java: StringUtils.removeStart(key, "cmdstat_")
            std::string name = key;
            if (cm::utils::StringUtils::startsWith(name, "cmdstat_")) {
                name = name.substr(8);
            }
            // Java: StringUtils.substringBetween(property, "calls=", ",usec")
            std::string value;
            auto callsPos = property.find("calls=");
            auto usecPos = property.find(",usec");
            if (callsPos != std::string::npos && usecPos != std::string::npos && callsPos < usecPos) {
                value = property.substr(callsPos + 6, usecPos - callsPos - 6);
            }
            Json item = Json::object();
            item["name"] = name;
            item["value"] = value;
            pieList.push_back(item);
        }
        result["commandStats"] = pieList;

        auto a = BaseController::success(result);
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/getNames
    r.get("/monitor/cache/getNames", [](RequestContext&) -> cm::http::ApiResponse {
        auto& client = cm::redis::RedisCache::instance().client();
        auto keys = client.keys("*");

        // 提取 cache names（key 的第一段，以 : 分隔）
        std::vector<std::string> names;
        for (const auto& key : keys) {
            auto pos = key.find(':');
            if (pos != std::string::npos) {
                std::string name = key.substr(0, pos);
                if (std::find(names.begin(), names.end(), name) == names.end()) {
                    names.push_back(name);
                }
            }
        }

        auto a = BaseController::success(Json(names));
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/getKeys/{cacheName}
    r.get("/monitor/cache/getKeys/{cacheName}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string cacheName = ctx.pathVar("cacheName");
        auto& client = cm::redis::RedisCache::instance().client();
        auto keys = client.keys(cacheName + ":*");

        auto a = BaseController::success(Json(keys));
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/getValue/{cacheName}/{cacheKey}
    r.get("/monitor/cache/getValue/{cacheName}/{cacheKey}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string cacheName = ctx.pathVar("cacheName");
        std::string cacheKey = ctx.pathVar("cacheKey");
        std::string fullKey = cacheName + ":" + cacheKey;

        auto& cache = cm::redis::RedisCache::instance();
        auto value = cache.get(fullKey);

        Json result = Json::object();
        result["key"] = fullKey;
        result["value"] = value ? Json(*value) : Json(nullptr);

        auto a = BaseController::success(result);
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/clearCacheName/{cacheName}
    r.get("/monitor/cache/clearCacheName/{cacheName}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string cacheName = ctx.pathVar("cacheName");
        auto& client = cm::redis::RedisCache::instance().client();
        auto keys = client.keys(cacheName + ":*");

        if (!keys.empty()) {
            client.del(keys);
        }

        auto a = BaseController::success();
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/clearCacheKey/{cacheName}/{cacheKey}
    r.get("/monitor/cache/clearCacheKey/{cacheName}/{cacheKey}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string cacheName = ctx.pathVar("cacheName");
        std::string cacheKey = ctx.pathVar("cacheKey");
        std::string fullKey = cacheName + ":" + cacheKey;

        auto& cache = cm::redis::RedisCache::instance();
        cache.del(fullKey);

        auto a = BaseController::success();
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");

    // GET /monitor/cache/clearCacheAll
    r.get("/monitor/cache/clearCacheAll", [](RequestContext&) -> cm::http::ApiResponse {
        auto& client = cm::redis::RedisCache::instance().client();
        client.flushdb();

        auto a = BaseController::success();
        return cm::http::ApiResponse::json(a.toJson());
    }).permi("monitor:cache:list");
}

} // namespace cm::web
