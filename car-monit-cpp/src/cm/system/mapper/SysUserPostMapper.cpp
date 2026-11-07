// 对应 Java: com.ruoyi.system.mapper.SysUserPostMapper
#include "cm/system/mapper/SysUserPostMapper.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::system::mapper {

bool SysUserPostMapper::deleteUserPostByUserId(long long userId) {
    std::string sql = "delete from sys_user_post where user_id = " + cm::db::bind(userId);
    return cm::db::Db::instance().execute(sql);
}

bool SysUserPostMapper::deleteUserPost(const std::vector<long long>& userIds) {
    if (userIds.empty()) return true;
    std::string sql = "delete from sys_user_post where user_id in " + cm::db::bindIn(userIds);
    return cm::db::Db::instance().execute(sql);
}

bool SysUserPostMapper::batchUserPost(const std::vector<std::pair<long long, long long>>& userPosts) {
    if (userPosts.empty()) return true;
    std::string sql = "insert into sys_user_post(user_id, post_id) values ";
    for (size_t i = 0; i < userPosts.size(); ++i) {
        if (i > 0) sql += ",";
        sql += "(" + cm::db::bind(userPosts[i].first) + "," + cm::db::bind(userPosts[i].second) + ")";
    }
    return cm::db::Db::instance().execute(sql);
}

int SysUserPostMapper::countUserPostById(long long postId) {
    std::string sql = "select count(1) from sys_user_post where post_id = " + cm::db::bind(postId);
    return static_cast<int>(cm::db::Db::instance().count(sql));
}

} // namespace cm::system::mapper
