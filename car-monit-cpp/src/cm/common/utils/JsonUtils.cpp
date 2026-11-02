#include "cm/common/utils/JsonUtils.hpp"

#include "cm/common/exception/Exceptions.hpp"

namespace cm {

Json parse_json(const std::string& text) {
    try {
        return Json::parse(text);
    } catch (const std::exception& e) {
        // Java: JSON parse error: <Jackson 原始消息>
        throw exception::JsonParseException(
            std::string("JSON parse error: ") + e.what() +
            "; nested exception is com.fasterxml.jackson.core.JsonParseException: " + e.what());
    }
}

} // namespace cm
