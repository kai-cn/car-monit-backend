// 由 scripts/gen_crud_spec.py 生成（area=system）。
// 重新生成: python scripts/gen_crud_spec.py --area system
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
//
// 每个实体的 Spec 通过 spec<Entity>() 暴露（声明见 SystemCrudSpecs.hpp），
// 手写控制器可以复用同一份列定义，避免把几十个字段再抄一遍。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/SystemCrudSpecs.hpp"

namespace cm::web::crud {

const Spec& specSysConfig() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_config";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::DateRange, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", nullptr, Fmt::Str, Cond::Eq, nullptr, false, false, false, false, nullptr},
            {"configId", "config_id", Fmt::Long, Cond::Eq, "参数主键", false, false, false, false},
            {"configName", "config_name", Fmt::Str, Cond::Eq, "参数名称", false, false, true, true},
            {"configKey", "config_key", Fmt::Str, Cond::Eq, "参数键名", false, false, true, true},
            {"configValue", "config_value", Fmt::Str, Cond::Eq, "参数键值", false, false, true, true},
            {"configType", "config_type", Fmt::Str, Cond::Eq, "系统内置", false, false, true, true},
        };
        s.excelSheetName = "参数管理";
        return s;
    }();
    return s;
}

const Spec& specSysDictData() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_dict_data";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", nullptr, Fmt::Str, Cond::Eq, nullptr, false, false, false, false, nullptr},
            {"dictCode", "dict_code", Fmt::Long, Cond::None, "字典编码", false, false, false, false},
            {"dictSort", "dict_sort", Fmt::Long, Cond::Eq, "字典排序", false, false, true, true},
            {"dictLabel", "dict_label", Fmt::Str, Cond::Eq, "字典标签", false, false, true, true},
            {"dictValue", "dict_value", Fmt::Str, Cond::Eq, "字典键值", false, false, true, true},
            {"dictType", "dict_type", Fmt::Str, Cond::Eq, "字典类型", false, false, true, true},
            {"cssClass", "css_class", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"listClass", "list_class", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"isDefault", "is_default", Fmt::Str, Cond::Eq, "是否默认", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
        };
        s.orderBy = "dict_sort asc";
        s.excelSheetName = "字典数据";
        return s;
    }();
    return s;
}

const Spec& specSysDictType() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_dict_type";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::DateRange, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", nullptr, Fmt::Str, Cond::Eq, nullptr, false, false, false, false, nullptr},
            {"dictId", "dict_id", Fmt::Long, Cond::None, "字典主键", false, false, false, false},
            {"dictName", "dict_name", Fmt::Str, Cond::Eq, "字典名称", false, false, true, true},
            {"dictType", "dict_type", Fmt::Str, Cond::Eq, "字典类型", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
        };
        s.orderBy = "create_time desc";
        s.excelSheetName = "字典类型";
        return s;
    }();
    return s;
}

const Spec& specSysFile() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_file";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, false, false, true, false},
            {"fileName", "file_name", Fmt::Str, Cond::Eq, "文件名称", false, false, true, true},
            {"bucketName", "bucket_name", Fmt::Str, Cond::Eq, "上传包名", false, false, true, true},
            {"original", "original", Fmt::Str, Cond::Eq, "上传文件名称", false, false, true, true},
            {"type", "type", Fmt::Str, Cond::Eq, "文件类型", false, false, true, true},
            {"fileSize", "file_size", Fmt::Long, Cond::Eq, "文件大小", false, false, true, true},
            {"bussType", "buss_type", Fmt::Str, Cond::Eq, "业务类型", false, false, true, true},
            {"bussName", "buss_name", Fmt::Str, Cond::Eq, "业务名称", false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::Eq, nullptr, false, false, true, true},
            {"createUser", "create_user", Fmt::Str, Cond::Eq, "文件大小", false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::Eq, nullptr, false, false, true, true},
            {"updateUser", "update_user", Fmt::Str, Cond::Eq, "文件大小", false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, "所属租户", false, false, true, true},
            {"files", nullptr, Fmt::Str, Cond::None, "文件s", false, false, false, false, nullptr, nullptr},
            {"createUserName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "文件";
        return s;
    }();
    return s;
}

const Spec& specSysNotice() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_notice";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::Eq, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", "remark", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"noticeId", "notice_id", Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"noticeTitle", "notice_title", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"noticeType", "notice_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"noticeContent", "notice_content", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"bussId", "buss_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"bussName", "buss_name", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, false},
        };
        s.orderBy = "t.create_time desc";
        s.excelSheetName = "通知公告";
        return s;
    }();
    return s;
}

const Spec& specSysPost() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_post";
        s.alias = "p";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", "remark", Fmt::Str, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"postId", "post_id", Fmt::Long, Cond::None, "岗位序号", false, false, true, false},
            {"postCode", "post_code", Fmt::Str, Cond::Eq, "岗位编码", false, false, true, true},
            {"postName", "post_name", Fmt::Str, Cond::Eq, "岗位名称", false, false, true, true},
            {"postSort", "post_sort", Fmt::Str, Cond::Eq, "岗位排序", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"flag", nullptr, Fmt::Bool, Cond::None, nullptr, false, false, false, false, nullptr, "false"},
        };
        s.excelSheetName = "岗位管理";
        return s;
    }();
    return s;
}

const Spec& specSysRole() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_role";
        s.alias = "r";
        s.extraWhere = " and r.del_flag = '0'";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::DateRange, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", "remark", Fmt::Str, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"roleId", "role_id", Fmt::Long, Cond::None, "角色序号", false, false, true, false},
            {"roleName", "role_name", Fmt::Str, Cond::Eq, "角色名称", false, false, true, true},
            {"roleKey", "role_key", Fmt::Str, Cond::Eq, "角色权限", false, false, true, true},
            {"roleSort", "role_sort", Fmt::Str, Cond::Eq, "角色排序", false, false, true, true},
            {"dataScope", "data_scope", Fmt::Str, Cond::Eq, "数据范围", false, false, true, true},
            {"menuCheckStrictly", "menu_check_strictly", Fmt::Bool, Cond::Eq, nullptr, false, false, true, true},
            {"deptCheckStrictly", "dept_check_strictly", Fmt::Bool, Cond::Eq, nullptr, false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "角色状态", false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Bool, Cond::None, nullptr, false, false, false, false, nullptr, "false"},
            {"menuIds", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"deptIds", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "r.role_sort";
        s.excelSheetName = "角色管理";
        return s;
    }();
    return s;
}

void registerSystemArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysConfig.java
        // ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml
        Perms p;
        p.list = "system:config:list";
        p.exportList = "system:config:export";
        p.query = "system:config:query";
        registerCrud(r, "/system/config", specSysConfig(), p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictData.java
        // ruoyi-system/src/main/resources/mapper/system/SysDictDataMapper.xml
        Perms p;
        p.list = "system:dict:list";
        p.exportList = "system:dict:export";
        p.query = "system:dict:query";
        registerCrud(r, "/system/dict/data", specSysDictData(), p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictType.java
        // ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml
        Perms p;
        p.list = "system:dict:list";
        p.exportList = "system:dict:export";
        p.query = "system:dict:query";
        registerCrud(r, "/system/dict/type", specSysDictType(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysFile.java
        // ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml
        Perms p;
        p.list = "base:sysflie:list";
        registerCrud(r, "/system/file", specSysFile(), p, "ids");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysNotice.java
        // ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml
        Perms p;
        p.list = "system:notice:list";
        registerCrud(r, "/system/notice", specSysNotice(), p, "id");
        registerListVariant(r, "/system/notice/listquery", specSysNotice(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java
        // ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
        Perms p;
        p.list = "system:post:list";
        p.exportList = "system:post:export";
        p.query = "system:post:query";
        registerCrud(r, "/system/post", specSysPost(), p, "id");
    }
    {
        // ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java
        // ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml
        Perms p;
        p.list = "system:role:list";
        p.exportList = "system:role:export";
        p.query = "system:role:query";
        registerCrud(r, "/system/role", specSysRole(), p, "id");
    }
}

} // namespace cm::web::crud
