// ImportSysUtil / ImportUtil 的 C++ 对应物，接口语义见 hpp 顶部。
#include "cm/web/util/ImportExcel.hpp"

#include <regex>

#include "cm/common/utils/CommonUtil.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::web::importx {
namespace {

using cm::utils::StringUtils;

/** ImportUtil 里那 6 个正则（Java 用 Pattern.matches，整串匹配 ⇒ 这里 regex_match）。
 *  \d 在两边都是 ASCII 数字，不受 locale 影响。 */
const std::regex RE_DECIMAL(R"(^(-?\d+)(\.\d+)?$)");                 // 2 小数
const std::regex RE_POSINT(R"(^[0-9]*$)");                           // 3 正整数
const std::regex RE_DATE(R"([0-9]{4}-[0-9]{2}-[0-9]{2})");           // 4 年月日
const std::regex RE_IDCARD(R"(^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X|x)$)");
const std::regex RE_YM(R"(^\d{4}(\-|\/|\.)\d{1,2}$)");               // 6 年月
const std::regex RE_DATETIME(R"(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$)");  // 8
const std::regex RE_NUMBER(R"(^(\-|\+)?\d+(\.\d+)?$)");              // 7

std::string cell(const cm::utils::Xlsx& x, size_t r, size_t c) {
    if (r >= x.rows().size() || c >= x.rows()[r].size()) return "";
    // getCellFormatValue07/08 的返回值都过了一遍 .trim()
    return StringUtils::trim(x.rows()[r][c]);
}

} // namespace

Json ImportErrorEntity::toJson() const {
    Json j = Json::object();
    j["rowNo"] = rowNo;
    j["colName"] = colName;
    j["message"] = message;
    return j;
}

ImportErrorEntity errorBo(int row, const std::string& colName, const std::string& msg) {
    ImportErrorEntity e;
    e.rowNo = row + 1;   // Java: errorBO.setRowNo(row+1)
    e.colName = colName;
    e.message = msg;
    return e;
}

bool colVda(const cm::utils::Xlsx& x, size_t rowNum, const std::vector<std::string>& colsName) {
    // Java: sheet.getRow(0) == null -> false。空表头行直接算模板不符。
    if (!x.rowPresent(rowNum)) return false;
    for (size_t j = 0; j < colsName.size(); ++j) {
        if (colsName[j] != cell(x, rowNum, j)) return false;
    }
    return true;
}

std::vector<std::vector<std::string>> dataRtn(const cm::utils::Xlsx& x, size_t startRow,
                                              size_t width, const std::vector<int>& skipCols) {
    std::vector<std::vector<std::string>> out;
    const long long last = x.lastRowNum();
    for (long long i = static_cast<long long>(startRow); i <= last; ++i) {
        // row == null -> getLastCellNum() NPE -> catch 后 break（中间空一行，后面全不读）
        if (!x.rowPresent(static_cast<size_t>(i))) break;
        const std::string first = cell(x, static_cast<size_t>(i), 0);
        if (first == "break" || first == "结束") break;
        std::vector<std::string> strs(width);
        for (size_t z = 0; z < width; ++z) {
            // 这些列 Java 留 null，后面 ImportUtil.isNull 变 "" —— 语义等价，这里直接空串
            if (std::find(skipCols.begin(), skipCols.end(), static_cast<int>(z)) !=
                skipCols.end()) {
                continue;
            }
            strs[z] = cell(x, static_cast<size_t>(i), z);
        }
        out.push_back(std::move(strs));
    }
    return out;
}

bool importRow(std::vector<ImportErrorEntity>& errorList,
               const std::vector<ImportEntity>& boList, int index,
               const std::vector<std::string>& excelVals, Json& objMap) {
    objMap = Json::object();
    for (size_t i = 0; i < boList.size(); ++i) {
        const std::string value =
            i < excelVals.size() ? StringUtils::trim(excelVals[i]) : std::string();
        const ImportEntity& bo = boList[i];
        objMap[bo.colProp] = Json(value);   // colProp 为空串时键就是 ""，Java 同样会覆盖
        const std::string rules = cm::utils::CommonUtil::isNull(bo.valadRes);
        if (rules.empty()) continue;
        for (const auto& gz : javaSplitComma(rules)) {
            if (gz == "1" && value.empty()) {
                errorList.push_back(errorBo(index + 1, bo.colName, "不能为空"));
            }
            if (value.empty()) continue;
            bool bad = false;
            std::string msg;
            if (gz == "2") {
                bad = !std::regex_match(value, RE_DECIMAL);
                msg = "不是小数";
            } else if (gz == "3") {
                bad = !std::regex_match(value, RE_POSINT);
                msg = "不是正整数";
            } else if (gz == "4") {
                bad = !std::regex_match(value, RE_DATE);
                msg = "日期格式（年-月-日）不正确";
            } else if (gz == "5") {
                bad = !std::regex_match(value, RE_IDCARD);
                msg = "身份证号码不正确";
            } else if (gz == "6") {
                bad = !std::regex_match(value, RE_YM);
                msg = "日期格式（年-月）不正确";
            } else if (gz == "7") {
                bad = !std::regex_match(value, RE_NUMBER);
                msg = "不是数值";
            } else if (gz == "8") {
                bad = !std::regex_match(value, RE_DATETIME);
                msg = "日期格式（年月日时分秒）不正确";
            }
            if (bad) errorList.push_back(errorBo(index + 1, bo.colName, msg));
        }
    }
    // Java: if (errorList.size() == 0) { 转对象 } —— 用的是**共享**的 errorList
    return errorList.empty();
}

std::vector<std::string> javaSplitComma(const std::string& s) {
    std::vector<std::string> out;
    if (s.empty()) return out;   // Java "".split(",") -> [""]，但调用点都先判过空
    size_t pos = 0;
    std::vector<std::string> parts;
    while (true) {
        const size_t c = s.find(',', pos);
        if (c == std::string::npos) { parts.push_back(s.substr(pos)); break; }
        parts.push_back(s.substr(pos, c - pos));
        pos = c + 1;
    }
    // limit=0 的 split 会把尾部空串全丢掉
    while (!parts.empty() && parts.back().empty()) parts.pop_back();
    if (parts.empty() && s.find(',') == std::string::npos) return {std::string()};
    return parts;
}

} // namespace cm::web::importx
