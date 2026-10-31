// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/SnapshotFlowEnhancedService.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java
// 类/职责: 门架抓拍流水（按月分表）的分页查询、导出与最早抓拍时间
// 对应 Go 文件: internal/modules/base/snapshotflow.go
//
// DIFF: Java 用 Forest 转发 {bigId} / earliest-time 到 vehicleMonitor，这里同样转发（见 fees.go）。
// DIFF: queryPage 成功路径返回 code=0/msg=null（源码如此），这里用 rawTable 复刻。
package base

import (
	"context"
	"encoding/json"
	"fmt"
	"reflect"
	"sort"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

const snapshotShardPrefix = "ods_rt_szdn_snapshot_flow_"

// shardingConds 对应 selectShardingList / selectShardingCount 的 22 条 <if>。
//
// JAVA 对照: 与普通列表条件不同 —— applyTime1/applyTime2 是 snapshottime 的不等式，
// sectionCodeStr 用 find_in_set。逐条照抄 XML，不要复用 snapshotFlowSpec。
var shardingConds = []cond{
	eqCond("bigId", "t.big_id"), eqCond("datasource", "t.datasource"),
	eqCond("cameratype", "t.cameratype"), eqCond("deviceid", "t.deviceid"),
	eqCond("gantrycode", "t.gantrycode"), likeCond("gantryname", "t.gantryname"),
	eqCond("roadcode", "t.roadcode"), likeCond("roadname", "t.roadname"),
	eqCond("sectioncode", "t.sectioncode"), likeCond("sectionname", "t.sectionname"),
	eqCond("tollcode", "t.tollcode"), likeCond("tollname", "t.tollname"),
	eqCond("orgcode", "t.orgcode"), likeCond("orgname", "t.orgname"),
	numCond("direction", "t.direction"), eqCond("platenumber", "t.platenumber"),
	eqCond("platecolor", "t.platecolor"), eqCond("cartype", "t.cartype"),
	tmplCond("applyTime1", "t.snapshottime >= {p}"),
	tmplCond("applyTime2", "t.snapshottime <= {p}"),
	tmplCond("sectionCodeStr", "find_in_set(t.sectioncode, {p})"),
}

// snapshotSelectColumns 对应 selectOdsRtSzdnSnapshotFlowAddcodeVo。
const snapshotSelectColumns = `t.big_id, t.datasource, t.cameratype, t.deviceid, t.gantrycode,
	t.gantryname, t.roadcode, t.roadname, t.sectioncode, t.sectionname, t.tollcode,
	t.tollname, t.orgcode, t.orgname, t.direction, t.hexcode, t.pileno, t.lon, t.lat,
	t.deviceip, t.siteid, t.laneid, t.snapshottimeunix, t.snapshottime, t.receivedtimeunix,
	t.receivedtime, t.platenumber, t.platecolor, t.platecolorcode, t.platetype,
	t.platetypecode, t.plateconfidence, t.carbrand, t.carcolor, t.carcolorcode, t.cartype,
	t.cartypecode, t.cardirection, t.snappicturepath, t.loadtime, t.gradelevel, t.datauuid,
	t.reserve3`

// rawTable 复刻 TableDataInfo 的 msg 可为 null 的形态。
type rawTable struct {
	Total int64 `json:"total"`
	Rows  any   `json:"rows"`
	Code  int   `json:"code"`
	Msg   *string
}

func (r rawTable) MarshalJSON() ([]byte, error) {
	return json.Marshal(struct {
		Total int64   `json:"total"`
		Rows  any     `json:"rows"`
		Code  int     `json:"code"`
		Msg   *string `json:"msg"`
	}{r.Total, r.Rows, r.Code, r.Msg})
}

// snapshotFlowList 对应 GET /base/snapshotflow/list。
func (h *handler) snapshotFlowList(c *gin.Context) {
	params := queryParams(c)
	h.writeQueryLog(c, paramJSON(params), "2", "1")
	defaultPaging(params)
	normalizeSectionCodeStr(params)

	empty := func() {
		web.JSON(c, &web.TableDataInfo{Total: 0, Rows: []*odsRtSzdnSnapshotFlowAddcode{}, Code: web.StatusSuccess, Msg: "查询成功"})
	}
	if isBlank(params["applyTime1"]) || isBlank(params["applyTime2"]) {
		empty()
		return
	}
	if !validateTimeRange(params["applyTime1"], params["applyTime2"]) {
		h.app.Log.Warn("【时间校验】查询时间范围无效或超过当前时间，返回空数据")
		empty()
		return
	}
	rows, total, err := h.queryShardingPage(c.Request.Context(), params)
	if err != nil {
		// JAVA 对照: queryPage 自己吞掉异常 -> 空列表 + code 200。
		h.app.Log.Error("【分表查询】查询失败", "err", err)
		empty()
		return
	}
	// JAVA 对照: 成功路径的 TableDataInfo 只 setRows/setTotal，code=0、msg=null。
	web.JSON(c, rawTable{Total: total, Rows: rows, Code: 0, Msg: nil})
}

// snapshotFlowExport 对应 GET /base/snapshotflow/export（EasyPOI 模板导出）。
func (h *handler) snapshotFlowExport(c *gin.Context) {
	params := queryParams(c)
	h.writeQueryLog(c, paramJSON(params), "2", "2")
	defaultPaging(params)
	normalizeSectionCodeStr(params)

	var rows []*odsRtSzdnSnapshotFlowAddcode
	if isNotBlank(params["applyTime1"]) && isNotBlank(params["applyTime2"]) {
		list, err := h.queryShardingListForExport(c.Request.Context(), params)
		if err != nil {
			h.app.Log.Error("【导出查询】查询失败", "err", err)
		} else {
			rows = list
		}
	}

	directionMap, err := h.dictValueLabel(c.Request.Context(), "direction")
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	for _, row := range rows {
		// JAVA 对照: dp.getDirection().toString() —— direction 为 null 时 Java 会 NPE；
		// 这里退化为空串（DIFF）。
		if row.Direction == nil {
			row.DirectionStr = strPtr("")
		} else {
			row.DirectionStr = strPtr(directionMap[fmt.Sprint(*row.Direction)])
		}
	}

	cols := snapshotFlowExportCols()
	index := jsonTagIndex(reflectTypeOf(&odsRtSzdnSnapshotFlowAddcode{}))
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		cells := make([]any, len(cols))
		for i, col := range cols {
			cells[i] = plainValue(fieldValue(reflect.ValueOf(row), index, col.Field), col.DateOnly)
		}
		out = append(out, cells)
	}
	h.templateExport(c, "门架抓拍流水数据", cols, out)
}

// snapshotFlowGet 对应 GET /base/snapshotflow/{bigId}（转发到车辆监测服务）。
func (h *handler) snapshotFlowGet(c *gin.Context) {
	h.proxyGet(c, "/base/snapshotflow/"+c.Param("id"))
}

// snapshotFlowEarliest 对应 GET /base/snapshotflow/earliest-time。
//
// JAVA 对照: Date earliestTime = http...getEarliestSnapshottime();
// 有值 -> success(earliestTime)；null -> success("暂无数据")。
//
// DIFF: Java 声明返回 java.util.Date，由 Jackson 按 ISO-8601 输出；这里原样透传上游值，
// 避免引入一个 Java 侧并不稳定的日期格式（与 Python 迁移一致）。
func (h *handler) snapshotFlowEarliest(c *gin.Context) {
	payload, err := h.forestGet(c.Request.Context(), "/base/snapshotflow/earliest-time", nil)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if payload == nil {
		web.JSON(c, web.SuccessMsg("暂无数据"))
		return
	}
	web.JSON(c, web.SuccessData(payload))
}

// snapshotFlowExportCols 是 templates/export/snapshotFlow.xlsx 的列定义。
func snapshotFlowExportCols() []exportCol {
	return []exportCol{
		{Title: "路线名称", Field: "roadname"},
		{Title: "路段名称", Field: "sectionname"},
		{Title: "车牌颜色", Field: "platecolor"},
		{Title: "车牌号", Field: "platenumber"},
		{Title: "车辆类型", Field: "cartype"},
		{Title: "门架", Field: "gantryname"},
		{Title: "方向", Field: "directionStr"},
		{Title: "抓拍时间", Field: "snapshottimeStr"},
	}
}

// ---------------------------------------------------------------------------
// 分表查询（SnapshotFlowEnhancedService）
// ---------------------------------------------------------------------------

// shardTableName 对应 ShardingTableUtil.getTableNameByDate(date)：前缀 + yyyyMM。
func shardTableName(t time.Time) string { return snapshotShardPrefix + t.Format("200601") }

// currentShardTable 对应当前月份分表。
func currentShardTable() string { return shardTableName(time.Now()) }

// parseDateLike 对应 ShardingTableUtil.parseDate 的三种长度。
func parseDateLike(value string) (time.Time, bool) {
	value = strings.TrimSpace(value)
	switch {
	case len(value) >= 19:
		t, err := time.ParseInLocation("2006-01-02 15:04:05", value[:19], time.Local)
		return t, err == nil
	case len(value) == 10:
		t, err := time.ParseInLocation("2006-01-02", value, time.Local)
		return t, err == nil
	case len(value) == 8:
		t, err := time.ParseInLocation("20060102", value, time.Local)
		return t, err == nil
	default:
		return time.Time{}, false
	}
}

// addMonthsClamped 等价 Calendar.add(MONTH, n)：日期按目标月夹紧。
func addMonthsClamped(t time.Time, months int) time.Time {
	total := t.Year()*12 + int(t.Month()) - 1 + months
	year, monthIndex := total/12, total%12
	month := time.Month(monthIndex + 1)
	day := t.Day()
	if last := time.Date(year, month+1, 0, 0, 0, 0, 0, t.Location()).Day(); day > last {
		day = last
	}
	return time.Date(year, month, day, t.Hour(), t.Minute(), t.Second(), 0, t.Location())
}

// tableNamesByDateRange 对应 ShardingTableUtil.getTableNamesByDateRange。
func tableNamesByDateRange(startStr, endStr string) []string {
	names := make([]string, 0)
	start, ok := parseDateLike(startStr)
	if !ok {
		return names
	}
	end, ok := parseDateLike(endStr)
	if !ok {
		return names
	}
	seen := make(map[string]bool)
	for cursor := start; !cursor.After(end); cursor = addMonthsClamped(cursor, 1) {
		name := shardTableName(cursor)
		if !seen[name] {
			seen[name] = true
			names = append(names, name)
		}
	}
	return names
}

// validateTimeRange 对应 SnapshotFlowEnhancedService#validateTimeRange。
func validateTimeRange(startStr, endStr string) bool {
	startStr, endStr = strings.TrimSpace(startStr), strings.TrimSpace(endStr)
	if startStr == "" && endStr == "" {
		return true
	}
	now := time.Now()
	const layout = "2006-01-02 15:04:05"
	if len(startStr) == 10 {
		startStr += " 00:00:00"
	}
	if len(endStr) == 10 {
		endStr += " 23:59:59"
	}
	if startStr != "" {
		start, err := time.ParseInLocation(layout, startStr, time.Local)
		if err != nil {
			return false
		}
		if start.After(now) {
			return false
		}
	}
	if endStr != "" {
		end, err := time.ParseInLocation(layout, endStr, time.Local)
		if err != nil {
			return false
		}
		if end.After(now) {
			return false
		}
	}
	if startStr != "" && endStr != "" {
		start, _ := time.ParseInLocation(layout, startStr, time.Local)
		end, _ := time.ParseInLocation(layout, endStr, time.Local)
		if start.After(end) {
			return false
		}
	}
	return true
}

// hasExtraFilters 对应 SnapshotFlowEnhancedService#hasExtraFilters。
func hasExtraFilters(params map[string]string) bool {
	return isNotBlank(params["platenumber"]) || isNotBlank(params["deviceid"]) ||
		isNotBlank(params["gantrycode"]) || isNotBlank(params["sectionCodeStr"]) ||
		isNotBlank(params["direction"]) || isNotBlank(params["platecolor"]) ||
		isNotBlank(params["cartype"]) || isNotBlank(params["datasource"])
}

// shardCount 对应 selectShardingCount。
func (h *handler) shardCount(ctx context.Context, table, clause string, args []any) (int64, error) {
	var total int64
	err := h.app.DB.WithContext(ctx).Raw(
		"SELECT COUNT(1) FROM "+table+" t "+clause, args...).Scan(&total).Error
	return total, err
}

// shardApproximateCount 对应 getTableApproximateCount（INFORMATION_SCHEMA.TABLE_ROWS）。
func (h *handler) shardApproximateCount(ctx context.Context, table string) (int64, bool) {
	var rows []int64
	err := h.app.DB.WithContext(ctx).Raw(
		"SELECT TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?",
		table).Scan(&rows).Error
	if err != nil || len(rows) == 0 {
		return 0, false
	}
	return rows[0], true
}

// approximateOrExactCount 对应 getApproximateCount。
func (h *handler) approximateOrExactCount(ctx context.Context, table string, params map[string]string,
	clause string, args []any) int64 {
	if !hasExtraFilters(params) {
		if approx, ok := h.shardApproximateCount(ctx, table); ok && approx > 0 {
			return approx
		}
	}
	total, err := h.shardCount(ctx, table, clause, args)
	if err != nil {
		return 0
	}
	return total
}

// shardPage 对应 selectShardingList：ORDER BY snapshottime DESC + LIMIT offset,pageSize。
func (h *handler) shardPage(ctx context.Context, table, clause string, args []any,
	offset, size int) ([]*odsRtSzdnSnapshotFlowAddcode, error) {
	sqlStr := "SELECT " + snapshotSelectColumns + " FROM " + table + " t " + clause +
		" ORDER BY t.snapshottime DESC LIMIT ? OFFSET ?"
	all := append(append([]any{}, args...), size, offset)
	var rows []*odsRtSzdnSnapshotFlowAddcode
	if err := h.app.DB.WithContext(ctx).Raw(sqlStr, all...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	return rows, nil
}

// queryShardingPage 对应 SnapshotFlowEnhancedService#queryFromShardingTables。
func (h *handler) queryShardingPage(ctx context.Context, params map[string]string) ([]*odsRtSzdnSnapshotFlowAddcode, int64, error) {
	tables := tableNamesByDateRange(params["applyTime1"], params["applyTime2"])
	clause, args := buildWhereMap("WHERE 1=1", shardingConds, params)
	current := currentShardTable()

	var total int64
	for _, table := range tables {
		if table == current {
			count, err := h.shardCount(ctx, table, clause, args)
			if err != nil {
				continue
			}
			total += count
		} else {
			total += h.approximateOrExactCount(ctx, table, params, clause, args)
		}
	}

	pageNum, pageSize := parseIntDefault(params["pageNum"], 1), parseIntDefault(params["pageSize"], 10)
	offset := (pageNum - 1) * pageSize
	out := make([]*odsRtSzdnSnapshotFlowAddcode, 0)
	if total <= int64(offset) {
		return out, total, nil
	}

	remaining := pageSize
	currentOffset := offset
	for _, table := range tables {
		if remaining <= 0 {
			break
		}
		tableCount, err := h.shardCount(ctx, table, clause, args)
		if err != nil {
			continue
		}
		if int64(currentOffset) >= tableCount {
			currentOffset -= int(tableCount)
			continue
		}
		pageRows, err := h.shardPage(ctx, table, clause, args, currentOffset, pageSize)
		if err != nil {
			continue
		}
		take := len(pageRows)
		if take > remaining {
			take = remaining
		}
		out = append(out, pageRows[:take]...)
		remaining -= take
		currentOffset = 0
	}
	sortBySnapshottimeDesc(out)
	return out, total, nil
}

// queryShardingListForExport 对应 queryListForExport（每张分表都带 LIMIT 0,pageSize）。
func (h *handler) queryShardingListForExport(ctx context.Context, params map[string]string) ([]*odsRtSzdnSnapshotFlowAddcode, error) {
	tables := tableNamesByDateRange(params["applyTime1"], params["applyTime2"])
	clause, args := buildWhereMap("WHERE 1=1", shardingConds, params)
	pageSize := parseIntDefault(params["pageSize"], 10)
	out := make([]*odsRtSzdnSnapshotFlowAddcode, 0)
	for _, table := range tables {
		pageRows, err := h.shardPage(ctx, table, clause, args, 0, pageSize)
		if err != nil {
			continue
		}
		out = append(out, pageRows...)
	}
	sortBySnapshottimeDesc(out)
	return out, nil
}

// sortBySnapshottimeDesc 对应 Comparator.comparing(getSnapshottime).reversed()。
//
// DIFF: Java 对 null 会 NPE；这里把 null 排在最后。
func sortBySnapshottimeDesc(rows []*odsRtSzdnSnapshotFlowAddcode) {
	sort.SliceStable(rows, func(i, j int) bool {
		a, b := rows[i].Snapshottime, rows[j].Snapshottime
		if a == nil {
			return false
		}
		if b == nil {
			return true
		}
		return a.After(b.Time)
	})
}

// parseIntDefault 解析分页参数，失败时返回默认值。
func parseIntDefault(value string, fallback int) int {
	if n, err := parseInt64(value); err == nil && n > 0 {
		return int(n)
	}
	return fallback
}
