#pragma once
// 对应 Java: io.jsonwebtoken (jjwt) 0.9.1 的 HS512 签发/校验
//
// ⚠️ 关键差异：jjwt 的 `signWith(alg, String secret)` 与 `setSigningKey(String)`
//    都会把字符串当成 **Base64** 解码后作为 HMAC key（JAXB DatatypeConverter）。
//    默认 secret "abcdefghijklmnopqrstuvwxyz" 因此只有 18 字节，而不是 26 字节。
//    为了与存量 Java 令牌互通，这里必须复刻同一套解码逻辑。
#include <optional>
#include <string>

namespace cm::security {

class Jwt {
public:
    explicit Jwt(std::string base64Secret);

    /** 对应 Jwts.builder().setClaims({"login_user_key":uuid}).signWith(HS512,secret).compact() */
    std::string createToken(const std::string& loginUserKey) const;
    /** 对应 Jwts.parser().setSigningKey(secret).parseClaimsJws(token).getBody().get("login_user_key") */
    std::optional<std::string> parseLoginUserKey(const std::string& token) const;
    /** 对应 getUsernameFromToken：读取 sub */
    std::optional<std::string> parseSubject(const std::string& token) const;

    static std::string base64UrlEncode(const std::string& in);
    static std::optional<std::string> base64UrlDecode(const std::string& in);
    /** jjwt/JAXB 风格的 Base64 解码（无填充时丢弃不完整尾组） */
    static std::optional<std::string> decodeJavaBase64(const std::string& in);
    static std::string hmacSha512(const std::string& data, const std::string& key);

private:
    std::optional<std::string> parsePayload(const std::string& token) const;
    std::string key_;
};

} // namespace cm::security
