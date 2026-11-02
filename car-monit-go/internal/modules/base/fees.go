// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/Http*.java（Forest 声明式 HTTP 客户端）
// 类/职责: 门架交易 / 收费流水 / 出口流水的转发查询与流水导出
// 对应 Go 文件: internal/modules/base/fees.go
//
// DIFF: 这四个端点（feeGantry、feerecords、feestationexit、snapshotflow 的 {bigId}/earliest-time）
// 在 Java 里由 Forest 客户端转发到 vehicleMonitor.baseUrl（另一套采集服务），本仓库没有它的实现。
// Go 用 net/http 转发到同一 baseUrl、同一路径，参数按 camelCase 原样透传；
// 不自行查库，避免凭空产生与原服务不同的数据语义。
package base

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// queryParams 对应 @Query 传实体：把请求参数摊平（多值以逗号连接）。
func queryParams(c *gin.Context) map[string]string {
	out := make(map[string]string)
	for key, values := range c.Request.URL.Query() {
		if len(values) == 0 {
			continue
		}
		out[key] = strings.Join(values, ",")
	}
	return out
}

// forestGet 对应 Forest 的 @Get：GET baseUrl+path，返回解析后的 JSON。
//
// DIFF: Forest 的 BackOffRetryer（重试 2 次）未实现；超时取 forest.timeout（毫秒）。
func (h *handler) forestGet(ctx context.Context, path string, params map[string]string) (any, error) {
	baseURL := strings.TrimRight(h.app.Cfg.VehicleMonitor.BaseURL, "/")
	target := baseURL + "/" + strings.TrimLeft(path, "/")
	query := url.Values{}
	for key, value := range params {
		query.Set(key, value)
	}
	if encoded := query.Encode(); encoded != "" {
		target += "?" + encoded
	}
	timeout := h.app.Cfg.Forest.Timeout
	if timeout <= 0 {
		timeout = 60000
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return nil, web.NewServiceError("请求车辆监测服务失败: %v", err)
	}
	req.Header.Set("Connection", "close")
	client := &http.Client{Timeout: time.Duration(timeout) * time.Millisecond}
	resp, err := client.Do(req)
	if err != nil {
		return nil, web.NewServiceError("请求车辆监测服务失败: %v", err)
	}
	defer func() { _ = resp.Body.Close() }()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, web.NewServiceError("读取车辆监测服务响应失败: %v", err)
	}
	// UseNumber：保持上游数字的字面量（Java 侧 hutool/Jackson 原样透传，
	// feerate 是 0.0 而不是 0；大整数也不会被 float64 打回科学计数）。
	var out any
	dec := json.NewDecoder(bytes.NewReader(body))
	dec.UseNumber()
	if err := dec.Decode(&out); err != nil {
		return nil, web.NewServiceError("车辆监测服务响应不是合法 JSON: %s", target)
	}
	return out, nil
}

// jsonFloat 取数字成员：UseNumber 解码后是 json.Number，旧路径可能仍是 float64。
func jsonFloat(v any) (float64, bool) {
	switch x := v.(type) {
	case json.Number:
		f, err := x.Float64()
		return f, err == nil
	case float64:
		return x, true
	}
	return 0, false
}

// dropNullMembers 对应 hutool JSONObject 的默认 ignoreNullValue=true：
// JSONUtil.toBean(jsonObject, TableDataInfo.class) 会把值为 null 的成员丢掉，
// 因此 Java 的行对象比 Go 少一批恒为 null 的字段（cid/enweight/paycardid…）。
func dropNullMembers(v any) any {
	switch x := v.(type) {
	case map[string]any:
		out := make(map[string]any, len(x))
		for k, item := range x {
			if item == nil {
				continue
			}
			out[k] = dropNullMembers(item)
		}
		return out
	case []any:
		out := make([]any, 0, len(x))
		for _, item := range x {
			out = append(out, dropNullMembers(item))
		}
		return out
	default:
		return v
	}
}

// remoteTable 是上游 TableDataInfo 的透传形态（rows 保留原始 JSON）。
type remoteTable struct {
	Total int64           `json:"total"`
	Rows  json.RawMessage `json:"rows"`
	Code  int             `json:"code"`
	Msg   string          `json:"msg"`
}

// forestGetTable 对应 toTableDataInfo（Jackson 反序列化成 TableDataInfo）。
func (h *handler) forestGetTable(c *gin.Context, path string, params map[string]string) (*remoteTable, error) {
	payload, err := h.forestGet(c.Request.Context(), path, params)
	if err != nil {
		return nil, err
	}
	// 数字成员经 UseNumber 解码后是 json.Number，不能再按 float64 断言
	asInt := func(v any) (int64, bool) {
		switch x := v.(type) {
		case json.Number:
			n, err := x.Int64()
			if err == nil {
				return n, true
			}
			f, err := x.Float64()
			return int64(f), err == nil
		case float64:
			return int64(x), true
		}
		return 0, false
	}
	table := &remoteTable{Code: 0}
	if m, ok := payload.(map[string]any); ok {
		if v, ok := asInt(m["total"]); ok {
			table.Total = v
		}
		if v, ok := m["rows"]; ok {
			raw, _ := json.Marshal(v)
			table.Rows = raw
		}
		if v, ok := asInt(m["code"]); ok {
			table.Code = int(v)
		}
		if v, ok := m["msg"].(string); ok {
			table.Msg = v
		}
	}
	return table, nil
}

// renderRemoteTable 输出上游 TableDataInfo。
//
// 两种 Java 侧机制的可见差别，用 dropNull 区分：
//   - OdsLwzxsfsjFeeStationExit01Controller.list:53 用 JSONUtil.toBean(jsonObject, TableDataInfo.class)，
//     hutool 的 JSONObject 默认 ignoreNullValue=true ⇒ 值为 null 的成员整个丢掉；
//   - OdsLwzxsfsjFeeGantryFusion01Controller.list:48 直接返回 Forest 反序列化的 TableDataInfo，
//     走的是 Jackson ⇒ null 成员照旧输出。
//
// 两条路径都保留上游数字的字面量（feerate 是 0.0，不是 0）。
func renderRemoteTable(c *gin.Context, table *remoteTable, dropNull bool) {
	rows := any(nil)
	if len(table.Rows) > 0 {
		dec := json.NewDecoder(bytes.NewReader(table.Rows))
		dec.UseNumber()
		if err := dec.Decode(&rows); err == nil && dropNull {
			rows = dropNullMembers(rows)
		}
	}
	c.JSON(http.StatusOK, &web.TableDataInfo{Total: table.Total, Rows: rows, Code: table.Code, Msg: table.Msg})
}

// feeRecordsRows 把上游 rows 解成可加工的行集合。
func decodeRows(raw json.RawMessage) []map[string]any {
	if len(raw) == 0 {
		return nil
	}
	var rows []map[string]any
	if err := json.Unmarshal(raw, &rows); err != nil {
		return nil
	}
	return rows
}

// feeGantryList 对应 GET /base/feeGantry/list：默认 1/10 后转发。
func (h *handler) feeGantryList(c *gin.Context) {
	params := queryParams(c)
	defaultPaging(params)
	table, err := h.forestGetTable(c, "/base/feeGantry/list", params)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// Forest 反序列化的 TableDataInfo 由 Jackson 输出，null 成员保留
	renderRemoteTable(c, table, false)
}

// feeGantryGet 对应 GET /base/feeGantry/{bigId}。
func (h *handler) feeGantryGet(c *gin.Context) {
	h.proxyGet(c, "/base/feeGantry/"+c.Param("id"))
}

// feeRecordsList 对应 GET /base/feerecords/list。
//
// JAVA 对照: 先写查询日志（模块 3 / 功能 1），再补默认分页、处理 sectionCodeStr，
// 只有 inApplyTime1 + inApplyTime2 都有值时才真正查询；返回体恒为 code=200/查询成功。
func (h *handler) feeRecordsList(c *gin.Context) {
	params := queryParams(c)
	h.writeQueryLog(c, paramJSON(params), "3", "1")
	defaultPaging(params)
	normalizeSectionCodeStr(params)

	rows := []map[string]any{}
	var total int64
	if isNotBlank(params["inApplyTime1"]) && isNotBlank(params["inApplyTime2"]) {
		table, err := h.forestGetTable(c, "/base/feerecords/list", params)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		// JAVA 对照: rows 为空时 Java 保留 new ArrayList<>()（响应里是 []，不是 null）。
		if decoded := decodeRows(table.Rows); len(decoded) > 0 {
			rows = decoded
		}
		total = table.Total
		if len(rows) > 0 {
			if err := h.enrichFeeRecords(c.Request.Context(), rows, false); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
		}
	}
	web.JSON(c, &web.TableDataInfo{Total: total, Rows: rows, Code: web.StatusSuccess, Msg: "查询成功"})
}

// feeRecordsExport 对应 GET /base/feerecords/export（EasyPOI 模板导出）。
func (h *handler) feeRecordsExport(c *gin.Context) {
	params := queryParams(c)
	h.writeQueryLog(c, paramJSON(params), "3", "2")
	defaultPaging(params)
	normalizeSectionCodeStr(params)

	rows := []map[string]any{}
	if isNotBlank(params["inApplyTime1"]) && isNotBlank(params["inApplyTime2"]) {
		payload, err := h.forestGet(c.Request.Context(), "/base/feerecords/listToExport", params)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		// JAVA 对照: 上游返回裸数组（不是 TableDataInfo 信封）。
		if list, ok := payload.([]any); ok {
			for _, item := range list {
				if m, ok := item.(map[string]any); ok {
					rows = append(rows, m)
				}
			}
		}
		if len(rows) > 0 {
			if err := h.enrichFeeRecords(c.Request.Context(), rows, true); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
		}
	}
	cols := feeRecordsExportCols()
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		cells := make([]any, len(cols))
		for i, col := range cols {
			cells[i] = cellValue(row, col.Field)
		}
		out = append(out, cells)
	}
	h.templateExport(c, "收费流水数据", cols, out)
}

// feeRecordsGet 对应 GET /base/feerecords/{bigId}。
func (h *handler) feeRecordsGet(c *gin.Context) {
	h.proxyGet(c, "/base/feerecords/"+c.Param("id"))
}

// feeStationExitList 对应 GET /base/feestationexit/list。
//
// JAVA 对照: 上游 code != 200 时抛 ServiceException("获取数据异常,请联系管理员")。
func (h *handler) feeStationExitList(c *gin.Context) {
	params := queryParams(c)
	defaultPaging(params)
	table, err := h.forestGetTable(c, "/base/feestationexit/list", params)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if table.Code != web.StatusSuccess {
		h.app.Log.Error("交易流水数据获取异常", "code", table.Code, "msg", table.Msg)
		web.JSON(c, web.ErrorResult(web.NewServiceError("获取数据异常,请联系管理员")))
		return
	}
	// Java 侧是 JSONUtil.toBean(...)，hutool 丢 null 成员
	renderRemoteTable(c, table, true)
}

// feeStationExitGet 对应 GET /base/feestationexit/{bigId}。
func (h *handler) feeStationExitGet(c *gin.Context) {
	h.proxyGet(c, "/base/feestationexit/"+c.Param("id"))
}

// proxyGet 转发一条详情查询并按 AjaxResult.success(data) 输出。
func (h *handler) proxyGet(c *gin.Context, path string) {
	payload, err := h.forestGet(c.Request.Context(), path, nil)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(payload))
}

// defaultPaging 对应控制器里的「pageNum/pageSize 为空则置 1/10」。
func defaultPaging(params map[string]string) {
	if isBlank(params["pageNum"]) {
		params["pageNum"] = "1"
	}
	if isBlank(params["pageSize"]) {
		params["pageSize"] = "10"
	}
}

// normalizeSectionCodeStr 对应：deleteEnd 后若包含 "all" 则清空路段条件。
func normalizeSectionCodeStr(params map[string]string) {
	value := deleteEnd(params["sectionCodeStr"])
	if isBlank(value) {
		return
	}
	params["sectionCodeStr"] = value
	if strings.Contains(value, "all") {
		params["sectionCodeStr"] = ""
	}
}

// paramJSON 对应 JSON.toJSONString(entity)（查询日志里的查询条件）。
func paramJSON(params map[string]string) string {
	raw, err := json.Marshal(params)
	if err != nil {
		return ""
	}
	return string(raw)
}

// enrichFeeRecords 复刻控制器的字典/路段名称加工。
//
// JAVA 对照: 车牌号拼车牌颜色、车型/车种走 *_old 字典、fee>0 -> 成功、
// fee 置 null、路段名称/路线名称按 sectionCodeStr 回填。
// withPassstate=true 时（导出）额外把 passstate 转成通行状态标签。
func (h *handler) enrichFeeRecords(ctx context.Context, rows []map[string]any, withPassstate bool) error {
	plateColorMap, err := h.dictValueLabel(ctx, "plate_color")
	if err != nil {
		return err
	}
	carTypeMap, err := h.dictValueLabel(ctx, "car_type_old")
	if err != nil {
		return err
	}
	carVehicleMap, err := h.dictValueLabel(ctx, "car_vehicle_old")
	if err != nil {
		return err
	}
	passstateMap := map[string]string{}
	if withPassstate {
		passstateMap, err = h.dictValueLabel(ctx, "passstate")
		if err != nil {
			return err
		}
	}
	sections := h.loadSectionList(ctx)
	sectionMap := make(map[string]*odsSzdnSection, len(sections))
	for _, section := range sections {
		sectionMap[isNull(section.SectionCode)] = section
	}
	for _, row := range rows {
		if plateColor := cellText(row, "plateColor"); isNotBlank(plateColor) {
			if label := isNull(plateColorMap[plateColor]); isNotBlank(label) {
				row["vehicleplate"] = cellText(row, "vehicleplate") + "_" + label
			}
		}
		if feeVehicleType := cellText(row, "feevehicletype"); isNotBlank(feeVehicleType) {
			row["feevehicletype"] = isNull(carTypeMap[isNull(feeVehicleType)])
		}
		if vehicleClass := cellText(row, "vehicleclass"); isNotBlank(vehicleClass) {
			row["vehicleclass"] = isNull(carVehicleMap[isNull(vehicleClass)])
		}
		if fee, ok := jsonFloat(row["fee"]); ok && fee > 0 {
			row["chargeStatus"] = "成功"
		} else {
			row["chargeStatus"] = "失败"
		}
		row["fee"] = nil
		if sectionCode := isNull(cellText(row, "sectionCodeStr")); isNotBlank(sectionCode) {
			if section, ok := sectionMap[sectionCode]; ok {
				row["sectionName"] = section.SectionName
				row["roadname"] = section.RoadName
			}
		}
		if withPassstate {
			row["passstate"] = isNull(passstateMap[cellText(row, "passstate")])
		}
	}
	return nil
}

// cellText 读取行里的字符串字段（数字转字符串）。
func cellText(row map[string]any, key string) string {
	v, ok := row[key]
	if !ok || v == nil {
		return ""
	}
	switch x := v.(type) {
	case string:
		return x
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return fmt.Sprint(x)
	}
}

// feeRecordsExportCols 是 templates/export/feeRecords.xlsx 的列定义。
func feeRecordsExportCols() []exportCol {
	return []exportCol{
		{Title: "路线名称", Field: "roadname"},
		{Title: "路段名称", Field: "sectionName"},
		{Title: "车牌号", Field: "vehicleplate"},
		{Title: "车型", Field: "feevehicletype"},
		{Title: "车种", Field: "vehicleclass"},
		{Title: "车轴数", Field: "axlecount"},
		{Title: "通行ID", Field: "passid"},
		{Title: "驶入时间", Field: "entimeStr"},
		{Title: "门架", Field: "gantryName"},
		{Title: "计费交易时间", Field: "transtimeStr"},
		{Title: "通行状态", Field: "passstate"},
		{Title: "交易结果", Field: "chargeStatus"},
	}
}
