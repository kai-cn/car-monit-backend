// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarInfo.java
// 类/职责: 车辆信息（重点车辆库）car_info
// 对应 Go 文件: internal/modules/manager/models_carinfo.go
//
// DIFF: Java 用 Lombok @Data + Jackson 默认驼峰；Go 显式 json/form 标签，保持字段名与顺序可读。
// DIFF: lastPassTime / nextPassTime 在 Java 是 @JsonFormat("yyyy-MM-dd")，这里用 dateOnly。
package manager

const carInfoTable = "car_info"

type carInfo struct {
	EntityBase
	CarNo                *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType              *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle           *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum               *int64    `json:"carNum" form:"carNum" gorm:"column:car_num"`
	EscapedType          *string   `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	EscapedTypeName      *string   `json:"escapedTypeName" form:"escapedTypeName" gorm:"column:escaped_type_name"`
	EscapedAmount        *float64  `json:"escapedAmount" form:"escapedAmount" gorm:"column:escaped_amount"`
	EscapedNum           *int64    `json:"escapedNum" form:"escapedNum" gorm:"column:escaped_num"`
	ReturnAmount         *float64  `json:"returnAmount" form:"returnAmount" gorm:"column:return_amount"`
	TotalAmount          *float64  `json:"totalAmount" form:"totalAmount" gorm:"column:total_amount"`
	ChargeAmount         *float64  `json:"chargeAmount" form:"chargeAmount" gorm:"column:charge_amount"`
	DifAmount            *float64  `json:"difAmount" form:"difAmount" gorm:"column:dif_amount"`
	AuitOrgID            *string   `json:"auitOrgId" form:"auitOrgId" gorm:"column:auit_org_id"`
	AuitOrgName          *string   `json:"auitOrgName" form:"auitOrgName" gorm:"column:auit_org_name"`
	IsWhite              *string   `json:"isWhite" form:"isWhite" gorm:"column:is_white"`
	WhiteRemark          *string   `json:"whiteRemark" form:"whiteRemark" gorm:"column:white_remark"`
	FileIDs              *string   `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	Brand                *string   `json:"brand" form:"brand" gorm:"column:brand"`
	PlateColor           *string   `json:"plateColor" form:"plateColor" gorm:"column:plate_color"`
	PlateType            *string   `json:"plateType" form:"plateType" gorm:"column:plate_type"`
	CarColor             *string   `json:"carColor" form:"carColor" gorm:"column:car_color"`
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
	SectionCode          *string   `json:"sectionCode" form:"sectionCode" gorm:"column:section_code"`
	RoadSectionName      *string   `json:"roadSectionName" form:"roadSectionName" gorm:"column:road_section_name"`
	NextPassTime         *dateOnly `json:"nextPassTime" gorm:"column:next_pass_time"`
	NextPassType         *string   `json:"nextPassType" form:"nextPassType" gorm:"column:next_pass_type"`
	NextPassAddress      *string   `json:"nextPassAddress" form:"nextPassAddress" gorm:"column:next_pass_address"`
	NextPassLongitude    *string   `json:"nextPassLongitude" form:"nextPassLongitude" gorm:"column:next_pass_longitude"`
	NextPassLatitude     *string   `json:"nextPassLatitude" form:"nextPassLatitude" gorm:"column:next_pass_latitude"`
	TrackID              *string   `json:"trackId" form:"trackId" gorm:"column:track_id"`
	TrackJosn            *string   `json:"trackJosn" gorm:"column:track_josn"`
	OrgID                *string   `json:"orgId" form:"orgId" gorm:"column:org_id"`
	OrgCode              *string   `json:"orgCode" form:"orgCode" gorm:"column:org_code"`
	OrgName              *string   `json:"orgName" form:"orgName" gorm:"column:org_name"`
	GantryCode           *string   `json:"gantryCode" form:"gantryCode" gorm:"column:gantry_code"`
	RoadCode             *string   `json:"roadCode" form:"roadCode" gorm:"column:road_code"`
	RoadName             *string   `json:"roadName" form:"roadName" gorm:"column:road_name"`
	TollCode             *string   `json:"tollCode" form:"tollCode" gorm:"column:toll_code"`
	TollName             *string   `json:"tollName" form:"tollName" gorm:"column:toll_name"`
	LinkName             *string   `json:"linkName" form:"linkName" gorm:"column:link_name"`
	LinkPhone            *string   `json:"linkPhone" form:"linkPhone" gorm:"column:link_phone"`
	Fwqbm                *string   `json:"fwqbm" form:"fwqbm" gorm:"column:fwqbm"`
	Fwqmc                *string   `json:"fwqmc" form:"fwqmc" gorm:"column:fwqmc"`
	BackCol1             *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2             *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status               *string   `json:"status" form:"status" gorm:"column:status"`
	Remark               *string   `json:"remark" form:"remark" gorm:"column:remark"`

	// 以下为 @TableField(exist = false) 的查询/展示字段
	ApplyTime1    *string      `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string      `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CarNoQuery    *string      `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
	CreateTimeStr *string      `json:"createTimeStr" form:"createTimeStr" gorm:"-"`
	CreateInfo    *string      `json:"createInfo" form:"createInfo" gorm:"column:create_info"`
	TrailList     []*trailInfo `json:"trailList" gorm:"-"`
	Flag          *string      `json:"flag" form:"flag" gorm:"-"`
}

// carInfoColumns 是 CarInfo 可写列的「JSON 键 -> 列名」白名单。
var carInfoColumns = map[string]string{
	"epsId":                "eps_id",
	"delFlag":              "del_flag",
	"createBy":             "create_by",
	"createTime":           "create_time",
	"updateBy":             "update_by",
	"updateTime":           "update_time",
	"sort":                 "sort",
	"tenantId":             "tenant_id",
	"carNo":                "car_no",
	"carType":              "car_type",
	"carVehicle":           "car_vehicle",
	"carNum":               "car_num",
	"escapedType":          "escaped_type",
	"escapedTypeName":      "escaped_type_name",
	"escapedAmount":        "escaped_amount",
	"escapedNum":           "escaped_num",
	"returnAmount":         "return_amount",
	"totalAmount":          "total_amount",
	"chargeAmount":         "charge_amount",
	"difAmount":            "dif_amount",
	"auitOrgId":            "auit_org_id",
	"auitOrgName":          "auit_org_name",
	"isWhite":              "is_white",
	"whiteRemark":          "white_remark",
	"fileIds":              "file_ids",
	"brand":                "brand",
	"plateColor":           "plate_color",
	"plateType":            "plate_type",
	"carColor":             "car_color",
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
	"sectionCode":          "section_code",
	"roadSectionName":      "road_section_name",
	"nextPassTime":         "next_pass_time",
	"nextPassType":         "next_pass_type",
	"nextPassAddress":      "next_pass_address",
	"nextPassLongitude":    "next_pass_longitude",
	"nextPassLatitude":     "next_pass_latitude",
	"trackId":              "track_id",
	"trackJosn":            "track_josn",
	"orgId":                "org_id",
	"orgCode":              "org_code",
	"orgName":              "org_name",
	"gantryCode":           "gantry_code",
	"roadCode":             "road_code",
	"roadName":             "road_name",
	"tollCode":             "toll_code",
	"tollName":             "toll_name",
	"linkName":             "link_name",
	"linkPhone":            "link_phone",
	"fwqbm":                "fwqbm",
	"fwqmc":                "fwqmc",
	"backCol1":             "back_col1",
	"backCol2":             "back_col2",
	"status":               "status",
	"remark":               "remark",
}

// carInfoSelectColumns 对应 CarInfoMapper.xml 的 <sql id="selectCarInfoVo">。
const carInfoSelectColumns = `t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.escaped_type,
	t.escaped_type_name, t.escaped_amount, t.escaped_num, t.return_amount, t.total_amount,
	t.charge_amount, t.dif_amount, t.auit_org_id, t.auit_org_name, t.is_white, t.white_remark,
	t.file_ids, t.brand, t.plate_color, t.plate_type, t.car_color, t.data_source, t.data_source_name,
	t.last_pass_time, t.last_pass_picture, t.last_pass_type, t.last_pass_address, t.last_pass_longitude,
	t.last_pass_latitude, t.last_pass_cardirection, t.road_section_id, t.section_code, t.road_section_name,
	t.next_pass_time, t.next_pass_type, t.next_pass_address, t.next_pass_longitude, t.next_pass_latitude,
	t.track_id, t.org_id, t.org_code, t.org_name, t.gantry_code, t.road_code, t.road_name, t.toll_code,
	t.toll_name, t.link_name, t.link_phone, t.fwqbm, t.fwqmc, t.back_col1, t.back_col2, t.remark,
	t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time,
	t.tenant_id`
