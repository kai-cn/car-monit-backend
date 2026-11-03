// 对应 Java: com.ruoyi.common.utils.poi.ExcelUtil
#include "cm/common/utils/Excel.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "cm/common/compat/Path.hpp"
#include "cm/common/utils/Deflate.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/framework/config/AppConfig.hpp"

namespace cm::common::utils {

std::string Excel::escapeCsvField(const std::string& field) {
    // 如果字段包含逗号、引号或换行，需要用引号包裹并转义内部引号
    bool needsQuoting = false;
    for (char c : field) {
        if (c == ',' || c == '"' || c == '\n' || c == '\r') {
            needsQuoting = true;
            break;
        }
    }
    if (!needsQuoting) return field;

    std::string result = "\"";
    for (char c : field) {
        if (c == '"') result += "\"\"";
        else result += c;
    }
    result += "\"";
    return result;
}

std::vector<std::string> Excel::parseCsvLine(const std::string& line) {
    std::vector<std::string> fields;
    std::string current;
    bool inQuotes = false;
    size_t i = 0;

    while (i < line.size()) {
        char c = line[i];
        if (inQuotes) {
            if (c == '"') {
                if (i + 1 < line.size() && line[i + 1] == '"') {
                    current += '"';
                    i += 2;
                } else {
                    inQuotes = false;
                    ++i;
                }
            } else {
                current += c;
                ++i;
            }
        } else {
            if (c == '"') {
                inQuotes = true;
                ++i;
            } else if (c == ',') {
                fields.push_back(current);
                current.clear();
                ++i;
            } else {
                current += c;
                ++i;
            }
        }
    }
    fields.push_back(current);
    return fields;
}

std::string Excel::exportCsv(const std::vector<ExcelColumn>& columns,
                              const std::vector<Json>& rows,
                              const std::string& sheetName) {
    std::ostringstream ss;

    // 写入 UTF-8 BOM（Excel 识别）
    ss << "\xEF\xBB\xBF";

    // 写入表头
    for (size_t i = 0; i < columns.size(); ++i) {
        if (i > 0) ss << ",";
        ss << escapeCsvField(columns[i].name);
    }
    ss << "\n";

    // 写入数据行
    for (const auto& row : rows) {
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i > 0) ss << ",";
            const auto& col = columns[i];
            auto it = row.find(col.field);
            if (it == row.end() || it->is_null()) {
                // 空值
            } else if (it->is_string()) {
                ss << escapeCsvField(it->get<std::string>());
            } else if (it->is_number_integer()) {
                ss << it->get<long long>();
            } else if (it->is_number_float()) {
                ss << it->get<double>();
            } else if (it->is_boolean()) {
                ss << (it->get<bool>() ? "true" : "false");
            } else {
                ss << escapeCsvField(it->dump());
            }
        }
        ss << "\n";
    }

    return ss.str();
}

std::string Excel::exportText(const std::vector<ExcelColumn>& columns,
                               const std::vector<Json>& rows) {
    std::ostringstream ss;

    // 写入表头
    for (size_t i = 0; i < columns.size(); ++i) {
        if (i > 0) ss << "\t";
        ss << columns[i].name;
    }
    ss << "\n";

    // 写入数据行
    for (const auto& row : rows) {
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i > 0) ss << "\t";
            const auto& col = columns[i];
            auto it = row.find(col.field);
            if (it == row.end() || it->is_null()) {
                // 空值
            } else if (it->is_string()) {
                ss << it->get<std::string>();
            } else if (it->is_number_integer()) {
                ss << it->get<long long>();
            } else if (it->is_number_float()) {
                ss << it->get<double>();
            } else if (it->is_boolean()) {
                ss << (it->get<bool>() ? "true" : "false");
            } else {
                ss << it->dump();
            }
        }
        ss << "\n";
    }

    return ss.str();
}

namespace {

/** 小端写入（zip 的字段一律 little-endian，且不能受本机字节序影响） */
void put16(std::string& out, uint16_t v) {
    out.push_back(static_cast<char>(v & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
}
void put32(std::string& out, uint32_t v) {
    out.push_back(static_cast<char>(v & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
    out.push_back(static_cast<char>((v >> 16) & 0xff));
    out.push_back(static_cast<char>((v >> 24) & 0xff));
}

/** ZIP（store）：Excel/unzip 都接受未压缩条目，省去自己实现 deflate 的兼容风险 */
struct ZipEntry {
    std::string name;
    std::string data;
};

std::string makeZip(const std::vector<ZipEntry>& entries) {
    namespace du = cm::utils;
    std::string out, central;
    uint32_t offset = 0;
    // 固定时间戳：同样内容产出同样字节，便于差分比对
    const uint16_t dosTime = 0, dosDate = (1 << 5) | 1;  // 1980-01-01
    for (const auto& e : entries) {
        const uint32_t crc = du::crc32(e.data);
        const auto size = static_cast<uint32_t>(e.data.size());
        const auto nameLen = static_cast<uint16_t>(e.name.size());

        std::string local;
        local += "PK\x03\x04";
        put16(local, 20);      // version needed to extract
        put16(local, 0);       // general purpose flags
        put16(local, 0);       // method = store
        put16(local, dosTime);
        put16(local, dosDate);
        put32(local, crc);
        put32(local, size);    // compressed size
        put32(local, size);    // uncompressed size
        put16(local, nameLen);
        put16(local, 0);       // extra length
        local += e.name;
        local += e.data;

        std::string cen;
        cen += "PK\x01\x02";
        put16(cen, 20);        // version made by
        put16(cen, 20);        // version needed
        put16(cen, 0);
        put16(cen, 0);
        put16(cen, dosTime);
        put16(cen, dosDate);
        put32(cen, crc);
        put32(cen, size);
        put32(cen, size);
        put16(cen, nameLen);
        put16(cen, 0);         // extra
        put16(cen, 0);         // comment
        put16(cen, 0);         // disk number start
        put16(cen, 0);         // internal attributes
        put32(cen, 0);         // external attributes
        put32(cen, offset);    // relative offset of local header
        cen += e.name;

        offset += static_cast<uint32_t>(local.size());
        out += local;
        central += cen;
    }
    const uint32_t cdOffset = offset;
    out += central;

    std::string eocd;
    eocd += "PK\x05\x06";
    put16(eocd, 0);                                   // this disk
    put16(eocd, 0);                                   // disk with CD
    put16(eocd, static_cast<uint16_t>(entries.size()));
    put16(eocd, static_cast<uint16_t>(entries.size()));
    put32(eocd, static_cast<uint32_t>(central.size()));
    put32(eocd, cdOffset);
    put16(eocd, 0);                                   // comment length
    out += eocd;
    return out;
}

std::string xmlEscape(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '&': out += "&amp;"; break;
            case '<': out += "&lt;"; break;
            case '>': out += "&gt;"; break;
            case '"': out += "&quot;"; break;
            default:
                // XML 1.0 不允许的控制字符直接丢掉，否则会生成打不开的文件
                if (static_cast<unsigned char>(c) < 0x20 && c != '\t' && c != '\n' && c != '\r') break;
                out.push_back(c);
        }
    }
    return out;
}

std::string colLetter(size_t idx) {
    std::string s;
    ++idx;
    while (idx) {
        int rem = static_cast<int>((idx - 1) % 26);
        s.insert(s.begin(), static_cast<char>('A' + rem));
        idx = (idx - 1) / 26;
    }
    return s;
}

/** 单元格值 -> <c>；数字走 <v>，其余走 inlineStr（与 POI 的字符串单元格行为一致） */
std::string cell(const ExcelColumn& col, size_t rowNo, size_t colNo, const Json& row) {
    const std::string ref = colLetter(colNo) + std::to_string(rowNo);
    const std::string head = "<c r=\"" + ref + "\"";
    auto it = row.find(col.field);
    if (it == row.end() || it->is_null()) return head + "/>";  // 空单元格

    if (col.isNumeric && it->is_number()) return head + "><v>" + it->dump() + "</v></c>";

    const std::string text = it->is_string() ? it->get<std::string>() : it->dump();
    return head + " t=\"inlineStr\"><is><t>" + xmlEscape(text) + "</t></is></c>";
}

} // namespace

std::string Excel::exportXlsx(const std::vector<ExcelColumn>& columns, const std::vector<Json>& rows,
                              const std::string& sheetName) {
    std::ostringstream sheet;
    sheet << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
          << "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData>";
    sheet << "<row r=\"1\">";
    for (size_t c = 0; c < columns.size(); ++c) {
        sheet << "<c r=\"" << colLetter(c) << "1\" t=\"inlineStr\"><is><t>"
              << xmlEscape(columns[c].name) << "</t></is></c>";
    }
    sheet << "</row>";
    for (size_t r = 0; r < rows.size(); ++r) {
        sheet << "<row r=\"" << (r + 2) << "\">";
        for (size_t c = 0; c < columns.size(); ++c)
            sheet << cell(columns[c], r + 2, c, rows[r]);
        sheet << "</row>";
    }
    sheet << "</sheetData></worksheet>";

    std::ostringstream cols;
    for (size_t c = 0; c < columns.size(); ++c)
        cols << "<col min=\"" << (c + 1) << "\" max=\"" << (c + 1) << "\" width=\"" << columns[c].width
             << "\" customWidth=\"1\"/>";

    std::vector<ZipEntry> parts;
    parts.push_back({"[Content_Types].xml",
                     "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                     "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
                     "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
                     "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
                     "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
                     "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
                     "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
                     "</Types>"});
    parts.push_back({"_rels/.rels",
                     "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                     "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
                     "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
                     "</Relationships>"});
    std::ostringstream wb;
    wb << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
       << "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\""
          " xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><sheets>"
       << "<sheet name=\"" << xmlEscape(sheetName.empty() ? std::string("Sheet1") : sheetName)
       << "\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>";
    parts.push_back({"xl/workbook.xml", wb.str()});
    parts.push_back({"xl/_rels/workbook.xml.rels",
                     "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                     "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
                     "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
                     "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>"
                     "</Relationships>"});
    parts.push_back({"xl/styles.xml",
                     "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                     "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
                     "<fonts count=\"1\"><font><sz val=\"11\"/><name val=\"Calibri\"/></font></fonts>"
                     "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
                     "<borders count=\"1\"><border/></borders>"
                     "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
                     "<cellXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/></cellXfs>"
                     "</styleSheet>"});
    // 列宽 + sheetData 合成最终的 worksheet（sheet 串里已含 worksheet 头尾，取其 sheetData 段）
    std::string sd = sheet.str();
    size_t begin = sd.find("<sheetData");
    size_t end = sd.rfind("</sheetData>");
    std::string sheetData = begin == std::string::npos
                                ? std::string("<sheetData/>")
                                : sd.substr(begin, end - begin + std::string("</sheetData>").size());
    std::ostringstream finalSheet;
    finalSheet << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
               << "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
               << "<cols>" << cols.str() << "</cols>" << sheetData << "</worksheet>";
    parts.push_back({"xl/worksheets/sheet1.xml", finalSheet.str()});
    return makeZip(parts);
}

std::string Excel::encodingFilename(const std::string& sheetName) {
    // Java: UUID.randomUUID() + "_" + filename + ".xlsx" —— 36 位带横线的 UUID
    return cm::utils::uuid() + "_" + sheetName + ".xlsx";
}

std::string Excel::writeDownloadFile(const std::string& filename, const std::string& bytes) {
    const std::string dir = cm::config::AppConfig::instance().profile + "/download";
    std::error_code ec;
    // 落盘一律走 fsPath：Windows 下 std::filesystem 会把窄字符串按 GBK 解释，
    // 而这里的文件名是 UTF-8 中文（"<uuid>_登录日志.xlsx"）。
    const std::filesystem::path file = cm::compat::fsPath(dir) / cm::compat::fsPath(filename);
    std::filesystem::create_directories(file.parent_path(), ec);  // 对应 getAbsoluteFile 里的 mkdirs
    std::ofstream f(file, std::ios::binary | std::ios::trunc);
    if (!f.is_open()) return std::string();
    f.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    f.close();
    return filename;
}

} // namespace cm::common::utils
