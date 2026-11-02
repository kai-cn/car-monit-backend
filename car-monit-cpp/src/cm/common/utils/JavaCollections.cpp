#include "cm/common/utils/JavaCollections.hpp"

namespace cm::utils {
namespace {

int spread(int h) { return h ^ (static_cast<uint32_t>(h) >> 16); }

/** 计算容纳 n 个元素所需的最小 2 的幂容量（初始 16） */
int capacityFor(size_t n) {
    int cap = 16;
    while (static_cast<size_t>(cap) * 3 / 4 < n) cap <<= 1;
    return cap;
}

} // namespace

int javaStringHash(const std::string& s) {
    // Java String#hashCode 基于 UTF-16 code unit；UTF-8 输入按 UTF-16 重新计算
    int h = 0;
    size_t i = 0;
    while (i < s.size()) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        uint32_t cp = 0;
        size_t len = 1;
        if (c < 0x80) {
            cp = c;
        } else if ((c >> 5) == 0x6 && i + 1 < s.size()) {
            cp = ((c & 0x1f) << 6) | (static_cast<unsigned char>(s[i + 1]) & 0x3f);
            len = 2;
        } else if ((c >> 4) == 0xe && i + 2 < s.size()) {
            cp = ((c & 0x0f) << 12) | ((static_cast<unsigned char>(s[i + 1]) & 0x3f) << 6) |
                 (static_cast<unsigned char>(s[i + 2]) & 0x3f);
            len = 3;
        } else if ((c >> 3) == 0x1e && i + 3 < s.size()) {
            cp = ((c & 0x07) << 18) | ((static_cast<unsigned char>(s[i + 1]) & 0x3f) << 12) |
                 ((static_cast<unsigned char>(s[i + 2]) & 0x3f) << 6) |
                 (static_cast<unsigned char>(s[i + 3]) & 0x3f);
            len = 4;
        } else {
            cp = c;
        }
        i += len;
        if (cp >= 0x10000) {
            uint32_t v = cp - 0x10000;
            h = 31 * h + static_cast<int>(0xD800 + (v >> 10));
            h = 31 * h + static_cast<int>(0xDC00 + (v & 0x3ff));
        } else {
            h = 31 * h + static_cast<int>(cp);
        }
    }
    return h;
}

int javaBucketIndex(const std::string& key, int capacity) {
    return spread(javaStringHash(key)) & (capacity - 1);
}

std::vector<std::string> javaMapOrder(const std::vector<std::string>& keys) {
    int cap = capacityFor(keys.size());
    std::vector<size_t> idx(keys.size());
    for (size_t i = 0; i < keys.size(); ++i) idx[i] = i;
    std::stable_sort(idx.begin(), idx.end(), [&](size_t a, size_t b) {
        int ba = javaBucketIndex(keys[a], cap);
        int bb = javaBucketIndex(keys[b], cap);
        if (ba != bb) return ba < bb;
        return a < b; // 同桶保持插入顺序
    });
    std::vector<std::string> out;
    out.reserve(keys.size());
    for (size_t i : idx) out.push_back(keys[i]);
    return out;
}

std::vector<std::string> javaSetOrder(const std::vector<std::string>& keys) {
    return javaMapOrder(keys);
}

} // namespace cm::utils
