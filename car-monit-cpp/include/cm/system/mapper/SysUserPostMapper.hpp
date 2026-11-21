#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysUserPostMapper
#include <string>
#include <vector>

namespace cm::system::mapper {

class SysUserPostMapper {
public:
    static bool deleteUserPostByUserId(long long userId);
    static bool deleteUserPost(const std::vector<long long>& userIds);
    static bool batchUserPost(const std::vector<std::pair<long long, long long>>& userPosts);
    static int countUserPostById(long long postId);
};

} // namespace cm::system::mapper
