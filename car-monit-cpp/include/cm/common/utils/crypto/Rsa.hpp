#pragma once
// RSA 公钥加密（PKCS#1 v2.2 OAEP，MGF1 + SHA-1）。
//
// 为什么要有这个文件：MySQL 8 的 caching_sha2_password 在非 TLS 连接上，
// 服务端会用 RSA 公钥要求客户端把口令加密上去（full authentication）。
// Java 侧由 mysql-connector-j 内部完成（AllowPublicKeyRetrieval=true）；
// C++ 侧我们自带 MySQL 协议实现，所以必须自己实现 OAEP。
//
// 对应 Java: javax.crypto.Cipher.getInstance("RSA/ECB/OAEPWithSHA-1AndMGF1Padding")
//            以及 mysql-connector-j 内部的 RSAPublicKey 加密实现
#include <string>
#include <string_view>

namespace cm::crypto {

struct RsaPublicKey {
    std::string modulus;   ///< 大端字节序
    std::string exponent;  ///< 大端字节序
    int keyBytes() const { return static_cast<int>(modulus.size()); }
};

/** 解析 PEM 格式 SubjectPublicKeyInfo（"-----BEGIN PUBLIC KEY-----"） */
bool parsePemPublicKey(std::string_view pem, RsaPublicKey& out, std::string* err = nullptr);

/**
 * RSAES-OAEP(mgf1Hash=sha1, hash=sha1, label=空) 加密。
 * 输出长度恒等于模数长度，与 OpenSSL EVP_PKEY_encrypt(RSA_PKCS1_OAEP_PADDING) 一致。
 */
bool rsaOaepEncrypt(const RsaPublicKey& key, std::string_view plaintext, std::string& out,
                   std::string* err = nullptr);

/** 便捷版：PEM + 明文一步加密 */
bool rsaOaepEncryptPem(std::string_view pem, std::string_view plaintext, std::string& out,
                       std::string* err = nullptr);

} // namespace cm::crypto
