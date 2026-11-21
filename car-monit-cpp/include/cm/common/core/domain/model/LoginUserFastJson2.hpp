#pragma once
// fastjson2 WriteClassName 兼容序列化（只用于 Redis `login_tokens:*`）
//
// 为什么单独一层：
//   Java 侧 RedisConfig 给 valueSerializer 用的是
//     new FastJson2JsonRedisSerializer(Object.class)
//   serialize = JSON.toJSONString(t, JSONWriter.Feature.WriteClassName)
//   deserialize = JSON.parseObject(str, Object.class, AUTO_TYPE_FILTER)
//   目标类型是 Object ⇒ 文本里没有 `@type` 时反序列化得到 JSONObject，
//   随后 TokenService 的 `LoginUser user = redisCache.getCacheObject(key)`
//   在 checkcast 处抛 ClassCastException（HTTP 200 + code:500）。
//
// 因此 C++ 写登录态时必须复刻 fastjson2 的写出形态，包括几处非常规细节：
//   * `@type` 置顶，其余键按属性名字母序（不是字段声明序）；
//   * null 整个键省略；primitive（int/boolean）与默认值 0/false 照写；
//   * 根对象的 boxed Long 不带 `L`，嵌套对象里的 Long 带 `L`（实测行为）；
//   * Set 写成 `Set["a","b"]`，List 写成 `[...]`；
//   * Date 写成 "yyyy-MM-dd HH:mm:ss"（不是 ISO，也不是毫秒）；
//   * BaseEntity.params 非 null 时整体写出，空 Map 也带 `{"@type":"java.util.HashMap"}`。
//
// golden 与生成脚本：tests/golden/login_user_fastjson2.json
//   由真实 ruoyi-common 编译产物 + fastjson2 2.0.43 生成，单测逐字节比对。
#include <string>

#include "cm/common/core/domain/model/LoginUser.hpp"

namespace cm::domain {

/** 与 Java FastJson2JsonRedisSerializer.serialize(WriteClassName) 逐字节一致的文本 */
std::string loginUserToFastJson2(const LoginUser& u);

/** 把 fastjson2 的非标准文本规范化为标准 JSON：
 *  - 去掉数字后缀 `L`（`103L` -> `103`）
 *  - `Set[` / `Set []` -> `[`
 *  - 其余（含 `@type`）原样保留，解析后忽略未知键
 *  只处理引号外的文本，字符串里的字面 `L` / `Set[` 不受影响。
 */
std::string fastJson2ToJson(const std::string& text);

/** 读 Java 写的登录态文本（内部先规范化再解析） */
LoginUser loginUserFromFastJson2(const std::string& text);

} // namespace cm::domain
