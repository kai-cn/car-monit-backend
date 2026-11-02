#pragma once
// 对应 Java: com.ruoyi.system.domain.SysOperLog
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/BaseEntity.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::domain {

struct SysOperLog : BaseEntity {
    std::optional<long long> operId;
    std::optional<std::string> title;
    std::optional<long long> businessType;
    std::vector<long long> businessTypes;
    std::optional<std::string> method;
    std::optional<std::string> requestMethod;
    std::optional<long long> operatorType;
    std::optional<std::string> operName;
    std::optional<std::string> deptName;
    std::optional<std::string> operUrl;
    std::optional<std::string> operIp;
    std::optional<std::string> operLocation;
    std::optional<std::string> operParam;
    std::optional<std::string> jsonResult;
    std::optional<long long> status;
    std::optional<std::string> errorMsg;
    std::optional<long long> operTime;

    Json toJson() const {
        Json j = Json::object();
        baseToJson(j);
        putI64(j, "operId", operId);
        putStr(j, "title", title);
        putI64(j, "businessType", businessType);
        Json btArr = Json::array();
        for (auto v : businessTypes) btArr.push_back(v);
        if (!businessTypes.empty()) j["businessTypes"] = btArr;
        putStr(j, "method", method);
        putStr(j, "requestMethod", requestMethod);
        putI64(j, "operatorType", operatorType);
        putStr(j, "operName", operName);
        putStr(j, "deptName", deptName);
        putStr(j, "operUrl", operUrl);
        putStr(j, "operIp", operIp);
        putStr(j, "operLocation", operLocation);
        putStr(j, "operParam", operParam);
        putStr(j, "jsonResult", jsonResult);
        putI64(j, "status", status);
        putStr(j, "errorMsg", errorMsg);
        putJsonDate(j, "operTime", operTime);
        return j;
    }

    void fromJson(const Json& j) {
        baseFromJson(j);
        operId = getI64(j, "operId");
        title = getStr(j, "title");
        businessType = getI64(j, "businessType");
        if (j.contains("businessTypes") && j["businessTypes"].is_array()) {
            businessTypes.clear();
            for (const auto& v : j["businessTypes"]) {
                if (v.is_number_integer()) businessTypes.push_back(v.get<long long>());
            }
        }
        method = getStr(j, "method");
        requestMethod = getStr(j, "requestMethod");
        operatorType = getI64(j, "operatorType");
        operName = getStr(j, "operName");
        deptName = getStr(j, "deptName");
        operUrl = getStr(j, "operUrl");
        operIp = getStr(j, "operIp");
        operLocation = getStr(j, "operLocation");
        operParam = getStr(j, "operParam");
        jsonResult = getStr(j, "jsonResult");
        status = getI64(j, "status");
        errorMsg = getStr(j, "errorMsg");
        operTime = getDate(j, "operTime");
    }

    static SysOperLog fromRow(const cm::db::Row& row) {
        SysOperLog r;
        r.operId = row.optI64("oper_id");
        r.title = row.get("title");
        r.businessType = row.optI64("business_type");
        r.method = row.get("method");
        r.requestMethod = row.get("request_method");
        r.operatorType = row.optI64("operator_type");
        r.operName = row.get("oper_name");
        r.deptName = row.get("dept_name");
        r.operUrl = row.get("oper_url");
        r.operIp = row.get("oper_ip");
        r.operLocation = row.get("oper_location");
        r.operParam = row.get("oper_param");
        r.jsonResult = row.get("json_result");
        r.status = row.optI64("status");
        r.errorMsg = row.get("error_msg");
        r.operTime = utils::DateUtils::parseDbDateTime(row.str("oper_time"));
        return r;
    }
};

} // namespace cm::domain
