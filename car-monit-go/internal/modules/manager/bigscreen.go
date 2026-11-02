// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java#syncCurrentTrack
// 类/职责: 大屏接口 + 实时轨迹同步
// 对应 Go 文件: internal/modules/manager/bigscreen.go
//
// DIFF: 实时轨迹同步里「预警的新增/删除」依赖 car_warning_config（base 模块）与轨迹状态机，
// Go 迁移版先实现 car_info 的在线状态与最新轨迹回写；预警差异计算留待 base 模块接入后补齐。
package manager

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

const carCurrentTrailKey = "car_curent_trail:"

type carLocationVO struct {
	ID           *string `json:"id"`
	CarNo        *string `json:"carNo"`
	CarType      *string `json:"carType"`
	LonStr       *string `json:"lonStr"`
	LatStr       *string `json:"latStr"`
	LastPassType *string `json:"lastPassType"`
	Lon          float64 `json:"lon"`
	Lat          float64 `json:"lat"`
	Status       *string `json:"status"`
}

type sectionVO struct {
	SectionCode *string `json:"sectionCode"`
	SectionName *string `json:"sectionName"`
}

type tollGantryFwqVO struct {
	Type *string `json:"type"`
	Code *string `json:"code"`
	Name *string `json:"name"`
}

type orgVO struct {
	OrgCode *string `json:"orgCode"`
	OrgName *string `json:"orgName"`
}

type carInfoVO struct {
	CarNo         *string  `json:"carNo"`
	CarType       *string  `json:"carType"`
	EscapedType   *string  `json:"escapedType"`
	EscapedAmount *float64 `json:"escapedAmount"`
}

type topTenVO struct {
	RoadCode    *string `json:"roadCode"`
	SectionName *string `json:"sectionName"`
	CarNum      int64   `json:"carNum"`
	Rank        int     `json:"rank"`
	Rate        *string `json:"rate"`
}

func registerBigScreen(reg *router.Registry, h *handler) {
	auth := reg.Authed
	auth.GET("/manager/bigScreen/carStatistics", h.bigCarStatistics)
	auth.GET("/manager/bigScreen/carLocation", h.bigCarLocation)
	auth.GET("/manager/bigScreen/sectionList", h.bigSectionList)
	auth.GET("/manager/bigScreen/tollGantryFwqList", h.bigTollGantryFwqList)
	auth.GET("/manager/bigScreen/carVoList", h.bigCarVoList)
	auth.GET("/manager/bigScreen/carAudit", h.bigCarAudit)
	auth.GET("/manager/bigScreen/carWarning", h.bigCarWarning)
	auth.GET("/manager/bigScreen/exceptionCar", h.bigExceptionCar)
	auth.GET("/manager/bigScreen/topTen", h.bigTopTen)
	auth.GET("/manager/bigScreen/orgList", h.bigOrgList)
	auth.GET("/manager/bigScreen/incomeStatistic", h.bigIncomeStatistic)
	auth.GET("/manager/bigScreen/exceptRecordList", h.bigExceptRecordList)
}

func (h *handler) bigCarStatistics(c *gin.Context) {
	web.JSON(c, web.SuccessData(h.confimGetCarStatistics(c)))
}

// normalizeLocationParam 对应 carLocation / carWarning 共用的入参规整。
func normalizeLocationParam(c *gin.Context) {
	if strings.Contains(isNull(queryParam(c, "sectionCode")), sectionAll) {
		setQuery(c, "sectionCode", "")
	}
	code := isNull(queryParam(c, "code"))
	switch isNull(queryParam(c, "type")) {
	case "1":
		if code == "" {
			code = stationCapture
		}
		setQuery(c, "tollCode", code)
	case "2":
		if code == "" {
			code = gantryCapture
		}
		setQuery(c, "gantryCode", code)
	case "3":
		if code == "" {
			code = serviceAreaCapture
		}
		setQuery(c, "fwqbm", code)
	}
}

func (h *handler) bigCarLocation(c *gin.Context) {
	normalizeLocationParam(c)
	out := make([]*carLocationVO, 0)
	for _, car := range h.getRedisCarList(c) {
		if isNull(car.Status) != "1" {
			continue
		}
		devCodes := isNull(car.GantryCode)
		if !isExitsStr(devCodes, queryParam(c, "roadCode")) ||
			!isExitsStr(devCodes, queryParam(c, "sectionCode")) ||
			!isExitsStr(devCodes, queryParam(c, "tollCode")) ||
			!isExitsStr(devCodes, queryParam(c, "gantryCode")) ||
			!isExitsStr(devCodes, queryParam(c, "fwqbm")) {
			continue
		}
		if !isExitsStr(car.EscapedType, queryParam(c, "escapedType")) ||
			!isExitsStr(car.CarNo, queryParam(c, "carNoQuery")) {
			continue
		}
		vo := &carLocationVO{
			ID: car.ID, CarNo: car.CarNo, CarType: car.CarType,
			LonStr: car.LastPassLongitude, LatStr: car.LastPassLatitude,
			LastPassType: car.LastPassType, Status: car.Status,
		}
		if v := parseFloatPtr(strOf(vo.LonStr)); v != nil {
			vo.Lon = *v
		}
		if v := parseFloatPtr(strOf(vo.LatStr)); v != nil {
			vo.Lat = *v
		}
		out = append(out, vo)
	}
	web.JSON(c, web.SuccessData(out))
}

func (h *handler) bigSectionList(c *gin.Context) {
	var rows []struct {
		SectionCode string `gorm:"column:section_code"`
		SectionName string `gorm:"column:section_name"`
	}
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(
		"SELECT DISTINCT t.section_code, concat(t.road_code, '', t.section_name) AS section_name " +
			"FROM ods_szdn_section t WHERE 1=1").Scan(&rows)
	out := make([]*sectionVO, 0, len(rows)+1)
	out = append(out, &sectionVO{SectionCode: strPtr(sectionAll), SectionName: strPtr("全部")})
	for _, row := range rows {
		out = append(out, &sectionVO{SectionCode: strPtr(row.SectionCode), SectionName: strPtr(row.SectionName)})
	}
	web.JSON(c, web.SuccessData(out))
}

// bigTollGantryFwqList 对应 GET /tollGantryFwqList。
func (h *handler) bigTollGantryFwqList(c *gin.Context) {
	typeParam := queryParam(c, "type")
	if typeParam == "" {
		web.JSON(c, web.ErrorResult(web.NewServiceError(
			"Required request parameter 'type' for method parameter type String is not present")))
		return
	}
	sectionCode := queryParam(c, "sectionCode")
	if isBlank(sectionCode) {
		web.JSON(c, web.SuccessData([]*tollGantryFwqVO{}))
		return
	}
	stripped := deleteEnd(sectionCode)
	var sectionList []string
	if !strings.Contains(stripped, sectionAll) {
		sectionList = splitCSV(stripped)
	}
	out := make([]*tollGantryFwqVO, 0)
	query := func(sqlStr string, args []any, build func(string, string) *tollGantryFwqVO) {
		var rows []struct {
			Code string `gorm:"column:code"`
			Name string `gorm:"column:name"`
		}
		_ = h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, args...).Scan(&rows)
		for _, row := range rows {
			out = append(out, build(row.Code, row.Name))
		}
	}
	switch typeParam {
	case "1":
		sqlStr := "SELECT DISTINCT t.toll_code AS code, t.toll_name AS name FROM ods_szdn_toll t WHERE 1=1"
		var args []any
		if len(sectionList) > 0 {
			sqlStr += " AND t.section_code IN ?"
			args = append(args, sectionList)
		}
		sqlStr += " ORDER BY t.toll_name"
		query(sqlStr, args, func(code, name string) *tollGantryFwqVO {
			return &tollGantryFwqVO{Type: strPtr("1"), Code: strPtr(code), Name: strPtr(name)}
		})
	case "2":
		sqlStr := "SELECT DISTINCT t.gantry_code AS code, t.gantry_name AS name FROM ods_szdn_gantry t WHERE 1=1"
		var args []any
		if len(sectionList) > 0 {
			sqlStr += " AND t.section_code IN ?"
			args = append(args, sectionList)
		}
		sqlStr += " ORDER BY t.gantry_name"
		query(sqlStr, args, func(code, name string) *tollGantryFwqVO {
			return &tollGantryFwqVO{Type: strPtr("2"), Code: strPtr(code), Name: strPtr(name)}
		})
	case "3":
		sqlStr := "SELECT DISTINCT t.fwqbm AS code, t.fwqmc AS name FROM dwd_lczt_fwqjcxx t WHERE 1=1"
		var args []any
		if len(sectionList) > 0 {
			sqlStr += " AND t.ssldbh IN ?"
			args = append(args, sectionList)
		}
		sqlStr += " UNION ALL SELECT DISTINCT t.fwqbm AS code, t.fwqmc AS name FROM base_config_service_area t WHERE 1=1"
		if len(sectionList) > 0 {
			sqlStr += " AND t.section_code IN ?"
			args = append(args, sectionList)
		}
		query(sqlStr, args, func(code, name string) *tollGantryFwqVO {
			return &tollGantryFwqVO{Type: strPtr("3"), Code: strPtr(code), Name: strPtr(name)}
		})
	}
	web.JSON(c, web.SuccessData(out))
}

// bigCarVoList 对应 selectCarVoList（resultMap 丢弃 id / escapedTypeName）。
func (h *handler) bigCarVoList(c *gin.Context) {
	sqlStr := "SELECT t.car_no, t.car_type, t.escaped_type, t.escaped_amount FROM car_info t " +
		"WHERE t.del_flag = '0' ORDER BY t.create_time DESC,t.id LIMIT 10"
	var rows []*carInfoVO
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr).Scan(&rows)
	web.JSON(c, web.SuccessData(rows))
}

func (h *handler) bigCarAudit(c *gin.Context) {
	vo := &carAuditVO{}
	if escaped := h.aduitGetCarAudit(c); escaped != nil {
		vo.TotalAmount = escaped.EscapedAmount
		vo.TotalCount = escaped.Number
	}
	if finished := h.confimGetCarConfirm(c); finished != nil {
		vo.FinishedAmount = finished.EscapedAmount
		vo.FinishedCount = finished.Number
	}
	web.JSON(c, web.SuccessData(vo))
}

func (h *handler) bigCarWarning(c *gin.Context) {
	normalizeLocationParam(c)
	web.JSON(c, web.SuccessData(h.selectWarningListLimit100(c)))
}

func (h *handler) bigExceptionCar(c *gin.Context) {
	web.JSON(c, web.SuccessData(h.suspiciousListLimit10(c)))
}

// bigTopTen 对应 getTopTen + 控制器外的排行榜加工。
func (h *handler) bigTopTen(c *gin.Context) {
	sqlStr := "SELECT t1.road_code, t1.section_name, count(1) AS car_num " +
		"FROM car_warning_info t, ods_szdn_section t1 " +
		"WHERE t.del_flag = '0' AND t.section_code = t1.section_code " +
		"GROUP BY t1.road_code, t1.section_name ORDER BY car_num DESC LIMIT 10"
	var rows []*topTenVO
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr).Scan(&rows)
	index := 1
	var topOne int64 = -1
	for _, item := range rows {
		item.SectionName = strPtr(strOf(item.RoadCode) + " " + strOf(item.SectionName))
		if index == 1 {
			item.Rate = strPtr("100")
			topOne = item.CarNum
		} else if topOne != -1 {
			item.Rate = strPtr(strconv.FormatInt(item.CarNum*100/topOne, 10))
		}
		item.Rank = index
		index++
	}
	web.JSON(c, web.SuccessData(rows))
}

func (h *handler) bigOrgList(c *gin.Context) {
	var rows []*orgVO
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(
		"SELECT t.org_code, t.org_name FROM ods_yhgl_v_base_org t").Scan(&rows)
	web.JSON(c, web.SuccessData(rows))
}

func (h *handler) bigIncomeStatistic(c *gin.Context) {
	if isBlank(queryParam(c, "queryDateType")) {
		setQuery(c, "queryDateType", "suo")
	}
	web.JSON(c, web.SuccessData(h.aduitIncomeStatistic(c)))
}

// bigExceptRecordList 对应 GET /exceptRecordList（逐行补 orgId / supplementaryStatus）。
func (h *handler) bigExceptRecordList(c *gin.Context) {
	clause, args := buildWhere(c, exceptRecordSpec.prefix(), exceptRecordSpec.conditions)
	dest := newSliceOf(&carExceptRecord{})
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: exceptRecordSpec.selectSQL + exceptRecordSpec.selectSuffix,
		FromSQL:   exceptRecordSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   exceptRecordSpec.orderBy,
		Page:      web.PageAlways(c),
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows := *(dest.(*[]*carExceptRecord))
	for _, row := range rows {
		// JAVA 对照: BigScreenController.list -> row.setOrgId(selectOrgId(...))
		// selectOrgId 查不到时返回 null，因此这里也要保持 nil（不能写成 ""）。
		if orgID := h.selectConfimOrgID(c, strOf(row.CarID), strOf(row.ID)); orgID != "" {
			row.OrgID = strPtr(orgID)
		} else {
			row.OrgID = nil
		}
		var count int64
		_ = h.app.DB.WithContext(c.Request.Context()).Raw(
			"SELECT COUNT(1) FROM car_aduit_free WHERE del_flag = '0' AND car_id = ?", row.CarID).Scan(&count).Error
		if count > 0 {
			row.SupplementaryStatus = strPtr("1")
		}
		row.normalize()
	}
	web.JSON(c, web.Table(rows, total))
}

// selectConfimOrgID 对应 selectOrgId(carId, id)。
func (h *handler) selectConfimOrgID(c *gin.Context, carID, exceptID string) string {
	var orgID string
	_ = h.app.DB.WithContext(c.Request.Context()).Raw(
		"SELECT org_id FROM car_confim_free WHERE car_id = ? AND find_in_set(except_ids, ?) > 0 LIMIT 1",
		carID, exceptID).Scan(&orgID)
	return orgID
}

// bussTestSyncCurrentTrack 对应 POST /manager/busstest/syncCurrentTrack。
func (h *handler) bussTestSyncCurrentTrack(c *gin.Context) {
	if isNull(h.app.Cfg.IsLocalhost) == "local" {
		c.Status(http.StatusOK)
		return
	}
	for _, car := range h.getRedisCarList(c) {
		carNo := isNull(car.CarNo)
		var trail trailInfo
		found := h.app.Cache.Get(c.Request.Context(), carCurrentTrailKey+carNo, &trail)
		cols := map[string]any{"status": "0", "track_josn": nil}
		if found {
			cols["status"] = "1"
			cols["track_josn"] = mustMarshal(trail)
			if points, ok := trail.TrailList.([]any); ok && len(points) > 0 {
				last := points[len(points)-1]
				if point, ok := last.(map[string]any); ok {
					cols["last_pass_longitude"] = stringValue(point["lon"])
					cols["last_pass_latitude"] = stringValue(point["lat"])
					cols["last_pass_time"] = stringValue(point["captureTime"])
					cols["last_pass_address"] = stringValue(point["devName"])
					cols["last_pass_type"] = stringValue(point["stateType"])
				}
			}
		}
		if _, err := h.updateRow(c.Request.Context(), carInfoTable, strOf(car.ID), cols); err != nil {
			h.app.Log.Warn("同步实时轨迹失败", "carNo", carNo, "err", err)
		}
	}
	// 缓存刷新（Java 在任务末尾重新装载 car_list）
	_ = h.refreshCarList(c)
	c.Status(http.StatusOK)
}

func mustMarshal(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

// stringValue 把任意 JSON 值转成字符串。
func stringValue(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return x
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	case int64:
		return strconv.FormatInt(x, 10)
	default:
		return strings.TrimSpace(strings.Trim(fmtSprint(x), `"`))
	}
}

func fmtSprint(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}
