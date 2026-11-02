// 对应 Java: com.ruoyi.system.mapper.SysLogininforMapper
// SQL 与 ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml 保持一致。
#include "cm/system/mapper/SysLogininforMapper.hpp"

#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

std::vector<cm::domain::SysLogininfor> SysLogininforMapper::selectLogininforList(const cm::domain::SysLogininfor& logininfor) {
    std::string sql = "select info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time from sys_logininfor";
    std::string where;
    if (logininfor.ipaddr && !logininfor.ipaddr->empty()) {
        where += " AND ipaddr like " + cm::db::Db::lit("%" + *logininfor.ipaddr + "%");
    }
    if (logininfor.status && !logininfor.status->empty()) {
        where += " AND status = " + cm::db::Db::lit(*logininfor.status);
    }
    if (logininfor.userName && !logininfor.userName->empty()) {
        where += " AND user_name like " + cm::db::Db::lit("%" + *logininfor.userName + "%");
    }
    if (logininfor.params.contains("beginTime") && logininfor.params["beginTime"].is_string()) {
        std::string beginTime = logininfor.params["beginTime"].get<std::string>();
        if (!beginTime.empty()) {
            where += " AND date_format(login_time,'%y%m%d') >= date_format(" + cm::db::Db::lit(beginTime) + ",'%y%m%d')";
        }
    }
    if (logininfor.params.contains("endTime") && logininfor.params["endTime"].is_string()) {
        std::string endTime = logininfor.params["endTime"].get<std::string>();
        if (!endTime.empty()) {
            where += " AND date_format(login_time,'%y%m%d') <= date_format(" + cm::db::Db::lit(endTime) + ",'%y%m%d')";
        }
    }
    if (!where.empty()) {
        sql += " WHERE" + where.substr(4); // 去掉开头的 " AND"
    }
    sql += " ORDER BY info_id DESC";

    cm::db::Result res;
    std::vector<cm::domain::SysLogininfor> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) {
        list.push_back(cm::domain::SysLogininfor::fromRow(row));
    }
    return list;
}

int SysLogininforMapper::deleteLogininforByIds(const std::vector<long long>& infoIds) {
    if (infoIds.empty()) return 0;
    std::string sql = "DELETE FROM sys_logininfor WHERE info_id IN " + cm::db::Db::inList(infoIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return static_cast<int>(affected);
}

void SysLogininforMapper::cleanLogininfor() {
    cm::db::Db::instance().execute("TRUNCATE TABLE sys_logininfor");
}

} // namespace cm::system::mapper
