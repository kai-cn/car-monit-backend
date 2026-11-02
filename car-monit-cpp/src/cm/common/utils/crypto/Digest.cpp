// 摘要 / HMAC 实现。算法参考公开规范：RFC 1321(MD5)、FIPS 180-4(SHA-1/256/512)、
// RFC 2104(HMAC)。与 Java MessageDigest 的一致性由 tests/crypto_test.cpp 的对拍保证。
#include "cm/common/utils/crypto/Digest.hpp"

#include <array>
#include <cmath>
#include <cstring>
#include <vector>

namespace cm::crypto {
namespace {

void putBe32(std::string& out, uint32_t v) {
    out.push_back(static_cast<char>((v >> 24) & 0xff));
    out.push_back(static_cast<char>((v >> 16) & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
    out.push_back(static_cast<char>(v & 0xff));
}
void putLe32(std::string& out, uint32_t v) {
    out.push_back(static_cast<char>(v & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
    out.push_back(static_cast<char>((v >> 16) & 0xff));
    out.push_back(static_cast<char>((v >> 24) & 0xff));
}
void putBe64(std::string& out, uint64_t v) {
    for (int i = 7; i >= 0; --i) out.push_back(static_cast<char>((v >> (i * 8)) & 0xff));
}
uint32_t getLe32(const uint8_t* p) {
    return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) | (static_cast<uint32_t>(p[3]) << 24);
}
uint32_t getBe32(const uint8_t* p) {
    return (static_cast<uint32_t>(p[0]) << 24) | (static_cast<uint32_t>(p[1]) << 16) |
           (static_cast<uint32_t>(p[2]) << 8) | static_cast<uint32_t>(p[3]);
}
uint64_t getBe64(const uint8_t* p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) v = (v << 8) | p[i];
    return v;
}

inline uint32_t rotl32(uint32_t x, int n) { return (x << n) | (x >> (32 - n)); }
inline uint32_t rotr32(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
inline uint64_t rotr64(uint64_t x, int n) { return (x >> n) | (x << (64 - n)); }

// ---------------------------------------------------------------- MD5
std::string md5Impl(std::string_view data) {
    // RFC 1321 的 T[i] = floor(abs(sin(i+1)) * 2^32)，运行时按定义生成，避免抄表出错
    static const auto kTable = [] {
        std::array<uint32_t, 64> t{};
        for (int i = 0; i < 64; ++i) {
            t[i] = static_cast<uint32_t>(
                std::floor(std::fabs(std::sin(static_cast<long double>(i + 1))) *
                           4294967296.0L));
        }
        return t;
    }();
    static const int s[64] = {
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9,  14, 20, 5, 9,
        14, 20, 5, 9, 14, 20, 5, 9,  14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        4, 11, 16, 23, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21};

    uint32_t a0 = 0x67452301, b0 = 0xefcdab89, c0 = 0x98badcfe, d0 = 0x10325476;
    std::string msg(data);
    const uint64_t bit_len = static_cast<uint64_t>(msg.size()) * 8;
    msg.push_back(static_cast<char>(0x80));
    while (msg.size() % 64 != 56) msg.push_back('\0');
    for (int i = 0; i < 8; ++i) msg.push_back(static_cast<char>((bit_len >> (i * 8)) & 0xff));

    for (size_t off = 0; off + 64 <= msg.size(); off += 64) {
        uint32_t m[16];
        for (int i = 0; i < 16; ++i) {
            m[i] = getLe32(reinterpret_cast<const uint8_t*>(msg.data() + off + i * 4));
        }
        uint32_t A = a0, B = b0, C = c0, D = d0;
        for (int i = 0; i < 64; ++i) {
            uint32_t F, g;
            if (i < 16) {
                F = (B & C) | (~B & D);
                g = i;
            } else if (i < 32) {
                F = (D & B) | (~D & C);
                g = (5 * i + 1) % 16;
            } else if (i < 48) {
                F = B ^ C ^ D;
                g = (3 * i + 5) % 16;
            } else {
                F = C ^ (B | ~D);
                g = (7 * i) % 16;
            }
            F = F + A + kTable[i] + m[g];
            A = D;
            D = C;
            C = B;
            B = B + rotl32(F, s[i]);
        }
        a0 += A;
        b0 += B;
        c0 += C;
        d0 += D;
    }
    std::string out;
    out.reserve(16);
    putLe32(out, a0);
    putLe32(out, b0);
    putLe32(out, c0);
    putLe32(out, d0);
    return out;
}

// ---------------------------------------------------------------- SHA-1
std::string sha1Impl(std::string_view data) {
    uint32_t h0 = 0x67452301, h1 = 0xEFCDAB89, h2 = 0x98BADCFE, h3 = 0x10325476,
             h4 = 0xC3D2E1F0;
    std::string msg(data);
    const uint64_t bit_len = static_cast<uint64_t>(msg.size()) * 8;
    msg.push_back(static_cast<char>(0x80));
    while (msg.size() % 64 != 56) msg.push_back('\0');
    putBe64(msg, bit_len);

    for (size_t off = 0; off + 64 <= msg.size(); off += 64) {
        uint32_t w[80];
        for (int i = 0; i < 16; ++i) {
            w[i] = getBe32(reinterpret_cast<const uint8_t*>(msg.data() + off + i * 4));
        }
        for (int i = 16; i < 80; ++i) {
            w[i] = rotl32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
        }
        uint32_t a = h0, b = h1, c = h2, d = h3, e = h4;
        for (int i = 0; i < 80; ++i) {
            uint32_t f, k;
            if (i < 20) {
                f = (b & c) | (~b & d);
                k = 0x5A827999;
            } else if (i < 40) {
                f = b ^ c ^ d;
                k = 0x6ED9EBA1;
            } else if (i < 60) {
                f = (b & c) | (b & d) | (c & d);
                k = 0x8F1BBCDC;
            } else {
                f = b ^ c ^ d;
                k = 0xCA62C1D6;
            }
            uint32_t tmp = rotl32(a, 5) + f + e + k + w[i];
            e = d;
            d = c;
            c = rotl32(b, 30);
            b = a;
            a = tmp;
        }
        h0 += a;
        h1 += b;
        h2 += c;
        h3 += d;
        h4 += e;
    }
    std::string out;
    putBe32(out, h0);
    putBe32(out, h1);
    putBe32(out, h2);
    putBe32(out, h3);
    putBe32(out, h4);
    return out;
}

// ---------------------------------------------------------------- SHA-256
constexpr uint32_t kSha256K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

std::string sha256Impl(std::string_view data) {
    std::array<uint32_t, 8> h = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                                 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    std::string msg(data);
    const uint64_t bit_len = static_cast<uint64_t>(msg.size()) * 8;
    msg.push_back(static_cast<char>(0x80));
    while (msg.size() % 64 != 56) msg.push_back('\0');
    putBe64(msg, bit_len);

    for (size_t off = 0; off + 64 <= msg.size(); off += 64) {
        uint32_t w[64];
        for (int i = 0; i < 16; ++i) {
            w[i] = getBe32(reinterpret_cast<const uint8_t*>(msg.data() + off + i * 4));
        }
        for (int i = 16; i < 64; ++i) {
            uint32_t s0 = rotr32(w[i - 15], 7) ^ rotr32(w[i - 15], 18) ^ (w[i - 15] >> 3);
            uint32_t s1 = rotr32(w[i - 2], 17) ^ rotr32(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
        for (int i = 0; i < 64; ++i) {
            uint32_t S1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25);
            uint32_t ch = (e & f) ^ (~e & g);
            uint32_t t1 = hh + S1 + ch + kSha256K[i] + w[i];
            uint32_t S0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22);
            uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint32_t t2 = S0 + maj;
            hh = g;
            g = f;
            f = e;
            e = d + t1;
            d = c;
            c = b;
            b = a;
            a = t1 + t2;
        }
        h[0] += a;
        h[1] += b;
        h[2] += c;
        h[3] += d;
        h[4] += e;
        h[5] += f;
        h[6] += g;
        h[7] += hh;
    }
    std::string out;
    for (uint32_t v : h) putBe32(out, v);
    return out;
}

// ---------------------------------------------------------------- SHA-512
constexpr uint64_t kSha512K[80] = {
    0x428a2f98d728ae22, 0x7137449123ef65cd, 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc,
    0x3956c25bf348b538, 0x59f111f1b605d019, 0x923f82a4af194f9b, 0xab1c5ed5da6d8118,
    0xd807aa98a3030242, 0x12835b0145706fbe, 0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2,
    0x72be5d74f27b896f, 0x80deb1fe3b1696b1, 0x9bdc06a725c71235, 0xc19bf174cf692694,
    0xe49b69c19ef14ad2, 0xefbe4786384f25e3, 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65,
    0x2de92c6f592b0275, 0x4a7484aa6ea6e483, 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5,
    0x983e5152ee66dfab, 0xa831c66d2db43210, 0xb00327c898fb213f, 0xbf597fc7beef0ee4,
    0xc6e00bf33da88fc2, 0xd5a79147930aa725, 0x06ca6351e003826f, 0x142929670a0e6e70,
    0x27b70a8546d22ffc, 0x2e1b21385c26c926, 0x4d2c6dfc5ac42aed, 0x53380d139d95b3df,
    0x650a73548baf63de, 0x766a0abb3c77b2a8, 0x81c2c92e47edaee6, 0x92722c851482353b,
    0xa2bfe8a14cf10364, 0xa81a664bbc423001, 0xc24b8b70d0f89791, 0xc76c51a30654be30,
    0xd192e819d6ef5218, 0xd69906245565a910, 0xf40e35855771202a, 0x106aa07032bbd1b8,
    0x19a4c116b8d2d0c8, 0x1e376c085141ab53, 0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8,
    0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb, 0x5b9cca4f7763e373, 0x682e6ff3d6b2b8a3,
    0x748f82ee5defb2fc, 0x78a5636f43172f60, 0x84c87814a1f0ab72, 0x8cc702081a6439ec,
    0x90befffa23631e28, 0xa4506cebde82bde9, 0xbef9a3f7b2c67915, 0xc67178f2e372532b,
    0xca273eceea26619c, 0xd186b8c721c0c207, 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178,
    0x06f067aa72176fba, 0x0a637dc5a2c898a6, 0x113f9804bef90dae, 0x1b710b35131c471b,
    0x28db77f523047d84, 0x32caab7b40c72493, 0x3c9ebe0a15c9bebc, 0x431d67c49c100d4c,
    0x4cc5d4becb3e42b6, 0x597f299cfc657e2a, 0x5fcb6fab3ad6faec, 0x6c44198c4a475817};

std::string sha512Impl(std::string_view data) {
    std::array<uint64_t, 8> h = {0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL,
                                 0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
                                 0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
                                 0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL};
    std::string msg(data);
    const uint64_t bit_len = static_cast<uint64_t>(msg.size()) * 8;
    msg.push_back(static_cast<char>(0x80));
    while (msg.size() % 128 != 112) msg.push_back('\0');
    putBe64(msg, 0);  // 128 位长度字段：对 < 2^64 bit 的输入高 64 位恒为 0
    putBe64(msg, bit_len);

    for (size_t off = 0; off + 128 <= msg.size(); off += 128) {
        uint64_t w[80];
        for (int i = 0; i < 16; ++i) {
            w[i] = getBe64(reinterpret_cast<const uint8_t*>(msg.data() + off + i * 8));
        }
        for (int i = 16; i < 80; ++i) {
            uint64_t s0 = rotr64(w[i - 15], 1) ^ rotr64(w[i - 15], 8) ^ (w[i - 15] >> 7);
            uint64_t s1 = rotr64(w[i - 2], 19) ^ rotr64(w[i - 2], 61) ^ (w[i - 2] >> 6);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        uint64_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
        for (int i = 0; i < 80; ++i) {
            uint64_t S1 = rotr64(e, 14) ^ rotr64(e, 18) ^ rotr64(e, 41);
            uint64_t ch = (e & f) ^ (~e & g);
            uint64_t t1 = hh + S1 + ch + kSha512K[i] + w[i];
            uint64_t S0 = rotr64(a, 28) ^ rotr64(a, 34) ^ rotr64(a, 39);
            uint64_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint64_t t2 = S0 + maj;
            hh = g;
            g = f;
            f = e;
            e = d + t1;
            d = c;
            c = b;
            b = a;
            a = t1 + t2;
        }
        h[0] += a;
        h[1] += b;
        h[2] += c;
        h[3] += d;
        h[4] += e;
        h[5] += f;
        h[6] += g;
        h[7] += hh;
    }
    std::string out;
    for (uint64_t v : h) putBe64(out, v);
    return out;
}

struct HashInfo {
    std::string (*fn)(std::string_view);
    size_t block;
    size_t digest;
};

HashInfo info(const std::string& algo) {
    if (algo == "md5") return {md5Impl, 64, 16};
    if (algo == "sha1") return {sha1Impl, 64, 20};
    if (algo == "sha512") return {sha512Impl, 128, 64};
    return {sha256Impl, 64, 32};
}

} // namespace

std::string md5(std::string_view data) { return md5Impl(data); }
std::string sha1(std::string_view data) { return sha1Impl(data); }
std::string sha256(std::string_view data) { return sha256Impl(data); }
std::string sha512(std::string_view data) { return sha512Impl(data); }

std::string hmac(const std::string& hash, std::string_view key, std::string_view data) {
    const HashInfo hi = info(hash);
    std::string k(key);
    if (k.size() > hi.block) k = hi.fn(k);
    if (k.size() < hi.block) k.resize(hi.block, '\0');
    std::string ipad(hi.block, '\0'), opad(hi.block, '\0');
    for (size_t i = 0; i < hi.block; ++i) {
        ipad[i] = static_cast<char>(static_cast<unsigned char>(k[i]) ^ 0x36);
        opad[i] = static_cast<char>(static_cast<unsigned char>(k[i]) ^ 0x5c);
    }
    std::string inner;
    inner.reserve(hi.block + data.size());
    inner.append(ipad).append(data);
    const std::string h1 = hi.fn(inner);
    std::string outer;
    outer.reserve(hi.block + h1.size());
    outer.append(opad).append(h1);
    return hi.fn(outer);
}

std::string hex(std::string_view bytes) {
    static const char* digits = "0123456789abcdef";
    std::string out;
    out.reserve(bytes.size() * 2);
    for (unsigned char c : bytes) {
        out.push_back(digits[c >> 4]);
        out.push_back(digits[c & 0xf]);
    }
    return out;
}

std::string unhex(std::string_view text) {
    auto val = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    if (text.size() % 2 != 0) return {};
    std::string out;
    out.reserve(text.size() / 2);
    for (size_t i = 0; i < text.size(); i += 2) {
        const int hi = val(text[i]);
        const int lo = val(text[i + 1]);
        if (hi < 0 || lo < 0) return {};
        out.push_back(static_cast<char>((hi << 4) | lo));
    }
    return out;
}

} // namespace cm::crypto
