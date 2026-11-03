#pragma once
// 对应 Java: com.alibaba.fastjson2.JSON#parseObject —— 读取 Redis 里由 Java 侧
// FastJson2JsonRedisSerializer 写入的缓存值。
//
// Java 侧 RedisConfig 打开 JSONWriter.Feature.WriteClassName 后，写出的字符串并不是
// 严格 JSON，而是 fastjson2 的类型标注扩展语法：
//   "permissions":Set["*:*:*"]        —— 集合带类型前缀
//   "deptId":25367L                   —— Long 后缀 L（Float 为 F、Double 为 D）
//   "params":{"@type":"java.util.HashMap",...}
// Jackson 根本读不了这种值（只有 fastjson2 能），而 C++ 侧必须读——否则 Java 创建的登录会话
// 在 C++ 里会解析失败并表现为 401。这里把上述扩展降级成严格 JSON，再交给 nlohmann。
//
// ⚠️ 只用于“读 Java 写过的缓存值”，请求体解析仍走严格 cm::parse_json，
//    这样 Java 会拒绝的非法入参，C++ 同样拒绝。
#include <string>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::utils {

/** 去掉 fastjson2 的类型前缀与数值后缀，返回严格 JSON 文本 */
std::string normalizeFastJson2(const std::string& text);

/** normalizeFastJson2 + Json::parse；解析失败抛 JsonParseException（与 parse_json 一致） */
Json parse_cached_json(const std::string& text);

} // namespace cm::utils
