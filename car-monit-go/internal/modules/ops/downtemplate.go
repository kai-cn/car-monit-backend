// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/DownTemplateController.java
// 类/职责: 模板下载 — 按 type 从 templates/down 读取 xlsx 并原样写出
// 对应 Go 文件: internal/modules/ops/downtemplate.go
//
// DIFF: Java 从 classpath:templates/down 读取；Go 以配置文件所在目录为根
// （configs/templates/down），模板文件已从 ruoyi-admin/src/main/resources 拷贝过来。
// DIFF: 未知 type 与模板缺失走同一条失败路径：读文件失败 -> 200 + 空 body + 无响应头，
// 对应 Java 的 catch (Exception e) { e.printStackTrace(); } + return null。
// DIFF: easypoi 的 TemplateExportParams(url, true) + 空 HashMap 对这 7 个模板是"原样输出"
// （模板中没有 ${...} 占位符），因此直接返回原始字节，避免 POI 重写丢失数据校验/表单控件。
package ops

import (
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
)

// JAVA 对照: DownTemplateController 的 `String url = "templates/down"`。
const templateDir = "templates/down"

// JAVA 对照: response.setContentType("application/octet-stream;charset=UTF-8")
const templateContentType = "application/octet-stream;charset=UTF-8"

// templateByType 顺序与 Java 的 if/else 链一致。
var templateByType = map[string]string{
	"goodsFkApplyDetail":        "importGoodsFkApplyDetail.xlsx",
	"goodsRkApplyDetail":        "importGoodsRkApplyDetail.xlsx",
	"planListDetail":            "importPlanListDetail.xlsx",
	"importPsbz":                "importPsbz.xlsx",
	"importSupplierAnnualScore": "importSupplierAnnualScore.xlsx",
	"carinfo":                   "importCar.xlsx",
	"carExcept":                 "importCarExcept.xlsx",
}

type downTemplateHandler struct {
	app *app.App
}

// DownExcel 对应 GET /downTemplate/{type}（登录即可，无权限点）。
func (h *downTemplateHandler) DownExcel(c *gin.Context) {
	typeName := c.Param("type")
	content, err := os.ReadFile(resolveTemplatePath(h.app.Cfg.ConfigFile, typeName))
	if err != nil {
		// Java: e.printStackTrace()（不经过日志框架）；这里走 slog，级别等价。
		// 全接口探测用占位 type；返回 200 空响应与 Java 基准 HTTP 行为一致。
		h.app.Log.Error("模板下载失败", "type", typeName, "err", err)
		c.Data(200, templateContentType, []byte{})
		return
	}
	c.Header("Content-Disposition", "attachment")
	c.Data(200, templateContentType, content)
}

// resolveTemplatePath 把 type 映射成磁盘路径；未知 type 落到目录本身（读文件必然失败），
// 与 Java 让异常发生在 ExcelExportUtil 里的位置一致。
//
// 根目录有两个候选：Java 从 classpath 取模板、位置与配置文件无关；Go 原先只认
// 「配置文件同级 templates/down」，配置被搬到别处（校验用的临时配置就是这样）时
// 七个合法 type 全退成 200 空 body。
//
// 安全口径：请求里的 type 只当 map 的键用，路径的每一段都来自本包常量（templateDir 与
// templateByType 的值），拼不出 ../，所以不存在目录穿越面。
func resolveTemplatePath(configFile, typeName string) string {
	name := ""
	if f, ok := templateByType[typeName]; ok {
		name = f
	}
	roots := []string{filepath.Dir(configFile)}
	if wd, err := os.Getwd(); err == nil {
		roots = append(roots, filepath.Join(wd, "configs"))
	}
	if name != "" {
		for _, root := range roots {
			p := filepath.Join(root, templateDir, filepath.FromSlash(name))
			if st, err := os.Stat(p); err == nil && !st.IsDir() {
				return p
			}
		}
	}
	// 全都找不着：返回目录路径，让读文件失败走与 Java 相同的"空 200"分支。
	return filepath.Join(roots[0], templateDir)
}

// newDownTemplateRoutes 注册 /downTemplate/**。
func newDownTemplateRoutes(reg gin.IRouter, a *app.App) {
	h := &downTemplateHandler{app: a}
	reg.GET("/downTemplate/:type", h.DownExcel)
}
