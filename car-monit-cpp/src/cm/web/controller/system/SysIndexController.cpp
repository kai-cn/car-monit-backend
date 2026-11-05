// 对应 Java: com.ruoyi.web.controller.system.SysIndexController
#include <string>

#include "cm/framework/config/AppConfig.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/controller/Controllers.hpp"
#include "cm/web/controller/system/SysAuthControllers.hpp"
#include "cm/web/controller/system/SysFileUploadController.hpp"
#include "cm/system/service/SysIndexMenuService.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/controller/base/CdcController.hpp"
#include "cm/web/controller/base/GeometrySyncController.hpp"
#include "cm/web/controller/common/CommonController.hpp"
#include "cm/web/controller/common/DownTemplateController.hpp"
#include "cm/web/controller/flow/FlowExtraControllers.hpp"
#include "cm/web/controller/manager/BigScreenController.hpp"
#include "cm/web/controller/manager/ManagerExtraControllers.hpp"
#include "cm/web/controller/manager/ManagerTemplateExportControllers.hpp"
#include "cm/web/controller/monitor/CacheController.hpp"
#include "cm/web/controller/monitor/ServerController.hpp"
#include "cm/web/controller/monitor/SysLogininforController.hpp"
#include "cm/web/controller/monitor/SysOperlogController.hpp"
#include "cm/web/controller/monitor/SysUserOnlineController.hpp"
#include "cm/web/controller/quartz/QuartzExtraControllers.hpp"
#include "cm/web/controller/system/SysAuxControllers.hpp"
#include "cm/web/controller/tool/TestController.hpp"
#include "cm/web/controller/tool/GenController.hpp"

namespace cm::web {

void registerIndexController(Router& r) {
    // @RequestMapping("/") —— 所有方法都映射到同一处理器
    auto handler = [](RequestContext&) -> cm::http::ApiResponse {
        auto& cfg = cm::config::AppConfig::instance();
        // StringUtils.format("欢迎使用{}后台管理框架，请通过前端地址访问。", name)
        return cm::http::ApiResponse::text(
            "欢迎使用" + cfg.name + "后台管理框架，请通过前端地址访问。",
            "text/plain;charset=UTF-8");
    };
    r.get("/", handler).permitAll();
    r.post("/", handler).permitAll();
    r.put("/", handler).permitAll();
    r.del("/", handler).permitAll();
    r.patch("/", handler).permitAll();
}

void registerControllers(Router& r) {
    registerCaptchaController(r);
    registerLoginController(r);
    registerIndexController(r);
    // common
    registerCommonController(r);
    registerDownTemplateController(r);
    // monitor
    registerCacheController(r);
    registerServerController(r);
    registerSysLogininforController(r);
    registerSysOperlogController(r);
    registerSysUserOnlineController(r);
    // system 辅助模块
    registerSysConfigController(r);
    registerSysDictTypeController(r);
    registerSysDictDataController(r);
    registerSysNoticeController(r);
    registerSysUpgradeInfoController(r);
    registerSysFileController(r);
    registerSysFileUploadController(r);
    registerGeometrySyncController(r);
    // tool
    // system 权限域：树形构建 / 数据范围 / 密码策略 / UUID 主键等均非同构 CRUD，逐个手写
    registerSysUserController(r);
    registerSysProfileController(r);
    registerSysRoleController(r);
    registerSysDeptController(r);
    registerSysMenuController(r);
    registerSysPostExtraController(r);
    registerSysIndexMenuController(r);
    registerCdcController(r);
    registerFlowExtraControllers(r);
    registerManagerExtraControllers(r);
    registerManagerTemplateExportControllers(r);
    registerBigScreenController(r);
    registerQuartzExtraControllers(r);
    registerTestController(r);
    registerGenController(r);
    // 业务域（base / manager / flow）：同构 CRUD 由 spec 引擎批量注册
    crud::registerBaseArea(r);
    crud::registerManagerArea(r);
    crud::registerFlowArea(r);
    crud::registerSystemArea(r);   // SysPost / SysIndexMenu
    crud::registerQuartzArea(r);   // SysJob / SysJobLog
}

} // namespace cm::web
