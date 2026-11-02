// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailTracksServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml
// 类/职责: 车辆行驶轨迹（car_track_info + zdata_trail_tracks）
// 对应 Go 文件: internal/modules/manager/car_track.go
//
// DIFF: Java 在本地轨迹为空时会调用 HttpSysUtilApiService.carTrackQueryByCarNo 远端接口并回写
// zdata_trail_tracks / car_history_trail；Go 迁移版未接入该外部服务，返回空列表（total=0）。
// DIFF: changeTrailInfo 的 raodTrailList / trailDevCountBO 依赖路网 Geometry 计算，
// Go 侧返回空数组与「0 个异常点」的默认结构。
package manager

import (
	"encoding/json"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/auth"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// trackList 对应 selectCarTrackInfoList：Java 在 Service 里把经纬度字符串转成 BigDecimal。
func (h *handler) trackList(c *gin.Context) {
	clause, args := buildWhere(c, trackInfoSpec.prefix(), trackInfoSpec.conditions)
	dest := newSliceOf(&carTrackInfo{})
	page := web.PageAlways(c)
	total, err := h.list(c.Request.Context(), listQuery{
		SelectSQL: trackInfoSpec.selectSQL,
		FromSQL:   trackInfoSpec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderFor(trackInfoSpec.orderBy, page),
		Page:      page,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows := *(dest.(*[]*carTrackInfo))
	for _, row := range rows {
		row.LongitudeDec = parseFloatPtr(strOf(row.Longitude))
		row.LatitudeDec = parseFloatPtr(strOf(row.Latitude))
	}
	web.JSON(c, web.Table(rows, total))
}

// zdataTrailTracks 对应 com.ruoyi.base.domain.ZdataTrailTracks。
//
// JAVA 对照: com/ruoyi/base/domain/ZdataTrailTracks.java
// Java 会把 track_josn / 轨迹表记录反序列化成该类再序列化输出，
// 因此响应里是「类字段全集」，未取到的键是 null —— Go 用指针 + 不带 omitempty 对齐。
type zdataTrailTracks struct {
	UUID              *string       `json:"uuid" gorm:"column:uuid"`
	Type              *int          `json:"type" gorm:"column:type"`
	PointCount        *int64        `json:"pointCount" gorm:"column:point_count"`
	PlateKey          *string       `json:"plateKey" gorm:"column:plate_key"`
	EnterTime         *web.DateTime `json:"enterTime" gorm:"column:enter_time"`
	ExitTime          *web.DateTime `json:"exitTime" gorm:"column:exit_time"`
	TrailPoints       *string       `json:"trailPoints" gorm:"column:trail_points"`
	EnterLocationcode *string       `json:"enterLocationcode" gorm:"column:enter_locationcode"`
	ExitLocationcode  *string       `json:"exitLocationcode" gorm:"column:exit_locationcode"`
	TrackJosn         *string       `json:"trackJosn" gorm:"column:track_josn"`
	Enaxlecount       *int          `json:"enaxlecount" gorm:"column:enaxlecount"`
	Entolllaneid      *string       `json:"entolllaneid" gorm:"column:entolllaneid"`
	Entollstationid   *string       `json:"entollstationid" gorm:"column:entollstationid"`
	Entollstationname *string       `json:"entollstationname" gorm:"column:entollstationname"`
	Envehicleclass    *string       `json:"envehicleclass" gorm:"column:envehicleclass"`
	Envehicleid       *string       `json:"envehicleid" gorm:"column:envehicleid"`
	Envehicletype     *string       `json:"envehicletype" gorm:"column:envehicletype"`
	Enweight          *float64      `json:"enweight" gorm:"column:enweight"`
	Extolllaneid      *string       `json:"extolllaneid" gorm:"column:extolllaneid"`
	Extollstationid   *string       `json:"extollstationid" gorm:"column:extollstationid"`
	Extollstationname *string       `json:"extollstationname" gorm:"column:extollstationname"`
	Exvehicleclass    *string       `json:"exvehicleclass" gorm:"column:exvehicleclass"`
	Exvehicleid       *string       `json:"exvehicleid" gorm:"column:exvehicleid"`
	Exvehicletype     *string       `json:"exvehicletype" gorm:"column:exvehicletype"`
	Exweight          *float64      `json:"exweight" gorm:"column:exweight"`
	StartLon          *string       `json:"startLon" gorm:"column:start_lon"`
	StratLat          *string       `json:"stratLat" gorm:"column:strat_lat"`
	EndLon            *string       `json:"endLon" gorm:"column:end_lon"`
	EndLat            *string       `json:"endLat" gorm:"column:end_lat"`

	// @TableField(exist = false)
	FirtStationCode   *string   `json:"firtStationCode" gorm:"-"`
	FirtStationName   *string   `json:"firtStationName" gorm:"-"`
	FirtStationTime   *string   `json:"firtStationTime" gorm:"-"`
	PlateColor        *string   `json:"plateColor" gorm:"-"`
	CarType           *string   `json:"carType" gorm:"-"`
	CarNo             *string   `json:"carNo" gorm:"-"`
	CarVehicle        *string   `json:"carVehicle" gorm:"-"`
	CarNum            *int64    `json:"carNum" gorm:"-"`
	EscapedType       *string   `json:"escapedType" gorm:"-"`
	PassType          *string   `json:"passType" gorm:"-"`
	EscapedTypeRemark *string   `json:"escapedTypeRemark" gorm:"-"`
	ApplyTime1        *string   `json:"applyTime1" gorm:"-"`
	ApplyTime2        *string   `json:"applyTime2" gorm:"-"`
	IsCylx            *string   `json:"isCylx" gorm:"-"`
	Flag              *string   `json:"flag" gorm:"-"`
	StartLonDec       *float64  `json:"startLonDec" gorm:"-"`
	StratLatDec       *float64  `json:"stratLatDec" gorm:"-"`
	EndLonDec         *float64  `json:"endLonDec" gorm:"-"`
	EndLatDec         *float64  `json:"endLatDec" gorm:"-"`
	UUIDList          []*string `json:"uuidList" gorm:"-"`
	PassCount         *int      `json:"passCount" gorm:"-"`
	EscapedTfcj       *string   `json:"escapedTfcj" gorm:"-"`
}

// trailDevCountBO 对应 com.ruoyi.base.domain.TrailDevCountBO
// （字段顺序照抄 Java 声明：exceptNum / trailDevList / trailList / exceptMsg）。
//
// DIFF: listByCarByTime 分支里 Java 只 set exceptNum 与空的 trailDevList，
// trailList / exceptMsg 保持 null，因此这里用 any 而不是切片/字符串。
type trailDevCountBO struct {
	ExceptNum    int64 `json:"exceptNum"`
	TrailDevList any   `json:"trailDevList"`
	TrailList    any   `json:"trailList"`
	ExceptMsg    any   `json:"exceptMsg"`
}

// trailDevBO 对应 com.ruoyi.base.domain.TrailDevBO。
type trailDevBO struct {
	Status    *string    `json:"status"`
	DevName   *string    `json:"devName"`
	TrailList []*trailBO `json:"trailList"`
}

const feeRecordState = "FeeRecord"

// applyPilenoDec 对应 CarTrackInfoServiceImpl.getCarGeometry 里的桩号换算：
// Java 在按路线分组前会把 "K3123+200" 这类桩号写成数值 pilenoDec，
// 该副作用会体现在详情接口的轨迹点上。
//
// DIFF: 只有需要生成路网几何的分支（详情接口）会调用；listByCarByTime 不调用。
// Java 遇到非法桩号会抛 NumberFormatException（500），这里按缺失值处理。
func applyPilenoDec(points []*trailBO) {
	for _, point := range points {
		roadCode := isNull(point.RoadCode)
		pileno := isNull(point.Pileno)
		if roadCode == "" || pileno == "" {
			continue
		}
		changed := strings.NewReplacer("+", ".", "ZK", "", "YK", "", "K", "").Replace(pileno)
		point.PilenoDec = parseFloatPtr(changed)
	}
}

// trailDevCount 对应 CarTrackInfoServiceImpl.getTrailDevBO：
// 门架抓拍/卡口流水按设备名合并，只有「有门架抓拍、无卡口流水」的设备记为异常。
func trailDevCount(tracks *zdataTrailTracks, points []*trailBO) *trailDevCountBO {
	if tracks == nil {
		tracks = &zdataTrailTracks{}
	}
	grouped := map[string][]*trailBO{}
	unique := make([]*trailBO, 0, len(points))
	for _, point := range points {
		stateType := isNull(point.StateType)
		devName := isNull(point.DevName)
		if stateType == gantryCapture || stateType == feeRecordState {
			if devName == "" {
				unique = append(unique, point)
				continue
			}
			if _, ok := grouped[devName]; !ok {
				unique = append(unique, point)
			}
			grouped[devName] = append(grouped[devName], point)
			continue
		}
		unique = append(unique, point)
	}

	var exceptNum int64
	devList := make([]*trailDevBO, 0, len(unique))
	for _, point := range unique {
		devName := isNull(point.DevName)
		list := []*trailBO{point}
		status := "0"
		stateType := isNull(point.StateType)
		if stateType == gantryCapture || stateType == feeRecordState {
			if merged, ok := grouped[devName]; ok {
				list = merged
				countGantryCapture, countFeeRecord := 0, 0
				for _, item := range list {
					switch isNull(item.StateType) {
					case gantryCapture:
						countGantryCapture++
					case feeRecordState:
						countFeeRecord++
					}
				}
				if countGantryCapture > 0 && countFeeRecord == 0 {
					status = "1"
					exceptNum++
				}
			}
		}
		devList = append(devList, &trailDevBO{Status: strPtr(status), DevName: strPtr(devName), TrailList: list})
	}

	// Java: 缺起止点经纬度时给出提示文案
	tips := ""
	if tracks.StartLonDec == nil || tracks.StratLatDec == nil {
		tips = "起始位置"
	}
	if tracks.EndLonDec == nil || tracks.EndLatDec == nil {
		if tips == "" {
			tips = "终点位置"
		} else {
			tips += "和终点位置"
		}
	}
	exceptMsg := any("")
	if tips != "" {
		exceptMsg = "由于无法获取轨迹" + tips + "，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。"
	}

	return &trailDevCountBO{
		ExceptNum:    exceptNum,
		TrailDevList: devList,
		TrailList:    points,
		ExceptMsg:    exceptMsg,
	}
}

const zdataTrailTracksColumns = `t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, t.exit_time,
	t.trail_points, t.enter_locationcode, t.exit_locationcode, t.track_josn, t.enaxlecount,
	t.entolllaneid, t.entollstationid, t.entollstationname, t.envehicleclass, t.envehicleid,
	t.envehicletype, t.enweight, t.extolllaneid, t.extollstationid, t.extollstationname,
	t.exvehicleclass, t.exvehicleid, t.exvehicletype, t.exweight, t.start_lon, t.strat_lat,
	t.end_lon, t.end_lat`

func (h *handler) registerTrackInfo(reg *router.Registry) {
	auth := reg.Authed
	auth.GET("/manager/cartrackinfo/list", h.trackList)
	auth.GET("/manager/cartrackinfo/listByCarId", h.trackListByCarID)
	auth.GET("/manager/cartrackinfo/listByCarByTime", h.trackListByCarByTime)
	auth.PUT("/manager/cartrackinfo/changeTrailInfo", h.trackChangeTrailInfo)
	auth.GET("/manager/cartrackinfo/carSnapShot", h.trackCarSnapshot)
	auth.GET("/manager/cartrackinfo/export", h.trackExport)
	auth.GET("/manager/cartrackinfo/:id", h.tableGet2(trackInfoSpec))
	auth.POST("/manager/cartrackinfo", h.tableSave2(trackInfoSpec))
	auth.PUT("/manager/cartrackinfo", h.tableSave2(trackInfoSpec))
	auth.DELETE("/manager/cartrackinfo/:ids", h.tableDelete2(trackInfoSpec))
}

// trackQuery 对应 selectZdataTrailTracksList / getCyly + getHistoryTrail。
// 两个调用方（listByCarId、listByCarByTime）在 Java 里都先 startPage() ⇒ 默认 1/10 分页。
func (h *handler) trackQuery(c *gin.Context) ([]*zdataTrailTracks, int64, error) {
	page := web.PageAlways(c)
	isCylx := isNull(queryParam(c, "isCylx"))
	base := " FROM zdata_trail_tracks t WHERE 1 = 1"
	var args []any
	if carNo := isNull(queryParam(c, "carNo")); carNo != "" {
		base += " AND t.plate_key = ?"
		args = append(args, carNo)
	}
	if plateKey := isNull(queryParam(c, "plateKey")); plateKey != "" {
		base += " AND t.plate_key LIKE CONCAT('%', ?, '%')"
		args = append(args, plateKey)
	}
	if v := argString(c, "applyTime1"); v != "" {
		base += " AND t.enter_time >= STR_TO_DATE(?, '%Y-%m-%d')"
		args = append(args, v)
	}
	if v := argString(c, "applyTime2"); v != "" {
		base += " AND t.enter_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
		args = append(args, v)
	}
	if v := argString(c, "entollstationid"); v != "" {
		base += " AND t.entollstationid = ?"
		args = append(args, v)
	}

	var uuidList []string
	passMap := map[string]int64{}
	if isCylx == "1" {
		// getCyly：取通行次数最多的 3 条常用路线
		cySQL := "SELECT uuid, pass_count FROM (SELECT t.uuid, gc.pass_count, " +
			"ROW_NUMBER() OVER (PARTITION BY t.plate_key, t.entollstationid, t.extollstationid " +
			"ORDER BY t.enter_time DESC) AS rn FROM zdata_trail_tracks t INNER JOIN (" +
			"SELECT plate_key, entollstationid, extollstationid, COUNT(*) AS pass_count " +
			"FROM zdata_trail_tracks t WHERE 1=1"
		var cyArgs []any
		if carNo := isNull(queryParam(c, "carNo")); carNo != "" {
			cySQL += " AND t.plate_key = ?"
			cyArgs = append(cyArgs, carNo)
		}
		if v := argString(c, "applyTime1"); v != "" {
			cySQL += " AND t.enter_time >= STR_TO_DATE(?, '%Y-%m-%d')"
			cyArgs = append(cyArgs, v)
		}
		if v := argString(c, "applyTime2"); v != "" {
			cySQL += " AND t.enter_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"
			cyArgs = append(cyArgs, v)
		}
		cySQL += " GROUP BY plate_key, entollstationid, extollstationid ORDER BY pass_count DESC LIMIT 3) gc " +
			"ON t.plate_key = gc.plate_key AND t.entollstationid = gc.entollstationid " +
			"AND t.extollstationid = gc.extollstationid) a WHERE rn = 1 ORDER BY pass_count DESC"
		var cyRows []struct {
			UUID      string `gorm:"column:uuid"`
			PassCount *int64 `gorm:"column:pass_count"`
		}
		if err := h.app.DB.WithContext(c.Request.Context()).Raw(cySQL, cyArgs...).Scan(&cyRows).Error; err != nil {
			return nil, 0, err
		}
		for _, row := range cyRows {
			uuidList = append(uuidList, row.UUID)
			if row.PassCount != nil {
				passMap[row.UUID] = *row.PassCount
			}
		}
		if len(uuidList) > 0 {
			base += " AND t.uuid IN ?"
			args = append(args, uuidList)
		}
	}
	if isCylx == "1" && len(uuidList) == 0 {
		return []*zdataTrailTracks{}, 0, nil
	}

	var total int64
	if page.HasPage {
		if err := h.app.DB.WithContext(c.Request.Context()).
			Raw("SELECT COUNT(1) "+base, args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	if page.SkipQuery(total) {
		return []*zdataTrailTracks{}, total, nil
	}
	sqlStr := "SELECT " + zdataTrailTracksColumns + base + " ORDER BY t.enter_time DESC"
	queryArgs := args
	if page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := page.LimitOffset(total)
		queryArgs = append(append([]any{}, args...), lim, off)
	}
	rows := newSliceOf(&zdataTrailTracks{})
	if err := h.app.DB.WithContext(c.Request.Context()).Raw(sqlStr, queryArgs...).Scan(rows).Error; err != nil {
		return nil, 0, err
	}
	result := *(rows.(*[]*zdataTrailTracks))
	if !page.HasPage {
		total = int64(len(result))
	}
	if isCylx == "1" {
		for _, row := range result {
			count, ok := passMap[strOf(row.UUID)]
			if !ok {
				continue
			}
			row.PlateKey = strPtr(strOf(row.PlateKey) + "(通行" + strconv.FormatInt(count, 10) + "次)")
		}
	}
	for _, row := range result {
		row.StartLonDec = parseFloatPtr(strOf(row.StartLon))
		row.StratLatDec = parseFloatPtr(strOf(row.StratLat))
		row.EndLonDec = parseFloatPtr(strOf(row.EndLon))
		row.EndLatDec = parseFloatPtr(strOf(row.EndLat))
	}
	return result, total, nil
}

// trackListByCarID 对应 GET /listByCarId。
func (h *handler) trackListByCarID(c *gin.Context) {
	if isBlank(queryParam(c, "carNo")) {
		setQueryOverride(c, "carNo", "-1")
	}
	rows, total, err := h.trackQuery(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	trailList := buildTrailInfos(rows)
	// DIFF: 本地无数据时 Java 会调用外部接口，这里不再外呼（见文件头说明）。
	web.JSON(c, web.Table(trailList, total))
}

// trackListByCarByTime 对应 GET /listByCarByTime（仅本地表）。
func (h *handler) trackListByCarByTime(c *gin.Context) {
	rows, total, err := h.trackQuery(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(buildTrailInfos(rows), total))
}

// buildTrailInfos 对应控制器里把 trackJosn 解析成 TrailBo 列表的分支。
func buildTrailInfos(rows []*zdataTrailTracks) []*trailInfo {
	out := make([]*trailInfo, 0, len(rows))
	for _, track := range rows {
		if isBlank(track.TrackJosn) {
			continue
		}
		var points []*trailBO
		_ = json.Unmarshal([]byte(strOf(track.TrackJosn)), &points)
		// JAVA 对照: tracksBo.setTrailPoints("") / setTrackJosn("")
		track.TrailPoints = strPtr("")
		track.TrackJosn = strPtr("")
		carNo := isNull(track.PlateKey)
		out = append(out, &trailInfo{
			TrailUUID:       &carNo,
			Tracks:          track,
			TrailList:       points,
			RaodTrailList:   []any{},
			TrailDevCountBO: &trailDevCountBO{ExceptNum: 0, TrailDevList: []any{}},
		})
	}
	return out
}

// trackChangeTrailInfo 对应 PUT /changeTrailInfo（记录查询日志后返回轨迹）。
func (h *handler) trackChangeTrailInfo(c *gin.Context) {
	body, err := jsonBody(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	encoded, _ := json.Marshal(body)
	h.writeQueryLog(c, string(encoded), "1", "1")

	var trail map[string]any
	_ = json.Unmarshal(encoded, &trail)
	if trail != nil {
		if points, ok := trail["trailList"].([]any); ok && len(points) > 0 {
			trail["raodTrailList"] = []any{}
			trail["trailDevCountBO"] = &trailDevCountBO{ExceptNum: 0, TrailDevList: []any{}}
		}
	}
	web.JSON(c, web.SuccessData(trail))
}

// trackCarSnapshot 对应 GET /carSnapShot（外部抓拍服务未迁移）。
func (h *handler) trackCarSnapshot(c *gin.Context) {
	stateType := isNull(queryParam(c, "stateType"))
	pointUUID := isNull(queryParam(c, "pointUuid"))
	if isBlank(stateType) || isBlank(pointUUID) {
		web.JSON(c, web.Success())
		return
	}
	web.JSON(c, web.SuccessData(nil))
}

func (h *handler) trackExport(c *gin.Context) {
	clause, args := buildWhere(c, trackInfoSpec.prefix(), trackInfoSpec.conditions)
	cols := []exportCol{
		{Title: "车牌号", Field: "carNo"}, {Title: "经度", Field: "longitude"},
		{Title: "纬度", Field: "latitude"}, {Title: "设备类型", Field: "deviceType"},
		{Title: "设备编号", Field: "deviceNo"}, {Title: "车道", Field: "laneNo"},
		{Title: "抓拍时间", Field: "snapTime"}, {Title: "路段名称", Field: "roadSectionName"},
		{Title: "备注", Field: "remark"},
	}
	h.exportWithClause(c, trackInfoSpec, clause, args, "carTrackInfo.xlsx", "车辆行驶轨迹数据", cols, true, nil)
}

// writeQueryLog 对应 ICarQueryLogService.queryLog。
func (h *handler) writeQueryLog(c *gin.Context, condition, modelType, menuPoint string) {
	userID := auth.CurrentUserID(c)
	realName := auth.CurrentUsername(c)
	loginIP := auth.ClientIP(c)
	cols := map[string]any{
		"id": newUUID(), "user_id": strconv.FormatInt(userID, 10), "user_name": realName,
		"user_ip": loginIP, "model_type": modelType, "menu_point": menuPoint,
		"query_condition": condition, "del_flag": "0",
		"create_by": userID, "create_time": time.Now(),
	}
	if err := h.insertRow(c.Request.Context(), carQueryLogTable, cols); err != nil {
		h.app.Log.Warn("写入查询日志失败", "err", err)
	}
}

func parseFloatPtr(s string) *float64 {
	if isBlank(s) {
		return nil
	}
	v, err := strconv.ParseFloat(strings.TrimSpace(s), 64)
	if err != nil {
		return nil
	}
	return &v
}
