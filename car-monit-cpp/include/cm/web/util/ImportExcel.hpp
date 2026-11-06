#pragma once
// 对应 Java: com.ruoyi.web.util.{ImportSysUtil, ImportUtil, ImportEntity, ImportErrorEntity}
//
// 两个 Excel 导入接口（/manager/carinfo/import、/manager/exceptrecord/import）共用这一套
// "表头校验 + 逐格规则校验 + 行转对象"的机器。规则号与文案必须逐字照抄：
//   1 必填 / 2 小数 / 3 正整数 / 4 日期(年月日) / 5 身份证 / 6 年月 / 7 数值 / 8 日期(年月日时分秒)
// 一条规则串可以写多个（"1,2"），逗号后split(",")，"1" 之外的那些只在值非空时才检查。
//
// ⚠️ 三处"看起来像 bug 但必须保留"的行为：
//   * errorList 是**跨行共享**的：一旦某行报错，后续所有行都不会进 importList
//     （控制器判的是 `errorList.size()==0`，不是"这一行有没有错"）；
//   * rowNo = index + 2（getErrorBO 内部又 +1）。exceptrecord 的数据从第 4 行开始，
//     但行号还是从 2 起 —— 报出来的行号和 Excel 里的实际行号差 2；
//   * 超过 100 条才 break（`> 100`），所以 errorList 最多 101 条。
#include <optional>
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/Xlsx.hpp"

namespace cm::web::importx {

/** ImportEntity：colName=表头文本，colProp=实体属性名（空串=这列丢弃），valadRes=规则串 */
struct ImportEntity {
    std::string colName;
    std::string colProp;
    std::string valadRes;
};

/** ImportErrorEntity：字段声明序 rowNo/colName/message，Jackson 就按这个顺序输出 */
struct ImportErrorEntity {
    int rowNo{0};
    std::string colName;
    std::string message;
    Json toJson() const;
};

/** 对应 ImportSysUtil.getErrorBO(row, col, msg)：注意里面的 +1 */
ImportErrorEntity errorBo(int row, const std::string& colName, const std::string& msg);

/** 对应 colVdaExcel07/08：第 rowNum 行（0 基）的前 n 格必须逐格等于 colsName[i] */
bool colVda(const cm::utils::Xlsx& x, size_t rowNum, const std::vector<std::string>& colsName);

/** 对应 dataRtnExcel07/08：从 startRow（0 基）读到 lastRowNum。
 *  skipCols 非空时，那些列留 null（exceptrecord 用 strNum 跳过合并表头列）。
 *  ⚠️ Java 在这里靠 `row.getLastCellNum()` 的 NPE 做 break：行不存在 ⇒ 整表读取提前结束；
 *     首列文本是 "break"/"结束" 同样 break。空行（行在、没格）不 break。 */
std::vector<std::vector<std::string>> dataRtn(const cm::utils::Xlsx& x, size_t startRow,
                                              size_t width,
                                              const std::vector<int>& skipCols = {});

/** 对应 ImportUtil.importExcel：逐格按 valadRes 校验，值塞进 objMap（colProp 为空的列也塞，
 *  键就是 ""，Java 的 HashMap 里反复覆盖同一个键）。
 *  返回 false 表示 errorList 非空 ⇒ 控制器拿不到对象，这一行不进 importList。 */
bool importRow(std::vector<ImportErrorEntity>& errorList,
               const std::vector<ImportEntity>& boList, int index,
               const std::vector<std::string>& excelVals, Json& objMap);

/** Java String.split(",")：丢掉尾部空串（"a," -> ["a"]，"a,,b" -> ["a","","b"]） */
std::vector<std::string> javaSplitComma(const std::string& s);

} // namespace cm::web::importx
