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
	"gorm.io/gorm"

	"car-monit-go/internal/middleware"
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
	// JAVA 对照: CarExceptRecordController —— 该控制器没有 @PreAuthorize，只有 @Log。
	auth.GET("/manager/exceptrecord/list", h.exceptList)
	auth.GET("/manager/exceptrecord/listCarNo", h.exceptListCarNo)
	auth.GET("/manager/exceptrecord/listCarOrgId", h.exceptListCarOrgID)
	auth.GET("/manager/exceptrecord/exportOrgId",
		middleware.OperLog(reg.App, "异常车辆流水", middleware.BusinessExport), h.exceptExportOrgID)
	auth.GET("/manager/exceptrecord/listExceptId", h.exceptListExceptID)
	auth.GET("/manager/exceptrecord/exceptRecordCount", h.exceptRecordCount)
	auth.GET("/manager/exceptrecord/export",
		middleware.OperLog(reg.App, "异常车辆流水", middleware.BusinessExport), h.exceptExport)
	auth.GET("/manager/exceptrecord/getConfirmId/:id", h.exceptGetConfirmID)
	auth.GET("/manager/exceptrecord/:id", h.exceptGet)
	auth.POST("/manager/exceptrecord",
		middleware.OperLog(reg.App, "异常车辆流水", middleware.BusinessInsert), h.exceptSave)
	auth.PUT("/manager/exceptrecord",
		middleware.OperLog(reg.App, "异常车辆流水", middleware.BusinessUpdate), h.exceptSave)
	auth.DELETE("/manager/exceptrecord/:ids",
		middleware.OperLog(reg.App, "异常车辆流水", middleware.BusinessDelete), h.exceptDelete)
	auth.POST("/manager/exceptrecord/import",
		middleware.OperLog(reg.App, "新增流水导入", middleware.BusinessImport), h.exceptImport)
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
	// JAVA 对照: templates/export/exportCarExcept.xlsx —— 三行静态表头（报表标题、列名、副表头）
	// + 21 列。控制器逐行 setSort(i+1)、setCarNoQuery("")，模板里凡是引用 carNoQuery 的格子
	// 都是空串；车型/车种/逃费类型用 containsKey 守卫（未命中保留原码，与其它模板导出不同）。
	titleRow := []any{"少交高速公路通行费流水明细表"}
	headerRow := []any{"序号", "出口收费站", "出口时间", "通行PASSID", "车牌", "交易车型", "车种",
		"入口站", "入口时间", "漏交通行费类型", "", "交易金额", "", "", "应交金额", "", "",
		"实际追交金额", "", "", "备注"}
	subRow := []any{"", "", "", "", "", "", "", "", "", "一级类型", "二级类型", "省内", "省外", "小计",
		"省内", "省外", "小计", "省内", "省外", "小计", ""}
	out := make([][]any, 0, len(rows))
	for i, row := range rows {
		out = append(out, []any{i + 1, row.OutStation, plainValue(row.OutTime), row.PassType, row.CarNo,
			dictOrRaw(carTypes, strOf(row.CarType)), dictOrRaw(carVehicles, strOf(row.CarVehicle)),
			row.InStation, plainValue(row.InTime), "", dictOrRaw(escapedTypes, strOf(row.EscapedType)),
			"", "", moneyText(row.ChargeAmount), "", "", moneyText(row.TotalAmount), "", "",
			moneyText(row.DifAmount), row.Remark})
	}
	data, err := buildStaticWorkbook("异常车辆流水", [][]any{titleRow, headerRow, subRow}, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "exportCarExcept.xlsx", data)
}

// dictOrRaw 复刻 Java 的 containsKey 守卫：命中字典取标签，未命中保留原值。
func dictOrRaw(dict map[string]string, key string) string {
	if label, ok := dict[key]; ok {
		return label
	}
	return key
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

// exceptTimeOverlap 对应 CarExceptRecordMapper.isExitsTime：同车牌、区间与 [inTime, outTime]
// 重叠、且不是自己那一行的记录数。id/车牌为空时对应的条件整个不下推（XML 的 <if>）。
func (h *handler) exceptTimeOverlap(ctx context.Context, id, carNo string, inTime, outTime any) (bool, error) {
	sqlStr := "SELECT COUNT(1) FROM car_except_record t WHERE t.del_flag = '0'"
	var args []any
	if id != "" {
		sqlStr += " AND t.id != ?"
		args = append(args, id)
	}
	sqlStr += " AND t.out_time >= ? AND t.in_time <= ?"
	args = append(args, inTime, outTime)
	if carNo != "" {
		sqlStr += " AND t.car_no = ?"
		args = append(args, carNo)
	}
	var count int64
	if err := h.app.DB.WithContext(ctx).Raw(sqlStr, args...).Scan(&count).Error; err != nil {
		return false, err
	}
	return count > 0, nil
}

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
		dup, err := h.exceptTimeOverlap(c.Request.Context(), id, carNo, inTime, outTime)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if dup {
			web.JSON(c, web.ErrorMsg("录入区间时间重复！"))
			return
		}
	}
	cols := pickColumns(body, carExceptRecordColumns)
	ctx := c.Request.Context()
	// JAVA 对照: CarExceptRecordServiceImpl.saveCarExceptRecord 带 @Transactional(rollbackFor = Exception.class)——
	// 流水写入与 car_info 逃费金额回写必须同属一个事务。
	err = h.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if id != "" {
			withUpdateAudit(c, cols)
			if _, err := updateRowTx(tx, carExceptRecordTable, id, cols); err != nil {
				return err
			}
		} else {
			cols["status"] = "0"
			id = newUUID()
			cols["id"] = id
			h.withInsertAudit(c, cols)
			if err := insertRowTx(tx, carExceptRecordTable, cols); err != nil {
				return err
			}
		}
		if carNo != "" {
			return saveCarExceptTx(tx, carNo)
		}
		return nil
	})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// saveCarExcept 按车牌重算逃费类型/金额并回写 car_info（只更新已存在车牌）。
func (h *handler) saveCarExcept(ctx context.Context, carNo string) error {
	return saveCarExceptTx(h.app.DB.WithContext(ctx), carNo)
}

// saveCarExceptTx 是 saveCarExcept 的事务版本。
func saveCarExceptTx(db *gorm.DB, carNo string) error {
	sqlStr := "SELECT t.car_no, count(1) AS except_num, round(sum(t.dif_amount), 2) AS except_amount, " +
		"round(sum(t.total_amount), 2) AS total_amount, round(sum(t.charge_amount), 2) AS charge_amount, " +
		"group_concat(distinct t.escaped_type SEPARATOR ',') AS escaped_type " +
		"FROM car_except_record t WHERE t.del_flag = '0' AND t.car_no = ? GROUP BY t.car_no"
	var rows []struct {
		CarNo        string   `gorm:"column:car_no"`
		ExceptAmount *float64 `gorm:"column:except_amount"`
		EscapedType  string   `gorm:"column:escaped_type"`
	}
	if err := db.Raw(sqlStr, carNo).Scan(&rows).Error; err != nil {
		return err
	}
	for _, row := range rows {
		if isBlank(row.CarNo) {
			continue
		}
		var carID string
		if err := db.Table(carInfoTable).
			Select("id").Where("del_flag = '0' AND car_no = ?", row.CarNo).Limit(1).
			Scan(&carID).Error; err != nil {
			return err
		}
		if carID == "" {
			continue
		}
		if err := db.Table(carInfoTable).
			Where("id = ? AND del_flag = '0'", carID).
			Updates(map[string]any{"escaped_type": row.EscapedType, "escaped_amount": row.ExceptAmount}).Error; err != nil {
			return err
		}
	}
	return nil
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
	// JAVA 对照: 不是 multipart / 缺 file part 的消息由 Spring 给出；
	// 后缀不是 .xlsx 才是 ImportSysUtil 的中文提示；再往后 0 字节与非法格式的消息来自 POI。
	fileHeader, err := web.FormFile(c, "file")
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
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
	if msg := web.CheckUpload(fileHeader.Size, f, notWorkbookMsg, ole2IsNotXSSFMsg); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	rows, err := readXlsxRows(f)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// JAVA 对照: colVdaExcel08 先拿 initListTwo 的表头比第 2 行，再比第 3 行；
	// 两处传的是同一个列表（colsNameThree 也是 initListTwo，initListThree 从未被用到），
	// 所以真实模板只有第 2 行能命中，第 3 行的子表头必然比不过。
	headerNames := importColNames(exceptImportCols)
	if len(rows) < 4 || (!sameHeader(rows[1], headerNames) && !sameHeader(rows[2], headerNames)) {
		web.JSON(c, web.ErrorMsg("导入失败,模板不正确,请下载对应的模板！"))
		return
	}
	dataRows := collectImportRows(rows[3:]) // dataRtnExcel08(..., num=3)
	if len(dataRows) == 0 {
		web.JSON(c, web.ErrorMsg("导入失败,模板excel没有数据可以导入，请确定！"))
		return
	}

	var errList []importError
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
	for i, row := range dataRows {
		vals := importCells(row, len(exceptImportCols))
		validateImportRow(&errList, exceptImportCols, i, vals)
		if len(errList) == 0 {
			importList = append(importList, parseExceptImportRow(vals))
		}
		if len(errList) > 100 {
			break
		}
	}

	// JAVA 对照: 控制器的第二段循环，只在没有格式错时开始，错误行号同样是数据行序号 +2。
	if len(errList) == 0 {
		for i, item := range importList {
			carType := isNull(item.CarType)
			if carType != "" {
				if value, ok := carTypeChange[carType]; ok {
					item.CarType = strPtr(value)
				}
			}
			// 车种不取表格里那一列，只由（转换后的）车型推导，推不出来就是 99。
			item.CarVehicle = strPtr(carVehicleOf(isNull(item.CarType)))

			// 车牌号_车牌颜色
			carNoRaw := isNull(item.CarNo)
			carNo, plateColor := carNoRaw, ""
			if strings.Contains(carNoRaw, "_") {
				parts := strings.Split(carNoRaw, "_")
				if len(parts) > 1 {
					plateColor = parts[1]
				}
				carNo = parts[0]
			}
			item.CarNo = strPtr(carNo)
			if plateColor != "" {
				if value, ok := plateColorMap[plateColor]; ok {
					plateColor = value
				}
			}
			if carNo != "" {
				if car, ok := carMap[carNo]; ok {
					item.CarID = strPtr(car.ID)
					item.CarNum = car.CarNum
				} else if _, seen := addCarSet[carNo]; !seen {
					addCarSet[carNo] = struct{}{}
					addCars = append(addCars, &addCarInfo{
						CarNo: carNo, PlateColor: plateColor,
						CarType: isNull(item.CarType), CarVehicle: isNull(item.CarVehicle),
					})
				}
			}
			escapedType := isNull(item.EscapedType)
			if escapedType != "" {
				if value, ok := escapedTypeMap[escapedType]; ok {
					item.EscapedType = strPtr(value)
				} else {
					errList = append(errList, importErrorAt(i, "逃费类型", escapedType+" 逃费类型不存在,请在字典菜单维护！"))
				}
			}
			inStation := isNull(item.InStation)
			if inStation != "" {
				// 查不到收费站时 Java 不动 inStationId，列保持 null（MP 的 NOT_NULL 策略）。
				if code, ok := tollMap[inStation]; ok {
					item.InStationID = strPtr(code)
				}
			}
			outStation := isNull(item.OutStation)
			if outStation != "" {
				if code, ok := tollMap[outStation]; ok {
					item.OutStationID = strPtr(code)
				}
			}
			if item.TotalAmount != nil && item.ChargeAmount != nil && *item.TotalAmount < *item.ChargeAmount {
				errList = append(errList, importErrorAt(i, "缴费金额", "收费金额不能大于应缴金额"))
			}
			if item.InTime != nil && item.OutTime != nil && item.InTime.After(item.OutTime.Time) {
				errList = append(errList, importErrorAt(i, "时间", "入口时间大于出口时间，请确认!"))
			}
			if len(errList) > 100 {
				break
			}
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

	userID := currentUserID(c)
	epsID := currentEpsID(c)
	tenantID := currentTenantID(c)
	for _, item := range importList {
		// JAVA 对照: 控制器第三段先算 difAmount，再按 car_no + in_time 找已有记录决定新增还是修改。
		if item.TotalAmount != nil && item.ChargeAmount != nil {
			diff := *item.TotalAmount - *item.ChargeAmount
			item.DifAmount = &diff
		}
		var existingID string
		_ = h.app.DB.WithContext(c.Request.Context()).Table(carExceptRecordTable).
			Select("id").Where("del_flag = '0' AND car_no = ? AND in_time = ?", item.CarNo, item.InTime).
			Limit(1).Scan(&existingID).Error
		if existingID != "" {
			item.ID = strPtr(existingID)
		}
		// JAVA 对照: saveCarExceptRecord 的区间查重命中就 return error，控制器忽略返回值，
		// 表现为「这一行不写库、响应里照样带着它」。
		if item.InTime != nil && item.OutTime != nil {
			dup, err := h.exceptTimeOverlap(c.Request.Context(), strOf(item.ID), isNull(item.CarNo), item.InTime, item.OutTime)
			if err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
			if dup {
				continue
			}
		}
		cols := mpNonNullCols(map[string]any{
			"car_id": item.CarID, "car_no": item.CarNo, "car_type": item.CarType,
			"car_vehicle": item.CarVehicle, "car_num": item.CarNum, "pass_type": item.PassType,
			"in_station_id": item.InStationID, "in_station": item.InStation, "in_time": item.InTime,
			"out_station_id": item.OutStationID, "out_station": item.OutStation, "out_time": item.OutTime,
			"total_amount": item.TotalAmount, "charge_amount": item.ChargeAmount, "dif_amount": item.DifAmount,
			"escaped_type": item.EscapedType, "back_col1": item.BackCol1, "remark": item.Remark,
		})
		if strOf(item.ID) != "" {
			// updateFill：MP 会把 updateBy/updateTime 同时写回实体，所以响应里也有。
			now := auditNow()
			cols["update_by"] = userID
			cols["update_time"] = now
			if _, err := h.updateRow(c.Request.Context(), carExceptRecordTable, strOf(item.ID), cols); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
			item.UpdateBy = &userID
			item.UpdateTime = ptrDateTime(now)
		} else {
			// insertFill：只填 createBy/createTime/epsId/tenantId，不填 updateBy/updateTime。
			item.ID = strPtr(newUUID())
			now := auditNow()
			cols["id"] = strOf(item.ID)
			cols["status"] = "0"
			cols["del_flag"] = "0"
			cols["create_by"] = userID
			cols["create_time"] = now
			cols["eps_id"] = epsID
			cols["tenant_id"] = tenantID
			if err := h.insertRow(c.Request.Context(), carExceptRecordTable, cols); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
			// Java 在 insert 前 setStatus("0")，而 delFlag 只靠列默认值，实体里一直是 null。
			item.Status = strPtr("0")
			item.CreateBy = &userID
			item.CreateTime = ptrDateTime(now)
			item.EpsID = &epsID
			item.TenantID = &tenantID
		}
		if isNull(item.CarNo) != "" {
			// 导入是逐行累积错误的批处理：单行车牌回写失败只记录告警，
			// 不影响其它行的导入结果（Java 侧这里的异常同样被 ImportUtil 逐行捕获）。
			if err := h.saveCarExcept(c.Request.Context(), isNull(item.CarNo)); err != nil {
				h.app.Log.Warn("导入后回写车辆逃费金额失败", "carNo", isNull(item.CarNo), "err", err)
			}
		}
	}
	web.JSON(c, web.SuccessFull("数据导入成功", importList))
}

// parseExceptImportRow 对应 JSONObject(objMap).toJavaObject(CarExceptRecord.class)：
// 只有 initListTwo 给了属性的列会进对象，文本列空串不是 null，数字/时间列空值转 null。
func parseExceptImportRow(vals []string) *carExceptRecord {
	item := &carExceptRecord{
		OutStation:  strPtr(vals[1]),
		PassType:    strPtr(vals[3]),
		CarNo:       strPtr(vals[4]),
		CarType:     strPtr(vals[5]),
		CarVehicle:  strPtr(vals[6]),
		InStation:   strPtr(vals[7]),
		BackCol1:    strPtr(vals[9]),
		EscapedType: strPtr(vals[10]),
		Remark:      strPtr(vals[20]),
		// JAVA 对照: 域对象的字段初始值，新增/修改分支都带着它序列化出去。
		SupplementaryStatus: strPtr("0"),
	}
	// JAVA 对照: fastjson 按 JVM 默认时区把这段文本解析成 Date，Go 这边必须用
	// ParseInLocation(time.Local)（web.ParseDate），否则 DSN 的 loc=Local 会把钟点平移。
	if t, err := web.ParseDate(vals[2]); err == nil {
		item.OutTime = ptrDateTime(t)
	}
	if t, err := web.ParseDate(vals[8]); err == nil {
		item.InTime = ptrDateTime(t)
	}
	if vals[13] != "" {
		if v, err := strconv.ParseFloat(vals[13], 64); err == nil {
			item.ChargeAmount = &v
		}
	}
	if vals[16] != "" {
		if v, err := strconv.ParseFloat(vals[16], 64); err == nil {
			item.TotalAmount = &v
		}
	}
	return item
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
