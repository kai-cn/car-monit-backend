#include "cm/framework/security/Jwt.hpp"

#include "cm/common/utils/crypto/Digest.hpp"

#include <cctype>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::security {
namespace {

const char* kB64Url = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

int b64Value(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+' || c == '-') return 62;
    if (c == '/' || c == '_') return 63;
    return -1;
}

} // namespace

Jwt::Jwt(std::string base64Secret) {
    auto decoded = decodeJavaBase64(base64Secret);
    key_ = decoded.value_or(base64Secret);
}

std::string Jwt::base64UrlEncode(const std::string& in) {
    std::string out;
    out.reserve((in.size() + 2) / 3 * 4);
    size_t i = 0;
    while (i + 2 < in.size()) {
        unsigned v = (static_cast<unsigned char>(in[i]) << 16) |
                     (static_cast<unsigned char>(in[i + 1]) << 8) |
                     static_cast<unsigned char>(in[i + 2]);
        out.push_back(kB64Url[(v >> 18) & 63]);
        out.push_back(kB64Url[(v >> 12) & 63]);
        out.push_back(kB64Url[(v >> 6) & 63]);
        out.push_back(kB64Url[v & 63]);
        i += 3;
    }
    size_t rem = in.size() - i;
    if (rem == 1) {
        unsigned v = static_cast<unsigned char>(in[i]) << 16;
        out.push_back(kB64Url[(v >> 18) & 63]);
        out.push_back(kB64Url[(v >> 12) & 63]);
    } else if (rem == 2) {
        unsigned v = (static_cast<unsigned char>(in[i]) << 16) |
                     (static_cast<unsigned char>(in[i + 1]) << 8);
        out.push_back(kB64Url[(v >> 18) & 63]);
        out.push_back(kB64Url[(v >> 12) & 63]);
        out.push_back(kB64Url[(v >> 6) & 63]);
    }
    return out;
}

std::optional<std::string> Jwt::base64UrlDecode(const std::string& in) {
    std::vector<int> vals;
    vals.reserve(in.size());
    size_t chars = 0;
    for (char c : in) {
        if (c == '=' || std::isspace(static_cast<unsigned char>(c))) continue;
        int v = b64Value(c);
        if (v < 0) return std::nullopt;
        vals.push_back(v);
        ++chars;
    }
    size_t rem = chars % 4;
    std::string out;
    for (size_t i = 0; i < vals.size(); i += 4) {
        size_t n = std::min<size_t>(4, vals.size() - i);
        unsigned v = static_cast<unsigned>(vals[i]) << 18;
        if (n > 1) v |= static_cast<unsigned>(vals[i + 1]) << 12;
        if (n > 2) v |= static_cast<unsigned>(vals[i + 2]) << 6;
        if (n > 3) v |= static_cast<unsigned>(vals[i + 3]);
        out.push_back(static_cast<char>((v >> 16) & 0xff));
        if (n > 2) out.push_back(static_cast<char>((v >> 8) & 0xff));
        if (n > 3) out.push_back(static_cast<char>(v & 0xff));
    }
    (void)rem;
    return out;
}

std::optional<std::string> Jwt::decodeJavaBase64(const std::string& in) {
    std::vector<int> vals;
    bool padded = false;
    for (char c : in) {
        unsigned char u = static_cast<unsigned char>(c);
        if (std::isspace(u)) continue;
        if (c == '=') {
            padded = true;
            break;
        }
        int v = b64Value(c);
        if (v < 0) return std::nullopt;
        vals.push_back(v);
    }
    size_t usable = padded ? (vals.size() / 4) * 4 : (vals.size() / 4) * 4;
    if (padded) {
        // 有填充时，JAXB 会把最后不完整组按已有字符补零输出
        usable = vals.size();
    }
    std::string out;
    for (size_t i = 0; i < usable; i += 4) {
        size_t n = std::min<size_t>(4, usable - i);
        unsigned v = (static_cast<unsigned>(vals[i]) << 18);
        if (n > 1) v |= static_cast<unsigned>(vals[i + 1]) << 12;
        if (n > 2) v |= static_cast<unsigned>(vals[i + 2]) << 6;
        if (n > 3) v |= static_cast<unsigned>(vals[i + 3]);
        out.push_back(static_cast<char>((v >> 16) & 0xff));
        if (n > 2) out.push_back(static_cast<char>((v >> 8) & 0xff));
        if (n > 3) out.push_back(static_cast<char>(v & 0xff));
    }
    if (out.empty() && !vals.empty()) return std::nullopt;
    return out;
}

std::string Jwt::hmacSha512(const std::string& data, const std::string& key) {
    // 对应 Java: Mac.getInstance("HmacSHA512") + SecretKeySpec(key)
    return cm::crypto::hmacSha512(key, data);
}

std::string Jwt::createToken(const std::string& loginUserKey) const {
    std::string header = R"({"alg":"HS512"})";
    Json payload = Json::object();
    payload["login_user_key"] = loginUserKey;
    std::string body = base64UrlEncode(header) + "." + base64UrlEncode(payload.dump());
    std::string sig = base64UrlEncode(hmacSha512(body, key_));
    return body + "." + sig;
}

std::optional<std::string> Jwt::parsePayload(const std::string& token) const {
    size_t d1 = token.find('.');
    if (d1 == std::string::npos) return std::nullopt;
    size_t d2 = token.find('.', d1 + 1);
    if (d2 == std::string::npos) return std::nullopt;
    std::string signingInput = token.substr(0, d2);
    std::string sig = token.substr(d2 + 1);
    auto decodedSig = base64UrlDecode(sig);
    if (!decodedSig) return std::nullopt;
    std::string expected = hmacSha512(signingInput, key_);
    if (expected.size() != decodedSig->size()) return std::nullopt;
    // 恒定时间比较，避免签名校验的时序侧信道（等价 MessageDigest.isEqual）
    unsigned char diff = 0;
    for (size_t i = 0; i < expected.size(); ++i) {
        diff |= static_cast<unsigned char>(expected[i] ^ (*decodedSig)[i]);
    }
    if (diff != 0) return std::nullopt;
    auto payload = base64UrlDecode(token.substr(d1 + 1, d2 - d1 - 1));
    if (!payload) return std::nullopt;
    return payload;
}

std::optional<std::string> Jwt::parseLoginUserKey(const std::string& token) const {
    auto payload = parsePayload(token);
    if (!payload) return std::nullopt;
    try {
        Json j = Json::parse(*payload);
        if (j.contains("login_user_key") && j["login_user_key"].is_string()) {
            return j["login_user_key"].get<std::string>();
        }
    } catch (...) {
    }
    return std::nullopt;
}

std::optional<std::string> Jwt::parseSubject(const std::string& token) const {
    auto payload = parsePayload(token);
    if (!payload) return std::nullopt;
    try {
        Json j = Json::parse(*payload);
        if (j.contains("sub") && j["sub"].is_string()) return j["sub"].get<std::string>();
    } catch (...) {
    }
    return std::nullopt;
}

} // namespace cm::security
