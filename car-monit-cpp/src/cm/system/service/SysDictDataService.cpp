// 对应 Java: SysDictDataServiceImpl
#include "cm/system/service/SysDictDataService.hpp"
#include "cm/system/service/SysDictTypeService.hpp"
#include "cm/system/mapper/SysDictDataMapper.hpp"

namespace cm::system::service {

std::pair<std::vector<cm::domain::SysDictData>, long long> SysDictDataService::selectDictDataListEntityPage(const cm::domain::SysDictData& dictData,
        const cm::db::PageRequest& page) {
    return cm::system::mapper::SysDictDataMapper::selectDictDataListEntityPage(dictData, page);
}

std::vector<cm::domain::SysDictData> SysDictDataService::selectDictDataList(const cm::domain::SysDictData& dictData) {
    return cm::system::mapper::SysDictDataMapper::selectDictDataList(dictData);
}

std::optional<cm::domain::SysDictData> SysDictDataService::selectDictDataById(long long dictCode) {
    return cm::system::mapper::SysDictDataMapper::selectDictDataById(dictCode);
}

long long SysDictDataService::insertDictData(cm::domain::SysDictData& dictData) {
    long long row = cm::system::mapper::SysDictDataMapper::insertDictData(dictData);
    if (row > 0) SysDictTypeService::clearCache();
    return row;
}

long long SysDictDataService::updateDictData(cm::domain::SysDictData& dictData) {
    long long row = cm::system::mapper::SysDictDataMapper::updateDictData(dictData);
    if (row > 0) SysDictTypeService::clearCache();
    return row;
}

long long SysDictDataService::deleteDictDataByIds(const std::vector<long long>& dictCodes) {
    long long row = cm::system::mapper::SysDictDataMapper::deleteDictDataByIds(dictCodes);
    if (row > 0) SysDictTypeService::clearCache();
    return row;
}

} // namespace cm::system::service
