#pragma once
// 对应 Java: com.ruoyi.common.core.domain.AjaxResult
//
// ⚠️ 这是整个迁移里最容易“看起来一样、字节不一样”的地方。
//    Java 侧 `AjaxResult extends HashMap<String,Object>`，Jackson 按 **HashMap 桶序** 输出，
//    不是插入序。真实响应是 {"msg":...,"code":...,...}。
//    C++ 侧用 ordered_json + 桶序重排复刻该行为（见 sortByHashMapOrder）。
#include <string>
#include <vector>

#include "cm/common/constant/HttpStatus.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::core::domain {

class AjaxResult {
public:
    static constexpr const char* CODE_TAG = "code";
    static constexpr const char* MSG_TAG = "msg";
    static constexpr const char* DATA_TAG = "data";

    AjaxResult();
    AjaxResult(int code, const std::string& msg);
    AjaxResult(int code, const std::string& msg, const Json& data);

    static AjaxResult success();
    /** Java 重载 success(String msg)：返回体只有 msg/code（参数被当作提示语） */
    static AjaxResult success(const std::string& msg);
    static AjaxResult success(const char* msg);
    /** Java 重载 success(Object data)：非字符串入参 */
    static AjaxResult success(const Json& data);
    static AjaxResult success(const std::string& msg, const Json& data);

    static AjaxResult warn(const std::string& msg);
    static AjaxResult warn(const std::string& msg, const Json& data);

    static AjaxResult error();
    static AjaxResult error(const std::string& msg);
    static AjaxResult error(const char* msg);
    static AjaxResult error(const std::string& msg, const Json& data);
    static AjaxResult error(int code, const std::string& msg);

    bool isSuccess() const;
    bool isWarn() const;
    bool isError() const;

    /** 链式 put（对应 Java 覆写后的 AjaxResult put） */
    AjaxResult& put(const std::string& key, const Json& value);
    AjaxResult& put(const std::string& key, const std::string& value);
    AjaxResult& put(const std::string& key, const char* value);
    AjaxResult& put(const std::string& key, long long value);
    AjaxResult& put(const std::string& key, int value);
    AjaxResult& put(const std::string& key, bool value);

    bool has(const std::string& key) const { return obj_.contains(key); }
    Json get(const std::string& key) const;
    const Json& raw() const { return obj_; }
    Json& raw() { return obj_; }
    int code() const { return code_; }

    /** 按 Java HashMap 桶序重排后的 JSON 对象 */
    Json toJson() const;
    std::string dump() const;

    /** 计算 Java String#hashCode（UTF-16 语义） */
    static int javaStringHash(const std::string& s);
    /** 计算 HashMap 桶号（capacity 默认 16） */
    static int bucketIndex(const std::string& key, int capacity = 16);
    /** 把 keys 按 HashMap 迭代序排序 */
    static std::vector<std::string> hashMapOrder(const std::vector<std::string>& keys);

private:
    Json obj_;
    int code_{0};
};

} // namespace cm::core::domain
