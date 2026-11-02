// JAVA 对照: ruoyi-generator 模板生成的 <Table>Controller.java + <Table>ServiceImpl.java
// 类/职责: base 标准控制器的通用 list/get/save/delete 实现
// 对应 Go 文件: internal/modules/base/crud.go
//
// DIFF: Java 每个控制器重复一份模板代码；Go 用 tableSpec 声明表/列/条件/主键，处理器共享。
// DIFF: PageHelper 隐式分页 -> 这里显式 COUNT + LIMIT/OFFSET（见 support.go 的 list）。
// DIFF: MyBatis-Plus 的 insert/updateById 只写非 null 字段；这里用「请求体里出现过」代替。
package base

import (
	"net/http"
	"reflect"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

type pkKind int

const (
	pkString pkKind = iota
	pkInteger
)

// tableSpec 描述一张 base 表的列表/详情/写入行为。
type tableSpec struct {
	table       string
	selectSQL   string
	fromSQL     string
	wherePrefix string
	orderBy     string
	conditions  []cond
	prototype   any

	// pk 是 @TableId 列名；detailPK 是 selectXxxById 的过滤列（默认同 pk）。
	pk       string
	detailPK string
	pkKind   pkKind

	// physicalDelete=true 对应 XML 里的 delete from（base_config_service_area / car_warning_config）。
	physicalDelete bool

	// assignUUID 对应 @TableId(type = IdType.ASSIGN_UUID)。
	assignUUID bool
	// audit=true 对应实体继承 BasePlusEntity（自动填充审计列）。
	audit bool
	// readOnly 是「不属于本表」的 JSON 键（join 出来的列），写入时排除。
	readOnly map[string]bool

	// afterChange 对应 Service 里 save/delete 之后的缓存刷新。
	afterChange func(h *handler, c *gin.Context)
}

func (s *tableSpec) from() string {
	from := s.fromSQL
	if from == "" {
		from = s.table + " t"
	}
	return from
}

func (s *tableSpec) prefix() string {
	if s.wherePrefix != "" {
		return s.wherePrefix
	}
	return "WHERE 1=1"
}

// detailColumn 返回详情语句的过滤列。
func (s *tableSpec) detailColumn() string {
	if s.detailPK != "" {
		return s.detailPK
	}
	return s.pk
}

// writeColumns 返回「JSON 键 -> 列名」映射（由实体标签反射得到，再剔除 join 列）。
// JAVA 对照: MyBatis-Plus 的实体列映射（@TableField）
func (s *tableSpec) writeColumns() map[string]string {
	cols := structFields(reflectTypeOf(s.prototype))
	for key := range s.readOnly {
		delete(cols, key)
	}
	return cols
}

// pkJSON 返回主键在 JSON 里的键名（id / fwqbm / big_id -> bigId / agent_pk -> agentPk）。
func (s *tableSpec) pkJSON() string {
	cols := structFields(reflectTypeOf(s.prototype))
	for key, column := range cols {
		if column == s.pk {
			return key
		}
	}
	return "id"
}

// tableList 对应 GET /list。
// JAVA 对照: 各控制器 list（startPage + selectXxxList）
func (h *handler) tableList(c *gin.Context, spec *tableSpec) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	h.respondList(c, spec, clause, args)
}

// respondList 执行列表查询并输出 TableDataInfo。
//
// JAVA 对照: 这些 list 方法都先 startPage()，TableSupport 对缺省参数取 1/10，
// 所以不带分页参数时也必须只返回一页 —— 用 PageAlways 而不是 Page。
func (h *handler) respondList(c *gin.Context, spec *tableSpec, clause string, args []any) {
	dest := newSliceOf(spec.prototype)
	page := web.PageAlways(c)
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: spec.selectSQL,
		FromSQL:   "FROM " + spec.from() + " ",
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderByFor(spec, page),
		Page:      page,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(nonNilSlice(dest), total))
}

// nonNilSlice 把 nil 切片替换成空切片（Jackson 对空 List 输出 []，不会输出 null）。
func nonNilSlice(dest any) any {
	v := reflect.ValueOf(dest)
	if v.Kind() == reflect.Ptr && !v.IsNil() && v.Elem().Kind() == reflect.Slice && v.Elem().IsNil() {
		return reflect.MakeSlice(v.Elem().Type(), 0, 0).Interface()
	}
	return dest
}

// orderByFor 复刻 PageHelper：语句本身没有 order by 时才追加客户端排序。
func orderByFor(spec *tableSpec, page web.PageDomain) string {
	if spec.orderBy != "" {
		return spec.orderBy
	}
	return page.OrderBy()
}

// tableGet 对应 GET /{pk} —— 详情语句不带 del_flag（与 XML 一致）。
func (h *handler) tableGet(c *gin.Context, spec *tableSpec) {
	h.getByID(c, spec, c.Param("id"))
}

// getByID 按给定主键取一行。
func (h *handler) getByID(c *gin.Context, spec *tableSpec, id string) {
	sqlStr := "SELECT " + spec.selectSQL + " FROM " + spec.from() +
		" WHERE t." + spec.detailColumn() + " = ?"
	dest := newElemOf(spec.prototype)
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, id).Scan(dest)
	if tx.Error != nil {
		web.JSON(c, web.ErrorResult(tx.Error))
		return
	}
	if tx.RowsAffected == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(dest))
}

// tableSave 对应 POST / PUT —— 新增与修改共用一个入口。
func (h *handler) tableSave(c *gin.Context, spec *tableSpec) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	cols := pickColumns(body, spec.writeColumns())
	ctx := c.Request.Context()
	pkKey := spec.pkJSON()

	if spec.pkKind == pkInteger {
		// JAVA 对照: GeometryServiceImpl#saveGeometry —— null != id 即修改（0 也算有值）。
		id := bodyInt(body, pkKey)
		delete(cols, spec.pk)
		if id != nil {
			if len(cols) > 0 {
				if err := h.app.DB.WithContext(ctx).Table(spec.table).
					Where(spec.pk+" = ?", *id).Updates(cols).Error; err != nil {
					web.JSON(c, web.ErrorResult(err))
					return
				}
			}
		} else if err := h.app.DB.WithContext(ctx).Table(spec.table).Create(cols).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if spec.afterChange != nil {
			spec.afterChange(h, c)
		}
		// JAVA 对照: AjaxResult.success(msg, data) 在 data 为 null 时不带 data 键。
		var result any
		if id != nil {
			result = *id
		}
		web.JSON(c, web.SuccessFull("操作成功！", result))
		return
	}

	id := bodyString(body, pkKey)
	if isNotBlank(id) {
		// JAVA 对照: updateFill 只对 BasePlusEntity 生效（其他表没有 update_time/update_by 列）。
		if spec.audit {
			updateAudit(c, cols)
		}
		delete(cols, spec.pk)
		if len(cols) > 0 {
			if err := h.app.DB.WithContext(ctx).Table(spec.table).
				Where(spec.pk+" = ?", id).Updates(cols).Error; err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
		}
	} else {
		switch {
		case spec.assignUUID:
			// JAVA 对照: @TableId(type = IdType.ASSIGN_UUID)
			id = newUUID()
			cols[spec.pk] = id
		case spec.audit:
			// JAVA 对照: BasePlusEntity.id + 全局 id-type: ASSIGN_ID（19 位雪花号字符串）
			id = nextSnowflakeID()
			cols[spec.pk] = id
		default:
			delete(cols, spec.pk)
		}
		if spec.audit {
			h.insertAudit(c, cols)
		}
		if err := h.app.DB.WithContext(ctx).Table(spec.table).Create(cols).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	if spec.afterChange != nil {
		spec.afterChange(h, c)
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// tableDelete 对应 DELETE /{ids} —— XML 里是逻辑删（update set del_flag='1'）或物理删。
func (h *handler) tableDelete(c *gin.Context, spec *tableSpec) {
	ids := splitCSV(c.Param("ids"))
	if len(ids) == 0 {
		web.JSON(c, web.ErrorResult(web.NewServiceError("参数错误")))
		return
	}
	var count int64
	var err error
	if spec.physicalDelete {
		tx := h.app.DB.WithContext(c.Request.Context()).Exec(
			"DELETE FROM "+spec.table+" WHERE "+spec.pk+" IN ("+placeholders(len(ids))+")", anySlice(ids)...)
		count, err = tx.RowsAffected, tx.Error
	} else {
		// JAVA 对照: update t set del_flag='1' where id in (...) —— 没有 del_flag='0' 守卫。
		tx := h.app.DB.WithContext(c.Request.Context()).Exec(
			"UPDATE "+spec.table+" SET del_flag = '1' WHERE "+spec.pk+" IN ("+placeholders(len(ids))+")",
			anySlice(ids)...)
		count, err = tx.RowsAffected, tx.Error
	}
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if spec.afterChange != nil {
		spec.afterChange(h, c)
	}
	web.JSON(c, web.SuccessData(count))
}

// anySlice 把 []string 转成 []any（GORM 的 IN 参数）。
func anySlice(values []string) []any {
	out := make([]any, len(values))
	for i, v := range values {
		out[i] = v
	}
	return out
}

// exportResult 构造 EasyPOI / ExcelUtil 两种输出形态。
//
// DIFF: Java EasyPOI 模板导出直接写附件流并 return null（Content-Disposition 只有 "attachment"）；
// ExcelUtil 导出把文件写进 profile/download 并把文件名放进 msg。
func (h *handler) exportResult(c *gin.Context, data []byte, fileName string, envelope bool) {
	if envelope {
		path := h.app.Cfg.RuoYi.DownloadPath() + fileName
		if err := writeFile(path, data); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		web.JSON(c, web.SuccessMsg(fileName))
		return
	}
	c.Header("Content-Type", "application/octet-stream;charset=UTF-8")
	c.Header("Content-Disposition", "attachment")
	c.Data(http.StatusOK, "application/octet-stream", data)
}
