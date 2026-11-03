#pragma once
// 对应 Java: com.ruoyi.common.core.page.TableDataInfo
// POJO，Jackson 按字段声明序输出：total -> rows -> code -> msg
#include <optional>
#include <string>

#include "cm/common/constant/HttpStatus.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::core::page {

class TableDataInfo {
public:
    long long total{0};
    std::optional<Json> rows;
    int code{0};
    std::optional<std::string> msg;

    /** 对应 new TableDataInfo()：code/msg 都是默认值（Java 侧只有 getDataTable 会填） */
    TableDataInfo() = default;
    /** 对应 BaseController.getDataTable：total/rows 之外，框架统一填 code=200、msg=查询成功 */
    TableDataInfo(Json list, long long total_)
        : total(total_), rows(std::move(list)), code(constant::HttpStatus::SUCCESS),
          msg(std::string("查询成功")) {}

    Json toJson() const {
        Json j = Json::object();
        j["total"] = total;
        j["rows"] = rows ? *rows : Json(nullptr);
        j["code"] = code;
        j["msg"] = msg ? Json(*msg) : Json(nullptr);
        return j;
    }
    std::string dump() const { return toJson().dump(); }
};

} // namespace cm::core::page
