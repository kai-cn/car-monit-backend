// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysPostController.java:28-124
// 类/职责: /system/post/** 全部 HTTP 入口
// 对应 Go 文件: internal/modules/system/post_handler.go
package system

import (
	"fmt"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type postHandler struct {
	app *app.App
	svc *service
}

func newPostHandler(a *app.App, svc *service) *postHandler {
	return &postHandler{app: a, svc: svc}
}

// List 对应 SysPostController.list（PageHelper 分页）。
func (h *postHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectPostList(c.Request.Context(), parsePostQuery(c), web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysPostController.export。
func (h *postHandler) Export(c *gin.Context) {
	filename, err := h.svc.exportPosts(c.Request.Context(), parsePostQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// GetInfo 对应 SysPostController.getInfo。
func (h *postHandler) GetInfo(c *gin.Context) {
	id, err := parseLongParam("postId", c.Param("postId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	post, err := h.svc.selectPostByID(c.Request.Context(), id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(post))
}

// Add 对应 SysPostController.add。
func (h *postHandler) Add(c *gin.Context) {
	var body postBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	post, err := h.svc.checkPostNameUnique(ctx, strOr(body.PostName))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if post != nil && (body.PostID == nil || post.PostID != *body.PostID) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增岗位'%s'失败，岗位名称已存在", strOr(body.PostName))))
		return
	}
	post, err = h.svc.checkPostCodeUnique(ctx, strOr(body.PostCode))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if post != nil && (body.PostID == nil || post.PostID != *body.PostID) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增岗位'%s'失败，岗位编码已存在", strOr(body.PostName))))
		return
	}
	rows, err := h.svc.insertPost(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysPostController.edit。
func (h *postHandler) Edit(c *gin.Context) {
	var body postBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	post, err := h.svc.checkPostNameUnique(ctx, strOr(body.PostName))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if post != nil && (body.PostID == nil || post.PostID != *body.PostID) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改岗位'%s'失败，岗位名称已存在", strOr(body.PostName))))
		return
	}
	post, err = h.svc.checkPostCodeUnique(ctx, strOr(body.PostCode))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if post != nil && (body.PostID == nil || post.PostID != *body.PostID) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改岗位'%s'失败，岗位编码已存在", strOr(body.PostName))))
		return
	}
	rows, err := h.svc.updatePost(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysPostController.remove。
func (h *postHandler) Remove(c *gin.Context) {
	ids, err := parseIDList(c.Param("postIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deletePostByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// OptionSelect 对应 SysPostController.optionselect。
func (h *postHandler) OptionSelect(c *gin.Context) {
	rows, err := h.svc.selectPostAll(c.Request.Context())
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

func registerPost(reg *router.Registry, svc *service) {
	h := newPostHandler(reg.App, svc)
	g := reg.Authed.Group("/system/post")

	g.GET("/list", middleware.Perm("system:post:list"), h.List)
	g.GET("/export", middleware.Perm("system:post:export"),
		middleware.OperLog(reg.App, "岗位管理", middleware.BusinessExport), h.Export)
	g.GET("/optionselect", h.OptionSelect)
	g.GET("/:postId", middleware.Perm("system:post:query"), h.GetInfo)
	g.POST("", middleware.Perm("system:post:add"),
		middleware.OperLog(reg.App, "岗位管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:post:edit"),
		middleware.OperLog(reg.App, "岗位管理", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:postIds", middleware.Perm("system:post:remove"),
		middleware.OperLog(reg.App, "岗位管理", middleware.BusinessDelete), h.Remove)
}
