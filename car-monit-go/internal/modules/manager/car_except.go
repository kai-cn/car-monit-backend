// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarExceptRecordServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml
// 类/职责: 异常车辆流水（car_except_record）控制器
// 对应 Go 文件: internal/modules/manager/car_except.go
//
// DIFF: Java 的 ImportSysUtil 支持「第二行/第三行表头」两种模板；这里按模板的 21 列
// 固定序号读取（与 initListTwo / initListThree 的属性下标完全一致）。
package manager

import (
	"context"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// exceptRecordSpec 对应 selectCarExceptRecordList（applyTime2 打在 out_time 上）。
var exceptRecordSpec = &tableSpec{
	table:     carExceptRecordTable,
	selectSQL: carExceptRecordSelectColumns,
	fromSQL: "car_except_record t left join sys_user su on su.user_id = t.create_by " +
		"left join sys_dept sd on t.eps_id = sd.dept_id",
	selectSuffix: ",concat(sd.dept_name, ' ', su.nick_name) AS create_info",
	orderBy:      "t.create_time desc,t.id",
	columns:      carExceptRecordColumns,
	prototype:    &carExceptRecord{},
	conditions: []cond{
		eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
		eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
		nullCond("carNum", "t.car_num"), eqCond("passType", "t.pass_type"),
		eqCond("inStationId", "t.in_station_id"), likeCond("inStation", "t.in_station"),
		nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
		likeCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
		nullCond("totalAmount", "t.total_amount"), nullCond("chargeAmount", "t.charge_amount"),
		nullCond("difAmount", "t.dif_amount"), eqCond("escapedType", "t.escaped_type"),
		eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
		eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		dateTimeGe("applyTime1", "in_time"), dateTimeLe("applyTime2", "out_time"),
		dateTimeGe("applyTime3", "out_time"), dateTimeLe("applyTime4", "out_time"),
		likeCond("carNoQuery", "t.car_no"), inSetCond("exceptIds"),
	},
}

// exceptRecordSpecNew 对应 selectCarExceptRecordListNew（按差额倒序）。
var exceptRecordSpecNew = &tableSpec{
	table:        carExceptRecordTable,
	selectSQL:    carExceptRecordSelectColumns,
	fromSQL:      exceptRecordSpec.fromSQL,
	selectSuffix: exceptRecordSpec.selectSuffix,
	orderBy:      "t.dif_amount desc,t.id",
	columns:      carExceptRecordColumns,
	prototype:    &carExceptRecord{},
	conditions: []cond{
		eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
		eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
		nullCond("carNum", "t.car_num"), eqCond("passType", "t.pass_type"),
		eqCond("inStationId", "t.in_station_id"), likeCond("inStation", "t.in_station"),
		nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
		likeCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
		nullCond("totalAmount", "t.total_amount"), nullCond("chargeAmount", "t.charge_amount"),
		nullCond("difAmount", "t.dif_amount"), eqCond("escapedType", "t.escaped_type"),
		eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
		eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		dateTimeGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		eqCond("orgId", "t.eps_id"),
		dateTimeGe("applyTime3", "out_time"), dateTimeLe("applyTime4", "out_time"),
		likeCond("carNoQuery", "t.car_no"), inSetCond("exceptIds"),
	},
}

func (h *handler) registerExceptRecord(reg *router.Registry) {
	auth := reg.Authed
	auth.GET("/manager/exceptrecord/list", h.exceptList)
	auth.GET("/manager/exceptrecord/listCarNo", h.exceptListCarNo)
	auth.GET("/manager/exceptrecord/listCarOrgId", h.exceptListCarOrgID)
	auth.GET("/manager/exceptrecord/exportOrgId", h.exceptExportOrgID)
	auth.GET("/manager/exceptrecord/listExceptId", h.exceptListExceptID)
	auth.GET("/manager/exceptrecord/exceptRecordCount", h.exceptRecordCount)
	auth.GET("/manager/exceptrecord/export", h.exceptExport)
	auth.GET("/manager/exceptrecord/getConfirmId/:id", h.exceptGetConfirmID)
	auth.GET("/manager/exceptrecord/:id", h.exceptGet)
	auth.POST("/manager/exceptrecord", h.exceptSave)
	auth.PUT("/manager/exceptrecord", h.exceptSave)
	auth.DELETE("/manager/exceptrecord/:ids", h.exceptDelete)
	auth.POST("/manager/exceptrecord/import", h.exceptImport)
}

// normalizeExceptRecords 补齐 Java 实体字段默认值（列表/详情扫描后调用）。
func normalizeExceptRecords(dest any) {
	switch x := dest.(type) {
	case *[]*carExceptRecord:
		for _, row := range *x {
			if row != nil {
				row.normalize()
			}
		}
	case *carExceptRecord:
		if x != nil {
			x.normalize()
		}
	}
}

func (h *handler) exceptList(c *gin.Context) { h.tableList(c, exceptRecordSpec) }
func (h *handler) exceptListCarNo(c *gin.Context) {
	if isBlank(queryParam(c, "carNo")) {
		setQueryOverride(c, "carNo", "-1")
	}
	h.tableList(c, exceptRecordSpec)
}

func (h *handler) exceptListCarOrgID(c *gin.Context) {
	if isBlank(queryParam(c, "epsId")) {
		setQueryOverride(c, "epsId", "-1")
	}
	h.tableList(c, exceptRecordSpecNew)
}

func (h *handler) exceptListExceptID(c *gin.Context) {
	if isBlank(queryParam(c, "exceptIds")) {
		setQueryOverride(c, "exceptIds", "-1")
	}
	h.tableList(c, exceptRecordSpec)
}

func (h *handler) exceptExportOrgID(c *gin.Context) {
	if isBlank(queryParam(c, "epsId")) {
		setQueryOverride(c, "epsId", "-1")
	}
	h.exceptExportWithSpec(c, exceptRecordSpecNew)
}

func (h *handler) exceptExport(c *gin.Context) { h.exceptExportWithSpec(c, exceptRecordSpec) }

// exceptExportWithSpec 输出 exportCarExcept.xlsx（标题行 + 明细行）。
func (h *handler) exceptExportWithSpec(c *gin.Context, spec *tableSpec) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	dest := newSliceOf(&carExceptRecord{})
	if _, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: spec.selectSQL + spec.selectSuffix,
		FromSQL:   spec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   spec.orderBy,
	}, dest); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows := *(dest.(*[]*carExceptRecord))
	carTypes, _ := h.dictValueLabel(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictValueLabel(c.Request.Context(), "car_vehicle")
	escapedTypes, _ := h.dictValueLabel(c.Request.Context(), "escaped_type")
	statuses, _ := h.dictValueLabel(c.Request.Context(), "supplementary_status")
	cols := []exportCol{{Title: "车牌号"}, {Title: "车型"}, {Title: "车种"}, {Title: "轴数"},
		{Title: "入口站"}, {Title: "入口时间"}, {Title: "出口站"}, {Title: "出口时间"},
		{Title: "应缴金额（元）"}, {Title: "收费金额（元）"}, {Title: "差额（元）"}, {Title: "逃费类型"},
		{Title: "状态"}, {Title: "录入单位及用户"}, {Title: "录入时间"}, {Title: "备注"}}
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		status := statuses[strOf(row.Status)]
		if status == "" {
			status = strOf(row.Status)
		}
		out = append(out, []any{row.CarNo, carTypes[strOf(row.CarType)], carVehicles[strOf(row.CarVehicle)],
			plainValue(row.CarNum), row.InStation, plainValue(row.InTime), row.OutStation,
			plainValue(row.OutTime), plainValue(row.TotalAmount), plainValue(row.ChargeAmount),
			plainValue(row.DifAmount), escapedTypes[strOf(row.EscapedType)], status, row.CreateInfo,
			plainValue(row.CreateTime), row.Remark})
	}
	data, err := buildWorkbook("异常车辆流水", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "exportCarExcept.xlsx", data)
}

// exceptRecordCount 对应 GET /exceptRecordCount。
func (h *handler) exceptRecordCount(c *gin.Context) {
	carNo := argString(c, "carNo")
	if carNo == "" {
		carNo = "-1"
	}
	sqlStr := "SELECT t.car_no, count(1) AS except_num, round(sum(t.dif_amount), 2) AS except_amount, " +
		"round(sum(t.total_amount), 2) AS total_amount, round(sum(t.charge_amount), 2) AS charge_amount " +
		"FROM car_except_record t WHERE t.del_flag = '0' AND t.car_no = ?"
	args := []any{carNo}
	if status := argString(c, "status"); status != "" {
		sqlStr += " AND t.status = ?"
		args = append(args, status)
	}
	sqlStr += " GROUP BY t.car_no"
	var rows []struct {
		CarNo        string   `gorm:"column:car_no"`
		ExceptNum    *int64   `gorm:"column:except_num"`
		ExceptAmount *float64 `gorm:"column:except_amount"`
		TotalAmount  *float64 `gorm:"column:total_amount"`
		ChargeAmount *float64 `gorm:"column:charge_amount"`
	}
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&rows).Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(rows) == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	row := rows[0]
	dest := &carExceptRecord{
		CarNo: strPtr(row.CarNo), ExceptNum: row.ExceptNum, ExceptAmount: row.ExceptAmount,
		TotalAmount: row.TotalAmount, ChargeAmount: row.ChargeAmount,
	}
	dest.normalize()
	web.JSON(c, web.SuccessData(dest))
}

// exceptGetConfirmID 对应 GET /getConfirmId/{id}（查不到返回 "-1"）。
func (h *handler) exceptGetConfirmID(c *gin.Context) {
	confirms := h.confimFreeByExceptIDs(c, []string{c.Param("id")})
	confirmID := "-1"
	if len(confirms) > 0 {
		confirmID = strOf(confirms[0].ID)
	}
	result := web.Success()
	result.Put("data", confirmID)
	web.JSON(c, result)
}

func (h *handler) exceptGet(c *gin.Context) { h.tableGet(c, exceptRecordSpec) }

// exceptSave 对应 saveCarExceptRecord：区间查重 -> 新增/修改 -> 回写重点车辆。
func (h *handler) exceptSave(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	id := bodyString(body, "id")
	inTime := bodyString(body, "inTime")
	outTime := bodyString(body, "outTime")
	carNo := isNull(bodyString(body, "carNo"))
	if inTime != "" && outTime != "" {
		sqlStr := "SELECT COUNT(1) FROM car_except_record t WHERE t.del_flag = '0'"
		var args []any
		if id != "" {
			sqlStr += " AND t.id != ?"
			args = append(args, id)
		}
		sqlStr += " AND t.out_time >= ? AND t.in_time <= ? AND t.car_no = ?"
		args = append(args, inTime, outTime, carNo)
		var count int64
		if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&count).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if count > 0 {
			web.JSON(c, web.ErrorMsg("录入区间时间重复！"))
			return
		}
	}
	cols := pickColumns(body, carExceptRecordColumns)
	if id != "" {
		withUpdateAudit(c, cols)
		if _, err := h.updateRow(c.Request.Context(), carExceptRecordTable, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		cols["status"] = "0"
		id = newUUID()
		cols["id"] = id
		h.withInsertAudit(c, cols)
		if err := h.insertRow(c.Request.Context(), carExceptRecordTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	if carNo != "" {
		h.saveCarExcept(c, carNo)
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// saveCarExcept 按车牌重算逃费类型/金额并回写 car_info（只更新已存在车牌）。
func (h *handler) saveCarExcept(c *gin.Context, carNo string) {
	h.saveCarExceptContext(c.Request.Context(), carNo)
}

func (h *handler) saveCarExceptContext(ctx context.Context, carNo string) {
	sqlStr := "SELECT t.car_no, count(1) AS except_num, round(sum(t.dif_amount), 2) AS except_amount, " +
		"round(sum(t.total_amount), 2) AS total_amount, round(sum(t.charge_amount), 2) AS charge_amount, " +
		"group_concat(distinct t.escaped_type SEPARATOR ',') AS escaped_type " +
		"FROM car_except_record t WHERE t.del_flag = '0' AND t.car_no = ? GROUP BY t.car_no"
	var rows []struct {
		CarNo        string   `gorm:"column:car_no"`
		ExceptAmount *float64 `gorm:"column:except_amount"`
		EscapedType  string   `gorm:"column:escaped_type"`
	}
	if err := h.app.DB.WithContext(ctx).Raw(sqlStr, carNo).Scan(&rows).Error; err != nil {
		return
	}
	for _, row := range rows {
		if isBlank(row.CarNo) {
			continue
		}
		var carID string
		if err := h.app.DB.WithContext(ctx).Table(carInfoTable).
			Select("id").Where("del_flag = '0' AND car_no = ?", row.CarNo).Limit(1).
			Scan(&carID).Error; err != nil || carID == "" {
			continue
		}
		_ = h.app.DB.WithContext(ctx).Table(carInfoTable).
			Where("id = ? AND del_flag = '0'", carID).
			Updates(map[string]any{"escaped_type": row.EscapedType, "escaped_amount": row.ExceptAmount}).Error
	}
}

// exceptDelete 对应 deleteCarExceptRecordByIds：有补缴记录则拒绝。
func (h *handler) exceptDelete(c *gin.Context) {
	ids := splitCSV(c.Param("ids"))
	var count int64
	if len(ids) > 0 {
		if confirms := h.confimFreeByExceptIDs(c, ids); len(confirms) > 0 {
			web.JSON(c, web.ErrorMsg("删除失败，车辆异常流水已补缴！"))
			return
		}
		var err error
		count, err = h.softDeleteByIDs(c.Request.Context(), carExceptRecordTable, ids)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	web.JSON(c, web.SuccessData(count))
}

// exceptImport 对应 POST /import（importCarExcept.xlsx）。
func (h *handler) exceptImport(c *gin.Context) {
	fileHeader, err := c.FormFile("file")
	if err != nil {
		web.JSON(c, web.ErrorMsg("请上传Excel文件(.xlsx)"))
		return
	}
	if !strings.HasSuffix(strings.ToLower(fileHeader.Filename), ".xlsx") {
		web.JSON(c, web.ErrorMsg("请上传Excel文件(.xlsx)"))
		return
	}
	f, err := fileHeader.Open()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	defer func() { _ = f.Close() }()
	rows, err := readXlsxRows(f)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(rows) < 4 || !looksLikeExceptHeader(rows[1]) && !looksLikeExceptHeader(rows[2]) {
		web.JSON(c, web.ErrorMsg("导入失败,模板不正确,请下载对应的模板！"))
		return
	}

	type importError struct {
		RowNum   int    `json:"rowNum"`
		ColName  string `json:"colName"`
		ErrorMsg string `json:"errorMsg"`
	}
	var errList []importError
	cell := func(row []string, idx int) string {
		if idx < len(row) {
			return strings.TrimSpace(row[idx])
		}
		return ""
	}
	carTypeChange, _ := h.dictLabelValue(c.Request.Context(), "car_type_change")
	escapedTypeMap, _ := h.dictLabelValue(c.Request.Context(), "escaped_type")
	plateColorMap, _ := h.dictLabelValue(c.Request.Context(), "plate_color")
	tollMap := map[string]string{}
	{
		var tolls []struct {
			TollName string `gorm:"column:toll_name"`
			TollCode string `gorm:"column:toll_code"`
		}
		_ = h.app.DB.WithContext(c.Request.Context()).
			Table("ods_szdn_toll").Select("toll_name, toll_code").Scan(&tolls).Error
		for _, toll := range tolls {
			tollMap[isNull(toll.TollName)] = isNull(toll.TollCode)
		}
	}
	carMap := map[string]struct {
		ID     string
		CarNum *int64
	}{}
	{
		var cars []struct {
			ID     string `gorm:"column:id"`
			CarNo  string `gorm:"column:car_no"`
			CarNum *int64 `gorm:"column:car_num"`
		}
		_ = h.app.DB.WithContext(c.Request.Context()).Table(carInfoTable).
			Select("id, car_no, car_num").Where("del_flag = '0'").Scan(&cars).Error
		for _, car := range cars {
			carMap[isNull(car.CarNo)] = struct {
				ID     string
				CarNum *int64
			}{ID: car.ID, CarNum: car.CarNum}
		}
	}

	type addCarInfo struct {
		CarNo, PlateColor, CarType, CarVehicle string
	}
	var importList []*carExceptRecord
	var addCars []*addCarInfo
	addCarSet := map[string]struct{}{}
	for i := 3; i < len(rows); i++ {
		row := rows[i]
		rowNum := i
		outStation, outTimeStr, passType, carNoRaw := cell(row, 1), cell(row, 2), cell(row, 3), cell(row, 4)
		carTypeLabel, inStation, inTimeStr := cell(row, 5), cell(row, 7), cell(row, 8)
		backCol1, escapedTypeLabel := cell(row, 9), cell(row, 10)
		chargeStr, totalStr, remark := cell(row, 13), cell(row, 16), cell(row, 20)
		if carNoRaw == "" {
			errList = append(errList, importError{rowNum, "车牌", "车牌不能为空"})
			continue
		}
		if outTimeStr == "" || inTimeStr == "" {
			errList = append(errList, importError{rowNum, "时间", "通行时间不能为空"})
			continue
		}
		outTime, err1 := web.ParseDate(outTimeStr)
		inTime, err2 := web.ParseDate(inTimeStr)
		if err1 != nil || err2 != nil {
			errList = append(errList, importError{rowNum, "时间", "时间格式不正确"})
			continue
		}
		chargeAmount, err1 := strconv.ParseFloat(chargeStr, 64)
		totalAmount, err2 := strconv.ParseFloat(totalStr, 64)
		if chargeStr == "" || totalStr == "" || err1 != nil || err2 != nil {
			errList = append(errList, importError{rowNum, "缴费金额", "缴费金额格式不正确"})
			continue
		}
		if totalAmount < chargeAmount {
			errList = append(errList, importError{rowNum, "缴费金额", "收费金额不能大于应缴金额"})
			continue
		}
		if inTime.After(outTime) {
			errList = append(errList, importError{rowNum, "时间", "入口时间大于出口时间，请确认!"})
			continue
		}

		// 车牌号_车牌颜色
		carNo := carNoRaw
		plateColor := ""
		if idx := strings.Index(carNoRaw, "_"); idx > -1 {
			parts := strings.Split(carNoRaw, "_")
			if len(parts) > 1 {
				plateColor = parts[1]
			}
			carNo = parts[0]
		}
		if plateColor != "" {
			if value, ok := plateColorMap[plateColor]; ok {
				plateColor = value
			}
		}
		item := &carExceptRecord{
			CarNo: strPtr(carNo), PassType: strPtr(passType), BackCol1: strPtr(backCol1),
			InStationID: strPtr(tollMap[inStation]), OutStationID: strPtr(tollMap[outStation]),
			TotalAmount: &totalAmount, ChargeAmount: &chargeAmount,
			Remark: strPtr(remark),
		}
		item.InTime = ptrDateTime(inTime)
		item.OutTime = ptrDateTime(outTime)
		item.InStation = strPtr(inStation)
		item.OutStation = strPtr(outStation)
		if carTypeLabel != "" {
			if value, ok := carTypeChange[carTypeLabel]; ok {
				item.CarType = strPtr(value)
			} else {
				item.CarType = strPtr(carTypeLabel)
			}
		}
		item.CarVehicle = strPtr(carVehicleOf(strOf(item.CarType)))
		if escapedTypeLabel != "" {
			if value, ok := escapedTypeMap[escapedTypeLabel]; ok {
				item.EscapedType = strPtr(value)
			} else {
				errList = append(errList, importError{rowNum, "逃费类型", escapedTypeLabel + " 逃费类型不存在,请在字典菜单维护！"})
				continue
			}
		}
		if car, ok := carMap[carNo]; ok {
			item.CarID = strPtr(car.ID)
			if item.CarNum == nil {
				item.CarNum = car.CarNum
			}
		} else if _, seen := addCarSet[carNo]; !seen {
			addCarSet[carNo] = struct{}{}
			addCars = append(addCars, &addCarInfo{
				CarNo: carNo, PlateColor: plateColor, CarType: strOf(item.CarType), CarVehicle: strOf(item.CarVehicle),
			})
		}
		diff := totalAmount - chargeAmount
		item.DifAmount = &diff
		importList = append(importList, item)
		if len(errList) > 100 {
			break
		}
	}

	if len(errList) > 0 {
		web.JSON(c, web.ErrorData("error", errList))
		return
	}

	// 新增车辆（走 saveCarInfo：车牌重复时会被拒绝，与 Java 一致）。
	for _, addCar := range addCars {
		h.insertCarInfoQuiet(c, &carInfo{
			CarNo:      strPtr(addCar.CarNo),
			PlateColor: strPtr(addCar.PlateColor),
			CarType:    strPtr(addCar.CarType),
			CarVehicle: strPtr(addCar.CarVehicle),
		})
	}

	now := time.Now()
	userID := currentUserID(c)
	for _, item := range importList {
		// 根据车牌号和入口时间判断是否已存在
		var existingID string
		_ = h.app.DB.WithContext(c.Request.Context()).Table(carExceptRecordTable).
			Select("id").Where("del_flag = '0' AND car_no = ? AND in_time = ?", item.CarNo, item.InTime).
			Limit(1).Scan(&existingID).Error
		cols := map[string]any{
			"car_id": item.CarID, "car_no": item.CarNo, "car_type": item.CarType,
			"car_vehicle": item.CarVehicle, "pass_type": item.PassType,
			"in_station_id": item.InStationID, "in_station": item.InStation, "in_time": item.InTime,
			"out_station_id": item.OutStationID, "out_station": item.OutStation, "out_time": item.OutTime,
			"total_amount": item.TotalAmount, "charge_amount": item.ChargeAmount, "dif_amount": item.DifAmount,
			"escaped_type": item.EscapedType, "back_col1": item.BackCol1, "remark": item.Remark,
			"update_by": userID, "update_time": now,
		}
		if existingID != "" {
			if _, err := h.updateRow(c.Request.Context(), carExceptRecordTable, existingID, cols); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
			item.ID = strPtr(existingID)
			continue
		}
		item.ID = strPtr(newUUID())
		cols["id"] = strOf(item.ID)
		cols["status"] = "0"
		cols["del_flag"] = "0"
		cols["create_by"] = userID
		cols["create_time"] = now
		if err := h.insertRow(c.Request.Context(), carExceptRecordTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		h.saveCarExcept(c, strOf(item.CarNo))
	}
	web.JSON(c, web.SuccessFull("数据导入成功", importList))
}

// looksLikeExceptHeader 校验模板第二/第三行表头。
func looksLikeExceptHeader(row []string) bool {
	if len(row) < 14 {
		return false
	}
	return strings.TrimSpace(row[1]) == "出口收费站" && strings.TrimSpace(row[4]) == "车牌"
}

// carVehicleOf 对应承运车型 -> 车种（1/2/3，未知 99）。
func carVehicleOf(carType string) string {
	switch carType {
	case "1", "2", "3", "4":
		return "1"
	case "11", "12", "13", "14", "15", "16":
		return "2"
	case "21", "22", "23", "24", "25", "26":
		return "3"
	default:
		return "99"
	}
}

// insertCarInfoQuiet 用于导入时补建重点车辆（忽略重复）。
func (h *handler) insertCarInfoQuiet(c *gin.Context, car *carInfo) {
	var count int64
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(
		"SELECT COUNT(1) FROM car_info WHERE del_flag = '0' AND car_no = ?", car.CarNo).Scan(&count).Error
	if count > 0 {
		return
	}
	userID := currentUserID(c)
	epsID := currentEpsID(c)
	now := time.Now()
	_ = h.app.DB.WithContext(c.Request.Context()).Table(carInfoTable).Create(map[string]any{
		"id": newUUID(), "car_no": car.CarNo, "plate_color": car.PlateColor,
		"car_type": car.CarType, "car_vehicle": car.CarVehicle, "escaped_amount": 0,
		"del_flag": "0", "create_by": userID, "create_time": now,
		"update_by": userID, "update_time": now, "eps_id": epsID,
	}).Error
}
