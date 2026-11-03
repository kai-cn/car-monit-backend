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
        // ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java
        // ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
        Spec s;
        s.table = "sys_post";
        s.alias = "t";
        s.fields = {
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
}

} // namespace cm::web::crud
