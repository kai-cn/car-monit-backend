// 对应 Java: SysFileMapper
#include "cm/system/mapper/SysFileMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {
namespace {
constexpr const char* kSelectVo =
    "t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, t.buss_type, t.buss_name,"
    " t.create_user, t.create_time, t.update_user, t.update_time, t.del_flag, t.tenant_id";
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
}

cm::domain::SysFile SysFileMapper::mapSysFile(const cm::db::Row& row) {
    cm::domain::SysFile f;
    f.id = row.optI64("id");
    f.fileName = row.get("file_name");
    f.bucketName = row.get("bucket_name");
    f.original = row.get("original");
    f.type = row.get("type");
    f.fileSize = row.optI64("file_size");
    f.bussType = row.get("buss_type");
    f.bussName = row.get("buss_name");
    f.createUser = row.get("create_user");
    f.createTime = parseDbDate(row.get("create_time"));
    f.updateUser = row.get("update_user");
    f.updateTime = parseDbDate(row.get("update_time"));
    f.delFlag = row.get("del_flag");
    f.tenantId = row.optI64("tenant_id");
    f.createUserName = row.get("createUserName");
    return f;
}

std::string SysFileMapper::selectSysFileListSql(const cm::domain::SysFile& q) {
    std::string sql = "select " + std::string(kSelectVo) + " from sys_file t where t.del_flag = '0'";
    if (q.id) sql += " and t.id = " + cm::db::bind(*q.id);
    if (q.fileName && !q.fileName->empty()) sql += " and t.file_name like " + cm::db::bind("%" + *q.fileName + "%");
    if (q.bucketName && !q.bucketName->empty()) sql += " and t.bucket_name like " + cm::db::bind("%" + *q.bucketName + "%");
    if (q.original && !q.original->empty()) sql += " and t.original = " + cm::db::bind(*q.original);
    if (q.type && !q.type->empty()) sql += " and t.type = " + cm::db::bind(*q.type);
    if (q.fileSize) sql += " and t.file_size = " + cm::db::bind(*q.fileSize);
    if (q.bussType && !q.bussType->empty()) sql += " and t.buss_type = " + cm::db::bind(*q.bussType);
    if (q.bussName && !q.bussName->empty()) sql += " and t.buss_name like " + cm::db::bind("%" + *q.bussName + "%");
    if (q.createUser && !q.createUser->empty()) sql += " and t.create_user = " + cm::db::bind(*q.createUser);
    if (q.updateUser && !q.updateUser->empty()) sql += " and t.update_user = " + cm::db::bind(*q.updateUser);
    if (q.tenantId) sql += " and t.tenant_id = " + cm::db::bind(*q.tenantId);
    sql += " order by t.create_time desc, t.id";
    return sql;
}

std::pair<std::vector<cm::domain::SysFile>, long long> SysFileMapper::selectSysFileListEntityPage(const cm::domain::SysFile& q,
                                                   const cm::db::PageRequest& page) {
    const std::string sql = selectSysFileListSql(q);
    // PageHelper 语义：count 包住与列表完全同一条 SQL，rows 与 total 不会各算一份
    auto pr = cm::db::queryPage("select count(1) from (" + sql + ") page_count", sql, page);
    std::vector<cm::domain::SysFile> out;
    for (const auto& row : pr.rows.rows) out.push_back(mapSysFile(row));
    return {std::move(out), pr.total};
}

std::vector<cm::domain::SysFile> SysFileMapper::selectSysFileList(const cm::domain::SysFile& q) {
    const std::string sql = selectSysFileListSql(q);
    cm::db::Result res;
    std::vector<cm::domain::SysFile> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapSysFile(row));
    return list;
}

std::optional<cm::domain::SysFile> SysFileMapper::selectSysFileById(long long id) {
    std::string sql = "select " + std::string(kSelectVo) + " from sys_file t where t.id = " + cm::db::bind(id);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapSysFile(res.rows.front());
}

std::vector<cm::domain::SysFile> SysFileMapper::selectSysFileByIds(const std::string& ids) {
    std::vector<std::string> parts;
    std::string cur;
    for (char c : ids) {
        if (c == ',') { if (!cur.empty()) { parts.push_back(cur); cur.clear(); } }
        else cur += c;
    }
    if (!cur.empty()) parts.push_back(cur);
    if (parts.empty()) return {};
    std::string sql = "select " + std::string(kSelectVo) + ", t2.nick_name createUserName"
                      " from sys_file t"
                      " left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag='0'"
                      " where t.id in " + cm::db::bindIn(parts) +
                      " order by t.id";
    cm::db::Result res;
    std::vector<cm::domain::SysFile> list;
    if (!cm::db::Db::instance().query(sql, res)) return list;
    for (const auto& row : res.rows) list.push_back(mapSysFile(row));
    return list;
}

long long SysFileMapper::insertSysFile(const cm::domain::SysFile& f) {
    std::string cols, vals;
    auto add = [&](const std::string& c, const std::string& v) {
        if (!cols.empty()) { cols += ", "; vals += ", "; }
        cols += c; vals += v;
    };
    if (f.id) add("id", cm::db::bind(*f.id));
    if (f.fileName) add("file_name", cm::db::bind(*f.fileName));
    if (f.bucketName) add("bucket_name", cm::db::bind(*f.bucketName));
    if (f.original) add("original", cm::db::bind(*f.original));
    if (f.type) add("type", cm::db::bind(*f.type));
    if (f.fileSize) add("file_size", cm::db::bind(*f.fileSize));
    if (f.bussType) add("buss_type", cm::db::bind(*f.bussType));
    if (f.bussName) add("buss_name", cm::db::bind(*f.bussName));
    if (f.createUser) add("create_user", cm::db::bind(*f.createUser));
    if (f.createTime) add("create_time", "from_unixtime(" + std::to_string(*f.createTime / 1000) + ")");
    if (f.updateUser) add("update_user", cm::db::bind(*f.updateUser));
    if (f.updateTime) add("update_time", "from_unixtime(" + std::to_string(*f.updateTime / 1000) + ")");
    if (f.delFlag) add("del_flag", cm::db::bind(*f.delFlag));
    if (f.tenantId) add("tenant_id", cm::db::bind(*f.tenantId));
    std::string sql = "insert into sys_file (" + cols + ") values (" + vals + ")";
    long long affected = 0, insertId = 0;
    cm::db::Db::instance().execute(sql, &affected, &insertId);
    return affected;
}

long long SysFileMapper::updateSysFile(const cm::domain::SysFile& f) {
    std::string sql = "update sys_file set";
    bool first = true;
    auto append = [&](const std::string& c) { if (!first) sql += ","; sql += " " + c; first = false; };
    if (f.fileName) append("file_name = " + cm::db::bind(*f.fileName));
    if (f.bucketName) append("bucket_name = " + cm::db::bind(*f.bucketName));
    if (f.original) append("original = " + cm::db::bind(*f.original));
    if (f.type) append("type = " + cm::db::bind(*f.type));
    if (f.fileSize) append("file_size = " + cm::db::bind(*f.fileSize));
    if (f.bussType) append("buss_type = " + cm::db::bind(*f.bussType));
    if (f.bussName) append("buss_name = " + cm::db::bind(*f.bussName));
    if (f.createUser) append("create_user = " + cm::db::bind(*f.createUser));
    if (f.createTime) append("create_time = from_unixtime(" + std::to_string(*f.createTime / 1000) + ")");
    if (f.updateUser) append("update_user = " + cm::db::bind(*f.updateUser));
    if (f.updateTime) append("update_time = from_unixtime(" + std::to_string(*f.updateTime / 1000) + ")");
    if (f.delFlag) append("del_flag = " + cm::db::bind(*f.delFlag));
    if (f.tenantId) append("tenant_id = " + cm::db::bind(*f.tenantId));
    sql += " where id = " + cm::db::bind(f.id.value_or(0));
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysFileMapper::deleteSysFileById(long long id) {
    std::string sql = "update sys_file set del_flag = '1' where id = " + cm::db::bind(id);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysFileMapper::deleteSysFileByIds(const std::vector<long long>& ids) {
    if (ids.empty()) return 0;
    std::string sql = "update sys_file set del_flag = '1' where id in " + cm::db::bindIn(ids);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysFileMapper::deleteSysFileByIdNew(long long id) {
    std::string sql = "delete from sys_file where id = " + cm::db::bind(id);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

long long SysFileMapper::updateCAFile(long long id) {
    std::string sql = "update sys_file set id = 3001 where id = " + cm::db::bind(id);
    long long affected = 0;
    cm::db::Db::instance().execute(sql, &affected);
    return affected;
}

} // namespace cm::system::mapper
