#pragma once
// 对应 Java: com.ruoyi.system.mapper.SysDictDataMapper
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/domain/entity/SysDictData.hpp"
#include "cm/framework/db/Row.hpp"

namespace cm::system::mapper {

class SysDictDataMapper {
public:
    static std::vector<cm::domain::SysDictData> selectDictDataList(const cm::domain::SysDictData& dictData);
    static std::vector<cm::domain::SysDictData> selectDictDataByType(const std::string& dictType);
    static std::vector<cm::domain::SysDictData> selectDictDataByTypeMore(const std::string& dictTypes);
    static std::optional<cm::domain::SysDictData> selectDictDataById(long long dictCode);
    static std::string selectDictLabel(const std::string& dictType, const std::string& dictValue);
    static long long countDictDataByType(const std::string& dictType);
    static long long insertDictData(const cm::domain::SysDictData& dictData);
    static long long updateDictData(const cm::domain::SysDictData& dictData);
    static long long updateDictDataType(const std::string& oldDictType, const std::string& newDictType);
    static long long deleteDictDataById(long long dictCode);
    static long long deleteDictDataByIds(const std::vector<long long>& dictCodes);

    static cm::domain::SysDictData mapDictData(const cm::db::Row& row);
};

} // namespace cm::system::mapper
