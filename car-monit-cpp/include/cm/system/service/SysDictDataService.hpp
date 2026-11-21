#pragma once
#include <optional>
#include <utility>
#include "cm/framework/db/Db.hpp"
#include <string>
#include <vector>
#include "cm/common/core/domain/entity/SysDictData.hpp"

namespace cm::system::service {

class SysDictDataService {
public:
    /** 对应 startPage() + selectDictDataList + getDataTable：rows 与 total 共用同一条 SQL */
    static std::pair<std::vector<cm::domain::SysDictData>, long long> selectDictDataListEntityPage(const cm::domain::SysDictData& dictData,
            const cm::db::PageRequest& page);
    static std::vector<cm::domain::SysDictData> selectDictDataList(const cm::domain::SysDictData& dictData);
    static std::optional<cm::domain::SysDictData> selectDictDataById(long long dictCode);
    static long long insertDictData(cm::domain::SysDictData& dictData);
    static long long updateDictData(cm::domain::SysDictData& dictData);
    static long long deleteDictDataByIds(const std::vector<long long>& dictCodes);
};

} // namespace cm::system::service
