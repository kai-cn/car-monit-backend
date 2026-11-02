#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysPostMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/system/domain/SysPost.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysPostMapper {
public:
    static std::vector<cm::domain::SysPost> selectPostList(const cm::domain::SysPost& post);
    static std::vector<cm::domain::SysPost> selectPostAll();
    static std::optional<cm::domain::SysPost> selectPostById(long long postId);
    static std::vector<long long> selectPostListByUserId(long long userId);
    static std::vector<cm::domain::SysPost> selectPostsByUserName(const std::string& userName);
    static std::optional<cm::domain::SysPost> checkPostNameUnique(const std::string& postName);
    static std::optional<cm::domain::SysPost> checkPostCodeUnique(const std::string& postCode);
    static bool insertPost(cm::domain::SysPost& post);
    static bool updatePost(const cm::domain::SysPost& post);
    static bool deletePostById(long long postId);
    static bool deletePostByIds(const std::vector<long long>& postIds);

    static cm::domain::SysPost mapPost(const cm::db::Row& row);
};

} // namespace cm::system::mapper
