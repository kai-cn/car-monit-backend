#pragma once
// 对应 Java: com.ruoyi.web.controller.manager.{CarInfoController,CarExceptRecordController}#doImport
//
// 只做一件事：注册两个 Excel 导入端点。
//   POST /manager/carinfo/import       车辆信息导入（8 列，表头在第 1 行）
//   POST /manager/exceptrecord/import  新增流水导入（22 列，表头在第 2 行**或**第 3 行）
namespace cm::web {

void registerManagerImportControllers(class Router& r);

} // namespace cm::web
