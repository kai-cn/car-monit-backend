#pragma once
// Base64 / Base64URL 编解码。
//
// 对应 Java: java.util.Base64.getEncoder()/getUrlEncoder()、
//           commons-codec Base64、RuoYi 的 Base64Utils。
//
// 与 Spring 的差别见 COMPATIBILITY.md：Jackson 对 byte[] 字段固定用**标准** Base64
// （带 + / 和 = 填充），验证码接口返回的也是标准 Base64，不要用 URL 安全变体。
#include <string>
#include <string_view>

namespace cm::crypto {

/** 标准 Base64，含 '=' 填充（等价 Java Base64.getEncoder()） */
std::string base64Encode(std::string_view data);
/** 标准 Base64 解码；遇到非法字符返回 false。填充可缺省（宽松，兼容 URL 变体输入） */
bool base64Decode(std::string_view text, std::string& out);

/** URL-safe Base64，无填充（JWT 用，等价 Java Base64.getUrlEncoder().withoutPadding()） */
std::string base64UrlEncodeNoPadding(std::string_view data);
bool base64UrlDecode(std::string_view text, std::string& out);

} // namespace cm::crypto
