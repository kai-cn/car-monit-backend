// 由 scripts/gen_crud_spec.py 生成（area=system）。
// 重新生成: python scripts/gen_crud_spec.py --area system
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

void registerSystemArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysConfig.java
        // ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml
        Spec s;
        s.table = "sys_config";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"configId", "config_id", Fmt::Long, Cond::Eq, "参数主键", false, false},
            {"configName", "config_name", Fmt::Str, Cond::Eq, "参数名称", false, false},
            {"configKey", "config_key", Fmt::Str, Cond::Eq, "参数键名", false, false},
            {"configValue", "config_value", Fmt::Str, Cond::Eq, "参数键值", false, false},
            {"configType", "config_type", Fmt::Str, Cond::Eq, "系统内置", false, false},
        };
        s.excelSheetName = "参数管理";
        Perms p;
        p.list = "system:config:list";
        p.exportList = "system:config:export";
        p.query = "system:config:query";
        registerCrud(r, "/system/config", s, p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictData.java
        // ruoyi-system/src/main/resources/mapper/system/SysDictDataMapper.xml
        Spec s;
        s.table = "sys_dict_data";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"dictCode", "dict_code", Fmt::Long, Cond::None, "字典编码", false, false},
            {"dictSort", "dict_sort", Fmt::Long, Cond::Eq, "字典排序", false, false},
            {"dictLabel", "dict_label", Fmt::Str, Cond::Eq, "字典标签", false, false},
            {"dictValue", "dict_value", Fmt::Str, Cond::Eq, "字典键值", false, false},
            {"dictType", "dict_type", Fmt::Str, Cond::Eq, "字典类型", false, false},
            {"cssClass", "css_class", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"listClass", "list_class", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"isDefault", "is_default", Fmt::Str, Cond::Eq, "是否默认", false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false},
        };
        s.orderBy = "dict_sort asc";
        s.excelSheetName = "字典数据";
        Perms p;
        p.list = "system:dict:list";
        p.exportList = "system:dict:export";
        p.query = "system:dict:query";
        registerCrud(r, "/system/dict/data", s, p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictType.java
        // ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml
        Spec s;
        s.table = "sys_dict_type";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"dictId", "dict_id", Fmt::Long, Cond::None, "字典主键", false, false},
            {"dictName", "dict_name", Fmt::Str, Cond::Eq, "字典名称", false, false},
            {"dictType", "dict_type", Fmt::Str, Cond::Eq, "字典类型", false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false},
        };
        s.orderBy = "create_time desc";
        s.excelSheetName = "字典类型";
        Perms p;
        p.list = "system:dict:list";
        p.exportList = "system:dict:export";
        p.query = "system:dict:query";
        registerCrud(r, "/system/dict/type", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysFile.java
        // ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml
        Spec s;
        s.table = "sys_file";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"fileName", "file_name", Fmt::Str, Cond::Eq, "文件名称", false, false},
            {"bucketName", "bucket_name", Fmt::Str, Cond::Eq, "上传包名", false, false},
            {"original", "original", Fmt::Str, Cond::Eq, "上传文件名称", false, false},
            {"type", "type", Fmt::Str, Cond::Eq, "文件类型", false, false},
            {"fileSize", "file_size", Fmt::Long, Cond::Eq, "文件大小", false, false},
            {"bussType", "buss_type", Fmt::Str, Cond::Eq, "业务类型", false, false},
            {"bussName", "buss_name", Fmt::Str, Cond::Eq, "业务名称", false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::Eq, nullptr, false, false},
            {"createUser", "create_user", Fmt::Str, Cond::Eq, "文件大小", false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::Eq, nullptr, false, false},
            {"updateUser", "update_user", Fmt::Str, Cond::Eq, "文件大小", false, false},
            {"delFlag", "del_flag", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, "所属租户", false, false},
            {"files", nullptr, Fmt::Str, Cond::None, "文件s", false, false, false, false},
            {"createUserName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "文件";
        Perms p;
        p.list = "base:sysflie:list";
        registerCrud(r, "/system/file", s, p, "ids");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysNotice.java
        // ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml
        Spec s;
        s.table = "sys_notice";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", "remark", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"noticeId", "notice_id", Fmt::Long, Cond::None, nullptr, false, false},
            {"noticeTitle", "notice_title", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"noticeType", "notice_type", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"noticeContent", "notice_content", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"status", "status", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"bussId", "buss_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"bussName", "buss_name", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.create_time desc";
        s.excelSheetName = "通知公告";
        Perms p;
        p.list = "system:notice:list";
        registerCrud(r, "/system/notice", s, p, "id");
        registerListVariant(r, "/system/notice/listquery", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java
        // ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
        Spec s;
        s.table = "sys_post";
        s.alias = "p";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", "remark", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"postId", "post_id", Fmt::Long, Cond::None, "岗位序号", false, false},
            {"postCode", "post_code", Fmt::Str, Cond::Eq, "岗位编码", false, false},
            {"postName", "post_name", Fmt::Str, Cond::Eq, "岗位名称", false, false},
            {"postSort", "post_sort", Fmt::Str, Cond::Eq, "岗位排序", false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false},
        };
        s.excelSheetName = "岗位管理";
        Perms p;
        p.list = "system:post:list";
        p.exportList = "system:post:export";
        p.query = "system:post:query";
        registerCrud(r, "/system/post", s, p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java
        // ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml
        Spec s;
        s.table = "sys_role";
        s.alias = "r";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"updateBy", "update_by", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
            {"remark", "remark", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"roleId", "role_id", Fmt::Long, Cond::None, "角色序号", false, false},
            {"roleName", "role_name", Fmt::Str, Cond::Eq, "角色名称", false, false},
            {"roleKey", "role_key", Fmt::Str, Cond::Eq, "角色权限", false, false},
            {"roleSort", "role_sort", Fmt::Str, Cond::Eq, "角色排序", false, false},
            {"dataScope", "data_scope", Fmt::Str, Cond::Eq, "数据范围", false, false},
            {"menuCheckStrictly", "menu_check_strictly", Fmt::Bool, Cond::Eq, nullptr, false, false},
            {"deptCheckStrictly", "dept_check_strictly", Fmt::Bool, Cond::Eq, nullptr, false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "角色状态", false, false},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false},
        };
        s.orderBy = "r.role_sort";
        s.excelSheetName = "角色管理";
        Perms p;
        p.list = "system:role:list";
        p.exportList = "system:role:export";
        p.query = "system:role:query";
        registerCrud(r, "/system/role", s, p, "id");
    }
}

} // namespace cm::web::crud
