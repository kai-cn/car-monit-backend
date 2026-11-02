// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningInfoServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml
// 类/职责: 预警车辆（car_warning_info）控制器与大屏预警缓存
// 对应 Go 文件: internal/modules/manager/car_warning.go
//
// DIFF: Java 详情里的 trailFwqList 从 Redis 的 car_history_trail:<车牌> 反推；
// Go 侧按同样的缓存键读取并做相同过滤（服务区/收费站抓拍点按设备名去重）。
package manager

import (
	"context"
	"math"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/auth"
	"car-monit-go/internal/cache"
	"car-monit-go/internal/web"
)

const (
	stationCapture     = "StationCapture"
	gantryCapture      = "GantryCapture"
	serviceAreaCapture = "ServiceAreaCapture"
	sectionAll         = "all"
)

var warningInfoSpec = &tableSpec{
	table:     carWarningInfoTable,
	selectSQL: carWarningInfoSelectColumns,
	fromSQL:   "car_warning_info t left join car_info c on t.car_id = c.id",
	detailSuffix: ",t.track_josn, c.escaped_type AS escaped_type, c.escaped_amount AS escaped_amount," +
		"c.plate_color AS plate_color",
	orderBy:   "t.gantry_time desc,t.id",
	columns:   carWarningInfoColumns,
	prototype: &carWarningInfo{},
	conditions: []cond{
		eqCond("id", "t.id"), eqCond("carId", "t.car_id"), likeCond("carNo", "t.car_no"),
		eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
		nullCond("carNum", "t.car_num"), eqCond("inStationId", "t.in_station_id"),
		eqCond("inStation", "t.in_station"), nullCond("inTime", "t.in_time"),
		eqCond("gantryStationId", "t.gantry_station_id"), likeCond("gantrytStation", "t.gantryt_station"),
		nullCond("gantryTime", "t.gantry_time"), eqCond("fileIds", "t.file_ids"),
		nullCond("nextPassTime", "t.next_pass_time"), eqCond("nextPassType", "t.next_pass_type"),
		eqCond("nextPassAddress", "t.next_pass_address"), eqCond("nextPassLongitude", "t.next_pass_longitude"),
		eqCond("nextPassLatitude", "t.next_pass_latitude"), likeCond("roadCode", "t.track_names"),
		likeCond("roadName", "t.road_name"), likeCond("sectionCode", "t.track_names"),
		likeCond("sectionName", "t.section_name"), eqCond("trackId", "t.track_id"),
		eqCond("trackJosn", "t.track_josn"), likeCond("trackNames", "t.track_names"),
		eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
		eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		dateTimeGe("applyTime1", "in_time"), dateTimeLe("applyTime2", "in_time"),
		likeCond("carNoQuery", "t.car_no"),
		tmplCond("escapedType", "c.escaped_type LIKE CONCAT('%', ?, '%')"),
		tmplCond("plateColor", "c.plate_color = ?"),
	},
}

// warningClause 对应控制器里的 flag/sectionCode/code 规整 + XML 里 4 条特殊 <if>。
func warningClause(c *gin.Context) (string, []any) {
	// Java 在拼完 sectionCodeList 后无条件清空 sectionCode（查询范围字段）。
	sectionCode := deleteEnd(queryParam(c, "sectionCode"))
	if sectionCode != "" {
		setQuery(c, "sectionCode", "")
	}
	clause, args := buildWhere(c, warningInfoSpec.prefix(), warningInfoSpec.conditions)

	flag := queryParam(c, "queryRante")
	if flag == "" {
		flag = "curDate"
	}
	formattedDate := time.Now().Format("20060102")
	switch flag {
	case "curDate":
		clause += " AND c.status = '1' and t.back_col1 = ?"
		args = append(args, formattedDate)
	case "histhory":
		clause += " AND t.back_col1 != ?"
		args = append(args, formattedDate)
	}

	// 路段：含 all 时不过滤；否则多值 OR（XML 用 or 而不是 in）。
	if sectionCode != "" && !strings.Contains(sectionCode, sectionAll) {
		values := splitCSV(sectionCode)
		if frag, fragArgs := orLikeClause("t.track_names", values); frag != "" {
			clause += " AND " + frag
			args = append(args, fragArgs...)
		}
	}

	// 选择对象：code 优先；否则按 type 塞抓拍类型。
	code := deleteEnd(queryParam(c, "code"))
	var codeValues []string
	if code != "" {
		codeValues = splitCSV(code)
	} else {
		switch queryParam(c, "type") {
		case "1":
			codeValues = []string{stationCapture}
		case "2":
			codeValues = []string{gantryCapture}
		case "3":
			codeValues = []string{serviceAreaCapture}
		}
	}
	if frag, fragArgs := orLikeClause("t.track_names", codeValues); frag != "" {
		clause += " AND " + frag
		args = append(args, fragArgs...)
	}
	return clause, args
}

// orLikeClause 生成 "(col LIKE %?% OR ...)"；空列表返回空片段。
func orLikeClause(column string, values []string) (string, []any) {
	if len(values) == 0 {
		return "", nil
	}
	parts := make([]string, 0, len(values))
	args := make([]any, 0, len(values))
	for _, value := range values {
		parts = append(parts, column+" LIKE CONCAT('%', ?, '%')")
		args = append(args, value)
	}
	return "(" + strings.Join(parts, " OR ") + ")", args
}

// isExitsStr 对应 CommonUtil.isExitsStr：空条件不过滤；逗号多值任一命中即可。
func isExitsStr(source, para any) bool {
	para = deleteEnd(para)
	if para == "" {
		return true
	}
	haystack := isNull(source)
	for _, item := range splitCSV(strOf(para)) {
		if strings.Contains(haystack, item) {
			return true
		}
	}
	return false
}

// warningInfoList 对应 GET /list（权限点被 Java 注释掉，仅需登录）。
func (h *handler) warningInfoList(c *gin.Context) {
	clause, args := warningClause(c)
	dest := newSliceOf(&carWarningInfo{})
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: warningInfoSpec.selectSQL,
		FromSQL:   warningInfoSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   warningInfoSpec.orderBy,
		Page:      web.Page(c),
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows := *(dest.(*[]*carWarningInfo))
	h.decorateWarningList(c, rows)
	web.JSON(c, web.Table(rows, total))
}

// decorateWarningList 对应控制器里的时间字符串与字典映射。
func (h *handler) decorateWarningList(c *gin.Context, rows []*carWarningInfo) {
	plateColors, _ := h.dictValueLabel(c.Request.Context(), "plate_color")
	carTypes, _ := h.dictValueLabel(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictValueLabel(c.Request.Context(), "car_vehicle")
	escapedTypes, _ := h.dictValueLabel(c.Request.Context(), "escaped_type")
	for _, row := range rows {
		if row.GantryTime != nil && !row.GantryTime.IsZero() {
			row.GantryTimeStr = strPtr(row.GantryTime.String())
		}
		if row.CreateTime != nil && !row.CreateTime.IsZero() {
			row.CreateTimeStr = strPtr(row.CreateTime.String())
		}
		if row.InTime != nil && !row.InTime.IsZero() {
			row.InTimeStr = strPtr(row.InTime.String())
		}
		if row.NextPassTime != nil && !row.NextPassTime.IsZero() {
			row.NextPassTimeStr = strPtr(row.NextPassTime.String())
		}
		if label, ok := plateColors[strOf(row.PlateColor)]; ok {
			row.PlateColor = strPtr(label)
		} else {
			row.PlateColor = strPtr("")
		}
		if label, ok := carTypes[strOf(row.CarType)]; ok {
			row.CarType = strPtr(label)
		} else {
			row.CarType = strPtr("")
		}
		if label, ok := carVehicles[strOf(row.CarVehicle)]; ok {
			row.CarVehicle = strPtr(label)
		} else {
			row.CarVehicle = strPtr("")
		}
		var names []string
		for _, part := range splitCSV(deleteEnd(row.EscapedType)) {
			if label, ok := escapedTypes[part]; ok {
				names = append(names, label)
			}
		}
		row.EscapedType = strPtr(strings.Join(names, ","))
	}
}

// warningInfoExport 对应 EasyPOI 模板 carWarningInfo.xlsx（附件流）。
func (h *handler) warningInfoExport(c *gin.Context) {
	clause, args := warningClause(c)
	dest := newSliceOf(&carWarningInfo{})
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: warningInfoSpec.selectSQL,
		FromSQL:   warningInfoSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   warningInfoSpec.orderBy,
	}, dest); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	h.decorateWarningList(c, *(dest.(*[]*carWarningInfo)))
	cols := []exportCol{
		{Title: "车牌颜色", Field: "plateColor"},
		{Title: "车牌号", Field: "carNo"},
		{Title: "车型", Field: "carType"},
		{Title: "逃费类型", Field: "escapedType"},
		{Title: "逃费金额（元）", Field: "escapedAmount"},
		{Title: "最新经纬度", Field: "nextPassLongitude"},
		{Title: "经过时间", Field: "gantryTimeStr"},
		{Title: "入口站", Field: "inStation"},
		{Title: "入口时间", Field: "inTimeStr"},
		{Title: "预计下一次通行时间", Field: "nextPassTimeStr"},
		{Title: "预计下一次通行地址", Field: "nextPassAddress"},
	}
	rows := make([][]any, 0, sliceLenOf(dest))
	for _, row := range *(dest.(*[]*carWarningInfo)) {
		values := make([]any, len(cols))
		for i, col := range cols {
			switch col.Field {
			case "plateColor":
				values[i] = row.PlateColor
			case "carNo":
				values[i] = row.CarNo
			case "carType":
				values[i] = row.CarType
			case "escapedType":
				values[i] = row.EscapedType
			case "escapedAmount":
				values[i] = plainValue(row.EscapedAmount)
			case "nextPassLongitude":
				values[i] = row.NextPassLongitude
			case "gantryTimeStr":
				values[i] = row.GantryTimeStr
			case "inStation":
				values[i] = row.InStation
			case "inTimeStr":
				values[i] = row.InTimeStr
			case "nextPassTimeStr":
				values[i] = row.NextPassTimeStr
			case "nextPassAddress":
				values[i] = row.NextPassAddress
			}
		}
		rows = append(rows, values)
	}
	data, err := buildWorkbook("预警车辆", cols, rows)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "carWarningInfo.xlsx", data)
}

// warningInfoGet 对应 GET /{id} —— 附带 trailFwqList。
func (h *handler) warningInfoGet(c *gin.Context) {
	dest := &carWarningInfo{}
	sqlStr := "SELECT " + warningInfoSpec.selectSQL + warningInfoSpec.detailSuffix +
		" FROM car_warning_info t left join car_info c on t.car_id = c.id WHERE t.id = ?"
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, c.Param("id")).Scan(dest)
	if tx.Error != nil {
		web.JSON(c, web.ErrorResult(tx.Error))
		return
	}
	if tx.RowsAffected == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	dest.TrailFwqList = h.trailFwqList(c, dest)
	web.JSON(c, web.SuccessData(dest))
}

// trailFwqList 对应 selectCarWarningInfoById 的轨迹反查（读 car_history_trail:<车牌>）。
func (h *handler) trailFwqList(c *gin.Context, dest *carWarningInfo) []*trailBO {
	carNo := isNull(dest.CarNo)
	gantryStationID := isNull(dest.GantryStationID)
	var trailInfoList []*trailInfo
	if !h.app.Cache.Get(c.Request.Context(), carHistoryTrailKey+carNo, &trailInfoList) {
		return []*trailBO{}
	}
	indexType := serviceAreaCapture
	if isNull(h.app.Cfg.IsLocalhost) == "local" {
		indexType = stationCapture
	}
	nameMap := map[string]string{}
	out := make([]*trailBO, 0)
	for _, info := range trailInfoList {
		points, ok := info.TrailList.([]any)
		if !ok {
			continue
		}
		matched := false
		for _, raw := range points {
			point, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			if gantryStationID == isNull(stringValue(point["devCode"])) {
				matched = true
				break
			}
		}
		if !matched {
			continue
		}
		for _, raw := range points {
			point, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			if indexType != isNull(stringValue(point["stateType"])) {
				continue
			}
			devName := isNull(stringValue(point["devName"]))
			if devName == "" {
				continue
			}
			if _, exists := nameMap[devName]; exists {
				continue
			}
			nameMap[devName] = devName
			out = append(out, &trailBO{
				PointUUID:   strPtr(stringValue(point["pointUuid"])),
				StateType:   strPtr(stringValue(point["stateType"])),
				DevCode:     strPtr(stringValue(point["devCode"])),
				DevName:     strPtr(devName),
				CaptureTime: strPtr(stringValue(point["captureTime"])),
				RoadCode:    strPtr(stringValue(point["roadCode"])),
				SectionCode: strPtr(stringValue(point["sectionCode"])),
			})
		}
	}
	return out
}

// warningInfoSave 对应 saveCarWarningInfo：userId 硬编码 1。
func (h *handler) warningInfoSave(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	id := bodyString(body, "id")
	cols := pickColumns(body, carWarningInfoColumns)
	now := time.Now()
	const systemUserID int64 = 1
	if id != "" {
		cols["update_by"] = systemUserID
		cols["update_time"] = now
		if _, err := h.updateRow(c.Request.Context(), carWarningInfoTable, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		id = newUUID()
		cols["id"] = id
		cols["del_flag"] = "0"
		cols["create_by"] = systemUserID
		cols["create_time"] = now
		cols["update_by"] = systemUserID
		cols["update_time"] = now
		if err := h.insertRow(c.Request.Context(), carWarningInfoTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// warningInfoDelete 对应 deleteCarWarningInfoByIds（逻辑删除）。
func (h *handler) warningInfoDelete(c *gin.Context) {
	h.tableDelete(c, warningInfoSpec)
}

// selectWarningListLimit100 对应 selectCarWarningInfoListLimit100（大屏）。
func (h *handler) selectWarningListLimit100(c *gin.Context) []*carWarningInfo {
	rows := h.getRedisWarningList(c)
	out := make([]*carWarningInfo, 0, len(rows))
	for _, row := range rows {
		devCodes := isNull(row.TrackNames)
		if !isExitsStr(devCodes, queryParam(c, "roadCode")) ||
			!isExitsStr(devCodes, queryParam(c, "sectionCode")) ||
			!isExitsStr(devCodes, queryParam(c, "tollCode")) ||
			!isExitsStr(devCodes, queryParam(c, "gantryCode")) ||
			!isExitsStr(devCodes, queryParam(c, "fwqbm")) {
			continue
		}
		if !isExitsStr(row.EscapedType, queryParam(c, "escapedType")) ||
			!isExitsStr(row.CarNo, queryParam(c, "carNoQuery")) {
			continue
		}
		row.NeedToWarnStr = strPtr("0")
		out = append(out, row)
	}
	if len(out) == 0 {
		return out
	}

	cacheObjectNum := 10
	userID := auth.CurrentUserID(c)
	noticeType := "1"
	redisKey := carWarningRuleKey + strconv.FormatInt(userID, 10) + "type" + noticeType
	var ruleList []string
	h.app.Cache.Get(c.Request.Context(), redisKey, &ruleList)
	if len(ruleList) > 0 {
		if span, ok := h.app.Cache.GetStringJava(c.Request.Context(), "sys_config:warning_trigger_timespan"); ok {
			if v, err := strconv.Atoi(span); err == nil {
				cacheObjectNum = v
			}
		}
		minutesInMillis := int64(cacheObjectNum) * 60 * 1000
		nowMillis := time.Now().UnixMilli()
		for _, row := range out {
			if row.GantryTime == nil || row.GantryTime.IsZero() {
				continue
			}
			diff := int64(math.Abs(float64(nowMillis - row.GantryTime.UnixMilli())))
			if diff <= minutesInMillis {
				for _, rule := range ruleList {
					if isNull(row.GantryStationID) == rule {
						row.NeedToWarnStr = strPtr("1")
					}
				}
			}
		}
	}
	return out
}

// getRedisWarningList 对应 getRedisCarWarningList（今天日期的在线车辆预警）。
func (h *handler) getRedisWarningList(c *gin.Context) []*carWarningInfo {
	var cached []*carWarningInfo
	if h.app.Cache.Get(c.Request.Context(), carWarningListKey, &cached) {
		return cached
	}
	rows := h.queryWarningToday(c)
	_ = h.app.Cache.SetJava(c.Request.Context(), carWarningListKey, rows, time.Duration(cacheTTL), cache.CarWarningInfoJava)
	return rows
}

// queryWarningToday 对应 mapper 的 selectCarWarningInfoListLimit100。
func (h *handler) queryWarningToday(c *gin.Context) []*carWarningInfo {
	sqlStr := "SELECT " + carWarningInfoSelectColumns + ", c.escaped_type AS escaped_type, " +
		"c.escaped_amount AS escaped_amount FROM car_warning_info t " +
		"inner join car_info c on c.del_flag = '0' and t.car_id = c.id and c.status = '1' " +
		"WHERE t.del_flag = '0' and t.back_col1 = ? order by t.gantry_time desc,t.id"
	dest := newSliceOf(&carWarningInfo{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, time.Now().Format("20060102")).Scan(dest).Error; err != nil {
		return nil
	}
	return *(dest.(*[]*carWarningInfo))
}

// updateRedisWarningList 对应 updateRedisWarningList（供定时任务调用）。
func (h *handler) updateRedisWarningList(c *gin.Context) {
	rows := h.queryWarningToday(c)
	_ = h.app.Cache.SetJava(c.Request.Context(), carWarningListKey, rows, time.Duration(cacheTTL), cache.CarWarningInfoJava)
}

// sliceLenOf 返回 *[]T 的长度。
func sliceLenOf(dest any) int64 { return sliceLen(dest) }
