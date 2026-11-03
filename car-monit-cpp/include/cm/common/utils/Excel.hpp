#pragma once
// 对应 Java: com.ruoyi.common.utils.poi.ExcelUtil
//
// 导出走真正的 Office Open XML：xlsx 本质是一个 zip 包，这里有最小可用的
// zip(store) + 单 sheet 生成器，因此不再需要第三方库。
// 导入（读 xlsx）仍未实现 —— 那是 POI 的另一半，见 COMPATIBILITY.md §2.3。
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::common::utils {

struct ExcelColumn {
    std::string name;     // 列名（中文）
    std::string field;    // JSON 字段名
    bool isNumeric{false}; // 是否为数字类型（Java @Excel(cellType = ColumnType.NUMERIC)）
    int width{16};        // 列宽（Java @Excel：double width() default 16）
};

class Excel {
public:
    /** 导出数据为 CSV 格式（保留给调试/文本型下载） */
    static std::string exportCsv(const std::vector<ExcelColumn>& columns,
                                  const std::vector<Json>& rows,
                                  const std::string& sheetName = "Sheet1");

    /** 对应 Java 用 POI 产出的 .xlsx 字节（单 sheet，inline string，无共享表） */
    static std::string exportXlsx(const std::vector<ExcelColumn>& columns,
                                   const std::vector<Json>& rows,
                                   const std::string& sheetName = "Sheet1");

    /** 对应 ExcelUtil.encodingFilename：UUID.randomUUID() + "_" + sheetName + ".xlsx" */
    static std::string encodingFilename(const std::string& sheetName);

    /** 对应 getAbsoluteFile + wb.write：落到 profile/download 目录，返回文件名 */
    static std::string writeDownloadFile(const std::string& filename, const std::string& bytes);

    /** 导出为简单的文本表格（用于测试/调试） */
    static std::string exportText(const std::vector<ExcelColumn>& columns,
                                   const std::vector<Json>& rows);

    /** 解析 CSV 行（对应 Java importExcel 的简化版本） */
    static std::vector<std::string> parseCsvLine(const std::string& line);

    /** 对 CSV 字段进行转义（处理逗号、引号、换行） */
    static std::string escapeCsvField(const std::string& field);
};

} // namespace cm::common::utils
