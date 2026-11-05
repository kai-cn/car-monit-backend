// HenDa 签名算法的单测：把那个"累加量翻倍"的 bug 逐字钉住。
// 参照值由 scripts/henda_sig_ref.py（Python 独立实现）算出，不是拿本实现自证。
#include "cm/common/utils/EncryptUtils.hpp"

#include <string>

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                            \
    do {                                                                       \
        auto _va = (a);                                                        \
        auto _vb = (b);                                                        \
        if (!(_va == _vb)) {                                                   \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                           \
        }                                                                      \
    } while (0)

using cm::crypto::createSignature;
using cm::crypto::getCiphertext;
using cm::crypto::signatureSource;

static const char* kAppid = "YHZS";
static const char* kSecret = "b48381c4b98311ea90b100155d14fa3b";

static void testSignatureSource() {
    const std::string src = signatureSource(kAppid, "20130524080000", "1369353600000", kSecret,
                                           "1369353600000");
    // 4 段排序后是 nonce < timestamp < appid < secretKey，累加量逐轮翻倍
    CK_EQ(src, std::string(
        "13693536000001369353600000&2013052408000013693536000001369353600000&20130524080000&YHZS"
        "13693536000001369353600000&2013052408000013693536000001369353600000&20130524080000"
        "&YHZS&b48381c4b98311ea90b100155d14fa3b&1369353600000"));
    CK_EQ(src.size(), static_cast<size_t>(221));
    CK_EQ(createSignature(kAppid, "20130524080000", "1369353600000", kSecret, "1369353600000"),
          std::string("83855a3e59687cf3059eba5858694921"));
}

static void testDetails() {
    // getCiphertext 把 nonce 当 jsonStr 传进去
    CK_EQ(getCiphertext(kAppid, kSecret, "1369353600000", "20130524080000"),
          createSignature(kAppid, "20130524080000", "1369353600000", kSecret, "1369353600000"));
    // jsonStr 会先删掉所有换行与空格
    CK_EQ(signatureSource(kAppid, "20130524080000", "1369353600000", kSecret, " a\nb "),
          signatureSource(kAppid, "20130524080000", "1369353600000", kSecret, "ab"));
    // appid/timestamp/nonce 都会剥掉 '[' 与 ']'（对真实值是空操作，但排序用的是剥完之后的串）
    CK_EQ(signatureSource("[YHZS]", "20130524080000", "1369353600000", kSecret, "1369353600000"),
          signatureSource(kAppid, "20130524080000", "1369353600000", kSecret, "1369353600000"));
    // 签名是 32 位小写十六进制
    const std::string sig = createSignature(kAppid, "20231115093000", "1699999999999", kSecret,
                                            "1699999999999");
    CK_EQ(sig.size(), static_cast<size_t>(32));
    for (char c : sig) {
        CK((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'));
    }
}

void run_encrypt_utils_tests() {
    testSignatureSource();
    testDetails();
}
