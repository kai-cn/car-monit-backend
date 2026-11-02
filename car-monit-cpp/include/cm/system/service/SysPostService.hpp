#pragma once
// 对应 Java: com.ruoyi.system.service.ISysPostService
#include <optional>
#include <string>
#include <vector>

#include "cm/system/domain/SysPost.hpp"

namespace cm::system::service {

class SysPostService {
public:
    static std::vector<cm::domain::SysPost> selectPostList(const cm::domain::SysPost& post);
    static std::vector<cm::domain::SysPost> selectPostAll();
    static std::optional<cm::domain::SysPost> selectPostById(long long postId);
    static std::vector<long long> selectPostListByUserId(long long userId);
    static std::string checkPostNameUnique(const cm::domain::SysPost& post);
    static std::string checkPostCodeUnique(const cm::domain::SysPost& post);
    static int insertPost(cm::domain::SysPost& post);
    static int updatePost(cm::domain::SysPost& post);
    static int deletePostById(long long postId);
    static int deletePostByIds(const std::vector<long long>& postIds);
};

} // namespace cm::system::service
