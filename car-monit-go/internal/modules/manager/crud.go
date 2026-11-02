// JAVA 对照: ruoyi-generator 模板生成的 <Table>Controller.java（manager 包 13 组标准 CRUD）
// 类/职责: manager 标准控制器的通用 list/get/save/delete 实现
// 对应 Go 文件: internal/modules/manager/crud.go
//
// DIFF: Java 每个控制器重复一份模板代码；Go 用 tableSpec 声明表/列/条件，处理器共享。
// DIFF: PageHelper 隐式分页 -> 这里显式 COUNT + LIMIT/OFFSET（见 support.go 的 list）。
package manager

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// tableSpec 描述一张 manager 表的列表/详情/写入行为。
type tableSpec struct {
	table        string
	selectSQL    string
	fromSQL      string
	wherePrefix  string
	selectSuffix string
	detailSuffix string
	detailFrom   string
	orderBy      string
	conditions   []cond
	columns      map[string]string
	prototype    any

	// afterChange 对应 Service 里 save/delete 之后的 cacheXxx()。
	afterChange func(h *handler, c *gin.Context)
	// afterScan 在列表/详情扫描完成后补齐 Java 的字段默认值。
	// 例：CarExceptRecord.supplementaryStatus 是 Java 字段初始化值 "0"，
	// 而 XML 的 select 语句根本没查这一列，MyBatis 不会覆盖它，JSON 里始终是 "0"。
	afterScan func(dest any)
	// prepareInsert 用于补 Java Service 在新增时的默认值（status/delFlag 等）。
	prepareInsert func(c *gin.Context, body map[string]any, cols map[string]any)
	// prepareUpdate 用于修改时的额外列。
	prepareUpdate func(c *gin.Context, body map[string]any, cols map[string]any)
}

func (s *tableSpec) from() string {
	from := s.fromSQL
	if from == "" {
		from = s.table + " t"
	}
	return "FROM " + from + " "
}

func (s *tableSpec) prefix() string {
	if s.wherePrefix != "" {
		return s.wherePrefix
	}
	return "WHERE t.del_flag = '0'"
}

// tableList 对应 GET /list。
func (h *handler) tableList(c *gin.Context, spec *tableSpec) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	h.respondList(c, spec, clause, args)
}

// respondList 执行列表查询并输出 TableDataInfo。
//
// JAVA 对照: 控制器 list 一律先 startPage()（TableSupport 默认 pageNum=1、pageSize=10），
// 不带分页参数时同样只返回一页，故用 PageAlways；导出接口不走这里（Java 导出不分页）。
func (h *handler) respondList(c *gin.Context, spec *tableSpec, clause string, args []any) {
	dest := newSliceOf(spec.prototype)
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: spec.selectSQL + spec.selectSuffix,
		FromSQL:   spec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   spec.orderBy,
		Page:      web.PageAlways(c),
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if spec.afterScan != nil {
		spec.afterScan(dest)
	}
	web.JSON(c, web.Table(dest, total))
}

// tableGet 对应 GET /{id} —— 详情语句不带 del_flag（与 XML 一致）。
func (h *handler) tableGet(c *gin.Context, spec *tableSpec) {
	from := spec.detailFrom
	if from == "" {
		from = spec.from()
	}
	sqlStr := "SELECT " + spec.selectSQL + spec.detailSuffix + " " + from + "WHERE t.id = ?"
	dest := newElemOf(spec.prototype)
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, c.Param("id")).Scan(dest)
	if tx.Error != nil {
		web.JSON(c, web.ErrorResult(tx.Error))
		return
	}
	if tx.RowsAffected == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	if spec.afterScan != nil {
		spec.afterScan(dest)
	}
	web.JSON(c, web.SuccessData(dest))
}

// tableSave 对应 POST / PUT —— 新增与修改共用一个入口（id 非空即修改）。
func (h *handler) tableSave(c *gin.Context, spec *tableSpec) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	id := bodyString(body, "id")
	cols := pickColumns(body, spec.columns)
	if id != "" {
		if spec.prepareUpdate != nil {
			spec.prepareUpdate(c, body, cols)
		}
		withUpdateAudit(c, cols)
		if _, err := h.updateRow(c.Request.Context(), spec.table, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		if spec.prepareInsert != nil {
			spec.prepareInsert(c, body, cols)
		}
		id = newUUID()
		cols["id"] = id
		h.withInsertAudit(c, cols)
		if err := h.insertRow(c.Request.Context(), spec.table, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	if spec.afterChange != nil {
		spec.afterChange(h, c)
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// tableDelete 对应 DELETE /{ids} —— 逻辑删除，返回受影响行数。
func (h *handler) tableDelete(c *gin.Context, spec *tableSpec) {
	ids := splitCSV(c.Param("ids"))
	if len(ids) == 0 {
		web.JSON(c, web.ErrorResult(web.NewServiceError("参数错误")))
		return
	}
	count, err := h.softDeleteByIDs(c.Request.Context(), spec.table, ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if spec.afterChange != nil {
		spec.afterChange(h, c)
	}
	web.JSON(c, web.SuccessData(count))
}

// bodyString 读取请求体里的字符串字段（null/缺失 -> ""）。
func bodyString(body map[string]any, key string) string {
	v, ok := body[key]
	if !ok || v == nil {
		return ""
	}
	switch x := v.(type) {
	case string:
		return strings.TrimSpace(x)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return strings.TrimSpace(fmt.Sprint(x))
	}
}

// exportResult 构造 EasyPOI / ExcelUtil 两种输出形态。
//
// DIFF: Java EasyPOI 的模板导出（TemplateExportParams）会直接写出附件流并返回 null；
// ExcelUtil 导出则把文件写进 profile/download 并把文件名放进 msg。这里两种都实现：
// envelope=true 时走后者，否则以附件流返回。
func (h *handler) exportResult(c *gin.Context, data []byte, sheet string, envelope bool) {
	if envelope {
		// JAVA 对照: ExcelUtil.encodingFilename() -> UUID.randomUUID() + "_" + sheetName + ".xlsx"
		fileName := newUUIDDashed() + "_" + sheet + ".xlsx"
		path := h.app.Cfg.RuoYi.DownloadPath() + fileName
		if err := writeFile(path, data); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		web.JSON(c, web.SuccessMsg(fileName))
		return
	}
	c.Header("Content-Type", "application/octet-stream;charset=UTF-8")
	c.Header("Content-Disposition", "attachment; filename="+sheet)
	c.Data(http.StatusOK, "application/octet-stream", data)
}
