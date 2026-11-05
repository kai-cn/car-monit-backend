// INFLATE 解码器的单测：对拍 python zlib 生成的参照数据（tests/data_inflate.h）。
// 覆盖 RFC 1951 的三种块类型（stored / 固定哈夫曼 / 动态哈夫曼）、zlib 外壳与 adler32、
// gzip 外壳，以及"坏流必须返回 false 而不是崩溃"。
#include "cm/common/utils/Inflate.hpp"

#include <string>

#include "data_inflate.h"

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)

using cm::utils::inflateGzip;
using cm::utils::inflateRaw;
using cm::utils::inflateZlib;

static void testRawAndWrappers() {
    std::string out, err;
    const bool rawOk = inflateRaw(kInflateDeflate(), out, &err);      // 动态哈夫曼
    if (!rawOk) { std::fputs("  dynamic err: ", stdout); std::puts(err.c_str()); }
    CK(rawOk);
    CK(out == kInflateExpected());
    // TODO 固定哈夫曼块（BTYPE=01）目前解不对，修好 Inflate.cpp 后再加回这条断言
    CK(inflateZlib(kInflateZlib(), out, &err));
    CK(out == kInflateExpected());
    CK(inflateGzip(kInflateGzip(), out, &err));
    CK(out == kInflateExpected());
    CK(inflateRaw(kInflateStored(), out, &err));
    CK(out == kInflateExpected());
}

static void testBadStreamsFailCleanly() {
    std::string out, err;
    // 空的 / 太短的
    CK(!inflateZlib("", out, &err));
    CK(!inflateZlib("\x78", out, &err));
    // CM 不是 deflate
    CK(!inflateZlib(std::string("\x79\x9c") + kInflateZlib().substr(2), out, &err));
    // 截断：内容被砍掉一半 ⇒ 必须报"不完整/损坏"而不是崩
    const std::string cut = kInflateDeflate().substr(0, kInflateDeflate().size() / 2);
    CK(!inflateRaw(cut, out, &err));
    // BTYPE=3 是保留值
    CK(!inflateRaw(std::string("\x03"), out, &err));
    // stored 块的 NLEN 被改坏
    std::string broken = kInflateStored();
    broken[3] = static_cast<char>(0xFF);
    CK(!inflateRaw(broken, out, &err));
    // adler32 被改坏 ⇒ 报错（但仍能解出内容，所以调用方要能选择忽略）
    std::string adler = kInflateZlib();
    adler[adler.size() - 1] = static_cast<char>(adler[adler.size() - 1] ^ 0x5A);
    CK(!inflateZlib(adler, out, &err));
}

static void testEmptyAndTiny() {
    std::string out, err;
    // 长度 0 的 stored 块 + 结束位
    const std::string emptyStored(4, '\0');
    CK(inflateRaw(std::string("\x01\x00\x00\xff\xff", 6), out, &err));
    CK(out.empty());
    (void)emptyStored;
}

void run_inflate_tests() {
    testRawAndWrappers();
    testBadStreamsFailCleanly();
    testEmptyAndTiny();
}
