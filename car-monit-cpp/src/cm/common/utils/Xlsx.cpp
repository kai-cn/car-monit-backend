// xlsx 读取器实现，见 include/cm/common/utils/Xlsx.hpp 顶部说明。
#include "cm/common/utils/Xlsx.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <sstream>

#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/Deflate.hpp"
#include "cm/common/utils/Inflate.hpp"

namespace cm::utils {
namespace {

uint16_t rd16(const std::string& b, size_t p) {
    return static_cast<uint16_t>(static_cast<unsigned char>(b[p]) |
                                 (static_cast<unsigned char>(b[p + 1]) << 8));
}
uint32_t rd32(const std::string& b, size_t p) {
    return static_cast<uint32_t>(static_cast<unsigned char>(b[p])) |
           (static_cast<uint32_t>(static_cast<unsigned char>(b[p + 1])) << 8) |
           (static_cast<uint32_t>(static_cast<unsigned char>(b[p + 2])) << 16) |
           (static_cast<uint32_t>(static_cast<unsigned char>(b[p + 3])) << 24);
}

std::string unescapeXml(const std::string& s) {
    std::string o;
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '&') {
            o.push_back(s[i]);
            continue;
        }
        if (s.compare(i, 4, "&amp;") == 0) { o.push_back('&'); i += 3; continue; }
        if (s.compare(i, 4, "&lt;") == 0) { o.push_back('<'); i += 3; continue; }
        if (s.compare(i, 4, "&gt;") == 0) { o.push_back('>'); i += 3; continue; }
        if (s.compare(i, 5, "&quot;") == 0) { o.push_back('"'); i += 4; continue; }
        if (s.compare(i, 5, "&apos;") == 0) { o.push_back('\''); i += 4; continue; }
        if (s.compare(i, 2, "&#") == 0) {
            const size_t semi = s.find(';', i);
            if (semi != std::string::npos && semi > i + 2) {
                const std::string num = s.substr(i + 2, semi - i - 2);
                long cp = 0;
                if (num.size() > 1 && num[0] == 'x') cp = std::strtol(num.c_str() + 1, nullptr, 16);
                else { try { cp = std::stol(num); } catch (...) { cp = 0; } }
                if (cp > 0 && cp < 0x110000) {
                    // UTF-8 编码
                    if (cp < 0x80) o.push_back(static_cast<char>(cp));
                    else if (cp < 0x800) {
                        o.push_back(static_cast<char>(0xC0 | (cp >> 6)));
                        o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
                    } else if (cp < 0x10000) {
                        o.push_back(static_cast<char>(0xE0 | (cp >> 12)));
                        o.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
                        o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
                    } else {
                        o.push_back(static_cast<char>(0xF0 | (cp >> 18)));
                        o.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
                        o.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
                        o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
                    }
                    i = semi;
                    continue;
                }
            }
        }
        o.push_back(s[i]);
    }
    return o;
}

/** 取标签属性值：attr("s=\"3\"", "s") -> "3" */
std::string attr(const std::string& tag, const std::string& name) {
    size_t pos = 0;
    while ((pos = tag.find(name, pos)) != std::string::npos) {
        size_t after = pos + name.size();
        // 必须是独立属性（前面是空白，后面是 =）
        const bool boundaryOk = pos == 0 || tag[pos - 1] == ' ' || tag[pos - 1] == '\t' ||
                                tag[pos - 1] == '"' || tag[pos - 1] == '\'' || tag[pos - 1] == '/';
        if (boundaryOk && after < tag.size() && tag[after] == '=') {
            const size_t q = tag.find_first_of("\"'", after + 1);
            if (q == std::string::npos) return "";
            const size_t e = tag.find(tag[q], q + 1);
            if (e == std::string::npos) return "";
            return tag.substr(q + 1, e - q - 1);
        }
        pos = after;
    }
    return "";
}

int colIndex(const std::string& ref) {
    int col = 0;
    for (char c : ref) {
        if (c >= 'A' && c <= 'Z') col = col * 26 + (c - 'A' + 1);
        else if (c >= 'a' && c <= 'z') col = col * 26 + (c - 'a' + 1);
        else break;
    }
    return col > 0 ? col - 1 : 0;
}

std::vector<std::string> findAll(const std::string& hay, const std::string& open,
                                 const std::string& close) {
    std::vector<std::string> out;
    size_t pos = 0;
    while ((pos = hay.find(open, pos)) != std::string::npos) {
        const size_t end = hay.find(close, pos);
        if (end == std::string::npos) break;
        out.push_back(hay.substr(pos, end - pos + close.size()));
        pos = end + close.size();
    }
    return out;
}

bool isBuiltinDateFormat(int id) {
    // POI DateUtil.getSanityCheck / isADateFormat 的内置日期格式号
    if ((id >= 14 && id <= 22) || (id >= 27 && id <= 36) || (id >= 45 && id <= 47) ||
        (id >= 50 && id <= 58))
        return true;
    return false;
}

const std::string* member(const std::vector<ZipEntry>& entries, const std::string& name) {
    for (const auto& e : entries) {
        if (e.name == name) return &e.data;
    }
    return nullptr;
}

} // namespace

bool readZip(const std::string& bytes, std::vector<ZipEntry>& out, std::string* err) {
    out.clear();
    const size_t n = bytes.size();
    if (n < 22) { if (err) *err = "zip 过短"; return false; }
    size_t eocd = std::string::npos;
    const size_t begin = n > 66000 ? n - 66000 : 0;
    for (size_t i = n - 22; i >= begin; --i) {
        if (rd32(bytes, i) == 0x06054b50u) { eocd = i; break; }
        if (i == 0) break;
    }
    if (eocd == std::string::npos) { if (err) *err = "找不到 zip 中央目录结尾"; return false; }
    const unsigned int count = rd16(bytes, eocd + 10);
    size_t p = rd32(bytes, eocd + 16);
    for (unsigned int i = 0; i < count; ++i) {
        if (p + 46 > n || rd32(bytes, p) != 0x02014b50u) {
            if (err) *err = "zip 中央目录损坏";
            return false;
        }
        ZipEntry e;
        e.method = rd16(bytes, p + 10);
        const uint32_t csize = rd32(bytes, p + 20);
        const unsigned int nameLen = rd16(bytes, p + 28);
        const unsigned int extraLen = rd16(bytes, p + 30);
        const unsigned int commentLen = rd16(bytes, p + 32);
        const size_t localOff = rd32(bytes, p + 42);
        e.name = bytes.substr(p + 46, nameLen);
        p += 46 + nameLen + extraLen + commentLen;
        if (localOff + 30 > n || rd32(bytes, localOff) != 0x04034b50u) {
            if (err) *err = "zip 本地文件头损坏: " + e.name;
            return false;
        }
        const unsigned int ln = rd16(bytes, localOff + 26);
        const unsigned int le = rd16(bytes, localOff + 28);
        const size_t dataAt = localOff + 30 + ln + le;
        if (dataAt + csize > n) {
            if (err) *err = "zip 成员数据越界: " + e.name;
            return false;
        }
        const std::string raw = bytes.substr(dataAt, csize);
        if (e.method == 0) {
            e.data = raw;
        } else if (e.method == 8) {
            std::string local;
            if (!inflateRaw(raw, e.data, &local)) {
                if (err) *err = "inflate 失败(" + e.name + "): " + local;
                return false;
            }
        } else {
            if (err) *err = "不支持的 zip 压缩方式 " + std::to_string(e.method) + ": " + e.name;
            return false;
        }
        out.push_back(std::move(e));
    }
    return true;
}

std::string decimalHashHash(double value) {
    // DecimalFormat("#.##")：最多两位小数、HALF_EVEN、不分组、无尾随 0
    if (std::isnan(value)) return "NaN";
    if (std::isinf(value)) return value > 0 ? "∞" : "-∞";
    // 先按 2 位小数做"银行家舍入"
    const double scaled = value * 100.0;
    double r = std::nearbyint(scaled);   // 默认舍入模式就是 round-half-even
    if (std::fabs(scaled - std::floor(scaled) - 0.5) < 1e-9) r = std::floor(scaled) / 2.0 * 2.0 + (std::fmod(std::floor(scaled), 2.0) == 0 ? 0.0 : 1.0);
    const long long cents = static_cast<long long>(r);
    const bool neg = cents < 0;
    const unsigned long long a = static_cast<unsigned long long>(neg ? -cents : cents);
    std::ostringstream o;
    o << (neg ? "-" : "") << (a / 100);
    const unsigned long long frac = a % 100;
    if (frac % 10 == 0 && frac != 0) o << '.' << frac / 10;
    else if (frac != 0) {
        o << '.' << (frac < 10 ? "0" : "") << frac;
    }
    return o.str();
}

bool Xlsx::load(const std::string& bytes, bool dateWithTime, Xlsx& out, std::string* err) {
    std::vector<ZipEntry> entries;
    if (!readZip(bytes, entries, err)) return false;
    const std::string* shared = member(entries, "xl/sharedStrings.xml");
    const std::string* sheet = member(entries, "xl/worksheets/sheet1.xml");
    if (!sheet) {
        // 有些导出把 sheet 写成 sheet0.xml 或带路径；按第一个 worksheets/*.xml 兜底
        for (const auto& e : entries) {
            if (e.name.rfind("xl/worksheets/", 0) == 0 && e.name.size() > 4 &&
                e.name.substr(e.name.size() - 4) == ".xml") {
                sheet = &e.data;
                break;
            }
        }
    }
    if (!sheet) { if (err) *err = "xlsx 里找不到 sheet1"; return false; }

    std::vector<std::string> strings;
    if (shared) {
        for (const auto& si : findAll(*shared, "<si>", "</si>")) {
            std::string text;
            for (const auto& t : findAll(si, "<t", "</t>")) {
                const size_t gt = t.find('>');
                const size_t start = (gt != std::string::npos && t.size() > gt + 1) ? gt + 1 : 0;
                text += t.substr(start, t.size() - start - 4);   // 去掉 </t>
            }
            strings.push_back(unescapeXml(text));
        }
    }

    // 样式：cellXfs 的下标 -> 是否是日期格式
    std::vector<bool> styleIsDate;
    const std::string* styles = member(entries, "xl/styles.xml");
    if (styles) {
        std::map<int, bool> customDate;
        for (const auto& nf : findAll(*styles, "<numFmt ", "</numFmt>")) {
            // 自闭合写法更常见：重新用原始串扫
            (void)nf;
        }
        size_t pos = 0;
        while ((pos = styles->find("<numFmt ", pos)) != std::string::npos) {
            const size_t end = styles->find("/>", pos);
            if (end == std::string::npos) break;
            const std::string tag = styles->substr(pos, end - pos);
            const std::string id = attr(tag, "numFmtId");
            const std::string code = attr(tag, "formatCode");
            bool date = false;
            for (char c : code) {
                if (c == 'y' || c == 'M' || c == 'd' || c == 'h' || c == 's') date = true;
                if (c == '[' ) date = false;   // [h]:mm 之类的经过时间，这里不细究
            }
            if (!id.empty()) { try { customDate[std::stoi(id)] = date; } catch (...) {} }
            pos = end;
        }
        const size_t cx = styles->find("<cellXfs");
        if (cx != std::string::npos) {
            const size_t cxe = styles->find("</cellXfs>", cx);
            const std::string block = styles->substr(cx, cxe == std::string::npos ? std::string::npos : cxe - cx);
            size_t q = 0;
            while ((q = block.find("<xf ", q)) != std::string::npos) {
                const size_t end = block.find_first_of("/>", q);
                if (end == std::string::npos) break;
                const std::string id = attr(block.substr(q, end - q), "numFmtId");
                int numId = 0;
                try { numId = id.empty() ? 0 : std::stoi(id); } catch (...) {}
                bool d = isBuiltinDateFormat(numId);
                auto it = customDate.find(numId);
                if (it != customDate.end()) d = it->second;
                styleIsDate.push_back(d);
                q = end;
            }
        }
    }

    out.rows_.clear();
    out.present_.clear();
    size_t rp = 0;
    while ((rp = sheet->find("<row", rp)) != std::string::npos) {
        // "<rows>" 之类的前缀不能误认成 row 标签
        const char after = rp + 4 < sheet->size() ? (*sheet)[rp + 4] : ' ';
        if (after != ' ' && after != '>' && after != '/' && after != '\t' && after != '\n' &&
            after != '\r') {
            rp += 4;
            continue;
        }
        const bool selfClosing = sheet->find("/>", rp) == rp + 1 ||
                                 (sheet->find("</row>", rp) == std::string::npos);
        const size_t rend = selfClosing ? sheet->find("/>", rp) : sheet->find("</row>", rp);
        if (rend == std::string::npos) break;
        const std::string rowTag = sheet->substr(rp, (sheet->find('>', rp) == std::string::npos
                                                          ? rend
                                                          : sheet->find('>', rp)) - rp);
        const std::string rAttr = attr(rowTag, "r");
        size_t rowIdx = out.rows_.size();
        if (!rAttr.empty()) {
            try { rowIdx = std::stoul(rAttr) - 1; } catch (...) {}
        }
        if (rowIdx > 200000) { rp = rend; continue; }   // 恶意/异常行号，跳过
        out.rows_.resize(rowIdx + 1);
        out.present_.resize(rowIdx + 1, 0);
        out.present_[rowIdx] = 1;                        // 这一行确实存在（区别于"行缺失"）
        std::vector<std::string>& row = out.rows_[rowIdx];

        const std::string body = selfClosing ? std::string()
                                            : sheet->substr(rp, rend - rp);
        size_t cp = 0;
        while ((cp = body.find("<c ", cp)) != std::string::npos) {
            const size_t cend = body.find("</c>", cp);
            const size_t selfClose = body.find("/>", cp);
            std::string tag, inner;
            size_t next = cend;
            if (selfClose != std::string::npos && (cend == std::string::npos || selfClose < cend)) {
                tag = body.substr(cp, selfClose - cp);
                next = selfClose + 2;
            } else {
                if (cend == std::string::npos) break;
                tag = body.substr(cp, body.find('>', cp) - cp);
                const size_t vstart = body.find('>', cp) + 1;
                inner = body.substr(vstart, cend - vstart);
                next = cend + 4;
            }
            cp = next;
            const std::string ref = attr(tag, "r");
            const size_t col = ref.empty() ? row.size() : static_cast<size_t>(colIndex(ref));
            if (col > 4096) continue;
            row.resize(col + 1);
            const std::string type = attr(tag, "t");
            const std::string sIdx = attr(tag, "s");
            std::string& cell = row[col];
            if (type == "s") {
                const size_t vp = inner.find("<v>");
                std::string num;
                if (vp != std::string::npos) {
                    const size_t ve = inner.find("</v>", vp);
                    num = inner.substr(vp + 3, ve - vp - 3);
                }
                try { cell = num.empty() ? std::string() : strings.at(std::stoul(num)); }
                catch (...) { cell.clear(); }
                continue;
            }
            if (type == "inlineStr") {
                std::string text;
                for (const auto& t : findAll(inner, "<t", "</t>")) {
                    const size_t gt = t.find('>');
                    text += t.substr(gt + 1, t.size() - gt - 5);
                }
                cell = unescapeXml(text);
                continue;
            }
            if (type == "e") { cell.clear(); continue; }   // ERROR 单元格：Java 吞掉成空串
            std::string v;
            {
                const size_t vp = inner.find("<v>");
                if (vp == std::string::npos) {
                    cell.clear();
                    continue;
                }
                const size_t ve = inner.find("</v>", vp);
                v = inner.substr(vp + 3, ve - vp - 3);
            }
            double d = 0;
            try { d = std::stod(v); } catch (...) { cell = v; continue; }
            bool date = false;
            if (!sIdx.empty()) {
                try {
                    const size_t si = std::stoul(sIdx);
                    if (si < styleIsDate.size()) date = styleIsDate[si];
                } catch (...) {}
            }
            if (type == "b") {
                cell = d != 0 ? "true" : "false";
                continue;
            }
            if (date) {
                // Excel 序列号 -> epoch 毫秒（1900 历法，含那个闰年 bug 的 25569 天偏移）
                const long long ms = static_cast<long long>(std::llround((d - 25569.0) * 86400000.0));
                cell = dateWithTime
                    ? cm::utils::DateUtils::formatMillis(ms, "yyyy-MM-dd HH:mm:ss")
                    : cm::utils::DateUtils::formatMillis(ms, "yyyy/MM/dd");
                continue;
            }
            cell = decimalHashHash(d);
        }
        rp = rend + 1;
    }
    if (err) err->clear();
    return true;
}

} // namespace cm::utils
