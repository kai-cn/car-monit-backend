// 内置 INFLATE 解码器（RFC 1951）。实现取向：宁可写得直白，也不要为了省几行
// 把位序/码表出错的风险留给"只有真实 xlsx 才能发现"的场景。
//
// 早先 BTYPE=01/10 都解不出第一个后向引用（stored 能过），字面量全对、只有距离错。
// 根因是 kDistBase 抄成了「长度码」那一路的翻倍序列（…6,8,12,16,24,32…），而
// RFC 1951 表 3.3.f 的距离基值在 4 之后是 5,7,9,13,17,25,…；bits-in/out 与
// 规范哈夫曼构造（含 MSB 先行累积、HLIT/HDIST/HCLEN 顺序、kOrder 重排）都对得上，
// 两张表唯一的不同就是这一处。距离码 0..3 的基值恰好一致，所以短距离的流看不出来。
// 现在 stored/fixed/dynamic + zlib + gzip 都按 scripts/gen_inflate_fixture.py 产出的
// 对拍样本（Python zlib 独立生成并回验）验证通过，测试见 tests/inflate_test.cpp。
#include "cm/common/utils/Inflate.hpp"

#include <map>
#include <vector>

namespace cm::utils {
namespace {

struct BitReader {
    const unsigned char* p;
    size_t n;
    size_t pos{0};       // 字节
    unsigned long long buf{0};
    int bits{0};

    BitReader(const unsigned char* d, size_t size) : p(d), n(size) {}

    bool need(int k) {
        while (bits < k) {
            if (pos >= n) return false;
            buf |= static_cast<unsigned long long>(p[pos++]) << bits;
            bits += 8;
        }
        return true;
    }
    unsigned int take(int k) {
        if (!need(k)) return 0;
        unsigned int v = static_cast<unsigned int>(buf & ((1ULL << k) - 1));
        buf >>= k;
        bits -= k;
        return v;
    }
    void skip(int k) { (void)take(k); }
};

/** 规范哈夫曼：给每个符号算出它的编码（MSB 先行），逐位累积后查表。
 *  比"count/first/index 三件套"直白，出问题时也能直接把码表打出来看。 */
struct Huffman {
    std::map<unsigned long long, int> table;   // key = (len << 16) | code
    int maxLen{0};
    bool ok{false};

    void build(const std::vector<unsigned char>& lens) {
        table.clear();
        ok = false;
        maxLen = 0;
        std::vector<unsigned int> count(16, 0);
        for (unsigned char l : lens) count[l]++;
        count[0] = 0;
        // 每个码长的起始码值
        unsigned int codeOf[16] = {0};
        unsigned int code = 0;
        for (int len = 1; len <= 15; ++len) {
            code = (code + count[len - 1]) << 1;
            codeOf[len] = code;
        }
        for (size_t s = 0; s < lens.size(); ++s) {
            const int len = lens[s];
            if (!len) continue;
            const unsigned int c = codeOf[len]++;
            table[(static_cast<unsigned long long>(len) << 16) | c] = static_cast<int>(s);
            if (len > maxLen) maxLen = len;
            ok = true;
        }
        if (!ok) return;
        // 不完码（Huffman 余数不为 0）在这里只能靠"解码时查不到"暴露，不做额外校验
    }

    int decode(BitReader& br) const {
        if (!ok) return -1;
        unsigned int code = 0;
        for (int len = 1; len <= maxLen; ++len) {
            if (!br.need(1)) return -1;
            code = (code << 1) | br.take(1);
            const auto it = table.find((static_cast<unsigned long long>(len) << 16) | code);
            if (it != table.end()) return it->second;
        }
        return -1;
    }
};

bool bad(std::string* err, const char* msg) {
    if (err) *err = msg;
    return false;
}

} // namespace

bool inflateRaw(std::string_view in, std::string& out, std::string* err) {
    BitReader br(reinterpret_cast<const unsigned char*>(in.data()), in.size());
    out.clear();
    bool finalBlock = false;
    while (!finalBlock) {
        finalBlock = br.take(1) != 0;
        const unsigned int type = br.take(2);
        if (type == 0) {
            // stored：先把当前字节里没用完的位丢掉（块数据从字节边界开始），再读 LEN/NLEN
            br.buf = 0;
            br.bits = 0;
            const size_t lo = br.take(8);
            const size_t hi = br.take(8);
            const size_t len = lo | (hi << 8);
            const size_t nlo = br.take(8);
            const size_t nhi = br.take(8);
            if ((lo | (hi << 8)) != ((~(nlo | (nhi << 8))) & 0xFFFF))
                return bad(err, "stored 块的 NLEN 与 LEN 不互补");
            for (size_t i = 0; i < len; ++i) {
                if (!br.need(8)) return bad(err, "stored 块数据不完整");
                out.push_back(static_cast<char>(br.take(8)));
            }
            continue;
        }
        if (type == 3) return bad(err, "非法的 BTYPE=3");

        Huffman lit, dist;
        if (type == 1) {
            // 固定哈夫曼表（RFC 1951 §3.2.6）
            std::vector<unsigned char> l(288);
            for (int i = 0; i < 144; ++i) l[i] = 8;
            for (int i = 144; i < 256; ++i) l[i] = 9;
            for (int i = 256; i < 280; ++i) l[i] = 7;
            for (int i = 280; i < 288; ++i) l[i] = 8;
            lit.build(l);
            std::vector<unsigned char> d(30, 5);
            dist.build(d);
        } else {
            static const int kOrder[] = {16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3,
                                         13, 2, 14, 1, 15};
            const unsigned int hlit = br.take(5) + 257;
            const unsigned int hdist = br.take(5) + 1;
            const unsigned int hclen = br.take(4) + 4;
            if (hlit > 286 || hdist > 30) return bad(err, "动态码表长度越界");
            std::vector<unsigned char> codeLens(19, 0);
            for (unsigned int i = 0; i < hclen; ++i) codeLens[kOrder[i]] = static_cast<unsigned char>(br.take(3));
            Huffman codeHuff;
            codeHuff.build(codeLens);
            std::vector<unsigned char> lens(hlit + hdist, 0);
            unsigned int idx = 0;
            while (idx < hlit + hdist) {
                const int sym = codeHuff.decode(br);
                if (sym < 0) return bad(err, "码表长度流损坏");
                if (sym < 16) {
                    lens[idx++] = static_cast<unsigned char>(sym);
                } else if (sym == 16) {
                    if (idx == 0) return bad(err, "16 号重复码出现在开头");
                    const unsigned char prev = lens[idx - 1];
                    const unsigned int rep = 3 + br.take(2);
                    for (unsigned int i = 0; i < rep && idx < hlit + hdist; ++i) lens[idx++] = prev;
                } else if (sym == 17) {
                    const unsigned int rep = 3 + br.take(3);
                    for (unsigned int i = 0; i < rep && idx < hlit + hdist; ++i) lens[idx++] = 0;
                } else if (sym == 18) {
                    const unsigned int rep = 11 + br.take(7);
                    for (unsigned int i = 0; i < rep && idx < hlit + hdist; ++i) lens[idx++] = 0;
                } else {
                    return bad(err, "非法的码表符号");
                }
            }
            lit.build(std::vector<unsigned char>(lens.begin(), lens.begin() + hlit));
            dist.build(std::vector<unsigned char>(lens.begin() + hlit, lens.end()));
        }

        static const int kLengthBase[] = {3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27,
                                          31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195,
                                          227, 258};
        static const int kLengthExtra[] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
                                           3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0};
        // RFC 1951 表 3.3.f 的距离基值。注意它和前向引用长度表（2 的幂翻倍）不同，
        // 这里是 1,2,3,4 之后接 5,7,9,13,17,25,... ；早先误抄了长度表那一路，
        // 表现是"字面量都对、第一个稍远的后向引用就报距离越界"。
        static const int kDistBase[] = {1,     2,     3,     4,     5,     7,     9,     13,
                                        17,    25,    33,    49,    65,    97,    129,   193,
                                        257,   385,   513,   769,   1025,  1537,  2049,  3073,
                                        4097,  6145,  8193,  12289, 16385, 24577};
        static const int kDistExtra[] = {0, 0, 0,  0,  1,  1,  2,  2,  3,  3,  4,
                                         4, 5, 5,  6,  6,  7,  7,  8,  8,  9,  9,
                                         10, 10, 11, 11, 12, 12, 13, 13};
        while (true) {
            const int sym = lit.decode(br);
            if (sym < 0) return bad(err, "字面量/长度流损坏");
            if (sym < 256) {
                out.push_back(static_cast<char>(sym));
                continue;
            }
            if (sym == 256) break;               // EOB
            const int li = sym - 257;
            if (li >= 29) return bad(err, "长度码越界");
            const size_t length = kLengthBase[li] + br.take(kLengthExtra[li]);
            const int ds = dist.decode(br);
            if (ds < 0 || ds >= 30) return bad(err, "距离码损坏/越界");
            const size_t distance = kDistBase[ds] + br.take(kDistExtra[ds]);
            if (distance > out.size()) return bad(err, "距离超过已解出的数据");
            const size_t start = out.size() - distance;
            for (size_t i = 0; i < length; ++i) out.push_back(out[start + i]);
        }
    }
    if (err) err->clear();
    return true;
}

bool inflateZlib(std::string_view in, std::string& out, std::string* err) {
    if (in.size() < 3) return bad(err, "zlib 流过短");
    const unsigned char c = static_cast<unsigned char>(in[0]);
    const unsigned char f = static_cast<unsigned char>(in[1]);
    if ((c & 0x0F) != 8) return bad(err, "zlib CM 不是 deflate");
    if (((c << 8) | f) % 31 != 0) return bad(err, "zlib 头校验位不对");
    size_t off = 2;
    if (f & 0x20) off += 4;   // FDICT
    std::string_view body = in.substr(off);
    if (body.size() >= 4) body = body.substr(0, body.size() - 4);   // 去掉 adler32
    if (!inflateRaw(body, out, err)) return false;
    // adler32 不匹配只影响可信度，不影响可用性：照旧报出来，由调用方决定是否接受
    unsigned long a = 1, b = 0;
    for (unsigned char ch : out) {
        a = (a + ch) % 65521;
        b = (b + a) % 65521;
    }
    const unsigned long want =
        (static_cast<unsigned long>(static_cast<unsigned char>(in[in.size() - 4])) << 24) |
        (static_cast<unsigned long>(static_cast<unsigned char>(in[in.size() - 3])) << 16) |
        (static_cast<unsigned long>(static_cast<unsigned char>(in[in.size() - 2])) << 8) |
        static_cast<unsigned long>(static_cast<unsigned char>(in[in.size() - 1]));
    if (want && want != ((b << 16) | a)) return bad(err, "zlib adler32 不匹配");
    return true;
}

bool inflateGzip(std::string_view in, std::string& out, std::string* err) {
    if (in.size() < 10) return bad(err, "gzip 流过短");
    if (static_cast<unsigned char>(in[0]) != 0x1F || static_cast<unsigned char>(in[1]) != 0x8B)
        return bad(err, "不是 gzip");
    const unsigned char flags = static_cast<unsigned char>(in[3]);
    size_t off = 10;
    if (flags & 1) {   // FEXTRA
        if (in.size() < off + 2) return bad(err, "gzip FEXTRA 截断");
        off += 2 + (static_cast<unsigned char>(in[off]) | (static_cast<unsigned char>(in[off + 1]) << 8));
    }
    auto cstr = [&](size_t& p) {
        while (p < in.size() && in[p] != '\0') ++p;
        ++p;
    };
    if (flags & 8) cstr(off);   // FNAME
    if (flags & 16) cstr(off);  // FCOMMENT
    if (flags & 2) off += 2;    // FHCRC
    if (off >= in.size()) return bad(err, "gzip 头过长");
    std::string_view body = in.substr(off, in.size() - off - 8);
    return inflateRaw(body, out, err);
}

} // namespace cm::utils
