// 对应 Java: SysDictTypeServiceImpl
#include "cm/system/service/SysDictTypeService.hpp"
#include "cm/common/constant/Constants.hpp"
#include "cm/common/constant/UserConstants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/redis/RedisClient.hpp"
#include "cm/system/mapper/SysDictTypeMapper.hpp"
#include "cm/system/mapper/SysDictDataMapper.hpp"

namespace cm::system::service {

using cm::constant::Constants;
using cm::constant::UserConstants;

namespace {
std::string getCacheKey(const std::string& dictType) {
    return std::string(Constants::SYS_DICT_KEY) + dictType;
}

void clearDictCache() {
    auto keys = cm::redis::RedisCache::instance().keys(std::string(Constants::SYS_DICT_KEY) + "*");
    if (!keys.empty()) cm::redis::RedisCache::instance().client().del(keys);
}

void setDictCache(const std::string& dictType, const std::vector<cm::domain::SysDictData>& datas) {
    Json arr = Json::array();
    for (const auto& d : datas) arr.push_back(d.toJson());
    cm::redis::RedisCache::instance().set(getCacheKey(dictType), arr.dump());
}

std::optional<std::vector<cm::domain::SysDictData>> getDictCache(const std::string& dictType) {
    auto cached = cm::redis::RedisCache::instance().get(getCacheKey(dictType));
    if (!cached || cached->empty()) return std::nullopt;
    try {
        Json arr = cm::utils::parse_cached_json(*cached);
        if (!arr.is_array()) return std::nullopt;
        std::vector<cm::domain::SysDictData> datas;
        for (const auto& e : arr) {
            cm::domain::SysDictData d;
            d.fromJson(e);
            datas.push_back(d);
        }
        return datas;
    } catch (...) {
        return std::nullopt;
    }
}
} // namespace

std::pair<std::vector<cm::domain::SysDictType>, long long> SysDictTypeService::selectDictTypeListEntityPage(const cm::domain::SysDictType& dictType,
        const cm::db::PageRequest& page) {
    return cm::system::mapper::SysDictTypeMapper::selectDictTypeListEntityPage(dictType, page);
}

std::vector<cm::domain::SysDictType> SysDictTypeService::selectDictTypeList(const cm::domain::SysDictType& dictType) {
    return cm::system::mapper::SysDictTypeMapper::selectDictTypeList(dictType);
}

std::vector<cm::domain::SysDictType> SysDictTypeService::selectDictTypeAll() {
    return cm::system::mapper::SysDictTypeMapper::selectDictTypeAll();
}

std::optional<cm::domain::SysDictType> SysDictTypeService::selectDictTypeById(long long dictId) {
    return cm::system::mapper::SysDictTypeMapper::selectDictTypeById(dictId);
}

std::string SysDictTypeService::checkDictTypeUnique(const cm::domain::SysDictType& dict) {
    long long dictId = dict.dictId.value_or(-1);
    auto info = cm::system::mapper::SysDictTypeMapper::checkDictTypeUnique(dict.dictType.value_or(""));
    if (info && info->dictId.value_or(-1) != dictId) {
        return UserConstants::NOT_UNIQUE_OLD;
    }
    return UserConstants::UNIQUE_OLD;
}

long long SysDictTypeService::insertDictType(cm::domain::SysDictType& dict) {
    long long row = cm::system::mapper::SysDictTypeMapper::insertDictType(dict);
    if (row > 0) clearDictCache();
    return row;
}

long long SysDictTypeService::updateDictType(cm::domain::SysDictType& dict) {
    auto oldDict = cm::system::mapper::SysDictTypeMapper::selectDictTypeById(dict.dictId.value_or(0));
    if (oldDict && oldDict->dictType && dict.dictType && *oldDict->dictType != *dict.dictType) {
        cm::system::mapper::SysDictDataMapper::updateDictDataType(*oldDict->dictType, *dict.dictType);
    }
    long long row = cm::system::mapper::SysDictTypeMapper::updateDictType(dict);
    if (row > 0) clearDictCache();
    return row;
}

long long SysDictTypeService::deleteDictTypeByIds(const std::vector<long long>& dictIds) {
    for (long long dictId : dictIds) {
        auto dictType = selectDictTypeById(dictId);
        if (dictType && dictType->dictType) {
            long long count = cm::system::mapper::SysDictDataMapper::countDictDataByType(*dictType->dictType);
            if (count > 0) {
                throw cm::exception::CustomException(
                    std::string(dictType->dictName.value_or("")) + "已分配,不能删除");
            }
        }
    }
    long long count = cm::system::mapper::SysDictTypeMapper::deleteDictTypeByIds(dictIds);
    if (count > 0) clearDictCache();
    return count;
}

void SysDictTypeService::clearCache() {
    clearDictCache();
}

std::vector<cm::domain::SysDictData> SysDictTypeService::selectDictDataByType(const std::string& dictType) {
    auto cached = getDictCache(dictType);
    if (cached) return *cached;
    auto datas = cm::system::mapper::SysDictDataMapper::selectDictDataByType(dictType);
    if (!datas.empty()) {
        setDictCache(dictType, datas);
    }
    return datas;
}

std::vector<cm::domain::SysDictData> SysDictTypeService::selectDictDataByTypeMore(const std::string& dictType) {
    auto cached = getDictCache(dictType);
    if (cached) return *cached;
    auto datas = cm::system::mapper::SysDictDataMapper::selectDictDataByTypeMore(dictType);
    if (!datas.empty()) {
        setDictCache(dictType, datas);
    }
    return datas;
}

} // namespace cm::system::service
