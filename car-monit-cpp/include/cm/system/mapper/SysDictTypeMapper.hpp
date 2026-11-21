#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysDictTypeMapper
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysDictType.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysDictTypeMapper {
public:
        static std::string selectDictTypeListSql(const cm::domain::SysDictType& dictType);
static std::pair<std::vector<cm::domain::SysDictType>, long long> selectDictTypeListEntityPage(
            const cm::domain::SysDictType& dictType, const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysDictType> selectDictTypeList(const cm::domain::SysDictType& dictType);
    static std::vector<cm::domain::SysDictType> selectDictTypeAll();
    static std::optional<cm::domain::SysDictType> selectDictTypeById(long long dictId);
    static std::optional<cm::domain::SysDictType> selectDictTypeByType(const std::string& dictType);
    static std::optional<cm::domain::SysDictType> checkDictTypeUnique(const std::string& dictType);
    static long long insertDictType(const cm::domain::SysDictType& dictType);
    static long long updateDictType(const cm::domain::SysDictType& dictType);
    static long long deleteDictTypeById(long long dictId);
    static long long deleteDictTypeByIds(const std::vector<long long>& dictIds);

    static cm::domain::SysDictType mapDictType(const cm::db::Row& row);
};

} // namespace cm::system::mapper
