#include "cm/common/utils/JsonUtils.hpp"

#include "cm/common/exception/Exceptions.hpp"

namespace cm {

Json parse_json(const std::string& text) {
    // ⚠️ 用非抛异常的 Json::accept 预检，再交给 Json::parse。
    // 原因：在 MSVC Release 构建里，nlohmann 对"空输入/非法 JSON"的异常路径实测会触发
    // __fastfail（0xC0000409），try/catch 拦不住、整个进程直接退出。
    // accept() 走 SAX 解析，失败只返回 false，不存在这条路径。
    if (text.empty() || !Json::accept(text)) {
        throw exception::JsonParseException(
            "JSON parse error: invalid or empty JSON input; nested exception is "
            "com.fasterxml.jackson.core.JsonParseException: Unrecognized token");
    }
    return Json::parse(text);  // accept 已确认合法
}

} // namespace cm
