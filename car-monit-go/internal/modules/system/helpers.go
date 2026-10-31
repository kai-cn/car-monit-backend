// JAVA 对照: com/ruoyi/framework/web/exception/GlobalExceptionHandler.java
// 类/职责: 系统管理模块的 HTTP 参数辅助
// 对应 Go 文件: internal/modules/system/helpers.go
package system

import (
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// parseLongParam 对应 @PathVariable Long：类型不匹配时由全局异常处理器转成同一条文案。
func parseLongParam(name, raw string) (int64, error) {
	v, err := strconv.ParseInt(strings.TrimSpace(raw), 10, 64)
	if err != nil {
		return 0, web.NewServiceError(
			"请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Long'，但输入值为：'%s'", name, raw)
	}
	return v, nil
}

// bindBody 对应 @RequestBody：解析失败时返回参数解析异常文案。
func bindBody(c *gin.Context, out any) error {
	if err := c.ShouldBindJSON(out); err != nil {
		return web.NewServiceError("请求参数解析异常：%s", err.Error())
	}
	return nil
}
