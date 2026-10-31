// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java
// 类/职责: 路线几何（桩号 -> 经纬度）查询与同步
// 对应 Go 文件: internal/modules/base/geometry.go
//
// DIFF: /getHenDa、/syncAllGeometry1 在 Java 里依赖外部恒达（HenDa）服务
// ($forest.variables.hendaUrl + hengda.appid/secret 签名)。本迁移不接外部调用，
// 但保持与 Java 一致的响应形态（getHenDa / syncAllGeometry1 恒为 code 200）。
package base

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// geometryGetHenDa 对应 GET /base/geometry/getHenDa。
//
// JAVA 对照: HenDa 不可达时 getPileToLonLat 返回 null，控制器仍然 AjaxResult.success(null)，
// 即 code 200 +「操作成功」且不带 data 键。
func (h *handler) geometryGetHenDa(c *gin.Context) {
	web.JSON(c, web.Success())
}

// geometrySyncAll 对应 GET /base/geometry/syncAllGeometry。
//
// JAVA 对照: GeometryServiceImpl.syncAllGeometry 先查 geometry_copy1。
// 目标库没有该表，Java 抛 SQLSyntaxErrorException（code 500），这里照做让 SQL 真正执行并失败。
func (h *handler) geometrySyncAll(c *gin.Context) {
	var rows []map[string]any
	if err := h.app.DB.WithContext(c.Request.Context()).Raw("SELECT * FROM geometry_copy1").Scan(&rows).Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// geometrySyncAllOne 对应 GET /base/geometry/syncAllGeometry1（手动补齐一条路线）。
//
// JAVA 对照: 控制器把几何交给线程池后立刻 AjaxResult.success()，因此恒为 code 200；
// HenDa 外呼失败只体现在后台线程日志里。
func (h *handler) geometrySyncAllOne(c *gin.Context) {
	web.JSON(c, web.Success())
}
