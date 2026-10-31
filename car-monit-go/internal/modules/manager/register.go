// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/*.java
// 类/职责: manager 模块路由总装配（20 个控制器）
// 对应 Go 文件: internal/modules/manager/register.go
//
// DIFF: Spring 反射发现 @RestController；Go 显式注册。权限点、@Log 标题、HTTP 方法照抄。
package manager

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
)

func init() { router.RegisterModule(Register) }

// Register 装配 /manager/** 全部路由。
func Register(reg *router.Registry) {
	h := newHandler(reg.App)
	auth := reg.Authed

	// ---------------------------------------------------------------- 标准 CRUD
	registerStandard(reg, h, "/manager/feerecord", "manager:feerecord", "收费流水", feeRecordSpec,
		"feeRecords.xlsx", "收费流水数据", true, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"},
			{Title: "入口站", Field: "inStation"}, {Title: "入口时间", Field: "inTime"},
			{Title: "出口站", Field: "outStation"}, {Title: "出口时间", Field: "outTime"},
			{Title: "收费类型", Field: "chargeType"}, {Title: "金额", Field: "amount"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/routedetail", "manager:routedetail", "常用路线明细", routeDetailSpec,
		"carRouteDetail.xlsx", "常用路线明细数据", true, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "数据来源", Field: "dataSourceName"},
			{Title: "通行时间", Field: "lastPassTime"}, {Title: "通行类型", Field: "lastPassType"},
			{Title: "通行地址", Field: "lastPassAddress"}, {Title: "路段名称", Field: "roadSectionName"},
			{Title: "下次通行时间", Field: "nextPassTime"}, {Title: "下次通行地址", Field: "nextPassAddress"},
			{Title: "机构", Field: "orgName"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/carsuspiciousback", "manager:carsuspiciousback", "可疑车辆备份", suspiciousBackSpec,
		"carSuspiciousBack.xlsx", "可疑车辆备份数据", true, suspiciousBackExportCols())
	registerStandard(reg, h, "/manager/suspiciouscheck", "manager:suspiciouscheck", "人工核实", suspiciousCheckSpec,
		"carSuspiciousCheck.xlsx", "人工核实", false, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "逃费类型", Field: "escapedType", Dict: "escaped_type"},
			{Title: "应缴金额（元）", Field: "totalAmount"}, {Title: "收费金额（元）", Field: "chargeAmount"},
			{Title: "差额（元）", Field: "difAmount"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/warningrule", "manager:warningrule", "预警规则", warningRuleSpec,
		"carWarningRule.xlsx", "预警规则", false, []exportCol{
			{Title: "预警规则", Field: "ruleName"}, {Title: "通知方式", Field: "noticeType", Dict: "notice_type"},
			{Title: "通知人员", Field: "noticeUserName"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/querylog", "manager:querylog", "查询日志", queryLogSpec,
		"queryLog.xlsx", "查询日志", false, []exportCol{
			{Title: "用户名称", Field: "userName"}, {Title: "用户IP", Field: "userIp"},
			{Title: "模块说明", Field: "modelType", Dict: "model_type"},
			{Title: "模块功能", Field: "menuPoint", Dict: "menu_point"},
			{Title: "查询时间", Field: "createTime"}, {Title: "查询条件", Field: "queryCondition"},
		})
	registerStandard(reg, h, "/manager/gantrycar", "manager:gantrycar", "门架车辆", gantryCarSpec,
		"gantryCar.xlsx", "门架车辆", false, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"}, {Title: "轴数", Field: "carNum"},
			{Title: "入口站", Field: "inStation"}, {Title: "通行时间", Field: "inTime"},
			{Title: "检测门架", Field: "gantrytStation"}, {Title: "经过时间", Field: "gantryTime"},
			{Title: "抓拍图片", Field: "fileIds"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/whiteinfo", "manager:whiteinfo", "白名单", whiteInfoSpec,
		"carWhiteInfo.xlsx", "白名单", false, []exportCol{
			{Title: "车牌颜色", Field: "plateColor", Dict: "plate_color"},
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"}, {Title: "轴数", Field: "carNum"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/routeinfo", "manager:routeinfo", "路线信息", routeInfoSpec,
		"carRouterInfo.xlsx", "路线信息", false, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"}, {Title: "轴数", Field: "carNum"},
			{Title: "起点通行地址", Field: "startAddress"}, {Title: "终点通行地址", Field: "endAddress"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/splitrecord", "manager:splitrecord", "拆分流水", splitRecordSpec,
		"carSplitRecord.xlsx", "拆分流水", false, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"}, {Title: "轴数", Field: "carNum"},
			{Title: "通行标识", Field: "passType"}, {Title: "入口站", Field: "inStation"},
			{Title: "出口站", Field: "outStation"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/gantrytrade", "manager:gantrytrade", "门架交易", gantryTradeSpec,
		"gantryTrade.xlsx", "门架交易", false, []exportCol{
			{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"}, {Title: "轴数", Field: "carNum"},
			{Title: "入口站", Field: "inStation"}, {Title: "入口时间", Field: "inTime"},
			{Title: "出口站", Field: "outStation"}, {Title: "出口时间", Field: "outTime"},
			{Title: "收费类型", Field: "chargeType"}, {Title: "金额", Field: "amount"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/busstest", "manager:busstest", "业务测试", bussTestSpec,
		"bussTest.xlsx", "业务测试数据", true, []exportCol{
			{Title: "单据名称", Field: "billName"}, {Title: "单据类型", Field: "billType"},
			{Title: "金额", Field: "amount"}, {Title: "状态", Field: "status"},
			{Title: "备注", Field: "remark"}, {Title: "创建时间", Field: "createTime"},
		})
	auth.POST("/manager/busstest/syncCurrentTrack", middleware.Perm("manager:busstest:syncTest"),
		middleware.OperLog(reg.App, "业务测试", middleware.BusinessInsert), h.bussTestSyncCurrentTrack)

	// ---------------------------------------------------------------- 车辆信息
	auth.GET("/manager/carinfo/list", middleware.Perm("manager:carinfo:list"), h.carInfoList)
	auth.GET("/manager/carinfo/listAll", h.carInfoList)
	auth.GET("/manager/carinfo/export", middleware.Perm("manager:carinfo:export"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessExport), h.carInfoExport)
	auth.GET("/manager/carinfo/:id", h.carInfoGet)
	auth.POST("/manager/carinfo", middleware.OperLog(reg.App, "车辆信息", middleware.BusinessInsert), h.carInfoSave)
	auth.PUT("/manager/carinfo", middleware.Perm("manager:carinfo:edit"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessUpdate), h.carInfoSave)
	auth.DELETE("/manager/carinfo/:ids", middleware.Perm("manager:carinfo:remove"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessDelete), h.carInfoDelete)
	auth.POST("/manager/carinfo/import", middleware.OperLog(reg.App, "车辆信息", middleware.BusinessImport), h.carInfoImport)

	// ---------------------------------------------------------------- 预警车辆
	auth.GET("/manager/carwarning/list", h.warningInfoList)
	auth.GET("/manager/carwarning/export", middleware.Perm("manager:carwarning:export"),
		middleware.OperLog(reg.App, "预警车辆", middleware.BusinessExport), h.warningInfoExport)
	auth.GET("/manager/carwarning/:id", h.warningInfoGet)
	auth.POST("/manager/carwarning", middleware.Perm("manager:carwarning:add"),
		middleware.OperLog(reg.App, "预警车辆", middleware.BusinessInsert), h.warningInfoSave)
	auth.PUT("/manager/carwarning", middleware.Perm("manager:carwarning:edit"),
		middleware.OperLog(reg.App, "预警车辆", middleware.BusinessUpdate), h.warningInfoSave)
	auth.DELETE("/manager/carwarning/:ids", middleware.Perm("manager:carwarning:remove"),
		middleware.OperLog(reg.App, "预警车辆", middleware.BusinessDelete), h.warningInfoDelete)

	// ---------------------------------------------------------------- 补缴处理
	h.registerAduitFree(reg)
	// ---------------------------------------------------------------- 确认补缴
	h.registerConfimFree(reg)
	// ---------------------------------------------------------------- 异常流水
	h.registerExceptRecord(reg)
	// ---------------------------------------------------------------- 行驶轨迹
	h.registerTrackInfo(reg)
	// ---------------------------------------------------------------- 可疑车辆
	h.registerSuspicious(reg)
	// ---------------------------------------------------------------- 大屏
	registerBigScreen(reg, h)
}

// registerStandard 装配一组「生成器模板」CRUD 路由。
func registerStandard(reg *router.Registry, h *handler, base, perm, title string, spec *tableSpec,
	fileName, sheet string, envelope bool, cols []exportCol) {
	auth := reg.Authed
	auth.GET(base+"/list", middleware.Perm(perm+":list"), h.tableList2(spec))
	auth.GET(base+"/export", middleware.Perm(perm+":export"),
		middleware.OperLog(reg.App, title, middleware.BusinessExport), h.tableExport2(spec, fileName, sheet, cols, envelope))
	auth.GET(base+"/:id", h.tableGet2(spec))
	auth.POST(base, middleware.Perm(perm+":add"),
		middleware.OperLog(reg.App, title, middleware.BusinessInsert), h.tableSave2(spec))
	auth.PUT(base, middleware.Perm(perm+":edit"),
		middleware.OperLog(reg.App, title, middleware.BusinessUpdate), h.tableSave2(spec))
	auth.DELETE(base+"/:ids", middleware.Perm(perm+":remove"),
		middleware.OperLog(reg.App, title, middleware.BusinessDelete), h.tableDelete2(spec))
}

// tableList2 等小包装把 tableSpec 绑定成 gin.HandlerFunc。
func (h *handler) tableList2(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableList(c, spec) }
}

func (h *handler) tableGet2(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableGet(c, spec) }
}

func (h *handler) tableSave2(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableSave(c, spec) }
}

func (h *handler) tableDelete2(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableDelete(c, spec) }
}

func (h *handler) tableExport2(spec *tableSpec, fileName, sheet string, cols []exportCol, envelope bool) gin.HandlerFunc {
	return func(c *gin.Context) { h.exportTable(c, spec, fileName, sheet, cols, envelope) }
}

// suspiciousExportCols 是可疑车辆（主表 / 历史表）共用的导出列。
func suspiciousExportCols() []exportCol {
	return []exportCol{
		{Title: "车牌颜色", Field: "plateColor", Dict: "plate_color"},
		{Title: "车牌号", Field: "carNo"},
		{Title: "车型", Field: "carType", Dict: "car_type"},
		{Title: "通行时间", Field: "inTime"},
		{Title: "入口站", Field: "inStation"},
		{Title: "经过门架时间", Field: "gantryTime"},
		{Title: "起始门架至终止门架", Field: "gantrytStation"},
		{Title: "轴数", Field: "carNum"},
		{Title: "通行标识", Field: "passType", Dict: "pass_type"},
		{Title: "逃费类型", Field: "escapedTypeName"},
		{Title: "是否为可疑车辆", Field: "isExcept", Dict: "is_except"},
		{Title: "核实状态", Field: "checkStatus", Dict: "check_status"},
		{Title: "备注", Field: "remark"},
		{Title: "录入时间", Field: "createTime"},
	}
}

// suspiciousBackExportCols 对应 ExcelUtil<CarSuspiciousBack>：
// 备份实体的每个字段都带 @Excel，因此导出列就是字段声明顺序的全部 43 列。
//
// JAVA 对照: com/ruoyi/manager/domain/CarSuspiciousBack.java（@Excel 注解顺序）
func suspiciousBackExportCols() []exportCol {
	return []exportCol{
		{Title: "车牌颜色", Field: "plateColor"},
		{Title: "车牌号", Field: "carNo"},
		{Title: "车型", Field: "carType"},
		{Title: "车种", Field: "carVehicle"},
		{Title: "轴数", Field: "carNum"},
		{Title: "通行标识", Field: "passType", Exp: "1=人工2ETC"},
		{Title: "入口站id", Field: "inStationId"},
		{Title: "入口站", Field: "inStation"},
		{Title: "通行时间", Field: "inTime"},
		{Title: "出口站id", Field: "outStationId"},
		{Title: "出口站", Field: "outStation"},
		{Title: "出口时间", Field: "outTime"},
		{Title: "门架id", Field: "gantryStationId"},
		{Title: "门架名称", Field: "gantrytStation"},
		{Title: "经过时间", Field: "gantryTime"},
		{Title: "图片(附件ids)", Field: "fileIds"},
		{Title: "终止门架id", Field: "outGantryStationId"},
		{Title: "终止门架名称", Field: "outGantrytStation"},
		{Title: "终止经过时间", Field: "outGantryTime"},
		{Title: "终止图片(附件ids)", Field: "outFileIds"},
		{Title: "逃费类型", Field: "escapedType"},
		{Title: "逃费类型名称", Field: "escapedTypeName"},
		{Title: "异常通行门架次数", Field: "escapedNum"},
		{Title: "是否为可疑车辆", Field: "isExcept"},
		{Title: "可疑原因", Field: "exceptRemark"},
		{Title: "可疑材料", Field: "exceptFileIds"},
		{Title: "核实状态", Field: "checkStatus", Exp: "0=未核实1已核实"},
		{Title: "管理中心id", Field: "orgId"},
		{Title: "管理中心名称", Field: "orgName"},
		{Title: "是否在白名单", Field: "isWhite", Exp: "0=否1是"},
		{Title: "白名单原因", Field: "whiteRemark"},
		{Title: "白名单材料", Field: "whiteFileIds"},
		{Title: "所属路线编码", Field: "roadCode"},
		{Title: "所属路线名称", Field: "roadName"},
		{Title: "所属路段编码", Field: "sectionCode"},
		{Title: "所属路段名称", Field: "sectionName"},
		{Title: "行驶轨迹id", Field: "trackId"},
		{Title: "行驶轨迹josn", Field: "trackJosn"},
		{Title: "轨迹点集合", Field: "trackNames"},
		{Title: "备用字段1", Field: "backCol1"},
		{Title: "备用字段2", Field: "backCol2"},
		{Title: "状态", Field: "status", Exp: "0=正常1停用"},
		{Title: "备注", Field: "remark"},
	}
}
