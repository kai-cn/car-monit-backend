// 对应 Java: com.ruoyi.system.mapper.SysPostMapper
#include "cm/system/mapper/SysPostMapper.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/common/utils/DateUtils.hpp"

namespace cm::system::mapper {

namespace {
std::optional<long long> parseDbDate(const std::optional<std::string>& text) {
    if (!text || text->empty()) return std::nullopt;
    auto tp = cm::utils::DateUtils::parseDate(*text);
    if (!tp) return std::nullopt;
    return cm::utils::DateUtils::toMillis(*tp);
}
} // namespace

cm::domain::SysPost SysPostMapper::mapPost(const cm::db::Row& row) {
    cm::domain::SysPost p;
    p.postId = row.optI64("post_id");
    p.postCode = row.get("post_code");
    p.postName = row.get("post_name");
    p.postSort = row.get("post_sort");
    p.status = row.get("status");
    p.createBy = row.get("create_by");
    p.createTime = parseDbDate(row.get("create_time"));
    p.updateBy = row.get("update_by");
    p.updateTime = parseDbDate(row.get("update_time"));
    p.remark = row.get("remark");
    return p;
}

std::vector<cm::domain::SysPost> SysPostMapper::selectPostList(const cm::domain::SysPost& post) {
    std::string sql = "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark from sys_post";
    bool hasWhere = false;
    if (post.postCode && !post.postCode->empty()) {
        sql += " where post_code like " + cm::db::Db::lit("%" + *post.postCode + "%");
        hasWhere = true;
    }
    if (post.status && !post.status->empty()) {
        sql += (hasWhere ? " and " : " where ") + std::string("status = ") + cm::db::Db::lit(*post.status);
        hasWhere = true;
    }
    if (post.postName && !post.postName->empty()) {
        sql += (hasWhere ? " and " : " where ") + std::string("post_name like ") + cm::db::Db::lit("%" + *post.postName + "%");
    }
    cm::db::Result res;
    std::vector<cm::domain::SysPost> posts;
    if (!cm::db::Db::instance().query(sql, res)) return posts;
    for (const auto& row : res.rows) posts.push_back(mapPost(row));
    return posts;
}

std::vector<cm::domain::SysPost> SysPostMapper::selectPostAll() {
    std::string sql = "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark from sys_post";
    cm::db::Result res;
    std::vector<cm::domain::SysPost> posts;
    if (!cm::db::Db::instance().query(sql, res)) return posts;
    for (const auto& row : res.rows) posts.push_back(mapPost(row));
    return posts;
}

std::optional<cm::domain::SysPost> SysPostMapper::selectPostById(long long postId) {
    std::string sql = "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark from sys_post where post_id = " + cm::db::Db::lit(postId);
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapPost(res.rows[0]);
}

std::vector<long long> SysPostMapper::selectPostListByUserId(long long userId) {
    std::string sql = "select p.post_id from sys_post p left join sys_user_post up on up.post_id = p.post_id left join sys_user u on u.user_id = up.user_id where u.user_id = " + cm::db::Db::lit(userId);
    cm::db::Result res;
    std::vector<long long> ids;
    if (!cm::db::Db::instance().query(sql, res)) return ids;
    for (const auto& row : res.rows) {
        auto id = row.optI64("post_id");
        if (id) ids.push_back(*id);
    }
    return ids;
}

std::vector<cm::domain::SysPost> SysPostMapper::selectPostsByUserName(const std::string& userName) {
    std::string sql = "select p.post_id, p.post_name, p.post_code from sys_post p left join sys_user_post up on up.post_id = p.post_id left join sys_user u on u.user_id = up.user_id where u.user_name = " + cm::db::Db::lit(userName);
    cm::db::Result res;
    std::vector<cm::domain::SysPost> posts;
    if (!cm::db::Db::instance().query(sql, res)) return posts;
    for (const auto& row : res.rows) posts.push_back(mapPost(row));
    return posts;
}

std::optional<cm::domain::SysPost> SysPostMapper::checkPostNameUnique(const std::string& postName) {
    std::string sql = "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark from sys_post where post_name = " + cm::db::Db::lit(postName) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapPost(res.rows[0]);
}

std::optional<cm::domain::SysPost> SysPostMapper::checkPostCodeUnique(const std::string& postCode) {
    std::string sql = "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark from sys_post where post_code = " + cm::db::Db::lit(postCode) + " limit 1";
    cm::db::Result res;
    if (!cm::db::Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    return mapPost(res.rows[0]);
}

bool SysPostMapper::insertPost(cm::domain::SysPost& post) {
    std::string sql = "insert into sys_post(";
    std::string vals;
    if (post.postId && *post.postId != 0) { sql += "post_id,"; vals += cm::db::Db::lit(*post.postId) + ","; }
    if (post.postCode && !post.postCode->empty()) { sql += "post_code,"; vals += cm::db::Db::lit(*post.postCode) + ","; }
    if (post.postName && !post.postName->empty()) { sql += "post_name,"; vals += cm::db::Db::lit(*post.postName) + ","; }
    if (post.postSort && !post.postSort->empty()) { sql += "post_sort,"; vals += cm::db::Db::lit(*post.postSort) + ","; }
    if (post.status && !post.status->empty()) { sql += "status,"; vals += cm::db::Db::lit(*post.status) + ","; }
    if (post.remark && !post.remark->empty()) { sql += "remark,"; vals += cm::db::Db::lit(*post.remark) + ","; }
    if (post.createBy && !post.createBy->empty()) { sql += "create_by,"; vals += cm::db::Db::lit(*post.createBy) + ","; }
    sql += "create_time) values (" + vals + "sysdate())";
    long long insertId = 0;
    bool ok = cm::db::Db::instance().execute(sql, nullptr, &insertId);
    if (ok && insertId > 0) post.postId = insertId;
    return ok;
}

bool SysPostMapper::updatePost(const cm::domain::SysPost& post) {
    std::string sql = "update sys_post set ";
    if (post.postCode && !post.postCode->empty()) sql += "post_code = " + cm::db::Db::lit(*post.postCode) + ",";
    if (post.postName && !post.postName->empty()) sql += "post_name = " + cm::db::Db::lit(*post.postName) + ",";
    if (post.postSort && !post.postSort->empty()) sql += "post_sort = " + cm::db::Db::lit(*post.postSort) + ",";
    if (post.status && !post.status->empty()) sql += "status = " + cm::db::Db::lit(*post.status) + ",";
    if (post.remark) sql += "remark = " + cm::db::Db::lit(*post.remark) + ",";
    if (post.updateBy && !post.updateBy->empty()) sql += "update_by = " + cm::db::Db::lit(*post.updateBy) + ",";
    sql += "update_time = sysdate() where post_id = " + cm::db::Db::lit(post.postId.value_or(0));
    return cm::db::Db::instance().execute(sql);
}

bool SysPostMapper::deletePostById(long long postId) {
    std::string sql = "delete from sys_post where post_id = " + cm::db::Db::lit(postId);
    return cm::db::Db::instance().execute(sql);
}

bool SysPostMapper::deletePostByIds(const std::vector<long long>& postIds) {
    if (postIds.empty()) return true;
    std::string sql = "delete from sys_post where post_id in " + cm::db::Db::inList(postIds);
    return cm::db::Db::instance().execute(sql);
}

} // namespace cm::system::mapper
