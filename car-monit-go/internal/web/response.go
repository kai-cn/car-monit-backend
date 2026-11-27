// JAVA 对照: com/ruoyi/common/core/domain/AjaxResult.java
// JAVA 对照: com/ruoyi/common/core/page/TableDataInfo.java
// JAVA 对照: com/ruoyi/common/core/domain/R.java
// 类/职责: HTTP 响应信封 — Java 的 AjaxResult / TableDataInfo / R
// 对应 Go 文件: internal/web/response.go
// 关键映射: AjaxResult extends HashMap -> JavaMap；TableDataInfo/R -> 普通 struct（字段声明序）
package web

import (
	"encoding/json"
	"net/http"
	"reflect"

	"github.com/gin-gonic/gin"
)

// HttpStatus 对应 com.ruoyi.common.constant.HttpStatus。
const (
	StatusSuccess            = 200
	StatusCreated            = 201
	StatusNoContent          = 204
	StatusMovedPermanently   = 301
	StatusFound              = 302
	StatusSeeOther           = 303
	StatusNotModified        = 304
	StatusTemporaryRedirect  = 307
	StatusBadRequest         = 400
	StatusUnauthorized       = 401
	StatusForbidden          = 403
	StatusNotFound           = 404
	StatusBadMethod          = 405
	StatusTimeout            = 408
	StatusConflict           = 409
	StatusUnsupportedType    = 415
	StatusInternalError      = 500
	StatusNotImplemented     = 501
	StatusBadGateway         = 502
	StatusServiceUnavailable = 503
	StatusGatewayTimeout     = 504
	StatusWarn               = 601
)

const (
	TagCode = "code"
	TagMsg  = "msg"
	TagData = "data"
)

// AjaxResult 对应 Java 的 AjaxResult extends HashMap<String,Object>。
type AjaxResult struct{ *JavaMap }

func NewAjaxResult() *AjaxResult { return &AjaxResult{NewJavaMap()} }

func (a *AjaxResult) Put(key string, value any) *AjaxResult {
	a.JavaMap.Put(key, value)
	return a
}

func (a *AjaxResult) MarshalJSON() ([]byte, error) { return a.JavaMap.MarshalJSON() }

// AJ 构造带 code/msg 的 AjaxResult。
//
// JAVA 对照: AjaxResult 构造函数里是 `if (data != null) super.put(TAG_DATA, data)`，
// 所以 data 为 null（含类型化空指针/空切片）时不输出 data 键。
func AJ(code int, msg string, data any) *AjaxResult {
	r := NewAjaxResult()
	r.Put(TagCode, code)
	r.Put(TagMsg, msg)
	if !IsNilValue(data) {
		r.Put(TagData, data)
	}
	return r
}

// IsNilValue 判断 any 是否为 nil、类型化空指针或空切片/空 map。
func IsNilValue(v any) bool {
	if v == nil {
		return true
	}
	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Pointer, reflect.Map, reflect.Slice, reflect.Interface:
		return rv.IsNil()
	}
	return false
}

func Success() *AjaxResult              { return SuccessMsg("操作成功") }
func SuccessData(data any) *AjaxResult  { return SuccessFull("操作成功", data) }
func SuccessMsg(msg string) *AjaxResult { return SuccessFull(msg, nil) }
func SuccessFull(msg string, data any) *AjaxResult {
	return AJ(StatusSuccess, msg, data)
}

func Warn(msg string) *AjaxResult               { return WarnData(msg, nil) }
func WarnData(msg string, data any) *AjaxResult { return AJ(StatusWarn, msg, data) }

func Error() *AjaxResult                         { return ErrorMsg("操作失败") }
func ErrorMsg(msg string) *AjaxResult            { return ErrorData(msg, nil) }
func ErrorData(msg string, data any) *AjaxResult { return AJ(StatusInternalError, msg, data) }
func ErrorCode(code int, msg string) *AjaxResult { return AJ(code, msg, nil) }

// ErrorNilMsg 对应 Java 的 AjaxResult.error(e.getMessage()) 且 message 为 null
// （未捕获的 NullPointerException 走 GlobalExceptionHandler，msg 键存在但值是 null）。
func ErrorNilMsg() *AjaxResult {
	r := NewAjaxResult()
	r.Put(TagCode, StatusInternalError)
	r.Put(TagMsg, nil)
	return r
}

// ToAjax 对应 BaseController.toAjax(int rows)。
func ToAjax(rows int64) *AjaxResult {
	if rows > 0 {
		return Success()
	}
	return Error()
}

// TableDataInfo 对应 com.ruoyi.common.core.page.TableDataInfo（字段顺序 total,rows,code,msg）。
type TableDataInfo struct {
	Total int64  `json:"total"`
	Rows  any    `json:"rows"`
	Code  int    `json:"code"`
	Msg   string `json:"msg"`
}

// Table 对应 BaseController.getDataTable(list)：code=200,msg=查询成功。
//
// JAVA 对照: getDataTable 用 `new PageInfo(list).getList()`，MyBatis 空结果集是空列表，
// 因此 rows 永远是 []（不是 null）。Go 侧扫描无行时切片为 nil，这里统一成空切片。
func Table(rows any, total int64) *TableDataInfo {
	return &TableDataInfo{Total: total, Rows: nonNilRows(rows), Code: StatusSuccess, Msg: "查询成功"}
}

// nonNilRows 把 *[]T(nil) / nil 切片换成同类型的空切片，保证 JSON 里是 [] 而不是 null。
func nonNilRows(rows any) any {
	if rows == nil {
		return []any{}
	}
	rv := reflect.ValueOf(rows)
	if rv.Kind() == reflect.Pointer && !rv.IsNil() && rv.Elem().Kind() == reflect.Slice && rv.Elem().IsNil() {
		return reflect.MakeSlice(rv.Elem().Type(), 0, 0).Interface()
	}
	if rv.Kind() == reflect.Slice && rv.IsNil() {
		return reflect.MakeSlice(rv.Type(), 0, 0).Interface()
	}
	return rows
}

// R 对应 com.ruoyi.common.core.domain.R<T>（字段顺序 code,msg,data）。
type R struct {
	Code int    `json:"code"`
	Msg  string `json:"msg"`
	Data any    `json:"data"`
}

func ROK(data any) *R                { return &R{Code: StatusSuccess, Msg: "操作成功", Data: data} }
func ROKMsg(data any, msg string) *R { return &R{Code: StatusSuccess, Msg: msg, Data: data} }
func RFail() *R                      { return &R{Code: StatusInternalError, Msg: "操作失败"} }
func RFailMsg(msg string) *R         { return &R{Code: StatusInternalError, Msg: msg} }

// JSON 以 HTTP 200 输出业务信封（RuoYi 前端约定：业务错误也走 200 + code）。
func JSON(c *gin.Context, body any) {
	c.JSON(http.StatusOK, body)
}

// JSONStatus 需要非 200 HTTP 状态时使用。
func JSONStatus(c *gin.Context, status int, body any) {
	c.JSON(status, body)
}

// RenderString 对应 ServletUtils.renderString。
func RenderString(c *gin.Context, body any) {
	c.JSON(http.StatusOK, body)
}

// Raw 直接序列化任意值，便于 JavaMap 与普通 struct 混用。
func Raw(v any) (json.RawMessage, error) {
	b, err := json.Marshal(v)
	return json.RawMessage(b), err
}
