// 对应 Java: com.ruoyi.common.utils.poi.ExcelUtil
#include "cm/common/utils/Excel.hpp"

#include <sstream>

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

} // namespace cm::common::utils
