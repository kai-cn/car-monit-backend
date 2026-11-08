// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml
// 类/职责: 可疑车辆（car_suspicious / car_suspicious_back）控制器
// 对应 Go 文件: internal/modules/manager/car_suspicious.go
//
// DIFF: Java 的 ASSIGN_ID（19 位雪花号）在 Go 用 UnixNano 生成同等长度的数字字符串。
// DIFF: cherkCarSuspicious 在 isExcept != "1" 且 checkList 为 null 时 Java 会 NPE；
// Go 侧不主动制造空指针，直接按「无核实明细」继续执行。
// DIFF: exportAbnormalPassage 的 Word 模板排版（含图片）无法逐字复刻，
// 这里生成只包含关键字段的 docx（附件流），文件名与下载行为保持一致。
package manager

import (
	"archive/zip"
	"bytes"
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/idgen"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

const (
	suspiciousNotFoundMessage = "可疑车俩不存在！"
	suspiciousPaidMessage     = "可疑车俩异常流水已追缴！"
	checkListEmptyMessage     = "车辆逃费类型列表不能为空！"
)

var suspiciousSpec = &tableSpec{
	table:        carSuspiciousTable,
	selectSQL:    carSuspiciousSelectColumns,
	detailSuffix: ",t.track_josn",
	orderBy:      "t.out_time desc,t.id",
	columns:      carSuspiciousColumns,
	prototype:    &carSuspicious{},
	conditions: []cond{
		eqCond("id", "t.id"), eqCond("plateColor", "t.plate_color"), eqCond("carNo", "t.car_no"),
		eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
		nullCond("carNum", "t.car_num"), eqCond("passType", "t.pass_type"),
		eqCond("inStationId", "t.in_station_id"), eqCond("inStation", "t.in_station"),
		nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
		eqCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
		eqCond("gantryStationId", "t.gantry_station_id"), eqCond("gantrytStation", "t.gantryt_station"),
		nullCond("gantryTime", "t.gantry_time"), eqCond("fileIds", "t.file_ids"),
		eqCond("outGantryStationId", "t.out_gantry_station_id"), eqCond("outGantrytStation", "t.out_gantryt_station"),
		nullCond("outGantryTime", "t.out_gantry_time"), eqCond("outFileIds", "t.out_file_ids"),
		eqCond("escapedType", "t.escaped_type"), likeCond("escapedTypeName", "t.escaped_type_name"),
		nullCond("escapedNum", "t.escaped_num"), eqCond("isExcept", "t.is_except"),
		eqCond("exceptRemark", "t.except_remark"), eqCond("exceptFileIds", "t.except_file_ids"),
		eqCond("checkStatus", "t.check_status"), eqCond("orgId", "t.org_id"),
		likeCond("orgName", "t.org_name"), eqCond("isWhite", "t.is_white"),
		eqCond("whiteRemark", "t.white_remark"), eqCond("whiteFileIds", "t.white_file_ids"),
		eqCond("roadCode", "t.road_code"), likeCond("roadName", "t.road_name"),
		likeCond("sectionCode", "t.track_names"), likeCond("sectionName", "t.track_names"),
		likeCond("trackNames", "t.track_names"), eqCond("trackId", "t.track_id"),
		eqCond("trackJosn", "t.track_josn"), eqCond("backCol1", "t.back_col1"),
		eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
		nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		likeCond("carNoQuery", "t.car_no"),
		dateTimeGe("applyTime1", "in_time"), dateTimeLe("applyTime2", "in_time"),
	},
}

func (h *handler) registerSuspicious(reg *router.Registry) {
	auth := reg.Authed
	// JAVA 对照: CarSuspiciousController.java:70-505。
	// 权限点与 @Log 逐条照抄；其中 /check 的 @PreAuthorize 在 Java 里被注释（第 426 行），
	// 因此 Go 侧也只挂 @Log 不挂 Perm。
	auth.GET("/manager/suspicious/list", middleware.Perm("manager:suspicious:list"), h.suspiciousList)
	auth.GET("/manager/suspicious/listCarNo", h.suspiciousListCarNo)
	auth.GET("/manager/suspicious/listFileCarNo", h.suspiciousListFileCarNo)
	auth.GET("/manager/suspicious/exportAbnormalPassage", h.suspiciousExportAbnormalPassage)
	auth.GET("/manager/suspicious/listAll", h.suspiciousListAll)
	auth.GET("/manager/suspicious/export", middleware.Perm("manager:suspicious:export"),
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessExport), h.suspiciousExport)
	auth.GET("/manager/suspicious/listHistory", middleware.Perm("manager:suspicious:list"),
		h.suspiciousListHistory)
	auth.GET("/manager/suspicious/history/:id", h.suspiciousHistoryGet)
	auth.GET("/manager/suspicious/exportHistory", middleware.Perm("manager:suspicious:export"),
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessExport), h.suspiciousExportHistory)
	auth.GET("/manager/suspicious/:id", h.suspiciousGet)
	auth.POST("/manager/suspicious", middleware.Perm("manager:suspicious:add"),
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessInsert), h.suspiciousSave)
	auth.PUT("/manager/suspicious", middleware.Perm("manager:suspicious:edit"),
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessUpdate), h.suspiciousSave)
	auth.PUT("/manager/suspicious/check",
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessUpdate), h.suspiciousCheck)
	auth.DELETE("/manager/suspicious/:ids", middleware.Perm("manager:suspicious:remove"),
		middleware.OperLog(reg.App, "可疑车辆", middleware.BusinessDelete), h.suspiciousDelete)
	auth.POST("/manager/suspicious/syncSuspiciousCarTask", h.suspiciousSync)
}

// suspiciousClause 对应控制器里的 sectionCode / code 规整。
func suspiciousClause(c *gin.Context) (string, []any) {
	sectionCode := deleteEnd(queryParam(c, "sectionCode"))
	if sectionCode != "" && strings.Contains(sectionCode, sectionAll) {
		setQuery(c, "sectionCode", "")
	}
	if isNotBlank(queryParam(c, "code")) {
		setQuery(c, "trackNames", queryParam(c, "code"))
	}
	return buildWhere(c, suspiciousSpec.prefix(), suspiciousSpec.conditions)
}

// setQuery 记录一个查询参数覆盖（空串表示视作没传）。
func setQuery(c *gin.Context, name, value string) {
	setQueryOverride(c, name, value)
}

func (h *handler) suspiciousList(c *gin.Context) {
	clause, args := suspiciousClause(c)
	h.respondList(c, suspiciousSpec, clause, args)
}

func (h *handler) suspiciousListAll(c *gin.Context) {
	clause, args := buildWhere(c, suspiciousSpec.prefix(), suspiciousSpec.conditions)
	h.respondList(c, suspiciousSpec, clause, args)
}

func (h *handler) suspiciousListCarNo(c *gin.Context) {
	if isBlank(queryParam(c, "carNo")) {
		setQueryOverride(c, "carNo", "-1")
	}
	clause, args := buildWhere(c, suspiciousSpec.prefix(), suspiciousSpec.conditions)
	h.respondList(c, suspiciousSpec, clause, args)
}

// suspiciousListFileCarNo 对应 GET /listFileCarNo：逐行重载核实明细并汇总金额。
func (h *handler) suspiciousListFileCarNo(c *gin.Context) {
	if isBlank(queryParam(c, "carNo")) {
		setQueryOverride(c, "carNo", "-1")
	}
	setQueryOverride(c, "isExcept", "1")
	setQueryOverride(c, "checkStatus", "1")
	clause, args := buildWhere(c, suspiciousSpec.prefix(), suspiciousSpec.conditions)
	dest := newSliceOf(&carSuspicious{})
	page := web.PageAlways(c)
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: suspiciousSpec.selectSQL,
		FromSQL:   suspiciousSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderFor(suspiciousSpec.orderBy, page),
		Page:      page,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	escapedMap, _ := h.dictValueLabel(c.Request.Context(), "escaped_type")
	out := make([]*carSuspicious, 0)
	for _, vo := range *(dest.(*[]*carSuspicious)) {
		detail := h.suspiciousDetail(c, strOf(vo.ID), carSuspiciousTable)
		if detail == nil {
			continue
		}
		if detail.CheckList != nil {
			charge, totalAmount, dif := 0.0, 0.0, 0.0
			for _, check := range detail.CheckList {
				if check.ChargeAmount != nil {
					charge += *check.ChargeAmount
				}
				if check.TotalAmount != nil {
					totalAmount += *check.TotalAmount
				}
				if check.DifAmount != nil {
					dif += *check.DifAmount
				}
			}
			chargeStr := strconv.FormatFloat(charge, 'f', -1, 64)
			totalStr := strconv.FormatFloat(totalAmount, 'f', -1, 64)
			difStr := strconv.FormatFloat(dif, 'f', -1, 64)
			detail.ChargeAmount = &chargeStr
			detail.TotalAmount = &totalStr
			detail.DifAmount = &difStr
			var names []string
			for _, part := range splitCSV(deleteEnd(detail.EscapedType)) {
				if label, ok := escapedMap[part]; ok {
					names = append(names, label)
				}
			}
			if len(names) > 0 {
				// Java 这里**没有** deleteEnd，保留尾逗号
				detail.EscapedTypeName = strPtr(strings.Join(names, ",") + ",")
			}
		}
		out = append(out, detail)
	}
	web.JSON(c, web.Table(out, total))
}

// suspiciousDetail 对应 selectCarSuspiciousById：checkList + trailList。
func (h *handler) suspiciousDetail(c *gin.Context, id, table string) *carSuspicious {
	dest := &carSuspicious{}
	sqlStr := "SELECT " + suspiciousSpec.selectSQL + suspiciousSpec.detailSuffix + " FROM " + table + " t WHERE t.id = ?"
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, id).Scan(dest)
	if tx.Error != nil || tx.RowsAffected == 0 {
		return nil
	}
	checks := newSliceOf(&carSuspiciousCheck{})
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(
		"SELECT "+carSuspiciousCheckSelectColumns+" FROM car_suspicious_check t WHERE t.del_flag = '0' AND t.car_id = ? ORDER BY t.create_time,t.id",
		id).Scan(checks)
	dest.CheckList = *(checks.(*[]*carSuspiciousCheck))
	if dest.CheckList == nil {
		dest.CheckList = []*carSuspiciousCheck{}
	}

	// 详情里的 TrailInfo：未取到轨迹时各字段保持 null（与 Java 的空对象一致）。
	trail := &trailInfo{}
	if isNotBlank(dest.TrackJosn) {
		parsed, tracks, points, err := parseTrailInfo(strOf(dest.TrackJosn))
		if err == nil {
			trail = parsed
		}
		trail.TrailUUID = strPtr(strOf(dest.CarNo))
		// DIFF: raodTrailList 依赖路网 Geometry + 路线规划接口（getCarGeometryByPlanNew），本模块不复现。
		trail.RaodTrailList = []any{}
		applyPilenoDec(points)
		trail.TrailDevCountBO = trailDevCount(tracks, points)
	}
	dest.TrailList = []*trailInfo{trail}
	return dest
}

func (h *handler) suspiciousGet(c *gin.Context) {
	dest := h.suspiciousDetail(c, c.Param("id"), carSuspiciousTable)
	web.JSON(c, web.SuccessData(dest))
}

// suspiciousSave 对应 saveCarSuspicious：userId 硬编码 1，新增默认 isExcept=1/status=0。
func (h *handler) suspiciousSave(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	id := bodyString(body, "id")
	cols := pickColumns(body, carSuspiciousColumns)
	cols["car_no"] = isNull(bodyString(body, "carNo"))
	const systemUserID int64 = 1
	now := time.Now()
	if id != "" {
		cols["update_by"] = systemUserID
		cols["update_time"] = now
		if _, err := h.updateRow(c.Request.Context(), carSuspiciousTable, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		id = newSnowflakeID()
		cols["id"] = id
		cols["create_by"] = systemUserID
		cols["create_time"] = now
		cols["update_by"] = systemUserID
		cols["update_time"] = now
		cols["is_except"] = "1"
		cols["status"] = "0"
		cols["del_flag"] = "0"
		if err := h.insertRow(c.Request.Context(), carSuspiciousTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

func (h *handler) suspiciousDelete(c *gin.Context) {
	h.tableDelete(c, suspiciousSpec)
}

// suspiciousCheck 对应 PUT /check（cherkCarSuspicious）。
func (h *handler) suspiciousCheck(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	carID := isNull(bodyString(body, "id"))
	if carID == "" {
		web.JSON(c, web.ErrorMsg(suspiciousNotFoundMessage))
		return
	}
	current := h.suspiciousDetail(c, carID, carSuspiciousTable)
	if current == nil {
		web.JSON(c, web.ErrorMsg(suspiciousNotFoundMessage))
		return
	}
	if isNull(current.Status) == "1" {
		web.JSON(c, web.ErrorMsg(suspiciousPaidMessage))
		return
	}
	carNo := isNull(bodyString(body, "carNo"))
	isExcept := isNull(bodyString(body, "isExcept"))
	rawChecks, hasChecks := body["checkList"]
	var checkList []*carSuspiciousCheck
	if hasChecks && rawChecks != nil {
		encoded, _ := json.Marshal(rawChecks)
		_ = json.Unmarshal(encoded, &checkList)
	}
	if isExcept == "1" && len(checkList) == 0 {
		web.JSON(c, web.ErrorMsg(checkListEmptyMessage))
		return
	}
	// JAVA 对照: checkList 是 CarSuspicious 的实例字段，请求里不给就是 null，
	// 而下面 `for (CarSuspiciousCheck check : checkList)` 不判空 ⇒ 直接 NPE，
	// GlobalExceptionHandler 拿到的 e.getMessage() 是 null ⇒ {"msg":null,"code":500}。
	// 方法带 @Transactional(rollbackFor=Exception.class)，NPE 会把随后两个 delete 回滚掉，
	// 所以在删除之前返回同样的空消息错误，净效果一致（数据一行都不动）。
	if !hasChecks || rawChecks == nil {
		web.JSON(c, web.ErrorResult(web.NewNilMessageError()))
		return
	}

	ctx := c.Request.Context()

	escapedType := ""
	escapedAmount := 0.0
	for _, check := range checkList {
		addCheckType := isNull(check.EscapedType)
		if !strings.Contains(escapedType, addCheckType) {
			escapedType += addCheckType + ","
		}
		if check.DifAmount != nil {
			escapedAmount += *check.DifAmount
		}
	}
	escapedType = deleteEnd(escapedType)
	// JAVA 对照: CarSuspiciousServiceImpl:256-268 的 escapedType 同样只计算不使用（源码遗留）；
	// 保留计算以维持行为一致，这里显式消费避免 ineffassign 误报。
	_ = escapedType

	// JAVA 对照: cherkCarSuspicious 带 @Transactional(rollbackFor = Exception.class)——
	// 两次物理删除、人工核实/异常流水的批量插入、可疑车状态更新必须在同一事务里，
	// 否则中途失败会留下「旧数据已删、新数据只写一半」的不可恢复中间态。
	err = h.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// 删除人工核验详情（物理删除）
		if err := tx.Exec("DELETE FROM car_suspicious_check WHERE car_id = ?", carID).Error; err != nil {
			return err
		}
		// 删除异常车辆信息（物理删除）
		if err := tx.Exec("DELETE FROM car_except_record WHERE car_id = ?", carID).Error; err != nil {
			return err
		}

		if isExcept == "1" {
			// 查询车辆（重点车辆库）
			var carCount int64
			if err := tx.Raw(
				"SELECT COUNT(1) FROM car_info WHERE del_flag = '0' AND car_no = ?", carNo).
				Scan(&carCount).Error; err != nil {
				return err
			}
			if carCount == 0 {
				userID := currentUserID(c)
				epsID := currentEpsID(c)
				now := time.Now()
				carNum := bodyNumberInt64(body, "carNum")
				if err := tx.Table(carInfoTable).Create(map[string]any{
					"id": newUUID(), "car_no": carNo, "car_type": bodyString(body, "carType"),
					"car_num": carNum, "car_vehicle": bodyString(body, "carVehicle"),
					"plate_color": bodyString(body, "plateColor"), "escaped_type": bodyString(body, "escapedType"),
					"escaped_amount": escapedAmount, "del_flag": "0",
					"create_by": userID, "create_time": now, "update_by": userID, "update_time": now,
					"eps_id": epsID,
				}).Error; err != nil {
					return err
				}
			}

			var excepts []*carExceptRecord
			for _, check := range checkList {
				check.CarID = strPtr(carID)
				check.CarNo = strPtr(carNo)
				check.SuspicousFlag = strPtr(isExcept)
				record := &carExceptRecord{
					CarID: strPtr(carID), CarNo: strPtr(carNo), CarType: strPtr(bodyString(body, "carType")),
					CarVehicle: strPtr(bodyString(body, "carVehicle")), CarNum: bodyNumberInt64(body, "carNum"),
					PassType: current.PassType, InStationID: current.InStationID, InStation: current.InStation,
					InTime: current.InTime, OutStationID: current.GantryStationID, OutStation: current.GantrytStation,
					OutTime: current.GantryTime, Status: strPtr("0"), TotalAmount: check.TotalAmount,
					ChargeAmount: check.ChargeAmount, DifAmount: check.DifAmount, EscapedType: check.EscapedType,
				}
				excepts = append(excepts, record)
			}
			for _, check := range checkList {
				cols := map[string]any{
					"id": newUUID(), "car_id": check.CarID, "car_no": check.CarNo,
					"pass_type": current.PassType, "in_station_id": current.InStationID,
					"in_station": current.InStation, "in_time": current.InTime,
					"out_station_id": current.GantryStationID, "out_station": current.GantrytStation,
					"out_time": current.GantryTime, "status": "0", "total_amount": check.TotalAmount,
					"charge_amount": check.ChargeAmount, "dif_amount": check.DifAmount,
					"escaped_type": check.EscapedType, "suspicous_flag": check.SuspicousFlag,
					"attachments": check.Attachments, "remark": check.Remark,
				}
				h.withInsertAudit(c, cols)
				if err := insertRowTx(tx, carSuspiciousCheckTable, cols); err != nil {
					return err
				}
			}
			for _, record := range excepts {
				cols := map[string]any{
					"id": newUUID(), "car_id": record.CarID, "car_no": record.CarNo,
					"car_type": record.CarType, "car_vehicle": record.CarVehicle, "car_num": record.CarNum,
					"pass_type": record.PassType, "in_station_id": record.InStationID,
					"in_station": record.InStation, "in_time": record.InTime,
					"out_station_id": record.OutStationID, "out_station": record.OutStation,
					"out_time": record.OutTime, "status": record.Status,
					"total_amount": record.TotalAmount, "charge_amount": record.ChargeAmount,
					"dif_amount": record.DifAmount, "escaped_type": record.EscapedType,
				}
				h.withInsertAudit(c, cols)
				if err := insertRowTx(tx, carExceptRecordTable, cols); err != nil {
					return err
				}
			}
		}

		// 修改状态已核实
		updateCols := map[string]any{
			"check_status": "1", "is_except": isExcept,
			"except_remark":   bodyString(body, "exceptRemark"),
			"except_file_ids": bodyString(body, "exceptFileIds"),
			"pass_type":       bodyString(body, "passType"),
			"plate_color":     bodyString(body, "plateColor"),
			"car_no":          carNo,
			"car_type":        bodyString(body, "carType"),
			"car_vehicle":     bodyString(body, "carVehicle"),
			"car_num":         bodyNumberInt64(body, "carNum"),
			"escaped_type":    bodyString(body, "escapedType"),
			"remark":          bodyString(body, "remark"),
		}
		if isExcept == "0" {
			updateCols["except_file_ids"] = ""
		}
		withUpdateAudit(c, updateCols)
		_, err := updateRowTx(tx, carSuspiciousTable, carID, updateCols)
		return err
	})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	_ = h.refreshCarList(c)
	web.JSON(c, web.SuccessFull("操作成功！", carID))
}

// ---------------------------------------------------------------- 历史表

func (h *handler) suspiciousListHistory(c *gin.Context) {
	clause, args := suspiciousClause(c)
	h.respondList(c, suspiciousHistSpec, clause, args)
}

func (h *handler) suspiciousHistoryGet(c *gin.Context) {
	dest := h.suspiciousDetail(c, c.Param("id"), carSuspiciousBackTable)
	web.JSON(c, web.SuccessData(dest))
}

// suspiciousExportHistory 对应 GET /exportHistory。
func (h *handler) suspiciousExportHistory(c *gin.Context) {
	h.suspiciousExportWith(c, suspiciousHistSpec, "carSuspiciousHistory.xlsx", "可疑车辆历史")
}

// ---------------------------------------------------------------- 导出

// suspiciousExport 对应 GET /export。
func (h *handler) suspiciousExport(c *gin.Context) {
	h.suspiciousExportWith(c, suspiciousSpec, "carSuspicious.xlsx", "可疑车辆")
}

// suspiciousExportWith 对应 CarSuspiciousController.export / exportHistory：
// 两个方法都在导出前 startPage()（所以带默认 1/10 分页），再把出入口两端拼成「A至B」
// 写回实体（模板打印的是 txTime/txAddress/mjTime/mjAddress/createTimeStr 这些派生字段）。
//
// JAVA 对照: CarSuspiciousController.java:272-368 / :506-603
func (h *handler) suspiciousExportWith(c *gin.Context, spec *tableSpec, fileName, sheet string) {
	clause, args := suspiciousClause(c)
	cols := suspiciousExportCols()
	rows, err := h.exportQuery(c.Request.Context(), spec, clause, args, web.PageAlways(c), cols, nil,
		func(dest any) {
			for _, row := range *(dest.(*[]*carSuspicious)) {
				row.TxTime = strPtr(suspiciousTimeRange(row.InTime, row.OutTime))
				row.TxAddress = strPtr(suspiciousTextRange(row.InStation, row.OutStation))
				row.MjTime = strPtr(suspiciousTimeRange(row.GantryTime, row.OutGantryTime))
				row.MjAddress = strPtr(suspiciousTextRange(row.GantrytStation, row.OutGantrytStation))
				if row.CreateTime != nil {
					row.CreateTimeStr = strPtr(row.CreateTime.String())
				}
			}
		})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	h.writeExport(c, sheet, cols, rows, fileName, false)
}

// suspiciousTimeRange 对应 Java 的「in 非空则拼时间，out 非空再拼『至』+时间」两段式判断。
func suspiciousTimeRange(start, end *web.DateTime) string {
	out := ""
	if start != nil {
		out += start.String()
	}
	if end != nil {
		out += "至" + end.String()
	}
	return out
}

func suspiciousTextRange(start, end *string) string {
	out := ""
	if !isBlank(strOf(start)) {
		out += strOf(start)
	}
	if !isBlank(strOf(end)) {
		out += "至" + strOf(end)
	}
	return out
}

// suspiciousExportAbnormalPassage 生成简化版 docx（Java 用 Word 模板）。
func (h *handler) suspiciousExportAbnormalPassage(c *gin.Context) {
	id := queryParam(c, "carSuspiciousId")
	car := h.suspiciousDetail(c, id, carSuspiciousTable)
	if car == nil {
		// JAVA 对照: exportAbnormalPassage 里 carSuspicious 为 null 时直接 NPE，
		// GlobalExceptionHandler 返回 code 500 + msg = e.getMessage() = null。
		web.JSON(c, web.ErrorResult(web.NewNilMessageError()))
		return
	}
	plateColors, _ := h.dictValueLabel(c.Request.Context(), "plate_color")
	carTypes, _ := h.dictValueLabel(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictValueLabel(c.Request.Context(), "car_vehicle")
	escapedTypes, _ := h.dictValueLabel(c.Request.Context(), "escaped_type")
	charge, totalAmount, dif := 0.0, 0.0, 0.0
	for _, check := range car.CheckList {
		if check.ChargeAmount != nil {
			charge += *check.ChargeAmount
		}
		if check.TotalAmount != nil {
			totalAmount += *check.TotalAmount
		}
		if check.DifAmount != nil {
			dif += *check.DifAmount
		}
	}
	var names []string
	for _, part := range splitCSV(deleteEnd(car.EscapedType)) {
		if label, ok := escapedTypes[part]; ok {
			names = append(names, label)
		}
	}
	isExcept := ""
	switch strOf(car.IsExcept) {
	case "0":
		isExcept = "无逃费"
	case "1":
		isExcept = "确认逃费"
	}
	// JAVA 对照: templates/export/carSuspicious.docx 的段落顺序与标签原文（车辆信息 / 通行异常 /
	// 核实信息 / 证据材料 四个小节），以及控制器给 map 赋值的三条规则：
	//   金额 = BigDecimal 累加后 toString()（decimal(19,2) ⇒ 两位小数；一条明细都没累加到是 "0"；
	//          checkList 为 null 时 Java 直接放空串）；
	//   车种 字典未命中回落原值（Java 只有 carVehicle 这么写，车牌颜色/车型未命中是给空串）；
	//   图片占位（poi-tl 的 {{susImg1..7}}）在这里无法内嵌，只保留"图片："这一行。
	amountText := func(v float64) string {
		if len(car.CheckList) == 0 {
			return "0"
		}
		return strconv.FormatFloat(v, 'f', 2, 64)
	}
	chargeTxt, totalTxt, difTxt := amountText(charge), amountText(totalAmount), amountText(dif)
	if car.CheckList == nil {
		chargeTxt, totalTxt, difTxt = "", "", ""
	}
	carVehicle := carVehicles[strOf(car.CarVehicle)]
	if carVehicle == "" {
		carVehicle = strOf(car.CarVehicle)
	}
	lines := []string{
		"车牌颜色：" + plateColors[strOf(car.PlateColor)],
		"车牌号：" + strOf(car.CarNo),
		"车型：" + carTypes[strOf(car.CarType)],
		"车种：" + carVehicle,
		"轴数：" + plainStr(car.CarNum),
		"通行异常",
		"入站口：" + strOf(car.InStation),
		"入口时间：" + dateTimeStr(car.InTime),
		"出站口：" + strOf(car.OutStation),
		"出口时间：" + dateTimeStr(car.OutTime),
		"起始门架：" + strOf(car.GantrytStation),
		"起始经过时间：" + dateTimeStr(car.GantryTime),
		"终止门架：" + strOf(car.OutGantrytStation),
		"终止经过时间：" + dateTimeStr(car.OutGantryTime),
		"逃费类型：" + strings.Join(names, ","),
		"收费金额（元）：" + chargeTxt,
		"应缴金额（元）：" + totalTxt,
		"差额（元）：" + difTxt,
		"核实信息",
		"核实结果：" + isExcept,
		"备注：" + strOf(car.ExceptRemark),
		"图片：",
		"证据材料",
	}
	data, err := buildDocx("车辆信息", lines)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "carSuspicious.docx", data)
}

// ---------------------------------------------------------------- 大屏 top10

// suspiciousListLimit10 对应 selectCarSuspiciousListLimit10（resultType，只有 4 列有值）。
func (h *handler) suspiciousListLimit10(c *gin.Context) []*carSuspicious {
	sqlStr := "SELECT t.car_no, t.car_type, t.escaped_type, t.section_name FROM car_suspicious t " +
		"WHERE t.del_flag = '0' and is_except = '1' and check_status = '1' " +
		"order by t.create_time desc,t.id limit 10"
	var rows []struct {
		CarNo       *string `gorm:"column:car_no"`
		CarType     *string `gorm:"column:car_type"`
		EscapedType *string `gorm:"column:escaped_type"`
		SectionName *string `gorm:"column:section_name"`
	}
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr).Scan(&rows)
	out := make([]*carSuspicious, 0, len(rows))
	for _, row := range rows {
		// 只查这 4 列，其余字段（含 id）在 Java 里是 null。
		out = append(out, &carSuspicious{
			CarNo: row.CarNo, CarType: row.CarType, EscapedType: row.EscapedType, SectionName: row.SectionName,
		})
	}
	return out
}

// ---------------------------------------------------------------- 同步

// suspiciousSync 对应 POST /syncSuspiciousCarTask（匿名接口，SHA1 验签）。
func (h *handler) suspiciousSync(c *gin.Context) {
	var payload struct {
		SignatureKey  string            `json:"signatureKey"`
		TimeStamp     *int64            `json:"timeStamp"`
		Signature     string            `json:"signature"`
		TrailInfoList []json.RawMessage `json:"trailInfoList"`
	}
	if err := bindJSON(c, &payload); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if isBlank(payload.SignatureKey) || isBlank(payload.Signature) || payload.TimeStamp == nil {
		web.JSON(c, web.ErrorMsg("参数错误"))
		return
	}
	sum := sha1.Sum([]byte(payload.SignatureKey + strconv.FormatInt(*payload.TimeStamp, 10)))
	if hex.EncodeToString(sum[:]) != payload.Signature {
		web.JSON(c, web.ErrorMsg("错误，签名验证失败！"))
		return
	}
	if len(payload.TrailInfoList) > 0 {
		if err := h.syncSuspiciousCar(c, payload.TrailInfoList); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	web.JSON(c, web.Success())
}

type trailPayload struct {
	Tracks struct {
		PlateKey          string `json:"plateKey"`
		UUID              string `json:"uuid"`
		EscapedTfcj       string `json:"escapedTfcj"`
		PlateColor        string `json:"plateColor"`
		Envehicletype     string `json:"envehicletype"`
		Enaxlecount       any    `json:"enaxlecount"`
		CarNum            *int64 `json:"carNum"`
		PassType          string `json:"passType"`
		Entollstationid   string `json:"entollstationid"`
		Entollstationname string `json:"entollstationname"`
		Extollstationid   string `json:"extollstationid"`
		Extollstationname string `json:"extollstationname"`
		EnterTime         string `json:"enterTime"`
		ExitTime          string `json:"exitTime"`
		EscapedType       string `json:"escapedType"`
		EscapedTypeRemark string `json:"escapedTypeRemark"`
	} `json:"tracks"`
	TrailList []trailPoint `json:"trailList"`
}

type trailPoint struct {
	StateType   string `json:"stateType"`
	DevCode     string `json:"devCode"`
	DevName     string `json:"devName"`
	CaptureTime string `json:"captureTime"`
	RoadCode    string `json:"roadCode"`
	SectionCode string `json:"sectionCode"`
}

func (h *handler) syncSuspiciousCar(c *gin.Context, rawList []json.RawMessage) error {
	whiteMap := map[string]struct{}{}
	for _, white := range h.getRedisWhiteList(c) {
		whiteMap[isNull(white.CarNo)] = struct{}{}
	}
	carMap := map[string]*carInfo{}
	for _, car := range h.getRedisCarList(c) {
		carMap[isNull(car.CarNo)] = car
	}
	plateColors, _ := h.dictLabelValue(c.Request.Context(), "plate_color")

	var addList []*carSuspicious
	var updateList []*carSuspicious
	for _, raw := range rawList {
		var payload trailPayload
		if err := json.Unmarshal(raw, &payload); err != nil {
			continue
		}
		carNo := isNull(payload.Tracks.PlateKey)
		trailUUID := isNull(payload.Tracks.UUID)
		if carNo == "" || trailUUID == "" {
			continue
		}
		if _, white := whiteMap[carNo]; white {
			continue
		}
		if len(payload.TrailList) == 0 {
			continue
		}
		var existingID, checkStatus string
		var existingRows []struct {
			ID          string `gorm:"column:id"`
			CheckStatus string `gorm:"column:check_status"`
		}
		_ = h.app.DB.WithContext(c.Request.Context()).Raw(
			"SELECT id, check_status FROM car_suspicious WHERE del_flag = '0' AND car_no = ? AND track_id = ? LIMIT 1",
			carNo, trailUUID).Scan(&existingRows)
		if len(existingRows) > 0 {
			existingID = existingRows[0].ID
			checkStatus = isNull(existingRows[0].CheckStatus)
		}
		if checkStatus == "1" {
			continue
		}

		item := &carSuspicious{
			CarNo: strPtr(carNo), TrackID: strPtr(trailUUID), BackCol1: strPtr(payload.Tracks.EscapedTfcj),
			PlateColor: strPtr(isNull(plateColors[isNull(payload.Tracks.PlateColor)])),
			TrackJosn:  strPtr(string(raw)),
		}
		if car, ok := carMap[carNo]; ok {
			item.PlateColor = strPtr(isNull(car.PlateColor))
			item.CarType = strPtr(isNull(car.CarType))
			item.CarVehicle = strPtr(isNull(car.CarVehicle))
		} else if isNotBlank(payload.Tracks.Envehicletype) {
			if vehicle := carVehicleOfSync(payload.Tracks.Envehicletype); vehicle != "" {
				item.CarType = strPtr(payload.Tracks.Envehicletype)
				item.CarVehicle = strPtr(vehicle)
			}
		}
		if payload.Tracks.Enaxlecount != nil {
			if n, err := strconv.ParseInt(fmt.Sprint(payload.Tracks.Enaxlecount), 10, 64); err == nil {
				item.CarNum = &n
			} else {
				item.CarNum = payload.Tracks.CarNum
			}
		} else {
			item.CarNum = payload.Tracks.CarNum
		}
		item.PassType = strPtr(payload.Tracks.PassType)
		if isBlank(item.PlateColor) {
			item.PlateColor = strPtr("9")
		}
		if isBlank(item.CarType) {
			item.CarType = strPtr("99")
		}
		if isBlank(item.CarVehicle) {
			item.CarVehicle = strPtr("99")
		}

		devCodes := ""
		var gantryList, stationList []trailPoint
		for _, point := range payload.TrailList {
			stateType := isNull(point.StateType)
			if isNotBlank(point.DevCode) {
				devCodes += stateType + ":" + point.DevCode + ","
			}
			if isNotBlank(point.RoadCode) {
				key := "roadCode:" + point.RoadCode + ","
				if !strings.Contains(devCodes, key) {
					devCodes += key
				}
			}
			if isNotBlank(point.SectionCode) {
				key := "sectionCode:" + point.SectionCode + ","
				if !strings.Contains(devCodes, key) {
					devCodes += key
				}
			}
			switch stateType {
			case gantryCapture:
				gantryList = append(gantryList, point)
			case stationCapture:
				stationList = append(stationList, point)
			}
		}
		for i, point := range stationList {
			if i == 0 {
				item.InStationID = strPtr(point.DevCode)
				item.InStation = strPtr(point.DevName)
				item.InTime = web.ParseOptional(point.CaptureTime)
			} else if i == len(stationList)-1 {
				item.OutStationID = strPtr(point.DevCode)
				item.OutStation = strPtr(point.DevName)
				item.OutTime = web.ParseOptional(point.CaptureTime)
			}
		}
		if isNotBlank(payload.Tracks.Entollstationid) {
			item.InStationID = strPtr(payload.Tracks.Entollstationid)
			item.InStation = strPtr(payload.Tracks.Entollstationname)
			item.InTime = web.ParseOptional(payload.Tracks.EnterTime)
		}
		if isNotBlank(payload.Tracks.Extollstationid) {
			item.OutStationID = strPtr(payload.Tracks.Extollstationid)
			item.OutStation = strPtr(payload.Tracks.Extollstationname)
			item.OutTime = web.ParseOptional(payload.Tracks.ExitTime)
		}
		for i, point := range gantryList {
			if i == 0 {
				item.GantryStationID = strPtr(point.DevCode)
				item.GantrytStation = strPtr(point.DevName)
				item.GantryTime = web.ParseOptional(point.CaptureTime)
			} else if i == len(gantryList)-1 {
				item.OutGantryStationID = strPtr(point.DevCode)
				item.OutGantrytStation = strPtr(point.DevName)
				item.OutGantryTime = web.ParseOptional(point.CaptureTime)
			}
		}
		item.TrackNames = strPtr(deleteEnd(devCodes))
		item.IsExcept = strPtr("1")
		item.Status = strPtr("0")
		item.Remark = strPtr(payload.Tracks.EscapedTypeRemark)
		if existingID == "" {
			item.EscapedType = strPtr(payload.Tracks.EscapedType)
			addList = append(addList, item)
		} else {
			item.ID = strPtr(existingID)
			updateList = append(updateList, item)
		}
	}

	systemUserID := int64(1)
	twoDaysAgo := time.Now().Add(-48 * time.Hour)
	// JAVA 对照: CarSuspiciousServiceImpl.syncSuspiciousCar 带 @Transactional(rollbackFor = Exception.class)。
	// 单条写入失败在 Java 里会抛出并回滚整批，这里同样让整个批次同生共死。
	return h.app.DB.WithContext(c.Request.Context()).Transaction(func(tx *gorm.DB) error {
		for _, item := range addList {
			item.ID = strPtr(newSnowflakeID())
			item.CreateBy = &systemUserID
			item.UpdateBy = &systemUserID
			item.CreateTime = ptrDateTime(twoDaysAgo)
			item.UpdateTime = ptrDateTime(twoDaysAgo)
			cols := map[string]any{
				"id": item.ID, "plate_color": item.PlateColor, "car_no": item.CarNo,
				"car_type": item.CarType, "car_vehicle": item.CarVehicle, "car_num": item.CarNum,
				"pass_type": item.PassType, "in_station_id": item.InStationID, "in_station": item.InStation,
				"in_time": item.InTime, "out_station_id": item.OutStationID, "out_station": item.OutStation,
				"out_time": item.OutTime, "gantry_station_id": item.GantryStationID,
				"gantryt_station": item.GantrytStation, "gantry_time": item.GantryTime,
				"out_gantry_station_id": item.OutGantryStationID, "out_gantryt_station": item.OutGantrytStation,
				"out_gantry_time": item.OutGantryTime, "escaped_type": item.EscapedType,
				"remark": item.Remark, "track_id": item.TrackID, "track_josn": item.TrackJosn,
				"track_names": item.TrackNames, "back_col1": item.BackCol1, "is_except": "1",
				"status": "0", "del_flag": "0", "create_by": systemUserID, "create_time": twoDaysAgo,
				"update_by": systemUserID, "update_time": twoDaysAgo,
			}
			if err := insertRowTx(tx, carSuspiciousTable, cols); err != nil {
				return err
			}
		}
		for _, item := range updateList {
			cols := map[string]any{
				"plate_color": item.PlateColor, "car_no": item.CarNo, "car_type": item.CarType,
				"car_vehicle": item.CarVehicle, "car_num": item.CarNum, "pass_type": item.PassType,
				"in_station_id": item.InStationID, "in_station": item.InStation, "in_time": item.InTime,
				"out_station_id": item.OutStationID, "out_station": item.OutStation, "out_time": item.OutTime,
				"gantry_station_id": item.GantryStationID, "gantryt_station": item.GantrytStation,
				"gantry_time": item.GantryTime, "out_gantry_station_id": item.OutGantryStationID,
				"out_gantryt_station": item.OutGantrytStation, "out_gantry_time": item.OutGantryTime,
				"track_josn": item.TrackJosn, "track_names": item.TrackNames,
				"back_col1": item.BackCol1, "is_except": "1", "status": "0",
				"remark": item.Remark, "update_by": systemUserID, "update_time": twoDaysAgo,
			}
			if _, err := updateRowTx(tx, carSuspiciousTable, strOf(item.ID), cols); err != nil {
				return err
			}
		}
		return nil
	})
}

// ---------------------------------------------------------------- 工具

// newSnowflakeID 对应 MyBatis-Plus IdWorker.nextId()（car_suspicious 主键）。
// DIFF: 原实现用 UnixNano，未带机器位；统一到 internal/idgen 后多副本不会碰撞。
func newSnowflakeID() string { return idgen.NextString() }

func carVehicleOfSync(carType string) string {
	switch carType {
	case "1", "2", "3", "4":
		return "1"
	case "11", "12", "13", "14", "15", "16":
		return "2"
	case "21", "22", "23", "24", "25", "26":
		return "3"
	default:
		return ""
	}
}

func bodyNumberInt64(body map[string]any, key string) *int64 {
	raw, ok := body[key]
	if !ok || raw == nil {
		return nil
	}
	switch v := raw.(type) {
	case float64:
		n := int64(v)
		return &n
	case string:
		if v == "" {
			return nil
		}
		if n, err := strconv.ParseInt(v, 10, 64); err == nil {
			return &n
		}
	}
	return nil
}

func plainStr(v *int64) string {
	if v == nil {
		return ""
	}
	return strconv.FormatInt(*v, 10)
}

func dateTimeStr(v *web.DateTime) string {
	if v == nil || v.IsZero() {
		return ""
	}
	return v.String()
}

// buildDocx 生成最小可读的 docx（WordprocessingML）。
func buildDocx(title string, lines []string) ([]byte, error) {
	var body bytes.Buffer
	body.WriteString(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`)
	body.WriteString(`<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>`)
	writePara := func(text string, bold bool) {
		body.WriteString("<w:p>")
		if bold {
			body.WriteString(`<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">` + xmlEscape(text) + `</w:t></w:r>`)
		} else {
			body.WriteString(`<w:r><w:t xml:space="preserve">` + xmlEscape(text) + `</w:t></w:r>`)
		}
		body.WriteString("</w:p>")
	}
	writePara(title, true)
	for _, line := range lines {
		writePara(line, false)
	}
	body.WriteString(`</w:body></w:document>`)

	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	files := map[string]string{
		"[Content_Types].xml": `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
			`<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
			`<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
			`<Default Extension="xml" ContentType="application/xml"/>` +
			`<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>` +
			`</Types>`,
		"_rels/.rels": `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
			`<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
			`<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>` +
			`</Relationships>`,
		"word/document.xml": body.String(),
	}
	for name, content := range files {
		w, err := zw.Create(name)
		if err != nil {
			return nil, err
		}
		if _, err := w.Write([]byte(content)); err != nil {
			return nil, err
		}
	}
	if err := zw.Close(); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func xmlEscape(s string) string {
	replacer := strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;", "'", "&apos;")
	return replacer.Replace(s)
}
