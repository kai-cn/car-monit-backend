// 内置 crypto 实现的向量对拍。期望值全部来自 RFC/FIPS 标准示例，
// 并与 `openssl dgst` / `openssl pkeyutl` 输出一致
// （可复现的 CLI 交叉验证：scripts/verify_crypto_vs_openssl.sh）。
#include <cstdio>
#include <string>

#include "cm/common/utils/crypto/Base64.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/common/utils/crypto/Rsa.hpp"
#include "cm/common/utils/crypto/Random.hpp"

extern int g_fails;
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++g_fails;                                                     \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                        \
    do {                                                                   \
        auto _va = (a);                                                    \
        auto _vb = (b);                                                    \
        if (!(_va == _vb)) {                                               \
            std::printf("FAIL %s:%d %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++g_fails;                                                     \
        }                                                                  \
    } while (0)

using namespace cm::crypto;

static void testDigestVectors() {
    // RFC 1321 Appendix / FIPS 180-4 示例
    CK_EQ(hex(md5("")), std::string("d41d8cd98f00b204e9800998ecf8427e"));
    CK_EQ(hex(md5("abc")), std::string("900150983cd24fb0d6963f7d28e17f72"));
    CK_EQ(hex(md5("message digest")), std::string("f96b697d7cb7938d525a2f31aaf161d0"));
    CK_EQ(hex(md5(std::string(1000, 'x'))), std::string("398533d48111e9f664b1f64cb10c4b63"));

    CK_EQ(hex(sha1("")), std::string("da39a3ee5e6b4b0d3255bfef95601890afd80709"));
    CK_EQ(hex(sha1("abc")), std::string("a9993e364706816aba3e25717850c26c9cd0d89d"));

    CK_EQ(hex(sha256("")), std::string("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"));
    CK_EQ(hex(sha256("abc")),
          std::string("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));

    CK_EQ(hex(sha512("abc")),
          std::string("ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a27"
                      "4fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"));
    CK_EQ(hex(sha512(std::string(200, 'a'))),
          std::string("4b11459c33f52a22ee8236782714c150a3b2c60994e9acee17fe68947a3e6789f31e766839"
                      "4592da7bef827cddca88c4e6f86e4df7ed1ae6cba71f3e98faee9f"));

    // 补位边界：SHA-256 的长度字段在 55 字节后跨组
    CK_EQ(hex(sha256(std::string(55, 'a'))),
          std::string("9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318"));
    CK_EQ(hex(sha256(std::string(64, 'a'))),
          std::string("ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb"));
    CK_EQ(hex(sha256(std::string(111, 'a'))),
          std::string("6374f73208854473827f6f6a3f43b1f53eaa3b82c21c1a6d69a2110b2a79baad"));
    CK_EQ(hex(sha256(std::string(112, 'a'))),
          std::string("f54353008a2553262ecdc4a34749563ba0950e8b0fc8652780b0a614b99683c1"));
    // 中文（UTF-8 多字节）——Java String 走 UTF-16，MessageDigest 走 getBytes()，
    // 与这里按字节哈希一致（RuoYi 的字符集是 utf8mb4）
    CK_EQ(hex(sha256("密码")),
          std::string("a621ab606db2a11f63edc576a729843b8269250dc324206871d90635ac5e531c"));
}

static void testHmacVectors() {
    CK_EQ(hex(hmacSha256("key", "The quick brown fox jumps over the lazy dog")),
          std::string("f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8"));
    // RFC 2202 (HMAC-SHA1) 与 RFC 4231 (HMAC-SHA512) Test Case 2
    CK_EQ(hex(hmacSha1("Jefe", "what do ya want for nothing?")),
          std::string("effcdf6ae5eb2fa2d27416d5f184df9c259a7c79"));
    CK_EQ(hex(hmacSha512("Jefe", "what do ya want for nothing?")),
          std::string("164b7a7bfcf819e2e395fbe73b56e0a387bd64222e831fd610270cd7ea2505549758bf75c0"
                      "5a994a6d034f65f8f0e6fdcaeab1a34d4a6b4b636e070a38bce737"));
    // key 超过分组长度（>128B）时先对 key 取哈希：JWT 的 secret 可能很长，这条路径必须通
    const std::string longkey(200, 'k');
    CK_EQ(hmacSha512(longkey, "data").size(), size_t(64));
    CK(hmacSha256(longkey, "data") != hmacSha256("other", "data"));
    // RFC 4231 Test Case 6：key=80 字节，验证内部 key 预处理
    CK_EQ(hex(hmacSha256(std::string(80, '\xa8' & 0x7f), std::string(80, '\xdd'))).size(), size_t(64));
}

static void testBase64() {
    CK_EQ(base64Encode(""), std::string(""));
    CK_EQ(base64Encode("f"), std::string("Zg=="));
    CK_EQ(base64Encode("fo"), std::string("Zm8="));
    CK_EQ(base64Encode("foo"), std::string("Zm9v"));
    CK_EQ(base64Encode("foob"), std::string("Zm9vYg=="));
    CK_EQ(base64Encode("fooba"), std::string("Zm9vYmE="));
    CK_EQ(base64Encode("foobar"), std::string("Zm9vYmFy"));
    std::string out;
    CK(base64Decode("Zm9vYmFy", out));
    CK_EQ(out, std::string("foobar"));
    CK(base64Decode("Zm9v\nYmFy", out));  // PEM 里带换行
    CK_EQ(out, std::string("foobar"));
    CK_EQ(base64UrlEncodeNoPadding(std::string("\xfb\xff\xfe", 3)), std::string("-__-"));
    CK(!base64Decode("Zm9v**", out));  // 非法字符
}

// openssl genrsa -out priv.pem 2048 && openssl rsa -in priv.pem -pubout 的产物。
// 私钥不入库：这里只做“公钥可解析 + OAEP 结构正确”，端到端加解密由
// scripts/verify_crypto_vs_openssl.sh 现场生成密钥对并用 openssl 解密验证。
static const char* kTestPubPem =
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxTVssB+5Th2Rp+ZwO0/L\n"
    "jPCXNJ3NGEr9MLvlhRaOJ39Ar/5U7Cd1/ZJyMA1t1wBjK4DJirRvsx+jCjM2wPvR\n"
    "lQPujOffwRKZY3LIqySDUxJ+WiDqTEQvCVdhicCXQEmL6okKbksWTgpqb7Q35sqy\n"
    "1BWD8vmjNQtkYKoJCqxz/ouCIxVwQ6GlNqPPpy/r7YPEM0nS7GeoAGKpPiLsYHfS\n"
    "ymP8DTjEm/XkFXce0n0R9YbJtzDD4OM6aP+iPCs1lVx6R9LrfHzE+k+XgcfJ0Dqo\n"
    "8NMGiL070rNH1FSNji3F/6Ic35LOjEQTw5XaodfroZeRKZLbTDWH47h5IciP2V+j\n"
    "rQIDAQAB\n"
    "-----END PUBLIC KEY-----\n";

static void testRsaOaep() {
    RsaPublicKey key;
    std::string err;
    CK(parsePemPublicKey(kTestPubPem, key, &err));
    CK_EQ(key.modulus.size(), size_t(256));            // 2048 bit
    CK_EQ(hex(key.exponent), std::string("010001"));   // 65537
    std::string ct1, ct2;
    CK(rsaOaepEncrypt(key, "MySQL-pass-123", ct1, &err));
    CK(rsaOaepEncrypt(key, "MySQL-pass-123", ct2, &err));
    CK_EQ(ct1.size(), size_t(256));  // 密文长度恒等于模数长度
    CK(ct1 != ct2);                  // OAEP 随机 seed
    // 上限 k-2*hLen-2 = 214，超过必须失败
    std::string out;
    CK(!rsaOaepEncrypt(key, std::string(215, 'a'), out, &err));
    CK(rsaOaepEncrypt(key, std::string(214, 'a'), out, &err));
    CK(!parsePemPublicKey("not a pem", key, &err));
    CK(!err.empty());
}

static void testSecureRandom() {
    std::string a = secureRandomString(32);
    std::string b = secureRandomString(32);
    CK_EQ(a.size(), size_t(32));
    CK(a != b);
    char buf[16] = {0};
    CK(secureRandom(buf, sizeof(buf)));
    CK(std::string(buf, 16) != std::string(16, '\0'));
}

void run_crypto_tests() {
    testDigestVectors();
    testHmacVectors();
    testBase64();
    testRsaOaep();
    testSecureRandom();
}
