// 对应 Java: com.ruoyi.system.mapper.SysOperLogMapper
// SQL 与 ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml 保持一致。
#include "cm/system/mapper/SysOperLogMapper.hpp"

#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

namespace {
constexpr const char* kSelectOperLogVo =
    "select oper_id, title, business_type, method, request_method, operator_type, oper_name, dept_name, "
    "oper_url, oper_ip, oper_location, oper_param, json_result, status, error_msg, oper_time "
    "from sys_oper_log";
}

std::vector<cm::domain::SysOperLog> SysOperLogMapper::selectOperLogList(const cm::domain::SysOperLog& operLog) {
    std::string sql = kSelectOperLogVo;
    std::string where;
    if (operLog.title && !operLog.title->empty()) {
        where += " AND title like " + cm::db::Db::lit("%" + *operLog.title + "%");
    }
    if (operLog.businessType) {
        where += " AND business_type = " + cm::db::Db::lit(*operLog.businessType);
    }
    if (!operLog.businessTypes.empty()) {
        where += " AND business_type IN " + cm::db::Db::inList(operLog.businessTypes);
    }
    if (operLog.status) {
        where += " AND status = " + cm::db::Db::lit(*operLog.status);
    }
    if (operLog.operName && !operLog.operName->empty()) {
        where += " AND oper_name like " + cm::db::Db::lit("%" + *operLog.operName + "%");
    }
    if (operLog.params.contains("beginTime") && operLog.params["beginTime"].is_string()) {
        std::string beginTime = operLog.params["beginTime"].get<std::string>();
        if (!beginTime.empty()) {
            where += " AND date_format(oper_time,'%y%m%d') >= date_format(" + cm::db::Db::lit(beginTime) + ",'%y%m%d')";
        }
    }
    if (operLog.params.contains("endTime") && operLog.params["endTime"].is_string()) {
        std::string endTime = operLog.params["endTime"].get<std::string>();
        if (!endTime.empty()) {
            where += " AND date_format(oper_time,'%y%m%d') <= date_format(" + cm::db::Db::lit(endTime) + ",'%y%m%d')";
        }
    }
    if (!where.empty()) {
        sql += " WHERE" + where.substr(4); // 去掉开头的 " AND"
    }
    sql += " ORDER BY oper_id DESC";

    cm::db::Result res;
    std::vector<cm::domain::SysOperLog> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) {
        list.push_back(cm::domain::SysOperLog::fromRow(row));
    }
    return list;
}

std::optional<cm::domain::SysOperLog> SysOperLogMapper::selectOperLogById(long long operId) {
    std::string sql = std::string(kSelectOperLogVo) + " WHERE oper_id = " + cm::db::Db::lit(operId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return cm::domain::SysOperLog::fromRow(res.rows.front());
}

int SysOperLogMapper::deleteOperLogByIds(const std::vector<long long>& operIds) {
    if (operIds.empty()) return 0;
    std::string sql = "DELETE FROM sys_oper_log WHERE oper_id IN " + cm::db::Db::inList(operIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

void SysOperLogMapper::cleanOperLog() {
    cm::db::Db::instance().execute("TRUNCATE TABLE sys_oper_log");
}

} // namespace cm::system::mapper
