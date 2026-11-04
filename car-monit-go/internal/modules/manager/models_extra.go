// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarAduitFree.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarConfimFree.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteDetail.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteInfo.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspicious.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousBack.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousCheck.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarTrackInfo.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningInfo.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningRule.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryCar.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryTradeInfo.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/BussTest.java
// 类/职责: manager 模块其余表的领域模型（列白名单 + JSON 形态）
// 对应 Go 文件: internal/modules/manager/models_extra.go
//
// DIFF: Java 的 @TableField(exist = false) 字段在 Go 里用 gorm:"-"；查询别名列用真实 column 标签。
// DIFF: BigDecimal -> *float64，Long -> *int64，日期列按 Java 的 @JsonFormat 选择 dateOnly / web.DateTime。
package manager

import "car-monit-go/internal/web"

// ---------------------------------------------------------------------------
// car_aduit_free —— 补缴处理明细
// ---------------------------------------------------------------------------

const carAduitFreeTable = "car_aduit_free"

type carAduitFree struct {
	EntityBase
	ConfirmID  *string  `json:"confirmId" form:"confirmId" gorm:"column:confirm_id"`
	CarID      *string  `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo      *string  `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType    *string  `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle *string  `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	OrgID      *string  `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName    *string  `json:"orgName" gorm:"column:org_name"`
	UserIDs    *string  `json:"userIds" form:"userIds" gorm:"column:user_ids"`
	UserNames  *string  `json:"userNames" form:"userNames" gorm:"column:user_names"`
	Amount     *float64 `json:"amount" form:"amount" gorm:"column:amount"`
	BackCol1   *string  `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2   *string  `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Remark     *string  `json:"remark" form:"remark" gorm:"column:remark"`
	Status     *string  `json:"status" form:"status" gorm:"column:status"`

	ApplyTime1 *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2 *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
}

var carAduitFreeColumns = mergeColumns(baseColumns, map[string]string{
	"confirmId":  "confirm_id",
	"carId":      "car_id",
	"carNo":      "car_no",
	"carType":    "car_type",
	"carVehicle": "car_vehicle",
	"orgId":      "org_id",
	"userIds":    "user_ids",
	"userNames":  "user_names",
	"amount":     "amount",
	"backCol1":   "back_col1",
	"backCol2":   "back_col2",
	"remark":     "remark",
	"status":     "status",
})

const carAduitFreeSelectColumns = `t.id, t.confirm_id, t.car_id, t.car_no, t.car_type, t.car_vehicle,
	t.org_id, t.user_ids, t.user_names, t.amount, t.back_col1, t.back_col2, t.remark, t.status,
	t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_confim_free —— 确认补缴单
// ---------------------------------------------------------------------------

const carConfimFreeTable = "car_confim_free"

type carConfimFree struct {
	EntityBase
	CarID        *string  `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo        *string  `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType      *string  `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle   *string  `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	LinkName     *string  `json:"linkName" form:"linkName" gorm:"column:link_name"`
	LinkPhone    *string  `json:"linkPhone" form:"linkPhone" gorm:"column:link_phone"`
	OrgID        *string  `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName      *string  `json:"orgName" gorm:"column:org_name"`
	UserIDs      *string  `json:"userIds" form:"userIds" gorm:"column:user_ids"`
	UserNames    *string  `json:"userNames" form:"userNames" gorm:"column:user_names"`
	Amount       *float64 `json:"amount" form:"amount" gorm:"column:amount"`
	AduitAmount  *float64 `json:"aduitAmount" form:"aduitAmount" gorm:"column:aduit_amount"`
	ExceptIDs    *string  `json:"exceptIds" form:"exceptIds" gorm:"column:except_ids"`
	EscapedTypes *string  `json:"escapedTypes" form:"escapedTypes" gorm:"column:escaped_types"`
	BackCol1     *string  `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string  `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Remark       *string  `json:"remark" form:"remark" gorm:"column:remark"`
	Status       *string  `json:"status" form:"status" gorm:"column:status"`

	// @TableField(exist = false)
	// Number / EscapedAmount 在 Java 里有非 null 初值（Integer 0 / BigDecimal.ZERO）。
	Number              int64    `json:"number" gorm:"-"`
	ConfimEscapedAmount float64  `json:"escapedAmount" gorm:"-"`
	TotalAmount         *float64 `json:"totalAmount" gorm:"-"`
	ChargeAmount        *float64 `json:"chargeAmount" gorm:"-"`
	DifAmount           *float64 `json:"difAmount" gorm:"-"`
	ApplyTime1          *string  `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2          *string  `json:"applyTime2" form:"applyTime2" gorm:"-"`
	ApplyTime3          *string  `json:"applyTime3" form:"applyTime3" gorm:"-"`
	ApplyTime4          *string  `json:"applyTime4" form:"applyTime4" gorm:"-"`
	CarNoQuery          *string  `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
	ConfimFreeNum       *int64   `json:"confimFreeNum" gorm:"column:confim_free_num"`
	ConfimFreeAmount    *float64 `json:"confimFreeAmount" gorm:"column:confim_free_amount"`
	EscapedType         *string  `json:"escapedType" form:"escapedType" gorm:"-"`
	ComfimFreeType      *string  `json:"comfimFreeType" form:"comfimFreeType" gorm:"-"`

	CarExceptRecordList []*carExceptRecord `json:"carExceptRecordList" gorm:"-"`
	CarAduitFreeList    []*carAduitFree    `json:"carAduitFreeList" gorm:"-"`
}

var carConfimFreeColumns = mergeColumns(baseColumns, map[string]string{
	"carId":        "car_id",
	"carNo":        "car_no",
	"carType":      "car_type",
	"carVehicle":   "car_vehicle",
	"linkName":     "link_name",
	"linkPhone":    "link_phone",
	"orgId":        "org_id",
	"userIds":      "user_ids",
	"userNames":    "user_names",
	"amount":       "amount",
	"aduitAmount":  "aduit_amount",
	"exceptIds":    "except_ids",
	"escapedTypes": "escaped_types",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"remark":       "remark",
	"status":       "status",
})

const carConfimFreeSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.link_name,
	t.link_phone, t.org_id, sd.dept_name AS org_name, t.user_ids, t.user_names, t.amount, t.aduit_amount,
	t.except_ids, t.escaped_types, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id,
	t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_route_detail
// ---------------------------------------------------------------------------

const carRouteDetailTable = "car_route_detail"

type carRouteDetail struct {
	EntityBase
	RouteID              *string   `json:"routeId" form:"routeId" gorm:"column:route_id"`
	CarID                *string   `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo                *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	DataSource           *string   `json:"dataSource" form:"dataSource" gorm:"column:data_source"`
	DataSourceName       *string   `json:"dataSourceName" form:"dataSourceName" gorm:"column:data_source_name"`
	LastPassTime         *dateOnly `json:"lastPassTime" gorm:"column:last_pass_time"`
	LastPassPicture      *string   `json:"lastPassPicture" form:"lastPassPicture" gorm:"column:last_pass_picture"`
	LastPassType         *string   `json:"lastPassType" form:"lastPassType" gorm:"column:last_pass_type"`
	LastPassAddress      *string   `json:"lastPassAddress" form:"lastPassAddress" gorm:"column:last_pass_address"`
	LastPassLongitude    *string   `json:"lastPassLongitude" form:"lastPassLongitude" gorm:"column:last_pass_longitude"`
	LastPassLatitude     *string   `json:"lastPassLatitude" form:"lastPassLatitude" gorm:"column:last_pass_latitude"`
	LastPassCardirection *string   `json:"lastPassCardirection" form:"lastPassCardirection" gorm:"column:last_pass_cardirection"`
	RoadSectionID        *string   `json:"roadSectionId" form:"roadSectionId" gorm:"column:road_section_id"`
	RoadSectionName      *string   `json:"roadSectionName" form:"roadSectionName" gorm:"column:road_section_name"`
	NextPassTime         *dateOnly `json:"nextPassTime" gorm:"column:next_pass_time"`
	NextPassType         *string   `json:"nextPassType" form:"nextPassType" gorm:"column:next_pass_type"`
	NextPassAddress      *string   `json:"nextPassAddress" form:"nextPassAddress" gorm:"column:next_pass_address"`
	NextPassLongitude    *string   `json:"nextPassLongitude" form:"nextPassLongitude" gorm:"column:next_pass_longitude"`
	NextPassLatitude     *string   `json:"nextPassLatitude" form:"nextPassLatitude" gorm:"column:next_pass_latitude"`
	OrgID                *string   `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName              *string   `json:"orgName" form:"orgName" gorm:"column:org_name"`
	BackCol1             *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2             *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status               *string   `json:"status" form:"status" gorm:"column:status"`
	Remark               *string   `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1 *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2 *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
}

var carRouteDetailColumns = mergeColumns(baseColumns, map[string]string{
	"routeId":              "route_id",
	"carId":                "car_id",
	"carNo":                "car_no",
	"dataSource":           "data_source",
	"dataSourceName":       "data_source_name",
	"lastPassTime":         "last_pass_time",
	"lastPassPicture":      "last_pass_picture",
	"lastPassType":         "last_pass_type",
	"lastPassAddress":      "last_pass_address",
	"lastPassLongitude":    "last_pass_longitude",
	"lastPassLatitude":     "last_pass_latitude",
	"lastPassCardirection": "last_pass_cardirection",
	"roadSectionId":        "road_section_id",
	"roadSectionName":      "road_section_name",
	"nextPassTime":         "next_pass_time",
	"nextPassType":         "next_pass_type",
	"nextPassAddress":      "next_pass_address",
	"nextPassLongitude":    "next_pass_longitude",
	"nextPassLatitude":     "next_pass_latitude",
	"orgId":                "org_id",
	"orgName":              "org_name",
	"backCol1":             "back_col1",
	"backCol2":             "back_col2",
	"status":               "status",
	"remark":               "remark",
})

const carRouteDetailSelectColumns = `t.id, t.route_id, t.car_id, t.car_no, t.data_source,
	t.data_source_name, t.last_pass_time, t.last_pass_picture, t.last_pass_type, t.last_pass_address,
	t.last_pass_longitude, t.last_pass_latitude, t.last_pass_cardirection, t.road_section_id,
	t.road_section_name, t.next_pass_time, t.next_pass_type, t.next_pass_address, t.next_pass_longitude,
	t.next_pass_latitude, t.org_id, t.org_name, t.back_col1, t.back_col2, t.remark, t.status, t.sort,
	t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_route_info
// ---------------------------------------------------------------------------

const carRouteInfoTable = "car_route_info"

type carRouteInfo struct {
	EntityBase
	CarID          *string `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo          *string `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType        *string `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle     *string `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum         *int64  `json:"carNum" form:"carNum" gorm:"column:car_num"`
	StartAddress   *string `json:"startAddress" form:"startAddress" gorm:"column:start_address"`
	StartLongitude *string `json:"startLongitude" form:"startLongitude" gorm:"column:start_longitude"`
	StartLatitude  *string `json:"startLatitude" form:"startLatitude" gorm:"column:start_latitude"`
	EndAddress     *string `json:"endAddress" form:"endAddress" gorm:"column:end_address"`
	EndLongitude   *string `json:"endLongitude" form:"endLongitude" gorm:"column:end_longitude"`
	EndLatitude    *string `json:"endLatitude" form:"endLatitude" gorm:"column:end_latitude"`
	RouteDetail    *string `json:"routeDetail" form:"routeDetail" gorm:"column:route_detail"`
	BackCol1       *string `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2       *string `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status         *string `json:"status" form:"status" gorm:"column:status"`
	Remark         *string `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var carRouteInfoColumns = mergeColumns(baseColumns, map[string]string{
	"carId":          "car_id",
	"carNo":          "car_no",
	"carType":        "car_type",
	"carVehicle":     "car_vehicle",
	"carNum":         "car_num",
	"startAddress":   "start_address",
	"startLongitude": "start_longitude",
	"startLatitude":  "start_latitude",
	"endAddress":     "end_address",
	"endLongitude":   "end_longitude",
	"endLatitude":    "end_latitude",
	"routeDetail":    "route_detail",
	"backCol1":       "back_col1",
	"backCol2":       "back_col2",
	"status":         "status",
	"remark":         "remark",
})

const carRouteInfoSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.start_address, t.start_longitude, t.start_latitude, t.end_address, t.end_longitude, t.end_latitude,
	t.route_detail, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag,
	t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_suspicious / car_suspicious_back —— 可疑车辆
// ---------------------------------------------------------------------------

const carSuspiciousTable = "car_suspicious"
const carSuspiciousBackTable = "car_suspicious_back"

type carSuspicious struct {
	EntityBase
	PlateColor         *string       `json:"plateColor" form:"plateColor" gorm:"column:plate_color"`
	CarNo              *string       `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType            *string       `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle         *string       `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum             *int64        `json:"carNum" form:"carNum" gorm:"column:car_num"`
	PassType           *string       `json:"passType" form:"passType" gorm:"column:pass_type"`
	InStationID        *string       `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation          *string       `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime             *web.DateTime `json:"inTime" gorm:"column:in_time"`
	OutStationID       *string       `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation         *string       `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime            *web.DateTime `json:"outTime" gorm:"column:out_time"`
	GantryStationID    *string       `json:"gantryStationId" form:"gantryStationId" gorm:"column:gantry_station_id"`
	GantrytStation     *string       `json:"gantrytStation" form:"gantrytStation" gorm:"column:gantryt_station"`
	GantryTime         *web.DateTime `json:"gantryTime" gorm:"column:gantry_time"`
	FileIDs            *string       `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	OutGantryStationID *string       `json:"outGantryStationId" form:"outGantryStationId" gorm:"column:out_gantry_station_id"`
	OutGantrytStation  *string       `json:"outGantrytStation" form:"outGantrytStation" gorm:"column:out_gantryt_station"`
	OutGantryTime      *web.DateTime `json:"outGantryTime" gorm:"column:out_gantry_time"`
	OutFileIDs         *string       `json:"outFileIds" form:"outFileIds" gorm:"column:out_file_ids"`
	EscapedType        *string       `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	EscapedTypeName    *string       `json:"escapedTypeName" form:"escapedTypeName" gorm:"column:escaped_type_name"`
	EscapedNum         *int64        `json:"escapedNum" form:"escapedNum" gorm:"column:escaped_num"`
	IsExcept           *string       `json:"isExcept" form:"isExcept" gorm:"column:is_except"`
	ExceptRemark       *string       `json:"exceptRemark" form:"exceptRemark" gorm:"column:except_remark"`
	ExceptFileIDs      *string       `json:"exceptFileIds" form:"exceptFileIds" gorm:"column:except_file_ids"`
	CheckStatus        *string       `json:"checkStatus" form:"checkStatus" gorm:"column:check_status"`
	OrgID              *string       `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName            *string       `json:"orgName" form:"orgName" gorm:"column:org_name"`
	IsWhite            *string       `json:"isWhite" form:"isWhite" gorm:"column:is_white"`
	WhiteRemark        *string       `json:"whiteRemark" form:"whiteRemark" gorm:"column:white_remark"`
	WhiteFileIDs       *string       `json:"whiteFileIds" form:"whiteFileIds" gorm:"column:white_file_ids"`
	RoadCode           *string       `json:"roadCode" form:"roadCode" gorm:"column:road_code"`
	RoadName           *string       `json:"roadName" form:"roadName" gorm:"column:road_name"`
	SectionCode        *string       `json:"sectionCode" form:"sectionCode" gorm:"column:section_code"`
	SectionName        *string       `json:"sectionName" form:"sectionName" gorm:"column:section_name"`
	TrackID            *string       `json:"trackId" form:"trackId" gorm:"column:track_id"`
	TrackJosn          *string       `json:"trackJosn" gorm:"column:track_josn"`
	TrackNames         *string       `json:"trackNames" form:"trackNames" gorm:"column:track_names"`
	BackCol1           *string       `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2           *string       `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status             *string       `json:"status" form:"status" gorm:"column:status"`
	Remark             *string       `json:"remark" form:"remark" gorm:"column:remark"`

	// @TableField(exist = false)
	CarNoQuery    *string               `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
	ApplyTime1    *string               `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string               `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string               `json:"createTimeStr" gorm:"-"`
	CheckList     []*carSuspiciousCheck `json:"checkList" gorm:"-"`
	TrailList     []*trailInfo          `json:"trailList" gorm:"-"`
	GantryCode    *string               `json:"gantryCode" form:"gantryCode" gorm:"-"`
	TollCode      *string               `json:"tollCode" form:"tollCode" gorm:"-"`
	Fwqbm         *string               `json:"fwqbm" form:"fwqbm" gorm:"-"`
	Type          *string               `json:"type" form:"type" gorm:"-"`
	Code          *string               `json:"code" form:"code" gorm:"-"`
	ChargeAmount  *string               `json:"chargeAmount" gorm:"-"`
	TotalAmount   *string               `json:"totalAmount" gorm:"-"`
	DifAmount     *string               `json:"difAmount" gorm:"-"`
	MjTime        *string               `json:"mjTime" gorm:"-"`
	MjAddress     *string               `json:"mjAddress" gorm:"-"`
	TxTime        *string               `json:"txTime" gorm:"-"`
	TxAddress     *string               `json:"txAddress" gorm:"-"`
}

var carSuspiciousColumns = mergeColumns(baseColumns, map[string]string{
	"plateColor":         "plate_color",
	"carNo":              "car_no",
	"carType":            "car_type",
	"carVehicle":         "car_vehicle",
	"carNum":             "car_num",
	"passType":           "pass_type",
	"inStationId":        "in_station_id",
	"inStation":          "in_station",
	"inTime":             "in_time",
	"outStationId":       "out_station_id",
	"outStation":         "out_station",
	"outTime":            "out_time",
	"gantryStationId":    "gantry_station_id",
	"gantrytStation":     "gantryt_station",
	"gantryTime":         "gantry_time",
	"fileIds":            "file_ids",
	"outGantryStationId": "out_gantry_station_id",
	"outGantrytStation":  "out_gantryt_station",
	"outGantryTime":      "out_gantry_time",
	"outFileIds":         "out_file_ids",
	"escapedType":        "escaped_type",
	"escapedTypeName":    "escaped_type_name",
	"escapedNum":         "escaped_num",
	"isExcept":           "is_except",
	"exceptRemark":       "except_remark",
	"exceptFileIds":      "except_file_ids",
	"checkStatus":        "check_status",
	"orgId":              "org_id",
	"orgName":            "org_name",
	"isWhite":            "is_white",
	"whiteRemark":        "white_remark",
	"whiteFileIds":       "white_file_ids",
	"roadCode":           "road_code",
	"roadName":           "road_name",
	"sectionCode":        "section_code",
	"sectionName":        "section_name",
	"trackId":            "track_id",
	"trackJosn":          "track_josn",
	"trackNames":         "track_names",
	"backCol1":           "back_col1",
	"backCol2":           "back_col2",
	"status":             "status",
	"remark":             "remark",
})

const carSuspiciousSelectColumns = `t.id, t.plate_color, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.pass_type, t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time,
	t.gantry_station_id, t.gantryt_station, t.gantry_time, t.file_ids, t.out_gantry_station_id,
	t.out_gantryt_station, t.out_gantry_time, t.out_file_ids, t.escaped_type, t.escaped_type_name,
	t.escaped_num, t.is_except, t.except_remark, t.except_file_ids, t.check_status, t.org_id, t.org_name,
	t.is_white, t.white_remark, t.white_file_ids, t.road_code, t.road_name, t.section_code, t.section_name,
	t.track_id, t.back_col1, t.back_col2, t.remark, t.status, t.create_time`

// carSuspiciousBackSelectColumns 对应 CarSuspiciousBackMapper.xml 的 selectCarSuspiciousBackVo。
//
// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousBackMapper.xml:61
// 与可疑车辆 VO 的差别只有一处：备份表多选了 t.sort。
const carSuspiciousBackSelectColumns = `t.id, t.plate_color, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.pass_type, t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time,
	t.gantry_station_id, t.gantryt_station, t.gantry_time, t.file_ids, t.out_gantry_station_id,
	t.out_gantryt_station, t.out_gantry_time, t.out_file_ids, t.escaped_type, t.escaped_type_name,
	t.escaped_num, t.is_except, t.except_remark, t.except_file_ids, t.check_status, t.org_id, t.org_name,
	t.is_white, t.white_remark, t.white_file_ids, t.road_code, t.road_name, t.section_code, t.section_name,
	t.track_id, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.create_time`

// ---------------------------------------------------------------------------
// car_suspicious_back —— 备份表实体
//
// JAVA 对照: com/ruoyi/manager/domain/CarSuspiciousBack.java:23
//
// DIFF: Java 的 CarSuspiciousBack 继承 BasePlusEntityInput（而 CarSuspicious 继承
// BasePlusEntityLong），且 4 个时间字段是 @JsonFormat(pattern = "yyyy-MM-dd")，
// 另外没有 @TableField(exist = false) 的扩展字段（checkList/trailList/… 都不存在）。
// 因此备份表接口必须用自己的实体，不能复用 carSuspicious。
// ---------------------------------------------------------------------------

type carSuspiciousBack struct {
	EntityBase
	PlateColor         *string   `json:"plateColor" form:"plateColor" gorm:"column:plate_color"`
	CarNo              *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType            *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle         *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum             *int64    `json:"carNum" form:"carNum" gorm:"column:car_num"`
	PassType           *string   `json:"passType" form:"passType" gorm:"column:pass_type"`
	InStationID        *string   `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation          *string   `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime             *dateOnly `json:"inTime" gorm:"column:in_time"`
	OutStationID       *string   `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation         *string   `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime            *dateOnly `json:"outTime" gorm:"column:out_time"`
	GantryStationID    *string   `json:"gantryStationId" form:"gantryStationId" gorm:"column:gantry_station_id"`
	GantrytStation     *string   `json:"gantrytStation" form:"gantrytStation" gorm:"column:gantryt_station"`
	GantryTime         *dateOnly `json:"gantryTime" gorm:"column:gantry_time"`
	FileIDs            *string   `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	OutGantryStationID *string   `json:"outGantryStationId" form:"outGantryStationId" gorm:"column:out_gantry_station_id"`
	OutGantrytStation  *string   `json:"outGantrytStation" form:"outGantrytStation" gorm:"column:out_gantryt_station"`
	OutGantryTime      *dateOnly `json:"outGantryTime" gorm:"column:out_gantry_time"`
	OutFileIDs         *string   `json:"outFileIds" form:"outFileIds" gorm:"column:out_file_ids"`
	EscapedType        *string   `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	EscapedTypeName    *string   `json:"escapedTypeName" form:"escapedTypeName" gorm:"column:escaped_type_name"`
	EscapedNum         *int64    `json:"escapedNum" form:"escapedNum" gorm:"column:escaped_num"`
	IsExcept           *string   `json:"isExcept" form:"isExcept" gorm:"column:is_except"`
	ExceptRemark       *string   `json:"exceptRemark" form:"exceptRemark" gorm:"column:except_remark"`
	ExceptFileIDs      *string   `json:"exceptFileIds" form:"exceptFileIds" gorm:"column:except_file_ids"`
	CheckStatus        *string   `json:"checkStatus" form:"checkStatus" gorm:"column:check_status"`
	OrgID              *string   `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName            *string   `json:"orgName" form:"orgName" gorm:"column:org_name"`
	IsWhite            *string   `json:"isWhite" form:"isWhite" gorm:"column:is_white"`
	WhiteRemark        *string   `json:"whiteRemark" form:"whiteRemark" gorm:"column:white_remark"`
	WhiteFileIDs       *string   `json:"whiteFileIds" form:"whiteFileIds" gorm:"column:white_file_ids"`
	RoadCode           *string   `json:"roadCode" form:"roadCode" gorm:"column:road_code"`
	RoadName           *string   `json:"roadName" form:"roadName" gorm:"column:road_name"`
	SectionCode        *string   `json:"sectionCode" form:"sectionCode" gorm:"column:section_code"`
	SectionName        *string   `json:"sectionName" form:"sectionName" gorm:"column:section_name"`
	TrackID            *string   `json:"trackId" form:"trackId" gorm:"column:track_id"`
	TrackJosn          *string   `json:"trackJosn" form:"trackJosn" gorm:"column:track_josn"`
	TrackNames         *string   `json:"trackNames" form:"trackNames" gorm:"column:track_names"`
	BackCol1           *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2           *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status             *string   `json:"status" form:"status" gorm:"column:status"`
	Remark             *string   `json:"remark" form:"remark" gorm:"column:remark"`
}

// carSuspiciousBackColumns 是备份表可写入列（MP 驼峰-下划线自动映射）。
var carSuspiciousBackColumns = mergeColumns(baseColumns, map[string]string{
	"plateColor":         "plate_color",
	"carNo":              "car_no",
	"carType":            "car_type",
	"carVehicle":         "car_vehicle",
	"carNum":             "car_num",
	"passType":           "pass_type",
	"inStationId":        "in_station_id",
	"inStation":          "in_station",
	"inTime":             "in_time",
	"outStationId":       "out_station_id",
	"outStation":         "out_station",
	"outTime":            "out_time",
	"gantryStationId":    "gantry_station_id",
	"gantrytStation":     "gantryt_station",
	"gantryTime":         "gantry_time",
	"fileIds":            "file_ids",
	"outGantryStationId": "out_gantry_station_id",
	"outGantrytStation":  "out_gantryt_station",
	"outGantryTime":      "out_gantry_time",
	"outFileIds":         "out_file_ids",
	"escapedType":        "escaped_type",
	"escapedTypeName":    "escaped_type_name",
	"escapedNum":         "escaped_num",
	"isExcept":           "is_except",
	"exceptRemark":       "except_remark",
	"exceptFileIds":      "except_file_ids",
	"checkStatus":        "check_status",
	"orgId":              "org_id",
	"orgName":            "org_name",
	"isWhite":            "is_white",
	"whiteRemark":        "white_remark",
	"whiteFileIds":       "white_file_ids",
	"roadCode":           "road_code",
	"roadName":           "road_name",
	"sectionCode":        "section_code",
	"sectionName":        "section_name",
	"trackId":            "track_id",
	"trackJosn":          "track_josn",
	"trackNames":         "track_names",
	"backCol1":           "back_col1",
	"backCol2":           "back_col2",
	"status":             "status",
	"remark":             "remark",
})

// ---------------------------------------------------------------------------
// car_suspicious_check —— 人工核实明细
// ---------------------------------------------------------------------------

const carSuspiciousCheckTable = "car_suspicious_check"

type carSuspiciousCheck struct {
	EntityBase
	CarID         *string  `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo         *string  `json:"carNo" form:"carNo" gorm:"column:car_no"`
	SuspicousFlag *string  `json:"suspicousFlag" form:"suspicousFlag" gorm:"column:suspicous_flag"`
	Attachments   *string  `json:"attachments" form:"attachments" gorm:"column:attachments"`
	EscapedType   *string  `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	BackCol1      *string  `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	ChargeAmount  *float64 `json:"chargeAmount" form:"chargeAmount" gorm:"column:charge_amount"`
	TotalAmount   *float64 `json:"totalAmount" form:"totalAmount" gorm:"column:total_amount"`
	BackCol2      *string  `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	DifAmount     *float64 `json:"difAmount" form:"difAmount" gorm:"column:dif_amount"`
	Status        *string  `json:"status" form:"status" gorm:"column:status"`
	Remark        *string  `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var carSuspiciousCheckColumns = mergeColumns(baseColumns, map[string]string{
	"carId":         "car_id",
	"carNo":         "car_no",
	"suspicousFlag": "suspicous_flag",
	"attachments":   "attachments",
	"escapedType":   "escaped_type",
	"backCol1":      "back_col1",
	"chargeAmount":  "charge_amount",
	"totalAmount":   "total_amount",
	"backCol2":      "back_col2",
	"difAmount":     "dif_amount",
	"status":        "status",
	"remark":        "remark",
})

const carSuspiciousCheckSelectColumns = `t.id, t.car_id, t.car_no, t.suspicous_flag, t.attachments,
	t.escaped_type, t.back_col1, t.charge_amount, t.total_amount, t.back_col2, t.dif_amount, t.remark,
	t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time,
	t.tenant_id`

// ---------------------------------------------------------------------------
// car_track_info
// ---------------------------------------------------------------------------

const carTrackInfoTable = "car_track_info"

type carTrackInfo struct {
	EntityBase
	CarID           *string   `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo           *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	Longitude       *string   `json:"longitude" form:"longitude" gorm:"column:longitude"`
	Latitude        *string   `json:"latitude" form:"latitude" gorm:"column:latitude"`
	DeviceType      *string   `json:"deviceType" form:"deviceType" gorm:"column:device_type"`
	DeviceNo        *string   `json:"deviceNo" form:"deviceNo" gorm:"column:device_no"`
	LaneNo          *string   `json:"laneNo" form:"laneNo" gorm:"column:lane_no"`
	SnapTime        *dateOnly `json:"snapTime" gorm:"column:snap_time"`
	ReceiveTime     *dateOnly `json:"receiveTime" gorm:"column:receive_time"`
	SnapPic         *string   `json:"snapPic" form:"snapPic" gorm:"column:snap_pic"`
	RoadSectionID   *string   `json:"roadSectionId" form:"roadSectionId" gorm:"column:road_section_id"`
	RoadSectionName *string   `json:"roadSectionName" form:"roadSectionName" gorm:"column:road_section_name"`
	TrackID         *string   `json:"trackId" form:"trackId" gorm:"column:track_id"`
	TrackJosn       *string   `json:"trackJosn" gorm:"column:track_josn"`
	BackCol1        *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2        *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status          *string   `json:"status" form:"status" gorm:"column:status"`
	Remark          *string   `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1   *string  `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2   *string  `json:"applyTime2" form:"applyTime2" gorm:"-"`
	LongitudeDec *float64 `json:"longitudeDec" gorm:"-"`
	LatitudeDec  *float64 `json:"latitudeDec" gorm:"-"`
	PageNum      *int64   `json:"pageNum" gorm:"-"`
	PageSize     *int64   `json:"pageSize" gorm:"-"`
}

var carTrackInfoColumns = mergeColumns(baseColumns, map[string]string{
	"carId":           "car_id",
	"carNo":           "car_no",
	"longitude":       "longitude",
	"latitude":        "latitude",
	"deviceType":      "device_type",
	"deviceNo":        "device_no",
	"laneNo":          "lane_no",
	"snapTime":        "snap_time",
	"receiveTime":     "receive_time",
	"snapPic":         "snap_pic",
	"roadSectionId":   "road_section_id",
	"roadSectionName": "road_section_name",
	"trackId":         "track_id",
	"trackJosn":       "track_josn",
	"backCol1":        "back_col1",
	"backCol2":        "back_col2",
	"status":          "status",
	"remark":          "remark",
})

const carTrackInfoSelectColumns = `t.id, t.car_id, t.car_no, t.longitude, t.latitude, t.device_type,
	t.device_no, t.lane_no, t.snap_time, t.receive_time, t.snap_pic, t.road_section_id,
	t.road_section_name, t.track_id, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id,
	t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_warning_info
// ---------------------------------------------------------------------------

const carWarningInfoTable = "car_warning_info"

type carWarningInfo struct {
	EntityBase
	CarID             *string       `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo             *string       `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType           *string       `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle        *string       `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum            *int64        `json:"carNum" form:"carNum" gorm:"column:car_num"`
	InStationID       *string       `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation         *string       `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime            *web.DateTime `json:"inTime" gorm:"column:in_time"`
	GantryStationID   *string       `json:"gantryStationId" form:"gantryStationId" gorm:"column:gantry_station_id"`
	GantrytStation    *string       `json:"gantrytStation" form:"gantrytStation" gorm:"column:gantryt_station"`
	GantryTime        *web.DateTime `json:"gantryTime" gorm:"column:gantry_time"`
	FileIDs           *string       `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	NextPassTime      *web.DateTime `json:"nextPassTime" gorm:"column:next_pass_time"`
	NextPassType      *string       `json:"nextPassType" form:"nextPassType" gorm:"column:next_pass_type"`
	NextPassAddress   *string       `json:"nextPassAddress" form:"nextPassAddress" gorm:"column:next_pass_address"`
	NextPassLongitude *string       `json:"nextPassLongitude" form:"nextPassLongitude" gorm:"column:next_pass_longitude"`
	NextPassLatitude  *string       `json:"nextPassLatitude" form:"nextPassLatitude" gorm:"column:next_pass_latitude"`
	RoadCode          *string       `json:"roadCode" form:"roadCode" gorm:"column:road_code"`
	RoadName          *string       `json:"roadName" form:"roadName" gorm:"column:road_name"`
	SectionCode       *string       `json:"sectionCode" form:"sectionCode" gorm:"column:section_code"`
	SectionName       *string       `json:"sectionName" form:"sectionName" gorm:"column:section_name"`
	BackCol1          *string       `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2          *string       `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status            *string       `json:"status" form:"status" gorm:"column:status"`
	TrackID           *string       `json:"trackId" form:"trackId" gorm:"column:track_id"`
	TrackJosn         *string       `json:"trackJosn" gorm:"column:track_josn"`
	TrackNames        *string       `json:"trackNames" form:"trackNames" gorm:"column:track_names"`

	// @TableField(exist = false)
	GantryTimeStr   *string    `json:"gantryTimeStr" gorm:"-"`
	ApplyTime1      *string    `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2      *string    `json:"applyTime2" form:"applyTime2" gorm:"-"`
	EscapedType     *string    `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	EscapedAmount   *float64   `json:"escapedAmount" gorm:"column:escaped_amount"`
	CarNoQuery      *string    `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
	CreateTimeStr   *string    `json:"createTimeStr" gorm:"-"`
	InTimeStr       *string    `json:"inTimeStr" gorm:"-"`
	Flag            *string    `json:"flag" form:"flag" gorm:"-"`
	FlagTime        *string    `json:"flagTime" form:"flagTime" gorm:"-"`
	QueryRante      *string    `json:"queryRante" form:"queryRante" gorm:"-"`
	GantryCode      *string    `json:"gantryCode" form:"gantryCode" gorm:"-"`
	TollCode        *string    `json:"tollCode" form:"tollCode" gorm:"-"`
	Fwqbm           *string    `json:"fwqbm" form:"fwqbm" gorm:"-"`
	Type            *string    `json:"type" form:"type" gorm:"-"`
	Code            *string    `json:"code" form:"code" gorm:"-"`
	PlateColor      *string    `json:"plateColor" form:"plateColor" gorm:"column:plate_color"`
	NeedToWarnStr   *string    `json:"needToWarnStr" gorm:"-"`
	NextPassTimeStr *string    `json:"nextPassTimeStr" gorm:"-"`
	TrailFwqList    []*trailBO `json:"trailFwqList" gorm:"-"`
	// JAVA 对照: CarWarningInfo:238-244 两个 @TableField(exist=false) 集合字段，
	// Java 未赋值时 Jackson 仍输出 null，键必须存在。
	SectionCodeList []*string `json:"sectionCodeList" gorm:"-"`
	CodeList        []*string `json:"codeList" gorm:"-"`
}

var carWarningInfoColumns = mergeColumns(baseColumns, map[string]string{
	"carId":             "car_id",
	"carNo":             "car_no",
	"carType":           "car_type",
	"carVehicle":        "car_vehicle",
	"carNum":            "car_num",
	"inStationId":       "in_station_id",
	"inStation":         "in_station",
	"inTime":            "in_time",
	"gantryStationId":   "gantry_station_id",
	"gantrytStation":    "gantryt_station",
	"gantryTime":        "gantry_time",
	"fileIds":           "file_ids",
	"nextPassTime":      "next_pass_time",
	"nextPassType":      "next_pass_type",
	"nextPassAddress":   "next_pass_address",
	"nextPassLongitude": "next_pass_longitude",
	"nextPassLatitude":  "next_pass_latitude",
	"roadCode":          "road_code",
	"roadName":          "road_name",
	"sectionCode":       "section_code",
	"sectionName":       "section_name",
	"backCol1":          "back_col1",
	"backCol2":          "back_col2",
	"status":            "status",
	"trackId":           "track_id",
	"trackJosn":         "track_josn",
	"trackNames":        "track_names",
})

const carWarningInfoSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.in_station_id, t.in_station, t.in_time, t.gantry_station_id, t.gantryt_station, t.gantry_time,
	t.file_ids, t.next_pass_time, t.next_pass_type, t.next_pass_address, t.next_pass_longitude,
	t.next_pass_latitude, t.road_code, t.road_name, t.section_code, t.section_name, t.back_col1,
	t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by,
	t.update_time, t.tenant_id, t.track_id, t.track_names`

// ---------------------------------------------------------------------------
// car_warning_rule
// ---------------------------------------------------------------------------

const carWarningRuleTable = "car_warning_rule"

type carWarningRule struct {
	EntityBase
	RuleName        *string `json:"ruleName" form:"ruleName" gorm:"column:rule_name"`
	NoticeRangeID   *string `json:"noticeRangeId" form:"noticeRangeId" gorm:"column:notice_range_id"`
	NoticeRangeAnme *string `json:"noticeRangeAnme" form:"noticeRangeAnme" gorm:"column:notice_range_anme"`
	Notice          *string `json:"notice" form:"notice" gorm:"column:notice"`
	NoticeType      *string `json:"noticeType" form:"noticeType" gorm:"column:notice_type"`
	NoticeUserID    *string `json:"noticeUserId" form:"noticeUserId" gorm:"column:notice_user_id"`
	NoticeUserName  *string `json:"noticeUserName" form:"noticeUserName" gorm:"column:notice_user_name"`
	OrgID           *string `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgName         *string `json:"orgName" form:"orgName" gorm:"column:org_name"`
	BackCol1        *string `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2        *string `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status          *string `json:"status" form:"status" gorm:"column:status"`
	Remark          *string `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var carWarningRuleColumns = mergeColumns(baseColumns, map[string]string{
	"ruleName":        "rule_name",
	"noticeRangeId":   "notice_range_id",
	"noticeRangeAnme": "notice_range_anme",
	"notice":          "notice",
	"noticeType":      "notice_type",
	"noticeUserId":    "notice_user_id",
	"noticeUserName":  "notice_user_name",
	"orgId":           "org_id",
	"orgName":         "org_name",
	"backCol1":        "back_col1",
	"backCol2":        "back_col2",
	"status":          "status",
	"remark":          "remark",
})

const carWarningRuleSelectColumns = `t.id, t.rule_name, t.notice_range_id, t.notice_range_anme,
	t.notice, t.notice_type, t.notice_user_id, t.notice_user_name, t.org_id, t.org_name, t.back_col1,
	t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time,
	t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// gantry_car
// ---------------------------------------------------------------------------

const gantryCarTable = "gantry_car"

type gantryCar struct {
	EntityBase
	CarNo           *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType         *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle      *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum          *int64    `json:"carNum" form:"carNum" gorm:"column:car_num"`
	InStationID     *string   `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation       *string   `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime          *dateOnly `json:"inTime" gorm:"column:in_time"`
	GantryStationID *string   `json:"gantryStationId" form:"gantryStationId" gorm:"column:gantry_station_id"`
	GantrytStation  *string   `json:"gantrytStation" form:"gantrytStation" gorm:"column:gantryt_station"`
	GantryTime      *dateOnly `json:"gantryTime" gorm:"column:gantry_time"`
	FileIDs         *string   `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	BackCol1        *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2        *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status          *string   `json:"status" form:"status" gorm:"column:status"`
	Remark          *string   `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var gantryCarColumns = mergeColumns(baseColumns, map[string]string{
	"carNo":           "car_no",
	"carType":         "car_type",
	"carVehicle":      "car_vehicle",
	"carNum":          "car_num",
	"inStationId":     "in_station_id",
	"inStation":       "in_station",
	"inTime":          "in_time",
	"gantryStationId": "gantry_station_id",
	"gantrytStation":  "gantryt_station",
	"gantryTime":      "gantry_time",
	"fileIds":         "file_ids",
	"backCol1":        "back_col1",
	"backCol2":        "back_col2",
	"status":          "status",
	"remark":          "remark",
})

const gantryCarSelectColumns = `t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.in_station_id,
	t.in_station, t.in_time, t.gantry_station_id, t.gantryt_station, t.gantry_time, t.file_ids,
	t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by,
	t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// gantry_trade_info
// ---------------------------------------------------------------------------

const gantryTradeInfoTable = "gantry_trade_info"

type gantryTradeInfo struct {
	EntityBase
	CarNo        *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType      *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle   *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum       *int64    `json:"carNum" form:"carNum" gorm:"column:car_num"`
	InStationID  *string   `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation    *string   `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime       *dateOnly `json:"inTime" gorm:"column:in_time"`
	OutStationID *string   `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation   *string   `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime      *dateOnly `json:"outTime" gorm:"column:out_time"`
	ChargeType   *string   `json:"chargeType" form:"chargeType" gorm:"column:charge_type"`
	Amount       *float64  `json:"amount" form:"amount" gorm:"column:amount"`
	BackCol1     *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status       *string   `json:"status" form:"status" gorm:"column:status"`
	Remark       *string   `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var gantryTradeInfoColumns = mergeColumns(baseColumns, map[string]string{
	"carNo":        "car_no",
	"carType":      "car_type",
	"carVehicle":   "car_vehicle",
	"carNum":       "car_num",
	"inStationId":  "in_station_id",
	"inStation":    "in_station",
	"inTime":       "in_time",
	"outStationId": "out_station_id",
	"outStation":   "out_station",
	"outTime":      "out_time",
	"chargeType":   "charge_type",
	"amount":       "amount",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"status":       "status",
	"remark":       "remark",
})

const gantryTradeInfoSelectColumns = `t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time, t.charge_type,
	t.amount, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by,
	t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// buss_test
// ---------------------------------------------------------------------------

const bussTestTable = "buss_test"

type bussTest struct {
	EntityBase
	BillName     *string   `json:"billName" form:"billName" gorm:"column:bill_name"`
	BillType     *string   `json:"billType" form:"billType" gorm:"column:bill_type"`
	Amount       *float64  `json:"amount" form:"amount" gorm:"column:amount"`
	DeptID       *int64    `json:"deptId" form:"deptId" gorm:"column:dept_id"`
	UserID       *int64    `json:"userId" form:"userId" gorm:"column:user_id"`
	ApplyTime    *dateOnly `json:"applyTime" gorm:"column:apply_time"`
	ApplyTime2   *dateOnly `json:"applyTime2" gorm:"column:apply_time2"`
	FileIDs      *string   `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	FlowKey      *string   `json:"flowKey" form:"flowKey" gorm:"column:flow_key"`
	FlowRuid     *string   `json:"flowRuid" form:"flowRuid" gorm:"column:flow_ruid"`
	FlowApplyOid *string   `json:"flowApplyOid" form:"flowApplyOid" gorm:"column:flow_apply_oid"`
	FlowStatus   *string   `json:"flowStatus" form:"flowStatus" gorm:"column:flow_status"`
	ShTime       *dateOnly `json:"shTime" gorm:"column:sh_time"`
	BackCol1     *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status       *string   `json:"status" form:"status" gorm:"column:status"`
	Remark       *string   `json:"remark" form:"remark" gorm:"column:remark"`
}

var bussTestColumns = mergeColumns(baseColumns, map[string]string{
	"billName":     "bill_name",
	"billType":     "bill_type",
	"amount":       "amount",
	"deptId":       "dept_id",
	"userId":       "user_id",
	"applyTime":    "apply_time",
	"applyTime2":   "apply_time2",
	"fileIds":      "file_ids",
	"flowKey":      "flow_key",
	"flowRuid":     "flow_ruid",
	"flowApplyOid": "flow_apply_oid",
	"flowStatus":   "flow_status",
	"shTime":       "sh_time",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"status":       "status",
	"remark":       "remark",
})

const bussTestSelectColumns = `t.id, t.bill_name, t.bill_type, t.amount, t.dept_id, t.user_id,
	t.apply_time, t.apply_time2, t.file_ids, t.flow_key, t.flow_ruid, t.flow_apply_oid, t.flow_status,
	t.sh_time, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by,
	t.create_time, t.update_by, t.update_time, t.tenant_id`
