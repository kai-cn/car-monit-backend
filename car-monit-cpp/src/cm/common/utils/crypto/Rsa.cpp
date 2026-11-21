// RSA-OAEP(SHA-1, MGF1-SHA-1) + 密码学安全随机数 + SPKI/PEM 解析。
// 只实现“公钥加密”这一个方向：MySQL caching_sha2_password 的 full auth 用得到，
// 不需要签名/解密，所以私钥运算一概不做。
#include "cm/common/utils/crypto/Rsa.hpp"

#include <cstdint>
#include <cstring>
#include <vector>

#include "cm/common/utils/crypto/Base64.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/common/utils/crypto/Random.hpp"

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#else
#include <cerrno>
#include <fcntl.h>
#include <unistd.h>
#if defined(__linux__)
#include <sys/random.h>
#endif
#endif

namespace cm::crypto {

// ------------------------------------------------------------------ 随机数
bool secureRandom(void* out, size_t len) {
#ifdef _WIN32
    // advapi32 导出的 SystemFunction036 == RtlGenRandom：Windows 侧最稳妥的 CSPRNG。
    // 动态解析符号，避免额外链接 -ladvapi32（MinGW 的 stdlib.h 不声明 rand_s）
    typedef int(__stdcall* RtlGenRandomFn)(void*, unsigned long);
    static RtlGenRandomFn fn = [] {
        HMODULE h = LoadLibraryA("advapi32.dll");
        return h ? reinterpret_cast<RtlGenRandomFn>(GetProcAddress(h, "SystemFunction036"))
                 : nullptr;
    }();
    if (fn == nullptr) return false;
    return fn(out, static_cast<unsigned long>(len)) != 0;
#else
#if defined(__linux__)
    if (getrandom(out, len, 0) == static_cast<ssize_t>(len)) return true;
    // 落到 /dev/urandom：老内核或 seccomp 屏蔽 getrandom 时仍可用
#endif
    static int ufd = ::open("/dev/urandom", O_RDONLY | O_CLOEXEC);
    if (ufd < 0) return false;
    auto* p = static_cast<unsigned char*>(out);
    size_t done = 0;
    while (done < len) {
        const ssize_t n = ::read(ufd, p + done, len - done);
        if (n <= 0) {
            if (n < 0 && errno == EINTR) continue;
            return false;
        }
        done += static_cast<size_t>(n);
    }
    return true;
#endif
}

// ------------------------------------------------------------------ 大整数
namespace {

using Word = uint32_t;
/// 小端 limb 数组：v[0] 是最低 32 位
using Big = std::vector<Word>;

Big fromBytesBe(std::string_view bytes) {
    Big a;
    for (size_t i = bytes.size(); i > 0;) {
        size_t begin = i >= 4 ? i - 4 : 0;
        uint64_t w = 0;
        for (size_t j = begin; j < i; ++j) w = (w << 8) | static_cast<unsigned char>(bytes[j]);
        a.push_back(static_cast<Word>(w));
        i = begin;
    }
    while (a.size() > 1 && a.back() == 0) a.pop_back();
    if (a.empty()) a.push_back(0);
    return a;
}

std::string toBytesBe(const Big& a, size_t length) {
    std::string out(length, '\0');
    for (size_t i = 0; i < length; ++i) {
        const size_t byte_from_end = length - i;             // 1..length
        const size_t limb = (byte_from_end - 1) / 4;
        const size_t shift = ((byte_from_end - 1) % 4) * 8;
        const uint64_t w = limb < a.size() ? a[limb] : 0;
        out[i] = static_cast<char>((w >> shift) & 0xff);
    }
    return out;
}

/** 逐 limb 从高位比较，长度不等时高位按 0 处理 */
int cmpWide(const Big& a, const Big& b) {
    const size_t n = a.size() > b.size() ? a.size() : b.size();
    for (size_t i = n; i-- > 0;) {
        const Word av = i < a.size() ? a[i] : 0;
        const Word bv = i < b.size() ? b[i] : 0;
        if (av != bv) return av > bv ? 1 : -1;
    }
    return 0;
}

/** a -= b（就地，b 长度 <= a.size()），返回最终借位 */
Word subInplace(Big& a, const Big& b) {
    int64_t borrow = 0;
    for (size_t i = 0; i < a.size(); ++i) {
        const int64_t sub = static_cast<int64_t>(i < b.size() ? b[i] : 0) + borrow;
        const int64_t diff = static_cast<int64_t>(a[i]) - sub;
        a[i] = static_cast<Word>(diff);  // 低位回绕即模 2^32 的结果
        borrow = diff < 0 ? 1 : 0;
    }
    return static_cast<Word>(borrow);
}

Big mul(const Big& a, const Big& b) {
    Big r(a.size() + b.size(), 0);
    for (size_t i = 0; i < a.size(); ++i) {
        uint64_t carry = 0;
        for (size_t j = 0; j < b.size(); ++j) {
            const uint64_t cur = r[i + j] + static_cast<uint64_t>(a[i]) * b[j] + carry;
            r[i + j] = static_cast<Word>(cur);
            carry = cur >> 32;
        }
        size_t k = i + b.size();
        while (carry) {
            const uint64_t cur = r[k] + carry;
            r[k] = static_cast<Word>(cur);
            carry = cur >> 32;
            ++k;
        }
    }
    return r;
}

/** (a * b) mod m：先乘，再按位做长除（够用且不易出错；指数只有 17 位，性能足够） */
Big mulmod(const Big& a, const Big& b, const Big& m) {
    const Big product = mul(a, b);
    const size_t n = m.size();
    Big rem(n + 1, 0);
    const size_t total_bits = product.size() * 32;
    for (size_t bit = total_bits; bit-- > 0;) {
        // rem <<= 1 | current bit
        uint64_t carry = (product[bit / 32] >> (bit % 32)) & 1;
        for (size_t i = 0; i <= n; ++i) {
            const uint64_t v = (static_cast<uint64_t>(rem[i]) << 1) | carry;
            rem[i] = static_cast<Word>(v);
            carry = v >> 32;
        }
        if (cmpWide(rem, m) >= 0) subInplace(rem, m);
    }
    Big out(rem.begin(), rem.begin() + n);
    while (out.size() > 1 && out.back() == 0) out.pop_back();
    return out;
}

Big modexp(const Big& base_in, const Big& exponent, const Big& m) {
    // 左到右双倍-加：公钥指数恒为 65537 这类小值，比特数很少
    Big base = base_in;
    while (!base.empty() && base.size() < m.size()) base.push_back(0);
    while (cmpWide(base, m) >= 0) subInplace(base, m);
    Big result{1};
    size_t top_bit = 0;
    for (size_t i = 0; i < exponent.size(); ++i) {
        if (exponent[i] == 0) continue;
        size_t b = i * 32;
        Word w = exponent[i];
        while (w >>= 1) ++b;
        if (b > top_bit) top_bit = b;
    }
    for (size_t bit = top_bit + 1; bit-- > 0;) {
        result = mulmod(result, result, m);
        const Word b = (exponent[bit / 32] >> (bit % 32)) & 1;
        if (b) result = mulmod(result, base, m);
    }
    return result;
}

// ------------------------------------------------------------------ DER
struct Der {
    const uint8_t* p;
    size_t n;
};

/** 读 TLV；返回内容，offset 前移。tag 不匹配返回 false */
bool readTlv(Der& d, uint8_t expect_tag, Der& content) {
    if (d.n < 2) return false;
    const uint8_t tag = d.p[0];
    size_t pos = 1;
    const uint8_t first = d.p[pos];
    size_t len = 0;
    if ((first & 0x80) == 0) {
        len = first;
        pos += 1;
    } else {
        const size_t num = first & 0x7f;
        if (num == 0 || num > 4 || pos + num >= d.n) return false;
        for (size_t i = 0; i < num; ++i) {
            len = (len << 8) | d.p[pos + 1 + i];
        }
        pos += 1 + num;
    }
    if (tag != expect_tag || pos + len > d.n) return false;
    content.p = d.p + pos;
    content.n = len;
    d.p = content.p + len;
    d.n -= pos + len;
    return true;
}

/** 跳过 tag 检查读 INTEGER（去掉 DER 的前导 0） */
bool readIntegerBytes(Der& d, std::string& out) {
    Der content;
    if (!readTlv(d, 0x02, content)) return false;
    size_t start = 0;
    while (start + 1 < content.n && content.p[start] == 0) ++start;
    out.assign(reinterpret_cast<const char*>(content.p + start), content.n - start);
    return true;
}

bool parseSpki(const std::string& der, RsaPublicKey& out, std::string* err) {
    Der top{reinterpret_cast<const uint8_t*>(der.data()), der.size()};
    Der seq;
    if (!readTlv(top, 0x30, seq)) {
        if (err) *err = "SPKI: 外层 SEQUENCE 解析失败";
        return false;
    }
    Der alg;
    if (!readTlv(seq, 0x30, alg)) {
        if (err) *err = "SPKI: AlgorithmIdentifier 解析失败";
        return false;
    }
    Der bitstring;
    if (!readTlv(seq, 0x03, bitstring)) {
        if (err) *err = "SPKI: BIT STRING 解析失败";
        return false;
    }
    if (bitstring.n < 1) return false;
    Der inner{bitstring.p + 1, bitstring.n - 1};  // 跳过 unused-bits 字节
    Der keySeq;
    if (!readTlv(inner, 0x30, keySeq)) {
        if (err) *err = "SPKI: RSAPublicKey SEQUENCE 解析失败";
        return false;
    }
    if (!readIntegerBytes(keySeq, out.modulus) || !readIntegerBytes(keySeq, out.exponent)) {
        if (err) *err = "SPKI: modulus/exponent 解析失败";
        return false;
    }
    if (out.modulus.empty()) {
        if (err) *err = "SPKI: 空模数";
        return false;
    }
    return true;
}

/** MGF1(SHA-1)，RFC 2437 第 9.1 节 */
std::string mgf1Sha1(std::string_view seed, size_t length) {
    std::string out;
    out.reserve(length + 20);
    uint32_t counter = 0;
    while (out.size() < length) {
        std::string c;
        c.push_back(static_cast<char>((counter >> 24) & 0xff));
        c.push_back(static_cast<char>((counter >> 16) & 0xff));
        c.push_back(static_cast<char>((counter >> 8) & 0xff));
        c.push_back(static_cast<char>(counter & 0xff));
        out += sha1(std::string(seed) + c);
        ++counter;
    }
    out.resize(length);
    return out;
}

} // namespace

bool parsePemPublicKey(std::string_view pem, RsaPublicKey& out, std::string* err) {
    const std::string text(pem);
    const size_t b = text.find("-----BEGIN");
    if (b == std::string::npos) {
        if (err) *err = "PEM: 缺少 BEGIN 标记";
        return false;
    }
    const size_t body_begin = text.find('\n', b);
    const size_t e = text.find("-----END", body_begin == std::string::npos ? b : body_begin);
    if (body_begin == std::string::npos || e == std::string::npos) {
        if (err) *err = "PEM: 格式不完整";
        return false;
    }
    std::string body = text.substr(body_begin + 1, e - body_begin - 1);
    // 去掉空白后 base64 解码
    std::string compact;
    compact.reserve(body.size());
    for (char c : body) {
        if (c != '\r' && c != '\n' && c != ' ' && c != '\t') compact.push_back(c);
    }
    std::string der;
    if (!base64Decode(compact, der) || der.empty()) {
        if (err) *err = "PEM: base64 解码失败";
        return false;
    }
    return parseSpki(der, out, err);
}

bool rsaOaepEncrypt(const RsaPublicKey& key, std::string_view plaintext, std::string& out,
                   std::string* err) {
    const size_t hlen = 20;  // SHA-1
    const size_t k = key.modulus.size();
    // EM = 0x00 || maskedSeed(hLen) || maskedDB(k-hLen-1)，DB 定长 k-hLen-1，
    // 因此明文上限是 k - 2*hLen - 2
    const size_t db_len = k - hlen - 1;
    if (plaintext.size() > k - 2 * hlen - 2) {
        if (err) *err = "RSA-OAEP: 明文过长";
        return false;
    }
    const std::string seed = secureRandomString(hlen);
    if (seed.size() != hlen) {
        if (err) *err = "RSA-OAEP: 随机数发生器不可用";
        return false;
    }
    // DB = lHash || PS || 0x01 || M
    const std::string lhash = sha1(std::string_view{});
    std::string db = lhash;
    db.append(db_len - hlen - 1 - plaintext.size(), '\0');
    db.push_back(0x01);
    db.append(plaintext);

    const std::string db_mask = mgf1Sha1(seed, db.size());
    std::string masked_db(db.size(), '\0');
    for (size_t i = 0; i < db.size(); ++i) {
        masked_db[i] = static_cast<char>(static_cast<unsigned char>(db[i]) ^
                                         static_cast<unsigned char>(db_mask[i]));
    }
    const std::string seed_mask = mgf1Sha1(masked_db, hlen);
    std::string masked_seed(hlen, '\0');
    for (size_t i = 0; i < hlen; ++i) {
        masked_seed[i] = static_cast<char>(static_cast<unsigned char>(seed[i]) ^
                                          static_cast<unsigned char>(seed_mask[i]));
    }
    std::string em;
    em.push_back(0x00);
    em += masked_seed;
    em += masked_db;

    const Big n = fromBytesBe(key.modulus);
    const Big ee = fromBytesBe(key.exponent);
    const Big m = fromBytesBe(em);
    if (cmpWide(m, n) >= 0) {
        if (err) *err = "RSA-OAEP: 编码后的消息超出模数范围";
        return false;
    }
    const Big c = modexp(m, ee, n);
    out = toBytesBe(c, k);
    return true;
}

bool rsaOaepEncryptPem(std::string_view pem, std::string_view plaintext, std::string& out,
                       std::string* err) {
    RsaPublicKey key;
    if (!parsePemPublicKey(pem, key, err)) return false;
    return rsaOaepEncrypt(key, plaintext, out, err);
}

} // namespace cm::crypto
