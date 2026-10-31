// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/*.java（25 个控制器）
// 类/职责: base 模块路由总装配
// 对应 Go 文件: internal/modules/base/register.go
//
// DIFF: Spring 反射发现 @RestController；Go 显式注册。权限点、@Log 标题、HTTP 方法照抄。
// 注意：OdsCxztFwqcllsController 挂在 /manager/fwqclls（不属 /base/**），依原样注册。
package base

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

func init() { router.RegisterModule(Register) }

// Register 装配 base 模块全部路由。
func Register(reg *router.Registry) {
	h := newHandler(reg.App)
	auth := reg.Authed

	// ---------------------------------------------------------------- 服务区配置
	auth.GET("/base/configServiceArea/list", middleware.Perm("base:configServiceArea:list"),
		h.listHandler(serviceAreaSpec))
	auth.GET("/base/configServiceArea/listQuery", h.serviceAreaListQuery)
	auth.GET("/base/configServiceArea/export", middleware.Perm("base:configServiceArea:export"),
		middleware.OperLog(reg.App, "服务区", middleware.BusinessExport),
		h.exportHandler(serviceAreaSpec, "服务区数据", serviceAreaExportCols()))
	auth.GET("/base/configServiceArea/:id", h.getHandler(serviceAreaSpec))
	auth.POST("/base/configServiceArea", middleware.Perm("base:configServiceArea:add"),
		middleware.OperLog(reg.App, "服务区", middleware.BusinessInsert), h.saveHandler(serviceAreaSpec))
	auth.PUT("/base/configServiceArea", middleware.Perm("base:configServiceArea:edit"),
		middleware.OperLog(reg.App, "服务区", middleware.BusinessUpdate), h.saveHandler(serviceAreaSpec))
	auth.DELETE("/base/configServiceArea/:ids", middleware.Perm("base:configServiceArea:remove"),
		middleware.OperLog(reg.App, "服务区", middleware.BusinessDelete), h.deleteHandler(serviceAreaSpec))

	// ---------------------------------------------------------------- 服务区判定规则
	auth.GET("/base/config/list", middleware.Perm("base:config:list"), h.listHandler(carWarningConfigSpec))
	auth.GET("/base/config/export", middleware.Perm("base:config:export"),
		middleware.OperLog(reg.App, "服务区判定规则", middleware.BusinessExport),
		h.exportHandler(carWarningConfigSpec, "服务区判定规则数据", warningConfigExportCols()))
	auth.GET("/base/config/:id", h.getHandler(carWarningConfigSpec))
	auth.POST("/base/config", middleware.Perm("base:config:add"),
		middleware.OperLog(reg.App, "服务区判定规则", middleware.BusinessInsert), h.saveHandler(carWarningConfigSpec))
	auth.PUT("/base/config", middleware.Perm("base:config:edit"),
		middleware.OperLog(reg.App, "服务区判定规则", middleware.BusinessUpdate), h.saveHandler(carWarningConfigSpec))
	auth.DELETE("/base/config/:ids", middleware.Perm("base:config:remove"),
		middleware.OperLog(reg.App, "服务区判定规则", middleware.BusinessDelete), h.deleteHandler(carWarningConfigSpec))

	// ---------------------------------------------------------------- CDC 同步管理
	// JAVA 对照: 全部端点都没有 @PreAuthorize（登录即可）。clear 必须排在 {messageId} 之前。
	auth.GET("/base/cdc/status", h.cdcQueueStatus)
	auth.GET("/base/cdc/dead-letters", h.cdcDeadLetters)
	auth.GET("/base/cdc/retry-messages", h.cdcRetryMessages)
	auth.POST("/base/cdc/retry/:messageId", h.cdcRetryOne)
	auth.POST("/base/cdc/retry-all", h.cdcRetryAll)
	auth.DELETE("/base/cdc/dead-letters/clear", h.cdcClearDeadLetters)
	auth.DELETE("/base/cdc/dead-letters/:messageId", h.cdcDeleteDeadLetter)
	auth.GET("/base/cdc/config", h.cdcGetConfig)

	// ---------------------------------------------------------------- 服务区基础信息（列表无权限点）
	registerListOnly(reg, h, "/base/fwqjcxx", "base:fwqjcxx", "服务区基础信息", fwqjcxxSpec,
		"服务区基础信息数据", fwqjcxxExportCols())

	// ---------------------------------------------------------------- 收费所基础信息
	registerListOnly(reg, h, "/base/sfsjcxx", "base:sfsjcxx", "收费所基础信息", sfsjcxxSpec,
		"收费所基础信息数据", sfsjcxxExportCols())

	// ---------------------------------------------------------------- 收费站基础信息（治超）
	registerListOnly(reg, h, "/base/sfzjcxx", "base:sfzjcxx", "收费站基础信息", sfzjcxxSpec,
		"收费站基础信息数据", sfzjcxxExportCols())

	// ---------------------------------------------------------------- 路线几何
	auth.GET("/base/geometry/getHenDa", middleware.Perm("base:geometry:list"), h.geometryGetHenDa)
	auth.GET("/base/geometry/syncAllGeometry", h.geometrySyncAll)
	auth.GET("/base/geometry/syncAllGeometry1", h.geometrySyncAllOne)
	auth.GET("/base/geometry/list", middleware.Perm("base:geometry:list"), h.listHandler(geometrySpec))
	auth.GET("/base/geometry/export", middleware.Perm("base:geometry:export"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessExport),
		h.exportHandler(geometrySpec, "车辆信息数据", geometryExportCols()))
	auth.GET("/base/geometry/:id", h.getHandler(geometrySpec))
	auth.POST("/base/geometry", middleware.Perm("base:geometry:add"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessInsert), h.saveHandler(geometrySpec))
	auth.PUT("/base/geometry", middleware.Perm("base:geometry:edit"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessUpdate), h.saveHandler(geometrySpec))
	auth.DELETE("/base/geometry/:ids", middleware.Perm("base:geometry:remove"),
		middleware.OperLog(reg.App, "车辆信息", middleware.BusinessDelete), h.deleteHandler(geometrySpec))

	// ---------------------------------------------------------------- 门架信息
	auth.GET("/base/gantry/list", h.gantryList)
	auth.GET("/base/gantry/listAll", h.gantryListAll)
	auth.GET("/base/gantry/export", middleware.Perm("base:gantry:export"),
		middleware.OperLog(reg.App, "门架信息", middleware.BusinessExport), h.gantryExport)
	auth.GET("/base/gantry/:id", h.getHandler(gantrySpec))
	auth.POST("/base/gantry", middleware.Perm("base:gantry:add"),
		middleware.OperLog(reg.App, "门架信息", middleware.BusinessInsert), h.saveHandler(gantrySpec))
	auth.PUT("/base/gantry", middleware.Perm("base:gantry:edit"),
		middleware.OperLog(reg.App, "门架信息", middleware.BusinessUpdate), h.saveHandler(gantrySpec))
	auth.DELETE("/base/gantry/:ids", middleware.Perm("base:gantry:remove"),
		middleware.OperLog(reg.App, "门架信息", middleware.BusinessDelete), h.deleteHandler(gantrySpec))

	// ---------------------------------------------------------------- 路段信息
	auth.GET("/base/section/list", h.listHandler(sectionSpec))
	auth.GET("/base/section/listAll", h.listHandler(sectionSpec))
	auth.GET("/base/section/export", middleware.Perm("base:section:export"),
		middleware.OperLog(reg.App, "路段信息", middleware.BusinessExport),
		h.exportHandler(sectionSpec, "路段信息数据", sectionExportCols()))
	auth.GET("/base/section/:id", h.getHandler(sectionSpec))
	auth.POST("/base/section", middleware.Perm("base:section:add"),
		middleware.OperLog(reg.App, "路段信息", middleware.BusinessInsert), h.saveHandler(sectionSpec))
	auth.PUT("/base/section", middleware.Perm("base:section:edit"),
		middleware.OperLog(reg.App, "路段信息", middleware.BusinessUpdate), h.saveHandler(sectionSpec))
	auth.DELETE("/base/section/:ids", middleware.Perm("base:section:remove"),
		middleware.OperLog(reg.App, "路段信息", middleware.BusinessDelete), h.deleteHandler(sectionSpec))

	// ---------------------------------------------------------------- 收费站基础信息
	auth.GET("/base/toll/list", h.tollList)
	auth.GET("/base/toll/listAll", h.tollListAll)
	auth.GET("/base/toll/export", middleware.Perm("base:toll:export"),
		middleware.OperLog(reg.App, "收费站基础信息", middleware.BusinessExport),
		h.exportHandler(tollSpec, "收费站基础信息数据", tollExportCols()))
	auth.GET("/base/toll/:id", h.getHandler(tollSpec))
	auth.POST("/base/toll", middleware.Perm("base:toll:add"),
		middleware.OperLog(reg.App, "收费站基础信息", middleware.BusinessInsert), h.saveHandler(tollSpec))
	auth.PUT("/base/toll", middleware.Perm("base:toll:edit"),
		middleware.OperLog(reg.App, "收费站基础信息", middleware.BusinessUpdate), h.saveHandler(tollSpec))
	auth.DELETE("/base/toll/:ids", middleware.Perm("base:toll:remove"),
		middleware.OperLog(reg.App, "收费站基础信息", middleware.BusinessDelete), h.deleteHandler(tollSpec))

	// ---------------------------------------------------------------- 机构信息
	auth.GET("/base/org/list", h.listHandler(orgSpec))
	auth.GET("/base/org/export", middleware.Perm("base:org:export"),
		middleware.OperLog(reg.App, "机构信息", middleware.BusinessExport),
		h.exportHandler(orgSpec, "机构信息数据", orgExportCols()))
	auth.GET("/base/org/:id", h.getHandler(orgSpec))
	auth.POST("/base/org", middleware.Perm("base:org:add"),
		middleware.OperLog(reg.App, "机构信息", middleware.BusinessInsert), h.saveHandler(orgSpec))
	auth.PUT("/base/org", middleware.Perm("base:org:edit"),
		middleware.OperLog(reg.App, "机构信息", middleware.BusinessUpdate), h.saveHandler(orgSpec))
	auth.DELETE("/base/org/:ids", middleware.Perm("base:org:remove"),
		middleware.OperLog(reg.App, "机构信息", middleware.BusinessDelete), h.deleteHandler(orgSpec))

	// ---------------------------------------------------------------- 只读列表（设备 IP / 位置 / 拟合 / 轨迹 / 流水）
	registerListGet(auth, h, "/base/gantryIp", "", gantryIPSpec)
	registerListGet(auth, h, "/base/tollStationIp", "", tollStationIPSpec)
	registerListGet(auth, h, "/base/location", "", locationSpec)
	registerListGet(auth, h, "/base/fitting", "", fittingSpec)
	registerListGet(auth, h, "/base/trailtracks", "", trailTracksSpec)
	registerListGet(auth, h, "/base/feeStationEnter", "", feeStationEnterSpec)
	registerListGet(auth, h, "/base/provcapture", "", provCaptureSpec)
	registerListGet(auth, h, "/base/stationcapture", "", stationCaptureSpec)
	registerListGet(auth, h, "/base/vehicleweight", "", vehicleWeightSpec)
	registerListGet(auth, h, "/manager/fwqclls", "manager:fwqclls:list", fwqCllsSpec)

	// ---------------------------------------------------------------- 交易 / 收费流水（转发 + 模板导出）
	auth.GET("/base/feeGantry/list", middleware.Perm("base:feeGantry:list"), h.feeGantryList)
	auth.GET("/base/feeGantry/:id", h.feeGantryGet)
	auth.GET("/base/feerecords/list", middleware.Perm("base:feerecords:list"), h.feeRecordsList)
	auth.GET("/base/feerecords/export", middleware.Perm("base:feerecords:list"), h.feeRecordsExport)
	auth.GET("/base/feerecords/:id", h.feeRecordsGet)
	auth.GET("/base/feestationexit/list", middleware.Perm("base:feestationexit:list"), h.feeStationExitList)
	auth.GET("/base/feestationexit/:id", h.feeStationExitGet)

	// ---------------------------------------------------------------- 门架抓拍流水（分表）
	auth.GET("/base/snapshotflow/list", middleware.Perm("base:snapshotflow:list"), h.snapshotFlowList)
	auth.GET("/base/snapshotflow/export", middleware.Perm("base:snapshotflow:list"), h.snapshotFlowExport)
	auth.GET("/base/snapshotflow/earliest-time", h.snapshotFlowEarliest)
	auth.GET("/base/snapshotflow/:id", h.snapshotFlowGet)
}

// registerListOnly 装配「列表无权限点 + 其余标准 CRUD」的 dwd 系列控制器。
//
// JAVA 对照: DwdLczt* 三个控制器的 list 上没有 @PreAuthorize（导出有）。
func registerListOnly(reg *router.Registry, h *handler, base, perm, title string, spec *tableSpec,
	sheet string, cols []exportCol) {
	auth := reg.Authed
	auth.GET(base+"/list", h.listHandler(spec))
	auth.GET(base+"/export", middleware.Perm(perm+":export"),
		middleware.OperLog(reg.App, title, middleware.BusinessExport), h.exportHandler(spec, sheet, cols))
	auth.GET(base+"/:id", h.getHandler(spec))
	auth.POST(base, middleware.Perm(perm+":add"),
		middleware.OperLog(reg.App, title, middleware.BusinessInsert), h.saveHandler(spec))
	auth.PUT(base, middleware.Perm(perm+":edit"),
		middleware.OperLog(reg.App, title, middleware.BusinessUpdate), h.saveHandler(spec))
	auth.DELETE(base+"/:ids", middleware.Perm(perm+":remove"),
		middleware.OperLog(reg.App, title, middleware.BusinessDelete), h.deleteHandler(spec))
}

// registerListGet 装配只有 list / {id} 的只读控制器。
func registerListGet(auth *gin.RouterGroup, h *handler, base, listPerm string, spec *tableSpec) {
	if listPerm != "" {
		auth.GET(base+"/list", middleware.Perm(listPerm), h.listHandler(spec))
	} else {
		auth.GET(base+"/list", h.listHandler(spec))
	}
	auth.GET(base+"/:id", h.getHandler(spec))
}

// ---------------------------------------------------------------------------
// 处理器包装
// ---------------------------------------------------------------------------

func (h *handler) listHandler(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableList(c, spec) }
}

func (h *handler) getHandler(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableGet(c, spec) }
}

func (h *handler) saveHandler(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableSave(c, spec) }
}

func (h *handler) deleteHandler(spec *tableSpec) gin.HandlerFunc {
	return func(c *gin.Context) { h.tableDelete(c, spec) }
}

func (h *handler) exportHandler(spec *tableSpec, sheet string, cols []exportCol) gin.HandlerFunc {
	return func(c *gin.Context) { h.exportTable(c, spec, sheet, cols) }
}

// serviceAreaListQuery 对应 GET /base/configServiceArea/listQuery：不分页、无权限。
func (h *handler) serviceAreaListQuery(c *gin.Context) {
	clause, args := buildWhere(c, serviceAreaSpec.prefix(), serviceAreaSpec.conditions)
	dest := newSliceOf(&baseConfigServiceArea{})
	if _, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: serviceAreaSpec.selectSQL,
		FromSQL:   "FROM " + serviceAreaSpec.from() + " ",
		Where:     &whereClause{clause: clause, args: args},
	}, dest); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(dest))
}
