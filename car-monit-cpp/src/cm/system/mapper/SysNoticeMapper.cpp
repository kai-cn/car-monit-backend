// 对应 Java: SysNoticeMapper
#include "cm/system/mapper/SysNoticeMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {
namespace {
constexpr const char* kSelectNoticeVo =
    "select t.notice_id, t.notice_title, t.notice_type, cast(t.notice_content as char) as notice_content,"
    " t.status, t.create_by, t.create_time, t.update_by, t.update_time, t.remark,"
    " t.buss_id, t.buss_name, t.tenant_id from sys_notice t";
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
}

cm::domain::SysNotice SysNoticeMapper::mapNotice(const cm::db::Row& row) {
    cm::domain::SysNotice n;
    n.noticeId = row.optI64("notice_id");
    n.noticeTitle = row.get("notice_title");
    n.noticeType = row.get("notice_type");
    n.noticeContent = row.get("notice_content");
    n.status = row.get("status");
    n.createBy = row.get("create_by");
    n.createTime = parseDbDate(row.get("create_time"));
    n.updateBy = row.get("update_by");
    n.updateTime = parseDbDate(row.get("update_time"));
    n.remark = row.get("remark");
    n.bussId = row.get("buss_id");
    n.bussName = row.get("buss_name");
    n.tenantId = row.optI64("tenant_id");
    return n;
}

std::string SysNoticeMapper::selectNoticeListSql(const cm::domain::SysNotice& notice) {
    std::string sql = std::string(kSelectNoticeVo) + " where 1=1";
    if (notice.noticeTitle && !notice.noticeTitle->empty())
        sql += " AND t.notice_title like " + cm::db::bind("%" + *notice.noticeTitle + "%");
    if (notice.noticeType && !notice.noticeType->empty())
        sql += " AND t.notice_type = " + cm::db::bind(*notice.noticeType);
    if (notice.createBy && !notice.createBy->empty())
        sql += " AND t.create_by = " + cm::db::bind(*notice.createBy);
    if (notice.status && !notice.status->empty())
        sql += " AND t.status = " + cm::db::bind(*notice.status);
    if (notice.bussId && !notice.bussId->empty())
        sql += " AND t.buss_id = " + cm::db::bind(*notice.bussId);
    if (notice.bussName && !notice.bussName->empty())
        sql += " AND t.buss_name like " + cm::db::bind("%" + *notice.bussName + "%");
    if (notice.tenantId)
        sql += " AND (t.TENANT_ID = " + cm::db::bind(*notice.tenantId) + " or t.TENANT_ID = 100)";
    if (notice.noticeContent && !notice.noticeContent->empty())
        sql += " AND (t.notice_content = " + cm::db::bind(*notice.noticeContent) + ")";
    sql += " order by t.create_time desc";
    return sql;
}

std::pair<std::vector<cm::domain::SysNotice>, long long> SysNoticeMapper::selectNoticeListEntityPage(const cm::domain::SysNotice& notice,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectNoticeListSql(notice);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysNotice> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapNotice(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysNotice> SysNoticeMapper::selectNoticeList(const cm::domain::SysNotice& notice) {
    const std::string sql = selectNoticeListSql(notice);
    cm::db::Result res;
    std::vector<cm::domain::SysNotice> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapNotice(row));
    return list;
}

std::optional<cm::domain::SysNotice> SysNoticeMapper::selectNoticeById(long long noticeId) {
    std::string sql = std::string(kSelectNoticeVo) + " where t.notice_id = " + cm::db::bind(noticeId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapNotice(res.rows.front());
}

long long SysNoticeMapper::insertNotice(const cm::domain::SysNotice& n) {
    std::string cols = "create_time";
    std::string vals = "sysdate()";
    if (n.noticeTitle && !n.noticeTitle->empty()) { cols += ", notice_title"; vals += ", " + cm::db::bind(*n.noticeTitle); }
    if (n.noticeType && !n.noticeType->empty()) { cols += ", notice_type"; vals += ", " + cm::db::bind(*n.noticeType); }
    if (n.noticeContent && !n.noticeContent->empty()) { cols += ", notice_content"; vals += ", " + cm::db::bind(*n.noticeContent); }
    if (n.status && !n.status->empty()) { cols += ", status"; vals += ", " + cm::db::bind(*n.status); }
    if (n.remark && !n.remark->empty()) { cols += ", remark"; vals += ", " + cm::db::bind(*n.remark); }
    if (n.createBy && !n.createBy->empty()) { cols += ", create_by"; vals += ", " + cm::db::bind(*n.createBy); }
    if (n.bussId) { cols += ", buss_id"; vals += ", " + cm::db::bind(*n.bussId); }
    if (n.bussName) { cols += ", buss_name"; vals += ", " + cm::db::bind(*n.bussName); }
    if (n.tenantId) { cols += ", tenant_id"; vals += ", " + cm::db::bind(*n.tenantId); }
    std::string sql = "insert into sys_notice (" + cols + ") values (" + vals + ")";
    long long affected = 0, insertId = 0;
    cm::db::Db::instance().execute(sql, &affected, &insertId);
    return affected;
}

long long SysNoticeMapper::updateNotice(const cm::domain::SysNotice& n) {
    std::string sql = "update sys_notice set";
    bool first = true;
    auto append = [&](const std::string& c) { if (!first) sql += ","; sql += " " + c; first = false; };
    if (n.noticeTitle && !n.noticeTitle->empty()) append("notice_title = " + cm::db::bind(*n.noticeTitle));
    if (n.noticeType && !n.noticeType->empty()) append("notice_type = " + cm::db::bind(*n.noticeType));
    if (n.noticeContent) append("notice_content = " + cm::db::bind(*n.noticeContent));
    if (n.status && !n.status->empty()) append("status = " + cm::db::bind(*n.status));
    if (n.updateBy && !n.updateBy->empty()) append("update_by = " + cm::db::bind(*n.updateBy));
    if (n.bussId && !n.bussId->empty()) append("buss_id = " + cm::db::bind(*n.bussId));
    if (n.bussName && !n.bussName->empty()) append("buss_name = " + cm::db::bind(*n.bussName));
    append("update_time = sysdate()");
    sql += " where notice_id = " + cm::db::bind(n.noticeId.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysNoticeMapper::deleteNoticeById(long long noticeId) {
    std::string sql = "delete from sys_notice where notice_id = " + cm::db::bind(noticeId);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysNoticeMapper::deleteNoticeByIds(const std::vector<long long>& noticeIds) {
    if (noticeIds.empty()) return 0;
    std::string sql = "delete from sys_notice where notice_id in " + cm::db::bindIn(noticeIds);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
