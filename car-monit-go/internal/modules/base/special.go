// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java
// 类/职责: 门架 / 收费站列表的关联名称回填与门架模板导出
// 对应 Go 文件: internal/modules/base/special.go
package base

import (
	"context"
	"net/http"
	"reflect"
	"sort"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// gantryList 对应 GET /base/gantry/list：用 redis section_list 回填 roadName/sectionName。
func (h *handler) gantryList(c *gin.Context) {
	clause, args := buildWhere(c, gantrySpec.prefix(), gantrySpec.conditions)
	page := web.PageAlways(c)
	dest := newSliceOf(&odsSzdnGantry{})
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: gantrySpec.selectSQL,
		FromSQL:   "FROM " + gantrySpec.from() + " ",
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderByFor(gantrySpec, page),
		Page:      page,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	sections := h.loadSectionList(c.Request.Context())
	roadMap, sectionMap := roadNameMap(sections), sectionNameMap(sections)
	for _, gantry := range *(dest.(*[]*odsSzdnGantry)) {
		gantry.RoadName = strPtr(roadMap[strOf(gantry.RoadCode)])
		gantry.SectionName = strPtr(sectionMap[strOf(gantry.SectionCode)])
	}
	web.JSON(c, web.Table(dest, total))
}

// gantryListAll 对应 GET /base/gantry/listAll：选择门架弹窗，不做名称回填。
func (h *handler) gantryListAll(c *gin.Context) {
	h.tableList(c, gantrySpec)
}

// tollList 对应 GET /base/toll/list：用 redis section_list 回填 sectionName。
//
// JAVA 对照: 控制器里还算了 roadMap，但没用上（照抄：不输出 roadName）。
func (h *handler) tollList(c *gin.Context) {
	clause, args := buildWhere(c, tollSpec.prefix(), tollSpec.conditions)
	page := web.PageAlways(c)
	dest := newSliceOf(&odsSzdnToll{})
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: tollSpec.selectSQL,
		FromSQL:   "FROM " + tollSpec.from() + " ",
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderByFor(tollSpec, page),
		Page:      page,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	sectionMap := sectionNameMap(h.loadSectionList(c.Request.Context()))
	for _, toll := range *(dest.(*[]*odsSzdnToll)) {
		toll.SectionName = strPtr(sectionMap[strOf(toll.SectionCode)])
	}
	web.JSON(c, web.Table(dest, total))
}

// tollListAll 对应 GET /base/toll/listAll：弹出窗口，不做名称回填。
func (h *handler) tollListAll(c *gin.Context) {
	h.tableList(c, tollSpec)
}

// gantryExportCols 是 EasyPOI 模板 templates/export/gantry.xlsx 的列定义。
func gantryExportCols() []exportCol {
	return []exportCol{
		{Title: "所属管理中心编号", Field: "orgCode"},
		{Title: "所属管理中心名称", Field: "orgName"},
		{Title: "所属路线编号", Field: "roadCode"},
		{Title: "所属路线名称", Field: "roadName"},
		{Title: "所属路段编码", Field: "sectionCode"},
		{Title: "所属路段名称", Field: "sectionName"},
		{Title: "收费站编号", Field: "tollCode"},
		{Title: "收费站名称", Field: "tollName"},
		{Title: "门架编号", Field: "gantryCode"},
		{Title: "门架名称", Field: "gantryName"},
		{Title: "边界门架类型", Field: "boundaryGantryType"},
		{Title: "是否虚门架", Field: "isVirtual"},
		{Title: "是否有交易流水", Field: "isData"},
	}
}

// gantryExport 对应 GET /base/gantry/export（EasyPOI 模板导出）。
func (h *handler) gantryExport(c *gin.Context) {
	ctx := c.Request.Context()
	list := h.loadGantryCache(ctx)
	if len(list) == 0 {
		// JAVA 对照: 列表为空时 Java 直接 return null（响应体为 null）。
		c.JSON(http.StatusOK, nil)
		return
	}
	sections := h.loadSectionList(ctx)
	roadMap, sectionMap := roadNameMap(sections), sectionNameMap(sections)
	tollMap := h.codeNameMap(ctx, "ods_szdn_toll", "toll_code", "toll_name")
	orgMap := h.codeNameMap(ctx, "ods_yhgl_v_base_org", "org_code", "org_name")

	for _, gantry := range list {
		gantry.RoadName = strPtr(roadMap[strOf(gantry.RoadCode)])
		gantry.SectionName = strPtr(sectionMap[strOf(gantry.SectionCode)])
		gantry.TollName = strPtr(tollMap[strOf(gantry.TollCode)])
		gantry.OrgName = strPtr(orgMap[strOf(gantry.OrgCode)])
		if strOf(gantry.BoundaryGantryType) == "0" {
			gantry.BoundaryGantryType = strPtr("边界入口门架")
		} else {
			gantry.BoundaryGantryType = strPtr("边界出口门架")
		}
		if strOf(gantry.IsVirtual) == "0" {
			gantry.IsVirtual = strPtr("否")
		} else {
			gantry.IsVirtual = strPtr("是")
		}
		gantry.IsData = strPtr("否")
		if h.gantryDataFlag(ctx, strOf(gantry.GantryCode)) {
			gantry.IsData = strPtr("是")
		}
	}
	sort.SliceStable(list, func(i, j int) bool {
		a, b := list[i], list[j]
		if strOf(a.OrgCode) != strOf(b.OrgCode) {
			return strOf(a.OrgCode) < strOf(b.OrgCode)
		}
		if strOf(a.RoadCode) != strOf(b.RoadCode) {
			return strOf(a.RoadCode) < strOf(b.RoadCode)
		}
		if strOf(a.SectionCode) != strOf(b.SectionCode) {
			return strOf(a.SectionCode) < strOf(b.SectionCode)
		}
		if strOf(a.TollCode) != strOf(b.TollCode) {
			return strOf(a.TollCode) < strOf(b.TollCode)
		}
		return strOf(a.GantryCode) < strOf(b.GantryCode)
	})

	cols := gantryExportCols()
	index := jsonTagIndex(reflectTypeOf(&odsSzdnGantry{}))
	rows := make([][]any, 0, len(list))
	for _, gantry := range list {
		row := make([]any, len(cols))
		for i, col := range cols {
			row[i] = plainValue(fieldValue(reflect.ValueOf(gantry), index, col.Field), col.DateOnly)
		}
		rows = append(rows, row)
	}
	h.templateExport(c, "门架信息数据", cols, rows)
}

// codeNameMap 对应 tollService.list()/baseOrgService.list() 后的 toMap(code, name)。
//
// DIFF: Java 用 Collectors.toMap，重复 key 会抛 IllegalStateException；这里取第一条（不报错）。
func (h *handler) codeNameMap(ctx context.Context, table, codeColumn, nameColumn string) map[string]string {
	type codeName struct {
		Code string `gorm:"column:code"`
		Name string `gorm:"column:name"`
	}
	var rows []codeName
	err := h.app.DB.WithContext(ctx).Table(table).
		Select(codeColumn + " AS code, " + nameColumn + " AS name").
		Scan(&rows).Error
	if err != nil {
		h.app.Log.Warn("加载编码名称映射失败", "table", table, "err", err)
		return map[string]string{}
	}
	m := make(map[string]string, len(rows))
	for _, row := range rows {
		if _, ok := m[row.Code]; !ok {
			m[row.Code] = row.Name
		}
	}
	return m
}
