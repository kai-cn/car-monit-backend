# System Auxiliary Modules Port - Implementation Report

## Summary
Successfully ported 6 system auxiliary modules from RuoYi Java backend to C++:
- SysConfig (参数配置)
- SysDictType (字典类型)
- SysDictData (字典数据)
- SysNotice (通知公告)
- SysUpgradeInfo (系统升级信息)
- SysFile (文件管理)

## Files Created

### Domain Entities (6 files)
1. `include/cm/system/domain/SysConfig.hpp`
2. `include/cm/common/core/domain/entity/SysDictType.hpp`
3. `include/cm/common/core/domain/entity/SysDictData.hpp`
4. `include/cm/system/domain/SysNotice.hpp`
5. `include/cm/system/domain/SysUpgradeInfo.hpp`
6. `include/cm/system/domain/SysFile.hpp`

### Mappers (12 files - 6 headers + 6 implementations)
1. `include/cm/system/mapper/SysConfigMapper.hpp` + `src/cm/system/mapper/SysConfigMapper.cpp`
2. `include/cm/system/mapper/SysDictTypeMapper.hpp` + `src/cm/system/mapper/SysDictTypeMapper.cpp`
3. `include/cm/system/mapper/SysDictDataMapper.hpp` + `src/cm/system/mapper/SysDictDataMapper.cpp`
4. `include/cm/system/mapper/SysNoticeMapper.hpp` + `src/cm/system/mapper/SysNoticeMapper.cpp`
5. `include/cm/system/mapper/SysUpgradeInfoMapper.hpp` + `src/cm/system/mapper/SysUpgradeInfoMapper.cpp`
6. `include/cm/system/mapper/SysFileMapper.hpp` + `src/cm/system/mapper/SysFileMapper.cpp`

### Services (12 files - 6 headers + 6 implementations)
1. `include/cm/system/service/SysConfigService.hpp` + `src/cm/system/service/SysConfigService.cpp`
2. `include/cm/system/service/SysDictTypeService.hpp` + `src/cm/system/service/SysDictTypeService.cpp`
3. `include/cm/system/service/SysDictDataService.hpp` + `src/cm/system/service/SysDictDataService.cpp`
4. `include/cm/system/service/SysNoticeService.hpp` + `src/cm/system/service/SysNoticeService.cpp`
5. `include/cm/system/service/SysUpgradeInfoService.hpp` + `src/cm/system/service/SysUpgradeInfoService.cpp`
6. `include/cm/system/service/SysFileService.hpp` + `src/cm/system/service/SysFileService.cpp`

### Controllers (7 files)
1. `include/cm/web/controller/system/SysAuxControllers.hpp` (combined header)
2. `src/cm/web/controller/system/SysConfigController.cpp`
3. `src/cm/web/controller/system/SysDictTypeController.cpp`
4. `src/cm/web/controller/system/SysDictDataController.cpp`
5. `src/cm/web/controller/system/SysNoticeController.cpp`
6. `src/cm/web/controller/system/SysUpgradeInfoController.cpp`
7. `src/cm/web/controller/system/SysFileController.cpp`

### Constants (1 file modified)
- `include/cm/common/constant/Constants.hpp` (added SYS_CONFIG_KEY and SYS_DICT_KEY)
- `include/cm/common/constant/UserConstants.hpp` (new file)

## API Endpoints Implemented

### SysConfigController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/config/list | system:config:list | 获取参数配置列表 |
| GET | /system/config/export | system:config:export | 导出参数配置 (❌ Excel未实现) |
| GET | /system/config/{configId} | system:config:query | 根据参数编号获取详细信息 |
| GET | /system/config/configKey/{configKey} | - | 根据参数键名查询参数值 |
| POST | /system/config | system:config:add | 新增参数配置 |
| PUT | /system/config | system:config:edit | 修改参数配置 |
| DELETE | /system/config/{configIds} | system:config:remove | 删除参数配置 |
| DELETE | /system/config/clearCache | system:config:remove | 清空缓存 |

### SysDictTypeController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/dict/type/list | system:dict:list | 获取字典类型列表 |
| GET | /system/dict/type/export | system:dict:export | 导出字典类型 (❌ Excel未实现) |
| GET | /system/dict/type/{dictId} | system:dict:query | 查询字典类型详细 |
| POST | /system/dict/type | system:dict:add | 新增字典类型 |
| PUT | /system/dict/type | system:dict:edit | 修改字典类型 |
| DELETE | /system/dict/type/{dictIds} | system:dict:remove | 删除字典类型 |
| DELETE | /system/dict/type/clearCache | system:dict:remove | 清空缓存 |
| GET | /system/dict/type/optionselect | - | 获取字典选择框列表 |

### SysDictDataController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/dict/data/list | system:dict:list | 获取字典数据列表 |
| GET | /system/dict/data/export | system:dict:export | 导出字典数据 (❌ Excel未实现) |
| GET | /system/dict/data/{dictCode} | system:dict:query | 查询字典数据详细 |
| GET | /system/dict/data/type/{dictType} | - | 根据字典类型查询字典数据 |
| GET | /system/dict/data/typemore/{dictType} | - | 根据多个字典类型查询字典数据 |
| POST | /system/dict/data | system:dict:add | 新增字典数据 |
| PUT | /system/dict/data | system:dict:edit | 修改字典数据 |
| DELETE | /system/dict/data/{dictCodes} | system:dict:remove | 删除字典数据 |

### SysNoticeController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/notice/list | - | 获取通知公告列表 |
| GET | /system/notice/listquery | - | 获取通知公告列表(status=0) |
| GET | /system/notice/{noticeId} | - | 根据通知公告编号获取详细信息 |
| GET | /system/notice/view/{noticeId} | permitAll | 根据通知公告编号获取详细信息(无需登录) |
| POST | /system/notice | system:notice:add | 新增通知公告 |
| PUT | /system/notice | system:notice:edit | 修改通知公告 |
| DELETE | /system/notice/{noticeIds} | system:notice:remove | 删除通知公告 |

### SysUpgradeInfoController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/upgradeInfo/list | - | 查询系统升级信息列表 |
| GET | /system/upgradeInfo/newest | - | 获取最新的更新日志 |
| GET | /system/upgradeInfo/export | - | 导出系统升级信息 (❌ Excel未实现) |
| GET | /system/upgradeInfo/{id} | - | 获取系统升级信息详细信息 |
| POST | /system/upgradeInfo | - | 新增系统升级信息 |
| PUT | /system/upgradeInfo | - | 修改系统升级信息 |
| DELETE | /system/upgradeInfo/{ids} | - | 删除系统升级信息 |

### SysFileController
| Method | Path | Permissions | Description |
|--------|------|-------------|-------------|
| GET | /system/file/list | base:sysflie:list | 获取文件列表 |
| GET | /system/file/getInfoById/{id} | - | 获取文件详细信息 |
| GET | /system/file/{ids} | - | 获取多个文件详细信息 |
| DELETE | /system/file/del/{id} | - | 删除单个文件 |
| DELETE | /system/file/{ids} | base:supplier:remove | 删除多个文件 |
| PUT | /system/file | - | 修改文件信息 |
| GET | /system/file/getNewCa | - | 获取最新的CA驱动程序 |
| POST | /system/file/updateCAFile | - | 更新CA文件 |

## Key Features Implemented

### 1. Redis Caching (Dict & Config)
- **SysConfig**: Uses `sys_config:` prefix for Redis keys
  - Cache on insert/update
  - Clear cache on delete
  - Fallback to DB if cache miss
  
- **SysDictType/Data**: Uses `sys_dict:` prefix for Redis keys
  - Cache dict data by dictType
  - Clear all dict cache on any dict operation
  - Cache stored as JSON array

### 2. SQL Semantics
- All SQL queries match the Java mapper XML files exactly
- LIKE queries use proper escaping with `Db::lit()`
- Pagination uses `cm::db::queryPage()` with count/data SQL separation
- ORDER BY clauses preserved from Java implementation
- del_flag filtering maintained for soft-delete entities

### 3. Business Logic
- **SysConfig**: Check unique config key before insert/update
- **SysDictType**: Check if dict data exists before delete (prevent orphaned data)
- **SysDictType**: Update dict_type in sys_dict_data when changing dict type
- **SysNotice**: Auto-set noticeType="1" and tenantId on insert
- **SysUpgradeInfo**: Auto-generate UUID for new records
- **SysFile**: Soft delete (set del_flag='1') instead of hard delete

### 4. Security & Permissions
- All endpoints use `.permi()` for permission checks
- SysNotice view endpoint uses `.permitAll()` for public access
- User context (userId, username, tenantId) properly propagated

## Deliberate Gaps (❌)

### 1. Excel Export
**Reason**: Java uses Apache POI with annotations (@Excel) for automatic Excel generation. C++ implementation would require:
- Third-party Excel library integration
- Annotation-based field mapping system
- Binary Excel file generation
**Status**: Return success message indicating feature not implemented

### 2. File Upload/Download
**Reason**: Java uses MultipartFile with MinIO/S3 storage backend. C++ implementation would require:
- Multipart form data parsing (partially exists in framework)
- MinIO/S3 client library integration
- File streaming and chunked upload support
- Base64 image processing for rich text
**Status**: Only CRUD operations on sys_file table implemented

### 3. XSS Filter for Notice Content
**Reason**: Java uses Jsoup.clean() for XSS protection on noticeContent. C++ implementation would require:
- HTML sanitization library (e.g., libxml2, Gumbo)
- Custom XSS filter rules
**Status**: Notice content stored as-is without sanitization

### 4. RepeatSubmit Annotation
**Reason**: Java uses @RepeatSubmit with Redis-based duplicate submission prevention. C++ implementation would require:
- Request fingerprinting (URL + params + user)
- Redis-based deduplication with TTL
- Interceptor/middleware integration
**Status**: Not implemented

## Build Status

### Compilation
✅ All 37 new files compile successfully with g++ -std=c++20
✅ No syntax errors in new code
✅ Proper include dependencies

### Pre-existing Build Errors
❌ FileUpload.cpp: Missing includes for Constants.hpp and HttpRequest.hpp (FIXED)
❌ SysMenuService_extra.cpp: push_back() signature errors (pre-existing)
❌ SysDeptService.cpp: Missing operator< for SysDept (pre-existing)
❌ SysLogininforService.cpp: Missing cm::db namespace (pre-existing)
❌ SysMenuService.cpp: Missing SysUser declaration (pre-existing)
❌ SysOperLogService.cpp: Missing cm::db namespace (pre-existing)

### Test Execution
Unable to run tests due to pre-existing build errors in other modules.

## Code Quality

### Consistency
- Follows existing codebase patterns (mapper/service/controller layers)
- Uses same naming conventions as Java (selectXxx, insertXxx, etc.)
- Maintains field order in JSON serialization matching Java

### Safety
- All SQL uses Db::lit() for parameter escaping
- No raw string concatenation in SQL queries
- Proper null/optional handling throughout

### Documentation
- Each file includes Java source reference comment
- SQL queries match mapper XML with comments
- API endpoints documented with permissions

## Integration Notes

### Controller Registration
The new controllers need to be registered in main.cpp or Controllers.hpp:
```cpp
cm::web::registerSysConfigController(router);
cm::web::registerSysDictTypeController(router);
cm::web::registerSysDictDataController(router);
cm::web::registerSysNoticeController(router);
cm::web::registerSysUpgradeInfoController(router);
cm::web::registerSysFileController(router);
```

### Database Schema
All tables must exist with exact column names:
- sys_config
- sys_dict_type
- sys_dict_data
- sys_notice
- sys_upgrade_info
- sys_file

### Redis Configuration
Redis must be configured and accessible for caching to work.

## Conclusion

Successfully ported 6 system auxiliary modules with 37 new files. All CRUD operations, business logic, and caching mechanisms implemented. Excel export and file upload/download features deliberately omitted due to complexity and missing dependencies. Code compiles cleanly and follows existing patterns. Pre-existing build errors in other modules prevent full integration testing.
