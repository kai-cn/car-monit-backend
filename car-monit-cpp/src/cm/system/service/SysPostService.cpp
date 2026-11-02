// 对应 Java: com.ruoyi.system.service.impl.SysPostServiceImpl
#include "cm/system/service/SysPostService.hpp"
#include "cm/system/mapper/SysPostMapper.hpp"
#include "cm/system/mapper/SysUserPostMapper.hpp"
#include "cm/common/exception/Exceptions.hpp"

namespace cm::system::service {

std::vector<cm::domain::SysPost> SysPostService::selectPostList(const cm::domain::SysPost& post) {
    return cm::system::mapper::SysPostMapper::selectPostList(post);
}

std::vector<cm::domain::SysPost> SysPostService::selectPostAll() {
    return cm::system::mapper::SysPostMapper::selectPostAll();
}

std::optional<cm::domain::SysPost> SysPostService::selectPostById(long long postId) {
    return cm::system::mapper::SysPostMapper::selectPostById(postId);
}

std::vector<long long> SysPostService::selectPostListByUserId(long long userId) {
    return cm::system::mapper::SysPostMapper::selectPostListByUserId(userId);
}

std::string SysPostService::checkPostNameUnique(const cm::domain::SysPost& post) {
    long long postId = post.postId.value_or(-1);
    auto info = cm::system::mapper::SysPostMapper::checkPostNameUnique(post.postName.value_or(""));
    if (info && info->postId && info->postId.value() != postId) {
        return "1"; // NOT_UNIQUE
    }
    return "0"; // UNIQUE
}

std::string SysPostService::checkPostCodeUnique(const cm::domain::SysPost& post) {
    long long postId = post.postId.value_or(-1);
    auto info = cm::system::mapper::SysPostMapper::checkPostCodeUnique(post.postCode.value_or(""));
    if (info && info->postId && info->postId.value() != postId) {
        return "1"; // NOT_UNIQUE
    }
    return "0"; // UNIQUE
}

int SysPostService::insertPost(cm::domain::SysPost& post) {
    return cm::system::mapper::SysPostMapper::insertPost(post) ? 1 : 0;
}

int SysPostService::updatePost(cm::domain::SysPost& post) {
    return cm::system::mapper::SysPostMapper::updatePost(post) ? 1 : 0;
}

int SysPostService::deletePostById(long long postId) {
    return cm::system::mapper::SysPostMapper::deletePostById(postId) ? 1 : 0;
}

int SysPostService::deletePostByIds(const std::vector<long long>& postIds) {
    for (long long postId : postIds) {
        auto post = selectPostById(postId);
        if (cm::system::mapper::SysUserPostMapper::countUserPostById(postId) > 0) {
            throw cm::exception::CustomException(post->postName.value_or("") + "已分配,不能删除");
        }
    }
    return cm::system::mapper::SysPostMapper::deletePostByIds(postIds) ? static_cast<int>(postIds.size()) : 0;
}

} // namespace cm::system::service
