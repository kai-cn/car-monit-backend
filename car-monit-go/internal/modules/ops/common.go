// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CommonController.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ServerConfig.java
// 类/职责: 通用下载 / 单文件上传 / 多文件上传 / 本地资源下载
// 对应 Go 文件: internal/modules/ops/common.go
//
// DIFF: Java 的 /common/download 在 SecurityConfig 里是 anonymous()（**只**允许匿名），
// Go 的 Engine 分组没有认证中间件，因此匿名与已登录请求都能访问 —— 对“浏览器直接下载”
// 这个真实用法没有影响。
// DIFF: fileDownload 的错误全部吞掉（catch + log），响应保持 200：缺 fileName、后缀不在
// 白名单、文件不存在都回空 body；缺 delete 参数时不删除文件（Java 在 if (delete) 处 NPE，
// 同样被 catch）。
// DIFF: uploadFile(s) 的 URL 由请求的 scheme/host + server.context-path 拼出，对应
// ServerConfig.getDomain；context-path 为 "/" 时与 Spring 一样视为空串。
// DIFF: /common/download/resource 的方法体在 Java 里整块被注释，仅白名单校验是活的；
// 这里同样始终返回 200 + 空 body。
package ops

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// JAVA 对照: CommonController.FILE_DELIMETER（Java 原文拼写如此）。
const fileDelimeter = ","

// JAVA 对照: MediaType.APPLICATION_OCTET_STREAM_VALUE
const octetStream = "application/octet-stream"

type commonHandler struct {
	app *app.App
}

// Download 对应 GET /common/download?fileName=&delete=。
func (h *commonHandler) Download(c *gin.Context) {
	fileName := c.Query("fileName")
	deleteRaw, deletePresent := c.GetQuery("delete")
	deleteFlag, err := springBool(deleteRaw, deletePresent)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	if !checkAllowDownload(fileName) {
		h.app.Log.Error("下载文件失败",
			"err", fmt.Sprintf("文件名称(%s)非法，不允许下载。 ", fileName))
		return
	}

	// Java: System.currentTimeMillis() + fileName.substring(fileName.indexOf("_") + 1)
	realFileName := strconv.FormatInt(time.Now().UnixMilli(), 10) + substringAfterUnderscore(fileName)
	filePath := h.app.Cfg.RuoYi.DownloadPath() + fileName

	c.Header("Content-Type", octetStream)
	setAttachmentResponseHeader(c, realFileName)
	if err := writeBytes(filePath, c.Writer); err != nil {
		// Java: FileNotFoundException 在 finally 关流后变成 "200 + 响应头 + 空 body"。
		h.app.Log.Error("下载文件失败", "err", err)
		return
	}
	// Java: if (delete) —— 缺参时拆箱 NPE，被 catch，文件不删除。
	if deleteFlag != nil && *deleteFlag {
		deleteFile(filePath)
	}
}

// substringAfterUnderscore 复刻 fileName.substring(fileName.indexOf("_") + 1)：
// 没有 "_" 时 indexOf 返回 -1，substring(0) 就是整个文件名。
func substringAfterUnderscore(fileName string) string {
	idx := strings.Index(fileName, "_")
	if idx < 0 {
		return fileName
	}
	return fileName[idx+1:]
}

// Upload 对应 POST /common/upload（单文件，部件名 "file"）。
func (h *commonHandler) Upload(c *gin.Context) {
	fh, err := c.FormFile("file")
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	fileName, err := uploadFile(h.app.Cfg.RuoYi.UploadPath(), h.app.Cfg.RuoYi.Profile, fh)
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	ajax := web.Success()
	ajax.Put("url", serverBaseURL(c, h.app)+fileName)
	ajax.Put("fileName", fileName)
	ajax.Put("newFileName", getName(fileName))
	ajax.Put("originalFilename", fh.Filename)
	web.JSON(c, ajax)
}

// Uploads 对应 POST /common/uploads（同名部件 "files" 重复提交，逗号拼接返回）。
func (h *commonHandler) Uploads(c *gin.Context) {
	form, err := c.MultipartForm()
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	files := form.File["files"]
	urls := make([]string, 0, len(files))
	fileNames := make([]string, 0, len(files))
	newFileNames := make([]string, 0, len(files))
	originalFilenames := make([]string, 0, len(files))
	for _, fh := range files {
		fileName, err := uploadFile(h.app.Cfg.RuoYi.UploadPath(), h.app.Cfg.RuoYi.Profile, fh)
		if err != nil {
			// Java: 任一个失败即整体 error，已落盘的前序文件不清理。
			web.JSON(c, web.ErrorMsg(err.Error()))
			return
		}
		urls = append(urls, serverBaseURL(c, h.app)+fileName)
		fileNames = append(fileNames, fileName)
		newFileNames = append(newFileNames, getName(fileName))
		originalFilenames = append(originalFilenames, fh.Filename)
	}
	ajax := web.Success()
	ajax.Put("urls", strings.Join(urls, fileDelimeter))
	ajax.Put("fileNames", strings.Join(fileNames, fileDelimeter))
	ajax.Put("newFileNames", strings.Join(newFileNames, fileDelimeter))
	ajax.Put("originalFilenames", strings.Join(originalFilenames, fileDelimeter))
	web.JSON(c, ajax)
}

// ResourceDownload 对应 GET /common/download/resource：方法体在 Java 里被注释，
// 只有白名单校验会执行，且通过与否响应一致（200 + 空 body）。
func (h *commonHandler) ResourceDownload(c *gin.Context) {
	resource := c.Query("resource")
	if !checkAllowDownload(resource) {
		h.app.Log.Error("下载文件失败",
			"err", fmt.Sprintf("资源文件(%s)非法，不允许下载。 ", resource))
	}
	c.Status(http.StatusOK)
}

// serverBaseURL 对应 ServerConfig.getDomain：scheme + host + contextPath。
// Java 的 ServletContext#getContextPath 在根上下文返回 ""，配置 "/" 时同样视为空串。
func serverBaseURL(c *gin.Context, a *app.App) string {
	scheme := "http"
	if c.Request.TLS != nil {
		scheme = "https"
	}
	if proto := c.GetHeader("X-Forwarded-Proto"); proto != "" {
		scheme = proto
	}
	contextPath := a.Cfg.Server.ContextPath
	if contextPath == "/" {
		contextPath = ""
	}
	return scheme + "://" + c.Request.Host + contextPath
}

// newCommonRoutes 注册 /common/**。
func newCommonRoutes(reg *router.Registry, a *app.App) {
	h := &commonHandler{app: a}
	// JAVA 对照: SecurityConfig antMatchers("/common/download**").anonymous()
	reg.Engine.GET("/common/download", h.Download)

	authed := reg.Authed.Group("/common")
	authed.POST("/upload", h.Upload)
	authed.POST("/uploads", h.Uploads)
	authed.GET("/download/resource", h.ResourceDownload)
}
