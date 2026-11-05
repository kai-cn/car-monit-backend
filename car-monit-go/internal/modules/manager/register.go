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
			// JAVA 对照: CarFeeRecord.java:29-96 的 @Excel 声明序（17 列）。
			// 车型/车种在 Java 侧没有 dictType/readConverterExp ⇒ 输出裸码，不能挂 Dict。
			{Title: "车辆id", Field: "carId"}, {Title: "车牌号", Field: "carNo"},
			{Title: "车型", Field: "carType"}, {Title: "车种", Field: "carVehicle"},
			{Title: "入口站id", Field: "inStationId"}, {Title: "入口站", Field: "inStation"},
			{Title: "入口时间", Field: "inTime"},
			{Title: "出口站id", Field: "outStationId"}, {Title: "出口站", Field: "outStation"},
			{Title: "出口时间", Field: "outTime"},
			{Title: "交易类型", Field: "chargeType", Exp: "字=典：1出口交易2逃费补缴"},
			{Title: "收费金额", Field: "amount", Money: true},
			{Title: "异常流水id", Field: "exceptId"},
			{Title: "备用字段1", Field: "backCol1"}, {Title: "备用字段2", Field: "backCol2"},
			{Title: "状态", Field: "status", Exp: "0=正常1停用"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/routedetail", "manager:routedetail", "常用路线明细", routeDetailSpec,
		"carRouteDetail.xlsx", "常用路线明细数据", true, []exportCol{
			// JAVA 对照: CarRouteDetail.java:28-127 的 @Excel 声明序（25 列）。
			// 第 12 列标题里的 ⾏(U+2F8F)/⽅(U+2F45) 是 Kangxi 部首字形，不是 行/方，
			// 照抄注解原文（已从 Java 生成的 xlsx 反查码位确认），不要"顺手改正"。
			{Title: "路线d", Field: "routeId"}, {Title: "车辆id", Field: "carId"},
			{Title: "车牌号", Field: "carNo"},
			{Title: "数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)", Field: "dataSource"},
			{Title: "来源名称", Field: "dataSourceName"},
			{Title: "最后通行时间", Field: "lastPassTime"},
			{Title: "最后通行图片", Field: "lastPassPicture"},
			{Title: "最后通行类型(1?架2收费拍)3服务区)", Field: "lastPassType"},
			{Title: "最后通行地址", Field: "lastPassAddress"},
			{Title: "最后通行经度", Field: "lastPassLongitude"},
			{Title: "最后通行维度", Field: "lastPassLatitude"},
			{Title: "⾏驶⽅向(1上行2下行3未知)", Field: "lastPassCardirection"},
			{Title: "管理中心路段id", Field: "roadSectionId"},
			{Title: "管理中心路段名称", Field: "roadSectionName"},
			{Title: "预计下一个通行时间", Field: "nextPassTime"},
			{Title: "预计下一个通行类型", Field: "nextPassType"},
			{Title: "预计下一个通行地址", Field: "nextPassAddress"},
			{Title: "预计下一个通行经度", Field: "nextPassLongitude"},
			{Title: "预计下一个通行维度", Field: "nextPassLatitude"},
			{Title: "管理中心id", Field: "orgId"}, {Title: "管理中心名称", Field: "orgName"},
			{Title: "备用字段1", Field: "backCol1"}, {Title: "备用字段2", Field: "backCol2"},
			{Title: "状态", Field: "status", Exp: "0=正常1停用"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/carsuspiciousback", "manager:carsuspiciousback", "可疑车辆备份", suspiciousBackSpec,
		"carSuspiciousBack.xlsx", "可疑车辆备份数据", true, suspiciousBackExportCols())
	registerStandard(reg, h, "/manager/suspiciouscheck", "manager:suspiciouscheck", "人工核实", suspiciousCheckSpec,
		"carSuspiciousCheck.xlsx", "人工核实", false, []exportCol{
			// JAVA 对照: templates/export/carSuspiciousCheck.xlsx 的 $fe 引用里
			// ruleName/noticeRangeAnme/notice/noticeType/noticeUserName/orgName 在
			// CarSuspiciousCheck 与其父类上都不存在 ⇒ EasyPOI 写 String.valueOf(缺失) = 空串。
			{Title: "车牌号", Field: "carNo"}, {Title: "规则名称"},
			{Title: "预警范围"}, {Title: "通知"}, {Title: "通知方式"},
			{Title: "通知人员"}, {Title: "所属站/所"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/warningrule", "manager:warningrule", "预警规则", warningRuleSpec,
		"carWarningRule.xlsx", "预警规则", false, []exportCol{
			{Title: "预警对象", Field: "noticeRangeAnme"},
			{Title: "通知方式", Field: "noticeType", Dict: "notice_type", BlankOnMiss: true},
			{Title: "通知人员", Field: "noticeUserName"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/querylog", "manager:querylog", "查询日志", queryLogSpec,
		"queryLog.xlsx", "查询日志", false, []exportCol{
			{Title: "用户名称", Field: "userName"}, {Title: "用户IP", Field: "userIp"},
			{Title: "模块菜单", Field: "modelType", Dict: "model_type"},
			{Title: "模块功能", Field: "menuPoint", Dict: "menu_point"},
			{Title: "创建时间", Field: "createTime", Stamp: true},
			{Title: "查询条件", Field: "queryCondition"},
		})
	registerStandard(reg, h, "/manager/gantrycar", "manager:gantrycar", "门架车辆", gantryCarSpec,
		"gantryCar.xlsx", "门架车辆", false, []exportCol{
			{Title: "车牌号", Field: "carNo"},
			{Title: "车型", Field: "carType", Dict: "car_type", BlankOnMiss: true},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
			{Title: "轴数", Field: "carNum"}, {Title: "入口站", Field: "inStation"},
			{Title: "通行时间", Field: "inTime", JavaDate: true},
			// G~J：模板引用 t.outStation/t.outTime/t.chargeType/t.amount，GantryCar 上没有这些属性 ⇒ 空列
			{Title: "出口门架"}, {Title: "出口时间"}, {Title: "交易类型"}, {Title: "收费金额"},
			{Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/whiteinfo", "manager:whiteinfo", "白名单", whiteInfoSpec,
		"carWhiteInfo.xlsx", "白名单", false, []exportCol{
			{Title: "车牌颜色", Field: "plateColor", Dict: "plate_color", BlankOnMiss: true},
			{Title: "车牌号", Field: "carNo"},
			{Title: "车型", Field: "carType", Dict: "car_type", BlankOnMiss: true},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
			{Title: "轴数", Field: "carNum"},
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
			{Title: "车牌号", Field: "carNo"},
			{Title: "车型", Field: "carType", Dict: "car_type", BlankOnMiss: true},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
			{Title: "轴数", Field: "carNum"},
			// JAVA 对照: CarSplitRecordController:84 用 car_vehicle 去查 pass_type 字典
			// （dp.setPassType(isNull(passTypeMap.get(dp.getCarVehicle())))），照抄这个错键。
			{Title: "通信标识", Field: "carVehicle", Dict: "pass_type", BlankOnMiss: true},
			{Title: "入口站", Field: "inStation"},
			{Title: "出口站", Field: "outStation"},
			// car_split_record 与其域对象都没有 remark 属性
			{Title: "备注"},
		})
	registerStandard(reg, h, "/manager/gantrytrade", "manager:gantrytrade", "门架交易", gantryTradeSpec,
		"gantryTrade.xlsx", "门架交易", false, []exportCol{
			{Title: "车牌号", Field: "carNo"},
			{Title: "车型", Field: "carType", Dict: "car_type", BlankOnMiss: true},
			{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
			{Title: "轴数", Field: "carNum"},
			// E/M/N/O：模板引用 t.passType/t.escapedType/t.orgName 等，域对象上没有 ⇒ 空列
			{Title: "通行标识"}, {Title: "入口站", Field: "inStation"},
			{Title: "入口时间", Field: "inTime", JavaDate: true},
			{Title: "出口站", Field: "outStation"},
			{Title: "出口时间", Field: "outTime", JavaDate: true},
			{Title: "应缴金额"}, {Title: "收费金额"}, {Title: "差额"}, {Title: "逃费类型"},
			{Title: "管理中心名称"}, {Title: "备注", Field: "remark"},
		})
	registerStandard(reg, h, "/manager/busstest", "manager:busstest", "业务测试", bussTestSpec,
		"bussTest.xlsx", "业务测试数据", true, []exportCol{
			// JAVA 对照: BussTest.java:27-94 的 @Excel 声明序（17 列）。父类 BasePlusEntity 没有
			// @Excel ⇒ Java 不导出 createTime，原来那列"创建时间"是凭空加的。
			{Title: "业务名称", Field: "billName"},
			{Title: "业务名称(字典：1业务2其他)", Field: "billType"},
			{Title: "金额", Field: "amount", Money: true},
			{Title: "部门id", Field: "deptId"}, {Title: "人员id", Field: "userId"},
			{Title: "申请时间", Field: "applyTime"}, {Title: "时间时分秒", Field: "applyTime2"},
			{Title: "附件(逗号多个分割)", Field: "fileIds"}, {Title: "流程key", Field: "flowKey"},
			{Title: "流程实例ID", Field: "flowRuid"}, {Title: "流程申请ID", Field: "flowApplyOid"},
			{Title: "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)", Field: "flowStatus"},
			{Title: "审核时间", Field: "shTime"}, {Title: "备用字段1", Field: "backCol1"},
			{Title: "备用字段2", Field: "backCol2"},
			{Title: "状态", Field: "status", Exp: "0=正常1停用"},
			{Title: "备注", Field: "remark"},
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
//
// JAVA 对照: templates/export/carSuspicious.xlsx 的第 1 行标题与第 2 行 $fe 引用。
// 模板打印的是控制器拼好的派生字段（txTime/txAddress/mjTime/mjAddress/createTimeStr），
// 而不是原始 inTime/inStation 等；C 列是「车种」(carVehicle) 不是车型。
func suspiciousExportCols() []exportCol {
	return []exportCol{
		{Title: "车牌颜色", Field: "plateColor", Dict: "plate_color", BlankOnMiss: true},
		{Title: "车牌号", Field: "carNo"},
		{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
		{Title: "通行时间", Field: "txTime"},
		{Title: "入口站及出口站", Field: "txAddress"},
		{Title: "经过门架时间", Field: "mjTime"},
		{Title: "起始门架及终止门架", Field: "mjAddress"},
		{Title: "轴数", Field: "carNum"},
		// 通行标识：控制器里的 passType 翻译整段被注释掉了 ⇒ 原样输出
		{Title: "通行标识", Field: "passType"},
		{Title: "逃费类型", Field: "escapedType", Dict: "escaped_type", BlankOnMiss: true},
		{Title: "是否为可疑车辆", Field: "isExcept", Dict: "is_except", BlankOnMiss: true},
		{Title: "稽查状态", Field: "checkStatus", Dict: "check_status", BlankOnMiss: true},
		{Title: "备注", Field: "remark"},
		{Title: "录入时间", Field: "createTimeStr"},
	}
}

// suspiciousBackExportCols 对应 ExcelUtil<CarSuspiciousBack>：
// 备份实体的每个字段都带 @Excel，因此导出列就是字段声明顺序的全部 43 列。
//
// JAVA 对照: com/ruoyi/manager/domain/CarSuspiciousBack.java（@Excel 注解顺序）
func suspiciousBackExportCols() []exportCol {
	return []exportCol{
		// 注解原文是残缺的 readConverterExp（键是"字"），除值恰为"字"外恒不命中 ⇒ Java 整列空。
		{Title: "车牌颜色", Field: "plateColor", Exp: "字=典：1白色2黑色"},
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
		{Title: "逃费类型", Field: "escapedType", Exp: "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂"},
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
