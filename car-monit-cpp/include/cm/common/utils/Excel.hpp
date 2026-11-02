#pragma once
// 对应 Java: com.ruoyi.common.utils.poi.ExcelUtil
//
// ❌  deliberate gap: Java 使用 Apache POI 生成真正的 XLSX（Office Open XML）。
//    C++ 侧实现最小化的 CSV 导出（单 sheet、header row、string/number cells）。
//    对于 import，返回 Java 的错误消息路径。
//    如需真正的 XLSX，需要引入第三方库（如 libxlsxwriter）。
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::common::utils {

struct ExcelColumn {
    std::string name;     // 列名（中文）
    std::string field;    // JSON 字段名
    bool isNumeric{false}; // 是否为数字类型
    int width{20};        // 列宽（字符数）
};

class Excel {
public:
    /** 导出数据为 CSV 格式（对应 Java exportExcel） */
    static std::string exportCsv(const std::vector<ExcelColumn>& columns,
                                  const std::vector<Json>& rows,
                                  const std::string& sheetName = "Sheet1");

    /** 导出为简单的文本表格（用于测试/调试） */
    static std::string exportText(const std::vector<ExcelColumn>& columns,
                                   const std::vector<Json>& rows);

    /** 解析 CSV 行（对应 Java importExcel 的简化版本） */
    static std::vector<std::string> parseCsvLine(const std::string& line);

    /** 对 CSV 字段进行转义（处理逗号、引号、换行） */
    static std::string escapeCsvField(const std::string& field);
};

} // namespace cm::common::utils
