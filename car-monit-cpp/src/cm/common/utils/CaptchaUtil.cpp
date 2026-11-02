#include "cm/common/utils/CaptchaUtil.hpp"

#include "cm/common/utils/Deflate.hpp"

#include <cstdio>
#include <cstring>
#include <random>
#include <vector>

namespace cm::utils {
namespace {

std::mt19937& rng() {
    static thread_local std::mt19937 gen{std::random_device{}()};
    return gen;
}

bool isMul(int x, int y) { return true; }
} // namespace

Captcha CaptchaUtil::randomMath() {
    static const char* CNUMBERS[] = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"};
    std::uniform_int_distribution<int> d10(0, 9);
    std::uniform_int_distribution<int> d3(0, 2);
    int x = d10(rng());
    int y = d10(rng());
    int op = d3(rng());
    int result = 0;
    std::string expr;
    if (op == 0) {
        result = x * y;
        expr = std::string(CNUMBERS[x]) + "*" + CNUMBERS[y];
    } else if (op == 1) {
        if (x != 0 && y % x == 0) {
            result = y / x;
            expr = std::string(CNUMBERS[y]) + "/" + CNUMBERS[x];
        } else {
            result = x + y;
            expr = std::string(CNUMBERS[x]) + "+" + CNUMBERS[y];
        }
    } else {
        if (x >= y) {
            result = x - y;
            expr = std::string(CNUMBERS[x]) + "-" + CNUMBERS[y];
        } else {
            result = y - x;
            expr = std::string(CNUMBERS[y]) + "-" + CNUMBERS[x];
        }
    }
    Captcha c;
    c.text = expr + "=?";
    c.code = std::to_string(result);
    (void)isMul;
    return c;
}

Captcha CaptchaUtil::randomChar(int length) {
    static const char chars[] = "abcdefghjkmnpqrstuvwxyz23456789";
    std::uniform_int_distribution<size_t> d(0, sizeof(chars) - 2);
    std::string s;
    for (int i = 0; i < length; ++i) s.push_back(chars[d(rng())]);
    return Captcha{s, s};
}

namespace {

// 5x7 点阵字库（仅涵盖 0-9、+ - * / = ?）
const unsigned char* glyph(char c) {
    static const unsigned char G0[7] = {0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E};
    static const unsigned char G1[7] = {0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E};
    static const unsigned char G2[7] = {0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F};
    static const unsigned char G3[7] = {0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E};
    static const unsigned char G4[7] = {0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02};
    static const unsigned char G5[7] = {0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E};
    static const unsigned char G6[7] = {0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E};
    static const unsigned char G7[7] = {0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08};
    static const unsigned char G8[7] = {0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E};
    static const unsigned char G9[7] = {0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C};
    static const unsigned char GPLUS[7] = {0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00};
    static const unsigned char GMINUS[7] = {0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00};
    static const unsigned char GMUL[7] = {0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x00};
    static const unsigned char GDIV[7] = {0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02};
    static const unsigned char GEQ[7] = {0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00};
    static const unsigned char GQ[7] = {0x0E, 0x11, 0x01, 0x0D, 0x15, 0x11, 0x0F};
    static const unsigned char GBAD[7] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    switch (c) {
        case '0': return G0;
        case '1': return G1;
        case '2': return G2;
        case '3': return G3;
        case '4': return G4;
        case '5': return G5;
        case '6': return G6;
        case '7': return G7;
        case '8': return G8;
        case '9': return G9;
        case '+': return GPLUS;
        case '-': return GMINUS;
        case '*': return GMUL;
        case '/': return GDIV;
        case '=': return GEQ;
        case '?': return GQ;
        default: return GBAD;
    }
}

void putU32(std::string& out, uint32_t v) {
    out.push_back(static_cast<char>((v >> 24) & 0xff));
    out.push_back(static_cast<char>((v >> 16) & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
    out.push_back(static_cast<char>(v & 0xff));
}

void chunk(std::string& png, const char* type, const std::string& data) {
    putU32(png, static_cast<uint32_t>(data.size()));
    std::string body(type, 4);
    body += data;
    png += body;
    const uint32_t crc = cm::utils::crc32(body);
    putU32(png, static_cast<uint32_t>(crc));
}

} // namespace

std::string CaptchaUtil::renderPng(const std::string& text, int width, int height) {
    const int W = width, H = height;
    std::vector<unsigned char> pix(static_cast<size_t>(W) * H * 3, 0xF8); // 浅灰白底
    auto set = [&](int x, int y, unsigned char r, unsigned char g, unsigned char b) {
        if (x < 0 || y < 0 || x >= W || y >= H) return;
        size_t i = (static_cast<size_t>(y) * W + x) * 3;
        pix[i] = r;
        pix[i + 1] = g;
        pix[i + 2] = b;
    };
    // 绿色边框
    for (int x = 0; x < W; ++x) {
        set(x, 0, 105, 179, 90);
        set(x, H - 1, 105, 179, 90);
    }
    for (int y = 0; y < H; ++y) {
        set(0, y, 105, 179, 90);
        set(W - 1, y, 105, 179, 90);
    }
    // 背景噪点
    std::uniform_int_distribution<int> dx(2, W - 3), dy(2, H - 3);
    for (int i = 0; i < 80; ++i) {
        int x = dx(rng()), y = dy(rng());
        set(x, y, 200, 200, 200);
    }
    // 文字：5x7 放大 5 倍，蓝色
    int scale = 5;
    int glyphW = 5 * scale + 4;
    int totalW = static_cast<int>(text.size()) * glyphW;
    int startX = (W - totalW) / 2;
    if (startX < 4) startX = 4;
    int baseY = (H - 7 * scale) / 2;
    for (size_t i = 0; i < text.size(); ++i) {
        const unsigned char* g = glyph(text[i]);
        int ox = startX + static_cast<int>(i) * glyphW;
        for (int row = 0; row < 7; ++row) {
            for (int col = 0; col < 5; ++col) {
                if (g[row] & (1 << (4 - col))) {
                    for (int sy = 0; sy < scale; ++sy) {
                        for (int sx = 0; sx < scale; ++sx) {
                            set(ox + col * scale + sx, baseY + row * scale + sy, 30, 60, 200);
                        }
                    }
                }
            }
        }
    }

    // PNG
    std::string raw;
    raw.reserve(static_cast<size_t>(H) * (1 + W * 3));
    for (int y = 0; y < H; ++y) {
        raw.push_back(0); // filter type 0
        raw.append(reinterpret_cast<const char*>(&pix[static_cast<size_t>(y) * W * 3]),
                   static_cast<size_t>(W) * 3);
    }
    const std::string z = cm::utils::deflateZlib(raw, 6);
    if (z.empty()) return "";

    std::string png("\x89PNG\r\n\x1a\n", 8);
    std::string ihdr;
    putU32(ihdr, static_cast<uint32_t>(W));
    putU32(ihdr, static_cast<uint32_t>(H));
    ihdr.push_back(8);  // bit depth
    ihdr.push_back(2);  // color type RGB
    ihdr.push_back(0);
    ihdr.push_back(0);
    ihdr.push_back(0);
    chunk(png, "IHDR", ihdr);
    chunk(png, "IDAT", z);
    chunk(png, "IEND", "");
    return png;
}

std::string CaptchaUtil::base64(const std::string& data) {
    static const char tbl[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    size_t i = 0;
    while (i + 2 < data.size()) {
        unsigned v = (static_cast<unsigned char>(data[i]) << 16) |
                     (static_cast<unsigned char>(data[i + 1]) << 8) |
                     static_cast<unsigned char>(data[i + 2]);
        out.push_back(tbl[(v >> 18) & 63]);
        out.push_back(tbl[(v >> 12) & 63]);
        out.push_back(tbl[(v >> 6) & 63]);
        out.push_back(tbl[v & 63]);
        i += 3;
    }
    if (i + 1 == data.size()) {
        unsigned v = static_cast<unsigned char>(data[i]) << 16;
        out.push_back(tbl[(v >> 18) & 63]);
        out.push_back(tbl[(v >> 12) & 63]);
        out += "==";
    } else if (i + 2 == data.size()) {
        unsigned v = (static_cast<unsigned char>(data[i]) << 16) |
                     (static_cast<unsigned char>(data[i + 1]) << 8);
        out.push_back(tbl[(v >> 18) & 63]);
        out.push_back(tbl[(v >> 12) & 63]);
        out.push_back(tbl[(v >> 6) & 63]);
        out.push_back('=');
    }
    return out;
}

} // namespace cm::utils
