#pragma once
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>
#include "cm/common/core/domain/entity/SysDictType.hpp"
#include "cm/common/core/domain/entity/SysDictData.hpp"

namespace cm::system::service {

class SysDictTypeService {
public:
    /** 对应 startPage() + selectDictTypeList + getDataTable：rows 与 total 共用同一条 SQL */
    static std::pair<std::vector<cm::domain::SysDictType>, long long> selectDictTypeListEntityPage(const cm::domain::SysDictType& dictType,
            const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysDictType> selectDictTypeList(const cm::domain::SysDictType& dictType);
    static std::vector<cm::domain::SysDictType> selectDictTypeAll();
    static std::optional<cm::domain::SysDictType> selectDictTypeById(long long dictId);
    static std::string checkDictTypeUnique(const cm::domain::SysDictType& dict);
    static long long insertDictType(cm::domain::SysDictType& dict);
    static long long updateDictType(cm::domain::SysDictType& dict);
    static long long deleteDictTypeByIds(const std::vector<long long>& dictIds);
    static void clearCache();
    static std::vector<cm::domain::SysDictData> selectDictDataByType(const std::string& dictType);
    static std::vector<cm::domain::SysDictData> selectDictDataByTypeMore(const std::string& dictType);
};

} // namespace cm::system::service
