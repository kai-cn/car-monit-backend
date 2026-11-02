#include "cm/common/utils/Deflate.hpp"

#include <array>
#include <cstdint>

#ifdef CM_HAVE_ZLIB
#include <zlib.h>
#endif

namespace cm::utils {
namespace {

uint32_t adler32(std::string_view data) {
    uint32_t a = 1, b = 0;
    for (unsigned char c : data) {
        a = (a + c) % 65521;
        b = (b + a) % 65521;
    }
    return (b << 16) | a;
}

} // namespace

uint32_t crc32(std::string_view data) {
    static const auto table = [] {
        std::array<uint32_t, 256> t{};
        for (uint32_t i = 0; i < 256; ++i) {
            uint32_t c = i;
            for (int k = 0; k < 8; ++k) c = (c & 1) ? (0xedb88320u ^ (c >> 1)) : (c >> 1);
            t[i] = c;
        }
        return t;
    }();
    uint32_t c = 0xffffffffu;
    for (unsigned char b : data) c = table[(c ^ b) & 0xff] ^ (c >> 8);
    return c ^ 0xffffffffu;
}

std::string deflateZlibStored(std::string_view data) {
    std::string out;
    out.push_back(static_cast<char>(0x78));  // CMF: 32K 窗口的 deflate
    out.push_back(static_cast<char>(0x01));  // FLG: 无字典，且 (CMF<<8|FLG) % 31 == 0
    size_t pos = 0;
    if (data.empty()) {
        out.push_back(static_cast<char>(0x01));  // BFINAL=1, BTYPE=00
        out.append("\0\0\xff\xff", 4);            // LEN=0, NLEN=0xffff
    }
    while (pos < data.size()) {
        const size_t n = data.size() - pos > 0xffff ? 0xffff : data.size() - pos;
        const bool last = (pos + n) >= data.size();
        out.push_back(last ? static_cast<char>(0x01) : static_cast<char>(0x00));
        out.push_back(static_cast<char>(n & 0xff));
        out.push_back(static_cast<char>((n >> 8) & 0xff));
        const uint16_t nlen = static_cast<uint16_t>(~static_cast<uint16_t>(n));
        out.push_back(static_cast<char>(nlen & 0xff));
        out.push_back(static_cast<char>((nlen >> 8) & 0xff));
        out.append(data.substr(pos, n));
        pos += n;
    }
    const uint32_t sum = adler32(data);
    out.push_back(static_cast<char>((sum >> 24) & 0xff));
    out.push_back(static_cast<char>((sum >> 16) & 0xff));
    out.push_back(static_cast<char>((sum >> 8) & 0xff));
    out.push_back(static_cast<char>(sum & 0xff));
    return out;
}

std::string deflateZlib(std::string_view data, int level) {
#ifdef CM_HAVE_ZLIB
    uLongf bound = compressBound(static_cast<uLong>(data.size()));
    std::string out(bound, '\0');
    if (compress2(reinterpret_cast<Bytef*>(&out[0]), &bound,
                  reinterpret_cast<const Bytef*>(data.data()), static_cast<uLong>(data.size()),
                  level) != Z_OK) {
        return {};
    }
    out.resize(bound);
    return out;
#else
    (void)level;
    return deflateZlibStored(data);
#endif
}

} // namespace cm::utils
