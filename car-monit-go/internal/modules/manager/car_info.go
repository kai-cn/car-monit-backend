// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml
// 类/职责: 重点车辆库（car_info）控制器
// 对应 Go 文件: internal/modules/manager/car_info.go
//
// DIFF: Java 详情里的轨迹回填走 ICarTrackInfoService 的路网 Geometry 计算；
// Go 侧只还原 trackJosn 到 trailList，raodTrailList 固定空数组、trailDevCountBO 为 null
// （与 Python 迁移版的降级策略一致）。
package manager

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/auth"
	"car-monit-go/internal/cache"
	"car-monit-go/internal/web"
)

// carInfoSpec 对应 CarInfoMapper.xml（固定 WHERE 前缀里带 not exists）。
var carInfoSpec = &tableSpec{
	table:     carInfoTable,
	selectSQL: carInfoSelectColumns,
	fromSQL:   "car_info t left join sys_user su on su.user_id = t.create_by left join sys_dept sd on t.eps_id = sd.dept_id",
	wherePrefix: "WHERE t.del_flag = '0' and not exists ( select 1 from (select t1.car_no, " +
		"sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num " +
		"from car_except_record t1 where t1.del_flag = '0' group by t1.car_no ) k " +
		"where t.car_no = k.car_no and k.count_num > 0 and k.except_num = 0 )",
	selectSuffix: ",concat(sd.dept_name, ' ', su.nick_name) AS create_info",
	detailSuffix: ",t.track_josn",
	detailFrom:   "car_info t",
	orderBy:      "t.create_time desc,t.id",
	columns:      carInfoColumns,
	prototype:    &carInfo{},
	conditions: []cond{
		eqCond("id", "t.id"), eqCond("carNo", "t.car_no"), eqCond("carType", "t.car_type"),
		eqCond("carVehicle", "t.car_vehicle"), nullCond("carNum", "t.car_num"),
		likeCond("escapedType", "t.escaped_type"), likeCond("escapedTypeName", "t.escaped_type_name"),
		nullCond("escapedAmount", "t.escaped_amount"), nullCond("escapedNum", "t.escaped_num"),
		nullCond("returnAmount", "t.return_amount"), nullCond("totalAmount", "t.total_amount"),
		nullCond("chargeAmount", "t.charge_amount"), nullCond("difAmount", "t.dif_amount"),
		eqCond("auitOrgId", "t.auit_org_id"), likeCond("auitOrgName", "t.auit_org_name"),
		eqCond("isWhite", "t.is_white"), eqCond("whiteRemark", "t.white_remark"),
		eqCond("fileIds", "t.file_ids"), eqCond("brand", "t.brand"),
		eqCond("plateColor", "t.plate_color"), eqCond("plateType", "t.plate_type"),
		eqCond("carColor", "t.car_color"), eqCond("dataSource", "t.data_source"),
		likeCond("dataSourceName", "t.data_source_name"), nullCond("lastPassTime", "t.last_pass_time"),
		eqCond("lastPassPicture", "t.last_pass_picture"), eqCond("lastPassType", "t.last_pass_type"),
		eqCond("lastPassAddress", "t.last_pass_address"), eqCond("lastPassLongitude", "t.last_pass_longitude"),
		eqCond("lastPassLatitude", "t.last_pass_latitude"), eqCond("lastPassCardirection", "t.last_pass_cardirection"),
		eqCond("roadSectionId", "t.road_section_id"), eqCond("sectionCode", "t.section_code"),
		likeCond("roadSectionName", "t.road_section_name"), nullCond("nextPassTime", "t.next_pass_time"),
		eqCond("nextPassType", "t.next_pass_type"), eqCond("nextPassAddress", "t.next_pass_address"),
		eqCond("nextPassLongitude", "t.next_pass_longitude"), eqCond("nextPassLatitude", "t.next_pass_latitude"),
		eqCond("orgId", "t.org_id"), eqCond("orgCode", "t.org_code"),
		likeCond("orgName", "t.org_name"), eqCond("gantryCode", "t.gantry_code"),
		eqCond("roadCode", "t.road_code"), likeCond("roadName", "t.road_name"),
		eqCond("tollCode", "t.toll_code"), likeCond("tollName", "t.toll_name"),
		likeCond("linkName", "t.link_name"), eqCond("linkPhone", "t.link_phone"),
		eqCond("fwqbm", "t.fwqbm"), eqCond("fwqmc", "t.fwqmc"),
		eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
		eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
		nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		likeCond("carNoQuery", "t.car_no"),
		dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		tmplCond("createInfo", "sd.dept_name LIKE CONCAT('%', ?, '%')"),
	},
}

// carInfoClause 组装列表 WHERE：XML 最后的 <if test="flag != null and flag == 'noTrack'">。
func carInfoClause(c *gin.Context) (string, []any) {
	clause, args := buildWhere(c, carInfoSpec.prefix(), carInfoSpec.conditions)
	if isNull(queryParam(c, "flag")) == "noTrack" {
		clause += " AND not exists ( select 1 from zdata_trail_tracks tr where tr.plate_key = t.car_no )"
	}
	return clause, args
}

// carInfoList 对应 GET /list 与 GET /listAll（同一实现，后者无权限点）。
func (h *handler) carInfoList(c *gin.Context) {
	clause, args := carInfoClause(c)
	h.respondList(c, carInfoSpec, clause, args)
}

// carInfoGet 对应 GET /{id} —— 回填 trailList。
func (h *handler) carInfoGet(c *gin.Context) {
	sqlStr := "SELECT " + carInfoSpec.selectSQL + carInfoSpec.detailSuffix + " FROM car_info t WHERE t.id = ?"
	dest := &carInfo{}
	tx := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, c.Param("id")).Scan(dest)
	if tx.Error != nil {
		web.JSON(c, web.ErrorResult(tx.Error))
		return
	}
	if tx.RowsAffected == 0 {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	trail := &trailInfo{}
	if isNull(dest.Status) == "1" && isNotBlank(dest.TrackJosn) {
		parsed, tracks, points, err := parseTrailInfo(strOf(dest.TrackJosn))
		if err == nil {
			trail = parsed
		}
		carNo := strOf(dest.CarNo)
		trail.TrailUUID = strPtr(carNo)
		// DIFF: Java 的 raodTrailList 由 getCarGeometryByPlanNew（路网 Geometry + 路线规划接口）
		// 生成，本模块不复现该几何计算，只保证它是空数组（未取到点时 Java 同样为空）。
		trail.RaodTrailList = []any{}
		applyPilenoDec(points)
		trail.TrailDevCountBO = trailDevCount(tracks, points)
	}
	dest.TrailList = []*trailInfo{trail}
	web.JSON(c, web.SuccessData(dest))
}

// carInfoSave 对应 saveCarInfo：车牌查重 -> 新增/修改 -> 刷新 car_list 缓存。
func (h *handler) carInfoSave(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	cols := pickColumns(body, carInfoColumns)
	id := bodyString(body, "id")
	carNo := isNull(bodyString(body, "carNo"))
	cols["car_no"] = carNo

	// 判断车牌号是否重复（id 不同时算重复）
	var count int64
	dupSQL := "SELECT COUNT(1) FROM car_info t WHERE t.del_flag = '0' AND t.car_no = ?"
	dupArgs := []any{carNo}
	if id != "" {
		dupSQL += " AND t.id != ?"
		dupArgs = append(dupArgs, id)
	}
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(dupSQL, dupArgs...).Scan(&count).Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if count > 0 {
		web.JSON(c, web.ErrorMsg("车牌号存在重复，请确定！"))
		return
	}

	if id != "" {
		withUpdateAudit(c, cols)
		if _, err := h.updateRow(c.Request.Context(), carInfoTable, id, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	} else {
		if _, ok := cols["escaped_amount"]; !ok {
			cols["escaped_amount"] = 0
		}
		// JAVA 对照: CarInfoServiceImpl.saveCarInfo:145-149 —— 新增时服务层显式写
		// epsId/createBy/updateBy/updateTime；epsId 已非空，insertFill 的 tenantId
		// 守卫不成立，所以 car_info.tenant_id 落 NULL（其余表由 insertFill 填 -1）。
		userID := currentUserID(c)
		now := auditNow()
		cols["eps_id"] = currentEpsID(c)
		cols["update_by"] = userID
		cols["update_time"] = now
		id = newUUID()
		cols["id"] = id
		h.withInsertAudit(c, cols)
		if err := h.insertRow(c.Request.Context(), carInfoTable, cols); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	if err := h.refreshCarList(c); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessFull("操作成功！", id))
}

// carInfoDelete 对应 deleteCarInfoByIds —— **不**刷新缓存（Java 原文如此）。
func (h *handler) carInfoDelete(c *gin.Context) {
	ids := splitCSV(c.Param("ids"))
	count, err := h.softDeleteByIDs(c.Request.Context(), carInfoTable, ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// carInfoExport 对应 EasyPOI 模板导出 carInfo.xlsx（附件流）。
func (h *handler) carInfoExport(c *gin.Context) {
	clause, args := carInfoClause(c)
	cols := []exportCol{
		{Title: "车牌颜色", Field: "plateColor", Dict: "plate_color", BlankOnMiss: true},
		{Title: "车牌号", Field: "carNo"},
		{Title: "车型", Field: "carType", Dict: "car_type", BlankOnMiss: true},
		{Title: "车种", Field: "carVehicle", Dict: "car_vehicle", BlankOnMiss: true},
		{Title: "轴数", Field: "carNum"},
		// 逃费类型是多值串，只由下面的 transform 映射（这里挂 Dict 会让 transform
		// 拿到的是标签而不是原码，二次映射必然落空）。
		{Title: "逃费类型", Field: "escapedType"},
		{Title: "逃费金额（元）", Field: "escapedAmount", Money: true},
		{Title: "备注", Field: "remark"},
	}
	// 逃费类型是多值逗号串，需要逐项映射后再拼回。
	escapedMap, err := h.dictValueLabel(c.Request.Context(), "escaped_type")
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	transform := func(values []any) {
		raw := fmt.Sprint(values[5])
		if raw == "" {
			return
		}
		var names []string
		for _, part := range strings.Split(deleteEnd(raw), ",") {
			if label, ok := escapedMap[strings.TrimSpace(part)]; ok {
				names = append(names, label)
			}
		}
		values[5] = strings.Join(names, ",")
	}
	h.exportWithClause(c, carInfoSpec, clause, args, "carInfo.xlsx", "车辆信息", cols, false, transform)
}

// carInfoImport 对应 POST /import（模板 importCar.xlsx）。
//
// DIFF: Java ImportSysUtil 的完整校验规则（必填/整数/小数/重复）在此按同等语义实现，
// 错误对象只保留 {rowNum,colName,errorMsg} 三个字段。
func (h *handler) carInfoImport(c *gin.Context) {
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
	headers := []string{"车牌颜色", "车牌号", "车型", "车种", "轴数", "逃费类型", "逃费金额（元）", "备注"}
	if len(rows) == 0 || !sameHeader(rows[0], headers) {
		web.JSON(c, web.ErrorMsg("导入失败,模板不正确,请下载对应的模板！"))
		return
	}
	if len(rows) == 1 {
		web.JSON(c, web.ErrorMsg("导入失败,模板excel没有数据可以导入，请确定！"))
		return
	}

	plateColors, _ := h.dictLabelValue(c.Request.Context(), "plate_color")
	carTypes, _ := h.dictLabelValue(c.Request.Context(), "car_type")
	carVehicles, _ := h.dictLabelValue(c.Request.Context(), "car_vehicle")
	escapedTypes, _ := h.dictLabelValue(c.Request.Context(), "escaped_type")

	type importError struct {
		RowNum   int    `json:"rowNum"`
		ColName  string `json:"colName"`
		ErrorMsg string `json:"errorMsg"`
	}
	var errList []importError
	importList := make([]*carInfo, 0, len(rows)-1)
	for i, row := range rows[1:] {
		rowNum := i + 1
		get := func(idx int) string {
			if idx < len(row) {
				return strings.TrimSpace(row[idx])
			}
			return ""
		}
		plateColor, carNo, carType, carVehicle := get(0), get(1), get(2), get(3)
		carNum, escapedType, escapedAmount, remark := get(4), get(5), get(6), get(7)
		if plateColor == "" {
			errList = append(errList, importError{rowNum, "车牌颜色", "车牌颜色不能为空"})
		}
		if carNo == "" {
			errList = append(errList, importError{rowNum, "车牌号", "车牌号不能为空"})
		}
		if carType == "" {
			errList = append(errList, importError{rowNum, "车型", "车型不能为空"})
		}
		if escapedType == "" {
			errList = append(errList, importError{rowNum, "逃费类型", "逃费类型不能为空"})
		}
		var carNumValue *int64
		if carNum != "" {
			v, err := strconv.ParseInt(carNum, 10, 64)
			if err != nil {
				errList = append(errList, importError{rowNum, "轴数", carNum + " 轴数格式不正确"})
			} else {
				carNumValue = &v
			}
		}
		var amountValue *float64
		if escapedAmount != "" {
			v, err := strconv.ParseFloat(escapedAmount, 64)
			if err != nil {
				errList = append(errList, importError{rowNum, "逃费金额（元）", escapedAmount + " 逃费金额格式不正确"})
			} else {
				amountValue = &v
			}
		}

		item := &carInfo{CarNo: strPtr(carNo), Remark: strPtr(remark), CarNum: carNumValue, EscapedAmount: amountValue}
		if value, ok := plateColors[plateColor]; ok {
			item.PlateColor = strPtr(value)
		} else {
			errList = append(errList, importError{rowNum, "车牌颜色", plateColor + " 车牌颜色不存在,请在字典菜单维护！"})
		}
		if value, ok := carTypes[carType]; ok {
			item.CarType = strPtr(value)
		} else {
			errList = append(errList, importError{rowNum, "车型", carType + " 车型不存在,请在字典菜单维护！"})
		}
		if carVehicle != "" {
			if value, ok := carVehicles[carVehicle]; ok {
				item.CarVehicle = strPtr(value)
			} else {
				errList = append(errList, importError{rowNum, "车种", carVehicle + " 车种不存在,请在字典菜单维护！"})
			}
		}
		var escapedValues []string
		for _, part := range strings.Split(deleteEnd(strings.ReplaceAll(escapedType, "，", ",")), ",") {
			part = strings.TrimSpace(part)
			if part == "" {
				continue
			}
			if value, ok := escapedTypes[part]; ok {
				escapedValues = append(escapedValues, value)
			} else {
				errList = append(errList, importError{rowNum, "逃费类型", part + " 逃费类型不存在,请在字典菜单维护！"})
			}
		}
		item.EscapedType = strPtr(strings.Join(escapedValues, ","))
		importList = append(importList, item)
		if len(errList) > 100 {
			break
		}
	}

	if len(errList) > 0 {
		web.JSON(c, web.ErrorData("error", errList))
		return
	}

	// 同车牌已存在则改为更新（Java: setId -> doImport 走 updateById）。
	now := time.Now()
	userID := auth.CurrentUserID(c)
	epsID := currentEpsID(c)
	for _, item := range importList {
		var existingID string
		if err := h.app.DB.WithContext(c.Request.Context()).
			Table(carInfoTable).Select("id").Where("del_flag = '0' AND car_no = ?", item.CarNo).
			Limit(1).Scan(&existingID).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		cols := map[string]any{
			"car_no": item.CarNo, "car_type": item.CarType, "car_vehicle": item.CarVehicle,
			"car_num": item.CarNum, "escaped_type": item.EscapedType, "remark": item.Remark,
			"plate_color": item.PlateColor, "escaped_amount": item.EscapedAmount,
			"update_by": userID, "update_time": now,
		}
		if existingID != "" {
			if _, err := h.updateRow(c.Request.Context(), carInfoTable, existingID, cols); err != nil {
				web.JSON(c, web.ErrorResult(err))
				return
			}
			item.ID = strPtr(existingID)
			continue
		}
		item.ID = strPtr(newUUID())
		item.DelFlag = strPtr("0")
		item.CreateBy = &userID
		item.UpdateBy = &userID
		item.EpsID = &epsID
		item.CreateTime = ptrDateTime(now)
		item.UpdateTime = ptrDateTime(now)
		if item.EscapedAmount == nil {
			item.EscapedAmount = ptrFloat(0)
		}
		if err := h.app.DB.WithContext(c.Request.Context()).Table(carInfoTable).Create(map[string]any{
			"id": item.ID, "car_no": item.CarNo, "car_type": item.CarType, "car_vehicle": item.CarVehicle,
			"car_num": item.CarNum, "escaped_type": item.EscapedType, "remark": item.Remark,
			"plate_color": item.PlateColor, "escaped_amount": item.EscapedAmount,
			"del_flag": "0", "create_by": userID, "create_time": now,
			"update_by": userID, "update_time": now, "eps_id": epsID,
		}).Error; err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	_ = h.refreshCarList(c)
	web.JSON(c, web.SuccessFull("数据导入成功", importList))
}

// refreshCarList 对应 updateRedisCarList：整份覆盖 car_list / car_list_jc。
func (h *handler) refreshCarList(c *gin.Context) error {
	return h.refreshCarListContext(c.Request.Context())
}

// refreshCarListContext 供定时任务等非 HTTP 场景复用。
func (h *handler) refreshCarListContext(ctx context.Context) error {
	rows := newSliceOf(&carInfo{})
	// Java: selectCarInfoList(new CarInfo()) —— 空条件，但固定前缀的 not exists 仍在。
	if _, err := h.list(ctx, listQuery{
		SelectSQL: carInfoSpec.selectSQL + carInfoSpec.selectSuffix,
		FromSQL:   carInfoSpec.from(),
		Where:     &whereClause{clause: carInfoSpec.prefix()},
		OrderBy:   carInfoSpec.orderBy,
	}, rows); err != nil {
		return err
	}
	cars := *(rows.(*[]*carInfo))
	jc := make([]*carVO, 0, len(cars))
	for _, item := range cars {
		jc = append(jc, &carVO{CarID: strOf(item.ID), CarNo: strOf(item.CarNo)})
	}
	if err := h.app.Cache.SetJava(ctx, carListJcKey, jc, time.Duration(cacheTTL), cache.CarVOJava); err != nil {
		return err
	}
	return h.app.Cache.SetJava(ctx, carListKey, cars, time.Duration(cacheTTL), cache.CarInfoJava)
}

// getRedisCarList 对应 getRedisCarList：命中直接用，未命中回源并回写 car_list。
func (h *handler) getRedisCarList(c *gin.Context) []*carInfo {
	var cached []*carInfo
	if h.app.Cache.Get(c.Request.Context(), carListKey, &cached) {
		return cached
	}
	if err := h.refreshCarList(c); err != nil {
		return nil
	}
	h.app.Cache.Get(c.Request.Context(), carListKey, &cached)
	return cached
}

func ptrDateTime(t time.Time) *web.DateTime { v := web.NewDateTime(t); return &v }
func ptrFloat(v float64) *float64           { return &v }
