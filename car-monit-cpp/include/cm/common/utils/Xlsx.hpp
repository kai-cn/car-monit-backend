#pragma once
// 最小可用的 xlsx 读取器（zip + sheet 单元格 → 文本）。
//
// 对应 Java: org.apache.poi.xssf.usermodel.XSSFWorkbook + Workbook.getSheetAt(0)
//            + ImportSysUtil.getCellFormatValue07/08 的取值规则
//
// 为什么自己写：导入类接口（/manager/carinfo/import、/manager/exceptrecord/import）
// 必须解析上传的 xlsx，而本工程要求零第三方依赖。xlsx = zip(deflate) + OOXML，
// 所以先要一个 zip 读取器（配 Inflate.hpp）再要一点 XML 扫描。
//
// 只支持 .xlsx —— 与这两个接口的 Java 端一致（`fileName.lastIndexOf(".xlsx") != -1` 才继续），
// .xls(HSSF) 的二进制格式这里不实现。
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace cm::utils {

struct ZipEntry {
    std::string name;
    std::string data;
    unsigned int method{0};
};

/** 读 zip（支持 store=0 与 deflate=8）。按中央目录顺序返回，找不到的成员不算错误 */
bool readZip(const std::string& bytes, std::vector<ZipEntry>& out, std::string* err);

/** DecimalFormat("#.##")：最多 2 位小数、HALF_EVEN、不分组、去掉尾随 0 */
std::string decimalHashHash(double value);

class Xlsx {
public:
    /** dateMode: true ⇒ 日期格式化成 yyyy-MM-dd HH:mm:ss（getCellFormatValue08），
     *  false ⇒ yyyy/MM/dd（getCellFormatValue07）。两个导入接口用的就是这两套。 */
    static bool load(const std::string& bytes, bool dateWithTime, Xlsx& out, std::string* err);

    /** rows[r][c]：r 是 sheet 里的行号（0 基），c 是列号（0 基，按单元格引用 A=0 对齐）。
     *  缺失的单元格是空串，与 POI 的 getCell(...) == null → "" 一致。 */
    const std::vector<std::vector<std::string>>& rows() const { return rows_; }
    int lastRowNum() const { return rows_.empty() ? -1 : static_cast<int>(rows_.size()) - 1; }

    /** 这一行在 sheet 里**存在**吗。POI 的 getRow(r) 对不存在的行返回 null，
     *  而 dataRtnExcel07/08 拿到 null 会 NPE 并被 catch 成 break —— 中间空一行 ⇒ 后面的数据全不读。
     *  "行存在但没有单元格"（<row r="5"/>）则是另一回事：那不算 null，循环继续。
     *  所以只凭 rows()[r].empty() 区分不了这两种，必须单独记。 */
    bool rowPresent(size_t r) const { return r < present_.size() && present_[r] != 0; }

private:
    std::vector<std::vector<std::string>> rows_;
    std::vector<unsigned char> present_;
};

} // namespace cm::utils
