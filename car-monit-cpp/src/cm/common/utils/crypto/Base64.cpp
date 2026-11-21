#include "cm/common/utils/crypto/Base64.hpp"

#include <cstdint>

namespace cm::crypto {
namespace {

constexpr char kStd[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
constexpr char kUrl[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

int valueOf(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+' || c == '-') return 62;
    if (c == '/' || c == '_') return 63;
    return -1;
}

template <const char* Table>
std::string encode(std::string_view data, bool padding) {
    std::string out;
    out.reserve((data.size() + 2) / 3 * 4);
    size_t i = 0;
    while (i + 3 <= data.size()) {
        const uint32_t v = (static_cast<unsigned char>(data[i]) << 16) |
                           (static_cast<unsigned char>(data[i + 1]) << 8) |
                           static_cast<unsigned char>(data[i + 2]);
        out.push_back(Table[(v >> 18) & 63]);
        out.push_back(Table[(v >> 12) & 63]);
        out.push_back(Table[(v >> 6) & 63]);
        out.push_back(Table[v & 63]);
        i += 3;
    }
    const size_t rest = data.size() - i;
    if (rest == 1) {
        const uint32_t v = static_cast<unsigned char>(data[i]) << 16;
        out.push_back(Table[(v >> 18) & 63]);
        out.push_back(Table[(v >> 12) & 63]);
        if (padding) {
            out.push_back('=');
            out.push_back('=');
        }
    } else if (rest == 2) {
        const uint32_t v = (static_cast<unsigned char>(data[i]) << 16) |
                           (static_cast<unsigned char>(data[i + 1]) << 8);
        out.push_back(Table[(v >> 18) & 63]);
        out.push_back(Table[(v >> 12) & 63]);
        out.push_back(Table[(v >> 6) & 63]);
        if (padding) out.push_back('=');
    }
    return out;
}

} // namespace

std::string base64Encode(std::string_view data) { return encode<kStd>(data, true); }

std::string base64UrlEncodeNoPadding(std::string_view data) {
    return encode<kUrl>(data, false);
}

bool base64Decode(std::string_view text, std::string& out) {
    out.clear();
    out.reserve(text.size() / 4 * 3 + 3);
    uint32_t buf = 0;
    int bits = 0;
    for (char c : text) {
        if (c == '=' || c == '\r' || c == '\n' || c == ' ' || c == '\t') continue;
        const int v = valueOf(c);
        if (v < 0) return false;
        buf = (buf << 6) | static_cast<uint32_t>(v);
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            out.push_back(static_cast<char>((buf >> bits) & 0xff));
        }
    }
    return true;
}

bool base64UrlDecode(std::string_view text, std::string& out) { return base64Decode(text, out); }

} // namespace cm::crypto
