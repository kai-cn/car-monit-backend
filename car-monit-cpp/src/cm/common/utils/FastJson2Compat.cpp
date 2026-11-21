#include "cm/common/utils/FastJson2Compat.hpp"

#include <cctype>
#include <string>
#include <string_view>

namespace cm::utils {
namespace {

bool isIdentStart(char c) {
    return std::isalpha(static_cast<unsigned char>(c)) || c == '_' || c == '$';
}
bool isIdentChar(char c) {
    return std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '$';
}
/** true/false/null 是合法 JSON 字面量，不能当成类型前缀丢掉 */
bool isJsonLiteral(std::string_view w) {
    return w == "true" || w == "false" || w == "null";
}
bool isValueSep(char c) { return c == ',' || c == ']' || c == '}' || c == ':'; }

} // namespace

std::string normalizeFastJson2(const std::string& text) {
    std::string out;
    out.reserve(text.size());
    bool inString = false;
    const size_t n = text.size();
    size_t i = 0;
    while (i < n) {
        char c = text[i];
        if (inString) {
            out.push_back(c);
            if (c == '\\' && i + 1 < n) {
                out.push_back(text[i + 1]);
                i += 2;
                continue;
            }
            if (c == '"') inString = false;
            ++i;
            continue;
        }
        if (c == '"') {
            inString = true;
            out.push_back(c);
            ++i;
            continue;
        }
        if (isIdentStart(c)) {
            size_t j = i;
            while (j < n && isIdentChar(text[j])) ++j;
            std::string_view word(text.data() + i, j - i);
            if (!isJsonLiteral(word) && j < n && (text[j] == '[' || text[j] == '{')) {
                // Set["a"] / ArrayList[1] / JSONObject{"a":1} —— 丢类型前缀，保留容器
                out.push_back(text[j]);
                i = j + 1;
                continue;
            }
            out.append(word);
            i = j;
            continue;
        }
        if (std::isdigit(static_cast<unsigned char>(c)) || c == '-') {
            size_t j = i + 1;
            while (j < n && (std::isdigit(static_cast<unsigned char>(text[j])) || text[j] == '.' ||
                             text[j] == 'e' || text[j] == 'E' || text[j] == '+' || text[j] == '-')) {
                ++j;
            }
            // 1L / 1.5F / 1.5D：后缀只有紧跟值分隔符时才算数，避免误吃 true 之类的字母
            bool typed = false;
            if (j < n && (text[j] == 'L' || text[j] == 'F' || text[j] == 'D')) {
                size_t k = j + 1;
                while (k < n && std::isspace(static_cast<unsigned char>(text[k]))) ++k;
                typed = (k >= n || isValueSep(text[k]));
            }
            out.append(text.data() + i, j - i);  // 只写数字本体
            if (typed) ++j;                      // 类型后缀丢弃
            i = j;
            continue;
        }
        out.push_back(c);
        ++i;
    }
    return out;
}

Json parse_cached_json(const std::string& text) { return parse_json(normalizeFastJson2(text)); }

} // namespace cm::utils
