// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDeptController.java:29-191
// 类/职责: /system/dept/** 全部 HTTP 入口
// 对应 Go 文件: internal/modules/system/dept_handler.go
//
// DIFF: SysDept 在 Java 里同时承担“查询条件 + 请求体”，Spring 用同名属性绑定；
// Go 侧查询参数显式解析为 deptQuery，请求体直接绑定 model.SysDept（JSON 字段名一致）。
package system

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type deptHandler struct {
	app *app.App
	svc *service
}

func newDeptHandler(a *app.App, svc *service) *deptHandler {
	return &deptHandler{app: a, svc: svc}
}

// parseDeptQuery 对应 Spring 对 SysDept 查询条件的属性绑定。
func parseDeptQuery(c *gin.Context) deptQuery {
	q := deptQuery{
		ParentID:    queryInt64(c, "parentId"),
		DeptName:    queryStr(c, "deptName"),
		Status:      queryStr(c, "status"),
		DeptID:      queryInt64(c, "deptId"),
		IsZbzg:      queryStr(c, "isZbzg"),
		IsUint:      queryStr(c, "isUint"),
		TreeLeavel:  queryInt(c, "treeLeavel"),
		SubCode:     queryStr(c, "subCode"),
		DeptJc:      queryStr(c, "deptJc"),
		TenantID:    queryInt64(c, "tenantId"),
		Flag:        queryStr(c, "flag"),
		DataID:      queryStr(c, "dataId"),
		LeaderID:    queryInt64(c, "leaderId"),
		Leader:      queryStr(c, "leader"),
		FgldID:      queryInt64(c, "fgldId"),
		FgldName:    queryStr(c, "fgldName"),
		DeptSubCode: queryStr(c, "deptSubCode"),
	}
	return q
}

// validateDept 对应 SysDept 上的 @Validated 约束（字段顺序与注解顺序一致）。
func validateDept(d *model.SysDept) string {
	switch {
	case strings.TrimSpace(model.Str(d.DeptName)) == "":
		return "部门名称不能为空"
	case len([]rune(model.Str(d.DeptName))) > 30:
		return "部门名称长度不能超过30个字符"
	case strings.TrimSpace(model.Str(d.OrderNum)) == "":
		return "显示顺序不能为空"
	case len([]rune(model.Str(d.Phone))) > 11:
		return "联系电话长度不能超过11个字符"
	case len([]rune(model.Str(d.Email))) > 50:
		return "邮箱长度不能超过50个字符"
	}
	return ""
}

// checkDeptNameUnique 对应 SysDeptServiceImpl.checkDeptNameUnique（deptId 为空按 -1 处理）。
func (h *deptHandler) checkDeptNameUnique(c *gin.Context, d *model.SysDept) (string, error) {
	info, err := h.svc.checkDeptNameUnique(c.Request.Context(), model.Str(d.DeptName), model.Int64Val(d.ParentID))
	if err != nil {
		return "", err
	}
	if info != nil && info.DeptID != d.DeptID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// List 对应 SysDeptController.list（分页参数被忽略：Java 未调用 startPage）。
func (h *deptHandler) List(c *gin.Context) {
	rows, err := h.svc.selectDeptList(c.Request.Context(), parseDeptQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// GetList 对应 SysDeptController.getList（无权限点）。
func (h *deptHandler) GetList(c *gin.Context) {
	rows, err := h.svc.selectDeptList(c.Request.Context(), parseDeptQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// ExcludeChild 对应 SysDeptController.excludeChild：剔除自身及所有后代节点。
func (h *deptHandler) ExcludeChild(c *gin.Context) {
	deptID, err := parseLongParam("deptId", c.Param("deptId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.selectDeptList(c.Request.Context(), deptQuery{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	target := strconv.FormatInt(deptID, 10)
	out := make([]model.SysDept, 0, len(rows))
	for _, d := range rows {
		if d.DeptID == deptID {
			continue
		}
		skip := false
		for _, a := range strings.Split(model.Str(d.Ancestors), ",") {
			if strings.TrimSpace(a) == target {
				skip = true
				break
			}
		}
		if !skip {
			out = append(out, d)
		}
	}
	web.JSON(c, web.SuccessData(out))
}

// GetInfo 对应 SysDeptController.getInfo。
func (h *deptHandler) GetInfo(c *gin.Context) {
	id, err := parseLongParam("deptId", c.Param("deptId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	dept, err := h.svc.selectDeptByID(c.Request.Context(), id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(dept))
}

// TreeSelect 对应 SysDeptController.treeselect。
func (h *deptHandler) TreeSelect(c *gin.Context) {
	rows, err := h.svc.selectDeptList(c.Request.Context(), parseDeptQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(buildDeptTreeSelect(rows)))
}

// TreeSelectNew 对应 SysDeptController.treeselectNew：按 flag 追加过滤条件。
func (h *deptHandler) TreeSelectNew(c *gin.Context) {
	q := parseDeptQuery(c)
	switch q.Flag {
	case "myDept", "myDeptCg":
		v := currentTenantID(c)
		q.TenantID = &v
	case "sjzbDept", "sjzbDeptCg":
		q.DataID = strconv.FormatInt(currentTenantID(c), 10)
	case "isUint":
		q.IsUint = "1"
	case "allDept":
		// 不追加条件
	case "onlyMyDept":
		v := currentDeptID(c)
		q.DeptID = &v
	default:
		v := int64(-1)
		q.DeptID = &v
	}
	rows, err := h.svc.selectDeptList(c.Request.Context(), q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(buildDeptTreeSelect(rows)))
}

// RoleDeptTreeSelect 对应 SysDeptController.roleDeptTreeselect。
func (h *deptHandler) RoleDeptTreeSelect(c *gin.Context) {
	roleID, err := parseLongParam("roleId", c.Param("roleId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	role, err := h.svc.selectRoleByID(ctx, roleID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	strict := role != nil && role.DeptCheckStrictly
	checked, err := h.svc.selectDeptListByRoleID(ctx, roleID, strict)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.selectDeptList(ctx, deptQuery{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ajax := web.Success()
	ajax.Put("checkedKeys", checked)
	ajax.Put("depts", buildDeptTreeSelect(rows))
	web.JSON(c, ajax)
}

// Add 对应 SysDeptController.add。
func (h *deptHandler) Add(c *gin.Context) {
	var body model.SysDept
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := validateDept(&body); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	res, err := h.checkDeptNameUnique(c, &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增部门'%s'失败，部门名称已存在", model.Str(body.DeptName))))
		return
	}
	body.CreateBy = model.Ptr(auth.CurrentUsername(c))
	rows, err := h.svc.insertDept(ctx, &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysDeptController.edit。
func (h *deptHandler) Edit(c *gin.Context) {
	var body model.SysDept
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := validateDept(&body); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	res, err := h.checkDeptNameUnique(c, &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改部门'%s'失败，部门名称已存在", model.Str(body.DeptName))))
		return
	}
	if model.Int64Val(body.ParentID) != 0 && model.Int64Val(body.ParentID) == body.DeptID {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改部门'%s'失败，上级部门不能是自己", model.Str(body.DeptName))))
		return
	}
	if model.Str(body.Status) == deptDisable {
		n, err := h.svc.selectNormalChildrenDeptByID(ctx, body.DeptID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if n > 0 {
			web.JSON(c, web.ErrorMsg("该部门包含未停用的子部门！"))
			return
		}
	}
	body.UpdateBy = model.Ptr(auth.CurrentUsername(c))
	rows, err := h.svc.updateDept(ctx, &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysDeptController.remove。
func (h *deptHandler) Remove(c *gin.Context) {
	id, err := parseLongParam("deptId", c.Param("deptId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	hasChild, err := h.svc.hasChildByDeptID(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if hasChild {
		web.JSON(c, web.ErrorMsg("存在下级部门,不允许删除"))
		return
	}
	hasUser, err := h.svc.checkDeptExistUser(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if hasUser {
		web.JSON(c, web.ErrorMsg("部门存在用户,不允许删除"))
		return
	}
	rows, err := h.svc.deleteDeptByID(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// GetCompanyList 对应 SysDeptController.getCompanyList（只查单位）。
func (h *deptHandler) GetCompanyList(c *gin.Context) {
	rows, err := h.svc.selectDeptList(c.Request.Context(), deptQuery{IsUint: "1"})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

func registerDept(reg *router.Registry, svc *service) {
	h := newDeptHandler(reg.App, svc)
	g := reg.Authed.Group("/system/dept")

	g.GET("/list", middleware.Perm("system:dept:list"), h.List)
	g.GET("/getList", h.GetList)
	g.GET("/list/exclude/:deptId", middleware.Perm("system:dept:list"), h.ExcludeChild)
	g.GET("/treeselect", h.TreeSelect)
	g.GET("/treeselectNew", h.TreeSelectNew)
	g.GET("/roleDeptTreeselect/:roleId", h.RoleDeptTreeSelect)
	g.GET("/getCompanyList", h.GetCompanyList)
	g.GET("/:deptId", middleware.Perm("system:dept:query"), h.GetInfo)
	g.POST("", middleware.Perm("system:dept:add"),
		middleware.OperLog(reg.App, "部门管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:dept:edit"),
		middleware.OperLog(reg.App, "部门管理", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:deptId", middleware.Perm("system:dept:remove"),
		middleware.OperLog(reg.App, "部门管理", middleware.BusinessDelete), h.Remove)
}
