#pragma once
#include <optional>
#include <string>
#include <vector>
#include "cm/common/core/domain/entity/SysDictData.hpp"

namespace cm::system::service {

class SysDictDataService {
public:
    static std::vector<cm::domain::SysDictData> selectDictDataList(const cm::domain::SysDictData& dictData);
    static std::optional<cm::domain::SysDictData> selectDictDataById(long long dictCode);
    static long long insertDictData(cm::domain::SysDictData& dictData);
    static long long updateDictData(cm::domain::SysDictData& dictData);
    static long long deleteDictDataByIds(const std::vector<long long>& dictCodes);
};

} // namespace cm::system::service
