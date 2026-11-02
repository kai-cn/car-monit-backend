// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarAduitFreeServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java
// 类/职责: 补缴处理 / 确认补缴（含堵漏增收统计）
// 对应 Go 文件: internal/modules/manager/car_free.go
package manager

import (
	"context"
	"encoding/json"
	"math"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// ---------------------------------------------------------------- VO

type carStatisticsVO struct {
	EscapedType     string  `json:"escapedType"`
	EscapedTypeName string  `json:"escapedTypeName"`
	Number          int64   `json:"number"`
	EscapedAmount   float64 `json:"escapedAmount"`
}

type incomeStatisticVO struct {
	OrgName *string  `json:"orgName"`
	Amount  *float64 `json:"amount"`
	CarNum  *int64   `json:"carNum"`
}

type pcIncomeStaticsVO struct {
	OrgID   *string  `json:"orgId"`
	OrgName *string  `json:"orgName"`
	Amount  *float64 `json:"amount"`
	CarNum  *int64   `json:"carNum"`
}

type pcCarStatisticsDetailVO struct {
	PlateColor    *string       `json:"plateColor"`
	CarNo         *string       `json:"carNo"`
	CarType       *string       `json:"carType"`
	EscapedType   *string       `json:"escapedType"`
	EscapedAmount float64       `json:"escapedAmount"`
	OrgName       *string       `json:"orgName"`
	CreateTime    *web.DateTime `json:"createTime"`
}

type pcCarStatisticsVO struct {
	OrgID   *string `json:"orgId"`
	OrgName *string `json:"orgName"`

	EscapedType10Num    int64   `json:"escapedType10Num"`
	EscapedType10Amount float64 `json:"escapedType10Amount"`
	EscapedType20Num    int64   `json:"escapedType20Num"`
	EscapedType20Amount float64 `json:"escapedType20Amount"`
	EscapedType30Num    int64   `json:"escapedType30Num"`
	EscapedType30Amount float64 `json:"escapedType30Amount"`
	EscapedType40Num    int64   `json:"escapedType40Num"`
	EscapedType40Amount float64 `json:"escapedType40Amount"`
	EscapedType50Num    int64   `json:"escapedType50Num"`
	EscapedType50Amount float64 `json:"escapedType50Amount"`
	EscapedType60Num    int64   `json:"escapedType60Num"`
	EscapedType60Amount float64 `json:"escapedType60Amount"`

	TotalNum    int64   `json:"totalNum"`
	TotalAmount float64 `json:"totalAmount"`

	DetailVOList []*pcCarStatisticsDetailVO `json:"detailVOList"`
}

type carAuditVO struct {
	TotalCount     int64   `json:"totalCount"`
	FinishedCount  int64   `json:"finishedCount"`
	TotalAmount    float64 `json:"totalAmount"`
	FinishedAmount float64 `json:"finishedAmount"`
}

// ---------------------------------------------------------------- 注册

func (h *handler) registerAduitFree(reg *router.Registry) {
	auth := reg.Authed
	auth.GET("/manager/aduitfree/list", h.tableList2(aduitFreeSpec))
	auth.GET("/manager/aduitfree/export", h.aduitFreeExport)
	auth.GET("/manager/aduitfree/incomeStatics", h.aduitFreeIncomeStatics)
	auth.GET("/manager/aduitfree/exportIncomeStatics", h.aduitFreeExportIncomeStatics)
	auth.GET("/manager/aduitfree/incomeDetailList", h.aduitFreeIncomeDetailList)
	auth.GET("/manager/aduitfree/exportIncomeDetailList", h.aduitFreeExportIncomeDetailList)
	auth.GET("/manager/aduitfree/:id", h.tableGet2(aduitFreeSpec))
	auth.POST("/manager/aduitfree", h.tableSave2(aduitFreeSpec))
	auth.PUT("/manager/aduitfree", h.tableSave2(aduitFreeSpec))
	auth.DELETE("/manager/aduitfree/:ids", h.tableDelete2(aduitFreeSpec))
}

func (h *handler) registerConfimFree(reg *router.Registry) {
	auth := reg.Authed
	auth.GET("/manager/confimfree/list", h.tableList2(confimFreeSpec))
	auth.GET("/manager/confimfree/listCarNo", h.confimFreeListCarNo)
	auth.GET("/manager/confimfree/listCount", h.confimFreeListCount)
	auth.GET("/manager/confimfree/export", h.confimFreeExport)
	auth.GET("/manager/confimfree/concernedList", h.confimFreeConcernedList)
	auth.GET("/manager/confimfree/exportConcernedList", h.confimFreeExportConcernedList)
	auth.GET("/manager/confimfree/carStatics", h.confimFreeCarStatics)
	auth.GET("/manager/confimfree/exportCarStatics", h.confimFreeExportCarStatics)
	auth.GET("/manager/confimfree/except/:exceptIds", h.confimFreeExcept)
	auth.GET("/manager/confimfree/:id", h.confimFreeGet)
	auth.POST("/manager/confimfree", h.confimFreeSave)
	auth.PUT("/manager/confimfree", h.confimFreeSave)
	auth.DELETE("/manager/confimfree/:ids", h.confimFreeDelete)
}

// ---------------------------------------------------------------- 补缴处理

func (h *handler) aduitFreeExport(c *gin.Context) {
	cols := []exportCol{
		{Title: "车牌号", Field: "carNo"}, {Title: "车型", Field: "carType", Dict: "car_type"},
		{Title: "车种", Field: "carVehicle", Dict: "car_vehicle"},
		{Title: "录入单位", Field: "orgName"}, {Title: "处理金额（元）", Field: "amount"},
		{Title: "状态", Field: "status"}, {Title: "备注", Field: "remark"},
	}
	h.exportTable(c, aduitFreeSpec, "aduitFree.xlsx", "补缴处理数据", cols, true)
}

// aduitFreeIncomeStatics 对应 GET /incomeStatics（分页的 PCIncomeStaticsVO）。
// JAVA 对照: CarAduitFreeController.incomeStatics:113-116 先 startPage()，
// 没带分页参数时 TableSupport 默认 1/10 —— 不能当成「不分页」。
func (h *handler) aduitFreeIncomeStatics(c *gin.Context) {
	rows, total, err := h.pcIncomeStatics(c, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// aduitFreeExportIncomeStatics 对应 exportIncomeStatics：Java 未 startPage，导出全量。
func (h *handler) aduitFreeExportIncomeStatics(c *gin.Context) {
	rows, _, err := h.pcIncomeStatics(c, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	cols := []exportCol{{Title: "录入单位", Field: "orgName"}, {Title: "车辆数", Field: "carNum"}, {Title: "金额（元）", Field: "amount"}}
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		out = append(out, []any{plainValue(row.OrgName), plainValue(row.CarNum), plainValue(row.Amount)})
	}
	data, err := buildWorkbook("堵漏增收", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "incomeStatics.xlsx", data)
}

// pcIncomeStatics 对应 getPCIncomeStatics（SQL 两段 UNION ALL + 共同的 4 条 <if>）。
func (h *handler) pcIncomeStatics(c *gin.Context, page web.PageDomain) ([]*pcIncomeStaticsVO, int64, error) {
	buildFilter := func() (string, []any) {
		filter := ""
		var args []any
		if v := argString(c, "orgId"); v != "" {
			filter += " AND a.org_id = ?"
			args = append(args, v)
		}
		if v := argString(c, "applyTime1"); v != "" {
			filter += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
			args = append(args, v)
		}
		if v := argString(c, "applyTime2"); v != "" {
			filter += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
			args = append(args, v)
		}
		if v := argString(c, "carNo"); v != "" {
			filter += " AND a.car_no LIKE CONCAT('%', ?, '%')"
			args = append(args, v)
		}
		return filter, args
	}
	f1, a1 := buildFilter()
	f2, a2 := buildFilter()
	base := "SELECT sum(t.amount) AS amount, count(distinct t.car_no) AS car_num, t.org_id, t.orgName AS org_name FROM (" +
		"SELECT ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name orgName FROM car_aduit_free a " +
		"LEFT JOIN sys_dept d ON d.dept_id = a.org_id WHERE a.del_flag = '0' AND a.status = '0'" + f1 +
		" UNION ALL " +
		"SELECT ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name orgName FROM car_confim_free a " +
		"LEFT JOIN sys_dept d ON d.dept_id = a.org_id WHERE a.del_flag = '0'" + f2 +
		") t GROUP BY t.org_id, t.orgName ORDER BY amount DESC"
	args := append(append([]any{}, a1...), a2...)

	var total int64
	if page.HasPage {
		countSQL := "SELECT COUNT(0) FROM (" + base + ") table_count"
		if err := h.app.DB.WithContext(c.Request.Context()).Raw(countSQL, args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	sqlStr := base
	queryArgs := args
	if page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := page.LimitOffset(total)
		queryArgs = append(append([]any{}, args...), lim, off)
	}
	var rows []*pcIncomeStaticsVO
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, queryArgs...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !page.HasPage {
		total = int64(len(rows))
	}
	return rows, total, nil
}

// incomeDetailRow 是堵漏增收明细的临时投影（对应 resultType 的 5 列）。
type incomeDetailRow struct {
	Amount     *float64      `gorm:"column:amount"`
	CarNo      string        `gorm:"column:car_no"`
	OrgID      string        `gorm:"column:org_id"`
	OrgName    string        `gorm:"column:org_name"`
	CreateTime *web.DateTime `gorm:"column:create_time"`
}

// incomeDetailList 返回 resultType 映射后的 CarConfimFree（只有 5 个字段有值）。
func (h *handler) incomeDetailList(c *gin.Context) ([]*carConfimFree, int64, error) {
	if isBlank(queryParam(c, "orgId")) {
		setQueryOverride(c, "orgId", "-1")
	}
	buildFilter := func() (string, []any) {
		filter := ""
		var args []any
		if v := argString(c, "orgId"); v != "" {
			filter += " AND a.org_id = ?"
			args = append(args, v)
		}
		if v := argString(c, "applyTime1"); v != "" {
			filter += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
			args = append(args, v)
		}
		if v := argString(c, "applyTime2"); v != "" {
			filter += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
			args = append(args, v)
		}
		if v := argString(c, "carNo"); v != "" {
			filter += " AND a.car_no LIKE CONCAT('%', ?, '%')"
			args = append(args, v)
		}
		return filter, args
	}
	f1, a1 := buildFilter()
	f2, a2 := buildFilter()
	base := "SELECT t.* FROM (" +
		"SELECT ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name AS org_name, a.create_time FROM car_aduit_free a " +
		"LEFT JOIN sys_dept d ON d.dept_id = a.org_id WHERE a.del_flag = '0' AND a.status = '0'" + f1 +
		" UNION ALL " +
		"SELECT ifnull(a.amount, 0) amount, a.car_no, a.org_id, d.dept_name AS org_name, a.create_time FROM car_confim_free a " +
		"LEFT JOIN sys_dept d ON d.dept_id = a.org_id WHERE a.del_flag = '0'" + f2 +
		") t ORDER BY t.create_time DESC"
	args := append(append([]any{}, a1...), a2...)
	page := web.Page(c)
	var total int64
	if page.HasPage {
		countSQL := "SELECT COUNT(0) FROM (" + base + ") table_count"
		if err := h.app.DB.WithContext(c.Request.Context()).Raw(countSQL, args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	sqlStr := base
	queryArgs := args
	if page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := page.LimitOffset(total)
		queryArgs = append(append([]any{}, args...), lim, off)
	}
	var rows []*incomeDetailRow
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, queryArgs...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !page.HasPage {
		total = int64(len(rows))
	}
	out := make([]*carConfimFree, 0, len(rows))
	for _, row := range rows {
		item := &carConfimFree{}
		item.Amount = row.Amount
		item.CarNo = strPtr(row.CarNo)
		item.OrgID = strPtr(row.OrgID)
		item.OrgName = strPtr(row.OrgName)
		item.CreateTime = row.CreateTime
		out = append(out, item)
	}
	return out, total, nil
}

func (h *handler) aduitFreeIncomeDetailList(c *gin.Context) {
	rows, total, err := h.incomeDetailList(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

func (h *handler) aduitFreeExportIncomeDetailList(c *gin.Context) {
	rows, _, err := h.incomeDetailList(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	cols := []exportCol{{Title: "车牌号", Field: "carNo"}, {Title: "追缴金额（元）", Field: "amount"},
		{Title: "录入单位", Field: "orgName"}, {Title: "录入时间", Field: "createTime"}}
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		out = append(out, []any{row.CarNo, plainValue(row.Amount), row.OrgName, plainValue(row.CreateTime)})
	}
	data, err := buildWorkbook("堵漏增收明细", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "exportIncomeDetailList.xlsx", data)
}

// ---------------------------------------------------------------- 确认补缴

func (h *handler) confimFreeListCarNo(c *gin.Context) {
	if isBlank(queryParam(c, "carNo")) {
		setQueryOverride(c, "carNo", "-1")
	}
	h.tableList(c, confimFreeSpec)
}

func (h *handler) confimFreeListCount(c *gin.Context) {
	carNo := argString(c, "carNo")
	if carNo == "" {
		carNo = "-1"
	}
	sqlStr := "SELECT t.car_no, count(1) AS confim_free_num, " +
		"round(ifnull(sum(t.aduit_amount), 0) + ifnull(sum(t.amount), 0), 2) AS confim_free_amount " +
		"FROM car_confim_free t WHERE t.del_flag = '0' AND t.car_no = ?"
	args := []any{carNo}
	if status := argString(c, "status"); status != "" {
		sqlStr += " AND t.status = ?"
		args = append(args, status)
	}
	sqlStr += " GROUP BY t.car_no"
	rows := newSliceOf(&carConfimFree{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(rows).Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	items := *(rows.(*[]*carConfimFree))
	if len(items) == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(items[0]))
}

// confimFreeGet 对应 selectCarConfimFreeById：带异常流水明细、处理明细与逃费合计。
func (h *handler) confimFreeGet(c *gin.Context) {
	dest := &carConfimFree{}
	sqlStr := "SELECT " + carConfimFreeSelectColumns +
		" FROM car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id WHERE t.id = ?"
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, c.Param("id")).Scan(dest)
	if tx.Error != nil {
		web.JSON(c, web.ErrorResult(tx.Error))
		return
	}
	if tx.RowsAffected == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	exceptIDs := deleteEnd(dest.ExceptIDs)
	if exceptIDs != "" {
		records := h.exceptRecordsByIDs(c, exceptIDs)
		dest.CarExceptRecordList = records
		dest.DifAmount = sumDifAmount(records)
	}
	aduitRows, err := h.aduitFreeByConfirmID(c, strOf(dest.ID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	dest.CarAduitFreeList = aduitRows
	web.JSON(c, web.SuccessData(dest))
}

// aduitFreeByConfirmID 对应 selectCarAduitFreeList(confirmId)。
func (h *handler) aduitFreeByConfirmID(c *gin.Context, confirmID string) ([]*carAduitFree, error) {
	sqlStr := "SELECT " + carAduitFreeSelectColumns + ", d.dept_name AS org_name" +
		" FROM car_aduit_free t LEFT JOIN sys_dept d ON d.dept_id = t.org_id AND d.del_flag = '0'" +
		" WHERE t.del_flag = '0' AND t.confirm_id = ? ORDER BY t.create_time,t.id"
	rows := newSliceOf(&carAduitFree{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, confirmID).Scan(rows).Error; err != nil {
		return nil, err
	}
	return *(rows.(*[]*carAduitFree)), nil
}

// exceptRecordsByIDs 对应 selectCarExceptRecordList(exceptIds)。
func (h *handler) exceptRecordsByIDs(c *gin.Context, exceptIDs string) []*carExceptRecord {
	sqlStr := "SELECT " + carExceptRecordSelectColumns + exceptRecordSpec.selectSuffix +
		" FROM " + exceptRecordSpec.fromSQL +
		" WHERE t.del_flag = '0' AND find_in_set(t.id, ?) > 0" +
		" ORDER BY t.create_time desc,t.id"
	rows := newSliceOf(&carExceptRecord{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, deleteEnd(exceptIDs)).Scan(rows).Error; err != nil {
		return nil
	}
	result := *(rows.(*[]*carExceptRecord))
	for _, item := range result {
		item.normalize()
	}
	return result
}

// sumDifAmount 对应 _sum_dif_amount：累加非 null 的 difAmount，非 0 时四舍五入到 2 位。
func sumDifAmount(records []*carExceptRecord) *float64 {
	sum := 0.0
	for _, record := range records {
		if record.DifAmount != nil {
			sum += *record.DifAmount
		}
	}
	if sum != 0 {
		sum = halfUp(sum)
	}
	return &sum
}

func halfUp(v float64) float64 { return math.Round(v*100) / 100 }

// confimFreeSave 对应 saveCarConfimFree（新增/修改共用）。
func (h *handler) confimFreeSave(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	exceptIDs := deleteEnd(bodyString(body, "exceptIds"))
	if exceptIDs == "" {
		web.JSON(c, web.ErrorMsg("请选择车辆异常流水！"))
		return
	}
	exceptIDList := splitCSV(exceptIDs)
	id := bodyString(body, "id")
	if id == "" {
		exists := h.confimFreeByExceptIDs(c, exceptIDList)
		if len(exists) > 0 {
			web.JSON(c, web.ErrorMsg("车辆补缴单已追缴，请勿重复补缴！"))
			return
		}
	}

	records := h.exceptRecordsByIDs(c, exceptIDs)
	difAmount := *sumDifAmount(records)

	// @RequestBody 的 carAduitFreeList
	var aduitList []*carAduitFree
	if raw, ok := body["carAduitFreeList"]; ok && raw != nil {
		encoded, _ := json.Marshal(raw)
		_ = json.Unmarshal(encoded, &aduitList)
	}
	aduitAmount := 0.0
	escapedTypes := ""
	if len(aduitList) > 0 {
		for _, item := range aduitList {
			if item.Amount != nil {
				aduitAmount += *item.Amount
			}
		}
		var types []string
		for _, record := range records {
			types = append(types, isNull(record.EscapedType))
		}
		escapedTypes = strings.Join(types, ",")
	}

	amount := 0.0
	if v, ok := body["amount"].(float64); ok {
		amount = v
	}
	comfimFreeType := bodyString(body, "comfimFreeType")
	if comfimFreeType != "waibu" {
		if halfUp(amount+aduitAmount) != difAmount {
			web.JSON(c, web.ErrorMsg("录入信息的拆分金额和处理信息的拆分金额合计不等于逃费金额！"))
			return
		}
	}

	cols := pickColumns(body, carConfimFreeColumns)
	if len(aduitList) > 0 {
		cols["aduit_amount"] = aduitAmount
		cols["escaped_types"] = escapedTypes
	}
	now := time.Now()
	if id != "" {
		withUpdateAudit(c, cols)
		if _, err := h.updateRow(c.Request.Context(), carConfimFreeTable, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		status := "0"
		if comfimFreeType == "waibu" {
			status = "1"
		}
		cols["status"] = status
		id = newUUID()
		cols["id"] = id
		h.withInsertAudit(c, cols)
		if err := h.insertRow(c.Request.Context(), carConfimFreeTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}

	if comfimFreeType == "waibu" {
		h.updateExceptStatus(c, exceptIDList, "1")
		h.markSuspicious(c, records)
	} else if len(aduitList) > 0 {
		if err := h.app.DB.WithContext(c.Request.Context()).Exec(
			"DELETE FROM car_aduit_free WHERE confirm_id = ?", id).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		userID := currentUserID(c)
		for _, item := range aduitList {
			item.ID = strPtr(newUUID())
			item.ConfirmID = strPtr(id)
			item.CarID = strPtr(bodyString(body, "carNo")) // Java 把 carNo 塞进 carId
			item.CarType = strPtr(bodyString(body, "carType"))
			item.CarVehicle = strPtr(bodyString(body, "carVehicle"))
			item.CarNo = strPtr(bodyString(body, "carNo"))
			item.DelFlag = strPtr("0")
			item.CreateBy = &userID
			item.UpdateBy = &userID
			item.CreateTime = ptrDateTime(now)
			item.UpdateTime = ptrDateTime(now)
			if err := h.app.DB.WithContext(c.Request.Context()).Table(carAduitFreeTable).Create(map[string]any{
				"id": item.ID, "confirm_id": item.ConfirmID, "car_id": item.CarID,
				"car_no": item.CarNo, "car_type": item.CarType, "car_vehicle": item.CarVehicle,
				"org_id": item.OrgID, "user_ids": item.UserIDs, "user_names": item.UserNames,
				"amount": item.Amount, "back_col1": item.BackCol1, "back_col2": item.BackCol2,
				"remark": item.Remark, "status": item.Status, "del_flag": "0",
				"create_by": userID, "create_time": now, "update_by": userID, "update_time": now,
			}).Error; err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
		}
		h.updateExceptStatus(c, exceptIDList, "1")
		h.markSuspicious(c, records)
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// confimFreeByExceptIDs 对应 selectCarConfimFreeByExceptIds（OR find_in_set）。
func (h *handler) confimFreeByExceptIDs(c *gin.Context, exceptIDs []string) []*carConfimFree {
	if len(exceptIDs) == 0 {
		return nil
	}
	parts := make([]string, 0, len(exceptIDs))
	args := make([]any, 0, len(exceptIDs))
	for _, exceptID := range exceptIDs {
		parts = append(parts, "find_in_set(?, t.except_ids) > 0")
		args = append(args, exceptID)
	}
	sqlStr := "SELECT " + carConfimFreeSelectColumns +
		" FROM car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id WHERE t.del_flag = '0' AND (" +
		strings.Join(parts, " OR ") + ")"
	rows := newSliceOf(&carConfimFree{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(rows).Error; err != nil {
		return nil
	}
	return *(rows.(*[]*carConfimFree))
}

// updateExceptStatus 对应 updateStatusByExceptId。
func (h *handler) updateExceptStatus(c *gin.Context, exceptIDs []string, status string) {
	if len(exceptIDs) == 0 {
		return
	}
	_ = h.app.DB.WithContext(c.Request.Context()).Table(carExceptRecordTable).
		Where("id IN ?", exceptIDs).Update("status", status).Error
}

// markSuspicious 把明细关联的可疑车辆状态改成 1。
func (h *handler) markSuspicious(c *gin.Context, records []*carExceptRecord) {
	for _, record := range records {
		if !isNotBlank(record.CarID) {
			continue
		}
		_ = h.app.DB.WithContext(c.Request.Context()).Table(carSuspiciousTable).
			Where("id = ? AND del_flag = '0'", record.CarID).Update("status", "1").Error
	}
}

// confimFreeDelete 对应 deleteCarConfimFreeByIds：删明细 -> 异常流水状态回 0 -> 逻辑删除。
func (h *handler) confimFreeDelete(c *gin.Context) {
	ids := splitCSV(c.Param("ids"))
	var count int64
	if len(ids) > 0 {
		var exceptIDs []string
		for _, id := range ids {
			entity := &carConfimFree{}
			_ = h.app.DB.WithContext(c.Request.Context()).Table(carConfimFreeTable).
				Select("id, except_ids").Where("id = ?", id).Scan(entity).Error
			if isNotBlank(entity.ExceptIDs) {
				exceptIDs = append(exceptIDs, splitCSV(deleteEnd(entity.ExceptIDs))...)
			}
			_ = h.app.DB.WithContext(c.Request.Context()).Exec(
				"DELETE FROM car_aduit_free WHERE confirm_id = ?", id).Error
		}
		h.updateExceptStatus(c, exceptIDs, "0")
		var err error
		count, err = h.softDeleteByIDs(c.Request.Context(), carConfimFreeTable, ids)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	web.JSON(c, web.SuccessData(count))
}

// confimFreeExport 对应 EasyPOI 模板 carConfirm.xlsx。
func (h *handler) confimFreeExport(c *gin.Context) {
	clause, args := buildWhere(c, confimFreeSpec.prefix(), confimFreeSpec.conditions)
	dest := newSliceOf(&carConfimFree{})
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: confimFreeSpec.selectSQL,
		FromSQL:   confimFreeSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   confimFreeSpec.orderBy,
	}, dest); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows := *(dest.(*[]*carConfimFree))
	carTypes, _ := h.dictValueLabel(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictValueLabel(c.Request.Context(), "car_vehicle")
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		carType := carTypes[strOf(row.CarType)]
		carVehicle := carVehicles[strOf(row.CarVehicle)]
		out = append(out, []any{row.CarNo, row.LinkName, row.LinkPhone, row.OrgName,
			plainValue(row.Amount), plainValue(row.AduitAmount), row.Status, plainValue(row.CreateTime), row.Remark,
			carType, carVehicle})
	}
	cols := []exportCol{{Title: "车牌号"}, {Title: "司机姓名"}, {Title: "联系方式"}, {Title: "录入单位"},
		{Title: "补缴金额（元）"}, {Title: "处理金额（元）"}, {Title: "状态"}, {Title: "录入时间"}, {Title: "备注"},
		{Title: "车型"}, {Title: "车种"}}
	data, err := buildWorkbook("确认补缴", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "carConfirm.xlsx", data)
}

// confimFreeExcept 对应 GET /except/{exceptIds}（选择异常查询回显）。
func (h *handler) confimFreeExcept(c *gin.Context) {
	exceptIDs := deleteEnd(c.Param("exceptIds"))
	entity := &carConfimFree{}
	if exceptIDs == "" {
		web.JSON(c, web.ErrorMsg("请选择车辆异常流水！"))
		return
	}
	records := h.exceptRecordsByIDs(c, exceptIDs)
	entity.CarExceptRecordList = records
	if len(records) == 0 {
		web.JSON(c, web.ErrorMsg("异常车辆流水不存在！"))
		return
	}
	carNoSet := map[string]struct{}{}
	epsSet := map[int64]struct{}{}
	var firstEps *int64
	for _, record := range records {
		carNoSet[strOf(record.CarNo)] = struct{}{}
		if record.EpsID != nil {
			epsSet[*record.EpsID] = struct{}{}
			if firstEps == nil {
				firstEps = record.EpsID
			}
		}
	}
	if len(carNoSet) > 1 {
		web.JSON(c, web.ErrorMsg("请勿选择多辆车！"))
		return
	}
	if len(epsSet) > 1 {
		web.JSON(c, web.ErrorMsg("选择的异常流水存在多个录入单位，请确认！"))
		return
	}
	if len(epsSet) > 0 && firstEps != nil {
		entity.OrgID = strPtr(strconv.FormatInt(*firstEps, 10))
	} else if len(epsSet) > 0 {
		entity.OrgID = strPtr("null")
	}
	if exists := h.confimFreeByExceptIDs(c, splitCSV(exceptIDs)); len(exists) > 0 {
		web.JSON(c, web.ErrorMsg("车辆补缴单已追缴，请勿重复补缴！"))
		return
	}
	first := records[0]
	entity.CarID = first.CarID
	entity.CarNo = first.CarNo
	entity.CarType = first.CarType
	entity.CarVehicle = first.CarVehicle
	entity.ExceptIDs = strPtr(exceptIDs)

	difAmount := *sumDifAmount(records)
	tempCfAmount := difAmount * 0.3
	amount := halfUp(tempCfAmount)
	entity.DifAmount = &difAmount
	entity.BackCol1 = strPtr("0.3")
	entity.Amount = &amount
	web.JSON(c, web.SuccessData(entity))
}

// concernedRow 对应 selectConcernedList 的 resultType 列。
type concernedRow struct {
	ID           *string  `gorm:"column:id"`
	CarNo        *string  `gorm:"column:car_no"`
	CarType      *string  `gorm:"column:car_type"`
	CarVehicle   *string  `gorm:"column:car_vehicle"`
	EscapedType  *string  `gorm:"column:escaped_type"`
	OrgID        *string  `gorm:"column:org_id"`
	OrgName      *string  `gorm:"column:org_name"`
	TotalAmount  *float64 `gorm:"column:total_amount"`
	ChargeAmount *float64 `gorm:"column:charge_amount"`
	DifAmount    *float64 `gorm:"column:dif_amount"`
	ExceptIDs    *string  `gorm:"column:except_ids"`
}

// confimFreeConcernedList 对应 selectConcernedList（car_info JOIN 聚合派生表）。
// JAVA 对照: CarConfimFreeController.concernedList:172-173 先 startPage()，默认 1/10。
func (h *handler) confimFreeConcernedList(c *gin.Context) {
	rows, total, err := h.concernedList(c, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// confimFreeExportConcernedList 对应导出：Java 未 startPage，导出全量。
func (h *handler) confimFreeExportConcernedList(c *gin.Context) {
	rows, _, err := h.concernedList(c, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	carTypes, _ := h.dictValueLabel(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictValueLabel(c.Request.Context(), "car_vehicle")
	escapedTypes, _ := h.dictValueLabel(c.Request.Context(), "escaped_type")
	cols := []exportCol{{Title: "车牌号"}, {Title: "车型"}, {Title: "车种"}, {Title: "逃费类型"},
		{Title: "录入单位"}, {Title: "应缴金额（元）"}, {Title: "收费金额（元）"}, {Title: "差额（元）"}, {Title: "备注"}}
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		var names []string
		for _, part := range splitCSV(deleteEnd(row.EscapedType)) {
			if label, ok := escapedTypes[part]; ok {
				names = append(names, label)
			}
		}
		out = append(out, []any{row.CarNo, carTypes[strOf(row.CarType)], carVehicles[strOf(row.CarVehicle)],
			strings.Join(names, ","), row.OrgName, plainValue(row.TotalAmount),
			plainValue(row.ChargeAmount), plainValue(row.DifAmount), ""})
	}
	data, err := buildWorkbook("待关注车辆", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "concernedList.xlsx", data)
}

func (h *handler) concernedList(c *gin.Context, page web.PageDomain) ([]*carConfimFree, int64, error) {
	base := "SELECT t.id, t.car_no, t.car_type, t.car_vehicle, t.escaped_type, t.org_id, sd.dept_name AS org_name, " +
		"k.total_amount AS total_amount, k.charge_amount AS charge_amount, k.dif_amount AS dif_amount, k.except_ids " +
		"FROM car_info t JOIN (SELECT t1.car_no, sum(t1.total_amount) total_amount, sum(t1.charge_amount) charge_amount, " +
		"sum(t1.dif_amount) dif_amount, sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num, " +
		"GROUP_CONCAT(t1.id SEPARATOR ',') except_ids FROM car_except_record t1 WHERE t1.del_flag = '0' " +
		"GROUP BY t1.car_no) k ON k.count_num > 0 AND k.except_num = 0 AND t.car_no = k.car_no " +
		"LEFT JOIN sys_dept sd ON sd.dept_id = t.eps_id AND sd.del_flag = '0' WHERE t.del_flag = '0'"
	// CONDITIONS_CONCERNED：部分条件打在不存在的列上（Java 原样），这里照抄。
	conds := []cond{
		eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
		eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
		likeCond("linkName", "t.link_name"), eqCond("linkPhone", "t.link_phone"),
		eqCond("orgId", "t.org_id"), tmplCond("orgName", "sd.dept_name LIKE CONCAT('%', ?, '%')"),
		eqCond("userIds", "t.user_ids"), eqCond("userNames", "t.user_names"),
		nullCond("amount", "t.amount"), eqCond("escapedTypes", "t.escaped_types"),
		eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
		eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		inSetCond("exceptIds"), likeCond("carNoQuery", "t.car_no"),
		dateTimeGe("applyTime1", "create_time"), dateTimeLe("applyTime2", "create_time"),
	}
	// buildWhere 需要完整 WHERE；base 已带 WHERE，这里只拼额外条件。
	extra, queryArgs := buildWhere(c, "", conds)
	sqlStr := base + extra
	var total int64
	if page.HasPage {
		if err := h.app.DB.WithContext(c.Request.Context()).
			Raw("SELECT COUNT(0) FROM ("+sqlStr+") table_count", queryArgs...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	if page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := page.LimitOffset(total)
		queryArgs = append(queryArgs, lim, off)
	}
	var rows []*concernedRow
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, queryArgs...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !page.HasPage {
		total = int64(len(rows))
	}
	out := make([]*carConfimFree, 0, len(rows))
	for _, row := range rows {
		out = append(out, &carConfimFree{
			EntityBase:   EntityBase{ID: row.ID},
			CarNo:        row.CarNo,
			CarType:      row.CarType,
			CarVehicle:   row.CarVehicle,
			EscapedType:  row.EscapedType,
			OrgID:        row.OrgID,
			OrgName:      row.OrgName,
			TotalAmount:  row.TotalAmount,
			ChargeAmount: row.ChargeAmount,
			DifAmount:    row.DifAmount,
			ExceptIDs:    row.ExceptIDs,
		})
	}
	return out, total, nil
}

// confimFreeCarStatics 对应 getPCCarStatistics（按单位聚合 6 种逃费类型）。
func (h *handler) confimFreeCarStatics(c *gin.Context) {
	rows, total, err := h.pcCarStatistics(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

func (h *handler) confimFreeExportCarStatics(c *gin.Context) {
	rows, _, err := h.pcCarStatistics(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	headers := []string{"录入单位", "少轴车辆数", "少轴金额（元）", "屏蔽车辆数", "屏蔽金额（元）",
		"货车客标车辆数", "货车客标金额（元）", "有入无出车辆数", "有入无出金额（元）",
		"绿通换挂车辆数", "绿通换挂金额（元）", "假冒减免车辆数", "假冒减免金额（元）", "合计车辆数", "合计金额（元）"}
	cols := make([]exportCol, len(headers))
	for i, title := range headers {
		cols[i] = exportCol{Title: title}
	}
	out := make([][]any, 0, len(rows))
	for _, row := range rows {
		out = append(out, []any{plainValue(row.OrgName),
			row.EscapedType10Num, row.EscapedType10Amount, row.EscapedType20Num, row.EscapedType20Amount,
			row.EscapedType30Num, row.EscapedType30Amount, row.EscapedType40Num, row.EscapedType40Amount,
			row.EscapedType50Num, row.EscapedType50Amount, row.EscapedType60Num, row.EscapedType60Amount,
			row.TotalNum, row.TotalAmount})
	}
	data, err := buildWorkbook("车辆统计", cols, out)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	downloadAttachment(c, "carStatistics.xlsx", data)
}

// pcStatRow 是 getPCCarStatistics 的 SQL 行。
type pcStatRow struct {
	EpsID         string   `gorm:"column:eps_id"`
	OrgName       string   `gorm:"column:org_name"`
	EscapedType   string   `gorm:"column:escaped_type"`
	EscapedAmount *float64 `gorm:"column:escaped_amount"`
	Number        *int64   `gorm:"column:number"`
}

func (h *handler) pcCarStatistics(c *gin.Context) ([]*pcCarStatisticsVO, int64, error) {
	sqlStr := "SELECT d.dept_id eps_id, d.dept_name org_name, a.escaped_type, " +
		"sum(ifnull(a.dif_amount, 0)) escaped_amount, count(distinct a.car_no) number " +
		"FROM car_except_record a INNER JOIN sys_dept d ON a.eps_id = d.dept_id AND d.del_flag = '0' " +
		"WHERE a.del_flag = '0'"
	var args []any
	if v := argString(c, "applyTime1"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		sqlStr += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	if v := argString(c, "escapedType"); v != "" {
		sqlStr += " AND a.escaped_type = ?"
		args = append(args, v)
	}
	if v := argString(c, "orgId"); v != "" {
		sqlStr += " AND a.eps_id = ?"
		args = append(args, v)
	}
	sqlStr += " GROUP BY d.dept_id,d.dept_name,a.escaped_type"
	page := web.Page(c)
	var total int64
	if page.HasPage {
		if err := h.app.DB.WithContext(c.Request.Context()).
			Raw("SELECT COUNT(0) FROM ("+sqlStr+") table_count", args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	queryArgs := args
	if page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := page.LimitOffset(total)
		queryArgs = append(append([]any{}, args...), lim, off)
	}
	var statRows []*pcStatRow
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, queryArgs...).Scan(&statRows).Error; err != nil {
		return nil, 0, err
	}
	// JAVA 对照: startPage() 分页的是 mapper 的 group by 结果行，而 service 之后
	// 会把分页结果重新聚合成 VO 列表；getDataTable 拿到的是这个 ArrayList，
	// 所以 total 退化成 list.size()（Java 原样，不修正）。
	var deptList []string
	deptMap := map[string]string{}
	exceptMap := map[string]*pcStatRow{}
	for _, row := range statRows {
		if isNotBlank(row.EpsID) {
			if _, ok := deptMap[row.EpsID]; !ok {
				deptList = append(deptList, row.EpsID)
				deptMap[row.EpsID] = row.OrgName
			}
			exceptMap[row.EpsID+row.EscapedType] = row
		}
	}
	out := make([]*pcCarStatisticsVO, 0, len(deptList))
	for _, org := range deptList {
		vo := &pcCarStatisticsVO{OrgID: &org}
		orgName := deptMap[org]
		vo.OrgName = &orgName
		for _, item := range []struct {
			key    string
			num    *int64
			amount *float64
		}{
			{"10", &vo.EscapedType10Num, &vo.EscapedType10Amount},
			{"20", &vo.EscapedType20Num, &vo.EscapedType20Amount},
			{"30", &vo.EscapedType30Num, &vo.EscapedType30Amount},
			{"40", &vo.EscapedType40Num, &vo.EscapedType40Amount},
			{"50", &vo.EscapedType50Num, &vo.EscapedType50Amount},
			{"60", &vo.EscapedType60Num, &vo.EscapedType60Amount},
		} {
			found := exceptMap[org+item.key]
			if found == nil {
				continue
			}
			if found.Number != nil {
				*item.num = *found.Number
				vo.TotalNum += *found.Number
			}
			if found.EscapedAmount != nil {
				*item.amount = *found.EscapedAmount
				vo.TotalAmount += *found.EscapedAmount
			}
		}
		vo.TotalAmount = halfUp(vo.TotalAmount)
		out = append(out, vo)
	}
	return out, int64(len(out)), nil
}

// ---------------------------------------------------------------- 大屏统计支撑

func (h *handler) aduitGetCarAudit(c *gin.Context) *carStatisticsVO {
	sqlStr := "SELECT sum(ifnull(a.dif_amount, 0)) AS escaped_amount, count(distinct a.car_no) AS number " +
		"FROM car_except_record a WHERE a.del_flag = '0'"
	var args []any
	if v := argString(c, "applyTime1"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		sqlStr += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	var row struct {
		EscapedAmount *float64 `gorm:"column:escaped_amount"`
		Number        *int64   `gorm:"column:number"`
	}
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&row)
	if tx.Error != nil || tx.RowsAffected == 0 {
		return nil
	}
	vo := &carStatisticsVO{}
	if row.EscapedAmount != nil {
		vo.EscapedAmount = *row.EscapedAmount
	}
	if row.Number != nil {
		vo.Number = *row.Number
	}
	return vo
}

func (h *handler) confimGetCarConfirm(c *gin.Context) *carStatisticsVO {
	sqlStr := "SELECT sum(ifnull(a.amount, 0) + ifnull(a.aduit_amount, 0)) AS escaped_amount, " +
		"count(distinct a.car_no) AS number FROM car_confim_free a " +
		"WHERE a.del_flag = '0' AND a.status = '0'"
	var args []any
	if v := argString(c, "applyTime1"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		sqlStr += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	var row struct {
		EscapedAmount *float64 `gorm:"column:escaped_amount"`
		Number        *int64   `gorm:"column:number"`
	}
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&row)
	if tx.Error != nil || tx.RowsAffected == 0 {
		return nil
	}
	vo := &carStatisticsVO{}
	if row.EscapedAmount != nil {
		vo.EscapedAmount = *row.EscapedAmount
	}
	if row.Number != nil {
		vo.Number = *row.Number
	}
	return vo
}

// confimGetCarStatistics 对应 getCarStatistics：按字典顺序输出，缺失补 0。
func (h *handler) confimGetCarStatistics(c *gin.Context) []*carStatisticsVO {
	dictRows, err := h.loadDict(c.Request.Context(), "escaped_type")
	if err != nil {
		return nil
	}
	sqlStr := "SELECT a.escaped_type, sum(ifnull(a.dif_amount, 0)) AS escaped_amount, " +
		"count(distinct a.car_no) AS number FROM car_except_record a WHERE a.del_flag = '0'"
	var args []any
	if v := argString(c, "applyTime1"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		sqlStr += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	if v := argString(c, "escapedType"); v != "" {
		sqlStr += " AND a.escaped_type = ?"
		args = append(args, v)
	}
	if v := argString(c, "orgId"); v != "" {
		sqlStr += " AND a.eps_id = ?"
		args = append(args, v)
	}
	sqlStr += " GROUP BY a.escaped_type"
	var rows []*carStatisticsVO
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&rows).Error; err != nil {
		return nil
	}
	voMap := map[string]*carStatisticsVO{}
	for _, row := range rows {
		voMap[row.EscapedType] = row
	}
	out := make([]*carStatisticsVO, 0, len(dictRows))
	for _, item := range dictRows {
		vo := &carStatisticsVO{EscapedType: item.DictValue, EscapedTypeName: item.DictLabel}
		if found, ok := voMap[item.DictValue]; ok {
			vo.Number = found.Number
			vo.EscapedAmount = found.EscapedAmount
		}
		out = append(out, vo)
	}
	return out
}

// aduitIncomeStatistic 对应 incomeStatistic（按机构汇总，UNION ALL）。
func (h *handler) aduitIncomeStatistic(c *gin.Context) []*incomeStatisticVO {
	sqlStr := "SELECT sum(ifnull(amount, 0)) AS amount, count(distinct car_no) AS car_num, " +
		"d.dept_name AS org_name, a.org_id FROM (" +
		"SELECT t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status FROM car_confim_free t " +
		"WHERE t.del_flag = '0' AND t.status = '0' UNION ALL " +
		"SELECT t.car_no,t.amount,t.org_id,t.create_time,t.del_flag,t.status FROM car_aduit_free t " +
		"WHERE t.del_flag = '0') a " +
		"LEFT JOIN sys_dept d ON d.dept_id = a.org_id AND d.del_flag = '0' WHERE a.del_flag = '0'"
	var args []any
	queryDateType := argString(c, "queryDateType")
	if queryDateType == "suo" {
		sqlStr += " AND a.status = '0'"
	}
	if v := argString(c, "startDate"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d') AND a.create_time < LAST_DAY(?)"
		args = append(args, v, v)
	}
	if queryDateType == "suo" {
		sqlStr += " AND d.tree_leavel = 2"
	}
	if queryDateType == "zhan" {
		sqlStr += " AND d.tree_leavel = 3"
	}
	if v := argString(c, "applyTime1"); v != "" {
		sqlStr += " AND a.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		sqlStr += " AND a.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	sqlStr += " GROUP BY a.org_id ORDER BY amount DESC"
	var rows []*incomeStatisticVO
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&rows).Error; err != nil {
		return nil
	}
	return rows
}
